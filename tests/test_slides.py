"""The slide deck (`radar/slides.py`): drawn from the stored draft only, so every word is the draft's, a label's or a fact, every
address is a fact, nothing runs off a slide, and drawing it again gives the same bytes."""

import io
import json
import re
import shutil
import zipfile
from pathlib import Path

import pytest
from pptx import Presentation

from radar import cli, config, slides
from radar.labels import L
from tests.support import make_draft
from tests.test_write import FACTS as BASE_FACTS

ROOT = config.ROOT
LINKS = [["Helpdesk docs", "https://helpdesk.example.org/docs"], ["bad", "javascript:alert(1)"], ["console", "http://localhost:8080"]]
BLOCKS = [["toml", '[helpdesk]\nurl = "https://helpdesk.example.org"']]
FACTS = {**BASE_FACTS, "bucket": "ai", "url": "https://github.com/example-org/sample-agent-kit", "links": LINKS, "blocks": BLOCKS}
EAST = re.compile(r"[぀-ヿ㐀-鿿]")


def stored_drafts() -> list[Path]:
    return sorted((ROOT / "digests").glob("*/*/draft-*.json"))


def texts(blob: bytes) -> list[str]:
    out = []
    for slide in Presentation(io.BytesIO(blob)).slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                out += [p.text for p in shape.text_frame.paragraphs if p.text]
    return out


def strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings(v)]
    if isinstance(value, (list, tuple)):
        return [s for v in value for s in strings(v)]
    return [str(value)] if isinstance(value, (int, float)) and not isinstance(value, bool) else []


def words(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"\w+", text)}


def allowed_words(facts: dict, draft: dict, lang: str) -> set[str]:
    return words(" ".join(strings(draft) + strings(L[lang]) + strings(facts)))


def check_words(blob: bytes, facts: dict, draft: dict, lang: str) -> None:
    allowed = allowed_words(facts, draft, lang)
    for text in texts(blob):
        stray = [w for w in words(text) if w not in allowed and not w.isdigit() and not EAST.search(w)]
        assert not stray, f"{stray} on a slide ({text!r}) are neither the draft's, a label nor a fact"


def addresses(blob: bytes) -> set[str]:
    found = set()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for name in z.namelist():
            if name.startswith("ppt/slides/_rels/"):
                found |= set(re.findall(r'Target="([^"]+)"[^>]*TargetMode="External"', z.read(name).decode("utf-8")))
    return found


def check_inside_the_slide(blob: bytes) -> None:
    prs = Presentation(io.BytesIO(blob))
    w, h = prs.slide_width, prs.slide_height
    for n, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            assert shape.left >= 0 and shape.top >= 0 and shape.left + shape.width <= w + 12700 and shape.top + shape.height <= h + 12700, \
                f"slide {n}: {shape.name} leaves the slide"


def check_pages_fit(book: slides.Book) -> None:
    for n, page in enumerate(book.pages, 1):
        placed = page.get("placed", [])
        if placed:
            b, y, h = placed[-1]
            assert y + h <= slides.BOTTOM + 0.5 or len(placed) == 1, f"slide {n} runs past the content area"


# ---------------------------------------------------------------- the stored digests of this repository

@pytest.mark.parametrize("path", stored_drafts(), ids=lambda p: "/".join(p.parts[-3:]))
def test_every_stored_draft_draws_a_deck_that_fits_and_says_only_what_the_draft_says(path):
    stored = json.loads(path.read_text(encoding="utf-8"))
    facts, draft, lang = stored["facts"], stored["draft"], stored["lang"]
    book = slides.guide_book(facts, draft, lang) if draft.get("guide") else slides.concept_book(facts, draft, lang)
    check_pages_fit(book)
    blob = book.build()
    check_inside_the_slide(blob)
    check_words(blob, facts, draft, lang)
    links = {facts["url"]} | {u for _, u in facts.get("links") or []}
    assert addresses(blob) <= links
    assert len(Presentation(io.BytesIO(blob)).slides) == len(book.pages) >= 5


def test_a_deck_is_the_same_bytes_every_time():
    draft = make_draft(FACTS, "vi")
    assert slides.deck(FACTS, draft, "vi") == slides.deck(FACTS, draft, "vi")
    with zipfile.ZipFile(io.BytesIO(slides.deck(FACTS, draft, "vi"))) as z:
        assert {i.date_time for i in z.infolist()} == {(2020, 1, 1, 0, 0, 0)}


