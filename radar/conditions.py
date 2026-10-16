"""Scan conditions: the part of the configuration a person may change for ONE scan, checked, applied and recorded.

They arrive from outside the code (a workflow input, a saved preset, a command-line flag), so every value is untrusted:
unknown keys, wrong types, out-of-range numbers and anything that could change the meaning of a GitHub search query
(a topic such as `llm stars:>0`) are refused before any request is made. What stays out of reach on purpose: licences,
models, the studio, the README cap and the pacing, which are the owner's content and safety rules (radar.yaml, CLAUDE.md).

No I/O here except reading the presets file; nothing is sent anywhere.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

LANGS = ("vi", "en", "ja")
PRESETS_FILE = Path(__file__).resolve().parent / "presets.json"

TOPIC = re.compile(r"[a-z0-9][a-z0-9-]{0,49}")        # GitHub's own rule for a topic: lower case, digits, hyphens, 50 characters
BUCKET_ID = re.compile(r"[a-z][a-z0-9-]{0,19}")
PRESET_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
MAX_TOPICS_PER_BUCKET = 8
MAX_JSON_CHARS = 4000

INTS = {"picks_per_run": (1, 10), "min_stars": (0, 1_000_000), "max_days_since_push": (1, 3650)}
RISING_INTS = {"slots": (0, 10), "created_within_days": (1, 1825), "min_stars": (0, 1_000_000)}
KEYS = tuple(INTS) + ("langs", "rising", "buckets")


def schema() -> dict:
    """The whole contract as plain JSON, so a front end can be checked against it (tests/test_conditions.py)."""
    return {"ints": {k: list(v) for k, v in INTS.items()}, "rising_ints": {k: list(v) for k, v in RISING_INTS.items()},
            "langs": list(LANGS), "topic_pattern": TOPIC.pattern, "bucket_id_pattern": BUCKET_ID.pattern,
            "max_topics_per_bucket": MAX_TOPICS_PER_BUCKET, "max_json_chars": MAX_JSON_CHARS}


def _show(value) -> str:
    """A value for an error message: repr (no raw newline survives) and short, so an input cannot forge a log line."""
    return repr(value)[:40]


def _int(value, low: int, high: int, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a whole number, got {_show(value)}")
    if not low <= value <= high:
        raise ValueError(f"{what} must be between {low} and {high}, got {_show(value)}")
    return value


def _reject_constant(name: str):
    raise ValueError(f"{name} is not allowed in JSON")


def _no_duplicates(pairs: list) -> dict:
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {_show(key)}")
        out[key] = value
    return out


def parse_json(text: str, what: str):
    """Strict JSON: bounded size, no NaN/Infinity, no duplicate keys. The error never repeats the input."""
    if len(text) > MAX_JSON_CHARS:
        raise ValueError(f"{what} is longer than {MAX_JSON_CHARS} characters")
    try:
        return json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_no_duplicates)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{what} is not valid JSON ({exc.msg} at character {exc.pos})") from None
    except (ValueError, RecursionError) as exc:
        raise ValueError(f"{what}: {str(exc)[:80]}") from None


def sanitize(obj, bucket_ids: list[str]) -> dict:
    """The conditions as a clean dict, or ValueError. `bucket_ids` are the buckets that exist in radar.yaml."""
    if not isinstance(obj, dict):
        raise ValueError(f"conditions must be a JSON object, got {_show(obj)}")
    out: dict = {}
    for key, value in obj.items():
        if key not in KEYS:
            raise ValueError(f"unknown condition {_show(key)}; allowed: {', '.join(KEYS)}")
        if key in INTS:
            out[key] = _int(value, *INTS[key], key)
        elif key == "langs":
            if not isinstance(value, list) or not value or len(value) > len(LANGS) \
                    or any(not isinstance(v, str) or v not in LANGS for v in value) or len(set(value)) != len(value):
                raise ValueError(f"langs must be a non-empty list of distinct values from {list(LANGS)}, got {_show(value)}")
            out[key] = list(value)
        elif key == "rising":
            if not isinstance(value, dict):
                raise ValueError(f"rising must be an object, got {_show(value)}")
            rising: dict = {}
            for name, item in value.items():
                if name == "enabled":
                    if not isinstance(item, bool):
                        raise ValueError(f"rising.enabled must be true or false, got {_show(item)}")
                    rising[name] = item
                elif name in RISING_INTS:
                    rising[name] = _int(item, *RISING_INTS[name], f"rising.{name}")
                else:
                    raise ValueError(f"unknown rising condition {_show(name)}")
            out[key] = rising
        else:                                                                       # buckets: {id: [topic, ...]}
            if not isinstance(value, dict) or not value:
                raise ValueError(f"buckets must be a non-empty object of bucket id to topics, got {_show(value)}")
            buckets: dict = {}
            for bid, topics in value.items():
                if not isinstance(bid, str) or not BUCKET_ID.fullmatch(bid) or bid not in bucket_ids:
                    raise ValueError(f"unknown bucket {_show(bid)}; radar.yaml has: {', '.join(bucket_ids)}")
                if not isinstance(topics, list) or not 1 <= len(topics) <= MAX_TOPICS_PER_BUCKET:
                    raise ValueError(f"bucket {bid} needs 1 to {MAX_TOPICS_PER_BUCKET} topics")
                for topic in topics:
                    if not isinstance(topic, str) or not TOPIC.fullmatch(topic):
                        raise ValueError(f"{_show(topic)} is not a GitHub topic (lower case letters, digits and hyphens, up to 50)")
                if len(set(topics)) != len(topics):
                    raise ValueError(f"bucket {bid} lists a topic twice")
                buckets[bid] = list(topics)
            out[key] = buckets
    return out


def apply(cfg: dict, overrides: dict) -> dict:
    """A copy of `cfg` with sanitized overrides applied. It does not validate the result: the caller does that once,
    after every layer (an override can only be judged together with the explicit environment ones that follow)."""
    out = copy.deepcopy(cfg)
    for key, value in overrides.items():
        if key == "rising":
            out["rising"] = {**out["rising"], **value}
        elif key == "buckets":                                  # these buckets, in radar.yaml's order, with these topics
            out["buckets"] = [{**b, "topics": list(value[b["id"]])} for b in cfg["buckets"] if b["id"] in value]
        else:
            out[key] = copy.deepcopy(value)
    return out


def resolved(cfg: dict) -> dict:
    """The final value of every overridable condition: what a report stores, instead of a name that can change later."""
    return {"picks_per_run": cfg["picks_per_run"], "min_stars": cfg["min_stars"], "max_days_since_push": cfg["max_days_since_push"],
            "langs": list(cfg["langs"]), "rising": dict(cfg["rising"]),
            "buckets": {b["id"]: list(b["topics"]) for b in cfg["buckets"]}}


def estimate(cfg: dict) -> dict:
    """What a scan with this configuration costs, in calls and waiting time. Search is the short part; the models are the long one.

    `searches` is the least: a busy topic can add one band query. `model_calls` is the least too: a fix round adds more.
    `pace_seconds` is the pause after each written post (radar.yaml pace_seconds), the main wait besides the models' own time."""
    topics = sum(len(b["topics"]) for b in cfg["buckets"])
    passes = 2 if cfg["rising"]["enabled"] and int(cfg["rising"]["slots"]) > 0 else 1
    posts = int(cfg["picks_per_run"]) * len(cfg["langs"])
    return {"searches": topics * passes, "search_seconds": round(topics * passes * float(cfg["search_interval_seconds"])),
            "model_calls": posts * 2, "pace_seconds": max(0, posts - 1) * round(float(cfg["pace_seconds"]))}


