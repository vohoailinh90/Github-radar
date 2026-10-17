"""The slide deck: a digest as a PowerPoint file (`slides-<lang>.pptx`), drawn by script from the stored draft.

Like the SVG pictures, the Excalidraw board and the Moda markup it is drawn from the stored draft and the facts only, with no model and
no network: every word on a slide is a draft field, a `labels.py` entry or a fact, and every address is `facts["url"]` or a README
address a `link_ref` names (docs/design-files.md). The layout is measured here, not by PowerPoint: a block that does not fit moves to
the next slide ("(2/3)"), so no text is cut and nothing is shrunk until it is small. The deck is the same bytes every time for the
same draft (fixed document dates and zip timestamps), so it can be drawn again and compared.

Type is large on purpose (22 pt and up for prose, 20 pt for code): the deck is read on a screen, not printed.
"""

from __future__ import annotations

import io
import json
import math
import re
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

from . import digest, gates, readme as readmelib, svg
from .labels import L

SW, SH = 960, 540                    # the slide in points: 13.333 x 7.5 in
LEFT, WIDTH = 54, 852
BOTTOM = 492                         # lowest point content may reach; the progress rail sits below
GAP = 10                             # between two blocks
COVER_TOP, COVER_BOTTOM = 116, 392   # where the copy of the cover may stand: under the badge, above the figures
SANS, SERIF, MONO = "Calibri", "Cambria", "Consolas"
EAST = {"ja": "Yu Gothic"}           # the East Asian font; Latin text keeps SANS
LH = 1.28                            # line height as a multiple of the font size, for measuring (Calibri sets 1.22)
MONO_EM = 0.62                       # width of a monospaced character as a multiple of the font size, for measuring
FIT = 1.04                           # margin on every measured line: a line is taken as 4% longer than the metrics say
BOLD = 1.03                          # Calibri Bold runs about 2.5% wider than Regular (measured on a Vietnamese sentence)
# Advance widths of Calibri in font units (2048 to the em), read from Carlito (the metric-compatible font LibreOffice draws instead) for
# the characters of Latin text. A letter with a diacritic is as wide as its base letter, except the horn letters of Vietnamese (ơ ư),
# which are listed. Anything not listed is 0.5 em. tests/test_slides.py checks the table against the font file when it is installed.
_CALIBRI = dict(zip(
    " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz",
    [463, 667, 821, 1020, 1038, 1464, 1397, 452, 621, 621, 1020, 1020, 511, 627, 517, 791,
     1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 1038, 548, 548, 1020, 1020, 1020, 949,
     1831, 1185, 1114, 1092, 1260, 1000, 941, 1292, 1276, 516, 653, 1064, 861, 1751, 1322, 1356,
     1058, 1378, 1112, 941, 998, 1314, 1162, 1822, 1063, 998, 959, 628, 791, 628, 1020, 1020,
     596, 981, 1076, 866, 1076, 1019, 625, 964, 1076, 470, 490, 931, 470, 1636, 1076, 1080,
     1076, 1076, 714, 801, 686, 1076, 925, 1464, 887, 927, 809]))
_CALIBRI.update({"·": 517, "–": 1020, "—": 1854, "…": 1414, "“": 857, "”": 857, "‘": 511, "’": 511, "đ": 1130, "Đ": 1279, "ơ": 1184, "ư": 1234, "Ơ": 1428, "Ư": 1478})
_XML_BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿\ud800-\udfff]")
RUN_SLUG = re.compile(r"\d{4}-\d{2}-\d{2}(-\d+)?")

THEMES = {
    "light": dict(bg="F3EEE3", ink="14161C", muted="6B6A66", kicker="1F3FD1", card="E8E0CF", good="D5EBDD", warn="F3DFC1",
                  code="14161C", codeink="F3EEE3", codelabel="6B6A66", inline="B02D16", link="1F3FD1", accent="E8472B",
                  num=["1F3FD1", "0F766E"], numink="FFFFFF"),
    "dark": dict(bg="12141B", ink="F3EEE3", muted="9AA0B5", kicker="7C93FF", card="1E2230", good="1E3A2E", warn="3A2C1A",
                 code="0B0C11", codeink="F3EEE3", codelabel="9AA0B5", inline="FF9A85", link="9FB2FF", accent="FF6A4D",
                 num=["7C93FF", "3DD6A0", "FFB454", "C58BFF", "FF6A4D"], numink="12141B"),
    "cobalt": dict(bg="1F3FD1", ink="FFFFFF", muted="C9D2FF", kicker="C9D2FF", card="3453E3", good="3453E3", warn="3453E3",
                   code="14161C", codeink="F3EEE3", codelabel="C9D2FF", inline="FFD6A0", link="FFFFFF", accent="FFB454",
                   num=["F3EEE3"], numink="1F3FD1"),
}


# ---------------------------------------------------------------- text: spans, measuring

def _clean(text) -> str:
    return _XML_BAD.sub("", str(text))


def _spans(text) -> list[tuple[str, bool]]:
    """A sentence as (text, is_code) pieces: a backtick span of the draft becomes its own monospaced piece, kept exactly (its spaces
    are its own); the words around it have their whitespace collapsed."""
    raw, pieces, last = _clean(text), [], 0
    for found in readmelib.CODE_SPAN.finditer(raw):
        pieces += [(re.sub(r"\s+", " ", raw[last:found.start()]), False), (found.group(2).strip(), True)]
        last = found.end()
    pieces.append((re.sub(r"\s+", " ", raw[last:]), False))
    pieces = [(s, c) for s, c in pieces if s]
    if pieces and not pieces[0][1]:
        pieces[0] = (pieces[0][0].lstrip(), False)
    if pieces and not pieces[-1][1]:
        pieces[-1] = (pieces[-1][0].rstrip(), False)
    return [(s, c) for s, c in pieces if s]


def _plain(text) -> str:
    return "".join(s for s, _ in _spans(text))


def _adv(ch: str, code: bool, size: float, bold: bool) -> float:
    """The advance of one character in points: a monospaced run is drawn 2 pt smaller than the text around it."""
    if code:
        return (size - 2) * (1.0 if svg._wide(ch) else MONO_EM)         # an East Asian glyph in a monospaced run is still about one em wide
    if svg._wide(ch):
        return size
    decomposed = unicodedata.normalize("NFD", ch)
    base = decomposed[0]
    if "\u031b" in decomposed:                 # the horn of ơ and ư (with or without a tone mark) makes the letter wider
        base = {"o": "ơ", "u": "ư", "O": "Ơ", "U": "Ư"}.get(base, base)
    return size * _CALIBRI.get(base, 1024) / 2048 * (BOLD if bold else 1.0)


