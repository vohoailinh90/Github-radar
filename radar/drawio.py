"""The draw.io diagram: a digest as a `.drawio` file, open it at app.diagrams.net and edit it by hand.

The layout comes from `boards.py`; this module only writes it in draw.io's XML. What draw.io adds over the other two files:
- every card is one shape that holds its own text, so dragging a card moves its words, number, tick and pictogram with it;
- the arrows between components are connectors attached to the cards (`source`/`target`), with their own lanes and a hop where
  two cross, so they follow a card that is moved and two opposite arrows are never one line;
- each component carries a pictogram from the closed set in `icons/` when the draft names one for every component.
Text is the draft's own, set in Helvetica (draw.io's default; it falls back by itself for Vietnamese and Japanese). Nothing here
calls a model or the network, ids are numbered, and the same draft always gives the same bytes (`rerender` relies on that).
"""

from __future__ import annotations

import html

from . import boards, icons
from .moda import _XML_BAD, CORAL, CREAM, FILL, NAVY, SUN, COLOR

STYLE = boards.Style(chip=20, title=50, hook=24, head=34, name=22, role=16, step_title=22, step_text=17, learn=17, foot=16,
                     body_lh=1.4, title_lh=1.2, icon=56)
FONT = "Helvetica"
LANE = 26                   # distance between two connectors that cross the same gap between rows
FIXED = "movable=0;resizable=0;rotatable=0;deletable=0;editable=0;connectable=0;"      # the page behind the diagram


def _attr(text) -> str:
    return html.escape(_XML_BAD.sub("", str(text)), quote=True)


