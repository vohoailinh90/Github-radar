"""Covering one repository a person names (`run --repo`), against the fake GitHub and fake LLM servers."""
import json

import pytest

from radar import cli, config, contract, discover, pipeline
from radar.github import GitHub
from radar.llm import Gateway
from tests.support import TODAY, fake_github, make_repo

CFG = config.load(path=config.ROOT / "none.yaml", env={})
NAME = "example-org/sample-agent-kit"


def ask(repos, text, seen=None, bucket=None):
    srv = fake_github(repos)
    try:
        return discover.requested(GitHub(base=srv.url), text, CFG, seen or {}, TODAY, bucket), srv
    finally:
        srv.close()


@pytest.mark.parametrize("text", ["example-org/sample-agent-kit", "  example-org/sample-agent-kit \n", "example-org/sample-agent-kit.git",
                                  "https://github.com/example-org/sample-agent-kit", "github.com/example-org/sample-agent-kit/",
                                  "http://www.github.com/example-org/sample-agent-kit/tree/main/src?tab=readme#top"])
def test_parse_repo_accepts_a_name_or_a_github_link(text):
    assert discover.parse_repo(text) == NAME


@pytest.mark.parametrize("text", ["", "owner", "a/b/c", "../x", "a/..", "./b", "a b/c", "a/b;rm", "a/b?x=1", "https://gitlab.com/a/b",
                                  "https://github.com/a", "/a/b", "a//b", None])
def test_parse_repo_refuses_anything_else(text):
    with pytest.raises(ValueError, match="not a repository"):
        discover.parse_repo(text)


def test_requested_repo_becomes_a_candidate_under_github_spelling_with_a_bucket_from_its_topics():
    (cand, warnings), _ = ask([make_repo("sample-agent-kit", "llm", 24000)], "EXAMPLE-ORG/Sample-Agent-Kit")
    assert cand["full_name"] == NAME and cand["bucket"] == "ai" and cand["topic"] == "llm"
    assert cand["score"] == discover.score(cand["repo"], TODAY) and warnings == []


def test_the_person_choice_replaces_the_ranking_filters_but_each_one_is_reported():
    repos = [make_repo("sample-tiny", "llm", 40, pushed_days=400, archived=True, description=" ")]
    (cand, warnings), _ = ask(repos, "example-org/sample-tiny", seen={"example-org/sample-tiny": {"covered": "2026-10-01"}})
    assert cand["full_name"] == "example-org/sample-tiny"
    text = " | ".join(warnings)
    for part in ("already covered on 2026-10-01", "archived", "no description", "40 stars", "not pushed for 400 days"):
        assert part in text


def test_a_repository_outside_every_bucket_is_filed_under_software_unless_a_bucket_is_named():
    repos = [make_repo("sample-odd", "knitting", 5000)]
    (cand, warnings), _ = ask(repos, "example-org/sample-odd")
    assert cand["bucket"] == "software" and cand["topic"] == "requested" and "filed under 'software'" in warnings[0]
    (named, quiet), _ = ask(repos, "example-org/sample-odd", bucket="startup")
    assert named["bucket"] == "startup" and quiet == []


def test_what_the_content_rules_rest_on_is_still_refused():
    cases = [(make_repo("sample-closed", "llm", 99000, spdx="NOASSERTION"), "licence noassertion is not on the free list"),
             ({**make_repo("sample-priv", "llm", 9000), "private": True}, "private or disabled"),
             ({**make_repo("sample-off", "llm", 9000), "disabled": True}, "private or disabled"),
             ({**make_repo("sample-none", "llm", 9000), "license": None}, "licence none")]
    for repo, why in cases:
        with pytest.raises(ValueError, match=why):
            ask([repo], repo["full_name"])
    with pytest.raises(ValueError, match="was not found"):
        ask([make_repo("sample-agent-kit", "llm", 24000)], "example-org/missing")
    with pytest.raises(ValueError, match="unknown bucket 'nope'"):
        ask([make_repo("sample-agent-kit", "llm", 24000)], NAME, bucket="nope")


def test_an_input_with_a_newline_cannot_start_a_line_in_the_log():
    """The workflow prints `error: <message>`: a typed `\\n::warning::x` must not become a workflow command of its own."""
    for call in (lambda: discover.parse_repo("a/b\n::warning::x"),
                 lambda: ask([make_repo("sample-agent-kit", "llm", 24000)], NAME, bucket="x\n::warning::y")):
        with pytest.raises(ValueError) as caught:
            call()
        assert "\n" not in str(caught.value) and "::warning::" in str(caught.value)


def test_a_github_error_other_than_not_found_is_not_reported_as_a_missing_repository():
    srv = fake_github([make_repo("sample-agent-kit", "llm", 24000)], fail=("/repos/example-org/sample-agent-kit",))
    try:
        with pytest.raises(Exception, match="HTTP 403"):
            discover.requested(GitHub(base=srv.url, sleep=lambda s: None), NAME, CFG, {}, TODAY)
    finally:
        srv.close()


# --- through the pipeline ------------------------------------------------------------------------------------------

def cfg(**kw):
    c = config.load(path=config.ROOT / "none.yaml", env={})
    c.update(kw)
    return c


