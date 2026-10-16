"""Deterministic checks on a draft. A model can be wrong; these cannot, so they decide.

The same shape of rules the studio applies to a post (numbers must exist in the facts, no URLs,
hook length) plus what only this pipeline needs: every explanation cites evidence that exists in
the repository, and every command to run appears verbatim in the README.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from decimal import Decimal

from . import readme as readmelib, urls

HYPE = {
    "en": ["best ever", "#1", "number one", "revolutionary", "game changer", "guaranteed", "100%", "world's best"],
    "vi": ["game changer", "số 1", "số một", "tốt nhất thế giới", "cách mạng", "đảm bảo 100", "100%", "tuyệt đối", "thần thánh"],
    "ja": ["世界一", "最強", "革命的", "絶対", "100%", "間違いなく最高"],
}
# A number, an optional unit that scales it (15k, 15 nghìn, 1.5万, 3 million). `v2.3`, `H100`, `Qwen2.5` are names, not numbers.
UNITS = {"k": 1000, "nghìn": 1000, "ngàn": 1000, "thousand": 1000, "千": 1000, "万": 10000, "m": 10 ** 6,
         "triệu": 10 ** 6, "million": 10 ** 6, "百万": 10 ** 6}
NUM = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)*)(?:\s(nghìn|ngàn|thousand|triệu|million)\b|(百万|[kKmM万千])(?![A-Za-z]))?", re.I)
VI_MARKS = set("àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ")
LIMITS = {"title": 70, "hook": 110, "one_liner": 200, "problem": 500, "analogy": 300, "step": 220,
          "component": 160, "learn": 200, "who_for": 140, "caveat": 220, "caption": 1200}
# The how-to guide: what a person does, in order, from nothing to the project's result.
GUIDE = {"outcome": 220, "item": 80, "detail": 180, "title": 70, "why": 200, "do": 200, "command": 800, "expect": 220,
         "if_fails": 220, "verify": 220, "problem": 120, "fix": 200, "next": 160}
GUIDE_COUNTS = {"requirements": (0, 8), "steps": (1, 10), "do": (1, 4), "commands": (0, 12), "troubleshooting": (0, 5), "next": (0, 3)}


@dataclass(frozen=True)
class Problem:
    level: str      # "error" blocks the draft; "warn" is advice
    field: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.field}: {self.message}"


def interpretations(token: str, with_unit: bool = False) -> set[Decimal]:
    """`24.000` is 24000 in Vietnamese and 24 in English; `1,5` is 1.5 or 15. Accept a plain token if ANY reading is a known
    number. With a unit (`1.5k`, `15,2 nghìn`) only the decimal reading exists: `1.5k` is 1500, never 15 thousand."""
    simple = re.fullmatch(r"\d+[.,]\d+", token)
    if with_unit:
        return {Decimal(token.replace(",", "."))} if simple else {Decimal(re.sub(r"[.,]", "", token))}
    out = {Decimal(re.sub(r"[.,]", "", token))}
    if simple:
        out.add(Decimal(token.replace(",", ".")))
    return out


def scan_numbers(text: str):
    """(token, readings, multiplier or None) for every number in `text`."""
    for m in NUM.finditer(text):
        unit = (m.group(2) or m.group(3) or "").lower()
        yield m.group(0).strip(), interpretations(m.group(1), bool(unit)), UNITS.get(unit) if unit else None


def allowed_numbers(facts: dict) -> tuple[set[Decimal], list[int]]:
    """(numbers the facts state, the counts a writer may abbreviate with a unit)."""
    blob = " ".join([facts["description"], facts["readme"], " ".join(facts["tree"]), " ".join(facts["topics"]),
                     facts["created"], facts["pushed"], facts["license"], facts["language"]])
    counts = [int(facts[k]) for k in ("stars", "forks", "open_issues")]
    allowed = {Decimal(n) for n in range(0, 11)} | {Decimal(c) for c in counts} | {Decimal(int(facts["age_years"]))}
    for _, readings, mult in scan_numbers(blob):
        allowed |= {r * mult if mult else r for r in readings}
    return allowed, counts


def bad_numbers(text: str, facts: dict) -> list[str]:
    allowed, counts = allowed_numbers(facts)
    bad = []
    for token, readings, mult in scan_numbers(text):
        if mult:                              # "15k": must match a stated value, or a count within 5%
            values = {r * mult for r in readings}
            ok = bool(values & allowed) or any(abs(v - c) <= max(Decimal(c) * Decimal("0.05"), 1) for v in values for c in counts)
        else:
            ok = bool(readings & allowed)
        if not ok:
            bad.append(token)
    return bad


def _dicts(value) -> list[tuple[int, dict]]:
    """(position, item) for the objects of a list; anything else a model sent in its place is the schema's business, not a crash."""
    return [(i, v) for i, v in enumerate(value) if isinstance(v, dict)] if isinstance(value, list) else []


