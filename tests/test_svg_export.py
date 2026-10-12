import xml.etree.ElementTree as ET

import pytest
import yaml

from radar import config, contract, svg, studio_export
from radar.labels import L
from tests.support import make_draft
from tests.test_write import FACTS

CFG = config.load(path=config.ROOT / "none.yaml", env={})
FACTS = {**FACTS, "bucket": "ai", "url": "https://github.com/example-org/sample-agent-kit"}


def wellformed(text):
    root = ET.fromstring(text)
    assert root.tag.endswith("svg")
    return root


@pytest.mark.parametrize("lang", ["vi", "en", "ja"])
def test_every_diagram_is_wellformed_xml_in_every_language(lang):
    d = make_draft(FACTS, lang)
    hiw = d["how_it_works"]
    for text in (svg.card(FACTS, d, L[lang]), svg.flow(hiw["components"], hiw["flow"], "t"), svg.steps(hiw["steps"], "t"),
                 svg.bars([("a/b", 10), ("c/d", 2000)], "t")):
        wellformed(text)


def test_text_is_escaped_so_a_hostile_title_cannot_inject_markup():
    d = make_draft(FACTS, "en", title='<script>alert(1)</script> & "x"')
    out = svg.card(FACTS, d, L["en"])
    assert "<script>" not in out and "&lt;script&gt;" in out
    wellformed(out)


def test_flow_survives_cycles_self_free_graphs_and_no_edges():
    comps = [{"name": f"C{i}", "role": "does a thing " * 6} for i in range(5)]
    for edges in ([[0, 1], [1, 2], [2, 0], [2, 3], [3, 4]], [], [[4, 0], [3, 0]]):
        wellformed(svg.flow(comps, edges, "t"))


def test_wrap_respects_width_for_latin_and_breaks_cjk_without_spaces():
    lines = svg.wrap("một hai ba bốn năm sáu bảy tám chín mười " * 3, 20, 200)
    assert len(lines) > 3 and all(svg.width(line, 20) <= 200 + 1e-6 for line in lines)
    cjk = svg.wrap("これは長い日本語の文章でスペースがありません" * 2, 20, 200)
    assert len(cjk) > 1 and all(svg.width(line, 20) <= 200 + 1e-6 for line in cjk)
    assert svg.wrap("word " * 100, 20, 200, max_lines=2)[-1].endswith("…")


def entries():
    return [{"facts": FACTS, "drafts": {lang: make_draft(FACTS, lang) for lang in ("vi", "en", "ja")}}]


def test_bundle_satisfies_the_vendored_studio_contract():
    cfg = {**CFG, "langs": ["vi", "en", "ja"]}
    files = studio_export.bundle(entries(), cfg, "2026-10-14")
    assert contract.validate(files) == []
    assert "campaigns/radar-2026-10-14/campaign.yaml" in files and "tools/github-radar/brief.yaml" in files
    post = yaml.safe_load(files["campaigns/radar-2026-10-14/posts/vi/01-sample-agent-kit.yaml"])
    assert post["status"] == "draft" and len(post["slides"]) <= 10
    assert post["platforms"]["facebook"]["first_comment"].endswith("{link}")
    camp = yaml.safe_load(files["campaigns/radar-2026-10-14/campaign.yaml"])
    assert camp["links"] == {"01-sample-agent-kit": FACTS["url"]} and camp["langs"] == ["vi", "en", "ja"]


