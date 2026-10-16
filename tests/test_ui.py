"""docs/ui/index.html: what can be proven without a browser. The page copies a few values from Python (presets, limits, costs) and
re-implements the arithmetic of radar/conditions.py, so a test runs that copy under Node against the Python original; and it
holds the one secret a person types in, so the file is also checked for everything that could leak it or run foreign code."""

import copy
import itertools
import json
import re
import shutil
import subprocess

import pytest

from radar import conditions, config
from scripts import ui_sync

PAGE = ui_sync.PAGE
HTML = PAGE.read_text(encoding="utf-8")
NODE = shutil.which("node")


def _logic() -> str:
    return HTML.split("/* LOGIC:BEGIN", 1)[1].split("*/", 1)[1].split("/* LOGIC:END */", 1)[0]


def _cfg() -> dict:
    return config.load(path=config.ROOT / "radar.yaml", env={})


# ---- the page keeps in step with the code it mirrors -------------------------------------------------------------------

def test_the_data_block_and_the_csp_hashes_are_in_step():
    assert ui_sync.synced(HTML) == HTML, "run python3 scripts/ui_sync.py"
    assert ui_sync.main(["--check"]) == 0


def test_a_stale_page_is_reported(tmp_path, monkeypatch, capsys):
    stale = tmp_path / "index.html"
    stale.write_text(HTML.replace('"min_stars": 1500', '"min_stars": 1'), encoding="utf-8")
    monkeypatch.setattr(ui_sync, "PAGE", stale)
    assert ui_sync.main(["--check"]) == 1 and "out of step" in capsys.readouterr().out
    assert ui_sync.main([]) == 0 and ui_sync.main(["--check"]) == 0                          # and the rewrite fixes it
    assert stale.read_text(encoding="utf-8") == HTML


def test_editing_the_script_changes_its_hash():
    edited = HTML.replace("const API =", "const API2 =", 1)
    assert ui_sync.synced(edited) != edited and ui_sync.synced(ui_sync.synced(edited)) == ui_sync.synced(edited)


def test_the_data_block_matches_python():
    data = json.loads(re.search(r'id="radar-data">(.*?)</script>', HTML, re.S).group(1))
    assert data == json.loads(json.dumps(ui_sync.data()))
    assert data["schema"] == conditions.schema() and data["presets"] == conditions.load_presets()
    assert data["base"] == conditions.resolved(_cfg())
    assert "<" not in re.search(r'id="radar-data">(.*?)</script>', HTML, re.S).group(1)       # no value can close the script element


# ---- the page can neither leak the token nor run foreign code ---------------------------------------------------------

FORBIDDEN = ["innerHTML", "outerHTML", "insertAdjacentHTML", "eval(", "new Function", "Function(", "document.write", "localStorage",
             "sessionStorage", "indexedDB", "document.cookie", "XMLHttpRequest", "WebSocket", "EventSource", "postMessage", "window.open",
             "sendBeacon", "importScripts", "import(", "serviceWorker", "location", "console.", "caches.", "srcdoc", "javascript:"]
FORBIDDEN_TAGS = ["<iframe", "<frame", "<link", "<img", "<form", "<object", "<embed", "<base", "<audio", "<video", "<source", "<svg"]


@pytest.mark.parametrize("word", FORBIDDEN)
def test_the_script_never_uses(word):
    assert word not in HTML


@pytest.mark.parametrize("tag", FORBIDDEN_TAGS)
def test_the_page_never_contains(tag):
    assert tag not in HTML.lower()


def test_no_timer_runs_a_string_and_no_attribute_runs_code_or_style():
    assert not re.search(r"set(Timeout|Interval)\(\s*[\"'`]", HTML)
    body = HTML.split("<body>", 1)[1].split("<script", 1)[0]
    assert not re.search(r"\son\w+\s*=", body, re.I) and not re.search(r"\sstyle\s*=", body, re.I)     # a hash CSP blocks both anyway


def test_the_only_addresses_are_the_api_and_links_to_github():
    urls = re.findall(r"https?://[^\s\"'<>)]*", HTML)
    csp = re.search(r'Content-Security-Policy" content="([^"]*)"', HTML).group(1)
    allowed = ("https://api.github.com", "https://github.com/")
    assert urls and all(u.startswith(allowed) for u in urls), urls
    assert "http://" not in HTML.replace("https://", "")
    assert HTML.count("fetch(") == 1 and HTML.count("Bearer") == 1                  # one gateway, the one place the token is used
    assert 'https://github.com/" + repo + "/actions/runs/" + run.id' in HTML and "if (!isRepo(repo) || !token())" in HTML     # a checked name, an integer id
    assert csp.count("https://") == 1


