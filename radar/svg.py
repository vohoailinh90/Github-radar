"""Deterministic SVG diagrams. The model supplies structure (components, arrows); this draws it.

No model ever writes SVG, so a diagram cannot contain a wrong shape, a script or an external
reference. Every file has an explicit background and fixed colours, so it reads the same in
GitHub's light and dark themes.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

FONT = "system-ui,-apple-system,'Segoe UI','Noto Sans','Noto Sans CJK JP',sans-serif"
INK, MUTED, LINE, BG = "#0f172a", "#475569", "#cbd5e1", "#ffffff"
# fill, stroke, accent per layer (blue, teal, amber, violet): light fills keep INK text above 7:1.
LAYERS = [("#e0f2fe", "#0284c7"), ("#ccfbf1", "#0f766e"), ("#fef3c7", "#b45309"), ("#ede9fe", "#6d28d9")]


def esc(text) -> str:
    return escape(str(text), {'"': "&quot;"})


def _wide(ch: str) -> bool:
    o = ord(ch)
    return o >= 0x1100 and (o <= 0x115F or 0x2E80 <= o <= 0xA4CF or 0xAC00 <= o <= 0xD7A3
                            or 0xF900 <= o <= 0xFAFF or 0xFE30 <= o <= 0xFE6F or 0xFF00 <= o <= 0xFF60
                            or 0x1F300 <= o <= 0x1FAFF)


def _em(c: str) -> float:
    if _wide(c):
        return 1.0
    if c in "il.,'|!:;()[]":
        return 0.32
    return 0.68 if c.isupper() else 0.6 if c.isdigit() else 0.58 if c != " " else 0.3


def width(text: str, px: float) -> float:
    """Estimated advance width. Deliberately generous (bold UI fonts run wide) so text never meets the shape beside it."""
    return sum(px * _em(c) for c in text)


def fit(text: str, px: float, max_w: float, min_px: float = 13) -> tuple[str, float]:
    """Shrink a single unbreakable label (a repository name) before cutting it with an ellipsis."""
    while width(text, px) > max_w and px > min_px:
        px -= 1
    if width(text, px) > max_w:
        while text and width(text + "…", px) > max_w:
            text = text[:-1]
        text += "…"
    return text, px


def wrap(text: str, px: float, max_w: float, max_lines: int = 99) -> list[str]:
    lines, cur = [], ""
    tokens = []
    for word in str(text).split():
        if any(_wide(c) for c in word):
            tokens += list(word)           # CJK has no spaces: break between characters
        else:
            tokens.append(word)
    for tok in tokens:
        sep = "" if (not cur or (_wide(tok[0]) and _wide(cur[-1]))) else " "
        trial = cur + sep + tok
        if width(trial, px) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = tok
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .,;") + "…"
    return lines


def _text(x, y, lines, px, fill=INK, weight=400, anchor="start", lh=1.3) -> str:
    out = [f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{px}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">']
    for i, line in enumerate(lines):
        out.append(f'<tspan x="{x}" dy="{0 if i == 0 else round(px * lh, 1)}">{esc(line)}</tspan>')
    out.append("</text>")
    return "".join(out)


def _svg(w: int, h: int, body: str, title: str, desc: str = "") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-labelledby="t d"><title id="t">{esc(title)}</title><desc id="d">{esc(desc or title)}</desc>'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>{body}</svg>\n')


def fmt_int(n: int, sep: str = ",") -> str:
    return f"{n:,}".replace(",", sep)


def card(facts: dict, draft: dict, labels: dict) -> str:
    """1200x630 summary card: what it is, and the numbers that frame it."""
    title = wrap(draft["title"], 54, 1040, 2)
    one = wrap(draft["one_liner"], 30, 1040, 3)
    y = 190
    body = [f'<rect x="0" y="0" width="16" height="630" fill="{LAYERS[0][1]}"/>',
            f'<rect x="64" y="52" rx="18" ry="18" width="{int(width(labels["bucket"][facts["bucket"]], 24)) + 44}" height="42" fill="{LAYERS[0][0]}"/>',
            _text(86, 82, [labels["bucket"][facts["bucket"]]], 24, LAYERS[0][1], 700),
            _text(64, y, title, 54, INK, 800, lh=1.15)]
    y += int(54 * 1.15 * (len(title) - 1)) + 62
    body.append(_text(64, y, one, 30, MUTED))
    sep = labels.get("sep", ",")
    chips = [f"{fmt_int(facts['stars'], sep)} {labels['stars']}", f"{fmt_int(facts['forks'], sep)} {labels['forks']}",
             f"{labels['license']}: {facts['license']}"]
    if facts["language"]:
        chips.append(f"{labels['language']}: {facts['language']}")
    x = 64
    for chip in chips:
        w = int(width(chip, 26)) + 40
        if x + w > 1136:
            break
        body.append(f'<rect x="{x}" y="500" rx="12" ry="12" width="{w}" height="52" fill="#f1f5f9" stroke="{LINE}"/>')
        body.append(_text(x + 20, 535, [chip], 26, INK, 600))
        x += w + 16
    body.append(_text(64, 596, [f"{facts['full_name']}  ·  {labels['scanned']} {facts['scanned']}"], 22, MUTED))
    return _svg(1200, 630, "".join(body), draft["title"], draft["one_liner"])


def _layers(n: int, edges: list) -> list[int]:
    """Column per component: longest path from a source, with loop-back edges ignored."""
    adj: dict[int, list[int]] = {i: [] for i in range(n)}
    for a, b in edges:
        adj[a].append(b)
    state: dict[int, int] = {}
    back: set[tuple[int, int]] = set()

    def visit(u: int) -> None:
        state[u] = 1
        for v in adj[u]:
            if state.get(v) == 1:
                back.add((u, v))
            elif v not in state:
                visit(v)
        state[u] = 2

    for i in range(n):
        if i not in state:
            visit(i)
    dag = [(a, b) for a, b in edges if (a, b) not in back]
    layer = [0] * n
    for _ in range(n):
        for a, b in dag:
            layer[b] = max(layer[b], layer[a] + 1)
    return layer


ARROW = 12            # arrowhead size in pixels, independent of the line width
STUB = 16             # straight horizontal run into and out of each box, so the head sits on a straight line


def flow_layout(components: list[dict], edges: list[list[int]], *, bw: int = 300, gap: int = 96, pad: int = 40,
                name_px: int = 22, role_px: int = 17, vgap: int = 24) -> dict:
    """Columns by dependency depth; inside a column each box sits at the average height of the boxes that feed it, so a
    chain is a straight line and a fork is symmetric. Returns positions and sizes; `flow` only draws them."""
    n = len(components)
    layer = _layers(n, edges) if edges else list(range(n)) if n <= 4 else [i // 2 for i in range(n)]
    cols = max(layer) + 1
    boxes = []
    for c in components:
        name = wrap(c["name"], name_px, bw - 32, 2)
        role = wrap(c["role"], role_px, bw - 32, 5)
        boxes.append((name, role, 28 + int(name_px * 1.25 * len(name)) + 10 + int(role_px * 1.35 * len(role)) + 20))
    stacks = {col: [i for i in range(n) if layer[i] == col] for col in range(cols)}
    top: dict[int, float] = {}
    for col in range(cols):
        want: dict[int, float | None] = {}
        for i in stacks[col]:
            feeders = [top[a] + boxes[a][2] / 2 for a, b in edges if b == i and layer[a] < col and a in top]
            want[i] = sum(feeders) / len(feeders) if feeders else None
        order = sorted(stacks[col], key=lambda i: (want[i] is None, want[i] if want[i] is not None else 0, i))
        y, placed = 0.0, {}
        for i in order:
            placed[i] = y
            y += boxes[i][2] + vgap
        known = [i for i in order if want[i] is not None]
        if known:       # shift the stack so its boxes sit as close as possible to where their feeders point
            shift = sum(want[i] - (placed[i] + boxes[i][2] / 2) for i in known) / len(known)
            placed = {i: v + shift for i, v in placed.items()}
        top.update(placed)
    first = 70 + pad // 2
    lift = first - min(top.values())
    pos = {i: (pad + layer[i] * (bw + gap), int(round(top[i] + lift))) for i in range(n)}
    bottom = max(pos[i][1] + boxes[i][2] for i in range(n))
    return {"layer": layer, "boxes": boxes, "pos": pos, "bw": bw, "pad": pad, "name_px": name_px, "role_px": role_px,
            "total_w": pad * 2 + cols * bw + (cols - 1) * gap, "total_h": bottom + pad + 30}


def flow(components: list[dict], edges: list[list[int]], title: str) -> str:
    """Components as boxes in columns by dependency depth, arrows for the data/control flow."""
    lay = flow_layout(components, edges)
    layer, boxes, pos, bw = lay["layer"], lay["boxes"], lay["pos"], lay["bw"]
    total_w, total_h, pad, name_px, role_px = lay["total_w"], lay["total_h"], lay["pad"], lay["name_px"], lay["role_px"]
    body = [f'<defs><marker id="a" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="{ARROW}" '
            f'markerHeight="{ARROW}" orient="auto"><path d="M0 1 L10 5 L0 9 z" fill="{MUTED}"/></marker></defs>',
            _text(pad, 40, wrap(title, 24, total_w - 2 * pad, 1), 24, INK, 700)]
    for a, b in edges:                                    # arrows first: the boxes are drawn over their tips, so they meet flush
        (xa, ya), (xb, yb) = pos[a], pos[b]
        ca, cb = ya + boxes[a][2] // 2, yb + boxes[b][2] // 2
        if layer[b] > layer[a]:
            x1, x2 = xa + bw, xb
            mid = (x1 + STUB + x2 - STUB) / 2
            body.append(f'<path d="M{x1} {ca} L{x1 + STUB} {ca} C{mid} {ca} {mid} {cb} {x2 - STUB} {cb} L{x2} {cb}" fill="none" '
                        f'stroke="{MUTED}" stroke-width="2.5" stroke-linejoin="round" marker-end="url(#a)"/>')
        else:                                             # same column or a loop back: dashed, around the bottom
            x1, x2 = xa + bw / 2, xb + bw / 2
            low = total_h - 22
            body.append(f'<path d="M{x1} {ya + boxes[a][2]} L{x1} {ya + boxes[a][2] + STUB} C{x1} {low} {x2} {low} {x2} '
                        f'{yb + boxes[b][2] + STUB} L{x2} {yb + boxes[b][2]}" fill="none" stroke="{MUTED}" stroke-width="2" '
                        f'stroke-dasharray="7 6" marker-end="url(#a)"/>')
    for i, c in enumerate(components):
        x, y = pos[i]
        fill, stroke = LAYERS[layer[i] % len(LAYERS)]
        name, role, h = boxes[i]
        body.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{h}" rx="14" ry="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        body.append(_text(x + 16, y + 34, name, name_px, INK, 700, lh=1.25))
        ry = y + 34 + int(name_px * 1.25 * (len(name) - 1)) + 26
        body.append(_text(x + 16, ry, role, role_px, INK, 400, lh=1.35))
    return _svg(total_w, total_h, "".join(body), title, "; ".join(f"{c['name']}: {c['role']}" for c in components))


def steps(items: list[dict], title: str) -> str:
    """Numbered vertical strip, one card per step."""
    w, pad, tx = 1000, 32, 104
    rows, y = [], 78
    for i, s in enumerate(items, 1):
        head = wrap(s["title"], 24, w - tx - pad, 1) if s.get("title") else []
        text = wrap(s["text"], 19, w - tx - pad, 4)
        h = 24 + (30 if head else 0) + int(19 * 1.4 * len(text)) + 20
        fill, stroke = LAYERS[(i - 1) % len(LAYERS)]
        rows.append(f'<rect x="{pad}" y="{y}" width="{w - 2 * pad}" height="{h}" rx="14" ry="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        rows.append(f'<circle cx="{pad + 38}" cy="{y + h // 2}" r="24" fill="{stroke}"/>')
        rows.append(_text(pad + 38, y + h // 2 + 9, [str(i)], 26, "#ffffff", 800, "middle"))
        ty = y + 34
        if head:
            rows.append(_text(tx, ty, head, 24, INK, 700))
            ty += 30
        rows.append(_text(tx, ty, text, 19, INK, 400, lh=1.4))
        y += h + 16
    body = _text(pad, 46, wrap(title, 28, w - 2 * pad, 1), 28, INK, 700) + "".join(rows)
    return _svg(w, y + 16, body, title, "; ".join(s["text"] for s in items))


def bars(rows: list[tuple[str, int]], title: str, sep: str = ",") -> str:
    """Horizontal bars for one measure; the value sits at each bar's end so there is no legend to decode."""
    w, pad, lab = 1000, 32, 320
    body = [_text(pad, 46, wrap(title, 28, w - 2 * pad, 1), 28, INK, 700)]
    peak = max((v for _, v in rows), default=1) or 1
    y = 78
    for full, value in rows:
        owner, _, name = full.rpartition("/")
        name, px = fit(name, 21, lab - 20)
        bar_w = max(6, int((w - pad * 2 - lab - 130) * value / peak))
        if owner:
            owner, _ = fit(owner, 14, lab - 20)
            body.append(_text(pad, y + 16, [owner], 14, MUTED))
        body.append(_text(pad, y + 38, [name], px, INK, 600))
        body.append(f'<rect x="{pad + lab}" y="{y + 8}" width="{bar_w}" height="36" rx="6" ry="6" fill="{LAYERS[0][1]}"/>')
        body.append(_text(pad + lab + bar_w + 10, y + 34, [fmt_int(value, sep)], 20, INK, 700))
        y += 60
    return _svg(w, y + 20, "".join(body), title, ", ".join(f"{n}: {v}" for n, v in rows))