def _obj(value) -> dict:
    return value if isinstance(value, dict) else {}


def texts(draft: dict) -> list[tuple[str, str]]:
    """(field, text) for every string a reader will see. Written for arbitrary JSON: a model may answer with any shape."""
    out = []
    for key in ("title", "hook", "one_liner", "problem", "analogy"):
        out.append((key, str(draft.get(key, ""))))
    hiw = _obj(draft.get("how_it_works"))
    for i, s in _dicts(hiw.get("steps")):
        out += [(f"steps[{i}]", f"{s.get('title', '')} {s.get('text', '')}")]
    for i, c in _dicts(hiw.get("components")):
        out += [(f"components[{i}]", f"{c.get('name', '')} {c.get('role', '')}")]
    for key in ("who_for", "learn", "caveats"):
        value = draft.get(key)
        out += [(f"{key}[{i}]", str(t)) for i, t in enumerate(value if isinstance(value, list) else [])]
    for i, g in _dicts(draft.get("glossary")):
        out += [(f"glossary[{i}]", f"{g.get('term', '')} {g.get('meaning', '')}")]
    out += guide_texts(draft.get("guide"))
    fb = _obj(draft.get("facebook"))
    tags = fb.get("hashtags")
    out.append(("facebook.caption", str(fb.get("caption", ""))))
    out.append(("facebook.hashtags", " ".join(str(t) for t in (tags if isinstance(tags, list) else []))))
    out += [("try_it.note", str(_obj(draft.get("try_it")).get("note", "")))]
    return out


def guide_texts(guide) -> list[tuple[str, str]]:
    """(field, text) for every sentence of the guide a reader will see. The commands are not here: they have their own gate."""
    if not isinstance(guide, dict):
        return []
    out = [("guide.outcome", str(guide.get("outcome", ""))), ("guide.verify", str(guide.get("verify", "")))]
    for i, r in _dicts(guide.get("requirements")):
        out.append((f"guide.requirements[{i}]", f"{r.get('item', '')} {r.get('detail', '')}"))
    for i, s in _dicts(guide.get("steps")):
        out.append((f"guide.steps[{i}]", " ".join(str(s.get(k, "")) for k in ("title", "why", "expect", "if_fails"))))
        do = s.get("do")
        out += [(f"guide.steps[{i}].do[{j}]", str(d)) for j, d in enumerate(do if isinstance(do, list) else [])]
    for i, t in _dicts(guide.get("troubleshooting")):
        out.append((f"guide.troubleshooting[{i}]", f"{t.get('problem', '')} {t.get('fix', '')}"))
    nxt = guide.get("next")
    out += [(f"guide.next[{i}]", str(t)) for i, t in enumerate(nxt if isinstance(nxt, list) else [])]
    return out


def _list(draft, key, lo, hi, problems, field=None):
    value = draft.get(key)
    if not isinstance(value, list) or not lo <= len(value) <= hi:
        problems.append(Problem("error", field or key, f"needs {lo}-{hi} items"))
        return []
    return value


