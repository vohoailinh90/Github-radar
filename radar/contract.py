"""The slice of tool-marketing-studio's rules that a bundle must satisfy, vendored as a snapshot.

`contracts/studio-layouts.json` is generated from the studio's own tables by
`scripts/studio_contract.py snapshot <studio checkout>`, and `scripts/studio_contract.py verify`
runs the real `studio.py check` on a bundle. This module is the fast, offline version used by
the tests and by every run before a bundle is written.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from . import urls

CONTRACT = Path(__file__).resolve().parent.parent / "contracts" / "studio-layouts.json"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
LINK_FIELDS = {("facebook", "first_comment")}


def load(path: Path = CONTRACT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)


def validate(files: dict[str, str], contract: dict | None = None) -> list[str]:
    """Error strings; an empty list means the studio would accept the bundle."""
    c = contract or load()
    errors: list[str] = []
    parsed = {}
    for path, text in files.items():
        try:
            parsed[path] = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            errors.append(f"{path}: invalid YAML: {exc}")
    campaigns = {p: d for p, d in parsed.items() if p.endswith("/campaign.yaml")}
    if not campaigns:
        return errors + ["no campaign.yaml in the bundle"]
    for camp_path, camp in campaigns.items():
        errors += _campaign(camp_path, camp or {}, parsed, c)
    return errors


def _campaign(camp_path: str, camp: dict, parsed: dict, c: dict) -> list[str]:
    errors: list[str] = []
    root = camp_path.rsplit("/", 1)[0]
    for key in ("tool", "langs", "platforms", "goal"):
        if not camp.get(key):
            errors.append(f"{camp_path}: missing '{key}'")
    for lang in camp.get("langs", []):
        if lang not in c["langs"]:
            errors.append(f"{camp_path}: unknown language {lang!r}")
    for platform in camp.get("platforms", []):
        if platform not in c["platforms"]:
            errors.append(f"{camp_path}: unknown platform {platform!r}")
    for name, url in (camp.get("links") or {}).items():
        if not re.match(r"^https?://\S+$", str(url)):
            errors.append(f"{camp_path}: links.{name} must be an http(s) URL")
    brief = parsed.get(f"tools/{camp.get('tool')}/brief.yaml") or {}
    for key in ("slug", "name", "status"):
        if not brief.get(key):
            errors.append(f"brief: missing '{key}'")
    if brief.get("status") not in c["tool_statuses"]:
        errors.append(f"brief: status must be one of {c['tool_statuses']}")
    if not HEX.match(str((brief.get("brand") or {}).get("accent", ""))):
        errors.append("brief: brand.accent must be #rrggbb")
    posts = {p: d for p, d in parsed.items() if p.startswith(root + "/posts/")}
    if not posts:
        errors.append(f"{camp_path}: no posts")
    for path, post in posts.items():
        errors += _post(path, post or {}, camp, c)
    return errors


def _post(path: str, post: dict, camp: dict, c: dict) -> list[str]:
    e: list[str] = []
    pid = path.rsplit("/", 1)[1][:-5]
    if not SLUG.match(pid):
        e.append(f"{path}: file name must use a-z, 0-9 and - only")
    if post.get("id") not in (None, pid):
        e.append(f"{path}: id differs from the file name")
    for key in post:
        if key not in c["post_keys"]:
            e.append(f"{path}: unknown key {key!r}")
    if post.get("status") not in c["post_statuses"]:
        e.append(f"{path}: bad status")
    if post.get("format", "portrait") not in c["formats"]:
        e.append(f"{path}: bad format")
    slides = post.get("slides") or []
    if not slides or len(slides) > c["max_slides"]:
        e.append(f"{path}: needs 1-{c['max_slides']} slides, has {len(slides)}")
    for text in strings({k: post.get(k) for k in ("series", "slides", "platforms")}):
        if urls.has_url(text):
            e.append(f"{path}: a URL or domain is written into the post: {text[:60]!r}")
    if any("{link}" in t for t in strings({k: post.get(k) for k in ("series", "slides")})):
        e.append(f"{path}: {{link}} cannot go on an image")
    for i, slide in enumerate(slides, 1):
        name = slide.get("layout") if isinstance(slide, dict) else None
        if name not in c["layouts"]:
            e.append(f"{path} slide {i}: unknown layout {name!r}")
            continue
        spec = c["layouts"][name]
        for key in spec["required"]:
            if slide.get(key) in (None, "", [], {}):
                e.append(f"{path} slide {i}: layout {name!r} needs {key!r}")
        for key in slide:
            if key != "layout" and key not in spec["fields"]:
                e.append(f"{path} slide {i}: layout {name!r} has no field {key!r}")
        for key, kind in (("tone", "tone"), ("variant", "variant"), ("style", "style")):
            if key in slide and slide[key] not in c["enums"][kind]:
                e.append(f"{path} slide {i}: {key} must be one of {c['enums'][kind]}")
    for platform, spec in (post.get("platforms") or {}).items():
        rules = c["platforms"].get(platform)
        if rules is None or not isinstance(spec, dict):
            e.append(f"{path}: bad platform {platform!r}")
            continue
        for key in rules["required"]:
            if not spec.get(key):
                e.append(f"{path} {platform}: needs {key!r}")
        for key, value in spec.items():
            if (platform, key) not in LINK_FIELDS and any("{link}" in t for t in strings(value)):
                e.append(f"{path} {platform}: {{link}} is not allowed in {key}")
        caption = str(spec.get("caption") or "")
        if len(caption) > rules.get("caption_limit", 10 ** 9):
            e.append(f"{path} {platform}: caption too long")
        if platform == "facebook" and len(caption.strip().split("\n", 1)[0]) > c["hook_limit"]:
            e.append(f"{path}: Facebook hook over {c['hook_limit']} characters")
    target = post.get("link", "survey")
    if target and target not in (camp.get("links") or {}):
        e.append(f"{path}: link {target!r} is not defined in campaign links")
    return e
