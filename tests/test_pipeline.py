import json

import yaml

from radar import config, contract, pipeline
from radar.github import GitHub
from radar.llm import Gateway
from tests.support import TODAY, make_draft


def cfg(**kw):
    c = config.load(path=config.ROOT / "none.yaml", env={})
    c.update(kw)
    return c


def go(tmp_path, servers, **kw):
    gh, llm = servers
    return pipeline.run(cfg(picks_per_run=kw.pop("picks", 3), **kw), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY,
                        **{k: v for k, v in kw.items() if k in ()})


def test_dry_run_ranks_but_calls_no_model_and_writes_nothing(tmp_path, servers):
    gh, llm = servers
    report = pipeline.run(cfg(), GitHub(), Gateway(), tmp_path, TODAY, dry_run=True)
    assert report["ok"] and len(report["picks"]) == 3 and llm.calls == []
    assert list(tmp_path.iterdir()) == []


def test_full_run_writes_digests_bundle_state_and_report(tmp_path, servers):
    gh, llm = servers
    report = go(tmp_path, servers)
    assert report["ok"], report
    assert len(report["written"]) == 3 and report["held"] == [] and report["export_errors"] == []
    day = tmp_path / "digests" / "2026-10-14"
    repos = sorted(p.name for p in day.iterdir() if p.is_dir())
    assert len(repos) == 3
    md = (day / repos[0] / "vi.md").read_text(encoding="utf-8")
    assert "![" in md and "card-vi.svg" in md and "flow-vi.svg" in md and "```bash" in md
    for svgfile in day.rglob("*.svg"):
        assert svgfile.read_text(encoding="utf-8").startswith("<svg")
    assert (day / "README.md").exists() and (tmp_path / "digests" / "INDEX.md").exists()
    files = pipeline.read_bundle(tmp_path)
    assert contract.validate(files) == []
    camp = yaml.safe_load(files["campaigns/radar-2026-10-14/campaign.yaml"])
    assert len(camp["links"]) == 3 and camp["langs"] == ["vi"]
    seen = json.loads((tmp_path / "state" / "seen.json").read_text())
    assert len(seen) == 3
    assert json.loads((tmp_path / "state" / "runs" / "2026-10-14.json").read_text())["ok"] is True
    # every request carried the right key for its provider and never leaked into the output files
    assert {c["headers"]["Authorization"] for c in llm.calls} == {"Bearer g-key", "Bearer m-key"}
    assert all("g-key" not in p.read_text(encoding="utf-8", errors="ignore") for p in tmp_path.rglob("*") if p.is_file())


def test_second_run_covers_different_repos_because_covered_ones_are_remembered(tmp_path, servers):
    first = go(tmp_path, servers)
    second = go(tmp_path, servers)
    a = {p["repo"] for p in first["picks"]}
    b = {p["repo"] for p in second["picks"]}
    assert a and not (a & b)


def test_all_models_failing_aborts_early_and_remembers_nothing(tmp_path, servers, monkeypatch):
    gh, llm = servers
    llm.script = lambda kind, facts, lang, n: (503, {"error": "down"})
    report = pipeline.run(cfg(), GitHub(), Gateway(sleep=lambda s: None, attempts_per_model=1), tmp_path, TODAY)
    assert not report["ok"] and report["aborted"] and report["written"] == []
    assert not (tmp_path / "state" / "seen.json").exists() and not (tmp_path / "export").exists()
    assert llm.counts["writer"] <= 2          # it stopped instead of burning the quota on every repo


def test_a_held_primary_language_is_not_exported_and_is_retried_next_run(tmp_path, servers):
    gh, llm = servers
    llm.script = lambda kind, facts, lang, n: make_draft(facts, lang, problem="Xem https://example.com") if kind == "writer" else None
    report = pipeline.run(cfg(picks_per_run=1), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    assert not report["ok"] and report["held"] and report["written"] == []
    assert not (tmp_path / "state" / "seen.json").exists()


def test_extra_languages_are_written_separately_and_missing_ones_are_reported(tmp_path, servers):
    gh, llm = servers
    report = pipeline.run(cfg(picks_per_run=1, langs=["vi", "en", "ja"]), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    assert report["ok"] and {w["lang"] for w in report["written"]} == {"vi", "en", "ja"}
    files = pipeline.read_bundle(tmp_path)
    assert sum("/posts/" in p for p in files) == 3 and contract.validate(files) == []
    assert llm.counts["writer"] == 3, "each language is written from the facts, not translated"


def test_a_bundle_the_studio_would_reject_is_not_written(tmp_path, servers, monkeypatch):
    monkeypatch.setattr(contract, "validate", lambda files, c=None: ["bad bundle"])
    monkeypatch.setattr(pipeline.contract, "validate", lambda files, c=None: ["bad bundle"])
    report = pipeline.run(cfg(picks_per_run=1), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    assert not report["ok"] and report["export_errors"] == ["bad bundle"]
    assert not (tmp_path / "export").exists() and (tmp_path / "digests").exists()
