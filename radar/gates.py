"""Deterministic checks on a draft. A model can be wrong; these cannot, so they decide.

The same shape of rules the studio applies to a post (numbers must exist in the facts, no URLs,
hook length) plus what only this pipeline needs: every explanation cites evidence that exists in
the repository, and every command to run appears verbatim in the README.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from . import icons, urls

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


def texts(draft: dict) -> list[tuple[str, str]]:
    """(field, text) for every string a reader will see."""
    out = []
    for key in ("title", "hook", "one_liner", "problem", "analogy"):
        out.append((key, str(draft.get(key, ""))))
    hiw = draft.get("how_it_works") or {}
    for i, s in enumerate(hiw.get("steps") or []):
        out += [(f"steps[{i}]", f"{s.get('title', '')} {s.get('text', '')}")]
    for i, c in enumerate(hiw.get("components") or []):
        out += [(f"components[{i}]", f"{c.get('name', '')} {c.get('role', '')}")]
    for key in ("who_for", "learn", "caveats"):
        out += [(f"{key}[{i}]", str(t)) for i, t in enumerate(draft.get(key) or [])]
    for i, g in enumerate(draft.get("glossary") or []):
        out += [(f"glossary[{i}]", f"{g.get('term', '')} {g.get('meaning', '')}")]
    fb = draft.get("facebook") or {}
    out.append(("facebook.caption", str(fb.get("caption", ""))))
    out.append(("facebook.hashtags", " ".join(str(t) for t in fb.get("hashtags") or [])))
    out += [("try_it.note", str((draft.get("try_it") or {}).get("note", "")))]
    return out


def _list(draft, key, lo, hi, problems, field=None):
    value = draft.get(key)
    if not isinstance(value, list) or not lo <= len(value) <= hi:
        problems.append(Problem("error", field or key, f"needs {lo}-{hi} items"))
        return []
    return value


def schema(draft: dict) -> list[Problem]:
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
    # `icon` is optional (drafts stored before it existed have none), but all or none: a row of cards with one bare card looks broken.
    given = [isinstance(c, dict) and c.get("icon") not in (None, "") for c in comps]
    if any(given):
        for i, (c, has) in enumerate(zip(comps, given)):
            if not has:
                p.append(Problem("error", f"components[{i}]", "icon missing: give every component an icon, or none"))
            elif not isinstance(c["icon"], str) or c["icon"] not in icons.NAMES:
                p.append(Problem("error", f"components[{i}]", f"icon {c['icon']!r} is not one of the ICONS names"))
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
    try_it = draft.get("try_it")
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


def icon_file(draft: dict, data) -> list[Problem]:
    """Problems with an `icons-<lang>.json` placed beside a draft that predates icons: one row per component, in order, naming that
    component exactly, with an icon from the closed set. Such a file is chosen by a person or a Claude session, not by the writer
    model, so it gets the same refusal of an unknown name as a draft does, plus the check that it still belongs to its draft."""
    rows = data.get("components") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return [Problem("error", "icons", "needs a `components` list of {name, icon}")]
    comps = (draft.get("how_it_works") or {}).get("components") or []
    if len(rows) != len(comps):
        return [Problem("error", "icons", f"{len(rows)} rows for {len(comps)} components")]
    out = []
    for i, (row, comp) in enumerate(zip(rows, comps)):
        if not isinstance(row, dict) or row.get("name") != comp.get("name"):
            out.append(Problem("error", f"icons.components[{i}]", "name is not the draft's component name"))
        elif not isinstance(row.get("icon"), str) or row["icon"] not in icons.NAMES:
            out.append(Problem("error", f"icons.components[{i}]", f"icon {row.get('icon')!r} is not one of the ICONS names"))
    return out


def _evidence_ok(evidence: str, tree: list[str]) -> bool:
    ev = str(evidence).strip().strip("`").lstrip("./").rstrip("/").lower()
    if ev == "readme":
        return True
    entries = [t.rstrip("/").lower() for t in tree]
    return any(e == ev or e.startswith(ev + "/") for e in entries)


def _flat(text: str) -> str:
    """Case, hyphens, spacing and '100 %' vs '100%' must not decide whether hype is caught."""
    return re.sub(r"\s*%", "%", re.sub(r"[\s\-_]+", " ", text.lower()))


def _norm_cmd(text: str) -> str:
    return re.sub(r"^(?:[$>]\s+)", "", re.sub(r"\s+", " ", str(text)).strip())


def readme_commands(readme: str) -> set[str]:
    """Whole README lines and inline-code spans: what a reader could copy from it."""
    found = set()
    for line in readme.splitlines():
        found |= {_norm_cmd(line), _norm_cmd(re.split(r"\s+#\s", line)[0])}
        found |= {_norm_cmd(m.group(1)) for m in re.finditer(r"`([^`\n]+)`", line)}
    return {c for c in found if c}


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


def check(draft: dict, facts: dict, lang: str) -> list[Problem]:
    problems = schema(draft)
    if any(p.field in ("how_it_works", "how_it_works.steps") for p in problems):
        return problems
    files = {t.rstrip("/").rsplit("/", 1)[-1].lower() for t in facts["tree"]}
    for field, text in texts(draft):
        for hit in urls.find(text, files):
            problems.append(Problem("error", field, f"contains a link or domain ({hit!r}); links are added by the renderer"))
        bad = bad_numbers(text, facts)
        if bad:
            problems.append(Problem("error", field, f"numbers not in the facts: {', '.join(bad)}"))
        flat = _flat(text)
        for word in HYPE.get(lang, []):
            if _flat(word) in flat:
                problems.append(Problem("error", field, f"hype wording '{word}'"))
    hiw = draft.get("how_it_works") or {}
    for key in ("steps", "components"):
        for i, item in enumerate(hiw.get(key) or []):
            if isinstance(item, dict) and item.get("evidence") and not _evidence_ok(item["evidence"], facts["tree"]):
                problems.append(Problem("error", f"{key}[{i}]", f"evidence {item['evidence']!r} is not README or a path in the repository"))
    known = readme_commands(facts["readme"])
    for cmd in (draft.get("try_it") or {}).get("commands") or []:
        shown = _norm_cmd(cmd)
        if not isinstance(cmd, str) or "`" in cmd or "\n" in cmd or len(shown) < 3 or shown not in known:
            problems.append(Problem("error", "try_it.commands", f"command is not a line or code span of the README: {cmd!r}"))
    if not language_ok(draft, lang):
        problems.append(Problem("error", "language", f"text does not look like '{lang}'"))
    return problems


def errors(problems) -> list[Problem]:
    return [p for p in problems if p.level == "error"]
