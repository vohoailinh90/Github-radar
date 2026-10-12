"""The learning digest: Markdown for reading on GitHub, with the SVG diagrams beside it."""

from __future__ import annotations

from pathlib import Path

from . import svg
from .facts import slug
from .labels import L


def _cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def repo_dir(root: Path, date: str, facts: dict) -> Path:
    return root / "digests" / date / slug(facts["full_name"])


def render_repo(root: Path, date: str, facts: dict, drafts: dict[str, dict]) -> list[Path]:
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
        }
        for name, content in files.items():
            (out / name).write_text(content, encoding="utf-8")
            written.append(out / name)
        md = [f"# {draft['title']}", "", f"![{_cell(draft['title'])}](card-{lang}.svg)", "",
              f"> {draft['hook']}", "", f"**{draft['one_liner']}**", "",
              f"## {t['problem']}", "", draft["problem"], "",
              f"> 💡 **{t['analogy']}:** {draft['analogy']}", "",
              f"## {t['how']}", "", f"![{t['how']}](flow-{lang}.svg)", "", f"![{t['how']}](steps-{lang}.svg)", ""]
        for i, step in enumerate(hiw["steps"], 1):
            md.append(f"{i}. **{step['title']}**: {step['text']} _({t['evidence']}: `{step['evidence']}`)_")
        md += ["", f"## {t['parts']}", "", f"| | {t['parts']} | {t['evidence']} |", "|---|---|---|"]
        md += [f"| **{_cell(c['name'])}** | {_cell(c['role'])} | `{_cell(c['evidence'])}` |" for c in hiw["components"]]
        md += ["", f"## {t['learn']}", ""] + [f"- {x}" for x in draft["learn"]]
        md += ["", f"## {t['who']}", ""] + [f"- {x}" for x in draft["who_for"]]
        md += ["", f"## {t['try']}", ""]
        cmds = draft["try_it"]["commands"]
        md += (["```bash"] + [str(c).lstrip("$ ").strip() for c in cmds] + ["```"]) if cmds else [t["no_cmd"]]
        if draft["try_it"].get("note"):
            md += ["", draft["try_it"]["note"]]
        md += ["", f"## {t['caveats']}", ""] + [f"- {x}" for x in draft["caveats"]]
        if draft["glossary"]:
            md += ["", f"## {t['glossary']}", ""] + [f"- **{g['term']}**: {g['meaning']}" for g in draft["glossary"]]
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
