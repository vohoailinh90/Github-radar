import json
from pathlib import Path

import yaml

from radar import cli, config, contract, pipeline
from radar.github import GitHub
from radar.labels import L
from radar.llm import Gateway
from tests.support import TODAY


def cfg(**kw):
    c = config.load(path=config.ROOT / "none.yaml", env={})
    c.update(kw)
    return c


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for base in ("digests", "export") for p in sorted((root / base).rglob("*")) if p.is_file()}


def first_run(root, **kw):
    report = pipeline.run(cfg(picks_per_run=3, **kw), GitHub(), Gateway(sleep=lambda s: None), root, TODAY)
    assert report["ok"], report
    return report


def wipe_drawn_files(root: Path):
    """Delete everything a render produces; only the stored drafts remain."""
    for p in sorted((root / "digests").rglob("*"), reverse=True):
        if p.is_file() and not p.name.startswith("draft-"):
            p.unlink()
    for p in sorted((root / "export").rglob("*"), reverse=True):
        p.unlink() if p.is_file() else p.rmdir()


def test_every_digest_keeps_the_draft_the_model_wrote(tmp_path, servers):
    first_run(tmp_path, langs=["vi", "en"])
    stored = json.loads(next((tmp_path / "digests").glob("2026-10-14/*/draft-en.json")).read_text(encoding="utf-8"))
    assert stored["lang"] == "en" and stored["draft"]["how_it_works"]["flow"] and "readme" not in stored["facts"]
    assert set(stored["facts"]) == {"full_name", "url", "stars", "forks", "license", "language", "bucket", "scanned"}


def test_rerender_draws_exactly_the_same_files_from_the_stored_drafts(tmp_path, servers):
    first_run(tmp_path, langs=["vi", "en", "ja"])
    before = snapshot(tmp_path)
    wipe_drawn_files(tmp_path)
    report = pipeline.rerender(cfg(langs=["vi", "en", "ja"]), tmp_path)
    assert report == {"rerendered": ["2026-10-14"], "skipped": {}}
    after = snapshot(tmp_path)
    assert after.keys() == before.keys() and [k for k in before if before[k] != after[k]] == []     # byte for byte, numbering included
    assert contract.validate(pipeline.read_bundle(tmp_path)) == []


def test_rerender_needs_no_network_and_no_keys(tmp_path, servers, monkeypatch):
    gh, llm = servers
    first_run(tmp_path)
    wipe_drawn_files(tmp_path)
    seen = (len(gh.calls), len(llm.calls))
    for name in ("GITHUB_TOKEN", "GOOGLE_GENERATIVE_AI_API_KEY", "MISTRAL_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GITHUB_API_URL", "http://127.0.0.1:9")
    assert pipeline.rerender(cfg(), tmp_path)["rerendered"] == ["2026-10-14"]
    assert (len(gh.calls), len(llm.calls)) == seen


def test_rerender_uses_the_current_renderer_not_the_one_that_wrote_the_files(tmp_path, servers, monkeypatch):
    first_run(tmp_path)
    monkeypatch.setitem(L["vi"], "save", "Lưu NGAY hôm nay")                  # a renderer change made after the run
    pipeline.rerender(cfg(), tmp_path)
    post = next((tmp_path / "export" / "studio" / "campaigns").glob("*/posts/vi/*.yaml"))
    assert any(s.get("title") == "Lưu NGAY hôm nay" for s in yaml.safe_load(post.read_text(encoding="utf-8"))["slides"])


def test_a_run_written_before_drafts_were_kept_is_skipped_and_left_alone(tmp_path, servers):
    first_run(tmp_path)
    old = tmp_path / "digests" / "2026-10-01" / "old-repo"
    old.mkdir(parents=True)
    (old / "vi.md").write_text("# old\n", encoding="utf-8")
    report = pipeline.rerender(cfg(), tmp_path)
    assert report["rerendered"] == ["2026-10-14"] and "no stored drafts" in report["skipped"]["2026-10-01"]
    assert (old / "vi.md").read_text(encoding="utf-8") == "# old\n"


def test_a_bundle_the_studio_would_refuse_changes_nothing(tmp_path, servers, monkeypatch):
    first_run(tmp_path)
    before = snapshot(tmp_path)
    monkeypatch.setattr(pipeline.contract, "validate", lambda files, c=None: ["bad bundle"])
    report = pipeline.rerender(cfg(), tmp_path)
    assert report["rerendered"] == [] and "studio contract" in report["skipped"]["2026-10-14"]
    assert snapshot(tmp_path) == before


def test_the_command_reports_an_unknown_run_as_a_failure_and_a_known_one_as_success(tmp_path, servers, monkeypatch, capsys):
    first_run(tmp_path)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    assert cli.main(["rerender", "--slug", "2026-10-14"]) == 0
    assert cli.main(["rerender", "--slug", "1999-01-01"]) == 1
    assert '"rerendered"' in capsys.readouterr().out


def test_rerendering_twice_keeps_the_numbering_stable(tmp_path, servers):
    first_run(tmp_path)
    once = None
    for _ in range(2):
        pipeline.rerender(cfg(), tmp_path)
        files = snapshot(tmp_path)
        assert once is None or files == once                              # the second pass changes nothing, including draft positions
        once = files
    positions = {json.loads(p.read_text(encoding="utf-8"))["facts"]["full_name"]: json.loads(p.read_text(encoding="utf-8"))["position"]
                 for p in (tmp_path / "digests").glob("2026-10-14/*/draft-vi.json")}
    assert sorted(positions.values()) == [1, 2, 3]


# --- review findings: path safety, all-or-nothing drawing, extra languages, provenance --------------------------------------
import pytest