def test_external_links_open_without_a_window_handle():
    for tag in re.findall(r"<a\b[^>]*>", HTML):
        assert "noopener" not in tag or "target" in tag
    assert 'target: "_blank", rel: "noopener noreferrer"' in HTML


def test_the_content_security_policy_allows_one_script_one_style_and_one_host():
    csp = re.search(r'Content-Security-Policy" content="([^"]*)"', HTML).group(1)
    directives = {d.split()[0]: d.split()[1:] for d in csp.split(";") if d.strip()}
    script = re.search(r"<script>(.*?)</script>", HTML, re.S).group(1)
    style = re.search(r"<style>(.*?)</style>", HTML, re.S).group(1)
    assert directives == {"default-src": ["'none'"], "script-src": [f"'{ui_sync.sha256(script)}'"], "style-src": [f"'{ui_sync.sha256(style)}'"],
                          "connect-src": ["https://api.github.com"], "base-uri": ["'none'"], "form-action": ["'none'"]}
    assert "unsafe" not in csp
    assert len(re.findall(r"<script\b", HTML)) == 2 and len(re.findall(r"<style\b", HTML)) == 1      # the code, the data block, the style
    assert 'name="referrer" content="no-referrer"' in HTML


def test_the_token_has_one_home_and_is_cleared_when_the_page_is_left():
    assert HTML.count('id="token" type="password"') == 1 and 'autocomplete="off"' in HTML
    assert len(re.findall(r"\btoken\(\)", HTML)) >= 5
    assert 'addEventListener("pagehide", () => { $("token").value = ""; })' in HTML
    assert "credentials: \"omit\"" in HTML and "referrerPolicy: \"no-referrer\"" in HTML
    # the field is touched in three places only: read by token(), emptied by "Quên token" and emptied on pagehide; no storage, no URL
    assert HTML.count('$("token")') == 3 and "?access_token" not in HTML and "token=" not in HTML.replace("Token=", "")


def test_the_page_stays_small_enough_to_read():
    assert len(HTML.encode("utf-8")) < 60_000


def test_it_is_a_single_self_contained_file():
    assert not re.search(r"\b(src|href)=\"(?!#)", HTML.split("<body>", 1)[1].replace("</script>", "").split("<script", 1)[0])


# ---- the page's arithmetic is the same as Python's ---------------------------------------------------------------------

