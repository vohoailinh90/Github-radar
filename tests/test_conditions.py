import copy
import json

import pytest
import yaml

from radar import cli, conditions, config, pipeline
from radar.github import GitHub
from radar.llm import Gateway
from tests.support import TODAY, fake_github

IDS = ["ai", "software", "solutions", "startup"]
BASE = config.load(path=config.ROOT / "none.yaml", env={})


def bad(obj, match):
    with pytest.raises(ValueError, match=match):
        conditions.sanitize(obj, IDS)


def test_a_valid_set_of_conditions_comes_back_clean():
    obj = {"picks_per_run": 2, "min_stars": 3000, "max_days_since_push": 60, "langs": ["vi", "en"],
           "rising": {"enabled": True, "slots": 1, "created_within_days": 90, "min_stars": 200},
           "buckets": {"ai": ["llm", "rag"], "startup": ["saas"]}}
    assert conditions.sanitize(obj, IDS) == obj
    assert conditions.sanitize({}, IDS) == {}


@pytest.mark.parametrize("obj,match", [
    ([], "JSON object"), ("x", "JSON object"), (None, "JSON object"),
    ({"licenses": ["mit"]}, "unknown condition"), ({"models": {}}, "unknown condition"), ({"pace_seconds": 0}, "unknown condition"),
    ({"picks_per_run": "3"}, "whole number"), ({"picks_per_run": True}, "whole number"), ({"picks_per_run": 2.5}, "whole number"),
    ({"picks_per_run": 0}, "between 1 and 10"), ({"picks_per_run": 11}, "between 1 and 10"), ({"min_stars": -1}, "between 0"),
    ({"min_stars": 10**7}, "between 0"), ({"max_days_since_push": 0}, "between 1"),
    ({"langs": []}, "langs"), ({"langs": ["fr"]}, "langs"), ({"langs": ["vi", "vi"]}, "langs"), ({"langs": "vi"}, "langs"), ({"langs": [1]}, "langs"),
    ({"rising": []}, "rising must be an object"), ({"rising": {"enabled": 1}}, "true or false"), ({"rising": {"slots": 11}}, "rising.slots"),
    ({"rising": {"bogus": 1}}, "unknown rising"), ({"rising": {"created_within_days": 0}}, "rising.created_within_days"),
    ({"buckets": {}}, "non-empty"), ({"buckets": []}, "non-empty"), ({"buckets": {"nope": ["llm"]}}, "unknown bucket"),
    ({"buckets": {"ai": []}}, "1 to 8"), ({"buckets": {"ai": ["a"] * 2}}, "twice"), ({"buckets": {"ai": [f"t{i}" for i in range(9)]}}, "1 to 8"),
    ({"buckets": {"ai": "llm"}}, "1 to 8"),
])
def test_every_kind_of_bad_condition_is_refused(obj, match):
    bad(obj, match)


@pytest.mark.parametrize("topic", [
    "llm stars:>0", "llm stars:>=0 pushed:>2000-01-01", "llm\n", "llm\nstars:>0", "LLM", "-llm", "llm topic:x", "llm OR rag", "a" * 51,
    "llm‮", "ll m", "llm:x", "", " llm", "llm ", "topic:llm", "llm\u0000",
])
def test_a_topic_that_could_change_the_search_query_is_refused(topic):
    bad({"buckets": {"ai": [topic]}}, "not a GitHub topic")           # fullmatch, not "$": "llm\n" must not slip through
    cfg = copy.deepcopy(BASE)
    cfg["buckets"][0]["topics"] = [topic]
    with pytest.raises(ValueError, match="GitHub would not accept"):   # radar.yaml is held to the same rule, at the line that builds the query
        config.validate(cfg)


def test_error_messages_never_carry_a_raw_newline_or_the_whole_input():
    for obj in ({"x" * 500 + "\n::set-output name=a::b": 1}, {"buckets": {"ai": ["llm\n::error::forged"]}}, {"min_stars": "9\n::error::forged"}):
        with pytest.raises(ValueError) as err:
            conditions.sanitize(obj, IDS)
        msg = str(err.value)
        assert "\n" not in msg and len(msg) < 300


def test_json_is_parsed_strictly_and_never_echoed():
    parse = lambda t: conditions.parse_json(t, "RADAR_CONDITIONS")  # noqa: E731
    assert parse('{"a": 1}') == {"a": 1}
    for text, match in (('{"a": NaN}', "not allowed"), ('{"a": Infinity}', "not allowed"), ('{"a": 1, "a": 2}', "duplicate"),
                        ('{"a": ', "not valid JSON"), ("x" * 5000, "longer than"), ("[" * 100000, "RADAR_CONDITIONS")):
        with pytest.raises(ValueError, match=match):
            parse(text)
    with pytest.raises(ValueError) as err:
        parse('{"secret-token-123": ')
    assert "secret-token-123" not in str(err.value)


