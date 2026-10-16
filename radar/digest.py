"""The learning digest: Markdown for reading on GitHub, with the SVG diagrams beside it."""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import excalidraw, moda, svg
from .facts import slug
from .labels import L


def _md(text) -> str:
    """One line, with a leading block marker (`#`, `>`, `-`, `1.`) defused, so a field cannot become a heading or a list."""
    line = re.sub(r"\s+", " ", str(text)).strip()
    return re.sub(r"^([#>*+\-]|\d+[.)])", r"\\\1", line)


def _cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


# The few facts every renderer reads; the README and the file tree are not needed to draw a digest again.
META_KEYS = ("full_name", "url", "stars", "forks", "license", "language", "bucket", "scanned")


def repo_dir(root: Path, date: str, facts: dict) -> Path:
    return root / "digests" / date / slug(facts["full_name"])


def render_repo(root: Path, date: str, facts: dict, drafts: dict[str, dict], position: int | None = None,
                note: str | None = None) -> list[Path]:
    """Write <date>/<repo>/<lang>.md plus card/flow/steps SVGs per language. Returns the files."""
    out = repo_dir(root, date, facts)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for lang, draft in drafts.items():
        t = L[lang]
        hiw = draft["how_it_works"]
        files = {
            f"card-{lang}.svg": svg.card(facts, draft, t),
            f"flow-{lang}.svg": svg.flow(hiw["components"], hiw["flow"], t["how"]),
            f"steps-{lang}.svg": svg.steps(hiw["steps"], t["how"]),
            # The same digest as files for two editors, drawn by script from the draft: open the board at excalidraw.com, or apply
            # the markup to a Moda canvas from a Claude session (docs/design-files.md). Neither is linked from the Markdown.
            f"board-{lang}.excalidraw": excalidraw.board(facts, draft, t),
            f"moda-{lang}.xml": moda.markup(facts, draft, t, lang),
        }
        # The draft is the model's answer after the gates: with it the digest, the diagrams and the studio posts can be drawn
        # again whenever the renderer improves (`radar.py rerender`), without asking a model or GitHub for anything.
        stored = {"lang": lang, "position": position, "facts": {k: facts[k] for k in META_KEYS}, "draft": draft}
        if note:
            stored["note"] = note        # e.g. "RECONSTRUCTED: ..." - a draft that is not the model's original answer says so here
        files[f"draft-{lang}.json"] = json.dumps(stored, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        for name, content in files.items():
            (out / name).write_text(content, encoding="utf-8")
            written.append(out / name)
        md = [f"# {_md(draft['title'])}", "", f"![{_cell(draft['title'])}](card-{lang}.svg)", "",
              f"> {_md(draft['hook'])}", "", f"**{_md(draft['one_liner'])}**", "",
              f"## {t['problem']}", "", _md(draft["problem"]), "",
              f"> 💡 **{t['analogy']}:** {_md(draft['analogy'])}", "",
              f"## {t['how']}", "", f"![{t['how']}](flow-{lang}.svg)", "", f"![{t['how']}](steps-{lang}.svg)", ""]
        for i, step in enumerate(hiw["steps"], 1):
            md.append(f"{i}. **{_md(step['title'])}**: {_md(step['text'])} _({t['evidence']}: `{_cell(step['evidence'])}`)_")
        md += ["", f"## {t['parts']}", "", f"| | {t['parts']} | {t['evidence']} |", "|---|---|---|"]
        md += [f"| **{_cell(c['name'])}** | {_cell(c['role'])} | `{_cell(c['evidence'])}` |" for c in hiw["components"]]
        md += ["", f"## {t['learn']}", ""] + [f"- {_md(x)}" for x in draft["learn"]]
        md += ["", f"## {t['who']}", ""] + [f"- {_md(x)}" for x in draft["who_for"]]
        md += ["", f"## {t['try']}", ""]
        cmds = draft["try_it"]["commands"]
        md += (["```bash"] + [re.sub(r"\s+", " ", str(c)).lstrip("$ ").strip() for c in cmds] + ["```"]) if cmds else [t["no_cmd"]]
        if draft["try_it"].get("note"):
            md += ["", _md(draft["try_it"]["note"])]
        md += ["", f"## {t['caveats']}", ""] + [f"- {_md(x)}" for x in draft["caveats"]]
        if draft["glossary"]:
            md += ["", f"## {t['glossary']}", ""] + [f"- **{_md(g['term'])}**: {_md(g['meaning'])}" for g in draft["glossary"]]
        md += ["", "---", "",
               f"{t['source']}: [{facts['full_name']}]({facts['url']}) · {t['license']}: {facts['license']} · "
               f"{svg.fmt_int(facts['stars'], t['sep'])} {t['stars']} · {t['scanned']} {facts['scanned']}", "", f"_{t['disclaimer']}_", ""]
        path = out / f"{lang}.md"
        path.write_text("\n".join(md), encoding="utf-8")
        written.append(path)
    return written


def render_index(root: Path, date: str, entries: list[dict], lang: str) -> list[Path]:
    """<date>/README.md: the list of this scan's repositories and a stars chart."""
    t = L[lang]
    folder = root / "digests" / date
    folder.mkdir(parents=True, exist_ok=True)
    chart = folder / "stars.svg"
    chart.write_text(svg.bars([(e["facts"]["full_name"], e["facts"]["stars"]) for e in entries], t["stars_chart"], t["sep"]),
                     encoding="utf-8")
    md = [f"# {t['radar_title']} · {date}", "", f"![{t['stars_chart']}](stars.svg)", "", f"## {t['picks']}", ""]
    for e in entries:
        f, d = e["facts"], e["drafts"].get(lang) or next(iter(e["drafts"].values()))
        md.append(f"- **[{d['title']}]({slug(f['full_name'])}/{lang if lang in e['drafts'] else next(iter(e['drafts']))}.md)** "
                  f"({t['bucket'][f['bucket']]}) — {d['one_liner']}")
    md.append("")
    index = folder / "README.md"
    index.write_text("\n".join(md), encoding="utf-8")
    return [chart, index]


def render_global_index(root: Path) -> Path:
    """digests/INDEX.md, rebuilt from the folders that exist: newest first."""
    base = root / "digests"
    base.mkdir(exist_ok=True)
    lines = ["# Digests", ""]
    for day in sorted((p for p in base.iterdir() if p.is_dir()), reverse=True):
        lines.append(f"- [{day.name}]({day.name}/README.md) — {', '.join(sorted(p.name for p in day.iterdir() if p.is_dir()))}")
    path = base / "INDEX.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