# ---------------------------------------------------------------- what is on the slides

@pytest.mark.parametrize("lang", ["vi", "en", "ja"])
@pytest.mark.parametrize("legacy", [False, True])
def test_a_deck_is_drawn_in_every_language_for_a_guide_and_for_an_older_draft(lang, legacy):
    draft = make_draft(FACTS, lang, legacy=legacy)
    blob = slides.deck(FACTS, draft, lang)
    check_inside_the_slide(blob)
    check_words(blob, FACTS, draft, lang)
    assert draft["title"] in " ".join(texts(blob))


def test_only_the_repository_and_the_readme_addresses_become_links():
    draft = make_draft(FACTS, "en")
    draft["guide"]["steps"][0]["link_ref"] = 1                     # javascript:, not a plain address: left out whatever the draft says
    draft["guide"]["steps"][1]["link_ref"] = 0
    draft["guide"]["steps"][3]["link_ref"] = 2                     # a local address is shown as code, never linked
    blob = slides.deck(FACTS, draft, "en")
    assert addresses(blob) == {FACTS["url"], "https://helpdesk.example.org/docs"}
    assert "javascript" not in " ".join(texts(blob)) and "http://localhost:8080" in " ".join(texts(blob))


def test_a_command_is_printed_as_the_draft_has_it_and_a_sample_as_the_readme_has_it():
    draft = make_draft(FACTS, "en")
    shown = texts(slides.deck(FACTS, draft, "en"))
    assert "pip install sample-agent-kit" in shown and "sample-agent run --queue support" in shown
    assert '[helpdesk]' in shown and 'url = "https://helpdesk.example.org"' in shown


def test_hostile_text_cannot_break_the_file_or_add_an_element():
    draft = make_draft(FACTS, "en", title="<script>alert(1)</script> \x00bad\x1b & \"quotes\"", hook="x" * 400)
    draft["learn"] = ["<a href='http://evil.example'>click</a> " + "w" * 300]
    blob = slides.deck(FACTS, draft, "en")
    assert Presentation(io.BytesIO(blob)).slides
    assert any("<script>" in t for t in texts(blob))                      # shown as text, so a reader sees what the README said
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        xml = "".join(z.read(n).decode("utf-8") for n in z.namelist() if n.startswith("ppt/slides/slide"))
    assert "<script>" not in xml and "evil.example" not in addresses(blob) and "\x00" not in xml


def test_a_long_paragraph_and_a_long_sample_continue_on_the_next_slide_instead_of_running_off():
    sentence = "Mỗi câu của đoạn này khá dài để chứng minh rằng đoạn văn được chia theo câu chứ không bị cắt giữa chừng. "
    draft = make_draft(FACTS, "vi", problem=sentence * 40)
    draft["guide"]["steps"][0]["commands"] = [f"echo line {i} " + "x" * 30 for i in range(90)]
    book = slides.guide_book(FACTS, draft, "vi")
    check_pages_fit(book)
    problem = [p for p in book.pages if p["title"].startswith(L["vi"]["problem"])]
    assert len(problem) >= 2 and "(1/" in problem[0]["title"]
    first_step = [p for p in book.pages if p["kicker"].startswith(L["vi"]["step"] + " 1")]
    assert len(first_step) >= 2
    check_inside_the_slide(book.build())


def test_a_block_that_cannot_fit_is_split_not_dropped():
    lines = [f"line {i}" for i in range(200)]
    page = slides.paginate([slides.code(lines)], 100)
    shown = [x for p in page for b, _, _ in p for x in b["lines"]]
    assert shown == lines and all(y + h <= slides.BOTTOM + 0.5 for p in page for _, y, h in p)


def test_a_link_never_starts_a_slide_alone_when_the_block_before_it_can_come_along():
    filler = [slides.card(None, "x " * 40, marker=i) for i in range(1, 4)]
    glued = slides.para([("Liên kết", "t", None)], glue=True)
    for count in range(1, 4):
        pages = slides.paginate(filler[:count] * 2 + [glued], 120)
        assert len(pages[-1]) > 1 or len(pages) == 1


def test_roadmap_numbers_every_step_in_order():
    draft = make_draft(FACTS, "en")
    steps = [s["title"] for s in draft["guide"]["steps"]]
    book = slides.guide_book(FACTS, draft, "en")
    road = next(p for p in book.pages if p["title"].startswith(L["en"]["roadmap"]))
    items = [t for b, _, _ in road["placed"] for _, t in b["items"]]
    assert items == steps[:len(items)]


