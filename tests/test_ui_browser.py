"""docs/ui/index.html in a real browser (Chromium through Playwright), with api.github.com answered by the test.

Skipped when Playwright or a browser is missing (CI installs neither): tests/test_ui.py is what always runs. These prove the
behaviour no source check can: that the token goes only where it should, what is sent, and that text from GitHub stays text."""

import datetime as dt
import json
import os
import re
import time
from pathlib import Path

import pytest

from radar import conditions, config
from scripts import ui_sync

sync_api = pytest.importorskip("playwright.sync_api")

PAGE_URL = ui_sync.PAGE.as_uri()
TOKEN = "github_pat_TESTONLY_not_a_real_token_0123456789"
REPO = "vohoailinh90/Github-radar"
CORS = {"access-control-allow-origin": "*", "access-control-allow-headers": "authorization, content-type, accept",
        "access-control-allow-methods": "GET, POST, OPTIONS"}


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as pw:
        try:
            exe = os.environ.get("RADAR_CHROMIUM") or None
            b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
        except Exception as exc:                                       # no browser installed in this environment
            pytest.skip(f"Chromium is not available: {str(exc)[:80]}")
        yield b
        b.close()


class Github:
    """api.github.com as the test wants it: records every request, answers from `routes` ({(method, path-prefix): (status, body)})."""

    def __init__(self):
        self.requests: list[dict] = []
        self.routes: dict = {
            ("GET", f"/repos/{REPO}"): (200, {"default_branch": "main"}),
            ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs"): (200, {"workflow_runs": []}),
            ("GET", f"/repos/{REPO}/actions/workflows/radar.yml"): (200, {"id": 1}),
            ("POST", f"/repos/{REPO}/actions/workflows/radar.yml/dispatches"): (204, None),
        }

    def handle(self, route, request):
        if request.method == "OPTIONS":
            return route.fulfill(status=204, headers=CORS)
        path = request.url.split("https://api.github.com", 1)[1]
        clean = path.split("?", 1)[0]
        self.requests.append({"method": request.method, "path": path, "headers": request.headers,
                              "body": json.loads(request.post_data) if request.post_data else None})
        for (method, prefix), (status, body) in sorted(self.routes.items(), key=lambda kv: -len(kv[0][1])):
            if method == request.method and clean == prefix:
                return route.fulfill(status=status, headers=CORS, content_type="application/json", body=json.dumps(body) if body is not None else "")
        return route.fulfill(status=404, headers=CORS, content_type="application/json", body='{"message":"Not Found"}')

    def posts(self) -> list:
        return [r for r in self.requests if r["method"] == "POST"]


@pytest.fixture
def ui(browser):
    context = browser.new_context()
    gh = Github()
    page = context.new_page()
    seen_requests, problems = [], []
    context.route("https://api.github.com/**", gh.handle)
    page.on("request", lambda r: seen_requests.append(r.url))
    page.on("pageerror", lambda e: problems.append(str(e)))
    page.on("console", lambda m: problems.append(m.text) if m.type in ("error", "warning") else None)
    page.goto(PAGE_URL)
    page.gh, page.seen, page.problems = gh, seen_requests, problems
    yield page
    context.close()


def connect(page, token=TOKEN):
    page.fill("#token", token)
    page.click("#check")
    wait(page, "document.getElementById('connect-msg').className.includes('ok')")


