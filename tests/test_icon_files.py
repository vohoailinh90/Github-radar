"""An `icons-<lang>.json` beside a draft that was stored before icons existed.

The stored draft is the model's answer and must not change; the icons come from a file that a person or a Claude session chose from
the closed set. These tests pin that: the file is checked like a draft is, a stale one stops the run instead of drawing something
wrong, only the draw.io diagram changes, and nothing in `digests/` that was already there is rewritten.
"""

import base64
import copy
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from radar import digest, drawio, gates, icons, pipeline
from radar.labels import L
from tests.support import make_draft
from tests.test_drawio import FACTS, images, parse, style
from tests.test_rerender import cfg, first_run, snapshot, wipe_drawn_files

PICKS = ["terminal", "route", "database"]


def file_for(draft, picks=PICKS):
    return {"note": "chosen for a draft that predates icons", "components": [
        {"name": c["name"], "icon": i} for c, i in zip(draft["how_it_works"]["components"], picks)]}


def old_draft():
    d = make_draft({}, "en")
    for c in d["how_it_works"]["components"]:
        c.pop("icon")
    return d


# --- the gate --------------------------------------------------------------------------------------------------------------------
def test_a_file_that_names_every_component_with_an_icon_of_the_set_passes():
    d = old_draft()
    assert gates.icon_file(d, file_for(d)) == []


@pytest.mark.parametrize("damage,needle", [
    (lambda f: f["components"].pop(), "rows for"),
    (lambda f: f["components"].append({"name": "extra", "icon": "box"}), "rows for"),
    (lambda f: f["components"][1].update(name="Another name"), "components[1]"),
    (lambda f: f["components"][0].update(icon="rocket-ship"), "components[0]"),
    (lambda f: f["components"][0].update(icon=None), "components[0]"),
    (lambda f: f["components"][0].update(icon=["terminal"]), "components[0]"),
    (lambda f: f["components"].reverse(), "components[0]"),
    (lambda f: f.pop("components"), "components"),
    (lambda f: f.update(components="terminal"), "components"),
])
def test_a_file_that_no_longer_fits_its_draft_is_refused(damage, needle):
    d = old_draft()
    f = file_for(d)
    damage(f)
    problems = [str(p) for p in gates.icon_file(d, f)]
    assert problems and all("[error]" in p for p in problems) and any(needle in p for p in problems), problems


@pytest.mark.parametrize("data", [None, [], "terminal", 3, {"components": None}])
def test_a_file_that_is_not_an_object_with_rows_is_refused(data):
    assert gates.icon_file(old_draft(), data)


# --- the overlay ------------------------------------------------------------------------------------------------------------------
def test_the_overlay_returns_a_copy_with_the_icons_and_leaves_the_stored_draft_alone():
    d = old_draft()
    before = copy.deepcopy(d)
    shown = icons.overlay(d, file_for(d))
    assert [c["icon"] for c in shown["how_it_works"]["components"]] == PICKS
    assert d == before and shown is not d


def test_a_draft_that_names_icons_itself_wins_over_the_file():
    d = make_draft({}, "en")
    assert icons.has_icons(d) and not icons.has_icons(old_draft())
    assert icons.overlay(d, file_for(d, ["bug", "zap", "mail"])) is d


@pytest.mark.parametrize("data", [None, {}, {"components": []}, {"components": [{"name": "x", "icon": "box"}]}])
def test_a_file_that_does_not_fit_is_never_applied(data):
    d = old_draft()
    assert icons.overlay(d, data) is d


def test_a_row_with_the_wrong_name_or_an_unknown_icon_is_skipped_by_the_overlay_itself():
    d = old_draft()
    f = file_for(d)
    f["components"][0]["icon"] = "<script>"
    f["components"][1]["name"] = "Not this one"
    shown = icons.overlay(d, f)
    assert [c.get("icon") for c in shown["how_it_works"]["components"]] == [None, None, "database"]


def test_the_renderer_draws_the_file_icons_and_the_stored_draft_it_is_given_is_what_is_written(tmp_path):
    d = old_draft()
    digest.render_repo(tmp_path, "2026-10-14", {**FACTS, "scanned": "2026-10-14"}, {"en": d}, icon_files={"en": file_for(d)})
    out = next((tmp_path / "digests" / "2026-10-14").iterdir())
    _, cells = parse((out / "drawio-en.drawio").read_text(encoding="utf-8"))
    assert [base64.b64decode(style(p)["image"].split(",", 1)[1]).decode() for p in images(cells)] == \
        [icons.svg(n, size=56, tile=drawio.NAVY) for n in PICKS]
    stored = json.loads((out / "draft-en.json").read_text(encoding="utf-8"))["draft"]
    assert stored == d and not any("icon" in c for c in stored["how_it_works"]["components"])        # the answer is untouched


