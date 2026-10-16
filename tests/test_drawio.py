"""The draw.io diagram: drawn from a draft by script, so it is checked like the SVGs and the other editor files are.

What must hold: every word comes from the draft, the labels or the facts; the pictograms are only ever the closed set, embedded
(never a link); connectors are attached to real cards; nothing leaves the page; README text cannot become markup; the same draft
gives the same bytes (`rerender` relies on that); and a draft that names no icons still draws.
"""

import base64
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from radar import boards, drawio, excalidraw, icons, moda, pipeline
from radar.github import GitHub
from radar.labels import L
from radar.llm import Gateway
from tests.support import TODAY, make_draft
from tests.test_boards import FACTS, HOSTILE, LANGS, allowed, cfg, compact, extreme, snapshot

NAMES = ["terminal", "route", "settings", "stethoscope", "database", "cloud"]


def with_icons(draft, names=NAMES):
    for c, name in zip(draft["how_it_works"]["components"], names):
        c["icon"] = name
    return draft


def without_icons(draft):
    for c in draft["how_it_works"]["components"]:
        c.pop("icon", None)
    return draft


def parse(text):
    root = ET.fromstring(text)
    assert root.tag == "mxfile"
    cells = {c.get("id"): c for c in root.iter("mxCell")}
    return root, cells


def geometry(cell):
    g = cell.find("mxGeometry")
    return {k: float(g.get(k)) for k in ("x", "y", "width", "height") if g.get(k) is not None}


def label_texts(cell):
    """The words of a label: one string per <div> block, the way the renderer wrote them."""
    value = cell.get("value") or ""
    blocks = re.findall(r"<div[^>]*>(.*?)</div>", value) or ([value] if value else [])
    return [html.unescape(re.sub(r"<[^>]+>", "", b.replace("<br>", ""))) for b in blocks]


def style(cell):
    return dict(part.split("=", 1) for part in cell.get("style", "").split(";") if "=" in part)


def images(cells):
    return [c for c in cells.values() if style(c).get("shape") == "image"]


def connectors(cells):
    return [c for c in cells.values() if c.get("edge") == "1" and c.get("source")]


def absolute(cell, cells):
    """(x, y, w, h) on the page; a child's geometry is relative to its parent."""
    g = geometry(cell)
    parent = cells.get(cell.get("parent"))
    ox, oy = (0, 0) if parent is None or parent.get("id") == "1" else absolute(parent, cells)[:2]
    return g["x"] + ox, g["y"] + oy, g["width"], g["height"]


# --- provenance: nothing on the picture is new text ----------------------------------------------------------------------
@pytest.mark.parametrize("lang", LANGS)
def test_every_word_on_the_diagram_comes_from_the_draft_the_labels_or_the_facts(lang):
    draft = with_icons(make_draft({}, lang))
    _, cells = parse(drawio.diagram(FACTS, draft, L[lang]))
    ok = allowed(FACTS, draft, lang)
    shown = [t for c in cells.values() for t in label_texts(c)]
    assert shown and [t for t in shown if compact(t) not in ok] == []


def test_no_pictogram_name_and_no_connector_label_is_ever_shown_as_text():
    draft = with_icons(make_draft({}, "en"))
    _, cells = parse(drawio.diagram(FACTS, draft, L["en"]))
    shown = " ".join(t for c in cells.values() for t in label_texts(c))
    assert not any(name in shown for name in NAMES[:3])
    assert all(not c.get("value") for c in cells.values() if c.get("edge") == "1")


# --- pictograms ------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("lang", LANGS)
def test_each_component_gets_its_own_embedded_pictogram_and_nothing_else_is_an_image(lang):
    draft = with_icons(make_draft({}, lang))
    text = drawio.diagram(FACTS, draft, L[lang])
    _, cells = parse(text)
    pics = images(cells)
    assert len(pics) == len(draft["how_it_works"]["components"])
    for pic, comp in zip(pics, draft["how_it_works"]["components"]):
        uri = style(pic)["image"]
        assert uri == icons.data_uri(comp["icon"], size=56, tile=drawio.NAVY)           # the closed set's own bytes
        assert base64.b64decode(uri.split(",", 1)[1]).decode("ascii") == icons.svg(comp["icon"], size=56, tile=drawio.NAVY)
    assert not re.search(r"image=(?!data:image/svg\+xml,)", text) and "href" not in text.lower() and 'link="' not in text


