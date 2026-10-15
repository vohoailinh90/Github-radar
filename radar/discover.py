"""Find candidate repositories and rank them. Everything here is arithmetic, never a model."""

from __future__ import annotations

import datetime as dt
import math
import re

from .net import HttpError

FALLBACK_BUCKET = "software"     # for a requested repo none of whose topics is in any bucket
_SEGMENT = re.compile(r"[A-Za-z0-9._-]+")


def _days(iso: str, today: dt.date) -> int:
    return max(0, (today - dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).date()).days)


def eligible(repo: dict, cfg: dict, seen: dict, today: dt.date) -> str | None:
    """None when the repo may be picked, else the reason it was dropped."""
    name = repo.get("full_name", "")
    spdx = ((repo.get("license") or {}).get("spdx_id") or "").lower()
    if name in seen:
        return "already covered"
    if spdx not in cfg["licenses"]:
        return f"licence {spdx or 'none'} is not on the free list"
    if repo.get("archived") or repo.get("fork") or repo.get("disabled") or repo.get("private"):
        return "archived, fork, disabled or private"
    if not (repo.get("description") or "").strip():
        return "no description"
    if int(repo.get("stargazers_count", 0)) < int(cfg["min_stars"]):
        return "below min_stars"
    if _days(repo.get("pushed_at", "1970-01-01T00:00:00Z"), today) > int(cfg["max_days_since_push"]):
        return "not pushed recently"
    return None


def score(repo: dict, today: dt.date) -> float:
    """ln(stars) + half of ln(stars gained per 30 days of life) + 1 if pushed in the last 30 days.

    Stars are GitHub's only public rating. The velocity term keeps a 90k-star classic from beating
    every newer project on every run, and needs no stored history."""
    stars = int(repo.get("stargazers_count", 0))
    age = max(30, _days(repo.get("created_at", today.isoformat() + "T00:00:00Z"), today))
    velocity = stars / age * 30
    fresh = 1.0 if _days(repo.get("pushed_at", "1970-01-01T00:00:00Z"), today) <= 30 else 0.0
    return round(math.log(1 + stars) + 0.5 * math.log(1 + velocity) + fresh, 4)


def candidates(gh, cfg: dict, seen: dict, today: dt.date) -> tuple[list[dict], dict]:
    """Search every bucket topic. Returns (ranked candidates, drop counts by reason)."""
    since = (today - dt.timedelta(days=int(cfg["max_days_since_push"]))).isoformat()
    found: dict[str, dict] = {}
    dropped: dict[str, int] = {}
    for bucket in cfg["buckets"]:
        for topic in bucket["topics"]:
            query = f"topic:{topic} stars:>={cfg['min_stars']} pushed:>={since} archived:false fork:false"
            try:
                results = gh.search(query, per_page=int(cfg["per_topic"]))
            except HttpError as exc:
                key = f"search failed (HTTP {exc.status})"
                dropped[key] = dropped.get(key, 0) + 1
                continue
            for repo in results:
                name = repo.get("full_name")
                if not name or name in found:
                    continue
                why = eligible(repo, cfg, seen, today)
                if why:
                    dropped[why] = dropped.get(why, 0) + 1
                    continue
                found[name] = {"full_name": name, "bucket": bucket["id"], "topic": topic,
                               "score": score(repo, today), "repo": repo}
    ranked = sorted(found.values(), key=lambda c: (-c["score"], c["full_name"]))
    return ranked, dropped


def pick(ranked: list[dict], cfg: dict, today: dt.date) -> list[dict]:
    """Best of each bucket in turn, starting at a bucket that rotates with the date, so a run
    does not always open with the same domain."""
    ids = [b["id"] for b in cfg["buckets"]]
    start = today.toordinal() % len(ids)
    order = ids[start:] + ids[:start]
    queues = {i: [c for c in ranked if c["bucket"] == i] for i in ids}
    chosen: list[dict] = []
    while len(chosen) < int(cfg["picks_per_run"]) and any(queues.values()):
        for bucket in order:
            if queues[bucket] and len(chosen) < int(cfg["picks_per_run"]):
                chosen.append(queues[bucket].pop(0))
    return chosen