def _count_lines(chars: list[tuple[str, bool, bool]], size: float, width: float) -> int:
    """Lines a greedy wrap at `width` takes for (character, is_code, is_bold) triples; words break at spaces, East Asian text anywhere."""
    limit = width / FIT
    words: list[tuple[list, bool]] = []
    cur: list = []
    spaced = False
    for ch, code, bold in chars:
        if ch == " " and not code:
            if cur:
                words.append((cur, spaced))
                cur, spaced = [], False
            spaced = True
        elif svg._wide(ch):
            if cur:
                words.append((cur, spaced))
                cur = []
            words.append(([(ch, code, bold)], spaced))
            spaced = False
        else:
            cur.append((ch, code, bold))
    if cur:
        words.append((cur, spaced))
    if not words:
        return 0
    lines, used = 1, 0.0
    for word, spaced in words:
        w = sum(_adv(c, k, size, b) for c, k, b in word)
        gap = _adv(" ", False, size, False) if spaced and used else 0.0
        if used + gap + w <= limit:
            used += gap + w
            continue
        if used:
            lines += 1
        lines += int(w // limit) if w > limit else 0
        used = w % limit if w > limit else w
    return lines


def _nlines(text, size: float, width: float, bold: bool = False) -> int:
    return _count_lines([(ch, code, bold) for s, code in _spans(text) for ch in s], size, width)


def _runs_nlines(runs, size: float, width: float, bold: bool = False) -> int:
    return _count_lines([(ch, kind == "m", bold or kind == "b") for text, kind, _ in runs for ch in re.sub(r"\s+", " ", _clean(text))], size, width)


def _lines_h(n: int, size: float) -> float:
    return n * size * LH


# ---------------------------------------------------------------- blocks and their measure
#
# A block is a dict: kind "card" | "para" | "code" | "grid" | "chips", plus what that kind draws. `measure` is the height it takes at a width.

PADX, PADY, MARK = 22, 11, 58         # card padding and the width a marker takes


def card(head=None, body="", *, marker=None, tint="card", size=22, extra=None) -> dict:
    """A rounded card. `marker`: an int (numbered circle), "tick" (an empty box to tick), "bar" (an accent bar) or None. `extra` is a
    line of runs (text, kind, url) under the body, e.g. a README link."""
    return {"kind": "card", "head": head, "body": body, "marker": marker, "tint": tint, "size": size, "extra": extra}


def para(runs, *, size=22, bold=False, color="ink", glue=False) -> dict:
    """A paragraph of runs (text, kind, url). `glue` keeps it with the block before it: it never starts a slide of its own."""
    return {"kind": "para", "runs": runs, "size": size, "bold": bold, "color": color, "glue": glue}


def code(lines, label=None) -> dict:
    return {"kind": "code", "lines": list(lines) or [""], "label": label}


def grid(items, *, size=24) -> dict:
    """Numbered rows in two columns (the first half down the left, the rest down the right): the roadmap."""
    return {"kind": "grid", "items": items, "size": size}


def chips(items) -> dict:
    return {"kind": "chips", "items": [i for i in items if i]}


def _pad(b: dict) -> tuple[float, float]:
    """Horizontal and vertical padding of a card; a card with tint "none" is plain text at the margin."""
    return (0, 0) if b["tint"] == "none" else (PADX, PADY)


def _card_geom(b: dict, width: float) -> tuple[float, float]:
    marker_w = MARK if b["marker"] not in (None, "bar") else (14 if b["marker"] == "bar" else 0)
    return marker_w, width - 2 * _pad(b)[0] - marker_w


def _runs_plain(runs) -> str:
    return "".join(r[0] for r in runs)


def _units(line: str) -> float:
    """The length of a code line in monospaced columns: an East Asian glyph is drawn about one em wide, which is 1 / MONO_EM columns."""
    return sum(1 / MONO_EM if svg._wide(ch) else 1.0 for ch in line)


def _rows(line: str, cpl: int) -> int:
    return max(1, math.ceil(_units(line) / cpl))


def _chunks(line: str, step: float) -> list[str]:
    """A code line as pieces of at most `step` columns each (at least one character)."""
    out, cur, used = [], "", 0.0
    for ch in line:
        w = 1 / MONO_EM if svg._wide(ch) else 1.0
        if cur and used + w > step:
            out.append(cur)
            cur, used = "", 0.0
        cur += ch
        used += w
    return out + [cur]


def _code_size(lines, width: float) -> tuple[int, int]:
    """The largest size (20 down to 14) at which no line wraps, else 14; and the columns that fit a line at it."""
    inner = width - 2 * PADX
    for size in (20, 18, 16, 14):
        cpl = int(inner / (size * MONO_EM))
        if all(_units(x) <= cpl for x in lines) or size == 14:
            return size, max(cpl, 1)
    raise AssertionError("unreachable")


def measure(b: dict, width: float) -> float:
    k = b["kind"]
    if k == "card":
        _, tw = _card_geom(b, width)
        size, hs = b["size"], b["size"] + 2
        parts = []
        if b["head"]:
            parts.append(_lines_h(_nlines(b["head"], hs, tw, True), hs))
        if b["body"]:
            parts.append(_lines_h(_nlines(b["body"], size, tw), size))
        if b["extra"]:
            parts.append(_lines_h(_runs_nlines(b["extra"], size - 4, tw), size - 4))
        py = _pad(b)[1]
        return max(2 * py + sum(parts) + 5 * max(0, len(parts) - 1), 2 * py + 30 if py else 0)
    if k == "para":
        return _lines_h(_runs_nlines(b["runs"], b["size"], width, b["bold"]), b["size"]) + 4
    if k == "code":
        size, cpl = _code_size(b["lines"], width)
        rows = sum(_rows(x, cpl) for x in b["lines"])
        return (26 if b["label"] else 0) + 2 * 14 + rows * size * 1.38
    if k == "grid":
        return max((sum(h for _, _, h in col) for col in _grid_cols(b, width)), default=0.0)
    if k == "chips":
        return _chip_rows(b["items"], 20, width)[1]
    raise ValueError(k)


def _grid_cols(b: dict, width: float) -> list[list[tuple[int, str, float]]]:
    """The columns of a grid block as (number, text, row height): one column up to five rows, else the first half down the left."""
    items, size = b["items"], b["size"]
    two = len(items) > 5
    colw = WIDTH / 2 - 16 if two else width
    rows = math.ceil(len(items) / 2) if two else len(items)
    return [[(n, text, max(_lines_h(_nlines(text, size, colw - 56), size) + 14, 46)) for n, text in chunk]
            for chunk in ([items[:rows], items[rows:]] if two else [items])]


def _chip_rows(items, size: float, width: float) -> tuple[list[list[tuple[str, float]]], float]:
    rows, cur, x = [], [], 0.0
    for text in items:
        w = svg.width(text, size) + 36
        if cur and x + w > width:
            rows.append(cur)
            cur, x = [], 0.0
        cur.append((text, w))
        x += w + 12
    if cur:
        rows.append(cur)
    return rows, len(rows) * 46 + max(0, len(rows) - 1) * 10


# ---------------------------------------------------------------- pagination

def _sentences(text: str) -> list[str]:
    """Split a long text at sentence ends, outside code spans, so a card too tall for a slide can continue on the next."""
    spans = [(m.start(), m.end()) for m in readmelib.CODE_SPAN.finditer(str(text))]
    out, last = [], 0
    for m in re.finditer(r"(?<=[.!?。])\s+", str(text)):
        if any(a <= m.start() < b for a, b in spans):
            continue
        out.append(str(text)[last:m.start()])
        last = m.end()
    out.append(str(text)[last:])
    return [s for s in out if s.strip()]


def _break_points(text: str) -> list[str]:
    """Pieces a text may be cut between: each word with the space before it, each East Asian character on its own; a backtick span stays
    whole. Joined again they give the text back exactly."""
    raw, out, last = str(text), [], 0
    for found in readmelib.CODE_SPAN.finditer(raw):
        out += _plain_break_points(raw[last:found.start()]) + [found.group(0)]
        last = found.end()
    return out + _plain_break_points(raw[last:])


def _plain_break_points(text: str) -> list[str]:
    pieces, cur = [], ""
    for ch in text:
        if svg._wide(ch):
            if cur:
                pieces.append(cur)
                cur = ""
            pieces.append(ch)
        elif ch.isspace():
            if cur.strip():
                pieces.append(cur)
                cur = ""
            cur += ch
        else:
            cur += ch
    return pieces + ([cur] if cur else [])


def _longest(piece: str, fits) -> int:
    """The largest n below len(piece) for which fits(piece[:n]) holds, or 1 when none does. `fits` only gets harder as the text grows, so the
    answer is found by doubling and then halving: a handful of measurements of about one slide of text, never one per prefix."""
    lo, step = 1, 1
    while lo + step < len(piece) and fits(piece[:lo + step]):
        lo += step
        step *= 2
    hi = min(lo + step, len(piece)) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fits(piece[:mid]):
            lo = mid
        else:
            hi = mid - 1
    return lo


def _chars(piece: str, fits) -> list[str]:
    """One word too long for a slide, cut between characters into pieces that each fit alone."""
    out = []
    while len(piece) > 1 and not fits(piece):
        cut = _longest(piece, fits)
        out.append(piece[:cut])
        piece = piece[cut:]
    return out + [piece]


def _span_chars(piece: str, fits) -> list[str]:
    """`_chars` for a piece that may be a whole backtick span: each fragment of a span too long for a slide is a span again, so it is still
    drawn as code and no backtick is left unpaired."""
    found = readmelib.CODE_SPAN.fullmatch(piece)
    if not found:
        return _chars(piece, fits)
    mark = found.group(1)
    return [mark + part + mark for part in _chars(found.group(2), lambda t: fits(mark + t + mark))]


def _cut(text: str, fits) -> list[str]:
    """A text as pieces that each satisfy `fits(piece, first)`: cut at sentence ends where there are any, between words or characters where
    a sentence is itself too tall (a Japanese paragraph without a full stop), and between characters only for a single unbreakable word.
    A first piece whose opening unit does not fit under the card's heading is left empty, so the heading stands alone."""
    units: list[str] = []
    for i, sentence in enumerate(_sentences(text)):
        lead = " " if i else ""
        if fits(sentence, False):
            units.append(lead + sentence)
            continue
        for piece in _break_points(sentence):
            for part in _span_chars(piece, lambda t: fits(t, False)):
                units.append(lead + part)
                lead = ""
    pieces: list[str] = []
    cur = ""
    for unit in units:
        if not pieces and not cur and not fits(unit.lstrip(), True):
            pieces.append("")
        if cur and not fits(cur + unit, not pieces):
            pieces.append(cur)
            cur = unit.lstrip()
        else:
            cur += unit
    return pieces + [cur]


def _split_card(b: dict, width: float, room: float) -> list[dict]:
    """A card taller than a slide as several that fit: a heading too long for one slide is cut first (each part a card of its own), then
    the body, the first piece of it under the last part of the heading and the README link under the last piece."""
    def alone(**kw) -> float:
        return measure({**b, "body": "", "extra": None, **kw}, width)

    reserve = measure({**b, "body": "x"}, width) - measure({**b, "body": "x", "extra": None}, width) if b["extra"] else 0.0
    heads = [b["head"]]
    if b["head"] and alone() > room:
        heads = [h.strip() for h in _cut(b["head"], lambda t, first: alone(head=t) <= room)]
    last = heads[-1]
    bodies = [t.strip() for t in _cut(b["body"], lambda t, first: measure({**b, "body": t, "head": last if first else None, "extra": None}, width) <= room - reserve)] \
        if b["body"] else [""]
    follow = "bar" if b["marker"] else None
    cards = [{**b, "head": h, "body": "", "extra": None, "marker": b["marker"] if i == 0 else follow} for i, h in enumerate(heads[:-1])]
    cards += [{**b, "head": last if i == 0 else None, "body": text, "marker": b["marker"] if not cards and i == 0 else follow,
               "extra": b["extra"] if i == len(bodies) - 1 else None} for i, text in enumerate(bodies)]
    return cards if len(cards) > 1 else [b]


def _split_para(b: dict, width: float, room: float) -> list[dict]:
    """A paragraph taller than a slide as several that fit, cut between words (or characters) and never inside a code span; every run keeps
    its kind and its link."""
    def fits(atoms) -> bool:
        return measure({**b, "runs": _merge(atoms)}, width) <= room

    atoms: list[tuple[str, str, str | None]] = []
    for text, kind, url in b["runs"]:
        for piece in [text] if kind == "m" else _break_points(text):
            atoms += [(part, kind, url) for part in _chars(piece, lambda t: fits([(t, kind, url)]))]
    pieces: list[list] = [[]]
    for atom in atoms:
        if pieces[-1] and not fits(pieces[-1] + [atom]):
            pieces.append([])
        pieces[-1].append(atom)
    if len(pieces) < 2:
        return [b]
    return [{**b, "runs": _merge(p), "glue": b["glue"] and i == 0} for i, p in enumerate(pieces)]


def _merge(atoms) -> list[tuple[str, str, str | None]]:
    """Atoms (text, kind, url) as runs: neighbours of one kind and link join; a piece never starts with the space it was cut at."""
    runs: list[tuple[str, str, str | None]] = []
    for text, kind, url in atoms:
        if runs and runs[-1][1:] == (kind, url):
            runs[-1] = (runs[-1][0] + text, kind, url)
        else:
            runs.append((text, kind, url))
    if runs and runs[0][1] != "m":
        runs[0] = (runs[0][0].lstrip(), *runs[0][1:])
    return [r for r in runs if r[0]]


def _fit(b: dict, width: float, room: float) -> list[dict]:
    """The block, or the pieces of it when it is taller than a whole slide (a long sample, a very long paragraph)."""
    if measure(b, width) <= room:
        return [b]
    k = b["kind"]
    if k == "code":
        size, cpl = _code_size(b["lines"], width)
        per = max(1, int((room - 28 - (26 if b["label"] else 0)) / (size * 1.38)))
        lines: list[str] = []
        for line in b["lines"]:                                           # a single line taller than a slide continues on the next one
            step = cpl * per
            lines += _chunks(line, step) if _units(line) > step else [line]
        pieces, cur, rows = [], [], 0
        for line in lines:
            need = _rows(line, cpl)
            if cur and rows + need > per:
                pieces.append(cur)
                cur, rows = [], 0
            cur.append(line)
            rows += need
        pieces.append(cur)
        return [code(p, b["label"] if i == 0 else None) for i, p in enumerate(pieces)]
    if k == "grid":
        items, n = b["items"], len(b["items"])
        for size in (10, 8, 6, 4, 2, 1):
            if measure(grid(items[:size], size=b["size"]), width) <= room:
                return [grid(items[i:i + size], size=b["size"]) for i in range(0, n, size)]
    if k == "card":
        return _split_card(b, width, room)
    if k == "para":
        return _split_para(b, width, room)
    return [b]


def paginate(blocks: list[dict], top: float, width: float = WIDTH) -> list[list[tuple[dict, float, float]]]:
    """Place blocks top to bottom; a block that does not fit starts the next slide, and a `glue` block takes the block before it along
    rather than start a slide alone. Returns, per slide, (block, y, height)."""
    pages: list[list[dict]] = []
    cur: list[dict] = []
    y = top
    for b in blocks:
        for piece in _fit(b, width, BOTTOM - top):
            h = measure(piece, width)
            if cur and y + h > BOTTOM:
                carry = [cur.pop()] if piece.get("glue") and len(cur) > 1 else []
                pages.append(cur)
                cur = carry
                y = top + sum(measure(p, width) + GAP for p in carry)
            cur.append(piece)
            y += h + GAP
    if cur or not pages:
        pages.append(cur)
    placed = []
    for page in pages:
        y, out = top, []
        for piece in page:
            h = measure(piece, width)
            out.append((piece, y, h))
            y += h + GAP
        placed.append(out)
    return placed


# ---------------------------------------------------------------- drawing

def _rgb(hexcolor: str) -> RGBColor:
    return RGBColor.from_string(hexcolor)


def _strip_style(shape) -> None:
    style = shape._element.find(qn("p:style"))
    if style is not None:
        shape._element.remove(style)             # the theme's shadow and line: every shape here sets its own fill and line


def _shape(slide, kind, x, y, w, h, fill=None, line=None, radius=None, name=None, line_w=2.0):
    shp = slide.shapes.add_shape(kind, Pt(x), Pt(y), Pt(w), Pt(h))
    _strip_style(shp)
    if radius is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = min(0.5, radius / min(w, h))
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = _rgb(fill)
    else:
        shp.fill.background()
    if line:
        shp.line.color.rgb = _rgb(line)
        shp.line.width = Pt(line_w)
    else:
        shp.line.fill.background()
    if name:
        shp.name = name
    return shp


def _runs(para_, runs, size, color, th, lang, bold=False, face=SANS) -> None:
    for text, kind, url in runs:
        r = para_.add_run()
        r.text = _clean(text)
        f = r.font
        f.size = Pt(size - 2 if kind == "m" else size)
        f.bold = bool(bold or kind == "b")
        f.name = MONO if kind == "m" else face
        f.color.rgb = _rgb(th["inline"] if kind == "m" else th["link"] if kind == "a" else color)
        if lang in EAST:
            rpr = r._r.get_or_add_rPr()
            ea = rpr.makeelement(qn("a:ea"), {"typeface": EAST[lang]})
            rpr.append(ea)
        if url:
            r.hyperlink.address = url
            if kind == "a":
                f.underline = True


def _text(slide, x, y, w, h, paras, th, lang, anchor="top", name=None):
    """paras: dicts with runs [(text, kind, url)], size, color (hex), bold, face, align, before."""
    tb = slide.shapes.add_textbox(Pt(x), Pt(y), Pt(w), Pt(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE}[anchor]
    for i, p in enumerate(paras):
        pg = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        pg.alignment = p.get("align", PP_ALIGN.LEFT)
        pg.line_spacing = 1.0
        if p.get("before"):
            pg.space_before = Pt(p["before"])
        _runs(pg, p["runs"], p["size"], p.get("color", th["ink"]), th, lang, p.get("bold", False), p.get("face", SANS))
    return tb


def prose(text, bold=False) -> list[tuple[str, str, None]]:
    """Runs for a sentence of the draft: code spans monospaced, the rest plain (or bold)."""
    return [(s, "m" if c else "b" if bold else "t", None) for s, c in _spans(text)]


def _marker(slide, b, x, y, h, th, lang) -> None:
    mk = b["marker"]
    if isinstance(mk, int):
        fill = th["num"][(mk - 1) % len(th["num"])]
        o = _shape(slide, MSO_SHAPE.OVAL, x, y + h / 2 - 20, 40, 40, fill=fill, name=f"marker {mk}")
        tf = o.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        pg = tf.paragraphs[0]
        pg.alignment = PP_ALIGN.CENTER
        _runs(pg, [(str(mk), "b", None)], 20, th["numink"], th, lang, True)
    elif mk == "tick":
        _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x + 4, y + h / 2 - 16, 32, 32, line=th["num"][min(1, len(th["num"]) - 1)],
               radius=8, name="tick box", line_w=3)


def _draw_card(slide, b, x, y, w, h, th, lang) -> None:
    px, py = _pad(b)
    if b["tint"] != "none":
        _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=th["card"] if b["tint"] == "card" else th[b["tint"]], radius=16, name="card")
    marker_w, tw = _card_geom(b, w)
    if b["marker"] == "bar":
        _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x + px - 6, y + py, 6, h - 2 * py, fill=th["accent"], radius=3, name="bar")
    elif b["marker"] is not None:
        _marker(slide, b, x + px, y, h, th, lang)
    paras, size = [], b["size"]
    if b["head"]:
        paras.append({"runs": prose(b["head"], bold=True), "size": size + 2, "bold": True})
    if b["body"]:
        paras.append({"runs": prose(b["body"]), "size": size, "before": 5 if paras else 0})
    if b["extra"]:
        paras.append({"runs": b["extra"], "size": size - 4, "before": 5 if paras else 0})
    _text(slide, x + px + marker_w, y + py, tw, h - 2 * py, paras, th, lang, anchor="middle" if py else "top", name="card text")


