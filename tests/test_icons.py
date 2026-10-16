"""The closed set of pictograms: vendored byte for byte, drawn only from an allowlist of shapes, and never from model text."""

import base64
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from radar import icons, write
from radar.config import ROOT

SVG = "{http://www.w3.org/2000/svg}"


def test_the_vendored_files_match_their_hashes_and_the_index():
    assert icons.verify() == []


def test_the_set_is_what_the_writer_prompt_offers():
    listed = dict(line.split(" = ", 1) for line in icons.prompt_list().splitlines())
    assert tuple(sorted(listed)) == icons.NAMES and all(listed.values())
    assert "box" in icons.NAMES and "(`box` if none fits)" in write.SYSTEM            # the prompt names it as the fallback


def test_every_name_is_plain_and_every_meaning_is_short():
    assert 40 <= len(icons.NAMES) <= 80
    assert all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", n) for n in icons.NAMES)
    assert all(0 < len(icons.gloss(n)) <= 60 for n in icons.NAMES)


def test_the_licence_travels_with_the_files():
    licence = (ROOT / "docs" / "third-party" / "lucide" / "LICENSE").read_text(encoding="utf-8")
    assert "ISC License" in licence and "Lucide" in licence
    assert icons.index()["license"] == "ISC" and icons.index()["version"]
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "radar/icons/** -text" in attributes            # a checkout that converts line endings must not change the hashed bytes


@pytest.mark.parametrize("name", icons.NAMES)
def test_every_icon_draws_as_a_self_contained_svg_with_nothing_but_shapes(name):
    root = ET.fromstring(icons.svg(name, size=56))
    tags = {el.tag.removeprefix(SVG) for el in root.iter()}
    assert tags <= {"svg", "circle", "g", *icons.SHAPES}, tags
    text = icons.svg(name)
    assert "http" not in text.replace("http://www.w3.org/2000/svg", "") and "script" not in text and "href" not in text
    assert "currentColor" not in text                      # the ink is the renderer's colour, not the page's
    uri = icons.data_uri(name)
    assert uri.startswith("data:image/svg+xml,") and ";" not in uri
    assert base64.b64decode(uri.split(",", 1)[1]).decode("ascii") == text


def test_colours_and_size_come_from_the_renderer_and_are_checked():
    assert 'fill="#112233"' in icons.svg("terminal", tile="#112233")
    for bad in ('red"/><script>', "#12345", "#GGGGGG", "url(#x)"):
        with pytest.raises(ValueError):
            icons.svg("terminal", tile=bad)
        with pytest.raises(ValueError):
            icons.svg("terminal", ink=bad)
    for size in (0, -5, 5000, "56", 56.5):
        with pytest.raises(ValueError):
            icons.svg("terminal", size=size)
    with pytest.raises(ValueError):
        icons.svg("../../etc/passwd")


def test_the_same_icon_always_gives_the_same_bytes():
    assert icons.svg("route") == icons.svg("route") and icons.data_uri("route", size=40) == icons.data_uri("route", size=40)


@pytest.fixture
def folder(tmp_path, monkeypatch):
    """A copy of the set in a temporary folder that the module is pointed at, so a test can damage it."""
    for p in icons.HERE.iterdir():
        if p.is_file():
            (tmp_path / p.name).write_bytes(p.read_bytes())
    monkeypatch.setattr(icons, "HERE", tmp_path)
    icons.index.cache_clear()
    icons.shapes.cache_clear()
    yield tmp_path
    icons.index.cache_clear()
    icons.shapes.cache_clear()


def damage(folder: Path, name: str, svg: str) -> None:
    (folder / f"{name}.svg").write_text(svg, encoding="utf-8")


EVIL = ['<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://evil.example/x.png"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0" onload="x()"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0&#10;<script>"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0" fill="url(#x)"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0" fill="red"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><g><path d="M0 0"/></g></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"></svg>']


@pytest.mark.parametrize("svg", EVIL)
def test_a_swapped_in_file_with_anything_but_plain_shapes_is_refused_and_reported(folder, svg):
    damage(folder, "terminal", svg)
    problems = icons.verify()
    assert any(p.startswith("terminal") for p in problems), problems       # the hash no longer matches, and the shapes are refused
    with pytest.raises(ValueError):
        icons.svg("terminal")


def test_a_missing_extra_or_edited_file_is_reported(folder):
    (folder / "rocket.svg").unlink()
    (folder / "extra.svg").write_text("<svg/>", encoding="utf-8")
    damage(folder, "bug", (folder / "bug.svg").read_text(encoding="utf-8") + "\n")
    problems = icons.verify()
    assert any("rocket.svg is listed" in p for p in problems)
    assert any("extra.svg is in the folder" in p for p in problems)
    assert any("bug.svg differs" in p for p in problems)


def test_the_hashes_in_the_index_are_the_files_sha256():
    for name, entry in icons.index()["icons"].items():
        assert hashlib.sha256((icons.HERE / f"{name}.svg").read_bytes()).hexdigest() == entry["sha256"]
    assert json.loads((icons.HERE / "index.json").read_text(encoding="utf-8"))["icons"].keys() == icons.index()["icons"].keys()
