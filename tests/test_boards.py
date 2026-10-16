"""The Excalidraw board and the Moda markup: drawn from a draft by script, so they are checked like the SVGs are.

What must hold: every word on them comes from the draft, the labels or the facts; nothing leaves its card or the canvas;
text from a README cannot become markup; and the same draft always gives the same bytes (`rerender` relies on that).
"""

import json
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from radar import boards, config, excalidraw, moda, pipeline, svg
from radar.github import GitHub
from radar.labels import L
from radar.llm import Gateway
from tests.support import TODAY, make_draft

FACTS = {"full_name": "owner/sample-agent-kit", "url": "https://github.com/owner/sample-agent-kit", "stars": 12345, "forks": 321,
         "license": "MIT", "language": "Python", "bucket": "ai", "scanned": "2026-10-14"}
LANGS = ("vi", "en", "ja")
STYLES = {"excalidraw": excalidraw.STYLE, "moda": moda.STYLE}


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def compact(text) -> str:
    """Without whitespace: a hard line break inside Japanese text must not count as a new word."""
    return re.sub(r"\s+", "", str(text))


def allowed(facts, draft, lang) -> set[str]:
    """Every sentence a picture may show: the draft's own, the fixed headings of that language, and the source line."""
    t = L[lang]
    out = set(strings(draft))
    out |= {t["parts"], t["how"], t["learn"], t["bucket"][facts["bucket"]], *map(str, range(1, 7))}
    out.add(f"{t['source']}: {facts['full_name']} · {t['license']}: {facts['license']} · "
            f"{svg.fmt_int(facts['stars'], t['sep'])} {t['stars']} · {t['scanned']} {facts['scanned']}")
    return {compact(x) for x in out}


def extreme(lang="vi") -> dict:
    """The largest draft the schema allows: 6 components with 12 edges (loops and long hops), 6 steps, 5 lessons, maximum text."""
    word = {"vi": "chuyển đổi dữ liệu nhanh chóng", "en": "converts incoming data quickly", "ja": "データを高速に変換して保存する仕組み"}[lang]

    def fill(n):
        text = (word + " ") * 40
        return text[:n].rstrip()
    comps = [{"name": fill(40), "role": fill(160), "evidence": "README"} for _ in range(6)]
    comps[2]["role"] = "x" * 60 + " " + fill(90)                      # a word wider than any card
    steps = [{"title": fill(40), "text": fill(220), "evidence": "README"} for _ in range(6)]
    edges = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 2], [2, 0], [1, 5], [3, 1], [0, 5], [4, 0]]
    return make_draft({}, lang, title=fill(70), hook=fill(110), learn=[fill(200)] * 5,
                      how_it_works={"steps": steps, "components": comps, "flow": edges})


def scenes(draft, lang):
    return {name: boards.build(FACTS, draft, L[lang], style) for name, style in STYLES.items()}


# --- provenance: nothing on the picture is new text ----------------------------------------------------------------------
@pytest.mark.parametrize("lang", LANGS)
def test_every_word_on_the_excalidraw_board_comes_from_the_draft_or_the_labels(lang):
    draft = make_draft({}, lang)
    doc = json.loads(excalidraw.board(FACTS, draft, L[lang]))
    ok = allowed(FACTS, draft, lang)
    shown = [e["text"] for e in doc["elements"] if e["type"] == "text"]
    assert shown and [t for t in shown if compact(t) not in ok] == []


@pytest.mark.parametrize("lang", LANGS)
def test_every_word_on_the_moda_markup_comes_from_the_draft_or_the_labels(lang):
    draft = make_draft({}, lang)
    root = ET.fromstring(moda.markup(FACTS, draft, L[lang], lang))
    ok = allowed(FACTS, draft, lang)
    shown = [(e.text or "") for e in root.iter("text")] + [e.get("text") for e in root.iter("rectangle") if e.get("text")]
    assert shown and [t for t in shown if compact(t) not in ok] == []