def _draw_code(slide, b, x, y, w, h, th, lang) -> None:
    size, cpl = _code_size(b["lines"], w)
    top = y
    if b["label"]:
        _text(slide, x, y, w, 22, [{"runs": [(_clean(b["label"]), "t", None)], "size": 16, "color": th["codelabel"]}], th, lang, name="code label")
        top = y + 26
    _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, top, w, h - (top - y), fill=th["code"], radius=14, name="code block")
    paras = [{"runs": [(line, "t", None)], "size": size, "color": th["codeink"], "face": MONO} for line in b["lines"]]
    _text(slide, x + PADX, top + 14, w - 2 * PADX, h - (top - y) - 28, paras, th, lang, anchor="middle", name="code")


def _draw_grid(slide, b, x, y, w, th, lang) -> None:
    size = b["size"]
    colw = WIDTH / 2 - 16 if len(b["items"]) > 5 else w
    for col, rows in enumerate(_grid_cols(b, w)):
        cy, cx = y, x + col * (colw + 32)
        for n, text, h in rows:
            o = _shape(slide, MSO_SHAPE.OVAL, cx, cy + h / 2 - 18, 36, 36, fill=th["num"][(n - 1) % len(th["num"])], name=f"marker {n}")
            tf = o.text_frame
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            _runs(tf.paragraphs[0], [(str(n), "b", None)], 18, th["numink"], th, lang, True)
            _text(slide, cx + 52, cy + 7, colw - 56, h - 14, [{"runs": prose(text), "size": size}], th, lang, anchor="middle", name="step")
            cy += h