def _guide_text(value, limit, field, problems, *, required=True) -> None:
    if value is None or value == "":
        if required:
            problems.append(Problem("error", field, "missing or empty"))
    elif not isinstance(value, str) or not value.strip():
        problems.append(Problem("error", field, "must be text"))
    elif len(value) > limit:
        problems.append(Problem("error", field, f"{len(value)} chars; limit {limit}"))


def _guide_list(value, key, field, problems) -> list:
    lo, hi = GUIDE_COUNTS[key]
    if not isinstance(value, list) or not lo <= len(value) <= hi:
        problems.append(Problem("error", field, f"needs {lo}-{hi} items"))
        return []
    return value


def _link_ref_ok(value) -> bool:
    return value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 0)


REFS = (("link_ref", "links"), ("snippet_ref", "blocks"))      # a number into FACTS.<name>, or null


def _ref_problems(item: dict, field: str) -> list[Problem]:
    """The reference fields of any guide item must be a whole number or null, whether or not the renderer reads them there."""
    return [Problem("error", f"{field}.{name}", f"must be a number from FACTS.{source}, or null")
            for name, source in REFS if not _link_ref_ok(item.get(name))]


def guide_schema(guide) -> list[Problem]:
    """Shape and size of the how-to guide. Whether its commands, evidence and links are real is `check`'s job."""
    if not isinstance(guide, dict):
        return [Problem("error", "guide", "must be an object")]
    p: list[Problem] = []
    _guide_text(guide.get("outcome"), GUIDE["outcome"], "guide.outcome", p)
    _guide_text(guide.get("verify"), GUIDE["verify"], "guide.verify", p)
    for i, r in enumerate(_guide_list(guide.get("requirements"), "requirements", "guide.requirements", p)):
        field = f"guide.requirements[{i}]"
        if not isinstance(r, dict) or not r.get("evidence"):
            p.append(Problem("error", field, "needs item and evidence"))
            continue
        _guide_text(r.get("item"), GUIDE["item"], field + ".item", p)
        _guide_text(r.get("detail"), GUIDE["detail"], field + ".detail", p, required=False)
        p += _ref_problems(r, field)
    for i, s in enumerate(_guide_list(guide.get("steps"), "steps", "guide.steps", p)):
        field = f"guide.steps[{i}]"
        if not isinstance(s, dict) or not s.get("evidence"):
            p.append(Problem("error", field, "needs title, do and evidence"))
            continue
        _guide_text(s.get("title"), GUIDE["title"], field + ".title", p)
        _guide_text(s.get("why"), GUIDE["why"], field + ".why", p)
        _guide_text(s.get("expect"), GUIDE["expect"], field + ".expect", p, required=False)
        _guide_text(s.get("if_fails"), GUIDE["if_fails"], field + ".if_fails", p, required=False)
        for j, d in enumerate(_guide_list(s.get("do"), "do", field + ".do", p)):
            _guide_text(d, GUIDE["do"], f"{field}.do[{j}]", p)
        cmds = s.get("commands", [])
        for c in _guide_list(cmds, "commands", field + ".commands", p):
            if not isinstance(c, str) or len(c) > GUIDE["command"]:
                p.append(Problem("error", field + ".commands", f"each command is text up to {GUIDE['command']} chars"))
        p += _ref_problems(s, field)
    for i, t in enumerate(_guide_list(guide.get("troubleshooting", []), "troubleshooting", "guide.troubleshooting", p)):
        field = f"guide.troubleshooting[{i}]"
        if not isinstance(t, dict) or not t.get("evidence"):
            p.append(Problem("error", field, "needs problem, fix and evidence"))
            continue
        _guide_text(t.get("problem"), GUIDE["problem"], field + ".problem", p)
        _guide_text(t.get("fix"), GUIDE["fix"], field + ".fix", p)
        p += _ref_problems(t, field)
    for i, t in enumerate(_guide_list(guide.get("next", []), "next", "guide.next", p)):
        _guide_text(t, GUIDE["next"], f"guide.next[{i}]", p)
    return p