def test_the_flow_edges_are_drawn_as_plain_arrows_with_no_invented_label():
    draft = make_draft({}, "en")
    doc = json.loads(excalidraw.board(FACTS, draft, L["en"]))
    arrows = [e for e in doc["elements"] if e["type"] == "arrow"]
    assert len(arrows) >= len(draft["how_it_works"]["flow"])
    assert all("text" not in a and not a.get("boundElements") for a in arrows)


# --- layout: nothing leaves its card or the canvas ----------------------------------------------------------------------
@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("make", [lambda lang: make_draft({}, lang), extreme], ids=["normal", "largest-allowed"])
def test_text_stays_inside_its_card_and_everything_inside_the_canvas(lang, make):
    for name, scene in scenes(make(lang), lang).items():
        items, w, h = scene["items"], scene["w"], scene["h"]
        for item in items:
            if item["k"] == "text" and item["inside"] is not None:
                card = items[item["inside"]]
                chip = card["role"] == "chip"                                # a chip's text is centred across its whole width
                pad_x, pad_y = (0, 3) if chip else (12, 12)                  # air between the words and the edge of the card
                assert card["x"] + pad_x <= item["x"] and item["x"] + item["w"] <= card["x"] + card["w"] - pad_x + 0.5, (name, item["text"][:30])
                assert card["y"] + pad_y <= item["y"] and item["y"] + item["h"] <= card["y"] + card["h"] - pad_y + 0.5, (name, item["text"][:30])
            if item["k"] == "text":
                assert all(width_ <= item["w"] + 0.5 for width_ in (svg.width(line, item["px"] * (1 if name == "excalidraw" else 1.15))
                                                                      for line in item["lines"])), (name, item["text"][:30])
            xs = [p[0] for p in item["pts"]] if item["k"] == "arrow" else [item["x"], item["x"] + item.get("w", item.get("d", 0))]
            ys = [p[1] for p in item["pts"]] if item["k"] == "arrow" else [item["y"], item["y"] + item.get("h", item.get("d", 0))]
            assert min(xs) >= 0 and max(xs) <= w and min(ys) >= 0 and max(ys) <= h + 0.5, (name, item["k"])


@pytest.mark.parametrize("lang", LANGS)
def test_no_two_cards_of_the_same_section_overlap(lang):
    for name, scene in scenes(extreme(lang), lang).items():
        cards = [i for i in scene["items"] if i["k"] == "rect" and re.fullmatch(r"layer\d|note\d", i["role"])]
        for a in range(len(cards)):
            for b in range(a + 1, len(cards)):
                p, q = cards[a], cards[b]
                apart = p["x"] + p["w"] <= q["x"] or q["x"] + q["w"] <= p["x"] or p["y"] + p["h"] <= q["y"] or q["y"] + q["h"] <= p["y"]
                assert apart, (name, a, b)


def hits(p, q, card, margin=1.0) -> bool:
    """Does the (horizontal or vertical) segment p-q enter the inside of the card, ignoring a margin at its edge?"""
    x0, x1 = sorted((p[0], q[0]))
    y0, y1 = sorted((p[1], q[1]))
    return (x1 > card["x"] + margin and x0 < card["x"] + card["w"] - margin
            and y1 > card["y"] + margin and y0 < card["y"] + card["h"] - margin)


@pytest.mark.parametrize("lang", ["vi", "ja"])
def test_no_arrow_runs_across_a_card_whatever_edges_the_draft_lists(lang):
    rng = random.Random(7)
    for _ in range(60):
        n = rng.randint(2, 6)
        comps = [{"name": f"Part {i}", "role": "does one thing " * rng.randint(1, 10), "evidence": "README"} for i in range(n)]
        # cycles, repeated edges and pairs that point nowhere are all things a stored draft could list
        edges = [[rng.randint(0, n + 1), rng.randint(0, n + 1)] for _ in range(rng.randint(0, 12))]
        draft = make_draft({}, lang, how_it_works={**make_draft({}, lang)["how_it_works"], "components": comps, "flow": edges})
        for name, scene in scenes(draft, lang).items():
            cards = [i for i in scene["items"] if i["k"] == "rect" and i["role"].startswith("layer")]
            for arrow in (i for i in scene["items"] if i["k"] == "arrow"):
                for p, q in zip(arrow["pts"], arrow["pts"][1:]):
                    assert p[0] == q[0] or p[1] == q[1], (name, edges, p, q)             # every segment is horizontal or vertical
                    assert not any(hits(p, q, c) for c in cards), (name, n, edges, p, q)


