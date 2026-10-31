"""Which repositories a hand-written report already covers. Arithmetic on files, never a model.

A report folder under `docs/reports/` names the repositories it studied in `deck.json` (`source.repo`) and `sources.json`
(`repo`, `url`, `pinned_url`). The scan reads those, so a repository with a report is not written a second time
(CLAUDE.md "One repository, one digest"). The result is kept apart from `state/seen.json`: a report is not a digest, and
nothing here is ever written to the seen list."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPORTS_DIR = Path("docs") / "reports"
FILES = ("deck.json", "sources.json")                 # the report metadata that lists the studied repositories
_URL = re.compile(r"(?<![A-Za-z0-9.-])github\.com/([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)")   # not notgithub.com
RESERVED = {"topics", "orgs", "sponsors", "search", "marketplace", "features", "settings", "collections", "apps", "users"}   # github.com/<this>/<x> is no repository
_NAME = re.compile(r"^([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)$")


def _pair(owner: str, name: str) -> str | None:
    name = name.rstrip(".").removesuffix(".git").rstrip(".")           # "github.com/a/b." at the end of a sentence is a/b
    if owner.lower() in RESERVED or not name:
        return None
    return f"{owner}/{name}".lower()


def _names(node) -> set[str]:
    """Every `owner/name` a JSON value points at: a GitHub URL in any string, or a `repo` field written as owner/name."""
    found: set[str] = set()
    if isinstance(node, str):
        found.update(p for m in _URL.finditer(node) if (p := _pair(*m.groups())))
    elif isinstance(node, list):
        for item in node:
            found |= _names(item)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key == "repo" and isinstance(value, str) and (m := _NAME.match(value)) and (p := _pair(*m.groups())):
                found.add(p)
            found |= _names(value)
    return found


def covered(root: Path) -> dict[str, str]:
    """{lower-case owner/name: report folder} for every repository a report under `root/docs/reports` lists.

    A file that is missing or does not parse adds nothing; `tests/test_reports.py` reads the real folders, so a broken one
    fails the suite instead of silently reopening a repository."""
    out: dict[str, str] = {}
    base = root / REPORTS_DIR
    if not base.is_dir():
        return out
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        for name in FILES:
            try:
                data = json.loads((folder / name).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            for repo in _names(data):
                out.setdefault(repo, folder.name)
    return out
