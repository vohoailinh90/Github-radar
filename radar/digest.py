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
OPTIONAL_META = ("links", "blocks", "shells")   # kept when a run found them: a guide points at them by number (older drafts have none)


def _g(text) -> str:
    """`_md` for the guide's sentences, also making `*` and `<` plain text outside code spans: a README's `1280*704` must not turn
    into emphasis and a stray `<tag>` must not reach the page as HTML."""
    parts = re.split(r"(`[^`\n]*`)", _md(text))
    return "".join(p if i % 2 else p.replace("*", "\\*").replace("<", "&lt;") for i, p in enumerate(parts))


def _link(facts: dict, ref, t: dict) -> str:
    """The README address a `link_ref` names, printed by the renderer: a local address as code, any other as a link. An entry that
    is not a plain http(s) address is left out, whatever the stored draft says."""
    links = facts.get("links") or []
    if not isinstance(ref, int) or isinstance(ref, bool) or not 0 <= ref < len(links):
        return ""
    label, url = links[ref]
    if not readmelib.url_ok(url):
        return ""
    if readmelib.is_local(url):
        return f"{t['open_addr']}: `{url}`"
    return f"{t['get_link']}: [{_cell(readmelib.clean_label(label, url))}]({url})"


def _snippet(facts: dict, ref, t: dict) -> list[str]:
    """A code block of the README (a config file, a sample) a `snippet_ref` names, exactly as the README has it."""
    blocks = facts.get("blocks") or []
    if not isinstance(ref, int) or isinstance(ref, bool) or not 0 <= ref < len(blocks):
        return []
    lang, body = blocks[ref]
    lang = lang if re.fullmatch(r"[a-z0-9+#.-]{1,16}", str(lang)) else ""
    body = str(body)
    if len(body.splitlines()) > readmelib.SNIPPET_LINES or len(body) > readmelib.SNIPPET_CHARS:
        return []
    fence = "```"
    while fence in body:
        fence += "`"
    return ["", f"_{t['snippet']}_", "", fence + lang] + body.splitlines() + [fence]


def _bash_block(commands, shell: str = "bash") -> list[str]:
    """The lines of a fenced block of `shell` (bash, powershell, bat) holding `commands`, the fence longer than any run of backticks in them."""
    lines = [str(c).rstrip() if data else _command(c) for c, data in zip(commands, readmelib.heredoc_data(commands))]       # heredoc data as it is
    fence = "```"
    while any(fence in line for line in lines):
        fence += "`"
    return [fence + shell] + lines + [fence]


def _command_blocks(facts: dict, commands, t: dict) -> list[str]:
    """The commands of a step as fenced blocks, one per run of lines for the same shell as the README writes them (FACTS.shells): a
    PowerShell line is not fenced as bash. When a step has a shell other than bash, each block says which shell it is for."""
    table = facts.get("shells") if isinstance(facts.get("shells"), dict) else {}
    groups: list[tuple[str, list]] = []
    for command, data in zip(commands, readmelib.heredoc_data(commands)):
        shell = table.get(readmelib.norm_command(command))
        shell = shell if shell in ("powershell", "bat", "fish") else "bash"
        if groups and (data or groups[-1][0] == shell or not str(command).strip()):        # a blank line and the data of a heredoc stay in the block they are in
            groups[-1][1].append(command)
        else:
            groups.append((shell, [command]))
    named = any(shell != "bash" for shell, _ in groups)
    out: list[str] = []
    for i, (shell, group) in enumerate(groups):
        out += ([""] if i else []) + ([f"_{t['shell_' + shell]}_", ""] if named else []) + _bash_block(group, shell)
    return out


def _command(text) -> str:
    """One line to type, as stored. A guide's commands are the README's own text (gates.canonicalize), so only the end is trimmed
    and a leading `$ ` or `PS C:\\>` that an older draft kept is dropped; a leading `> ` is a redirection in a shell block and stays.
    The indentation and the spaces inside are kept: the body of a heredoc, or a quoted argument such as `'s/foo  bar/baz/'`, depends on them."""
    body = str(text).rstrip()
    stripped = body.lstrip()
    return body[:len(body) - len(stripped)] + readmelib.SHELL_PROMPT.sub("", stripped).strip()


def _gcell(text) -> str:
    """A table cell holding model prose: `_g` (literal `*` and `<`), then the pipes and newlines a cell cannot hold."""
    return _cell(_g(text))


def _alt(text) -> str:
    """Image alt text without anything that could close the `![...]` or open markup."""
    return re.sub(r"[\[\]<>*_`]", "", _cell(text))


def _evidence(value, t: dict) -> str:
    return f"<sub>{t['evidence']}: `{_cell(value)}`</sub>"


