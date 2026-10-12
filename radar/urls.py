"""Link detection with the studio's own rules, so a draft this repository accepts cannot be rejected by `studio.py check`.

`contracts/tlds.txt` is a copy of the studio's `mkt/tlds.txt` (refreshed by scripts/studio_contract.py snapshot) and the
pattern below is the studio's: a scheme (also hxxp and with spaces), `www.`, a bare domain ending in any real TLD, or a
domain followed by a path. Text is normalised first (NFKC, zero-width characters removed, `[.]` and `。` between letters
read as a dot), because the obvious ways to hide a link are exactly those.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

TLD_FILE = Path(__file__).resolve().parent.parent / "contracts" / "tlds.txt"


def trie_pattern(words) -> str:
    tree: dict = {}
    for word in words:
        node = tree
        for char in word:
            node = node.setdefault(char, {})
        node[""] = {}

    def walk(node: dict) -> str:
        alts = [re.escape(char) + walk(child) for char, child in sorted(node.items()) if char]
        if not alts:
            return ""
        group = alts[0] if len(alts) == 1 else "(?:" + "|".join(alts) + ")"
        return f"(?:{group})?" if "" in node else group
    return walk(tree)


TLDS = {w for line in TLD_FILE.read_text(encoding="utf-8").splitlines() if not line.startswith("#") for w in line.split()}
START, LABEL, MORE = r"(?<![a-z0-9-])", r"[a-z0-9-]{1,63}", r"(?:\.[a-z0-9-]{1,63}){0,10}"
END = r"(?![a-z0-9À-ɏ̀-ͯḀ-ỿ-])"
URL = re.compile(
    r"(?i)(?:" + START + r"h[tx]{2}ps?\s*:\s*//|" + START + r"www\.|"
    + START + r"[a-z0-9][a-z0-9-]{0,62}" + MORE + r"\.(?:" + trie_pattern(TLDS) + r")" + END + r"|"
    + START + LABEL + MORE + r"\.[a-z]{2,}/[\w/%-])")
# Not links the studio looks for, but never wanted in generated text: script-ish schemes and markdown link syntax.
INJECTION = re.compile(r"(?i)\b(?:javascript|data|vbscript)\s*:|\]\s*\(|<\s*/?\s*(?:script|iframe|img|a)\b")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text))
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    text = re.sub(r"[\[({]\s*\.\s*[\])}]", ".", text)
    return re.sub(r"(?<=[A-Za-z0-9])。(?=[A-Za-z])", ".", text)


def has_url(text: str) -> bool:
    return bool(URL.search(unicodedata.normalize("NFKC", text)))


def find(text: str, allow: frozenset[str] | set[str] = frozenset()) -> list[str]:
    """Link-like snippets in `text`. A bare token that is the name of a file in the repository is allowed (`planner.py`)."""
    norm = normalize(text)
    hits = [m.group(0) for m in URL.finditer(norm) if m.group(0).lower() not in allow]
    return hits + [m.group(0) for m in INJECTION.finditer(norm)]


def strip_domains(text: str) -> str:
    """For studio posts: `planner.py` -> `planner`, a real URL -> nothing. The studio forbids both, and meaning survives."""
    def repl(m: re.Match) -> str:
        s = m.group(0)
        return "" if re.match(r"(?i)h[tx]{2}ps?|www\.", s) or "/" in s else s.rsplit(".", 1)[0]
    text = re.sub(r"(?i)(?:h[tx]{2}ps?\s*:\s*//|www\.)\S*", "", text)
    return re.sub(r"[ \t]{2,}", " ", URL.sub(repl, text)).strip()