def load_presets(path: Path | None = None) -> dict:
    """{name: {"label": str, "conditions": {...}}} from radar/presets.json, strictly parsed. Conditions are checked
    against a bucket list by `preset()`, which is what a scan uses."""
    path = path or PRESETS_FILE
    data = parse_json(path.read_text(encoding="utf-8"), path.name) if path.exists() else {"presets": {}}
    items = data.get("presets") if isinstance(data, dict) else None
    if not isinstance(items, dict):
        raise ValueError(f"{path.name}: expected an object with a 'presets' object")
    for name, item in items.items():
        if not PRESET_NAME.fullmatch(name) or not isinstance(item, dict) or set(item) != {"label", "conditions"} \
                or not isinstance(item["label"], str) or not 1 <= len(item["label"]) <= 60 or not isinstance(item["conditions"], dict):
            raise ValueError(f"{path.name}: preset {_show(name)} needs a name like 'ai-sau' and exactly a label and conditions")
    return items


def preset(name: str, bucket_ids: list[str], path: Path | None = None) -> dict:
    """The sanitized conditions of a saved preset."""
    if not isinstance(name, str) or not PRESET_NAME.fullmatch(name):
        raise ValueError(f"{_show(name)} is not a preset name")
    items = load_presets(path)
    if name not in items:
        raise ValueError(f"unknown preset {_show(name)}; saved presets: {', '.join(sorted(items)) or 'none'}")
    return sanitize(items[name]["conditions"], bucket_ids)


def from_env(env: dict, bucket_ids: list[str]) -> tuple[dict, str | None]:
    """(overrides, label) from RADAR_CONDITIONS (inline JSON) or RADAR_PRESET (a saved name). Inline conditions win over a
    preset; with both, the preset name is only the label. 'none' and an empty value mean "no preset"."""
    name = (env.get("RADAR_PRESET") or "").strip()
    name = "" if name == "none" else name
    inline = (env.get("RADAR_CONDITIONS") or "").strip()
    if inline:
        return sanitize(parse_json(inline, "RADAR_CONDITIONS"), bucket_ids), (name if PRESET_NAME.fullmatch(name) else "custom")
    if name:
        return preset(name, bucket_ids), name
    return {}, None
