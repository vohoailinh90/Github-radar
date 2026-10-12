"""Hand a bundle to tool-marketing-studio as a DRAFT pull request, never a push to its main.

The studio's own approval (a content hash) and publishing steps stay the owner's. The token
travels only in the environment of the git child process (`GIT_CONFIG_*`), never in argv, a URL
or a file, and the clone runs with hooks and `ext::` transport switched off.
"""

from __future__ import annotations

import base64
import os
import subprocess
import tempfile
from pathlib import Path

from .net import request_json

GIT_SAFE = ["-c", "core.hooksPath=/dev/null", "-c", "protocol.ext.allow=never", "-c", "protocol.file.allow=always",
            "-c", "core.fsmonitor=false", "-c", "commit.gpgsign=false"]


def _git(args: list[str], cwd: Path, token: str = "", host: str = "github.com") -> str:
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE")}
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_AUTHOR_NAME": "github-radar", "GIT_AUTHOR_EMAIL": "radar@users.noreply.github.com",
                "GIT_COMMITTER_NAME": "github-radar", "GIT_COMMITTER_EMAIL": "radar@users.noreply.github.com"})
    if token:
        basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        env.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": f"http.https://{host}/.extraheader",
                    "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}"})
    proc = subprocess.run(["git", *GIT_SAFE, *args], cwd=cwd, env=env, text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"git {args[0]} failed: {proc.stderr.strip()[:300]}")
    return proc.stdout


def open_pr(files: dict[str, str], *, remote: str, repo: str, campaign: str, token: str, base: str = "main",
            title: str, body: str, api: str | None = None) -> dict:
    """Clone `remote`, add the bundle on branch radar/<campaign>, push it, open a draft PR.

    Existing studio files are never overwritten: a brief or positioning the owner has edited
    stays theirs, and a campaign that already exists is reported as already handed off."""
    api = (api or os.environ.get("GITHUB_API_URL") or "https://api.github.com").rstrip("/")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "studio"
        _git(["clone", "--depth", "1", "--branch", base, remote, str(work)], Path(tmp), token)
        if (work / "campaigns" / campaign).exists():
            return {"status": "already-handed-off", "campaign": campaign}
        branch = f"radar/{campaign}"
        try:
            _git(["ls-remote", "--exit-code", "--heads", "origin", branch], work, token)
            return {"status": "branch-exists", "campaign": campaign, "branch": branch}   # an earlier PR (maybe closed) owns it
        except RuntimeError:
            pass
        _git(["checkout", "-b", branch], work)
        added = []
        for rel, text in sorted(files.items()):
            target = work / rel
            if target.exists() and not rel.startswith("campaigns/"):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            added.append(rel)
        _git(["add", "--"] + added, work)
        _git(["commit", "-q", "-m", f"radar: add campaign {campaign} (draft posts)"], work)
        _git(["push", "-q", "origin", branch], work, token)
    result = request_json(f"{api}/repos/{repo}/pulls", headers={
        "Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "github-radar",
        "Accept": "application/vnd.github+json"},
        payload={"title": title, "head": branch, "base": base, "body": body, "draft": True})
    return {"status": "opened", "campaign": campaign, "branch": branch, "url": result.get("html_url", ""),
            "files": added}