def parse_repo(text: str) -> str:
    """`owner/name` from `owner/name` or a github.com link. A person (or a workflow input) typed it, so it is
    checked before it becomes part of an API path: letters, digits, `.`, `_` and `-` only."""
    raw = (text or "").strip()
    url = re.match(r"(?i)^(?:https?://)?(?:www\.)?github\.com/(.*)$", raw)
    parts = (re.split(r"[?#]", url.group(1), maxsplit=1)[0].strip("/") if url else raw).split("/")
    owner, name = (parts + ["", ""])[:2]
    name = re.sub(r"(?i)\.git$", "", name)
    # a link may continue (/tree/main, /issues); a bare owner/name may not
    if (len(parts) < 2 if url else len(parts) != 2) or not (_SEGMENT.fullmatch(owner) and _SEGMENT.fullmatch(name)) \
            or {owner, name} & {".", ".."}:
        raise ValueError(f"{raw[:80]!r} is not a repository: write owner/name or a github.com link")   # !r: no raw newline reaches the log
    return f"{owner}/{name}"


def requested(gh, text: str, cfg: dict, seen: dict, today: dt.date, bucket: str | None = None) -> tuple[dict, list[str]]:
    """One repository a person asked for, as a candidate shaped like the ones `candidates` returns.

    The person's choice replaces the ranking filters (stars, freshness, already covered): those only decide what the
    scheduled scan offers. What stays refused is what the content rules rest on: a repository that is private or
    disabled, or whose licence is not on the free list. The soft mismatches come back as warnings."""
    name = parse_repo(text)
    ids = [b["id"] for b in cfg["buckets"]]
    if bucket and bucket not in ids:
        raise ValueError(f"unknown bucket {bucket[:40]!r}: choose one of {', '.join(ids)}")
    try:
        repo = gh.get(f"/repos/{name}")
    except HttpError as exc:
        if exc.status == 404:
            raise ValueError(f"{name} was not found: it does not exist, is private, or was renamed") from exc
        raise
    if not isinstance(repo, dict) or not repo.get("full_name"):
        raise ValueError(f"GitHub gave no repository for {name}")
    full = repo["full_name"]                       # GitHub's spelling, which every later path and the seen list use
    spdx = ((repo.get("license") or {}).get("spdx_id") or "").lower()
    if repo.get("private") or repo.get("disabled"):
        raise ValueError(f"{full} is private or disabled")
    if spdx not in cfg["licenses"]:
        raise ValueError(f"{full}: licence {spdx or 'none'} is not on the free list (`licenses` in radar.yaml)")

    warnings: list[str] = []
    if full in seen:
        warnings.append(f"already covered on {seen[full].get('covered', '?')}: written again")
    if repo.get("archived"):
        warnings.append("archived")
    if repo.get("fork"):
        warnings.append("a fork")
    if not (repo.get("description") or "").strip():
        warnings.append("no description")
    stars = int(repo.get("stargazers_count", 0))
    if stars < int(cfg["min_stars"]):
        warnings.append(f"{stars} stars, below min_stars {cfg['min_stars']}")
    idle = _days(repo.get("pushed_at", "1970-01-01T00:00:00Z"), today)
    if idle > int(cfg["max_days_since_push"]):
        warnings.append(f"not pushed for {idle} days")

    topics = set(repo.get("topics") or [])
    chosen, hit, best = bucket, None, 0
    if not chosen:                                  # the bucket whose topics share most with the repository's
        for b in cfg["buckets"]:
            shared = [t for t in b["topics"] if t in topics]
            if len(shared) > best:
                chosen, hit, best = b["id"], shared[0], len(shared)
    if not chosen:
        chosen = FALLBACK_BUCKET if FALLBACK_BUCKET in ids else ids[0]
        warnings.append(f"no topic of the repository is in a bucket: filed under '{chosen}' (--bucket changes it)")
    cand = {"full_name": full, "bucket": chosen, "topic": hit or "requested", "score": score(repo, today), "repo": repo}
    return cand, warnings