def _draw_chips(slide, b, x, y, w, th, lang, size=20) -> None:
    rows, _ = _chip_rows(b["items"], size, w)
    for r, row in enumerate(rows):
        cx = x
        for text, cw in row:
            _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, cx, y + r * 56, cw, 46, fill=th["card"], radius=23, name="chip")
            _text(slide, cx, y + r * 56, cw, 46, [{"runs": [(_clean(text), "b", None)], "size": size, "align": PP_ALIGN.CENTER}], th, lang, anchor="middle", name="chip text")
            cx += cw + 12


def _arrow(shape) -> None:
    """An arrowhead on the end of an open freeform line."""
    ln = shape.line._get_or_add_ln()
    tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
    ln.append(tail)


def _polyline(slide, pts, color, dashed=False, width=2.5, name="arrow"):
    fb = slide.shapes.build_freeform(Pt(pts[0][0]), Pt(pts[0][1]), scale=1.0)
    fb.add_line_segments([(Pt(x), Pt(y)) for x, y in pts[1:]], close=False)
    shp = fb.convert_to_shape()
    _strip_style(shp)
    shp.fill.background()
    shp.line.color.rgb = _rgb(color)
    shp.line.width = Pt(width)
    if dashed:
        shp.line.dash_style = MSO_LINE.DASH
    _arrow(shp)
    shp.name = name
    return shp


