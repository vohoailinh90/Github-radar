"""Publish a scan's results as a pull request instead of a push to main.

Needed once main is protected (the workflow's own token can neither push there nor start CI on a pull request it opens).
Runs in the checkout of a scheduled or manual scan, right after the results were committed. The token (a fine-grained
personal access token limited to this repository: Contents and Pull requests, read and write) travels only in the
environment of the git child process and in an Authorization header: never in argv, a URL or a file (see handoff.py).
"""

from __future__ import annotations

import datetime as dt
import os
import re
from pathlib import Path

from .handoff import _git
from .net import HttpError, request_json

SEGMENT = re.compile(r"[A-Za-z0-9._-]{1,100}")
BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,99}")
DIGITS = re.compile(r"[0-9]{1,20}")


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "github-radar",
            "Accept": "application/vnd.github+json"}


def branch_name(date: str, run_id: str, attempt: str, now: dt.datetime) -> str:
    """radar/scan-<date>-<run id>-<attempt>: unique per workflow run, so a re-run never collides with an earlier branch."""
    tail = f"{run_id}-{attempt}" if DIGITS.fullmatch(run_id or "") and DIGITS.fullmatch(attempt or "") else now.strftime("%H%M%S")
    return f"radar/scan-{date}-{tail}"


def open_scan_prs(api: str, repo: str, token: str) -> list[int]:
    """Numbers of open pull requests that earlier scans opened (head radar/scan-...). Best effort: an error means "none known"."""
    try:
        items = request_json(f"{api}/repos/{repo}/pulls?state=open&per_page=100", headers=_headers(token))
    except HttpError:
        return []
    found = [i.get("number") for i in items if isinstance(i, dict) and str((i.get("head") or {}).get("ref", "")).startswith("radar/scan-")] \
        if isinstance(items, list) else []
    return sorted(n for n in found if isinstance(n, int))


def publish(*, repo: str, token: str, cwd: Path, base: str = "main", remote: str = "origin", automerge: bool = False,
            run_url: str = "", run_id: str = "", attempt: str = "1", api: str | None = None, now: dt.datetime | None = None) -> dict:
    """Push HEAD (the results commit) to a new branch and open a pull request into `base`. Returns what happened.

    A failure of the push raises (the results are then still only in the runner); a failure after it (the pull request, the
    auto-merge request) is reported in the result and the branch keeps the results."""
    owner, _, name = repo.partition("/")
    if not (SEGMENT.fullmatch(owner) and SEGMENT.fullmatch(name)) or {owner, name} & {".", ".."}:
        raise ValueError(f"{repo[:60]!r} is not owner/name")
    if not BRANCH.fullmatch(base) or ".." in base:
        raise ValueError(f"{base[:60]!r} is not a branch name")
    if not token:
        raise ValueError("RADAR_PR_TOKEN is not set")
    api = (api or os.environ.get("GITHUB_API_URL") or "https://api.github.com").rstrip("/")
    now = now or dt.datetime.now(dt.timezone.utc)
    date = now.strftime("%Y-%m-%d")
    branch = branch_name(date, run_id, attempt, now)

    # No --exit-code: "no such branch" is an empty answer, so a failure (auth, network) is an error with its own message.
    if _git(["ls-remote", "--heads", remote, branch], cwd, token, reset_header=True).strip():
        return {"status": "branch-exists", "branch": branch}                 # this run already published once
    _git(["push", "-q", remote, f"HEAD:refs/heads/{branch}"], cwd, token, reset_header=True)
    earlier = open_scan_prs(api, repo, token)

    body = ("Results of a Radar scan: new digests, the studio export and the state files (`seen.json`, `stars.json`, the run report).\n\n"
            + (f"Run: {run_url}\n\n" if run_url else "")
            + "Merge it to keep them: the next scan reads `state/` from `main`, so an unmerged scan is covered again and its star "
              "snapshot is missing. If GitHub says the branch is out of date, use *Update branch*."
            + (f"\n\n**Earlier scan pull requests are still open: {', '.join('#' + str(n) for n in earlier)}.** Every scan changes "
               "`state/`, so this one will conflict once an earlier one is merged. Merge them oldest first; if a conflict remains, "
               "close this one and run the scan again." if earlier else ""))
    try:
        pr = request_json(f"{api}/repos/{repo}/pulls", headers=_headers(token),
                          payload={"title": f"radar: scan {date}", "head": branch, "base": base, "body": body})
    except HttpError as exc:
        return {"status": "branch-pushed", "branch": branch, "error": f"pull request not opened (HTTP {exc.status})"}
    if not isinstance(pr, dict):
        return {"status": "branch-pushed", "branch": branch, "error": "pull request answer was not an object"}
    result = {"status": "opened", "branch": branch, "url": pr.get("html_url", ""), "number": pr.get("number")}
    if earlier:
        result["earlier_scan_prs"] = earlier
    if automerge:
        try:
            out = request_json(f"{api}/graphql", headers=_headers(token), payload={
                "query": "mutation($id: ID!) { enablePullRequestAutoMerge(input: {pullRequestId: $id, mergeMethod: MERGE}) { pullRequest { number } } }",
                "variables": {"id": pr.get("node_id", "")}})
            errors = out.get("errors") if isinstance(out, dict) else None
            result["automerge"] = "requested" if not errors else f"not enabled: {str((errors[0] or {}).get('message', ''))[:120]}"
        except HttpError as exc:
            result["automerge"] = f"not enabled (HTTP {exc.status})"
    return result
