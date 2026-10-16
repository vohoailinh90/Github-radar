"""A closed set of pictograms for the diagrams. The writer model names one per component; the renderer draws it.

The pictures are Lucide icons (ISC licence, docs/third-party/lucide/), copied byte for byte into this folder; `index.json` holds
their sha256, a one-line meaning for the writer prompt and the version they come from. A model never writes SVG or a path: it
returns one of `NAMES`, `gates.schema` refuses anything else, and `svg()` re-serialises only the shapes found in these files
(an allowlist of elements and attributes), never anything it was handed at run time. The one paint a file may carry is
`fill="currentColor"` (the dot of a key), drawn in the icon's ink.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG_NS = "{http://www.w3.org/2000/svg}"
# What a Lucide icon is made of. Anything else in a file is refused, so a swapped-in file cannot carry a script or a link.
SHAPES = {"path": {"d", "fill"}, "circle": {"cx", "cy", "r", "fill"}, "ellipse": {"cx", "cy", "rx", "ry"}, "line": {"x1", "y1", "x2", "y2"},
          "polyline": {"points"}, "polygon": {"points"}, "rect": {"x", "y", "width", "height", "rx", "ry"}}
_NUMBERS = re.compile(r"[-0-9a-zA-Z\s.,]*")
_COLOUR = re.compile(r"#[0-9A-Fa-f]{6}")


@lru_cache(maxsize=1)
def index() -> dict:
    return json.loads((HERE / "index.json").read_text(encoding="utf-8"))


NAMES = tuple(sorted(index()["icons"]))


def gloss(name: str) -> str:
    return index()["icons"][name]["gloss"]


def prompt_list() -> str:
    """`name = meaning` per line: what the writer sees. The names are the only values a draft may use for `icon`."""
    return "\n".join(f"{name} = {gloss(name)}" for name in NAMES)


@lru_cache(maxsize=None)
def shapes(name: str) -> tuple[tuple[str, tuple[tuple[str, str], ...]], ...]:
    """The drawing elements of one icon as (tag, ((attribute, value), ...)); ValueError for anything outside the allowlist."""
    if name not in index()["icons"]:
        raise ValueError(f"unknown icon {name!r}")
    try:
        root = ET.fromstring((HERE / f"{name}.svg").read_text(encoding="utf-8"))
    except ET.ParseError as exc:
        raise ValueError(f"{name}: not valid XML ({exc})") from exc
    out = []
    for el in root:
        tag = el.tag.removeprefix(SVG_NS)
        if tag not in SHAPES or len(el):
            raise ValueError(f"{name}: unexpected element <{tag}>")
        attrs = tuple(sorted(el.attrib.items()))
        for key, value in attrs:
            if key not in SHAPES[tag] or not _NUMBERS.fullmatch(value) or (key == "fill" and value != "currentColor"):
                raise ValueError(f"{name}: unexpected attribute {key}={value!r} on <{tag}>")
        out.append((tag, attrs))
    if not out:
        raise ValueError(f"{name}: no shapes")
    return tuple(out)


def svg(name: str, *, size: int = 56, tile: str = "#0B1B3A", ink: str = "#FFFFFF") -> str:
    """A round tile with the icon in it, as a stand-alone SVG `size` px wide. `tile` and `ink` are colours chosen by the renderer."""
    if not (isinstance(size, int) and 8 <= size <= 512 and _COLOUR.fullmatch(tile) and _COLOUR.fullmatch(ink)):
        raise ValueError("size is a whole number of px, colours are #RRGGBB")
    k = size / 24 * 0.6                    # the 24-unit icon fills 60% of the tile
    shift = (size - 24 * k) / 2
    body = "".join(f"<{tag} " + " ".join(f'{key}="{ink if value == "currentColor" else value}"' for key, value in attrs) + "/>"
                   for tag, attrs in shapes(name))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<circle cx="{size / 2:g}" cy="{size / 2:g}" r="{size / 2:g}" fill="{tile}"/>'
            f'<g transform="translate({shift:g} {shift:g}) scale({k:g})" fill="none" stroke="{ink}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>')


def data_uri(name: str, **kw) -> str:
    """The icon as a draw.io image source: `data:image/svg+xml,<base64>` (draw.io writes no `;base64` because `;` ends a style entry)."""
    return "data:image/svg+xml," + base64.b64encode(svg(name, **kw).encode("ascii")).decode("ascii")


FILE = "icons-{lang}.json"            # beside draft-<lang>.json: {"components": [{"name": ..., "icon": ...}, ...]}


def overlay(draft: dict, data) -> dict:
    """The draft as it is drawn when a draft stored before icons existed has an icon file beside it: a copy with each component's
    `icon` filled in. A draft that already names icons wins, and a row whose name is not the component's or whose icon is not in
    the set is never applied (the gate refuses such a file before anything is drawn; this is the second lock). The stored draft
    is the model's answer and is never changed: only the copy that is handed to the renderer carries the icons."""
    comps = (draft.get("how_it_works") or {}).get("components") or []
    rows = data.get("components") if isinstance(data, dict) else None
    if not isinstance(rows, list) or len(rows) != len(comps) or any(isinstance(c, dict) and c.get("icon") not in (None, "") for c in comps):
        return draft
    shown = copy.deepcopy(draft)
    for comp, row in zip(shown["how_it_works"]["components"], rows):
        if isinstance(row, dict) and row.get("name") == comp.get("name") and isinstance(row.get("icon"), str) and row["icon"] in NAMES:
            comp["icon"] = row["icon"]
    return shown


def verify() -> list[str]:
    """Problems with the vendored files: a hash that no longer matches, a missing or extra file, a shape outside the allowlist."""
    problems = []
    listed = set(index()["icons"])
    present = {p.stem for p in HERE.glob("*.svg")}
    problems += [f"{n}.svg is listed in index.json but missing" for n in sorted(listed - present)]
    problems += [f"{n}.svg is in the folder but not in index.json" for n in sorted(present - listed)]
    for name in sorted(listed & present):
        if hashlib.sha256((HERE / f"{name}.svg").read_bytes()).hexdigest() != index()["icons"][name]["sha256"]:
            problems.append(f"{name}.svg differs from the hash in index.json")
        try:
            shapes(name)
        except ValueError as exc:
            problems.append(str(exc))
    return problems