def test_a_long_word_is_broken_across_lines_instead_of_overflowing_and_nothing_is_cut():
    lines = boards.wrap("x" * 70 + " tail", 18, 200)
    assert "".join(lines).replace(" ", "") == "x" * 70 + "tail" and all(svg.width(line, 18) <= 200 for line in lines)
    assert boards.wrap("", 18, 200) == [""]
    assert "".join(boards.wrap("日本語のとても長い説明文です", 20, 100)) == "日本語のとても長い説明文です"


MIXED = ["AIエージェント", "GitHubのAPI", "AIエージェントでGitHubのAPIを使う", "テキスト 日本語", "Python で書かれた CLI ツール",
         "日本語 English 日本語", "v2.0対応のREST API", "ファイル(config.yaml)を読む"]


@pytest.mark.parametrize("text", MIXED)
def test_wrapping_gives_back_exactly_the_text_it_was_given_when_there_is_room(text):
    assert boards.wrap(text, 18, 10 ** 6) == [text]                 # no space put inside `AIエージェント`, none dropped between words


@pytest.mark.parametrize("text", MIXED)
def test_wrapping_to_a_narrow_box_never_adds_a_space_inside_a_word(text):
    for max_w in (40, 70, 110, 200):
        lines = boards.wrap(text, 18, max_w)
        assert sum(line.count(" ") for line in lines) <= text.count(" "), (max_w, lines)     # a space can be eaten by a break, never added
        assert re.sub(r"\s+", "", "".join(lines)) == re.sub(r"\s+", "", text), (max_w, lines)


def test_wrapping_random_mixed_text_keeps_every_character_and_adds_no_space():
    rng, pool = random.Random(11), ["AI", "GitHub", "API", "エージェント", "日本語", "の", "を使う", "v2.0", "CLI", "ツール", "(x)"]
    for _ in range(200):
        text = "".join(rng.choice(pool) + rng.choice(["", "", " "]) for _ in range(rng.randint(1, 9))).strip()
        assert boards.wrap(text, 18, 10 ** 6) == [text]
        lines = boards.wrap(text, 18, rng.choice([50, 90, 160]))
        assert sum(line.count(" ") for line in lines) <= text.count(" ") and "".join(lines).replace(" ", "") == text.replace(" ", "")


@pytest.mark.parametrize("name", ["excalidraw", "moda"])
def test_mixed_script_text_reaches_the_picture_exactly_as_the_draft_wrote_it(name):
    title, hook, learn = "AIエージェントでGitHubのAPIを使う", "Python で書かれた CLI ツール", "テキスト 日本語"
    draft = make_draft({}, "ja", title=title, hook=hook)
    draft["learn"][0] = learn
    draft["how_it_works"]["components"][0]["name"] = "AIエージェント"
    if name == "excalidraw":
        doc = json.loads(excalidraw.board(FACTS, draft, L["ja"]))
        shown = [e["text"] for e in doc["elements"] if e["type"] == "text"]
    else:
        shown = [e.text for e in ET.fromstring(moda.markup(FACTS, draft, L["ja"], "ja")).iter("text")]
    assert {title, hook, learn, "AIエージェント"} <= set(shown)        # exact, not whitespace-insensitive like the provenance tests


# --- safety: a README sentence cannot become markup ---------------------------------------------------------------------
HOSTILE = ['<script>alert(1)</script>', '"><image src="https://evil.example/x.png"/>', "a & b < c > d ]]> <!-- x -->", "tab\x00nul\x0bvt\x1fesc",
           "</content><content><image src='https://evil.example/y.png'/>", "'; DROP TABLE x; --", "emoji 🧩 and مرحبا"]