def test_apply_copies_and_replaces_the_buckets_wholesale():
    before = copy.deepcopy(BASE)
    out = conditions.apply(BASE, {"picks_per_run": 2, "rising": {"slots": 0}, "buckets": {"startup": ["saas"], "ai": ["llm"]}})
    assert BASE == before                                                  # the input is never touched
    assert out["picks_per_run"] == 2 and out["rising"] == {**BASE["rising"], "slots": 0}
    assert [b["id"] for b in out["buckets"]] == ["ai", "startup"]           # radar.yaml's order, only the named buckets
    assert out["buckets"][0]["emoji"] == "🤖" and out["buckets"][0]["topics"] == ["llm"]
    out["buckets"][0]["topics"].append("x")
    assert BASE["buckets"][0]["topics"] == before["buckets"][0]["topics"]


def test_resolved_and_estimate_report_final_values_and_costs():
    cfg = conditions.apply(BASE, {"buckets": {"ai": ["llm", "rag"]}, "picks_per_run": 3, "langs": ["vi", "en"]})
    assert conditions.resolved(cfg)["buckets"] == {"ai": ["llm", "rag"]} and conditions.resolved(cfg)["langs"] == ["vi", "en"]
    est = conditions.estimate(cfg)
    assert est == {"searches": 4, "search_seconds": 8, "model_calls": 12, "pace_seconds": 5 * 45}      # 2 topics x 2 passes; 6 posts x 2 calls
    off = conditions.apply(cfg, {"rising": {"slots": 0}})
    assert conditions.estimate(off)["searches"] == 2
    assert conditions.estimate(BASE)["searches"] == 32 and conditions.estimate(BASE)["model_calls"] == 6


# --- how the conditions meet config.load ------------------------------------------------------------------------------

def load(**env):
    return config.load(path=config.ROOT / "radar.yaml", env=env)


def test_nothing_set_means_radar_yaml_exactly_as_before():
    plain = load()
    assert plain["scan_label"] is None and plain == load(RADAR_PRESET="none", RADAR_CONDITIONS="")
    assert plain["picks_per_run"] == 3 and len(plain["buckets"]) == 4


def test_a_saved_preset_inline_conditions_and_the_precedence_between_them():
    ai = load(RADAR_PRESET="ai-sau")
    assert ai["scan_label"] == "ai-sau" and [b["id"] for b in ai["buckets"]] == ["ai"]
    inline = load(RADAR_PRESET="ai-sau", RADAR_CONDITIONS='{"picks_per_run": 1, "buckets": {"startup": ["saas"]}}')
    assert inline["scan_label"] == "ai-sau" and inline["picks_per_run"] == 1                  # inline wins; the preset name is only the label
    assert [b["id"] for b in inline["buckets"]] == ["startup"]                                 # and the buckets are replaced, not merged
    assert load(RADAR_CONDITIONS='{"min_stars": 5000}')["scan_label"] == "custom"
    assert load(RADAR_PRESET="ai-sau", RADAR_PICKS="2")["picks_per_run"] == 2                  # the explicit variables are more specific
    assert load(RADAR_CONDITIONS='{"langs": ["vi"]}', RADAR_LANGS="vi,en")["langs"] == ["vi", "en"]


def test_a_bad_preset_or_condition_stops_the_run_before_anything_is_fetched():
    for env, match in (({"RADAR_PRESET": "nope"}, "unknown preset"), ({"RADAR_PRESET": "../etc"}, "not a preset name"),
                       ({"RADAR_CONDITIONS": '{"models": 1}'}, "unknown condition"), ({"RADAR_CONDITIONS": "{"}, "not valid JSON"),
                       ({"RADAR_CONDITIONS": '{"rising": {"slots": 5}, "picks_per_run": 2}'}, "slots between 0 and picks_per_run")):
        with pytest.raises(ValueError, match=match):
            load(**env)


def test_the_validation_runs_once_after_every_layer():
    # slots 1 is fine at 3 picks; the conditions alone (picks 1) are fine too; together with an explicit RADAR_PICKS=1 it still is
    assert load(RADAR_CONDITIONS='{"picks_per_run": 1}', RADAR_PICKS="1")["picks_per_run"] == 1
    with pytest.raises(ValueError, match="slots between 0 and picks_per_run"):
        load(RADAR_CONDITIONS='{"rising": {"slots": 3}}', RADAR_PICKS="2")      # only the final combination is invalid


