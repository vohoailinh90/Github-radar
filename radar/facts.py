"""Facts about one repository: the only source of claims for everything that is written about it."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from . import readme as readmelib

PEEK_DIRS = ("src", "packages", "apps", "lib", "core", "cmd", "internal", "docs", "examples")


def clean_readme(text: str, limit: int) -> str:
    """The README without comments and images, cut to `limit` characters by whole sections (see readme.select)."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)           # images and badges
    text = re.sub(r"<img\b[^>]*>", "", text, flags=re.I)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return readmelib.select(text, limit)


def build(gh, cand: dict, cfg: dict, today: dt.date) -> dict:
    repo, name = cand["repo"], cand["full_name"]
    branch = repo.get("default_branch") or "main"
    tree = gh.tree(name, branch)
    budget = int(cfg["tree_max_entries"])
    for directory in [t.rstrip("/") for t in tree if t.endswith("/") and t.rstrip("/") in PEEK_DIRS][:4]:
        if len(tree) >= budget:
            break
        try:
            tree += gh.children(name, branch, directory)
        except Exception:  # noqa: BLE001 - a missing sub-tree must not sink the repo
            continue
    created = repo.get("created_at", "")[:10]
    languages = list(gh.languages(name))[:5]
    text = clean_readme(gh.readme(name), int(cfg["readme_max_chars"]))
    return {
        "full_name": name,
        "url": repo.get("html_url") or f"https://github.com/{name}",
        "description": (repo.get("description") or "").strip(),
        "stars": int(repo.get("stargazers_count", 0)),
        "forks": int(repo.get("forks_count", 0)),
        "open_issues": int(repo.get("open_issues_count", 0)),
        "license": (repo.get("license") or {}).get("spdx_id", ""),
        "language": repo.get("language") or (languages[0] if languages else ""),
        "languages": languages,
        "topics": list(repo.get("topics") or []),
        "created": created,
        "pushed": (repo.get("pushed_at") or "")[:10],
        "age_years": max(0, (today - dt.date.fromisoformat(created)).days // 365) if created else 0,
        "branch": branch,
        "tree": tree[:budget],
        "readme": text,
        "links": readmelib.links(text),               # [[label, url], ...]: the only addresses a guide may point to, by number
        "blocks": readmelib.blocks(text),             # [[language, text], ...]: README samples (config files...) a guide may show, by number
        "bucket": cand["bucket"],
        "topic": cand["topic"],
        "score": cand["score"],
        "scanned": today.isoformat(),
    }


def slug(full_name: str) -> str:
    """A studio-safe id (a-z, 0-9, -) for a repository."""
    return re.sub(r"[^a-z0-9]+", "-", full_name.lower().split("/")[-1]).strip("-") or "repo"


def load_seen(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_seen(path: Path, seen: dict) -> None:
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(seen, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
