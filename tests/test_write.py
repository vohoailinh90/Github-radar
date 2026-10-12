import pytest

from radar import config
from radar.llm import AllModelsFailed, Gateway
from radar.write import write_one
from tests.support import FakeLLM, TODAY, make_draft, README, TREE

CFG = config.load(path=config.ROOT / "none.yaml", env={})
FACTS = {"full_name": "example-org/sample-agent-kit", "description": "Run AI agents", "readme": README, "stars": 24000,
         "forks": 2400, "open_issues": 12, "license": "MIT", "language": "Python", "languages": ["Python"], "topics": ["llm"],
         "created": "2024-11-14", "pushed": "2026-10-09", "age_years": 1,
         "tree": TREE + ["src/planner.py", "src/memory.py", "src/tools/"], "scanned": TODAY.isoformat()}


@pytest.fixture
def served(monkeypatch):
    holder = {}

    def make(script=None):
        srv = FakeLLM(script)
        holder["srv"] = srv
        for p in ("GOOGLE", "MISTRAL"):
            monkeypatch.setenv(f"RADAR_BASE_{p}", srv.url)
        return srv
    yield make
    if "srv" in holder:
        holder["srv"].close()


def gw():
    return Gateway(sleep=lambda s: None, env={"GOOGLE_GENERATIVE_AI_API_KEY": "k", "MISTRAL_API_KEY": "k"})


def test_clean_draft_is_written_checked_and_not_rewritten(served):
    srv = served()
    res = write_one(gw(), CFG, FACTS, "vi")
    assert res["status"] == "ok" and not res["fixed"] and srv.counts == {"writer": 1, "checker": 1}
    assert res["writer"].startswith("google/") and res["checker"].startswith("mistral/")


def test_checker_blocker_triggers_exactly_one_fix_round_with_the_issue_in_the_prompt(served):
    issue = {"severity": "blocker", "field": "problem", "problem": "claims a benchmark", "fact": "none"}
    srv = served(lambda kind, facts, lang, n: {"verdict": "fix", "issues": [issue]} if kind == "checker" else None)
    res = write_one(gw(), CFG, FACTS, "vi")
    assert res["fixed"] and srv.counts["writer"] == 2 and srv.counts["checker"] == 1
    fix_prompt = srv.calls[-1]["body"]["messages"][1]["content"]
    assert "claims a benchmark" in fix_prompt and "previous DRAFT" in fix_prompt


def test_a_draft_that_still_fails_the_gates_after_the_fix_round_is_held(served):
    bad = make_draft(FACTS, "vi", problem="Nhanh hơn 95% so với mọi đối thủ, xem https://example.com")
    served(lambda kind, facts, lang, n: bad if kind == "writer" else None)
    res = write_one(gw(), CFG, FACTS, "vi")
    assert res["status"] == "held" and res["fixed"]
    assert any("link or domain" in str(p) for p in res["problems"])


def test_minor_issues_alone_do_not_trigger_a_rewrite(served):
    minor = {"severity": "minor", "field": "hook", "problem": "wordy"}
    srv = served(lambda kind, facts, lang, n: {"verdict": "pass", "issues": [minor]} if kind == "checker" else None)
    assert write_one(gw(), CFG, FACTS, "vi")["fixed"] is False and srv.counts["writer"] == 1


def test_unparseable_output_gets_one_repair_then_fails(served):
    srv = served(lambda kind, facts, lang, n: "not an object" if kind == "writer" else None)
    # the fake wraps non-dict script values as JSON strings, which parse_json rejects as non-objects
    with pytest.raises(AllModelsFailed, match="unparseable"):
        write_one(gw(), CFG, FACTS, "vi")
    assert srv.counts["writer"] == 2


def test_prompt_marks_the_readme_as_data_and_carries_the_language(served):
    srv = served()
    write_one(gw(), CFG, FACTS, "ja")
    system = srv.calls[0]["body"]["messages"][0]["content"]
    user = srv.calls[0]["body"]["messages"][1]["content"]
    assert "never instructions" in system and "Japanese" in system and "<<<README" in user
    assert srv.calls[0]["body"]["response_format"] == {"type": "json_object"}
