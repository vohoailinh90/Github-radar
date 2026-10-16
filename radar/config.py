"""radar.yaml, with defaults, plus the few environment overrides a scheduled run needs."""

from __future__ import annotations

import copy
import os
from pathlib import Path

import yaml

from . import conditions

ROOT = Path(__file__).resolve().parent.parent
LANGS = conditions.LANGS

DEFAULTS = {
    "scan_label": None,             # set by load(): the preset (or "custom") whose conditions this scan runs with; recorded in the run report
    "langs": ["vi"],
    "picks_per_run": 3,
    "min_stars": 1500,
    "max_days_since_push": 120,
    "per_topic": 15,
    # A second search per topic for young repositories under a lower stars floor, and the share of picks reserved for young
    # repositories (any stars) that the plain ranking did not pick (never more than half). 0 slots switches the pass off. See docs/research.md.
    "rising": {"enabled": True, "slots": 1, "created_within_days": 120, "min_stars": 300},
    "history_days": 60,             # star snapshots older than this are dropped from state/stars.json
    "search_interval_seconds": 2.1,  # gap between Search API calls: its limit is 30 a minute, with a stricter hidden one on bursts
    # SPDX ids (lower case). "Free" here means a licence anyone may use without paying.
    "licenses": ["mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "mpl-2.0", "gpl-2.0",
                 "gpl-3.0", "lgpl-2.1", "lgpl-3.0", "agpl-3.0", "unlicense", "0bsd", "cc0-1.0"],
    "buckets": [
        {"id": "ai", "emoji": "🤖", "topics": ["llm", "ai-agents", "rag", "machine-learning"]},
        {"id": "software", "emoji": "🧰", "topics": ["developer-tools", "self-hosted", "cli", "productivity"]},
        {"id": "solutions", "emoji": "🧩", "topics": ["automation", "workflow", "open-source-alternative", "low-code"]},
        {"id": "startup", "emoji": "🚀", "topics": ["saas", "startup", "boilerplate", "indie-hacker"]},
    ],
    "models": {
        # First is the primary. Fallbacks matter: a free model returns 503 "high demand" or stalls now and then.
        "writer": ["google/gemini-flash-latest", "google/gemini-flash-lite-latest", "groq/openai/gpt-oss-120b", "mistral/mistral-small-2603"],
        "checker": ["groq/openai/gpt-oss-120b", "groq/openai/gpt-oss-20b", "mistral/mistral-small-2603", "google/gemini-flash-lite-latest"],
    },
    "pace_seconds": 45,
    "max_run_minutes": 35,       # stop starting work after this: the workflow job is killed at 60 minutes and would lose everything
    # The checker re-sends it with the draft (about 7-8.5k tokens a request at 12,000 characters, 5.5-6.5k at 8,000). Mistral's cap is
    # 20,000 tokens/minute; Groq's (the checker used now) is NOT measured: if models_log shows 429s from it, lower this (docs/models.md).
    # 12,000 (was 8,000) because a long README often puts its Quick Start just past 8,000 (crisng95/flowkit: character 8,220).
    "readme_max_chars": 12000,
    "tree_max_entries": 120,
    "studio": {"tool": "github-radar", "name": "GitHub Radar", "accent": "#0ea5e9", "platforms": ["facebook"]},
}


def deep_merge(base: dict, extra: dict) -> dict:
    out = dict(base)
    for key, value in extra.items():
        out[key] = deep_merge(out[key], value) if isinstance(value, dict) and isinstance(out.get(key), dict) else value
    return out


def load(path: Path | None = None, env: dict | None = None) -> dict:
    env = os.environ if env is None else env
    path = path or ROOT / "radar.yaml"
    cfg = copy.deepcopy(DEFAULTS)                    # a copy all the way down: the overrides below must never change DEFAULTS
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"{path}: expected a mapping at the top level")
        cfg = copy.deepcopy(deep_merge(DEFAULTS, data))
    # One scan's conditions (RADAR_PRESET / RADAR_CONDITIONS, see radar/conditions.py): ONE layer over the file. They are
    # checked before they are applied, and the result is validated once, after the explicit variables below.
    overrides, label = conditions.from_env(env, [b["id"] for b in cfg["buckets"]])
    if overrides:
        cfg = conditions.apply(cfg, overrides)
    cfg["scan_label"] = label
    # The explicit variables are more specific than a preset and win over it: RADAR_LANGS=vi,en  RADAR_PICKS=2
    # RADAR_SEARCH_INTERVAL=0  RADAR_MODELS_WRITER="google/x mistral/y"
    if env.get("RADAR_LANGS"):
        cfg["langs"] = [x for x in env["RADAR_LANGS"].replace(",", " ").split() if x]
    if env.get("RADAR_PICKS"):
        cfg["picks_per_run"] = int(env["RADAR_PICKS"])
    if env.get("RADAR_SEARCH_INTERVAL"):
        cfg["search_interval_seconds"] = float(env["RADAR_SEARCH_INTERVAL"])
    for role in ("writer", "checker"):
        if env.get(f"RADAR_MODELS_{role.upper()}"):
            cfg["models"][role] = env[f"RADAR_MODELS_{role.upper()}"].replace(",", " ").split()
    validate(cfg)
    return cfg


def validate(cfg: dict) -> None:
    bad = [lang for lang in cfg["langs"] if lang not in LANGS]
    if bad or not cfg["langs"]:
        raise ValueError(f"langs must be a non-empty subset of {list(LANGS)}, got {cfg['langs']}")
    if not 1 <= int(cfg["picks_per_run"]) <= 10:
        raise ValueError("picks_per_run must be between 1 and 10")
    if float(cfg["max_run_minutes"]) <= 0:
        raise ValueError("max_run_minutes must be positive")
    rise = cfg["rising"]
    if not 0 <= int(rise["slots"]) <= int(cfg["picks_per_run"]) or int(rise["created_within_days"]) < 1 or int(rise["min_stars"]) < 0:
        raise ValueError("rising needs slots between 0 and picks_per_run, created_within_days >= 1 and min_stars >= 0")
    if int(cfg["history_days"]) < 21:
        raise ValueError("history_days must be at least 21: velocity compares today with a snapshot up to 21 days old")
    if float(cfg["search_interval_seconds"]) < 0:
        raise ValueError("search_interval_seconds cannot be negative")
    for bucket in cfg["buckets"]:
        if not bucket.get("id") or not bucket.get("topics"):
            raise ValueError("every bucket needs an id and at least one topic")
        # a topic is pasted into the search query (`topic:{topic}`): anything GitHub itself would not accept as a topic could add a qualifier
        if not conditions.BUCKET_ID.fullmatch(str(bucket["id"])) or any(not isinstance(t, str) or not conditions.TOPIC.fullmatch(t) for t in bucket["topics"]):
            raise ValueError(f"bucket {str(bucket['id'])[:20]!r}: an id or a topic that GitHub would not accept (a topic is lower case letters, digits and hyphens)")
    for role in ("writer", "checker"):
        if not cfg["models"].get(role):
            raise ValueError(f"models.{role} must list at least one <provider>/<model>")
