"""Find candidate repositories and rank them. Everything here is arithmetic, never a model."""

from __future__ import annotations

import datetime as dt
import math
import re

from . import history
from .net import HttpError

FALLBACK_BUCKET = "software"     # for a requested repo none of whose topics is in any bucket
LOW_FORKS_PER_1K = 10            # flag (never a filter): fewer forks than this per 1,000 stars
SPIKE_RATIO = 0.25               # flag (never a filter): gained this share of all its stars within one measured window
_SEGMENT = re.compile(r"[A-Za-z0-9._-]+")


def _days(iso: str, today: dt.date) -> int:
    return max(0, (today - dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).date()).days)


def eligible(repo: dict, cfg: dict, seen: dict, today: dt.date, min_stars: int | None = None) -> str | None:
    """None when the repo may be picked, else the reason it was dropped. `min_stars` overrides the configured floor
    (the rising pass has a lower one)."""
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
    if int(repo.get("stargazers_count", 0)) < int(cfg["min_stars"] if min_stars is None else min_stars):
        return "below min_stars"
    if _days(repo.get("pushed_at", "1970-01-01T00:00:00Z"), today) > int(cfg["max_days_since_push"]):
        return "not pushed recently"
    return None


def momentum(repo: dict, today: dt.date, hist: dict | None = None) -> dict:
    """Stars gained per 30 days, and where the number comes from.

    "measured": the difference to a stored snapshot (radar.history), the only honest "what is climbing now".
    "lifetime": stars / age, used until a repository has a snapshot to compare with."""
    stars = int(repo.get("stargazers_count", 0))
    measured = history.velocity(hist or {}, repo.get("full_name", ""), stars, today)
    if measured:
        return {"per_30d": max(0.0, measured["per_day"]) * 30, "source": "measured",
                "gap_days": measured["gap_days"], "gained": measured["gained"]}
    age = max(30, _days(repo.get("created_at", today.isoformat() + "T00:00:00Z"), today))
    return {"per_30d": stars / age * 30, "source": "lifetime"}


def score(repo: dict, today: dt.date, hist: dict | None = None) -> float:
    """ln(stars) + half of ln(1 + stars gained per 30 days) + 1 if pushed in the last 30 days.

    Stars are GitHub's only public rating. The velocity term keeps a 90k-star classic from beating
    every newer project on every run: measured from stored snapshots when there are any, else the lifetime average."""
    stars = int(repo.get("stargazers_count", 0))
    fresh = 1.0 if _days(repo.get("pushed_at", "1970-01-01T00:00:00Z"), today) <= 30 else 0.0
    return round(math.log(1 + stars) + 0.5 * math.log(1 + momentum(repo, today, hist)["per_30d"]) + fresh, 4)


def flags(repo: dict, mom: dict) -> list[str]:
    """Reasons to look twice before trusting the stars. They are reported, never used to drop or rank a repository:
    stars can be bought, but neither signal proves it (a viral launch also spikes)."""
    stars, out = int(repo.get("stargazers_count", 0)), []
    if stars and int(repo.get("forks_count", 0)) * 1000 < stars * LOW_FORKS_PER_1K:
        out.append("few-forks")
    if mom["source"] == "measured" and stars and mom["gained"] >= stars * SPIKE_RATIO:
        out.append("star-spike")
    return out


def _candidate(repo: dict, bucket: str, topic: str, cfg: dict, today: dt.date, hist: dict | None) -> dict:
    mom = momentum(repo, today, hist)
    age = _days(repo.get("created_at", "1970-01-01T00:00:00Z"), today)
    return {"full_name": repo["full_name"], "bucket": bucket, "topic": topic, "score": score(repo, today, hist),
            "rising": age <= int(cfg["rising"]["created_within_days"]), "velocity": mom, "flags": flags(repo, mom), "repo": repo}


