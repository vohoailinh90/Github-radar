"""The draw.io diagram: drawn from a draft by script, so it is checked like the SVGs and the other editor files are.

What must hold: every word comes from the draft, the labels or the facts; the pictograms are only ever the closed set, embedded
(never a link); connectors are attached to real cards; nothing leaves the page; README text cannot become markup; the same draft
gives the same bytes (`rerender` relies on that); and a draft that names no icons still draws.
"""

import base64
import html
import json
import random
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from radar import boards, drawio, excalidraw, icons, moda, pipeline
from radar.github import GitHub
from radar.labels import L
from radar.config import ROOT
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


def paths(cells):
    """The polyline of every component connector as draw.io draws it: leave the port, run to the lane, along it, into the port."""
    cards = {pic.get("parent"): absolute(cells[pic.get("parent")], cells) for pic in images(cells)}
    out = []
    for e in connectors(cells):
        if e.get("source") not in cards:
            continue
        s, (ax, ay, aw, ah), (bx, by, bw, bh) = style(e), cards[e.get("source")], cards[e.get("target")]
        points = [(ax + float(s["exitX"]) * aw, ay + float(s["exitY"]) * ah)]
        points += [(float(p.get("x")), float(p.get("y"))) for p in e.findall("mxGeometry/Array/mxPoint")]
        points.append((bx + float(s["entryX"]) * bw, by + float(s["entryY"]) * bh))
        out.append((e, points))
    return out, list(cards.values())


def segments(points):
    return list(zip(points, points[1:]))


def overlap(p, q, tol=1.0):
    """True when two axis-parallel segments lie on one line and share more than `tol` px of it."""
    (x1, y1), (x2, y2) = p
    (u1, v1), (u2, v2) = q
    if abs(x1 - x2) < 0.05 and abs(u1 - u2) < 0.05 and abs(x1 - u1) < 0.5:
        return min(max(y1, y2), max(v1, v2)) - max(min(y1, y2), min(v1, v2)) > tol
    if abs(y1 - y2) < 0.05 and abs(v1 - v2) < 0.05 and abs(y1 - v1) < 0.5:
        return min(max(x1, x2), max(u1, u2)) - max(min(x1, x2), min(u1, u2)) > tol
    return False


def enters(seg, card, inset=2.0):
    (x1, y1), (x2, y2) = seg
    x, y, w, h = card
    return (min(x1, x2) < x + w - inset and max(x1, x2) > x + inset and min(y1, y2) < y + h - inset and max(y1, y2) > y + inset)


def check_lines(draft):
    _, cells = parse(drawio.diagram(FACTS, draft, L["en"]))
    drawn, cards = paths(cells)
    flat = []
    for e, points in drawn:
        for seg in segments(points):
            (x1, y1), (x2, y2) = seg
            assert abs(x1 - x2) < 0.05 or abs(y1 - y2) < 0.05, ("not orthogonal", e.get("id"), seg)       # a jog would be a different route
            assert not any(enters(seg, card) for card in cards), ("runs across a card", e.get("id"), seg)
            flat.append((e.get("id"), seg))
    for i, (ei, si) in enumerate(flat):
        for ej, sj in flat[i + 1:]:
            assert ei == ej or not overlap(si, sj), ("two connectors on one line", ei, si, ej, sj)
    return len(drawn)


def test_links_that_would_share_a_line_get_their_own_ports_and_lanes():
    """A->D and B->C cross a gap together; A->B and B->A face each other; A->D, A->E and B->E share cards and stubs: no two
    connectors may lie on one line, or two arrows read as one."""
    draft = with_icons(extreme("en"))
    draft["how_it_works"]["components"] = draft["how_it_works"]["components"][:4]        # 2 columns: 0 1 / 2 3
    for flow in ([[0, 3], [1, 2]], [[0, 2], [2, 0]], [[0, 1], [1, 0]], [[0, 3], [3, 0], [1, 2]]):
        draft["how_it_works"]["flow"] = flow
        assert check_lines(draft) == len(flow), flow
    draft = with_icons(extreme("en"))                                                        # 3 columns: 0 1 2 / 3 4 5
    for flow in ([[0, 3], [0, 4], [1, 4], [3, 4]], [[0, 2], [2, 0], [3, 5], [5, 3]], [[0, 5], [5, 0], [2, 3], [3, 2], [1, 4], [4, 1]]):
        draft["how_it_works"]["flow"] = flow
        assert check_lines(draft) == len(flow), flow


def test_a_hop_marks_every_connector_that_runs_in_a_lane():
    draft = with_icons(extreme("en"))
    draft["how_it_works"]["flow"] = [[0, 4], [1, 3], [0, 2], [3, 5]]                          # two cross the gap, two arc over a card
    _, cells = parse(drawio.diagram(FACTS, draft, L["en"]))
    drawn, _ = paths(cells)
    with_lane = [e for e, _ in drawn if e.find("mxGeometry/Array") is not None]
    assert len(with_lane) == 4 and all(style(e).get("jumpStyle") == "arc" for e in with_lane)


@pytest.mark.parametrize("seed", range(6))
def test_no_flow_a_draft_may_list_puts_two_connectors_on_one_line_or_a_connector_across_a_card(seed):
    rng = random.Random(seed)
    for _ in range(40):
        n = rng.randint(2, 6)
        draft = with_icons(extreme("en"))
        draft["how_it_works"]["components"] = draft["how_it_works"]["components"][:n]
        edges = [[a, b] for a in range(n) for b in range(n) if a != b]
        draft["how_it_works"]["flow"] = rng.sample(edges, rng.randint(1, min(12, len(edges))))
        check_lines(draft)


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


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_git_keeps_the_hashed_icon_bytes_as_they_are_on_a_checkout_that_converts_line_endings():
    for name in ("radar/icons/bell.svg", "radar/icons/index.json", "docs/third-party/lucide/LICENSE"):
        out = subprocess.run(["git", "check-attr", "text", name], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        assert out.strip().endswith("text: unset"), out