def _hits(pts, boxes) -> bool:
    """Whether a polyline of horizontal and vertical segments passes through the inside of any of the boxes (x0, y0, x1, y1)."""
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        for x0, y0, x1, y1 in boxes:
            if min(xa, xb) < x1 and max(xa, xb) > x0 and min(ya, yb) < y1 and max(ya, yb) > y0:
                return True
    return False


def flow_geometry(components: list[dict], edges: list[list[int]], top: float, bottom: float) -> dict:
    """Box positions and edge routes of the how-it-works diagram: columns by dependency depth (as in `svg.flow`), rows ordered by the
    boxes that feed them, loop-backs routed under the boxes. Pure numbers, so a test can check nothing overlaps."""
    n = len(components)
    layer = svg._layers(n, edges) if edges else list(range(n)) if n <= 4 else [i // 2 for i in range(n)]
    cols = max(layer) + 1
    gapx = 72 if cols <= 3 else 44
    bw = min(300.0, (WIDTH - (cols - 1) * gapx) / cols)
    order: dict[int, list[int]] = {}
    row_of: dict[int, float] = {}
    for col in range(cols):
        ids = [i for i in range(n) if layer[i] == col]
        ids.sort(key=lambda i: (sum(row_of[a] for a, b in edges if b == i and a in row_of) / max(1, len([1 for a, b in edges if b == i and a in row_of])), i))
        order[col] = ids
        for r, i in enumerate(ids):
            row_of[i] = r
    back = [(a, b) for a, b in edges if layer[b] <= layer[a]]
    skips = [(a, b) for a, b in edges if layer[b] - layer[a] >= 2]         # these may have to go round the boxes between their columns
    nlane = len(back) + len(skips)
    lanes = 0 if not nlane else 26 + min(16 * nlane, 70)
    area = bottom - top - lanes
    tallest = max(len(ids) for ids in order.values())
    # The largest type at which the tallest column fits: one height for every box (so boxes in the same row of two columns line up and
    # their arrow is straight), the gap between boxes shrinking from 28 to 10 pt before the type does, and the boxes widening to the whole
    # column before the type shrinks again (a long name then needs fewer lines).
    wide = (WIDTH - (cols - 1) * gapx) / cols
    for size in (22, 18, 16, 14, 12, 10):
        for bw in dict.fromkeys((min(300.0, wide), wide)):
            one = max(86.0 if size >= 18 else 48.0 if size >= 14 else 36.0, max(_lines_h(_nlines(c["name"], size, bw - 28, True), size) + 24 for c in components))
            spare = area - tallest * one
            vgap = min(28.0, spare / (tallest - 1)) if tallest > 1 else 28.0
            if (vgap >= 10 and spare >= 0) or (size == 10 and bw == wide):
                break
        else:
            continue
        break
    vgap = max(vgap, 6.0)
    heights = [one] * n
    col_h = {c: sum(heights[i] for i in order[c]) + vgap * (len(order[c]) - 1) for c in order}
    pos = {}
    for col in range(cols):
        y = max(top, top + (area - col_h[col]) / 2)
        for i in order[col]:
            pos[i] = (LEFT + col * (bw + gapx), y)
            y += heights[i] + vgap
    low = max(pos[i][1] + heights[i] for i in range(n))
    routes = []
    lane = 0

    def next_lane() -> float:
        nonlocal lane
        lane += 1
        return low + 22 + min(16, 70 / max(1, nlane)) * (lane - 1)

    for a, b in edges:
        (xa, ya), (xb, yb) = pos[a], pos[b]
        others = [(x, y, x + bw, y + heights[i]) for i, (x, y) in pos.items() if i not in (a, b)]
        if layer[b] > layer[a]:
            y1, y2, x1, x2 = ya + heights[a] / 2, yb + heights[b] / 2, xa + bw, xb
            mid = (x1 + x2) / 2
            pts = [(x1, y1), (x2, y2)] if abs(y1 - y2) < 1 else [(x1, y1), (mid, y1), (mid, y2), (x2, y2)]
            if layer[b] - layer[a] >= 2 and _hits(pts, others):          # it would run behind a box in a column between: go round, under them
                ylane = next_lane()
                pts = [(x1, y1), (x1 + gapx / 2, y1), (x1 + gapx / 2, ylane), (x2 - gapx / 2, ylane), (x2 - gapx / 2, y2), (x2, y2)]
            routes.append({"pts": pts, "dashed": False})
        elif layer[b] == layer[a] and abs((xa + bw / 2) - (xb + bw / 2)) < 1:      # one under the other: a straight line between them
            if yb > ya:
                routes.append({"pts": [(xa + bw / 2, ya + heights[a]), (xb + bw / 2, yb)], "dashed": True})
            else:
                routes.append({"pts": [(xa + bw / 2, ya), (xb + bw / 2, yb + heights[b])], "dashed": True})
        else:                                           # a loop back: down under the boxes, across, and up into the target
            ylane = next_lane()
            pts = [(xa + bw / 2, ya + heights[a]), (xa + bw / 2, ylane), (xb + bw / 2, ylane), (xb + bw / 2, yb + heights[b])]
            if layer[b] < layer[a] and _hits(pts, others):          # it would climb through a box of its own column: use the gaps beside them
                ya_out, yb_in = ya + heights[a] - 14, yb + heights[b] - 14
                gap_a, gap_b = xa - gapx * 0.35, xb + bw + gapx * 0.35
                pts = [(xa, ya_out), (gap_a, ya_out), (gap_a, ylane), (gap_b, ylane), (gap_b, yb_in), (xb + bw, yb_in)]
            routes.append({"pts": pts, "dashed": True})
    return {"layer": layer, "pos": pos, "heights": heights, "bw": bw, "size": size, "routes": routes}


def _draw_flow(slide, geo, components, th, lang) -> None:
    for r in geo["routes"]:
        _polyline(slide, r["pts"], "475569", dashed=r["dashed"], name="flow arrow")
    for i, c in enumerate(components):
        x, y = geo["pos"][i]
        fill, stroke = svg.LAYERS[geo["layer"][i] % len(svg.LAYERS)]
        _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, geo["bw"], geo["heights"][i], fill=fill.lstrip("#"), line=stroke.lstrip("#"), radius=16, name="component")
        _text(slide, x + 14, y + 8, geo["bw"] - 28, geo["heights"][i] - 16, [{"runs": prose(c["name"], bold=True), "size": geo["size"], "bold": True,
                                                                           "color": "0F172A", "align": PP_ALIGN.CENTER}], th, lang, anchor="middle", name="component name")