# --- rerender --------------------------------------------------------------------------------------------------------------------
def strip_icons(root: Path) -> None:
    """Make the stored drafts what the ones from before this feature are: no `icon` on any component."""
    for path in (root / "digests").glob("*/*/draft-*.json"):
        stored = json.loads(path.read_text(encoding="utf-8"))
        for c in stored["draft"]["how_it_works"]["components"]:
            c.pop("icon", None)
        path.write_text(json.dumps(stored, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_files(root: Path, picks=PICKS) -> list[Path]:
    paths = []
    for path in sorted((root / "digests").glob("*/*/draft-*.json")):
        stored = json.loads(path.read_text(encoding="utf-8"))
        target = path.with_name(icons.FILE.format(lang=stored["lang"]))
        target.write_text(json.dumps(file_for(stored["draft"], picks), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths.append(target)
    return paths


def old_run(tmp_path, langs=("vi", "en")):
    first_run(tmp_path, langs=list(langs))
    strip_icons(tmp_path)
    wipe_drawn_files(tmp_path)
    assert pipeline.rerender(cfg(langs=list(langs)), tmp_path)["rerendered"] == ["2026-10-14"]
    return snapshot(tmp_path)


def test_an_icon_file_changes_only_the_drawio_diagram_and_nothing_stored_is_rewritten(tmp_path, servers):
    bare = old_run(tmp_path)
    assert not any(p.endswith(".drawio") and b"shape=image" in v for p, v in bare.items())          # no file, no icons
    files = write_files(tmp_path)
    written = {p: p.read_bytes() for p in files}
    assert pipeline.rerender(cfg(langs=["vi", "en"]), tmp_path)["skipped"] == {}
    after = snapshot(tmp_path)
    changed = sorted(k for k in bare if bare[k] != after[k])
    assert changed and all(k.endswith(".drawio") for k in changed), changed       # draft, board, Moda, SVGs, Markdown: byte for byte
    assert {k for k in after} - set(bare) == {p.relative_to(tmp_path).as_posix() for p in files}     # the only new files are the icon files
    assert {p: p.read_bytes() for p in files} == written                            # and rerender leaves them as they were
    for k in changed:
        _, cells = parse(after[k].decode("utf-8"))
        assert len(images(cells)) == len(PICKS)


@pytest.mark.parametrize("damage", [
    lambda f: f["components"][0].update(name="A component the draft never had"),
    lambda f: f["components"][0].update(icon="rocket-ship"),
    lambda f: f["components"].pop(),
])
def test_a_stale_or_unknown_icon_file_stops_that_run_and_changes_nothing(tmp_path, servers, damage):
    old_run(tmp_path)
    files = write_files(tmp_path)
    victim = files[0]
    data = json.loads(victim.read_text(encoding="utf-8"))
    damage(data)
    victim.write_text(json.dumps(data), encoding="utf-8")
    before = snapshot(tmp_path)
    report = pipeline.rerender(cfg(langs=["vi", "en"]), tmp_path)
    assert report["rerendered"] == [] and "icon file does not fit its draft" in report["skipped"]["2026-10-14"]
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("content", ["{ not json", "", "\ufeff{}", "[" * 100000, "null"])
def test_a_file_that_is_not_usable_json_is_reported_not_a_crash(tmp_path, servers, content):
    old_run(tmp_path)
    files = write_files(tmp_path)
    files[0].write_text(content, encoding="utf-8")
    before = snapshot(tmp_path)
    report = pipeline.rerender(cfg(langs=["vi", "en"]), tmp_path)
    assert "icon file does not fit its draft" in report["skipped"]["2026-10-14"] and "not a JSON object" in report["skipped"]["2026-10-14"]
    assert snapshot(tmp_path) == before


def test_a_draft_that_names_its_own_icons_keeps_them_whatever_the_file_says(tmp_path, servers):
    first_run(tmp_path, langs=["vi"])
    drawn = snapshot(tmp_path)
    write_files(tmp_path, ["bug", "zap", "mail"])
    assert pipeline.rerender(cfg(langs=["vi"]), tmp_path)["skipped"] == {}
    after = snapshot(tmp_path)
    assert {k: v for k, v in after.items() if not k.startswith("digests/") or "icons-" not in k} == drawn


@pytest.mark.parametrize("error", [PermissionError("no access"), OSError("transient I/O error"), IsADirectoryError("is a directory")])
def test_an_icon_file_that_cannot_be_read_stops_that_run_and_nothing_else(tmp_path, servers, monkeypatch, error):
    old_run(tmp_path)
    files = write_files(tmp_path)
    before = snapshot(tmp_path)
    real = Path.read_text

    def read_text(self, *args, **kwargs):
        if self.name == files[0].name and self.parent == files[0].parent:
            raise error
        return real(self, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", read_text)
    report = pipeline.rerender(cfg(langs=["vi", "en"]), tmp_path)
    assert report["rerendered"] == [] and "icon file does not fit its draft" in report["skipped"]["2026-10-14"]
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("content", ["{ stale", "null", json.dumps({"components": [{"name": "A component the draft never had", "icon": "box"}]}),
                                     json.dumps({"components": [{"name": "x", "icon": "rocket-ship"}]})])
def test_a_stale_or_broken_icon_file_beside_a_draft_that_names_its_own_icons_stops_nothing(tmp_path, servers, content):
    first_run(tmp_path, langs=["vi"])
    drawn = snapshot(tmp_path)
    for path in write_files(tmp_path):
        path.write_text(content, encoding="utf-8")
    assert pipeline.rerender(cfg(langs=["vi"]), tmp_path) == {"rerendered": ["2026-10-14"], "skipped": {}}
    assert {k: v for k, v in snapshot(tmp_path).items() if "icons-" not in k} == {k: v for k, v in drawn.items() if "icons-" not in k}
    assert all(p.read_text(encoding="utf-8") == content for p in (tmp_path / "digests").rglob("icons-*.json"))     # left as they were


def test_the_run_that_writes_new_drafts_never_writes_an_icon_file(tmp_path, servers):
    first_run(tmp_path, langs=["vi", "en"])
    assert list((tmp_path / "digests").rglob("icons-*.json")) == []