def schema(draft: dict, require_guide: bool = False) -> list[Problem]:
    """`require_guide` is for a draft being written now; a stored draft from before the guide existed still has to render."""
    p: list[Problem] = []
    for key, limit in (("title", "title"), ("hook", "hook"), ("one_liner", "one_liner"),
                       ("problem", "problem"), ("analogy", "analogy")):
        v = draft.get(key)
        if not isinstance(v, str) or not v.strip():
            p.append(Problem("error", key, "missing or empty"))
        elif len(v) > LIMITS[limit]:
            p.append(Problem("error", key, f"{len(v)} chars; limit {LIMITS[limit]}"))
    hiw = draft.get("how_it_works")
    if not isinstance(hiw, dict):
        return p + [Problem("error", "how_it_works", "missing")]
    for i, s in enumerate(_list(hiw, "steps", 3, 6, p, "how_it_works.steps")):
        if not isinstance(s, dict) or not s.get("text") or not s.get("evidence"):
            p.append(Problem("error", f"steps[{i}]", "needs text and evidence"))
        elif len(str(s["text"])) > LIMITS["step"]:
            p.append(Problem("error", f"steps[{i}]", f"text over {LIMITS['step']} chars"))
    comps = _list(hiw, "components", 2, 6, p, "how_it_works.components")
    for i, c in enumerate(comps):
        if not isinstance(c, dict) or not c.get("name") or not c.get("role") or not c.get("evidence"):
            p.append(Problem("error", f"components[{i}]", "needs name, role and evidence"))
        elif len(str(c["role"])) > LIMITS["component"] or len(str(c["name"])) > 40:
            p.append(Problem("error", f"components[{i}]", "name over 40 or role over 160 chars"))
    flow = hiw.get("flow")
    if not isinstance(flow, list) or len(flow) > 12:
        p.append(Problem("error", "flow", "must be a list of at most 12 [from, to] pairs"))
    else:
        for edge in flow:
            ok = (isinstance(edge, list) and len(edge) == 2 and all(isinstance(x, int) for x in edge)
                  and all(0 <= x < len(comps) for x in edge) and edge[0] != edge[1])
            if not ok:
                p.append(Problem("error", "flow", f"edge {edge!r} must be two different component indexes"))
    for key, lo, hi, limit in (("who_for", 2, 4, "who_for"), ("learn", 3, 5, "learn"), ("caveats", 1, 4, "caveat")):
        for i, t in enumerate(_list(draft, key, lo, hi, p)):
            if not isinstance(t, str) or not t.strip() or len(t) > LIMITS[limit]:
                p.append(Problem("error", f"{key}[{i}]", f"must be text up to {LIMITS[limit]} chars"))
    gl = draft.get("glossary")
    if not isinstance(gl, list) or len(gl) > 4 or any(not isinstance(g, dict) or not g.get("term") or not g.get("meaning") for g in gl):
        p.append(Problem("error", "glossary", "at most 4 entries with term and meaning"))
    guide = draft.get("guide")
    if guide is None and require_guide:
        p.append(Problem("error", "guide", "missing: every new draft carries the step-by-step guide"))
    elif guide is not None:
        p += guide_schema(guide)
    try_it = draft.get("try_it")
    if guide is None or try_it is not None:          # the guide replaces try_it; an older draft still has only try_it
        if not isinstance(try_it, dict) or not isinstance(try_it.get("commands"), list):
            p.append(Problem("error", "try_it", "needs commands (a list, maybe empty)"))
    fb = draft.get("facebook")
    if not isinstance(fb, dict) or not str(fb.get("caption", "")).strip():
        p.append(Problem("error", "facebook.caption", "missing"))
    else:
        caption = str(fb["caption"])
        if len(caption) > LIMITS["caption"]:
            p.append(Problem("error", "facebook.caption", f"{len(caption)} chars; limit {LIMITS['caption']}"))
        if len(caption.strip().split("\n", 1)[0]) > 125:
            p.append(Problem("error", "facebook.caption", "first line over 125 chars (Facebook folds after that)"))
        tags = fb.get("hashtags", [])
        if not isinstance(tags, list) or len(tags) > 5 or any(not re.fullmatch(r"#?\w{2,30}", str(t)) for t in tags):
            p.append(Problem("error", "facebook.hashtags", "at most 5 single words"))
    return p