def _n(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _label(blocks: list[dict]) -> str:
    """The HTML of one label: a block per text item, the lines exactly as `boards.wrap` broke them."""
    parts, previous = [], None
    for b in blocks:
        gap = 0 if previous is None else max(round(b["y"] - (previous["y"] + previous["h"])), 0)
        lines = "<br>".join(html.escape(_XML_BAD.sub("", line), quote=False) for line in b["lines"])
        style = f"font-size:{b['px']}px;font-weight:{'bold' if b['weight'] >= 700 else 'normal'};line-height:{b['lh']};color:{COLOR[b['color']]}"
        parts.append(f'<div style="{style};margin-top:{gap}px">{lines}</div>' if gap else f'<div style="{style}">{lines}</div>')
        previous = b
    return "".join(parts)


class _Cells:
    def __init__(self) -> None:
        self.rows: list[str] = []
        self.count = 1                                     # ids 0 and 1 are the root and the layer

    def new_id(self) -> str:
        self.count += 1
        return f"c{self.count}"

    def vertex(self, x, y, w, h, style: str, value: str = "", parent: str = "1") -> str:
        cid = self.new_id()
        self.rows.append(f'<mxCell id="{cid}" value="{_attr(value)}" style="{style}" vertex="1" parent="{parent}">'
                         f'<mxGeometry x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" as="geometry"/></mxCell>')
        return cid

    def edge(self, style: str, *, source: str | None = None, target: str | None = None, waypoints=(), ends=None, parent: str = "1") -> str:
        cid = self.new_id()
        terms = (f' source="{source}"' if source else "") + (f' target="{target}"' if target else "")
        geometry = '<mxGeometry relative="1" as="geometry">'
        if ends:
            geometry += f'<mxPoint x="{_n(ends[0][0])}" y="{_n(ends[0][1])}" as="sourcePoint"/><mxPoint x="{_n(ends[1][0])}" y="{_n(ends[1][1])}" as="targetPoint"/>'
        if waypoints:
            geometry += '<Array as="points">' + "".join(f'<mxPoint x="{_n(x)}" y="{_n(y)}"/>' for x, y in waypoints) + "</Array>"
        self.rows.append(f'<mxCell id="{cid}" style="{style}" edge="1" parent="{parent}"{terms}>{geometry}</mxGeometry></mxCell>')
        return cid


def _connector_style(hop: bool = False, **ports) -> str:
    base = (f"html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;endArrow=block;endFill=1;endSize=4;strokeColor={CORAL};strokeWidth=4;"
            "exitPerimeter=0;entryPerimeter=0;" + ("jumpStyle=arc;jumpSize=14;" if hop else ""))
    return base + "".join(f"{k}={v};" for k, v in ports.items())


def _component_edges(cells: _Cells, ids: dict[int, str], boxes: dict[int, dict], links: list[tuple[int, int]]) -> None:
    """One connector per link. Neighbours join side to side; a longer hop leaves through the side that faces its target and runs
    in its own lane, so two links that cross the same gap (A->D and B->C) stay two lines and meet at one hop."""
    xs = sorted({b["x"] for b in boxes.values()})
    ys = sorted({b["y"] for b in boxes.values()})
    col = {i: xs.index(b["x"]) for i, b in boxes.items()}
    row = {i: ys.index(b["y"]) for i, b in boxes.items()}
    groups: dict[tuple, list[tuple[int, int]]] = {}
    for a, b in links:
        if row[a] != row[b]:
            groups.setdefault(("gap",) + tuple(sorted((row[a], row[b]))), []).append((a, b))
        elif abs(col[a] - col[b]) > 1:
            groups.setdefault(("arc", row[a]), []).append((a, b))
    both_ways = {(a, b) for a, b in links if (b, a) in links}        # A->B and B->A between neighbours run side by side, not on one line
    for a, b in links:
        ba, bb = boxes[a], boxes[b]
        f = (0.3 if a < b else 0.7) if (a, b) in both_ways else 0.5
        if row[a] == row[b] and abs(col[a] - col[b]) == 1:
            right = col[b] > col[a]
            cells.edge(_connector_style(exitX=int(right), exitY=f, entryX=int(not right), entryY=f), source=ids[a], target=ids[b])
        elif col[a] == col[b] and abs(row[a] - row[b]) == 1:
            down = row[b] > row[a]
            cells.edge(_connector_style(exitX=f, exitY=int(down), entryX=f, entryY=int(not down)), source=ids[a], target=ids[b])
        elif row[a] == row[b]:                                   # over the cards between: an arc above the row
            group = groups[("arc", row[a])]
            k, m = group.index((a, b)), len(group)
            f = 0.5 if m == 1 else 0.3 + 0.4 * k / (m - 1)
            lane = ba["y"] - 16 - 12 * min(k, 2)
            cells.edge(_connector_style(True, exitX=f, exitY=0, entryX=f, entryY=0), source=ids[a], target=ids[b],
                       waypoints=[(ba["x"] + f * ba["w"], lane), (bb["x"] + f * bb["w"], lane)])
        else:
            group = groups[("gap",) + tuple(sorted((row[a], row[b])))]
            k, m = group.index((a, b)), len(group)
            f = 0.5 if m == 1 else 0.3 + 0.4 * k / (m - 1)
            down = row[b] > row[a]
            upper = [bx for i, bx in boxes.items() if row[i] == min(row[a], row[b])]
            lower = [bx for i, bx in boxes.items() if row[i] == max(row[a], row[b])]
            lane = (max(bx["y"] + bx["h"] for bx in upper) + min(bx["y"] for bx in lower)) / 2 + (k - (m - 1) / 2) * LANE
            cells.edge(_connector_style(True, exitX=f, exitY=int(down), entryX=f, entryY=int(not down)), source=ids[a], target=ids[b],
                       waypoints=[(ba["x"] + f * ba["w"], lane), (bb["x"] + f * bb["w"], lane)])


def diagram(facts: dict, draft: dict, t: dict) -> str:
    scene = boards.build(facts, draft, t, STYLE)
    items = scene["items"]
    cells = _Cells()
    cells.vertex(0, 0, scene["w"], scene["h"], f"rounded=0;html=1;fillColor={CREAM};strokeColor=none;{FIXED}")

    inside: dict[int, list[dict]] = {}                       # the text items that sit in each rectangle, in order
    for item in items:
        if item["k"] == "text" and item["inside"] is not None:
            inside.setdefault(item["inside"], []).append(item)

    font = f"fontFamily={FONT};"
    ids: dict[int, str] = {}                                 # scene index of a rectangle -> its cell id
    pos: dict[int, dict] = {}
    comp_ids: dict[int, str] = {}
    comp_boxes: dict[int, dict] = {}
    step_ids: dict[int, str] = {}
    card = None                                              # the rectangle the next badge, tick or pictogram belongs to
    for index, item in enumerate(items):
        kind = item["k"]
        if kind == "rect":
            role = item["role"]
            if role == "panel":                              # the dashed frame belongs to the Excalidraw board
                continue
            blocks = inside.get(index, [])
            stroke = f"strokeColor={NAVY};strokeWidth=3;" if role.startswith("layer") else "strokeColor=none;"
            shape = "rounded=0;" if role in ("header", "accent") else f"rounded=1;arcSize={50 if role == 'chip' else 9 if role.startswith('note') else 8};"
            style = f"{shape}html=1;whiteSpace=wrap;fillColor={FILL[role]};{stroke}{font}"
            if blocks and role == "chip":
                style += "align=center;verticalAlign=middle;"
            elif blocks:
                first = blocks[0]
                style += (f"align=left;verticalAlign=top;spacingTop={_n(first['y'] - item['y'])};spacingLeft={_n(first['x'] - item['x'])};"
                          f"spacingRight={_n(item['x'] + item['w'] - first['x'] - first['w'])};spacing=0;")
            cid = cells.vertex(item["x"], item["y"], item["w"], item["h"], style, _label(blocks) if blocks else "")
            ids[index] = cid
            pos[index] = item
            card = index
            if "comp" in item:
                comp_ids[item["comp"]], comp_boxes[item["comp"]] = cid, item
            elif "step" in item:
                step_ids[item["step"]] = cid
        elif kind == "text" and item["inside"] is None:
            style = (f"text;html=1;whiteSpace=wrap;align={item['align']};verticalAlign=top;spacing=0;{font}"
                     f"fontSize={item['px']};fontColor={COLOR[item['color']]};{'fontStyle=1;' if item['weight'] >= 700 else ''}")
            cells.vertex(item["x"], item["y"], item["w"], item["h"], style, _label([item]))
        elif kind == "badge":
            c = pos[card]
            cells.vertex(item["x"] - c["x"], item["y"] - c["y"], item["d"], item["d"],
                         f"ellipse;html=1;aspect=fixed;fillColor={FILL['badge']};strokeColor=none;fontColor=#FFFFFF;fontSize=28;fontStyle=1;{font}",
                         item["label"], parent=ids[card])
        elif kind == "icon":
            c = pos[card]
            cells.vertex(item["x"] - c["x"], item["y"] - c["y"], item["d"], item["d"],
                         f"shape=image;html=1;aspect=fixed;imageAspect=0;image={icons.data_uri(item['name'], size=item['d'], tile=NAVY)};",
                         parent=ids[card])
        elif kind == "tick":
            c = pos[card]
            x, y, d = item["x"] - c["x"], item["y"] - c["y"], item["d"]
            cells.edge(f"html=1;endArrow=none;strokeColor={SUN};strokeWidth=5;", parent=ids[card], ends=((x + d * .27, y + d * .52), (x + d * .75, y + d * .32)),
                       waypoints=[(x + d * .44, y + d * .70)])

    comps = draft["how_it_works"]["components"]
    links = [(a, b) for a, b in dict.fromkeys(tuple(e) for e in draft["how_it_works"]["flow"])
             if a != b and 0 <= a < len(comps) and 0 <= b < len(comps)]
    _component_edges(cells, comp_ids, comp_boxes, links)
    for item in items:                                       # the hand-off from a step to the next one on the same row
        if item["k"] == "arrow" and "step" in item:
            n = item["step"]
            cells.edge(_connector_style(exitX=1, exitY=0.5, entryX=0, entryY=0.5), source=step_ids[n], target=step_ids[n + 1])

    name = _attr(facts["full_name"])
    model = (f'<mxGraphModel dx="1200" dy="900" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
             f'pageScale="1" pageWidth="{scene["w"]}" pageHeight="{scene["h"]}" background="{CREAM}" math="0" shadow="0">'
             '<root><mxCell id="0"/><mxCell id="1" parent="0"/>\n' + "\n".join(cells.rows) + "\n</root></mxGraphModel>")
    return f'<mxfile host="radar" compressed="false"><diagram id="radar" name="{name}">{model}</diagram></mxfile>\n'
