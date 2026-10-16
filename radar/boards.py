"""A digest laid out once, as a neutral scene, for the editors that cannot run in CI (Excalidraw, Moda).

`build` turns a stored draft into positioned rectangles, text, arrows and badges. `excalidraw.py` and `moda.py` only
translate that scene into their own file format, so both pictures show the same content in the same places. Nothing here
calls a model or the network, and every word on the scene is a field of the draft, a label of `labels.py` or a fact:
no arrow label, caption or icon is invented (an icon is the draft's own pick from the closed set in `icons/`, drawn only by an
editor whose Style asks for it), and the draft's `flow` (index pairs, no names) is drawn as plain arrows.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from . import icons
from .svg import _wide, fmt_int, width        # the same width estimate as the SVG diagrams, so text reserves the same room

W, M = 1200, 60                    # canvas width and side margin
CW = W - 2 * M                     # content width


@dataclass(frozen=True)
class Style:
    """Font sizes of one editor (px). The scene reserves room for the text at these sizes."""
    chip: int
    title: int
    hook: int
    head: int
    name: int
    role: int
    step_title: int
    step_text: int
    learn: int
    foot: int
    body_lh: float                 # line height factor of body text
    title_lh: float = 1.15
    band: bool = True              # a dark band behind the title (Moda); False puts the title straight on the page (Excalidraw)
    wscale: float = 1.0            # how much wider than svg.py's estimate this editor's font runs (Be Vietnam Pro: wider)
    icon: int = 0                  # width of the pictogram on each component card; 0 draws none (only a draft that names an icon for every component gets them)


def one_line(text) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def _pieces(text: str) -> list[tuple[str, bool]]:
    """(piece, glued) for each place a line may end. A line can end at a space, and inside a word only next to a wide (CJK)
    character, since Japanese has no spaces to break at. A run of narrow characters inside such a word (`AI`, `GitHub`) stays
    whole, and `glued` means the piece continues the word before it: nothing is ever put between the pieces of one word."""
    out = []
    for word in str(text).split():
        runs, run = [], ""
        for ch in word:
            if _wide(ch):
                if run:
                    runs.append(run)
                run = ""
                runs.append(ch)
            else:
                run += ch
        if run:
            runs.append(run)
        out += [(r, i > 0) for i, r in enumerate(runs)]
    return out


def wrap(text: str, px: float, max_w: float, scale: float = 1.0) -> list[str]:
    """Lines no wider than `max_w` (svg.py's width estimate times `scale`), never changing text: svg.wrap caps its lines with an
    ellipsis, lets a word wider than the box overflow, and puts spaces inside `AIエージェント` and drops the one between two
    Japanese words. Here a word wider than the box is broken where the line ends, and the spaces are exactly the text's own."""
    lines, cur = [], ""
    for tok, glued in _pieces(text):
        sep = "" if (not cur or glued) else " "
        if width(cur + sep + tok, px * scale) <= max_w:
            cur += sep + tok
            continue
        if cur:
            lines.append(cur)
        cur = ""
        for ch in tok:
            if cur and width(cur + ch, px * scale) > max_w:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
    if cur:
        lines.append(cur)
    return lines or [""]


def _columns(n: int, sizes: tuple[int, int]) -> int:
    """2 or 3 columns so that no row is left with a single card when it can be avoided."""
    return sizes[0] if n in (2, 4) else sizes[1]


def build(facts: dict, draft: dict, t: dict, st: Style) -> dict:
    """The scene: {"w", "h", "items"}. Items are drawn in order; a text item's `inside` is the index of the rectangle that holds it."""
    items: list[dict] = []

    def add(**kw) -> int:
        items.append(kw)
        return len(items) - 1

    def text(x, y, w, s, px, *, weight=400, color="ink", align="left", lh=None, inside=None, center_in=None) -> int:
        """Adds wrapped text, returns its height. `center_in=(top, height)` centres it vertically inside that band."""
        lh = lh or st.body_lh
        s = one_line(s)
        lines = wrap(s, px, w, st.wscale)
        h = math.ceil(len(lines) * px * lh)
        if center_in:
            y = center_in[0] + (center_in[1] - h) / 2
        add(k="text", x=x, y=y, w=w, h=h, text=s, lines=lines, px=px, weight=weight, color=color, align=align, lh=lh, inside=inside)
        return h

    hiw = draft["how_it_works"]
    comps, edges, steps = hiw["components"], hiw["flow"], hiw["steps"]

    # --- header: a band, the bucket chip, the title and the hook ---------------------------------------------------------
    band = add(k="rect", role="header", x=0, y=0, w=W, h=0) if st.band else None
    accent = add(k="rect", role="accent", x=0, y=0, w=W, h=10) if st.band else None
    head_y = 52 if st.band else 24
    label = one_line(t["bucket"].get(facts["bucket"], facts["bucket"]))
    chip_w = int(width(label, st.chip * st.wscale)) + 44
    chip = add(k="rect", role="chip", x=M, y=head_y, w=chip_w, h=40, round=True)
    text(M, 0, chip_w, label, st.chip, weight=700, color="chip_ink", align="center", inside=chip, center_in=(head_y, 40))
    y = head_y + 60
    y += text(M, y, CW, draft["title"], st.title, weight=800, color="title", lh=st.title_lh) + 22
    y += text(M, y, CW, draft["hook"], st.hook, color="hook")
    if st.band:
        y += 40
        items[band]["h"] = y
        items[accent]["y"] = y
        y += 10 + 44
    else:
        y += 36

    def section(heading: str, lane: int = 18):
        """Opens a framed section; returns the panel's index and the y where its content starts."""
        panel = add(k="rect", role="panel", x=M - 20, y=y, w=CW + 40, h=0)
        h = text(M, y + 20, CW, heading, st.head, weight=800, color="head")
        return panel, y + 20 + h + lane

    def close(panel: int, bottom: float) -> None:
        nonlocal y
        items[panel]["h"] = math.ceil(bottom + 26 - items[panel]["y"])
        y = items[panel]["y"] + items[panel]["h"] + 36

    # --- the moving parts: a grid by index; every flow edge is an arrow that cannot cross a card -------------------------
    cols = _columns(len(comps), (2, 3))
    links = list(dict.fromkeys((a, b) for a, b in edges if a != b and 0 <= a < len(comps) and 0 <= b < len(comps)))
    # room above the first row only when an arrow has to arc over it (two cards of that row that are not neighbours)
    arc = any(a // cols == b // cols == 0 and abs(a % cols - b % cols) > 1 for a, b in links)
    panel, top = section(t["parts"], lane=46 if arc else 18)
    gap_x, gap_y = 120, 74
    bw = (CW - (cols - 1) * gap_x) // cols
    blocks = []
    pic = st.icon if st.icon and all(isinstance(c.get("icon"), str) and c["icon"] in icons.NAMES for c in comps) else 0
    off = pic + 16 if pic else 0                               # the text starts right of the pictogram
    for c in comps:
        name = wrap(c["name"], st.name, bw - 40 - off, st.wscale)
        role = wrap(c["role"], st.role, bw - 40 - off, st.wscale)
        blocks.append((name, role, max(22 + math.ceil(len(name) * st.name * 1.25) + 10 + math.ceil(len(role) * st.role * st.body_lh) + 22,
                                       44 + pic)))
    rows = [blocks[i:i + cols] for i in range(0, len(blocks), cols)]
    row_h = [max(b[2] for b in row) for row in rows]
    row_y = [top]
    for h in row_h[:-1]:
        row_y.append(row_y[-1] + h + gap_y)
    pos = {}
    for i, (name, role, _) in enumerate(blocks):
        r, c = divmod(i, cols)
        x, yy = M + c * (bw + gap_x), row_y[r]
        pos[i] = (x, yy, bw, row_h[r])
        card = add(k="rect", role=f"layer{i % 4}", x=x, y=yy, w=bw, h=row_h[r], comp=i)
        if pic:
            add(k="icon", name=comps[i]["icon"], x=x + 20, y=yy + 22, d=pic)
        ny = yy + 22
        ny += text(x + 20 + off, ny, bw - 40 - off, comps[i]["name"], st.name, weight=800, lh=1.25, inside=card) + 10
        text(x + 20 + off, ny, bw - 40 - off, comps[i]["role"], st.role, inside=card)
    for a, b in links:
        add(k="arrow", pts=_route(a, b, cols, pos, row_y, row_h, gap_y), link=(a, b))
    close(panel, row_y[-1] + row_h[-1])

    # --- the steps: two columns of numbered cards ------------------------------------------------------------------------
    panel, top = section(t["how"])
    sw, tx = (CW - 40) // 2, 94
    tw = sw - tx - 22
    laid = []
    for s in steps:
        head = wrap(s["title"], st.step_title, tw, st.wscale) if s.get("title") else []
        body = wrap(s["text"], st.step_text, tw, st.wscale)
        h = 22 + (math.ceil(len(head) * st.step_title * 1.25) + 8 if head else 0) + math.ceil(len(body) * st.step_text * st.body_lh) + 22
        laid.append((head, body, max(h, 100)))
    srows = [laid[i:i + 2] for i in range(0, len(laid), 2)]
    sy = top
    for r, row in enumerate(srows):
        rh = max(b[2] for b in row)
        for c, (head, body, _) in enumerate(row):
            n = r * 2 + c
            x = M + c * (sw + 40)
            card = add(k="rect", role=f"layer{n % 4}", x=x, y=sy, w=sw, h=rh, step=n)
            add(k="badge", x=x + 22, y=sy + 22, d=56, label=str(n + 1))
            ty = sy + 22
            if head:
                ty += text(x + tx, ty, tw, steps[n]["title"], st.step_title, weight=800, lh=1.25, inside=card) + 8
            text(x + tx, ty, tw, steps[n]["text"], st.step_text, inside=card)
            if c == 0 and len(row) == 2:                    # the hand-off to the next step on the same row
                add(k="arrow", pts=[(x + sw + 4, sy + rh / 2), (x + sw + 36, sy + rh / 2)], step=n)
        sy += rh + 24
    close(panel, sy - 24)

    # --- what to learn: cards with a tick --------------------------------------------------------------------------------
    panel, top = section(t["learn"])
    learn = draft["learn"]
    lcols = 2 if len(learn) == 4 else 3
    lw = (CW - (lcols - 1) * 30) // lcols
    ltw = lw - 76 - 20
    lrows = [learn[i:i + lcols] for i in range(0, len(learn), lcols)]
    ly = top
    for r, row in enumerate(lrows):
        shaped = [wrap(s, st.learn, ltw, st.wscale) for s in row]
        rh = max(100, max(40 + math.ceil(len(w_) * st.learn * st.body_lh) for w_ in shaped))
        for c, s in enumerate(row):
            n = r * lcols + c
            x = M + c * (lw + 30)
            card = add(k="rect", role=f"note{n % 2}", x=x, y=ly, w=lw, h=rh)
            add(k="tick", x=x + 20, y=ly + 20, d=40)
            text(x + 76, ly + 20, ltw, s, st.learn, color="learn_ink", inside=card)
        ly += rh + 24
    close(panel, ly - 24)

    # --- footer: the same source line as the digest, without a link ------------------------------------------------------
    sep = t.get("sep", ",")
    foot = (f"{t['source']}: {facts['full_name']} · {t['license']}: {facts['license']} · "
            f"{fmt_int(facts['stars'], sep)} {t['stars']} · {t['scanned']} {facts['scanned']}")
    foot_y = y - 10
    bottom = foot_y + text(M, foot_y, CW, foot, st.foot, color="muted")
    return {"w": W, "h": math.ceil(bottom + 40), "items": items}


def _route(a: int, b: int, cols: int, pos: dict, row_y: list, row_h: list, gap_y: float) -> list[tuple[float, float]]:
    """Points of the arrow from card a to card b. It leaves and enters through the sides that face the other card, and a
    long hop runs through the empty lane between rows (or above the first row), never over a card."""
    ra, ca = divmod(a, cols)
    rb, cb = divmod(b, cols)
    xa, ya, wa, ha = pos[a]
    xb, yb, wb, hb = pos[b]
    mid_a, mid_b = ya + ha / 2, yb + hb / 2
    if ra == rb and abs(ca - cb) == 1:
        return [(xa + wa, mid_a), (xb, mid_b)] if cb > ca else [(xa, mid_a), (xb + wb, mid_b)]
    if ra == rb:
        lane = ya - 26
        return [(xa + wa / 2, ya), (xa + wa / 2, lane), (xb + wb / 2, lane), (xb + wb / 2, yb)]
    if ca == cb and abs(ra - rb) == 1:
        return [(xa + wa / 2, ya + ha), (xb + wb / 2, yb)] if rb > ra else [(xa + wa / 2, ya), (xb + wb / 2, yb + hb)]
    if ra < rb:
        lane = row_y[ra] + row_h[ra] + gap_y / 2
        return [(xa + wa / 2, ya + ha), (xa + wa / 2, lane), (xb + wb / 2, lane), (xb + wb / 2, yb)]
    lane = row_y[ra] - gap_y / 2
    return [(xa + wa / 2, ya), (xa + wa / 2, lane), (xb + wb / 2, lane), (xb + wb / 2, yb + hb)]