def test_pictograms_are_children_of_their_card_so_they_move_with_it():
    draft = with_icons(make_draft({}, "en"))
    _, cells = parse(drawio.diagram(FACTS, draft, L["en"]))
    for pic in images(cells):
        card = cells[pic.get("parent")]
        cx, cy, cw, ch = absolute(card, cells)
        px, py, pw, ph = absolute(pic, cells)
        assert cx < px and cy < py and px + pw < cx + cw and py + ph < cy + ch


def test_text_starts_to_the_right_of_the_pictogram_and_uses_the_whole_card_when_there_is_none():
    with_pics = parse(drawio.diagram(FACTS, with_icons(make_draft({}, "en")), L["en"]))[1]
    bare = parse(drawio.diagram(FACTS, without_icons(make_draft({}, "en")), L["en"]))[1]
    left = lambda cells, name: next(float(style(c)["spacingLeft"]) for c in cells.values() if name in (c.get("value") or "") and "spacingLeft" in style(c))
    assert left(with_pics, "Planner") == 20 + 56 + 16 and left(bare, "Planner") == 20
    assert images(bare) == []


def test_a_draft_that_names_icons_for_only_some_components_or_unknown_ones_draws_none():
    partial = with_icons(make_draft({}, "en"), ["terminal", None, "route"])
    unknown = with_icons(make_draft({}, "en"), ["terminal", '"><script>', "route"])
    for draft in (partial, unknown):
        text = drawio.diagram(FACTS, draft, L["en"])
        ET.fromstring(text)
        assert images(parse(text)[1]) == []


def test_icons_change_nothing_in_the_other_files_of_a_digest():
    for lang in LANGS:
        a, b = with_icons(make_draft({}, lang)), without_icons(make_draft({}, lang))
        assert excalidraw.board(FACTS, a, L[lang]) == excalidraw.board(FACTS, b, L[lang])
        assert moda.markup(FACTS, a, L[lang], lang) == moda.markup(FACTS, b, L[lang], lang)


# --- structure: connectors are attached, geometry is inside the page ---------------------------------------------------------
@pytest.mark.parametrize("make", [lambda lang: with_icons(make_draft({}, lang)), lambda lang: with_icons(extreme(lang))])
@pytest.mark.parametrize("lang", LANGS)
def test_ids_are_unique_connectors_join_real_cards_and_everything_is_on_the_page(lang, make):
    draft = make(lang)
    text = drawio.diagram(FACTS, draft, L[lang])
    root, cells = parse(text)
    ids = [c.get("id") for c in root.iter("mxCell")]
    assert len(ids) == len(set(ids)) and ids[:2] == ["0", "1"]
    for c in cells.values():
        if c.get("edge") == "1":
            assert c.find("mxGeometry") is not None and c.find("mxGeometry").get("relative") == "1"       # draw.io drops edges without it
            for end in ("source", "target"):
                if c.get(end):
                    assert cells[c.get(end)].get("vertex") == "1"
    page = root.find("diagram/mxGraphModel")
    w, h = float(page.get("pageWidth")), float(page.get("pageHeight"))
    for c in cells.values():
        if c.get("vertex") == "1":
            x, y, cw, ch = absolute(c, cells)
            assert -0.5 <= x and -0.5 <= y and x + cw <= w + 0.5 and y + ch <= h + 0.5, (c.get("id"), x, y, cw, ch, w, h)


def test_every_flow_edge_is_one_attached_connector_and_steps_hand_off_to_the_next():
    draft = with_icons(make_draft({}, "en"))
    draft["how_it_works"]["flow"] = [[0, 1], [1, 2], [2, 0], [0, 1]]                       # a repeated edge is drawn once
    _, cells = parse(drawio.diagram(FACTS, draft, L["en"]))
    card = {c["name"]: next(cid for cid, x in cells.items() if c["name"] in (x.get("value") or "") and x.get("vertex") == "1")
            for c in draft["how_it_works"]["components"]}
    names = [c["name"] for c in draft["how_it_works"]["components"]]
    pairs = [(e.get("source"), e.get("target")) for e in connectors(cells) if e.get("source") in card.values()]
    assert sorted(pairs) == sorted({(card[names[a]], card[names[b]]) for a, b in [(0, 1), (1, 2), (2, 0)]})
    steps = [next(cid for cid, x in cells.items() if s["title"] in (x.get("value") or "") and x.get("vertex") == "1")
             for s in draft["how_it_works"]["steps"]]
    hand_offs = {(e.get("source"), e.get("target")) for e in connectors(cells) if e.get("source") in steps}
    assert hand_offs == {(steps[0], steps[1])}                                              # 3 steps: two share a row, the third is alone