# ---------------------------------------------------------------- the diagram

@pytest.mark.parametrize("edges", [[[0, 1], [1, 2], [2, 0]], [], [[0, 2], [1, 3], [2, 4], [3, 4]], [[4, 0], [3, 0]], [[0, 1], [0, 2], [0, 3], [0, 4]]])
def test_the_diagram_never_overlaps_a_box_and_stays_on_the_slide(edges):
    comps = [{"name": f"Component number {i}", "role": "does a thing"} for i in range(5)]
    geo = slides.flow_geometry(comps, edges, 120, slides.BOTTOM)
    boxes = [(x, y, x + geo["bw"], y + geo["heights"][i]) for i, (x, y) in geo["pos"].items()]
    for i, a in enumerate(boxes):
        assert a[0] >= 0 and a[2] <= slides.SW and a[1] >= 0 and a[3] <= slides.SH
        for b in boxes[i + 1:]:
            assert a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1], "two boxes overlap"
    assert len(geo["routes"]) == len(edges)
    for r in geo["routes"]:
        assert all(0 <= x <= slides.SW and 0 <= y <= slides.SH for x, y in r["pts"])


# ---------------------------------------------------------------- the command

def one_digest(tmp_path: Path) -> Path:
    src = ROOT / "digests" / "2026-10-17-2" / "agent-orchestrator"
    dst = tmp_path / "digests" / "2026-10-17-2" / "agent-orchestrator"
    dst.mkdir(parents=True)
    shutil.copy(src / "draft-vi.json", dst)
    (dst / "vi.md").write_text("# kept\n", encoding="utf-8")
    return dst


def tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_the_command_writes_the_deck_beside_the_draft_and_touches_nothing_else(tmp_path, monkeypatch, capsys):
    folder = one_digest(tmp_path)
    before = tree(tmp_path)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    assert cli.main(["slides", "2026-10-17-2/agent-orchestrator"]) == 0
    after = tree(tmp_path)
    assert set(after) - set(before) == {"digests/2026-10-17-2/agent-orchestrator/slides-vi.pptx"}
    assert {k: v for k, v in after.items() if k in before} == before
    assert (folder / "slides-vi.pptx").read_bytes()[:2] == b"PK" and '"written"' in capsys.readouterr().out


def test_running_it_twice_changes_nothing(tmp_path):
    one_digest(tmp_path)
    slides.write(tmp_path, ["2026-10-17-2"])
    first = tree(tmp_path)
    slides.write(tmp_path, ["2026-10-17-2"])
    assert tree(tmp_path) == first


def test_it_needs_to_be_told_what_to_draw_and_refuses_what_it_cannot_find(tmp_path):
    one_digest(tmp_path)
    with pytest.raises(ValueError, match="name what to draw"):
        slides.write(tmp_path, [])
    for bad in ("nope", "2026-10-17-2/../../etc", "2026-10-17-2/x/y", "2026-01-01", "2026-10-17-2/missing"):
        with pytest.raises(ValueError):
            slides.write(tmp_path, [bad])
    assert slides.write(tmp_path, everything=True)["written"] == ["digests/2026-10-17-2/agent-orchestrator/slides-vi.pptx"]
    assert slides.write(tmp_path, ["2026-10-17-2"], langs=["en"]) == {"written": [], "skipped": {}}


def test_a_draft_that_no_longer_fits_the_schema_is_skipped_and_its_old_deck_stays(tmp_path):
    folder = one_digest(tmp_path)
    slides.write(tmp_path, ["2026-10-17-2"])
    old = (folder / "slides-vi.pptx").read_bytes()
    stored = json.loads((folder / "draft-vi.json").read_text(encoding="utf-8"))
    del stored["draft"]["how_it_works"]
    (folder / "draft-vi.json").write_text(json.dumps(stored), encoding="utf-8")
    report = slides.write(tmp_path, ["2026-10-17-2"])
    assert report["written"] == [] and "schema" in next(iter(report["skipped"].values()))
    assert (folder / "slides-vi.pptx").read_bytes() == old
    assert not list(folder.glob("*.tmp"))
    (folder / "draft-vi.json").write_text("{not json", encoding="utf-8")
    assert "not JSON" in next(iter(slides.write(tmp_path, ["2026-10-17-2"])["skipped"].values()))
