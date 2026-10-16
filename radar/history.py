"""Star snapshots: one observation per repository per UTC day, so growth is measured instead of guessed.

GitHub only reports a star total. A repository's lifetime average (`stars / age`) says little about what is climbing now,
so every scan stores the totals it saw in `state/stars.json` and a later scan divides the difference by the days between.
Pure arithmetic and a JSON file: no model, no network.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

WINDOW_DAYS = 7           # the gap a measurement aims for
MIN_GAP_DAYS = 3          # scans run Wed + Sat: 3 and 4 days apart, so the second scan already measures
MAX_GAP_DAYS = 21         # older than this the number no longer says what is climbing *now*


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save(path: Path, hist: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(hist, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def record(hist: dict, name: str, day: dt.date, stars: int) -> None:
    """Today's total for `name`. Keyed by day, so a second run the same day replaces the first instead of adding a point."""
    hist.setdefault(name, {})[day.isoformat()] = int(stars)


def prune(hist: dict, today: dt.date, keep_days: int) -> None:
    cutoff = (today - dt.timedelta(days=keep_days)).isoformat()
    for name in list(hist):
        hist[name] = {d: s for d, s in hist[name].items() if d >= cutoff}
        if not hist[name]:
            del hist[name]


def velocity(hist: dict, name: str, stars: int, today: dt.date) -> dict | None:
    """Stars gained per day, from the stored observation whose age is closest to WINDOW_DAYS (within MIN..MAX_GAP_DAYS).

    The difference is divided by the real gap, so an irregular schedule does not skew it. `None` means "no usable
    observation yet", which is not the same as "gained nothing": callers must not turn it into 0."""
    best = None
    for day, old in (hist.get(name) or {}).items():
        try:
            gap = (today - dt.date.fromisoformat(day)).days
        except ValueError:
            continue
        if MIN_GAP_DAYS <= gap <= MAX_GAP_DAYS and (best is None or abs(gap - WINDOW_DAYS) < abs(best[0] - WINDOW_DAYS)):
            best = (gap, int(old))
    if best is None:
        return None
    gap, old = best
    return {"per_day": (int(stars) - old) / gap, "gap_days": gap, "gained": int(stars) - old}