def _evidence_ok(evidence: str, tree: list[str]) -> bool:
    ev = str(evidence).strip().strip("`").lstrip("./").rstrip("/").lower()
    if ev == "readme":
        return True
    entries = [t.rstrip("/").lower() for t in tree]
    return any(e == ev or e.startswith(ev + "/") for e in entries)


def _flat(text: str) -> str:
    """Case, hyphens, spacing and '100 %' vs '100%' must not decide whether hype is caught."""
    return re.sub(r"\s*%", "%", re.sub(r"[\s\-_]+", " ", text.lower()))


_norm_cmd = readmelib.norm_command


def _block_variants(readme: str):
    """(text, prompt pattern) for the logical lines of the README's code blocks (a command written over several lines is ONE line; its
    pieces are not commands; in a `console` transcript only the lines after a prompt, the rest is output). Each comes without a trailing
    `# comment` too."""
    for lang, lines in readmelib.code_blocks(readme):
        prompt = readmelib.prompt_for(lang)
        for line in lines:
            if lang in readmelib.CONSOLE_LANGS and not prompt.match(line):       # a transcript: the lines without a prompt are output
                continue
            yield line, prompt
            yield re.split(r"\s+#\s", line)[0], prompt


def _command_variants(readme: str):
    """(text, prompt pattern) for every text of the README a reader could copy as a command, as the README has it: the lines of its
    code blocks (see `_block_variants`), and outside the blocks whole lines and inline code spans. Each text also comes without a
    trailing `# comment`."""
    yield from _block_variants(readme)
    for line in (l.strip() for l in readmelib.prose_lines(readme)):
        yield line, readmelib.SHELL_PROMPT
        yield re.split(r"\s+#\s", line)[0], readmelib.SHELL_PROMPT
        yield from ((m.group(1), readmelib.SHELL_PROMPT) for m in re.finditer(r"`([^`\n]+)`", line))


def _shown(text: str, prompt) -> str:
    """`text` as it is to be shown: a leading prompt dropped and the end trimmed, the indentation and the spaces inside kept (the body of a
    heredoc or a YAML sample is indented on purpose)."""
    body = text.rstrip()
    stripped = body.lstrip()
    return body[:len(body) - len(stripped)] + prompt.sub("", stripped).strip()


def command_texts(readme: str) -> dict[str, list[str]]:
    """{comparable form: every distinct text of it in the README, in README order}. A prompt is dropped where it is one (see
    readme.prompt_for) and the ends trimmed; the spaces inside are kept. Two commands that differ only in significant spaces share a
    form and both are kept: the code blocks come first, and the comparable form is only a fallback."""
    out: dict[str, list[str]] = {}
    for text, prompt in _command_variants(readme):
        key = _norm_cmd(text)
        if key:
            shown = _shown(text, prompt)
            if shown not in out.setdefault(key, []):
                out[key].append(shown)
    return out


def block_commands(readme: str) -> set[str]:
    """The comparable form of every line of the README's code blocks: what a reader types, as opposed to a line of prose or a code
    span, where a pair of backticks is Markdown and not part of a command."""
    return {key for text, _ in _block_variants(readme) if (key := _norm_cmd(text))}


