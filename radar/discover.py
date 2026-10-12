"""Find candidate repositories and rank them. Everything here is arithmetic, never a model."""

from __future__ import annotations

import datetime as dt
import math

from .net import HttpError


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