def test_links_that_would_share_a_line_get_their_own_ports_and_lanes():
    """A->D and B->C cross a gap together; A->B and B->A, A->C and C->A face each other: none may share a lane or a port, or two
    arrows read as one."""
    draft = with_icons(extreme("en"))
    draft["how_it_works"]["components"] = draft["how_it_works"]["components"][:4]        # 2 columns: 0 1 / 2 3
    for flow in ([[0, 3], [1, 2]], [[0, 2], [2, 0]], [[0, 1], [1, 0]], [[0, 3], [3, 0], [1, 2]]):
        draft["how_it_works"]["flow"] = flow
        _, cells = parse(drawio.diagram(FACTS, draft, L["en"]))
        comp = {pic.get("parent") for pic in images(cells)}
        edges = [c for c in connectors(cells) if c.get("source") in comp]
        assert len(edges) == len(flow)
        # a line is its two attachment points, whichever way the arrow points: A->C and C->A at the same ports would be one line
        lines = [frozenset({(e.get("source"), style(e)["exitX"], style(e)["exitY"]), (e.get("target"), style(e)["entryX"], style(e)["entryY"])})
                 for e in edges]
        assert len(set(lines)) == len(lines), (flow, lines)
        with_lane = [e for e in edges if e.find("mxGeometry/Array") is not None]
        lanes = [e.find("mxGeometry/Array/mxPoint").get("y") for e in with_lane]
        assert len(set(lanes)) == len(lanes), (flow, lanes)
        assert all(style(e).get("jumpStyle") == "arc" for e in with_lane)


# --- safety: a README sentence cannot become markup --------------------------------------------------------------------------------
def test_hostile_text_stays_inert_text_in_the_diagram():
    draft = with_icons(make_draft({}, "en"))
    hiw = draft["how_it_works"]
    for i, text in enumerate(HOSTILE):
        hiw["components"][i % 3]["name"], hiw["components"][i % 3]["role"] = text, text
        hiw["steps"][i % 3]["text"] = text
    draft["title"], draft["hook"], draft["learn"][0] = HOSTILE[0], HOSTILE[1], HOSTILE[2]
    text = drawio.diagram(FACTS, draft, L["en"])
    assert not any(ord(c) < 32 and c not in "\n\t" for c in text)
    root, cells = parse(text)                                            # one well-formed document
    assert {e.tag for e in root.iter()} <= {"mxfile", "diagram", "mxGraphModel", "root", "mxCell", "mxGeometry", "mxPoint", "Array"}
    assert all(c.get("link") is None for c in cells.values()) and all(c.get("tooltip") is None for c in cells.values())
    for c in cells.values():                                             # HTML in a label is only the renderer's own div and br
        assert set(re.findall(r"</?([a-zA-Z]+)", c.get("value", ""))) <= {"div", "br"}
    shown = " ".join(t for c in cells.values() for t in label_texts(c))
    assert "alert(1)" in shown and "https://evil.example" in shown          # the words arrive, as words
    assert not re.search(r"image=(?!data:image/svg\+xml,)", text)


# --- the files ----------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("lang", LANGS)
def test_the_same_draft_gives_the_same_bytes_and_a_valid_file(lang):
    draft = with_icons(make_draft({}, lang))
    first = drawio.diagram(FACTS, draft, L[lang])
    assert first == drawio.diagram(FACTS, draft, L[lang])
    root, _ = parse(first)
    assert root.get("compressed") == "false" and root.find("diagram").get("name") == FACTS["full_name"]


def test_icons_in_the_stored_draft_are_what_the_diagram_draws_after_a_run(tmp_path, servers):
    report = pipeline.run(cfg(picks_per_run=2, langs=["vi", "en", "ja"]), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    assert report["ok"], report
    folders = [p for p in (tmp_path / "digests" / "2026-10-14").iterdir() if p.is_dir()]
    assert folders
    for folder in folders:
        for lang in LANGS:
            draft = json.loads((folder / f"draft-{lang}.json").read_text(encoding="utf-8"))["draft"]
            _, cells = parse((folder / f"drawio-{lang}.drawio").read_text(encoding="utf-8"))
            names = [c["icon"] for c in draft["how_it_works"]["components"]]
            assert len(names) and [base64.b64decode(style(p)["image"].split(",", 1)[1]).decode() for p in images(cells)] == \
                [icons.svg(n, size=56, tile=drawio.NAVY) for n in names]
    before = snapshot(tmp_path)
    for p in before:
        if p.endswith(".drawio"):
            (tmp_path / p).unlink()
    assert pipeline.rerender(cfg(langs=["vi", "en", "ja"]), tmp_path)["rerendered"] == ["2026-10-14"]
    assert snapshot(tmp_path) == before
