import json

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


def test_independent_checkers_come_first_and_the_rest_stay_as_a_last_resort():
    from radar.write import checker_pool
    checkers = ["mistral/mistral-small-2603", "google/gemini-flash-lite-latest"]
    assert checker_pool(checkers, "google/gemini-flash-latest") == ["mistral/mistral-small-2603", "google/gemini-flash-lite-latest"]
    assert checker_pool(checkers, "mistral/mistral-small-2603") == ["google/gemini-flash-lite-latest", "mistral/mistral-small-2603"]
    assert checker_pool(["mistral/a"], "mistral/b") == ["mistral/a"]


class StubGateway:
    """Answers by script: each entry is (kind, model, payload) in call order; a model in `broken` fails like a 404."""

    def __init__(self, steps, broken=()):
        self.steps, self.broken, self.log, self.asked = list(steps), set(broken), [], []

    def chat(self, models, system, user, **kw):
        self.asked.append(list(models))
        kind, model, payload = self.steps.pop(0)
        usable = [m for m in models if m not in self.broken]
        if not usable:
            from radar.llm import AllModelsFailed
            raise AllModelsFailed("no model answered: stub")
        return (json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload), model if model in usable else usable[0]


def test_a_dead_independent_checker_does_not_abort_a_run_that_already_has_a_draft():
    # Mistral wrote (writer fallback); the only independent checker, gemini-lite, is retired (404): the same-family checker is used and flagged.
    cfg = {**CFG, "models": {"writer": ["mistral/mistral-small-2603"], "checker": ["mistral/mistral-small-2603", "google/gemini-flash-lite-latest"]}}
    gw = StubGateway([("w", "mistral/mistral-small-2603", make_draft(FACTS, "vi")),
                      ("c", "mistral/mistral-small-2603", {"verdict": "pass", "issues": []})], broken={"google/gemini-flash-lite-latest"})
    res = write_one(gw, cfg, FACTS, "vi")
    assert res["status"] == "ok" and res["checker"] == "mistral/mistral-small-2603" and res["independent"] is False
    assert gw.asked[1][0] == "google/gemini-flash-lite-latest"          # the independent one was tried first


def test_independence_is_judged_against_the_writer_of_the_final_draft_after_a_fix_round():
    cfg = {**CFG, "models": {"writer": ["google/gemini-flash-latest", "mistral/mistral-small-2603"], "checker": ["mistral/mistral-small-2603"]}}
    issue = {"severity": "blocker", "field": "problem", "problem": "unsupported", "fact": "none"}
    gw = StubGateway([("w", "google/gemini-flash-latest", make_draft(FACTS, "vi")),
                      ("c", "mistral/mistral-small-2603", {"verdict": "fix", "issues": [issue]}),
                      ("w", "mistral/mistral-small-2603", make_draft(FACTS, "vi"))])      # the fix round fell back to mistral
    res = write_one(gw, cfg, FACTS, "vi")
    assert res["fixed"] and res["writer"] == "mistral/mistral-small-2603" and res["independent"] is False