# ---------------------------------------------------------------- the book: pages in order, drawn once the count is known

class Book:
    """Collects pages (title, kicker, theme, placed blocks or a drawer), then draws them with their "n/N" and progress rail."""

    def __init__(self, facts: dict, draft: dict, lang: str):
        self.facts, self.draft, self.lang, self.t = facts, draft, lang, L[lang]
        self.pages: list[dict] = []

    def _title_geom(self, title: str) -> tuple[int, int, float]:
        """Size, lines and height of a slide title: Cambria Bold (about 6.5% wider than Calibri Bold), 36 pt down to 26 pt for a long one."""
        for size in (36, 30, 26):
            lines = max(1, _nlines(title, size * 1.065, WIDTH, True))
            if lines <= 2 or size == 26:
                return size, lines, lines * size * 1.18
        raise AssertionError("unreachable")

    def add(self, title: str, blocks: list[dict], *, kicker: str = "", theme: str = "light") -> None:
        size, _, th_h = self._title_geom(title if kicker else title + " (9/9)")        # without a kicker the "(2/3)" joins the title
        top = 48 + th_h + 14
        pages = paginate(blocks, top)
        for i, placed in enumerate(pages, 1):
            suffix = f" ({i}/{len(pages)})" if len(pages) > 1 else ""
            self.pages.append({"theme": theme, "title": title + ("" if kicker else suffix), "kicker": kicker + (suffix if kicker else ""),
                               "placed": placed, "tsize": size, "top": top})

    def diagram(self, title: str, components: list[dict], edges: list[list[int]]) -> None:
        size, _, th_h = self._title_geom(title)
        top = 48 + th_h + 20
        self.pages.append({"theme": "light", "title": title, "kicker": "", "tsize": size, "top": top, "flow": (components, edges)})

    def _cover_plan(self) -> dict:
        """The type sizes of the cover and which of hook and one-liner it shows. Everything is tried at three sizes; if the copy still does
        not fit, the title stays and the rest moves to the slide after the cover, so no field of the draft is ever left out."""
        d = self.draft
        for tsize, hsize, osize in ((48, 24, 22), (40, 22, 20), (34, 20, 18)):
            title_h = _nlines(d["title"], tsize * 1.065, WIDTH, True) * tsize * 1.2
            hook_h = _lines_h(_nlines(d["hook"], hsize, WIDTH), hsize)
            line_h = _lines_h(_nlines(d["one_liner"], osize, WIDTH, True), osize)
            if COVER_TOP + title_h + 18 + hook_h + 12 + line_h <= COVER_BOTTOM:
                return {"title": tsize, "hook": hsize, "one_liner": osize, "shown": ("hook", "one_liner")}
        title_h = _nlines(d["title"], 34 * 1.065, WIDTH, True) * 34 * 1.2
        hook_h = _lines_h(_nlines(d["hook"], 20, WIDTH), 20)
        fits_hook = COVER_TOP + title_h + 18 + hook_h <= COVER_BOTTOM
        return {"title": 34, "hook": 20, "one_liner": 18, "shown": ("hook",) if fits_hook else ()}

    def cover(self) -> None:
        plan = self._cover_plan()
        self.pages.append({"theme": "dark", "cover": True, "title": self.draft["title"], "kicker": "", "plan": plan})
        rest = [card(None, self.draft[key], marker=None, tint="none", size=28 if key == "hook" else 24)
                for key in ("hook", "one_liner") if key not in plan["shown"]]
        if rest:                                     # the copy the cover had no room for, on the slide right after it
            self.add(self.draft["title"], rest)

    # -- drawing
    def build(self) -> bytes:
        prs = Presentation()
        prs.slide_width, prs.slide_height = Pt(SW), Pt(SH)
        total = len(self.pages)
        name = self.facts["full_name"].split("/")[-1]
        for n, pg in enumerate(self.pages, 1):
            th = THEMES[pg["theme"]]
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = _rgb(th["bg"])
            if pg.get("cover"):
                self._draw_cover(slide, pg, th)
            else:
                if pg["kicker"]:
                    _text(slide, LEFT, 24, 640, 22, [{"runs": [(_clean(pg["kicker"]), "b", None)], "size": 16, "color": th["kicker"]}], th, self.lang, name="kicker")
                _text(slide, LEFT, 48, WIDTH, 120, [{"runs": prose(pg["title"], bold=True), "size": pg["tsize"], "bold": True, "face": SERIF}], th, self.lang, name="title")
                if "flow" in pg:
                    comps, edges = pg["flow"]
                    geo = flow_geometry(comps, edges, pg["top"], BOTTOM)
                    _draw_flow(slide, geo, comps, th, self.lang)
                for b, y, h in pg.get("placed", ()):
                    self._draw_block(slide, b, y, h, th)
            self._chrome(slide, th, n, total, name)
        self._properties(prs)
        buf = io.BytesIO()
        prs.save(buf)
        return _stable_zip(buf.getvalue())

    def _draw_block(self, slide, b, y, h, th) -> None:
        k = b["kind"]
        if k == "card":
            _draw_card(slide, b, LEFT, y, WIDTH, h, th, self.lang)
        elif k == "para":
            color = th["ink"] if b["color"] == "ink" else th["muted"]
            _text(slide, LEFT, y, WIDTH, h, [{"runs": b["runs"], "size": b["size"], "bold": b["bold"], "color": color}], th, self.lang, name="text")
        elif k == "code":
            _draw_code(slide, b, LEFT, y, WIDTH, h, th, self.lang)
        elif k == "grid":
            _draw_grid(slide, b, LEFT, y, WIDTH, th, self.lang)
        elif k == "chips":
            _draw_chips(slide, b, LEFT, y, WIDTH, th, self.lang)

    def _chrome(self, slide, th, n, total, name) -> None:
        _text(slide, SW - LEFT - 160, 24, 160, 22, [{"runs": [(f"{n}/{total}", "b", None)], "size": 16, "color": th["ink"], "align": PP_ALIGN.RIGHT}], th, self.lang, name="page")
        _shape(slide, MSO_SHAPE.RECTANGLE, LEFT, 508, WIDTH, 3, fill=th["muted"], name="rail")
        _shape(slide, MSO_SHAPE.RECTANGLE, LEFT, 506, max(8.0, WIDTH * n / total), 7, fill=th["accent"], name="progress")
        _text(slide, LEFT, 518, 600, 18, [{"runs": [(f"{self.t['series']} · {name}", "t", None)], "size": 12, "color": th["muted"]}], th, self.lang, name="footer")

    def _draw_cover(self, slide, pg, th) -> None:
        f, d, t = self.facts, self.draft, self.t
        _chips = [t["bucket"][f["bucket"]]]
        _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, LEFT, 56, svg.width(_chips[0], 20) + 40, 40, fill=th["accent"], radius=20, name="bucket")
        _text(slide, LEFT, 56, svg.width(_chips[0], 20) + 40, 40, [{"runs": [(_chips[0], "b", None)], "size": 20, "color": "12141B", "align": PP_ALIGN.CENTER}],
              th, self.lang, anchor="middle", name="bucket text")
        plan = pg["plan"]
        size = plan["title"]
        tl = _nlines(d["title"], size * 1.065, WIDTH, True)
        _text(slide, LEFT, COVER_TOP, WIDTH, tl * size * 1.2, [{"runs": prose(d["title"], bold=True), "size": size, "bold": True, "face": SERIF}], th, self.lang, name="title")
        y = COVER_TOP + tl * size * 1.2 + 18
        for key, colour, bold in (("hook", th["muted"], False), ("one_liner", th["ink"], True)):
            if key not in plan["shown"]:
                continue
            sz = plan[key]
            h = _lines_h(_nlines(d[key], sz, WIDTH, bold), sz)
            _text(slide, LEFT, y, WIDTH, h, [{"runs": prose(d[key], bold=bold), "size": sz, "color": colour, "bold": bold}], th, self.lang, name=key)
            y += h + 12
        sep = t["sep"]
        items = [f"{svg.fmt_int(f['stars'], sep)} {t['stars']}", f"{svg.fmt_int(f['forks'], sep)} {t['forks']}", f"{t['license']}: {f['license']}"]
        if f["language"]:
            items.append(f"{t['language']}: {f['language']}")
        _draw_chips(slide, chips(items), LEFT, 408, WIDTH, th, self.lang)

    def _properties(self, prs) -> None:
        cp, when = prs.core_properties, datetime.fromisoformat(self.facts["scanned"]).replace(tzinfo=timezone.utc)
        cp.title, cp.subject, cp.author, cp.last_modified_by = _clean(self.draft["title"]), self.facts["full_name"], "GitHub Radar", "GitHub Radar"
        cp.created = cp.modified = cp.last_printed = when
        cp.revision, cp.keywords, cp.comments, cp.category, cp.language = 1, "", "", "", self.lang