def test_hostile_text_cannot_add_an_element_an_attribute_or_a_link_to_the_moda_markup():
    draft = make_draft({}, "en")
    hiw = draft["how_it_works"]
    for i, text in enumerate(HOSTILE):
        hiw["components"][i % 3]["name"], hiw["components"][i % 3]["role"] = text, text
        hiw["steps"][i % 3]["text"] = text
    draft["title"], draft["hook"], draft["learn"][0] = HOSTILE[0], HOSTILE[1], HOSTILE[2]
    text = moda.markup(FACTS, draft, L["en"], "en")
    root = ET.fromstring(text)                                          # still one well-formed document
    assert {e.tag for e in root.iter()} <= {"content", "background", "rectangle", "text", "line"}
    assert root.tag == "content" and "http" not in "".join(v for e in root.iter() for v in e.attrib.values())
    assert not any(ord(c) < 32 and c not in "\n\t" for c in text)
    shown = {boards.one_line(e.text or "") for e in root.iter("text")}
    assert boards.one_line(moda._XML_BAD.sub("", HOSTILE[2])) in shown        # the text itself arrives, escaped, as text


def test_hostile_text_stays_inert_text_in_the_excalidraw_file():
    draft = make_draft({}, "en", title=HOSTILE[1])
    doc = json.loads(excalidraw.board(FACTS, draft, L["en"]))
    assert {e["type"] for e in doc["elements"]} <= {"rectangle", "text", "arrow", "ellipse", "line"}
    assert all(e["link"] is None for e in doc["elements"]) and doc["files"] == {}
    assert "https://evil.example" in " ".join(e["text"] for e in doc["elements"] if e["type"] == "text")   # shown as text, never a link


# --- the files themselves --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("lang", LANGS)
def test_the_board_is_a_valid_excalidraw_file_and_the_same_draft_gives_the_same_bytes(lang):
    draft = make_draft({}, lang)
    first = excalidraw.board(FACTS, draft, L[lang])
    assert first == excalidraw.board(FACTS, draft, L[lang])
    doc = json.loads(first)
    ids = [e["id"] for e in doc["elements"]]
    assert doc["type"] == "excalidraw" and doc["version"] == 2 and len(ids) == len(set(ids))
    assert all(e["fontFamily"] == 5 for e in doc["elements"] if e["type"] == "text")        # Excalifont
    assert all(e["seed"] != e["versionNonce"] for e in doc["elements"])


@pytest.mark.parametrize("lang", LANGS)
def test_the_moda_markup_says_how_big_a_canvas_it_needs_and_the_same_draft_gives_the_same_bytes(lang):
    draft = make_draft({}, lang)
    first = moda.markup(FACTS, draft, L[lang], lang)
    assert first == moda.markup(FACTS, draft, L[lang], lang)
    scene = boards.build(FACTS, draft, L[lang], moda.STYLE)
    assert first.startswith(f"<!-- radar: Moda canvas {scene['w']}x{scene['h']};")
    assert f'font-family="{moda.FONTS[lang]}"' in first


# --- the pipeline writes them, and rerender draws them again byte for byte --------------------------------------------------
def cfg(**kw):
    c = config.load(path=config.ROOT / "none.yaml", env={})
    c.update(kw)
    return c


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted((root / "digests").rglob("*")) if p.is_file()}


def test_a_run_stores_a_board_and_moda_markup_beside_every_digest_and_rerender_restores_them_exactly(tmp_path, servers):
    report = pipeline.run(cfg(picks_per_run=2, langs=["vi", "en", "ja"]), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    assert report["ok"], report
    folders = [p for p in (tmp_path / "digests" / "2026-10-14").iterdir() if p.is_dir()]
    assert folders
    for folder in folders:
        for lang in LANGS:
            json.loads((folder / f"board-{lang}.excalidraw").read_text(encoding="utf-8"))
            ET.fromstring((folder / f"moda-{lang}.xml").read_text(encoding="utf-8"))
    before = snapshot(tmp_path)
    for p in before:
        if re.search(r"(board|moda)-\w+\.(excalidraw|xml)$", p):
            (tmp_path / p).unlink()
    assert pipeline.rerender(cfg(langs=["vi", "en", "ja"]), tmp_path)["rerendered"] == ["2026-10-14"]
    assert snapshot(tmp_path) == before
