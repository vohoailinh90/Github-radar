"""A repository a hand-written report studied is not written again by the scan (CLAUDE.md "One repository, one digest")."""
import json
from pathlib import Path

from radar import config, discover, pipeline, reports
from radar.github import GitHub
from radar.llm import Gateway
from tests.support import TODAY, fake_github, make_repo

CFG = config.load(path=config.ROOT / "none.yaml", env={})
ROOT = Path(__file__).resolve().parent.parent


def report(root, name, **files):
    folder = root / "docs" / "reports" / name
    folder.mkdir(parents=True)
    for fname, data in files.items():
        (folder / fname).write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


def test_covered_reads_the_repositories_a_report_lists_whatever_the_file_shape(tmp_path):
    report(tmp_path, "one", **{"deck.json": {"source": {"repo": "https://github.com/Org-A/Tool-One", "commit": "abc"}}})
    report(tmp_path, "two", **{"sources.json": [{"repo": "Org-B/tool-two", "url": "https://github.com/org-b/tool-two/blob/main/x.md"}]})
    report(tmp_path, "three", **{"sources.json": {"sources": [
        {"url": "https://github.com/search?q=stars%3A%3E1&type=repositories", "pinned_url": None},
        {"pinned_url": "https://github.com/Org-C/tool-three.git/blob/0a1b/README.md"}]}})
    assert reports.covered(tmp_path) == {"org-a/tool-one": "one", "org-b/tool-two": "two", "org-c/tool-three": "three"}


def test_extraction_edge_cases(tmp_path):
    text = ("see https://notgithub.com/x/y, then github.com/Foo/Bar. and https://github.com/topics/ai, "
            "https://github.com/orgs/acme/people and (https://github.com/a/b.js).")
    assert reports._names(text) == {"foo/bar", "a/b.js"}


def test_a_missing_folder_or_a_broken_file_covers_nothing_and_does_not_raise(tmp_path):
    assert reports.covered(tmp_path) == {}
    report(tmp_path, "broken", **{"deck.json": "{not json", "sources.json": "[]"})
    assert reports.covered(tmp_path) == {}


def test_the_reports_of_this_repository_are_all_read():
    """Each report folder must name at least one repository in deck.json or sources.json, or the scan cannot know it exists."""
    found = reports.covered(ROOT)
    for folder in sorted(p for p in (ROOT / "docs" / "reports").iterdir() if p.is_dir()):
        assert folder.name in found.values(), f"{folder.name}: no repository found in deck.json or sources.json"
    for repo in ("graphify-labs/graphify", "tt-a1i/archify", "nirdiamant/genai_agents", "sindresorhus/awesome",
                 "public-apis/public-apis", "codecrafters-io/build-your-own-x", "obra/superpowers"):
        assert repo in found, repo


def test_eligible_drops_a_repository_a_report_covers_whatever_its_case():
    repo = make_repo("a", "llm", 5000)                                  # example-org/a
    assert discover.eligible(repo, CFG, {}, TODAY) is None
    assert discover.eligible(repo, CFG, {}, TODAY, reports={"example-org/a": "r"}) == discover.REPORT_COVERED
    assert discover.eligible({**repo, "full_name": "Example-Org/A"}, CFG, {}, TODAY, reports={"example-org/a": "r"}) == discover.REPORT_COVERED
    assert discover.eligible(repo, CFG, {"example-org/a": {}}, TODAY, reports={"example-org/a": "r"}) == "already covered"


def test_candidates_count_the_repositories_dropped_for_a_report():
    srv = fake_github()
    try:
        free, _ = discover.candidates(GitHub(base=srv.url), CFG, {}, TODAY)
        one = free[0]["full_name"]
        ranked, dropped = discover.candidates(GitHub(base=srv.url), CFG, {}, TODAY, reports={one.lower(): "r"})
    finally:
        srv.close()
    assert one not in [c["full_name"] for c in ranked] and dropped[discover.REPORT_COVERED] == 1


def test_requested_warns_but_still_writes_when_a_report_covers_the_repository():
    srv = fake_github([make_repo("sample-agent-kit", "llm", 24000)])
    try:
        cand, warnings = discover.requested(GitHub(base=srv.url), "example-org/sample-agent-kit", CFG, {}, TODAY,
                                            reports={"example-org/sample-agent-kit": "demo"})
    finally:
        srv.close()
    assert cand["full_name"] == "example-org/sample-agent-kit"
    assert warnings == ["already covered by the report docs/reports/demo: written again"]


def test_a_scan_skips_what_a_report_covers_and_never_writes_it_into_the_seen_list(tmp_path, servers):
    cfg = CFG | {"picks_per_run": 3}
    first = pipeline.run(cfg, GitHub(), Gateway(), tmp_path, TODAY, dry_run=True)
    top = [p["repo"] for p in first["picks"]]
    report(tmp_path, "demo", **{"sources.json": [{"repo": top[0].upper()}]})
    again = pipeline.run(cfg, GitHub(), Gateway(sleep=lambda s: None), tmp_path, TODAY)
    picked = [p["repo"] for p in again["picks"]]
    assert top[0] not in picked and again["dropped"][discover.REPORT_COVERED] >= 1
    seen = json.loads((tmp_path / "state" / "seen.json").read_text())
    assert top[0] not in seen and set(seen) == {w["repo"] for w in again["written"]}


def test_the_trial_scan_command_uses_the_same_report_filter_as_a_real_run(tmp_path, servers, monkeypatch, capsys):
    from radar import cli
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    assert cli.main(["scan", "--date", "2026-10-14"]) == 0
    top = capsys.readouterr().out.split("\n")[1].split()[-1]               # the best-ranked repository of the trial scan
    report(tmp_path, "demo", **{"sources.json": [{"repo": top}]})
    cli.main(["scan", "--date", "2026-10-14"])
    out = capsys.readouterr().out
    assert top not in out and discover.REPORT_COVERED in out
