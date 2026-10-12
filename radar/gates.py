"""Deterministic checks on a draft. A model can be wrong; these cannot, so they decide.

The same shape of rules the studio applies to a post (numbers must exist in the facts, no URLs,
hook length) plus what only this pipeline needs: every explanation cites evidence that exists in
the repository, and every command to run appears verbatim in the README.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
TLDS = ("com|org|net|io|ai|dev|app|sh|co|me|xyz|gg|to|so|cloud|tech|vn|jp|info|page|run|tools|site|"
        "online|chat|edu|gov|us|uk|de|fr|cn|ru|in|tv|fm|ly|im|sc|cc")
URL = re.compile(r"(?i)(?:https?\s*:\s*//|\bwww\.|(?<![\w-])[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:" + TLDS + r")(?![\w-]))")
HYPE = {
    "en": ["best ever", "#1", "number one", "revolutionary", "game-changer", "guaranteed", "100%", "world's best"],
    "vi": ["số 1", "số một", "tốt nhất thế giới", "cách mạng", "đảm bảo 100", "100%", "tuyệt đối", "thần thánh"],
    "ja": ["世界一", "最強", "革命的", "絶対", "100%", "間違いなく最高"],
}
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


def norm_numbers(text: str) -> set[str]:
    return {re.sub(r"[.,]", "", t) for t in NUMBER.findall(text)}


def allowed_numbers(facts: dict) -> set[str]:
    """Every number the facts state, plus the ways a writer may round or abbreviate a count."""
    blob = " ".join([facts["description"], facts["readme"], " ".join(facts["tree"]), " ".join(facts["topics"]),
                     facts["created"], facts["pushed"], facts["license"], facts["language"]])
    found = norm_numbers(blob) | {str(n) for n in range(0, 11)}
    for key in ("stars", "forks", "open_issues"):
        value = int(facts[key])
        found |= {str(value), str(round(value / 1000)), f"{value / 1000:.1f}".replace(".", "")}
    found.add(str(facts["age_years"]))
    return found


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


def _evidence_ok(evidence: str, tree: list[str]) -> bool:
    ev = str(evidence).strip().strip("`").lstrip("./").rstrip("/")
    if ev.lower().startswith("readme"):
        return True
    entries = [t.rstrip("/") for t in tree]
    return any(e == ev or e.startswith(ev + "/") for e in entries)


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
    allowed = allowed_numbers(facts)
    for field, text in texts(draft):
        if URL.search(text):
            problems.append(Problem("error", field, "contains a URL or domain; links are added by the renderer"))
        bad = sorted(norm_numbers(text) - allowed)
        if bad:
            problems.append(Problem("error", field, f"numbers not in the facts: {', '.join(bad)}"))
        low = text.lower()
        for word in HYPE.get(lang, []):
            if word in low:
                problems.append(Problem("error", field, f"hype wording '{word}'"))
    hiw = draft.get("how_it_works") or {}
    for key in ("steps", "components"):
        for i, item in enumerate(hiw.get(key) or []):
            if isinstance(item, dict) and item.get("evidence") and not _evidence_ok(item["evidence"], facts["tree"]):
                problems.append(Problem("error", f"{key}[{i}]", f"evidence {item['evidence']!r} is not README or a path in the repository"))
    readme = re.sub(r"\s+", " ", facts["readme"])
    for cmd in (draft.get("try_it") or {}).get("commands") or []:
        shown = re.sub(r"\s+", " ", str(cmd)).strip().lstrip("$ ").strip()
        if not shown or shown not in readme:
            problems.append(Problem("error", "try_it.commands", f"command not found verbatim in the README: {cmd!r}"))
    if not language_ok(draft, lang):
        problems.append(Problem("error", "language", f"text does not look like '{lang}'"))
    return problems


def errors(problems) -> list[Problem]:
    return [p for p in problems if p.level == "error"]
