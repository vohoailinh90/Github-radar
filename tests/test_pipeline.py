import json

import yaml

from radar import config, contract, pipeline
from radar.github import GitHub
from radar.llm import Gateway
from tests.support import TODAY, FakeLLM, fake_github, make_draft


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
    from radar.llm import has_key
    usable = [m for m in cfg()["models"]["writer"] if has_key(m)]               # a model without a key is skipped, not called
    assert llm.counts["writer"] == len(usable) >= 3                          # each usable writer model tried once, for the FIRST repo only


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


def test_primary_language_rule_a_repo_whose_first_language_is_held_is_not_exported_even_if_another_language_passed(tmp_path, servers):
    gh, llm = servers
    llm.script = lambda kind, facts, lang, n: make_draft(facts, "vi", problem="Xem https://example.com") if kind == "writer" and lang == "vi" else None
    report = pipeline.run(cfg(picks_per_run=1, langs=["vi", "en"]), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    assert not report["ok"] and any(w["lang"] == "en" for w in report["written"]) and any(h["lang"] == "vi" for h in report["held"])
    assert not (tmp_path / "export").exists() and not (tmp_path / "state" / "seen.json").exists()


def test_a_github_error_on_one_repo_holds_that_repo_only(tmp_path, servers, monkeypatch):
    gh, llm = servers
    gh.close()
    bad = fake_github(fail=("sample-agent-kit/git/trees",))
    monkeypatch.setenv("GITHUB_API_URL", bad.url)
    try:
        report = pipeline.run(cfg(picks_per_run=3), GitHub(sleep=lambda s: None), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    finally:
        bad.close()
    assert [h["repo"] for h in report["held"]] == ["example-org/sample-agent-kit"] and "GitHub" in report["held"][0]["problems"][0]
    assert report["ok"] and len(report["written"]) == 2
    assert "example-org/sample-agent-kit" not in json.loads((tmp_path / "state" / "seen.json").read_text())


def test_a_failing_search_is_counted_not_fatal(tmp_path, monkeypatch):
    bad = fake_github(fail=("topic%3Allm",))
    try:
        report = pipeline.run(cfg(), GitHub(base=bad.url, sleep=lambda s: None), Gateway(), tmp_path, TODAY, dry_run=True)
    finally:
        bad.close()
    assert report["dropped"]["search failed (HTTP 403)"] == 1 and report["picks"]


def test_a_refused_bundle_leaves_repos_unremembered_so_they_are_offered_again(tmp_path, servers, monkeypatch):
    monkeypatch.setattr(pipeline.contract, "validate", lambda files, c=None: ["bad bundle"])
    pipeline.run(cfg(picks_per_run=2), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    assert not (tmp_path / "state" / "seen.json").exists()


def test_a_second_run_on_the_same_day_gets_its_own_folder_and_campaign_and_both_validate(tmp_path, servers):
    first = go(tmp_path, servers, picks=2)
    second = go(tmp_path, servers, picks=2)
    assert first["campaign"] == "radar-2026-10-14" and second["campaign"] == "radar-2026-10-14-2"
    assert (tmp_path / "digests" / "2026-10-14").is_dir() and (tmp_path / "digests" / "2026-10-14-2").is_dir()
    files = pipeline.read_bundle(tmp_path)
    assert {p.split("/")[1] for p in files if p.startswith("campaigns/")} == {"radar-2026-10-14", "radar-2026-10-14-2"}
    assert contract.validate(files) == []
    c1 = yaml.safe_load(files["campaigns/radar-2026-10-14/campaign.yaml"])["links"]
    c2 = yaml.safe_load(files["campaigns/radar-2026-10-14-2/campaign.yaml"])["links"]
    assert len(c1) == 2 and len(c2) == 2 and not (set(c1.values()) & set(c2.values()))


def test_the_report_flags_a_checker_that_shares_the_writers_family(tmp_path, servers):
    report = pipeline.run(cfg(picks_per_run=1, models={"writer": ["google/gemini-flash-latest"], "checker": ["google/gemma-3"]}),
                          GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    assert report["ok"] and report["written"][0]["independent_checker"] is False and report["warnings"]
    ok = pipeline.run(cfg(picks_per_run=1), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    assert ok["written"][0]["independent_checker"] is True and not ok["warnings"]


def test_pace_is_applied_between_repositories_but_not_after_the_last_call(tmp_path, servers):
    waits = []
    pipeline.run(cfg(picks_per_run=3), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY, pace=45.0, sleep=waits.append)
    assert waits == [45.0, 45.0]                     # 3 repos, 1 language: after repos 1 and 2 only
    waits.clear()
    pipeline.run(cfg(picks_per_run=1, langs=["vi", "en"]), GitHub(), Gateway(sleep=lambda s: None), tmp_path / "b", TODAY,
                 pace=45.0, sleep=waits.append)
    assert waits == [45.0]                           # 1 repo, 2 languages: between the two languages only


def test_the_cli_passes_the_configured_pace_to_the_pipeline(monkeypatch, capsys):
    from radar import cli
    seen = {}
    monkeypatch.setattr(cli.pipeline, "run", lambda *a, **kw: seen.update(kw) or {"ok": True})
    assert cli.main(["run", "--dry-run"]) == 0
    assert seen["pace"] == 45.0 and seen["dry_run"] is True


def test_the_time_budget_stops_new_work_but_keeps_what_was_finished(tmp_path, servers):
    ticks = iter([0, 0, 36 * 60, 36 * 60, 36 * 60])                         # start, repo 1 starts, then 36 minutes have passed
    clock = lambda: next(ticks, 36 * 60)  # noqa: E731
    report = pipeline.run(cfg(picks_per_run=3), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY, clock=clock)
    assert report["aborted"] and "time budget of 35 minutes" in report["aborted"] and report["ok"] is False
    assert [w["repo"] for w in report["written"]] == [report["picks"][0]["repo"]]
    assert contract.validate(pipeline.read_bundle(tmp_path)) == [] and (tmp_path / "state" / "seen.json").exists()
    assert list((tmp_path / "digests").glob("20*/*/vi.md"))                 # the finished repository's digest is on disk


def test_an_aborted_run_keeps_a_repository_whose_primary_language_was_already_written(tmp_path, servers):
    gh, llm = servers
    llm.script = lambda kind, facts, lang, n: (503, {"e": 1}) if lang == "en" and kind == "writer" else None
    report = pipeline.run(cfg(picks_per_run=1, langs=["vi", "en"]), GitHub(), Gateway(sleep=lambda s: None, attempts_per_model=1),
                          tmp_path, TODAY)
    assert report["aborted"] and [w["lang"] for w in report["written"]] == ["vi"]
    assert (tmp_path / "state" / "seen.json").exists() and pipeline.read_bundle(tmp_path)


def test_the_readme_cap_really_limits_what_reaches_both_prompts(tmp_path, monkeypatch):
    big = "\n".join(f"step {i}: run the installer with option number {i} and read the notes" for i in range(3000))      # ~200,000 chars
    gh, llm = fake_github(readme=big), FakeLLM()
    monkeypatch.setenv("GITHUB_API_URL", gh.url)
    for provider in ("GOOGLE", "MISTRAL"):
        monkeypatch.setenv(f"RADAR_BASE_{provider}", llm.url)
    monkeypatch.setenv("GOOGLE_GENERATIVE_AI_API_KEY", "k")
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    try:
        pipeline.run(cfg(picks_per_run=1), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    finally:
        gh.close()
        llm.close()
    users = [c["body"]["messages"][1]["content"] for c in llm.calls]
    assert len(users) >= 2
    for user in users:                                  # the writer prompt and the checker prompt
        readme = user.split("<<<README\n", 1)[1].split("\nREADME>>>", 1)[0]
        assert 0 < len(readme) <= 8000