def plant_hostile_folder(outside: Path):
    """A folder outside the repository that looks like a run: this is what `--slug ../../x` used to reach and write into."""
    repo = outside / "repoA"
    repo.mkdir(parents=True)
    (repo / "draft-vi.json").write_text(json.dumps({"lang": "vi", "position": 1, "facts": {
        "full_name": "o/repoA", "url": "https://github.com/o/repoA", "stars": 5, "forks": 1, "license": "MIT", "language": "Python",
        "bucket": "ai", "scanned": "2026-10-14"}, "draft": __import__("tests.support", fromlist=["make_draft"]).make_draft({}, "vi")}))
    return outside


@pytest.mark.parametrize("bad", ["../x", "../../etc", "/tmp/evil", "2026-10-14/../..", "2026-10-14\n", "x", "", "2026-10-14-"])
def test_a_slug_that_is_not_a_run_name_is_refused_and_nothing_is_written(tmp_path, servers, bad):
    first_run(tmp_path)
    outside = plant_hostile_folder(tmp_path.parent / f"{tmp_path.name}-outside")
    before, outside_before = snapshot(tmp_path), sorted(p.name for p in outside.rglob("*"))
    with pytest.raises(ValueError, match="run slug"):
        pipeline.rerender(cfg(), tmp_path, bad)
    with pytest.raises(ValueError):
        pipeline.rerender(cfg(), tmp_path, str(outside))                    # an absolute path replaces the base in pathlib
    assert snapshot(tmp_path) == before and sorted(p.name for p in outside.rglob("*")) == outside_before


def test_the_command_refuses_a_traversal_slug_with_a_clear_message(tmp_path, servers, monkeypatch, capsys):
    first_run(tmp_path)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    outside = plant_hostile_folder(tmp_path.parent / f"{tmp_path.name}-cli-outside")
    assert cli.main(["rerender", "--slug", "../" + outside.name]) == 2
    assert "run slug" in capsys.readouterr().err and not (outside / "repoA" / "vi.md").exists()


def test_the_listing_without_a_slug_only_visits_run_folders(tmp_path, servers):
    first_run(tmp_path)
    stray = plant_hostile_folder(tmp_path / "digests" / "evil-folder") / "repoA"
    report = pipeline.rerender(cfg(), tmp_path)
    assert report["rerendered"] == ["2026-10-14"] and "evil-folder" not in report["skipped"]
    assert not (stray / "vi.md").exists()


def test_a_failure_while_drawing_leaves_the_repository_exactly_as_it_was(tmp_path, servers, monkeypatch):
    from radar import digest
    first_run(tmp_path)
    before = snapshot(tmp_path)
    monkeypatch.setitem(L["vi"], "problem", "TIÊU ĐỀ MỚI")                  # so a repository drawn before the failure WOULD differ on disk
    real, calls = digest.render_repo, []

    def flaky(*a, **kw):
        calls.append(1)
        if len(calls) == 2:
            raise KeyError("boom while drawing the second repository")
        return real(*a, **kw)
    monkeypatch.setattr(digest, "render_repo", flaky)
    report = pipeline.rerender(cfg(), tmp_path)
    assert report["rerendered"] == [] and "nothing was changed" in report["skipped"]["2026-10-14"] and "boom" in report["skipped"]["2026-10-14"]
    assert snapshot(tmp_path) == before                                    # no half-rewritten digests next to a stale export
    assert not any(b"TI\xc3\x8aU \xc4\x90\xe1\xbb\x80 M\xe1\xbb\x9a" in data for data in snapshot(tmp_path).values())


def test_a_stored_draft_that_no_longer_fits_the_schema_is_skipped_not_drawn(tmp_path, servers):
    first_run(tmp_path)
    path = next((tmp_path / "digests").glob("2026-10-14/*/draft-vi.json"))
    stored = json.loads(path.read_text(encoding="utf-8"))
    del stored["draft"]["how_it_works"]["steps"]
    path.write_text(json.dumps(stored), encoding="utf-8")
    before = snapshot(tmp_path)
    report = pipeline.rerender(cfg(), tmp_path)
    assert "no longer fits the schema" in report["skipped"]["2026-10-14"] and snapshot(tmp_path) == before


def test_a_language_stored_in_the_drafts_but_missing_from_the_config_is_still_redrawn_and_listed(tmp_path, servers):
    first_run(tmp_path, langs=["vi", "en"])
    wipe_drawn_files(tmp_path)
    pipeline.rerender(cfg(langs=["vi"]), tmp_path)                           # the owner later narrowed langs to vi only
    campaign = yaml.safe_load((tmp_path / "export/studio/campaigns/radar-2026-10-14/campaign.yaml").read_text(encoding="utf-8"))
    assert campaign["langs"] == ["vi", "en"] and list((tmp_path / "export/studio/campaigns/radar-2026-10-14/posts/en").glob("*.yaml"))
    assert list((tmp_path / "digests/2026-10-14").glob("*/en.md"))


def test_a_note_on_a_draft_survives_every_rerender_so_a_reconstructed_draft_stays_labelled(tmp_path, servers):
    first_run(tmp_path)
    path = next((tmp_path / "digests").glob("2026-10-14/*/draft-vi.json"))
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["note"] = "RECONSTRUCTED: not the model's original answer"
    path.write_text(json.dumps(stored, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for _ in range(2):
        pipeline.rerender(cfg(), tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["note"] == "RECONSTRUCTED: not the model's original answer"
    other = next(p for p in (tmp_path / "digests").glob("2026-10-14/*/draft-vi.json") if p != path)
    assert "note" not in json.loads(other.read_text(encoding="utf-8"))      # only drafts that carry one