def guide_markdown(facts: dict, draft: dict, lang: str, t: dict) -> list[str]:
    """The how-to document: outcome, what to prepare, a route, then every step with its commands and what to expect."""
    g, hiw = draft["guide"], draft["how_it_works"]
    md = [f"# {_g(draft['title'])}", "", f"![{_alt(draft['title'])}](card-{lang}.svg)", "",
          f"> {_g(draft['hook'])}", "", f"**{_g(draft['one_liner'])}**", "",
          f"## 🎯 {t['outcome']}", "", _g(g["outcome"]), "",
          f"## {t['problem']}", "", _g(draft["problem"]), "", f"> 💡 **{t['analogy']}:** {_g(draft['analogy'])}", "",
          f"## {t['who']}", ""] + [f"- {_g(x)}" for x in draft["who_for"]]
    md += ["", f"## ⚠️ {t['caveats']}", ""] + [f"- {_g(x)}" for x in draft["caveats"]]
    if g["requirements"]:
        md += ["", f"## 🧰 {t['before']}", "", f"_{t['tick']}_", ""]
        for r in g["requirements"]:
            line = f"- [ ] **{_g(r['item'])}**" + (f": {_g(r['detail'])}" if r.get("detail") else "")
            link = _link(facts, r.get("link_ref"), t)
            md.append(line + (f"  \n  {link}" if link else ""))
    md += ["", f"## 🗺️ {t['roadmap']}", "", f"![{t['roadmap']}](path-{lang}.svg)", "", f"## 🪜 {t['do_steps']}", ""]
    hinted = False
    for i, step in enumerate(g["steps"], 1):
        md += [f"### {t['step']} {i} · {_g(step['title'])}", "", f"**{t['why']}:** {_g(step['why'])}", ""]
        md += [f"{n}. {_g(d)}" for n, d in enumerate(step["do"], 1)]
        if step.get("commands"):
            md += [""] + ([f"_{t['type_here']}_", ""] if not hinted else []) + _command_blocks(facts, step["commands"], t)
            hinted = True
        md += _snippet(facts, step.get("snippet_ref"), t)
        link = _link(facts, step.get("link_ref"), t)
        if link:
            md += ["", f"🔗 {link}"]
        if step.get("expect"):
            md += ["", f"✅ **{t['expect']}:** {_g(step['expect'])}"]
        if step.get("if_fails"):
            md += ["", f"🩹 **{t['if_fails']}:** {_g(step['if_fails'])}"]
        md += ["", _evidence(step["evidence"], t), ""]
    md += [f"## ✔️ {t['verify']}", "", _g(g["verify"]), ""]
    if g.get("troubleshooting"):
        md += [f"## 🩹 {t['trouble']}", "", f"| {t['problem_col']} | {t['fix_col']} | {t['evidence']} |", "|---|---|---|"]
        md += [f"| {_gcell(x['problem'])} | {_gcell(x['fix'])} | `{_cell(x['evidence'])}` |" for x in g["troubleshooting"]]
        md.append("")
    if g.get("next"):
        md += [f"## 🚀 {t['next']}", ""] + [f"- {_g(x)}" for x in g["next"]] + [""]
    md += [f"## 🔍 {t['inside']}", "", f"![{t['inside']}](flow-{lang}.svg)", "", f"![{t['inside']}](steps-{lang}.svg)", ""]
    for i, step in enumerate(hiw["steps"], 1):
        md.append(f"{i}. **{_g(step['title'])}**: {_g(step['text'])} _({t['evidence']}: `{_cell(step['evidence'])}`)_")
    md += ["", f"### {t['parts']}", "", f"| | {t['parts']} | {t['evidence']} |", "|---|---|---|"]
    md += [f"| **{_gcell(c['name'])}** | {_gcell(c['role'])} | `{_cell(c['evidence'])}` |" for c in hiw["components"]]
    md += ["", f"## {t['learn']}", ""] + [f"- {_g(x)}" for x in draft["learn"]]
    if draft["glossary"]:
        md += ["", f"## {t['glossary']}", ""] + [f"- **{_g(x['term'])}**: {_g(x['meaning'])}" for x in draft["glossary"]]
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
    md += _bash_block(cmds) if cmds else [t["no_cmd"]]
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
        title, one_liner = (_g(d["title"]), _g(d["one_liner"])) if d.get("guide") else (d["title"], d["one_liner"])
        md.append(f"- **[{title}]({slug(f['full_name'])}/{lang if lang in e['drafts'] else next(iter(e['drafts']))}.md)** "
                  f"({t['bucket'][f['bucket']]}) — {one_liner}")
        if d.get("guide"):                  # what the reader ends up with, and how long the way is, before opening the guide
            md.append(f"  - 🎯 {_g(d['guide']['outcome'])} · 🪜 {len(d['guide']['steps'])} {t['steps_n']}")
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