def _node(cases: list, schema: dict | None = None) -> list:
    """Run the page's LOGIC block under Node for each (function, args) case and return the results. `schema` overrides limits."""
    if NODE is None:
        pytest.skip("node is not installed")
    data = ui_sync.data()
    data["schema"] = {**data["schema"], **(schema or {})}
    data = json.dumps(data)
    program = f"""const DATA = {data};
{_logic()}
const fns = {{ isRepo, isBranch, merge, resolve, estimate, estimateFor, estimateRun, problems, dispatchInputs, runState, roundHalfEven, risingSlots, canon, bucketFor, newestId }};
const cases = JSON.parse(require("fs").readFileSync(0, "utf8"));
process.stdout.write(JSON.stringify(cases.map(([name, args]) => fns[name](...args))));
"""
    out = subprocess.run([NODE, "-e", program], input=json.dumps(cases), capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def _python_values(name: str) -> dict:
    cfg = _cfg()
    ids = [b["id"] for b in cfg["buckets"]]
    return conditions.resolved(conditions.apply(cfg, conditions.preset(name, ids)) if name else cfg)


def test_every_saved_preset_resolves_to_the_same_values_in_the_page_and_in_python():
    names = ["", *conditions.load_presets()]
    got = _node([["resolve", [n]] for n in names])
    for name, js in zip(names, got):
        assert js == _python_values(name), name
    assert _node([["resolve", ["nonsense"]], ["resolve", ["constructor"]]]) == [_python_values("")] * 2    # an unknown name is radar.yaml


def test_merge_follows_conditions_merge_for_every_combination():
    base = conditions.resolved(_cfg())
    tops = [{}, {"min_stars": 5}, {"rising": {"slots": 0}}, {"buckets": {"ai": ["llm"]}}, {"langs": ["en", "ja"], "rising": {"enabled": False}},
            {"picks_per_run": 9, "rising": {"created_within_days": 7, "min_stars": 1, "slots": 4, "enabled": True}}]
    got = _node([["merge", [base, t]] for t in tops])
    for top, js in zip(tops, got):
        assert js == conditions.merge(base, top), top


def test_the_estimate_prints_the_numbers_radar_py_presets_prints():
    cfg = _cfg()
    cases, expected = [], []
    ids = [b["id"] for b in cfg["buckets"]]
    for picks, langs, enabled, slots, widths in itertools.product(
            (1, 2, 3, 5, 10), (["vi"], ["vi", "en"], ["vi", "en", "ja"]), (True, False), (0, 1, 3), ((1, 1, 1, 1), (4, 4, 4, 4), (8, 5, 3, 1), (3, 0, 0, 0))):
        buckets = {i: [f"t{n}" for n in range(w)] for i, w in zip(ids, widths) if w}
        v = {"picks_per_run": picks, "min_stars": 1, "max_days_since_push": 1, "langs": langs, "buckets": buckets,
             "rising": {"enabled": enabled, "slots": slots, "created_within_days": 1, "min_stars": 1}}
        full = copy.deepcopy(cfg)
        full.update(picks_per_run=picks, langs=langs, rising=v["rising"], buckets=[{"id": i, "topics": t} for i, t in buckets.items()])
        cases.append(["estimate", [v]])
        expected.append(conditions.estimate(full))
    got = _node(cases)
    assert len(got) == 5 * 3 * 2 * 3 * 4 and got == expected


def test_half_way_values_round_to_even_like_python():
    values = [0.5, 1.5, 2.5, 10.5, 12.6, 14.7, 0.49999, 63.0, 67.2, 41.8, 100.5]
    assert _node([["roundHalfEven", [x]] for x in values]) == [round(x) for x in values]


def test_the_slots_a_scan_really_reserves_match_python():
    cfg, cases, expected = _cfg(), [], []
    for picks, enabled, slots in itertools.product(range(1, 11), (True, False), range(0, 6)):
        cases.append(["risingSlots", [{"picks_per_run": picks, "rising": {"enabled": enabled, "slots": slots}}]])
        expected.append(conditions.rising_slots({**cfg, "picks_per_run": picks, "rising": {**cfg["rising"], "enabled": enabled, "slots": slots}}))
    assert _node(cases) == expected


def _accepted_by_python(values: dict) -> bool:
    cfg = _cfg()
    try:
        clean = conditions.sanitize(conditions.parse_json(json.dumps(values), "conditions"), [b["id"] for b in cfg["buckets"]])
        config.validate(conditions.apply(cfg, clean))
    except ValueError:
        return False
    return True


def _variants() -> list:
    base = conditions.resolved(_cfg())
    out = [base]
    for key, bad in [("picks_per_run", 0), ("picks_per_run", 11), ("picks_per_run", 2.5), ("picks_per_run", "3"), ("min_stars", -1), ("min_stars", 1_000_001),
                     ("max_days_since_push", 0), ("max_days_since_push", 3651), ("langs", []), ("langs", ["vi", "ja"]),
                     ("langs", ["vi", "en", "ja"]), ("picks_per_run", 10), ("min_stars", 0), ("max_days_since_push", 3650)]:
        out.append({**base, key: bad})
    for patch in [{"slots": -1}, {"slots": 11}, {"slots": 4}, {"created_within_days": 0}, {"created_within_days": 1826}, {"min_stars": -5},
                  {"slots": 3}, {"slots": 0, "enabled": False}]:
        out.append({**base, "rising": {**base["rising"], **patch}})
    for buckets in [{}, {"ai": []}, {"ai": ["llm stars:>0"]}, {"ai": ["LLM"]}, {"ai": ["llm", "llm"]}, {"ai": [f"t{i}" for i in range(9)]},
                    {"ai": [f"t{i}" for i in range(8)]}, {"ai": ["-bad"]}, {"ai": ["x" * 51]}, {"ai": ["x" * 50]}, {"nope": ["llm"]},
                    {"ai": ["llm"], "startup": ["saas"]}, {"ai": ["a b"]}, {"ai": ["a\nb"]}]:
        out.append({**base, "buckets": buckets})
    return out


def test_the_page_refuses_exactly_what_python_refuses():
    variants = _variants()
    got = _node([["problems", [v]] for v in variants])
    for v, issues in zip(variants, got):
        # "nope" is a bucket the page never offers, so only Python can know it; every other case must agree both ways
        if "nope" in v["buckets"]:
            assert not _accepted_by_python(v)
            continue
        assert (issues == []) == _accepted_by_python(v), (v, issues)


def test_a_condition_longer_than_the_json_limit_is_refused_by_both():
    # radar.yaml's four buckets can never reach the real limit from the page, so shrink it: the check must still work if buckets are added
    base = conditions.resolved(_cfg())
    size = len(json.dumps(base, sort_keys=True, separators=(",", ":")))
    assert _node([["problems", [base]]]) == [[]]
    short = _node([["problems", [base]]], schema={"max_json_chars": size - 1})[0]
    assert len(short) == 1 and str(size - 1) in short[0]
    assert _node([["problems", [base]]], schema={"max_json_chars": size})[0] == []
    with pytest.raises(ValueError):
        conditions.parse_json(" " * (conditions.MAX_JSON_CHARS + 1), "conditions")


def test_what_the_page_sends_is_what_the_workflow_expects():
    base = conditions.resolved(_cfg())
    quick = _python_values("quet-nhanh")
    same, changed, plain, single = _node([["dispatchInputs", [quick, "quet-nhanh", True, "", ""]],
                                          ["dispatchInputs", [{**quick, "min_stars": 5000}, "quet-nhanh", False, "", ""]],
                                          ["dispatchInputs", [base, "", True, "", ""]],
                                          ["dispatchInputs", [base, "", True, "owner/name", "ai"]]])
    assert same == {"dry_run": "true", "preset": "quet-nhanh", "conditions": "", "repo": "", "bucket": ""}
    assert plain == {"dry_run": "true", "preset": "none", "conditions": "", "repo": "", "bucket": ""}
    assert single["repo"] == "owner/name" and single["bucket"] == "ai"
    assert changed["dry_run"] == "false" and all(isinstance(x, str) for x in changed.values())
    # inline conditions on top of the preset give back exactly the values on the form
    cfg = _cfg()
    ids = [b["id"] for b in cfg["buckets"]]
    overrides, label = conditions.from_env({"RADAR_PRESET": changed["preset"], "RADAR_CONDITIONS": changed["conditions"]}, ids)
    assert conditions.resolved(conditions.apply(cfg, overrides)) == {**quick, "min_stars": 5000} and label == "quet-nhanh+custom"


def test_every_input_the_page_sends_exists_in_the_workflow():
    import yaml
    inputs = yaml.safe_load((config.ROOT / ".github" / "workflows" / "radar.yml").read_text(encoding="utf-8"))[True]["workflow_dispatch"]["inputs"]
    sent = _node([["dispatchInputs", [conditions.resolved(_cfg()), "", True, "", ""]]])[0]
    assert set(sent) <= set(inputs) and all(inputs[k]["type"] in {"string", "boolean", "choice"} for k in sent)
    assert set(conditions.load_presets()) | {"none"} == set(inputs["preset"]["options"])


REPOS = [("owner/name", True), ("a/b", True), ("Github-radar/x.y_z-1", True), ("a/b/c", False), ("a", False), ("", False), ("../x", False),
         ("a/..", False), ("a/.", False), ("a b/c", False), ("a/b?x=1", False), ("a/b#x", False), ("a//b", False), ("/a/b", False), ("a/b ", False),
         ("a/\u202eb", False), ("x" * 101 + "/b", False)]


@pytest.mark.parametrize("repo,ok", REPOS)
def test_a_repository_name_is_checked_before_it_reaches_a_url(repo, ok):
    assert _node([["isRepo", [repo]]]) == [ok]


def test_run_states_are_text_and_unknown_values_are_shortened():
    states = _node([["runState", [{"status": "in_progress", "conclusion": None}]], ["runState", [{"status": "queued", "conclusion": None}]],
                    ["runState", [{"status": "completed", "conclusion": "cancelled"}]], ["runState", [{"status": "completed", "conclusion": "success"}]],
                    ["runState", [{"status": "completed", "conclusion": "<b>" + "x" * 100}]]])
    assert [s["active"] for s in states] == [True, True, False, False, False]
    assert "thay" in states[2]["text"] and len(states[4]["text"]) < 40


def test_a_single_repository_is_estimated_as_one_repository_without_a_search():
    cfg = _cfg()
    cases, expected = [], []
    for picks, langs, widths in itertools.product((1, 3, 10), (["vi"], ["vi", "en"], ["vi", "en", "ja"]), ((4, 4, 4, 4), (1, 0, 0, 0))):
        ids = [b["id"] for b in cfg["buckets"]]
        buckets = {i: [f"t{n}" for n in range(w)] for i, w in zip(ids, widths) if w}
        v = {"picks_per_run": picks, "min_stars": 1, "max_days_since_push": 1, "langs": langs, "buckets": buckets,
             "rising": {"enabled": True, "slots": 2, "created_within_days": 1, "min_stars": 1}}
        one = copy.deepcopy(cfg)
        one.update(picks_per_run=1, langs=langs, buckets=[], rising=v["rising"])
        cases.append(["estimateFor", [v, True]])
        expected.append(conditions.estimate(one))
        cases.append(["estimateFor", [v, False]])
        many = copy.deepcopy(cfg)
        many.update(picks_per_run=picks, langs=langs, buckets=[{"id": i, "topics": t} for i, t in buckets.items()], rising=v["rising"])
        expected.append(conditions.estimate(many))
    got = _node(cases)
    assert got == expected
    assert got[0]["searches"] == 0 and got[0]["model_calls"] == 2                 # one repository, one language: a writer call and a checker call


@pytest.mark.parametrize("name,ok", [("main", True), ("master", True), ("release@next", True), ("feature+plus", True), ("v1.0/hotfix_2", True),
                                     ("a" * 255, True), ("üñí", True), ("a" * 256, False), ("", False), ("main; echo pwned", False), ("a b", False),
                                     ("x..y", False), ("../../x", False), ("a@{b", False), ("@", False), ("-x", False), ("/a", False), ("a/", False),
                                     ("a//b", False), ("a/.b", False), (".a", False), ("a.", False), ("a.lock", False), ("a.lock/b", False),
                                     ("a:b", False), ("a?b", False), ("a*b", False), ("a[b", False), ("a\\b", False), ("a\x01b", False), ("a~b", False),
                                     ("a^b", False), (None, False), (5, False)])
def test_a_branch_name_follows_the_git_ref_rules_not_a_narrow_allowlist(name, ok):
    assert _node([["isBranch", [name]]]) == [ok]


def test_the_bucket_of_a_single_repository_must_be_one_the_scan_keeps():
    v = {"buckets": {"ai": ["llm"], "startup": ["saas"]}}
    got = _node([["bucketFor", [v, "owner/name", "ai"]], ["bucketFor", [v, "owner/name", "software"]], ["bucketFor", [v, "", "ai"]],
                 ["bucketFor", [v, "owner/name", ""]], ["bucketFor", [v, "owner/name", "constructor"]], ["bucketFor", [v, "owner/name", "__proto__"]]])
    assert got == ["ai", "", "", "", "", ""]


def test_the_newest_run_id_ignores_everything_that_is_not_a_run():
    assert _node([["newestId", [[]]], ["newestId", [[{"id": 3}, {"id": 9}, {"id": 5}]]], ["newestId", [[None, "x", {"id": "99"}, {"id": 1.5}, {"id": 4}, {}]]]]) == [0, 9, 4]


def test_a_dry_run_keeps_the_search_and_drops_the_model_calls_and_pauses():
    cfg = _cfg()
    v = conditions.resolved(cfg)
    full, dry, one_dry, one_real = _node([["estimateRun", [v, False, False]], ["estimateRun", [v, False, True]],
                                          ["estimateRun", [v, True, True]], ["estimateRun", [v, True, False]]])
    assert full == conditions.estimate(cfg) and full["model_calls"] > 0 and full["pace_seconds"] > 0
    assert dry == {**full, "model_calls": 0, "pace_seconds": 0} and dry["searches"] == full["searches"] > 0
    assert one_dry["searches"] == 0 and one_dry["model_calls"] == 0 and one_dry["pace_seconds"] == 0
    assert one_real["searches"] == 0 and one_real["model_calls"] == 2