def _stable_zip(blob: bytes) -> bytes:
    """The same parts in the same order with one fixed timestamp, so drawing a deck again gives the same bytes."""
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(blob)) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            clone = zipfile.ZipInfo(info.filename, date_time=(2020, 1, 1, 0, 0, 0))
            clone.compress_type, clone.external_attr = zipfile.ZIP_DEFLATED, 0o600 << 16
            dst.writestr(clone, src.read(info.filename))
    return out.getvalue()


# ---------------------------------------------------------------- what goes on the slides

def _link_runs(facts: dict, ref, t: dict):
    found = digest.link_parts(facts, ref)
    if not found:
        return None
    label, url, local = found
    if local:
        return [(f"{t['open_addr']}: ", "t", None), (url, "m", None)]
    return [(f"{t['get_link']}: ", "t", None), (label, "a", url)]


def _stats(facts: dict, t: dict) -> list[str]:
    sep = t["sep"]
    items = [f"{svg.fmt_int(facts['stars'], sep)} {t['stars']}", f"{svg.fmt_int(facts['forks'], sep)} {t['forks']}", f"{t['license']}: {facts['license']}"]
    if facts["language"]:
        items.append(f"{t['language']}: {facts['language']}")
    return items


def _closing(book: Book) -> None:
    f, t = book.facts, book.t
    blocks = [chips(_stats(f, t)),
              card(t["source"], "", marker=None, tint="card", size=24,
                   extra=[(f["full_name"], "a", f["url"]), (f" · {t['scanned']} {f['scanned']}", "t", None)]),
              para([(_clean(t["disclaimer"]), "t", None)], size=20, color="muted")]
    book.add(t["source"], blocks, theme="dark")


def _steps_pages(book: Book, g: dict) -> None:
    f, t = book.facts, book.t
    hinted = False
    for i, step in enumerate(g["steps"], 1):
        blocks = [para([(f"{t['why']}: ", "b", None)] + prose(step["why"]), size=22)]
        blocks += [card(None, d, marker=j, size=24) for j, d in enumerate(step["do"], 1)]
        if step.get("commands"):
            groups = digest.command_groups(f, step["commands"])
            named = any(shell != "bash" for shell, _ in groups)
            for gi, (shell, group) in enumerate(groups):
                label = t["shell_" + shell] if named else (t["type_here"] if not hinted and gi == 0 else None)
                blocks.append(code(digest.command_lines(group, shell), label))
            hinted = True
        snippet = digest.snippet_body(f, step.get("snippet_ref"))
        if snippet:
            blocks.append(code(snippet[1].splitlines(), t["snippet"]))
        link = _link_runs(f, step.get("link_ref"), t)
        if link:
            blocks.append(para(link, size=22, glue=True))
        if step.get("expect"):
            blocks.append(card(t["expect"], step["expect"], marker="tick", tint="good", size=22))
        if step.get("if_fails"):
            blocks.append(card(t["if_fails"], step["if_fails"], marker="bar", tint="warn", size=22))
        book.add(step["title"], blocks, kicker=f"{t['step']} {i}")