def test_loading_never_changes_the_defaults():
    snapshot = copy.deepcopy(config.DEFAULTS)
    config.load(path=config.ROOT / "none.yaml", env={"RADAR_MODELS_WRITER": "google/x"})           # no file, no conditions: the override used to land in DEFAULTS
    config.load(path=config.ROOT / "none.yaml", env={"RADAR_MODELS_WRITER": "google/x", "RADAR_CONDITIONS": '{"buckets": {"ai": ["llm"]}}'})
    config.load(path=config.ROOT / "radar.yaml", env={"RADAR_MODELS_CHECKER": "groq/y", "RADAR_PRESET": "quet-nhanh"})
    assert config.DEFAULTS == snapshot


# --- the saved presets ------------------------------------------------------------------------------------------------

def test_every_saved_preset_is_valid_against_the_real_radar_yaml():
    presets = conditions.load_presets()
    assert len(presets) >= 3
    for name, item in presets.items():
        cfg = load(RADAR_PRESET=name)                                      # sanitize + apply + validate, as a scan would
        assert cfg["scan_label"] == name and len(item["label"]) <= 60
        est = conditions.estimate(cfg)
        assert est["searches"] >= 1 and est["model_calls"] >= 2


def test_the_presets_file_is_strict(tmp_path):
    def write(text):
        path = tmp_path / "p.json"
        path.write_text(text, encoding="utf-8")
        return path
    for text in ('{"presets": []}', '{"presets": {"Bad Name": {"label": "x", "conditions": {}}}}',
                 '{"presets": {"ok": {"label": "x"}}}', '{"presets": {"ok": {"label": "", "conditions": {}}}}',
                 '{"presets": {"ok": {"label": "x", "conditions": {}, "extra": 1}}}', '{"presets": {"a": {}, "a": {}}}', "[]"):
        with pytest.raises(ValueError):
            conditions.load_presets(write(text))
    assert conditions.load_presets(tmp_path / "missing.json") == {}
    good = write('{"presets": {"ok": {"label": "x", "conditions": {"min_stars": 1}}}}')
    assert conditions.preset("ok", IDS, good) == {"min_stars": 1}
    with pytest.raises(ValueError, match="unknown preset"):
        conditions.preset("zzz", IDS, good)


def test_the_schema_is_plain_json_for_a_front_end_to_be_checked_against():
    s = conditions.schema()
    assert json.loads(json.dumps(s)) == s and s["topic_pattern"] == conditions.TOPIC.pattern and s["langs"] == ["vi", "en", "ja"]
    assert set(s["ints"]) == {"picks_per_run", "min_stars", "max_days_since_push"}


# --- the run report and the command line ------------------------------------------------------------------------------

def test_every_run_report_records_the_conditions_it_ran_with(tmp_path, monkeypatch):
    srv = fake_github()
    monkeypatch.setenv("GITHUB_API_URL", srv.url)
    try:
        plain = pipeline.run(BASE, GitHub(), Gateway(), tmp_path, TODAY, dry_run=True)
        cfg = config.load(path=config.ROOT / "none.yaml", env={"RADAR_CONDITIONS": '{"buckets": {"ai": ["llm", "rag"]}, "picks_per_run": 2}',
                                                               "RADAR_PRESET": "ai-sau"})
        narrowed = pipeline.run(cfg, GitHub(), Gateway(), tmp_path, TODAY, dry_run=True)
    finally:
        srv.close()
    assert plain["conditions"]["label"] is None and plain["conditions"]["resolved"]["picks_per_run"] == 3
    assert narrowed["conditions"] == {"label": "ai-sau", "resolved": {**conditions.resolved(cfg)}}
    assert narrowed["conditions"]["resolved"]["buckets"] == {"ai": ["llm", "rag"]}
    assert {p["bucket"] for p in narrowed["picks"]} == {"ai"} and len(narrowed["picks"]) <= 2


def test_the_command_line_takes_the_same_conditions(capsys):
    assert cli.main(["presets"]) == 0
    out = capsys.readouterr().out
    assert "ai-sau" in out and "searches" in out and "quet-nhanh" in out
    assert cli.main(["scan", "--preset", "nope"]) == 2
    assert cli.main(["run", "--dry-run", "--conditions", '{"min_stars": "x"}']) == 2
    err = capsys.readouterr().err
    assert "unknown preset 'nope'" in err and "min_stars must be a whole number" in err