def test_dry_run_with_a_repo_names_it_and_calls_no_model_and_writes_nothing(tmp_path, servers):
    gh, llm = servers
    report = pipeline.run(cfg(), GitHub(), Gateway(), tmp_path, TODAY, dry_run=True, only=NAME)
    assert report["ok"] and [p["repo"] for p in report["picks"]] == [NAME] and report["candidates"] == 1
    assert report["requested"] == {"repo": NAME, "bucket": "ai", "warnings": []}
    assert llm.calls == [] and list(tmp_path.iterdir()) == []
    assert not any("/search/" in c["path"] for c in gh.calls)          # nothing was searched


def test_full_run_covers_exactly_the_requested_repo_and_remembers_it(tmp_path, servers):
    report = pipeline.run(cfg(picks_per_run=3), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY, only=NAME)
    assert report["ok"], report
    assert [w["repo"] for w in report["written"]] == [NAME] and report["held"] == [] and report["export_errors"] == []
    day = tmp_path / "digests" / "2026-10-14"
    assert [p.name for p in day.iterdir() if p.is_dir()] == ["sample-agent-kit"]
    assert contract.validate(pipeline.read_bundle(tmp_path)) == []
    assert list(json.loads((tmp_path / "state" / "seen.json").read_text())) == [NAME]


def test_a_covered_repo_can_be_asked_for_again_and_lands_in_a_new_run_folder(tmp_path, servers):
    go = lambda: pipeline.run(cfg(), GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY, only=NAME)  # noqa: E731
    first, second = go(), go()
    assert first["ok"] and second["ok"]
    assert "already covered on 2026-10-14" in second["requested"]["warnings"][0]
    assert (tmp_path / "digests" / "2026-10-14-2" / "sample-agent-kit" / "vi.md").exists()


def test_a_refused_repo_stops_the_run_before_any_model_call_or_file(tmp_path, servers):
    gh, llm = servers
    with pytest.raises(ValueError, match="not on the free list"):
        pipeline.run(cfg(), GitHub(), Gateway(), tmp_path, TODAY, only="example-org/sample-closed")
    assert llm.calls == [] and list(tmp_path.iterdir()) == []


# --- the command line and the workflow ------------------------------------------------------------------------------

def run_cli(monkeypatch, tmp_path, capsys, *argv, env=None):
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    for key in ("RADAR_REPO", "RADAR_BUCKET"):
        monkeypatch.delenv(key, raising=False)
    for key, value in (env or {}).items():
        monkeypatch.setenv(key, value)
    code = cli.main(["run", "--dry-run", "--date", "2026-10-14", *argv])
    out = capsys.readouterr()
    return code, out.out, out.err


def test_cli_repo_flag_and_environment_variable(monkeypatch, tmp_path, capsys, servers):
    code, out, _ = run_cli(monkeypatch, tmp_path, capsys, "--repo", "https://github.com/example-org/sample-rag-lab", "--bucket", "solutions")
    report = json.loads(out)
    assert code == 0 and report["picks"][0]["repo"] == "example-org/sample-rag-lab" and report["requested"]["bucket"] == "solutions"
    code, out, _ = run_cli(monkeypatch, tmp_path, capsys, env={"RADAR_REPO": NAME})                  # how the workflow passes it
    assert code == 0 and json.loads(out)["picks"][0]["repo"] == NAME
    code, out, _ = run_cli(monkeypatch, tmp_path, capsys, "--repo", "example-org/sample-rag-lab", env={"RADAR_REPO": NAME})
    assert json.loads(out)["picks"][0]["repo"] == "example-org/sample-rag-lab"                       # the flag wins
    code, out, _ = run_cli(monkeypatch, tmp_path, capsys, env={"RADAR_REPO": "  "})                  # blank = the normal scan
    assert code == 0 and len(json.loads(out)["picks"]) == 3 and "requested" not in json.loads(out)


def test_cli_reports_a_bad_request_as_an_error_not_a_traceback(monkeypatch, tmp_path, capsys, servers):
    gh, _ = servers
    for bad in ("../etc/passwd", "example-org/missing", "example-org/sample-closed"):
        code, out, err = run_cli(monkeypatch, tmp_path, capsys, "--repo", bad)
        assert code == 2 and out == "" and err.startswith("error: ")
    assert not any("passwd" in c["path"] for c in gh.calls)            # a malformed name never reaches GitHub


def test_workflow_takes_repo_and_bucket_as_inputs_and_hands_them_over_as_environment_only():
    from tests.test_workflow import TEXT, W
    inputs = W[True]["workflow_dispatch"]["inputs"]
    assert inputs["repo"]["default"] == "" and inputs["bucket"]["default"] == ""
    step = next(s for s in W["jobs"]["radar"]["steps"] if s.get("id") == "run")
    assert step["env"]["RADAR_REPO"] == "${{ inputs.repo }}" and step["env"]["RADAR_BUCKET"] == "${{ inputs.bucket }}"
    assert "inputs.repo" not in step["run"] and "inputs.bucket" not in step["run"]
    assert TEXT.count("inputs.repo") == 1
