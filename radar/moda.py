"""The Moda design: a digest as Moda markup (XML), to be applied to a canvas with Moda's `canvas_apply_markup`.

Moda cannot be called from a scheduled run (its connector lives in the owner's Claude account, and this repository holds no key
for it), so the run stores the markup and a Claude session with the Moda connector applies it: docs/design-files.md.
The layout comes from `boards.py`. Every piece of text is XML-escaped and written only as element content, never as an
attribute or a tag, so a README sentence cannot add an element, an image or a link to the design.
"""

from __future__ import annotations

import re

from . import boards
from .svg import esc

NAVY, INK, MUTED, CREAM, CORAL, SUN = "#0B1B3A", "#1F2A44", "#5B6478", "#FFF6E5", "#FF6B4A", "#FFC83D"
FILL = {"header": NAVY, "accent": CORAL, "chip": SUN, "layer0": "#CFF5EE", "layer1": "#FFD9CF", "layer2": "#FFF0B8", "layer3": "#DDE8FF",
        "note0": NAVY, "note1": NAVY, "badge": NAVY}
RADIUS = {"chip": "full", "note0": 20, "note1": 20}      # every other card: 24
COLOR = {"title": "#FFFFFF", "hook": "#BFD0F0", "head": NAVY, "ink": INK, "muted": MUTED, "chip_ink": NAVY, "learn_ink": "#FFFFFF"}
STYLE = boards.Style(chip=20, title=54, hook=24, head=34, name=22, role=15, step_title=22, step_text=16, learn=16, foot=16,
                     body_lh=1.4, title_lh=1.25, wscale=1.15)     # measured on Moda: its line box is ~1.23 and Be Vietnam Pro runs ~15% wide
# Be Vietnam Pro covers Vietnamese and Latin. The Japanese font is named but NOT checked against Moda's font list (docs/design-files.md).
FONTS = {"vi": "Be Vietnam Pro", "en": "Be Vietnam Pro", "ja": "Noto Sans JP"}
# XML 1.0 forbids these; a stray one in a sentence would make Moda refuse the whole document.
_XML_BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿\ud800-\udfff]")


def _x(text) -> str:
    return esc(_XML_BAD.sub("", str(text)))


def _n(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def markup(facts: dict, draft: dict, t: dict, lang: str) -> str:
    scene = boards.build(facts, draft, t, STYLE)
    out = [f'<!-- radar: Moda canvas {scene["w"]}x{scene["h"]}; create it that size, then apply this markup -->',
           f'<content font-family="{esc(FONTS[lang])}">', f'<background fill="{CREAM}"/>']
    for item in scene["items"]:
        k = item["k"]
        if k == "rect":
            if item["role"] == "panel":                      # the dashed frame belongs to the Excalidraw board
                continue
            role = item["role"]
            stroke = f' stroke="{NAVY}" stroke-width="3"' if role.startswith("layer") else ""
            radius = "" if role in ("header", "accent") else f' corner-radius="{RADIUS.get(role, 24)}"'
            out.append(f'<rectangle x="{_n(item["x"])}" y="{_n(item["y"])}" width="{_n(item["w"])}" height="{_n(item["h"])}" '
                       f'fill="{FILL[role]}"{stroke}{radius}/>')
        elif k == "text":
            out.append(f'<text x="{_n(item["x"])}" y="{_n(item["y"])}" width="{_n(item["w"])}" height="{_n(item["h"])}" '
                       f'font-size="{item["px"]}" font-weight="{item["weight"]}" color="{COLOR[item["color"]]}" '
                       f'text-align="{item["align"]}" line-height="{item["lh"]}">{_x(item["text"])}</text>')
        elif k == "badge":
            out.append(f'<rectangle x="{_n(item["x"])}" y="{_n(item["y"])}" width="{item["d"]}" height="{item["d"]}" corner-radius="full" '
                       f'fill="{FILL["badge"]}" text="{_x(item["label"])}" font-size="28" font-weight="800" color="#FFFFFF"/>')
        elif k == "tick":
            x, y, d = item["x"], item["y"], item["d"]
            a, b, c = (x + d * 0.27, y + d * 0.52), (x + d * 0.44, y + d * 0.70), (x + d * 0.75, y + d * 0.32)
            for p, q in ((a, b), (b, c)):
                out.append(f'<line x1="{_n(p[0])}" y1="{_n(p[1])}" x2="{_n(q[0])}" y2="{_n(q[1])}" stroke="{SUN}" stroke-width="5"/>')
        elif k == "arrow":
            pts = item["pts"]
            for i, (p, q) in enumerate(zip(pts, pts[1:])):
                head = ' arrow-end="triangle" pointer-length="14" pointer-width="14"' if i == len(pts) - 2 else ""
                out.append(f'<line x1="{_n(p[0])}" y1="{_n(p[1])}" x2="{_n(q[0])}" y2="{_n(q[1])}" stroke="{CORAL}" stroke-width="5"{head}/>')
    out.append("</content>")
    return "\n".join(out) + "\n"