def readme_commands(readme: str) -> set[str]:
    """Whole README lines and inline-code spans: what a reader could copy from it."""
    return set(command_texts(readme))


def canonicalize(draft: dict, facts: dict) -> dict:
    """The draft with every command replaced by the README's own text of it. The gate compares commands with their spaces collapsed
    (a model may normalise them), but a guide must show the README's spaces: `sed 's/foo  bar/baz/'` is not `sed 's/foo bar/baz/'`.
    A command that is exactly one of the README's texts is left as it is, even if another text of the README normalises to the same
    form; one that is not exactly any of them becomes the first text of its form (the best guess when several share it); a command
    the README does not hold is left alone, for the gate to refuse."""
    out = copy.deepcopy(draft)
    table = command_texts(facts["readme"])
    exact = {text for texts in table.values() for text in texts}

    def fix(command):
        if not isinstance(command, str):
            return command
        if not command.strip():
            return ""                                   # a blank line of a block
        shown = _shown(command, readmelib.SHELL_PROMPT)
        return shown if shown in exact else (table.get(_norm_cmd(command)) or [command])[0]

    guide = out.get("guide")
    for _, step in _dicts(guide.get("steps") if isinstance(guide, dict) else None):
        if isinstance(step.get("commands"), list):
            step["commands"] = [fix(c) for c in step["commands"]]
    if isinstance(out.get("try_it"), dict) and isinstance(out["try_it"].get("commands"), list):
        out["try_it"]["commands"] = [fix(c) for c in out["try_it"]["commands"]]
    return out


def guide_commands(draft: dict) -> list[tuple[str, object]]:
    """(field, command) for every line a reader is told to type: the guide's steps, or an older draft's try_it."""
    out = []
    guide = _obj(draft.get("guide"))
    for i, step in _dicts(guide.get("steps")):
        cmds = step.get("commands")
        out += [(f"guide.steps[{i}].commands", c) for c in (cmds if isinstance(cmds, list) else [])]
    cmds = _obj(draft.get("try_it")).get("commands")
    out += [("try_it.commands", c) for c in (cmds if isinstance(cmds, list) else [])]
    return out


def command_coverage(draft: dict, facts: dict) -> tuple[int, int]:
    """(README command lines the draft uses, command lines the README's code blocks hold): how much of the way in it shows."""
    wanted = {_norm_cmd(c) for c in readmelib.setup_commands(facts["readme"])}
    used = {_norm_cmd(c) for _, c in guide_commands(draft) if isinstance(c, str)}
    return len(used & wanted), len(wanted)


def _backtick_problems(text: str, blob: str, paths: set[str]) -> list[str]:
    """Messages for text a model writes between backticks that does not come from the README or the repository. That text is shown
    to the reader as code to copy; a command invented inside a sentence would get past the command gate otherwise."""
    if text.count("`") % 2:
        return ["unbalanced backtick"]
    out = []
    for span in re.findall(r"`([^`\n]*)`", text):
        shown = _norm_cmd(span)
        ref = shown.strip("`").lstrip("./").rstrip("/").lower()
        if shown and shown not in blob and ref not in paths:
            out.append(f"`{span}` is shown as code but is not in the README or the repository")
    return out


def language_ok(draft: dict, lang: str) -> bool:
    text = " ".join(t for _, t in texts(draft))
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 200:
        return True
    if lang == "vi":
        return sum(c.lower() in VI_MARKS for c in letters) / len(letters) >= 0.04
    if lang == "ja":
        return sum("぀" <= c <= "ヿ" or "一" <= c <= "鿿" for c in letters) / len(letters) >= 0.3
    return sum(c.isascii() for c in letters) / len(letters) >= 0.9