def candidates(gh, cfg: dict, seen: dict, today: dt.date, hist: dict | None = None) -> tuple[list[dict], dict]:
    """Search every bucket topic. Returns (ranked candidates, drop counts by reason).

    Two passes per topic, as in StarVelocity: "top" (the stars floor, what a plain star ranking finds) and "rising"
    (young repositories under a lower floor, which a star ranking never reaches). The Search API returns at most the
    best 1,000 hits of one query, so a single query ordered by stars would show the same classics every run.

    A page is ordered by stars, so in a busy topic the rising page can fill up with young repositories that are already
    above the stars floor and push the ones between the two floors off the page. Whenever the page is full and reaches
    above the floor, a second rising query asks for exactly that band; a quiet topic costs no extra call."""
    since = (today - dt.timedelta(days=int(cfg["max_days_since_push"]))).isoformat()
    rise = cfg["rising"]
    window = int(rise["created_within_days"])
    top_floor, rise_floor, per_page = int(cfg["min_stars"]), int(rise["min_stars"]), int(cfg["per_topic"])
    born = f" created:>={(today - dt.timedelta(days=window)).isoformat()}"
    rising_on = bool(rise["enabled"]) and int(rise["slots"]) > 0
    found: dict[str, dict] = {}
    dropped: dict[str, int] = {}

    def search(bucket_id: str, topic: str, kind: str, stars: str, floor: int, extra: str = "") -> list[dict] | None:
        query = f"topic:{topic} stars:{stars} pushed:>={since} archived:false fork:false{extra}"
        try:
            results = gh.search(query, per_page=per_page)
        except HttpError as exc:
            key = f"search failed (HTTP {exc.status})"
            dropped[key] = dropped.get(key, 0) + 1
            return None
        for repo in results:
            name = repo.get("full_name")
            if not name or name in found:
                continue
            if kind == "rising" and _days(repo.get("created_at", "1970-01-01T00:00:00Z"), today) > window:
                continue                             # the query asked for young repositories; an old one is not "rising"
            why = eligible(repo, cfg, seen, today, min_stars=floor)
            if why:
                dropped[why] = dropped.get(why, 0) + 1
                continue
            found[name] = _candidate(repo, bucket_id, topic, cfg, today, hist)
        return results

    for bucket in cfg["buckets"]:
        for topic in bucket["topics"]:
            search(bucket["id"], topic, "top", f">={top_floor}", top_floor)
            if not rising_on:
                continue
            page = search(bucket["id"], topic, "rising", f">={rise_floor}", rise_floor, born)
            if page and len(page) >= per_page and rise_floor < top_floor \
                    and max(int(r.get("stargazers_count", 0)) for r in page) >= top_floor:
                search(bucket["id"], topic, "rising", f"{rise_floor}..{top_floor - 1}", rise_floor, born)
    ranked = sorted(found.values(), key=lambda c: (-c["score"], c["full_name"]))
    return ranked, dropped


def _rotate(pool: list[dict], order: list[str], limit: int) -> list[dict]:
    """Best of each bucket in turn, in the order given, until `limit` are taken or the pool is empty."""
    queues = {b: [c for c in pool if c["bucket"] == b] for b in order}
    chosen: list[dict] = []
    while len(chosen) < limit and any(queues.values()):
        for bucket in order:
            if queues[bucket] and len(chosen) < limit:
                chosen.append(queues[bucket].pop(0))
    return chosen


def pick(ranked: list[dict], cfg: dict, today: dt.date) -> list[dict]:
    """Best of each bucket in turn, starting at a bucket that rotates with the date, so a run
    does not always open with the same domain.

    `rising.slots` (never more than half of the picks) are then filled with young, climbing repositories that the plain
    ranking did NOT pick: on stars alone they never beat an established project, and one that already wins on merit has
    been found without any help. Each takes the place of the weakest plain pick."""
    ids = [b["id"] for b in cfg["buckets"]]
    start = today.toordinal() % len(ids)
    order = ids[start:] + ids[:start]
    total = int(cfg["picks_per_run"])
    rise = cfg["rising"]
    slots = min(int(rise["slots"]), total // 2) if rise["enabled"] else 0
    plain = _rotate(ranked, order, total)
    names = {c["full_name"] for c in plain}
    # copies, flagged `slot`: "rising" only says a repository is young, `slot` says which picks really used a reserved slot
    extra = [dict(c, slot=True) for c in _rotate([c for c in ranked if c.get("rising") and c["full_name"] not in names], order, slots)]
    # weakest first; of two equal scores the later pick goes, since the rotation took it after the other
    weakest = sorted(range(len(plain)), key=lambda i: (plain[i]["score"], -i))[:len(extra)]
    return extra + [c for i, c in enumerate(plain) if i not in weakest]


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


def requested(gh, text: str, cfg: dict, seen: dict, today: dt.date, bucket: str | None = None,
              hist: dict | None = None) -> tuple[dict, list[str]]:
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
    return _candidate(repo, chosen, hit or "requested", cfg, today, hist), warnings