def wait(page, expression, seconds=8):
    """Wait until a JavaScript expression is true. Playwright's own wait_for_function evals a string, which the page's CSP (no
    unsafe-eval, on purpose) refuses; evaluate() goes through the debugging protocol instead."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if page.evaluate(f"() => Boolean({expression})"):
            return
        time.sleep(0.05)
    raise AssertionError(f"still false after {seconds}s: {expression}")


def text(page, selector):
    return page.inner_text(selector)


def test_the_page_loads_clean_with_the_saved_presets_and_the_base_configuration(ui):
    assert ui.problems == []                                                       # no CSP violation, no script error
    assert ui.title() == "GitHub Radar: quét theo yêu cầu"
    names = ui.eval_on_selector_all("#preset option", "els => els.map(e => e.value)")
    assert names == ["none", *conditions.load_presets()]
    base = conditions.resolved(config.load(path=config.ROOT / "radar.yaml", env={}))
    assert ui.input_value("#picks") == str(base["picks_per_run"]) and ui.input_value("#min_stars") == str(base["min_stars"])
    assert ui.is_checked("#lang-vi") and not ui.is_checked("#lang-en")
    assert ui.is_checked("#dry") and ui.is_hidden("#confirm-box") and ui.is_disabled("#go")      # nothing runs before a token
    assert "Ước tính: ít nhất" in text(ui, "#estimate")
    assert [r for r in ui.seen if not r.startswith("file://")] == []             # opening the page contacts nobody


def test_choosing_a_preset_fills_the_form_with_what_python_resolves(ui):
    cfg = config.load(path=config.ROOT / "radar.yaml", env={})
    ids = [b["id"] for b in cfg["buckets"]]
    for name in conditions.load_presets():
        ui.select_option("#preset", name)
        want = conditions.resolved(conditions.apply(cfg, conditions.preset(name, ids)))
        assert ui.input_value("#picks") == str(want["picks_per_run"])
        assert ui.is_checked("#rising-enabled") == want["rising"]["enabled"]
        assert ui.input_value("#rising-slots") == str(want["rising"]["slots"])
        for bid in ids:
            assert ui.is_checked(f"#bucket-{bid}") == (bid in want["buckets"])
        assert json.loads(ui.input_value("#json")) == want


def test_a_dry_run_sends_exactly_the_documented_dispatch(ui):
    connect(ui)
    ui.select_option("#preset", "quet-nhanh")
    assert text(ui, "#go") == "Quét thử" and ui.is_enabled("#go")
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    post, = ui.gh.posts()
    assert post["path"] == f"/repos/{REPO}/actions/workflows/radar.yml/dispatches"
    assert post["body"] == {"ref": "main", "inputs": {"dry_run": "true", "preset": "quet-nhanh", "conditions": "", "repo": "", "bucket": ""}}
    assert post["headers"]["authorization"] == f"Bearer {TOKEN}"
    assert post["headers"]["accept"] == "application/vnd.github+json"


def test_a_changed_value_goes_as_conditions_and_python_resolves_it_to_the_form(ui):
    connect(ui)
    ui.select_option("#preset", "quet-nhanh")
    ui.fill("#min_stars", "5000")
    ui.uncheck("#dry")
    ui.fill("#confirm", "QUET")
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('quét thật')")
    inputs = ui.gh.posts()[0]["body"]["inputs"]
    assert inputs["dry_run"] == "false" and inputs["preset"] == "quet-nhanh" and all(isinstance(v, str) for v in inputs.values())
    cfg = config.load(path=config.ROOT / "radar.yaml", env={})
    overrides, label = conditions.from_env({"RADAR_PRESET": inputs["preset"], "RADAR_CONDITIONS": inputs["conditions"]}, [b["id"] for b in cfg["buckets"]])
    assert conditions.resolved(conditions.apply(cfg, overrides)) == json.loads(ui.input_value("#json")) and label == "quet-nhanh+custom"
    assert ui.input_value("#confirm") == ""                                       # a second real scan needs a fresh confirmation


def test_a_real_scan_needs_the_word_typed_exactly(ui):
    connect(ui)
    ui.uncheck("#dry")
    assert ui.is_visible("#confirm-box") and ui.is_disabled("#go") and text(ui, "#go") == "Quét thật"
    for wrong in ("quet", "QUÉT", "QUET ", "QUE", "yes"):
        ui.fill("#confirm", wrong)
        assert ui.is_disabled("#go"), repr(wrong)                                  # exact match only: not "QUET " either
    ui.fill("#confirm", "QUET")
    assert ui.is_enabled("#go")
    ui.check("#dry")                                                              # back to a dry run hides the box, button works without it
    assert ui.is_hidden("#confirm-box") and ui.is_enabled("#go")


def test_the_token_is_kept_nowhere_but_the_field(ui):
    connect(ui)
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    stores = ui.evaluate("""() => ({ local: Object.keys(window.localStorage), session: Object.keys(window.sessionStorage),
                                     cookie: document.cookie, dbs: indexedDB.databases ? null : null })""")
    assert stores["local"] == [] and stores["session"] == [] and stores["cookie"] == ""
    assert ui.context.cookies() == []
    assert all(TOKEN not in url for url in ui.seen)                               # never in a URL
    assert all(TOKEN not in (r["body"] and json.dumps(r["body"]) or "") for r in ui.gh.requests)
    assert all(r["headers"].get("authorization") == f"Bearer {TOKEN}" for r in ui.gh.requests)
    assert all(r.startswith(("file://", "https://api.github.com/")) for r in ui.seen), ui.seen
    assert TOKEN not in ui.content().replace(f'value="{TOKEN}"', "")             # not written into the markup
    assert TOKEN not in text(ui, "body")
    ui.click("#forget")
    assert ui.input_value("#token") == "" and ui.is_disabled("#go")
    ui.reload()
    assert ui.input_value("#token") == ""


def test_leaving_the_page_empties_the_field(browser):
    context = browser.new_context()
    context.route("https://api.github.com/**", Github().handle)
    page = context.new_page()
    page.goto(PAGE_URL)
    page.fill("#token", TOKEN)
    page.evaluate("window.dispatchEvent(new Event('pagehide'))")
    assert page.input_value("#token") == ""
    context.close()


@pytest.mark.parametrize("repo", ["a/b/c", "../x", "owner", "a b/c", "a/b?x=1", "", "a/.."])
def test_a_bad_repository_name_blocks_every_request(ui, repo):
    ui.fill("#token", TOKEN)
    ui.fill("#repo", repo)
    assert ui.is_disabled("#go")
    ui.click("#check")
    assert "chủ/tên" in text(ui, "#connect-msg")
    ui.evaluate("document.getElementById('go').disabled = false; document.getElementById('go').click()")      # even if the button were forced
    ui.wait_for_timeout(400)                                                       # a request would be sent within this time
    assert ui.gh.requests == []


def test_without_a_token_nothing_is_sent(ui):
    assert ui.is_disabled("#go")
    ui.evaluate("document.getElementById('go').disabled = false; document.getElementById('go').click()")
    ui.click("#check")
    ui.click("#refresh")
    ui.wait_for_timeout(400)
    assert ui.gh.requests == []


def test_changing_the_repository_forgets_the_branch_found_for_the_old_one(ui):
    connect(ui)
    other = "someone/else-radar"
    ui.gh.routes[("GET", f"/repos/{other}")] = (200, {"default_branch": "trunk"})
    ui.gh.routes[("POST", f"/repos/{other}/actions/workflows/radar.yml/dispatches")] = (204, None)
    ui.gh.routes[("GET", f"/repos/{other}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": []})
    ui.fill("#repo", other)
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert ui.gh.posts()[0]["body"]["ref"] == "trunk" and ui.gh.posts()[0]["path"].startswith(f"/repos/{other}/")


def test_a_hostile_default_branch_is_refused(ui):
    ui.gh.routes[("GET", f"/repos/{REPO}")] = (200, {"default_branch": "main; echo pwned"})
    ui.fill("#token", TOKEN)
    ui.click("#check")
    wait(ui, "document.getElementById('connect-msg').className.includes('bad')")
    ui.click("#go")
    assert ui.gh.posts() == [] and "không trả nhánh" in text(ui, "#connect-msg")


def test_sending_without_checking_first_looks_up_the_branch_and_refuses_a_hostile_one(ui):
    ui.fill("#token", TOKEN)
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert [r["path"] for r in ui.gh.requests][:2] == [f"/repos/{REPO}", f"/repos/{REPO}/actions/workflows/radar.yml/dispatches"]
    assert ui.gh.posts()[0]["body"]["ref"] == "main"
    ui.reload()
    ui.gh.requests.clear()
    ui.gh.routes[("GET", f"/repos/{REPO}")] = (200, {"default_branch": "../../x"})
    ui.fill("#token", TOKEN)
    ui.click("#go")
    wait(ui, "document.getElementById('msg').className.includes('bad')")
    assert ui.gh.posts() == []


@pytest.mark.parametrize("status,words", [(401, "Token sai"), (403, "không đủ quyền"), (404, "Không thấy repo"), (500, "mã 500")])
def test_a_refused_token_gets_a_plain_explanation(ui, status, words):
    ui.gh.routes[("GET", f"/repos/{REPO}")] = (status, {"message": "x"})
    ui.fill("#token", TOKEN)
    ui.click("#check")
    wait(ui, "document.getElementById('connect-msg').className.includes('bad')")
    assert words in text(ui, "#connect-msg")


def test_text_from_github_stays_text(ui):
    hostile = "<img src=x onerror=\"document.title='pwned'\"><b>bold</b>"
    ui.gh.routes[("POST", f"/repos/{REPO}/actions/workflows/radar.yml/dispatches")] = (422, {"message": hostile})
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 111, "status": "completed", "conclusion": "cancelled", "created_at": "2026-10-10T01:00:00Z"},
        {"id": 222, "status": "completed", "conclusion": hostile, "created_at": "not a date"},
        {"id": "333; evil", "status": "completed", "conclusion": "success", "created_at": now},
        {"id": 444, "status": hostile, "created_at": now},
        None, "text", {"id": 555}]})
    connect(ui)
    ui.click("#go")
    wait(ui, "document.getElementById('msg').className.includes('bad')")
    assert hostile[:30] in text(ui, "#msg") or "GitHub từ chối" in text(ui, "#msg")
    assert ui.query_selector("img") is None and ui.query_selector("#msg b") is None and ui.title() != "pwned"
    ui.click("#refresh")
    ui.wait_for_selector("#runs-body tr")
    rows = ui.eval_on_selector_all("#runs-body tr", "trs => trs.map(t => [...t.children].map(c => c.textContent))")
    assert len(rows) == 3                                                          # the two malformed runs and the non-objects are skipped
    assert "Đã hủy" in rows[0][1] and "thay bằng một yêu cầu mới hơn" in rows[0][1]
    assert rows[1][0] == "?" and "Kết thúc" in rows[1][1] and len(rows[1][1]) < 60
    assert ui.query_selector("#runs-body b") is None and ui.query_selector("#runs-body img") is None
    links = ui.eval_on_selector_all("#runs-body a", "as => as.map(a => [a.href, a.rel, a.target])")
    assert links[0] == [f"https://github.com/{REPO}/actions/runs/111", "noopener noreferrer", "_blank"]
    assert all(re.fullmatch(rf"https://github.com/{REPO}/actions/runs/\d+", href) for href, _, _ in links)


def test_a_run_just_sent_blocks_a_second_send_until_it_finishes(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 9, "status": "in_progress", "conclusion": None, "created_at": now}]})
    ui.click("#go")
    wait(ui, "document.getElementById('runs-body').children.length === 1")
    assert "lượt bạn vừa gửi" in text(ui, "#runs-body") and "Đang chạy" in text(ui, "#runs-body")
    assert ui.is_disabled("#go")
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 9, "status": "completed", "conclusion": "success", "created_at": now}]})
    ui.click("#refresh")
    wait(ui, "document.getElementById('go').disabled === false")
    assert "Xong" in text(ui, "#runs-body")


def test_forgetting_the_token_frees_the_button_a_run_of_mine_was_holding(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    ui.gh.routes[runs] = (200, {"workflow_runs": [{"id": 9, "status": "in_progress", "conclusion": None, "created_at": now}]})
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    ui.gh.routes[runs] = (200, {"workflow_runs": []})
    ui.click("#forget")
    ui.fill("#token", TOKEN)
    assert ui.is_enabled("#go")                                                    # nothing of the old session is still waiting


def test_a_failed_run_list_does_not_leave_the_button_off(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    ui.gh.routes[runs] = (200, {"workflow_runs": [{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]})
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    ui.gh.routes[runs] = (500, {"message": "x"})
    ui.click("#refresh")
    wait(ui, "document.getElementById('msg').className.includes('bad')")
    assert ui.is_enabled("#go")


def test_run_links_point_at_the_repository_the_list_was_asked_for(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    ui.gh.routes[runs] = (200, {"workflow_runs": [{"id": 5, "status": "completed", "conclusion": "success", "created_at": now}]})
    original = ui.gh.handle

    def edit_the_field_meanwhile(route, request):
        if request.url.endswith("/runs?event=workflow_dispatch&per_page=10"):
            ui.evaluate("document.getElementById('repo').value = 'attacker/other'")          # typed while the request is in flight
        return original(route, request)
    ui.context.unroute("https://api.github.com/**")
    ui.context.route("https://api.github.com/**", edit_the_field_meanwhile)
    ui.click("#refresh")
    ui.wait_for_selector("#runs-body a")
    assert ui.eval_on_selector("#runs-body a", "a => a.href") == f"https://github.com/{REPO}/actions/runs/5"


def test_a_send_uses_the_fields_as_they_were_when_it_was_asked_for(ui):
    ui.fill("#token", TOKEN)
    ui.fill("#single", "owner/name")
    ui.select_option("#single-bucket", "ai")
    original = ui.gh.handle

    def edit_the_fields_meanwhile(route, request):
        if request.method == "GET" and request.url.endswith(f"/repos/{REPO}"):
            ui.evaluate("""() => { document.getElementById('repo').value = 'attacker/other'; document.getElementById('single').value = 'not a repo';
                                   document.getElementById('single-bucket').value = 'startup'; }""")
        return original(route, request)
    ui.context.unroute("https://api.github.com/**")
    ui.context.route("https://api.github.com/**", edit_the_fields_meanwhile)
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    post, = ui.gh.posts()
    assert post["path"] == f"/repos/{REPO}/actions/workflows/radar.yml/dispatches" and post["body"]["ref"] == "main"
    assert post["body"]["inputs"]["repo"] == "owner/name" and post["body"]["inputs"]["bucket"] == "ai"


def test_a_branch_read_for_one_repository_is_not_used_for_another_that_was_typed_meanwhile(ui):
    ui.fill("#token", TOKEN)
    other = "someone/else-radar"
    ui.gh.routes[("GET", f"/repos/{other}")] = (200, {"default_branch": "trunk"})
    ui.gh.routes[("POST", f"/repos/{other}/actions/workflows/radar.yml/dispatches")] = (204, None)
    ui.gh.routes[("GET", f"/repos/{other}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": []})
    original = ui.gh.handle

    def edit_the_field_meanwhile(route, request):
        if request.url.endswith("/actions/workflows/radar.yml"):
            ui.evaluate(f"document.getElementById('repo').value = '{other}'")
        return original(route, request)
    ui.context.unroute("https://api.github.com/**")
    ui.context.route("https://api.github.com/**", edit_the_field_meanwhile)
    ui.click("#check")
    wait(ui, "document.getElementById('connect-msg').className.includes('warn')")
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert ui.gh.posts()[0]["body"]["ref"] == "trunk" and ui.gh.posts()[0]["path"].startswith(f"/repos/{other}/")


def test_a_real_scan_without_the_word_sends_nothing_even_if_the_button_is_forced(ui):
    connect(ui)
    ui.uncheck("#dry")
    ui.evaluate("document.getElementById('go').disabled = false; document.getElementById('go').click()")
    ui.wait_for_timeout(400)
    assert ui.gh.posts() == []
    ui.fill("#confirm", "quet")
    ui.evaluate("document.getElementById('go').disabled = false; document.getElementById('go').click()")
    ui.wait_for_timeout(400)
    assert ui.gh.posts() == []


def test_a_bad_single_repository_sends_nothing_even_if_the_button_is_forced(ui):
    connect(ui)
    ui.fill("#single", "not a repo")
    ui.gh.requests.clear()
    ui.evaluate("document.getElementById('go').disabled = false; document.getElementById('go').click()")
    ui.wait_for_timeout(400)
    assert ui.gh.requests == []


def test_a_bucket_is_not_sent_without_a_single_repository(ui):
    connect(ui)
    ui.select_option("#single-bucket", "startup")
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert ui.gh.posts()[0]["body"]["inputs"]["bucket"] == "" and ui.gh.posts()[0]["body"]["inputs"]["repo"] == ""


def test_the_token_check_says_only_what_it_checked(ui):
    connect(ui)
    message = text(ui, "#connect-msg")
    assert "đọc được" in message and "Quyền ghi Actions chưa kiểm được" in message and "dùng được" not in message


def test_the_button_stays_off_until_the_run_just_sent_is_listed(ui):
    connect(ui)
    ui.click("#go")                                                                # accepted (204), but the run list is still empty
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert ui.is_disabled("#go")
    ui.evaluate("document.getElementById('go').disabled = false; document.getElementById('go').click()")      # a forced second send
    ui.wait_for_timeout(400)
    assert len(ui.gh.posts()) == 1
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 7, "status": "completed", "conclusion": "success", "created_at": now}]})
    ui.click("#refresh")                                                           # listed, and already finished
    wait(ui, "document.getElementById('go').disabled === false")


def test_the_wait_for_a_run_that_never_shows_up_ends_after_two_minutes(browser):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    page = context.new_page()
    page.clock.install(time=dt.datetime.now(dt.timezone.utc))
    page.goto(PAGE_URL)
    connect(page)
    page.click("#go")
    wait(page, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert page.is_disabled("#go")
    page.clock.fast_forward(60_000)
    page.click("#refresh")
    assert page.is_disabled("#go")                                                 # a minute in: still waiting
    page.clock.fast_forward(70_000)
    page.click("#refresh")
    wait(page, "document.getElementById('go').disabled === false")
    context.close()


def test_a_dispatch_that_was_refused_does_not_start_a_wait(ui):
    connect(ui)
    ui.gh.routes[("POST", f"/repos/{REPO}/actions/workflows/radar.yml/dispatches")] = (422, {"message": "nope"})
    ui.click("#go")
    wait(ui, "document.getElementById('msg').className.includes('bad')")
    assert ui.is_enabled("#go")


def test_a_dispatch_the_server_does_not_acknowledge_is_not_reported_as_sent(ui):
    connect(ui)
    ui.gh.routes[("POST", f"/repos/{REPO}/actions/workflows/radar.yml/dispatches")] = (200, {})
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent !== 'Đang gửi lệnh…'")
    assert "Đã gửi" not in text(ui, "#msg")


def test_a_topic_that_would_change_the_search_is_caught_before_sending(ui):
    ui.fill("#topics-ai", "llm stars:>0, rag")
    assert "không phải topic GitHub" in text(ui, "#problems") and ui.is_disabled("#go") and ui.input_value("#json") == ""
    ui.fill("#topics-ai", "llm, rag")
    assert text(ui, "#problems") == ""
    for bid in ("ai", "software", "solutions", "startup"):
        ui.uncheck(f"#bucket-{bid}")
    assert "ít nhất một nhóm" in text(ui, "#problems")


def test_a_single_repository_goes_with_its_bucket(ui):
    connect(ui)
    ui.fill("#single", "owner/name")
    ui.select_option("#single-bucket", "ai")
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    inputs = ui.gh.posts()[0]["body"]["inputs"]
    assert inputs["repo"] == "owner/name" and inputs["bucket"] == "ai"
    ui.fill("#single", "not a repo")
    assert ui.is_disabled("#go") and "chủ/tên" in text(ui, "#problems")


def test_the_page_refuses_to_run_inside_a_frame(browser, tmp_path):
    outer = Path(tmp_path) / "outer.html"
    outer.write_text(f'<!doctype html><iframe id="f" src="{PAGE_URL}" width="600" height="400"></iframe>', encoding="utf-8")
    context = browser.new_context()
    page = context.new_page()
    page.goto(outer.as_uri())
    frame = page.frame_locator("#f")
    page.wait_for_timeout(300)
    assert "không chạy trong khung nhúng" in frame.locator("html").inner_text()
    assert frame.locator("#go").count() == 0
    context.close()


def test_the_content_security_policy_really_blocks_injected_script(ui):
    ui.evaluate("""() => { const s = document.createElement('script'); s.textContent = 'window.__ran = 1'; document.body.append(s); }""")
    assert ui.evaluate("window.__ran") is None                                   # the hash allows our script and nothing else
    ui.evaluate("() => { fetch('https://example.com/x').catch(() => { window.__blocked = true; }); }")
    wait(ui, "window.__blocked === true")
    assert not [u for u in ui.seen if "example.com" in u]