def check(draft: dict, facts: dict, lang: str, require_guide: bool = False) -> list[Problem]:
    problems = schema(draft, require_guide)
    if any(p.field in ("how_it_works", "how_it_works.steps") for p in problems):
        return problems
    files = {t.rstrip("/").rsplit("/", 1)[-1].lower() for t in facts["tree"]}
    paths = {t.rstrip("/").lstrip("./").lower() for t in facts["tree"]} | files
    blob = _norm_cmd(facts["readme"])
    for field, text in texts(draft):
        problems += [Problem("error", field, message) for message in _backtick_problems(text, blob, paths)]
        for hit in urls.find(text, files):
            problems.append(Problem("error", field, f"contains a link or domain ({hit!r}); links are added by the renderer"))
        bad = bad_numbers(text, facts)
        if bad:
            problems.append(Problem("error", field, f"numbers not in the facts: {', '.join(bad)}"))
        flat = _flat(text)
        for word in HYPE.get(lang, []):
            if _flat(word) in flat:
                problems.append(Problem("error", field, f"hype wording '{word}'"))
    hiw = _obj(draft.get("how_it_works"))
    for key in ("steps", "components"):
        for i, item in _dicts(hiw.get(key)):
            if item.get("evidence") and not _evidence_ok(item["evidence"], facts["tree"]):
                problems.append(Problem("error", f"{key}[{i}]", f"evidence {item['evidence']!r} is not README or a path in the repository"))
    known, typed = readme_commands(facts["readme"]), block_commands(facts["readme"])
    for field, cmd in guide_commands(draft):
        if cmd == "":                                  # a blank line between two lines of a block (a heredoc body)
            continue
        shown = _norm_cmd(cmd)
        # a backtick is shell (command substitution) only in a line of a code block; around a span of prose it is Markdown
        if not isinstance(cmd, str) or "\n" in cmd or len(shown) < 3 or shown not in known or ("`" in shown and shown not in typed):
            problems.append(Problem("error", field, f"command is not a line or code span of the README: {cmd!r}"))
    guide = draft.get("guide")
    if isinstance(guide, dict) and not any(p.level == "error" and p.field.startswith("guide") for p in problems):
        links, blocks = len(facts.get("links") or []), len(facts.get("blocks") or [])
        for key in ("requirements", "steps", "troubleshooting"):
            for i, item in enumerate(guide.get(key) or []):
                field = f"guide.{key}[{i}]"
                if item.get("evidence") and not _evidence_ok(item["evidence"], facts["tree"]):
                    problems.append(Problem("error", field, f"evidence {item['evidence']!r} is not README or a path in the repository"))
                for name, size, source in (("link_ref", links, "links"), ("snippet_ref", blocks, "blocks")):
                    ref = item.get(name)
                    if isinstance(ref, int) and not isinstance(ref, bool) and ref >= size:
                        problems.append(Problem("error", f"{field}.{name}", f"{ref} is not an entry of FACTS.{source} (it has {size})"))
        used, wanted = command_coverage(draft, facts)
        steps = guide.get("steps")
        if wanted >= 2 and isinstance(steps, list) and len(steps) < 3:          # one or two steps only for a README with next to nothing to run
            problems.append(Problem("error", "guide.steps", f"the README shows {wanted} command lines, so the guide needs 3-10 steps "
                                    "(1-2 only when the README has fewer than 2 command lines to follow)"))
        if wanted >= 1 and used == 0:            # any README line passes the command gate; only a command of a code block counts here
            problems.append(Problem("error", "guide.steps", f"the README shows {wanted} command line{'s' if wanted != 1 else ''} but the guide uses "
                                    f"{'none of them' if wanted != 1 else 'it'}; copy the ones a reader types, in order"))
        elif wanted >= 4 and used < 2:
            problems.append(Problem("warn", "guide.steps", f"the guide uses {used} of the README's {wanted} command lines"))
    if not language_ok(draft, lang):
        problems.append(Problem("error", "language", f"text does not look like '{lang}'"))
    return problems


def errors(problems) -> list[Problem]:
    return [p for p in problems if p.level == "error"]
