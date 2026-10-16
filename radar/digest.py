"""The learning digest: Markdown for reading on GitHub, with the SVG diagrams beside it."""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import readme as readmelib, svg
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
OPTIONAL_META = ("links",)       # kept when a run found them: a guide points at them by number (older drafts have none)


def _link(facts: dict, ref, t: dict) -> str:
    """The README address a `link_ref` names, printed by the renderer: a local address as code, any other as a link marked as
    taken from the README. An entry that is not a plain http(s) address is left out, whatever the stored draft says."""
    links = facts.get("links") or []
    if not isinstance(ref, int) or isinstance(ref, bool) or not 0 <= ref < len(links):
        return ""
    label, url = links[ref]
    if not readmelib.url_ok(url):
        return ""
    if readmelib.is_local(url):
        return f"{t['open_addr']}: `{url}`"
    return f"{t['get_link']}: [{_cell(readmelib.clean_label(label, url))}]({url}) _({t['from_readme']})_"


def _command(text) -> str:
    return re.sub(r"\s+", " ", str(text)).lstrip("$ ").strip()


def _evidence(value, t: dict) -> str:
    return f"<sub>{t['evidence']}: `{_cell(value)}`</sub>"


def guide_markdown(facts: dict, draft: dict, lang: str, t: dict) -> list[str]:
    """The how-to document: outcome, what to prepare, a route, then every step with its commands and what to expect."""
    g, hiw = draft["guide"], draft["how_it_works"]
    md = [f"# {_md(draft['title'])}", "", f"![{_cell(draft['title'])}](card-{lang}.svg)", "",
          f"> {_md(draft['hook'])}", "", f"**{_md(draft['one_liner'])}**", "",
          f"## 🎯 {t['outcome']}", "", _md(g["outcome"]), "",
          f"## {t['problem']}", "", _md(draft["problem"]), "", f"> 💡 **{t['analogy']}:** {_md(draft['analogy'])}", "",
          f"## {t['who']}", ""] + [f"- {_md(x)}" for x in draft["who_for"]]
    md += ["", f"## ⚠️ {t['caveats']}", ""] + [f"- {_md(x)}" for x in draft["caveats"]]
    if g["requirements"]:
        md += ["", f"## 🧰 {t['before']}", "", f"_{t['tick']}_", ""]
        for r in g["requirements"]:
            line = f"- [ ] **{_md(r['item'])}**" + (f": {_md(r['detail'])}" if r.get("detail") else "")
            link = _link(facts, r.get("link_ref"), t)
            md.append(line + (f"  \n  {link}" if link else ""))
    md += ["", f"## 🗺️ {t['roadmap']}", "", f"![{t['roadmap']}](path-{lang}.svg)", "", f"## 🪜 {t['do_steps']}", ""]
    hinted = False
    for i, step in enumerate(g["steps"], 1):
        md += [f"### {t['step']} {i} · {_md(step['title'])}", "", f"**{t['why']}:** {_md(step['why'])}", ""]
        md += [f"{n}. {_md(d)}" for n, d in enumerate(step["do"], 1)]
        if step.get("commands"):
            md += [""] + ([f"_{t['type_here']}_", ""] if not hinted else []) + ["```bash"] + [_command(c) for c in step["commands"]] + ["```"]
            hinted = True
        link = _link(facts, step.get("link_ref"), t)
        if link:
            md += ["", f"🔗 {link}"]
        if step.get("expect"):
            md += ["", f"✅ **{t['expect']}:** {_md(step['expect'])}"]
        if step.get("if_fails"):
            md += ["", f"🩹 **{t['if_fails']}:** {_md(step['if_fails'])}"]
        md += ["", _evidence(step["evidence"], t), ""]
    md += [f"## ✔️ {t['verify']}", "", _md(g["verify"]), ""]
    if g.get("troubleshooting"):
        md += [f"## 🩹 {t['trouble']}", "", f"| {t['problem_col']} | {t['fix_col']} | {t['evidence']} |", "|---|---|---|"]
        md += [f"| {_cell(x['problem'])} | {_cell(x['fix'])} | `{_cell(x['evidence'])}` |" for x in g["troubleshooting"]]
        md.append("")
    if g.get("next"):
        md += [f"## 🚀 {t['next']}", ""] + [f"- {_md(x)}" for x in g["next"]] + [""]
    md += [f"## 🔍 {t['inside']}", "", f"![{t['inside']}](flow-{lang}.svg)", "", f"![{t['inside']}](steps-{lang}.svg)", ""]
    for i, step in enumerate(hiw["steps"], 1):
        md.append(f"{i}. **{_md(step['title'])}**: {_md(step['text'])} _({t['evidence']}: `{_cell(step['evidence'])}`)_")
    md += ["", f"### {t['parts']}", "", f"| | {t['parts']} | {t['evidence']} |", "|---|---|---|"]
    md += [f"| **{_cell(c['name'])}** | {_cell(c['role'])} | `{_cell(c['evidence'])}` |" for c in hiw["components"]]
    md += ["", f"## {t['learn']}", ""] + [f"- {_md(x)}" for x in draft["learn"]]
    if draft["glossary"]:
        md += ["", f"## {t['glossary']}", ""] + [f"- **{_md(x['term'])}**: {_md(x['meaning'])}" for x in draft["glossary"]]
    return md + footer(facts, t)


def footer(facts: dict, t: dict) -> list[str]:
    return ["", "---", "",
            f"{t['source']}: [{facts['full_name']}]({facts['url']}) · {t['license']}: {facts['license']} · "
            f"{svg.fmt_int(facts['stars'], t['sep'])} {t['stars']} · {t['scanned']} {facts['scanned']}", "", f"_{t['disclaimer']}_", ""]


def concept_markdown(facts: dict, draft: dict, lang: str, t: dict) -> list[str]:
    """The explainer a draft without a guide gets (every digest written before the guide existed)."""
    hiw = draft["how_it_works"]
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
    return md + footer(facts, t)


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
        }
        if draft.get("guide"):
            files[f"path-{lang}.svg"] = svg.roadmap(draft["guide"]["steps"], t["roadmap"], draft["guide"]["outcome"], t)
        # The draft is the model's answer after the gates: with it the digest, the diagrams and the studio posts can be drawn
        # again whenever the renderer improves (`radar.py rerender`), without asking a model or GitHub for anything.
        stored = {"lang": lang, "position": position, "facts": {k: facts[k] for k in META_KEYS}, "draft": draft}
        stored["facts"].update({k: facts[k] for k in OPTIONAL_META if facts.get(k)})
        if note:
            stored["note"] = note        # e.g. "RECONSTRUCTED: ..." - a draft that is not the model's original answer says so here
        files[f"draft-{lang}.json"] = json.dumps(stored, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        for name, content in files.items():
            (out / name).write_text(content, encoding="utf-8")
            written.append(out / name)
        md = guide_markdown(facts, draft, lang, t) if draft.get("guide") else concept_markdown(facts, draft, lang, t)
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
        if d.get("guide"):                  # what the reader ends up with, and how long the way is, before opening the guide
            md.append(f"  - 🎯 {_md(d['guide']['outcome'])} · 🪜 {len(d['guide']['steps'])} {t['steps_n']}")
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
