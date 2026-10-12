"""radar.yaml, with defaults, plus the few environment overrides a scheduled run needs."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("vi", "en", "ja")

DEFAULTS = {
    "langs": ["vi"],
    "picks_per_run": 3,
    "min_stars": 1500,
    "max_days_since_push": 120,
    "per_topic": 15,
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
        "writer": ["google/gemini-flash-latest", "google/gemini-flash-lite-latest", "mistral/mistral-small-2603"],
        "checker": ["mistral/mistral-small-2603", "google/gemini-flash-lite-latest"],
    },
    "pace_seconds": 45,
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
    cfg = dict(DEFAULTS)
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"{path}: expected a mapping at the top level")
        cfg = deep_merge(DEFAULTS, data)
    # Scheduled runs override without editing the file: RADAR_LANGS=vi,en  RADAR_PICKS=2
    # RADAR_MODELS_WRITER="google/x mistral/y"
    if env.get("RADAR_LANGS"):
        cfg["langs"] = [x for x in env["RADAR_LANGS"].replace(",", " ").split() if x]
    if env.get("RADAR_PICKS"):
        cfg["picks_per_run"] = int(env["RADAR_PICKS"])
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
    for bucket in cfg["buckets"]:
        if not bucket.get("id") or not bucket.get("topics"):
            raise ValueError("every bucket needs an id and at least one topic")
    for role in ("writer", "checker"):
        if not cfg["models"].get(role):
            raise ValueError(f"models.{role} must list at least one <provider>/<model>")