def test_contract_rejects_what_the_studio_rejects():
    files = studio_export.bundle(entries(), CFG, "2026-10-14")
    key = next(k for k in files if "/posts/" in k)
    post = yaml.safe_load(files[key])

    def broken(fn):
        p = yaml.safe_load(files[key])
        fn(p)
        return contract.validate({**files, key: yaml.safe_dump(p, allow_unicode=True)})

    assert any("URL" in e for e in broken(lambda p: p["slides"][0].update(subtitle="see https://x.dev")))
    assert any("URL" in e for e in broken(lambda p: p["slides"][0].update(subtitle="run install.sh")))
    assert any("{link}" in e for e in broken(lambda p: p["slides"][0].update(subtitle="{link}")))
    assert any("unknown layout" in e for e in broken(lambda p: p["slides"].append({"layout": "nope"})))
    assert any("no field" in e for e in broken(lambda p: p["slides"][0].update(bogus=1)))
    assert any("slides" in e for e in broken(lambda p: p["slides"].extend(p["slides"])))
    assert any("hook" in e for e in broken(lambda p: p["platforms"]["facebook"].update(caption="x" * 130)))
    assert any("not defined" in e for e in broken(lambda p: p.update(link="missing")))
    assert any("caption" in e for e in broken(lambda p: p["platforms"]["facebook"].pop("caption")))
    assert post["slides"][0]["layout"] == "cover"


def test_shorten_prefers_sentence_boundaries():
    s = studio_export.shorten("First sentence here. Second sentence goes on and on and on for a very long time.", 40)
    assert s == "First sentence here."
    assert studio_export.shorten("x" * 100, 20).endswith("…") and len(studio_export.shorten("x" * 100, 20)) == 20


def test_a_long_repository_name_never_runs_under_its_bar():
    long_name = "some-organisation/an-extremely-long-repository-name-that-keeps-going"
    text, px = svg.fit(long_name.rpartition("/")[2], 21, 300)
    assert svg.width(text, px) <= 300 and px >= 13 and text.endswith("…")
    short, spx = svg.fit("sample-agent-kit", 21, 300)
    assert short == "sample-agent-kit" and spx == 21
    root = wellformed(svg.bars([(long_name, 5), ("a/b", 90000)], "t"))
    visible = " ".join(t.text or "" for t in root.iter("{http://www.w3.org/2000/svg}tspan"))
    assert long_name.rpartition("/")[2] not in visible and "…" in visible       # cut on screen; the <desc> keeps the full name


def test_vietnamese_uses_dots_for_thousands_and_the_others_commas():
    assert svg.fmt_int(24000, L["vi"]["sep"]) == "24.000" and svg.fmt_int(24000, L["en"]["sep"]) == "24,000"
    files = studio_export.bundle(entries(), CFG, "2026-10-14")
    post = yaml.safe_load(files["campaigns/radar-2026-10-14/posts/vi/01-sample-agent-kit.yaml"])
    assert next(s for s in post["slides"] if s["layout"] == "stat")["value"] == "24.000"


def test_markdown_digest_fields_cannot_become_headings_lists_or_links(tmp_path):
    from radar import digest
    d = make_draft(FACTS, "vi", title="# Tiêu đề\n## giả", learn=["- mục giả", "1. số giả", "> trích giả"], caveats=["| a | b |", "ok"])
    digest.render_repo(tmp_path, "2026-10-14", FACTS, {"vi": d})
    md = (tmp_path / "digests" / "2026-10-14" / "sample-agent-kit" / "vi.md").read_text(encoding="utf-8")
    lines = md.splitlines()
    assert lines[0].startswith("# \\#") and "\n## giả" not in md
    assert not any(line.startswith(("- mục giả", "1. số giả", "> trích")) for line in lines)


def test_domain_shaped_tokens_are_stripped_from_studio_posts_so_the_real_studio_accepts_them():
    d = make_draft(FACTS, "vi")
    d["how_it_works"]["steps"][0]["text"] = "Planner đọc planner.py rồi mở https://example.com/a và www.evil.dev để chạy installer.sh."
    d["facebook"]["caption"] = "Xem planner.py nhé\n\nDòng hai có main.py"
    files = studio_export.bundle([{"facts": FACTS, "drafts": {"vi": d}}], CFG, "2026-10-14")
    assert contract.validate(files) == []
    post = yaml.safe_load(files["campaigns/radar-2026-10-14/posts/vi/01-sample-agent-kit.yaml"])
    flow = next(s for s in post["slides"] if s["layout"] == "flow")
    assert "planner" in flow["steps"][0]["text"] and "https" not in flow["steps"][0]["text"] and ".py" not in flow["steps"][0]["text"]
    assert post["platforms"]["facebook"]["caption"].startswith("Xem planner nhé\n\n")
