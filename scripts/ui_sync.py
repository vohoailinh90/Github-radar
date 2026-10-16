#!/usr/bin/env python3
"""Keep docs/ui/index.html in step with the code it mirrors: the data block (saved presets, the base configuration, the limits of
radar/conditions.py, the costs) and the two CSP hashes (the page's one script and one style).

    python3 scripts/ui_sync.py           rewrite the page
    python3 scripts/ui_sync.py --check   exit 1 and say what differs (the test suite runs this)

The page cannot import Python, so it carries a copy of these values; this script (and its test) is what stops the copy drifting.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from radar import conditions, config  # noqa: E402

PAGE = ROOT / "docs" / "ui" / "index.html"
DEFAULT_REPO = "vohoailinh90/Github-radar"

DATA_RE = re.compile(r'(<script type="application/json" id="radar-data">)(.*?)(</script>)', re.S)
SCRIPT_RE = re.compile(r"<script>(.*?)</script>", re.S)
STYLE_RE = re.compile(r"<style>(.*?)</style>", re.S)


def sha256(text: str) -> str:
    return "sha256-" + base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode()


def data() -> dict:
    cfg = config.load(path=ROOT / "radar.yaml", env={})
    return {"defaultRepo": DEFAULT_REPO, "schema": conditions.schema(), "base": conditions.resolved(cfg),
            "costs": {"pace_seconds": cfg["pace_seconds"], "search_interval_seconds": cfg["search_interval_seconds"]},
            "emoji": {b["id"]: b.get("emoji", "") for b in cfg["buckets"]},
            "presets": conditions.load_presets()}


def data_text() -> str:
    # `<` is escaped so no value can ever close the script element; the result is still plain JSON
    return json.dumps(data(), ensure_ascii=False, indent=1).replace("<", "\\u003c")


def synced(html: str) -> str:
    """The page with the data block and both hashes brought up to date."""
    html = DATA_RE.sub(lambda m: m.group(1) + "\n" + data_text() + "\n" + m.group(3), html, count=1)
    script, style = SCRIPT_RE.search(html), STYLE_RE.search(html)
    if not script or not style:
        raise ValueError("the page needs exactly one <script> and one <style> block")
    html = re.sub(r"script-src 'sha256-[^']*'", f"script-src '{sha256(script.group(1))}'", html, count=1)
    return re.sub(r"style-src 'sha256-[^']*'", f"style-src '{sha256(style.group(1))}'", html, count=1)


def main(argv: list[str]) -> int:
    html = PAGE.read_text(encoding="utf-8")
    fresh = synced(html)
    if "--check" in argv:
        if fresh != html:
            print("docs/ui/index.html is out of step with radar.yaml, radar/presets.json or radar/conditions.py: run python3 scripts/ui_sync.py")
            return 1
        print("docs/ui/index.html is in step")
        return 0
    PAGE.write_text(fresh, encoding="utf-8")
    print("docs/ui/index.html updated" if fresh != html else "docs/ui/index.html already in step")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