def guide_book(facts: dict, draft: dict, lang: str) -> Book:
    t, g, hiw = L[lang], draft["guide"], draft["how_it_works"]
    book = Book(facts, draft, lang)
    book.cover()
    book.add(t["outcome"], [card(None, g["outcome"], marker=None, tint="good", size=32)])
    book.add(t["problem"], [card(None, draft["problem"], marker=None, tint="none", size=26), card(t["analogy"], draft["analogy"], marker="bar", tint="warn", size=24)])
    book.add(t["who"], [card(None, x, marker=i) for i, x in enumerate(draft["who_for"], 1)])
    book.add(t["caveats"], [card(None, x, marker="bar", tint="warn") for x in draft["caveats"]])
    if g["requirements"]:
        book.add(t["before"], [para([(_clean(t["tick"]), "t", None)], size=20, color="muted")] +
                 [card(r["item"], r.get("detail", ""), marker="tick", size=22, extra=_link_runs(facts, r.get("link_ref"), t)) for r in g["requirements"]])
    book.add(t["roadmap"], [grid([(i, s["title"]) for i, s in enumerate(g["steps"], 1)], size=24)])
    _steps_pages(book, g)
    book.add(t["verify"], [card(None, g["verify"], marker=None, tint="good", size=30)])
    if g.get("troubleshooting"):
        book.add(t["trouble"], [card(x["problem"], x["fix"], marker="bar", tint="warn", size=22) for x in g["troubleshooting"]])
    if g.get("next"):
        book.add(t["next"], [card(None, x, marker=i) for i, x in enumerate(g["next"], 1)])
    book.diagram(t["inside"], hiw["components"], hiw["flow"])
    book.add(t["parts"], [card(c["name"], c["role"], marker=i, size=22) for i, c in enumerate(hiw["components"], 1)])
    book.add(t["how"], [card(s["title"], s["text"], marker=i, size=22) for i, s in enumerate(hiw["steps"], 1)], theme="dark")
    book.add(t["learn"], [card(None, x, marker=i, size=26) for i, x in enumerate(draft["learn"], 1)], theme="cobalt")
    if draft["glossary"]:
        book.add(t["glossary"], [card(x["term"], x["meaning"], marker=None, size=24) for x in draft["glossary"]])
    _closing(book)
    return book


def concept_book(facts: dict, draft: dict, lang: str) -> Book:
    """The deck of a draft without a guide (every digest written before the guide existed)."""
    t, hiw = L[lang], draft["how_it_works"]
    book = Book(facts, draft, lang)
    book.cover()
    book.add(t["problem"], [card(None, draft["problem"], marker=None, tint="none", size=26), card(t["analogy"], draft["analogy"], marker="bar", tint="warn", size=24)])
    book.add(t["who"], [card(None, x, marker=i) for i, x in enumerate(draft["who_for"], 1)])
    book.diagram(t["how"], hiw["components"], hiw["flow"])
    book.add(t["parts"], [card(c["name"], c["role"], marker=i, size=22) for i, c in enumerate(hiw["components"], 1)])
    book.add(t["how"], [card(s["title"], s["text"], marker=i, size=22) for i, s in enumerate(hiw["steps"], 1)], theme="dark")
    commands = draft["try_it"]["commands"]
    tryit = [code(commands)] if commands else [para([(_clean(t["no_cmd"]), "t", None)], size=24)]
    if draft["try_it"].get("note"):
        tryit.append(para(prose(draft["try_it"]["note"]), size=22))
    book.add(t["try"], tryit)
    book.add(t["caveats"], [card(None, x, marker="bar", tint="warn") for x in draft["caveats"]])
    book.add(t["learn"], [card(None, x, marker=i, size=26) for i, x in enumerate(draft["learn"], 1)], theme="cobalt")
    if draft["glossary"]:
        book.add(t["glossary"], [card(x["term"], x["meaning"], marker=None, size=24) for x in draft["glossary"]])
    _closing(book)
    return book


def deck(facts: dict, draft: dict, lang: str) -> bytes:
    """The .pptx of one draft in one language."""
    return (guide_book(facts, draft, lang) if draft.get("guide") else concept_book(facts, draft, lang)).build()


# ---------------------------------------------------------------- the command: write the decks beside the stored drafts

def _folders(root: Path, selectors: list[str], everything: bool) -> list[Path]:
    base = root / "digests"
    if everything:
        runs = sorted(p for p in base.iterdir() if p.is_dir() and RUN_SLUG.fullmatch(p.name)) if base.is_dir() else []
        return [r for run in runs for r in sorted(p for p in run.iterdir() if p.is_dir())]
    if not selectors:
        raise ValueError("name what to draw: a run (2026-10-17-2), one repository of it (2026-10-17-2/orca), or --all")
    out: list[Path] = []
    for sel in selectors:
        run, _, repo = sel.strip("/").partition("/")
        if not RUN_SLUG.fullmatch(run) or "/" in repo or repo in (".", ".."):
            raise ValueError(f"a digest looks like 2026-10-17-2 or 2026-10-17-2/orca, got {sel!r}")
        folder = base / run
        if not folder.is_dir():
            raise ValueError(f"no digests for {run}")
        found = [folder / repo] if repo else sorted(p for p in folder.iterdir() if p.is_dir())
        if repo and not found[0].is_dir():
            raise ValueError(f"no digest {run}/{repo}")
        out += found
    return out


def write(root: Path, selectors: list[str] | None = None, *, everything: bool = False, langs: list[str] | None = None) -> dict:
    """Draw `slides-<lang>.pptx` beside each stored `draft-<lang>.json` of the chosen digests. A draft that no longer fits the schema is
    skipped and said so; nothing else in the folder is touched, and a deck is replaced only when it was drawn completely."""
    report: dict = {"written": [], "skipped": {}}
    for folder in _folders(root, selectors or [], everything):
        for path in sorted(folder.glob("draft-*.json")):
            rel = path.relative_to(root).as_posix()
            tmp = None
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(stored, dict) or not isinstance(stored.get("draft"), dict) or not isinstance(stored.get("facts"), dict):
                    report["skipped"][rel] = "not a stored draft (expected an object with lang, facts and draft)"
                    continue
                lang = stored.get("lang")
                if not isinstance(lang, str) or lang not in L:
                    continue
                if path.name != f"draft-{lang}.json":                  # `draft-zz.json` saying "vi" must not overwrite the deck of `draft-vi.json`
                    report["skipped"][rel] = f"the file name says {path.stem.removeprefix('draft-')!r} but the draft says {lang!r}"
                    continue
                if langs and lang not in langs:
                    continue
                problems = [str(p) for p in gates.schema(stored["draft"]) if p.level == "error"]
                if problems:
                    report["skipped"][rel] = "the stored draft no longer fits the schema: " + "; ".join(problems[:2])
                    continue
                blob = deck(stored["facts"], stored["draft"], lang)
                target = folder / f"slides-{lang}.pptx"
                tmp = target.with_name(target.name + ".tmp")
                tmp.write_bytes(blob)
                tmp.replace(target)
                tmp = None
                report["written"].append(target.relative_to(root).as_posix())
            except json.JSONDecodeError:
                report["skipped"][rel] = "not JSON"
            except (OSError, ValueError, RecursionError, KeyError, TypeError, AttributeError) as exc:
                report["skipped"][rel] = f"{type(exc).__name__}: {exc}"          # one strange file must not stop the rest, nor change anything
            finally:
                if tmp is not None:
                    tmp.unlink(missing_ok=True)
    return report
