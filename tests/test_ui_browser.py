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
                if callable(body):                                           # an answer that depends on what happened so far
                    status, body = body()
                if status == "abort":                                        # the connection drops: the browser gets no answer at all
                    self.requests[-1]["aborted"] = True
                    return route.abort("connectionreset")
                return route.fulfill(status=status, headers=CORS, content_type="application/json", body=json.dumps(body) if body is not None else "")
        return route.fulfill(status=404, headers=CORS, content_type="application/json", body='{"message":"Not Found"}')

    def runs_after_dispatch(self, runs: list):
        """The run list as GitHub gives it: the new run appears only once a dispatch was accepted (its id is larger than any listed before)."""
        return lambda: (200, {"workflow_runs": runs if self.posts() else []})

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


def runs_requests(gh) -> int:
    return len([r for r in gh.requests if r["method"] == "GET" and "/radar.yml/runs" in r["path"]])


def settle(page, looks, seconds=8):
    """Under a fake clock: wait until `looks` run-list requests were made, then give the page a moment to take the last answer and set its next
    timer (it does both in one task). A clock jump before that would find no timer to fire. (wait_for_timeout, not time.sleep: only a call into
    Playwright lets the route handlers run.)"""
    deadline = time.monotonic() + seconds
    while runs_requests(page.gh) < looks and time.monotonic() < deadline:
        page.wait_for_timeout(50)
    assert runs_requests(page.gh) >= looks
    page.wait_for_timeout(300)


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
    assert json.loads(inputs["conditions"]) == {"min_stars": 5000}                 # the one field changed, nothing of the page's snapshot
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
    assert [r["path"].split("?")[0] for r in ui.gh.requests][:3] == [f"/repos/{REPO}", f"/repos/{REPO}/actions/workflows/radar.yml/runs",
                                                                       f"/repos/{REPO}/actions/workflows/radar.yml/dispatches"]      # branch, runs before, send
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
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (
        200, ui.gh.runs_after_dispatch([{"id": 9, "status": "in_progress", "conclusion": None, "created_at": now}]))
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
    ui.gh.routes[runs] = (200, ui.gh.runs_after_dispatch([{"id": 9, "status": "in_progress", "conclusion": None, "created_at": now}]))
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    ui.gh.routes[runs] = (200, {"workflow_runs": []})
    ui.click("#forget")
    ui.fill("#token", TOKEN)
    assert ui.is_enabled("#go")                                                    # nothing of the old session is still waiting


def test_a_failed_run_list_keeps_the_lock_of_a_run_last_seen_active_until_a_good_answer_says_it_ended(browser):
    context, page = _with_a_fake_clock(browser)
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    connect(page)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    page.gh.routes[runs] = (200, page.gh.runs_after_dispatch([{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]))
    page.click("#go")
    wait(page, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    seen = runs_requests(page.gh)
    page.gh.routes[runs] = (500, {"message": "x"})
    page.clock.fast_forward(10_000)
    wait(page, "document.getElementById('msg').className.includes('bad')")
    settle(page, seen + 1)
    assert page.is_disabled("#go")                                                 # not knowing is not "finished"
    page.clock.fast_forward(200_000)                                               # even far beyond the discovery wait: the run was seen active
    settle(page, seen + 2)
    assert page.is_disabled("#go")
    page.gh.routes[runs] = (200, {"workflow_runs": [{"id": 9, "status": "completed", "conclusion": "success", "created_at": now}]})
    page.clock.fast_forward(10_000)                                                # it kept looking, and now a good answer says it ended
    wait(page, "document.getElementById('go').disabled === false")
    context.close()


def test_forgetting_the_token_frees_a_lock_held_by_a_run_that_cannot_be_looked_up(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    ui.gh.routes[runs] = (200, ui.gh.runs_after_dispatch([{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]))
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    ui.gh.routes[runs] = (500, {"message": "x"})
    ui.click("#refresh")
    wait(ui, "document.getElementById('msg').className.includes('bad')")
    assert ui.is_disabled("#go")
    ui.click("#forget")
    ui.fill("#token", TOKEN)
    assert ui.is_enabled("#go")


@pytest.mark.parametrize("answer", [("abort", None), (502, {"message": "bad gateway"}), (504, None)])
def test_a_send_whose_answer_is_lost_may_have_started_a_run_so_it_is_not_repeated_at_once(ui, answer):
    connect(ui)
    ui.gh.routes[("POST", f"/repos/{REPO}/actions/workflows/radar.yml/dispatches")] = answer
    ui.click("#go")
    wait(ui, "document.getElementById('msg').className.includes('warn')")
    assert "chưa biết lệnh đã tới GitHub chưa" in text(ui, "#msg") and ui.is_disabled("#go")
    ui.evaluate("document.getElementById('go').disabled = false; document.getElementById('go').click()")
    ui.wait_for_timeout(400)
    assert len(ui.gh.posts()) == 1                                                 # a forced second send is refused too
    ui.click("#refresh")                                                           # nothing listed yet: the page puts the lock back (it was forced open above)
    wait(ui, "document.getElementById('go').disabled === true")
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 31, "status": "completed", "conclusion": "success", "created_at": now}]})
    ui.click("#refresh")                                                           # the run did start: found by its id, finished, the lock ends
    wait(ui, "document.getElementById('runs-body').children.length === 1 && document.getElementById('go').disabled === false")
    assert "lượt bạn vừa gửi" in text(ui, "#runs-body")


def test_a_real_scan_whose_answer_was_lost_needs_the_word_typed_again(ui):
    connect(ui)
    ui.uncheck("#dry")
    ui.fill("#confirm", "QUET")
    ui.gh.routes[("POST", f"/repos/{REPO}/actions/workflows/radar.yml/dispatches")] = ("abort", None)
    ui.click("#go")
    wait(ui, "document.getElementById('msg').className.includes('warn')")
    assert ui.input_value("#confirm") == ""


def test_a_lost_answer_that_never_produces_a_run_ends_after_the_wait(browser):
    context, page = _with_a_fake_clock(browser)
    connect(page)
    page.gh.routes[("POST", f"/repos/{REPO}/actions/workflows/radar.yml/dispatches")] = ("abort", None)
    page.click("#go")
    wait(page, "document.getElementById('msg').className.includes('warn')")
    settle(page, 2)
    assert page.is_disabled("#go")
    page.clock.fast_forward(125_000)
    wait(page, "document.getElementById('go').disabled === false")
    context.close()


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
    context, page = _with_a_fake_clock(browser)
    connect(page)
    page.click("#go")
    wait(page, "document.getElementById('msg').textContent.includes('Đã gửi')")
    settle(page, 2)
    assert page.is_disabled("#go")
    page.clock.fast_forward(60_000)
    page.click("#refresh")
    settle(page, 3)
    assert page.is_disabled("#go")                                                 # a minute in: still waiting
    page.clock.fast_forward(70_000)
    page.click("#refresh")
    wait(page, "document.getElementById('go').disabled === false")
    context.close()


def _with_a_fake_clock(browser, hold=False):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    if hold:
        context.add_init_script(HOLD)
    page = context.new_page()
    page.clock.install(time=dt.datetime.now(dt.timezone.utc))
    page.goto(PAGE_URL)
    page.gh = gh
    return context, page


def test_a_failed_answer_while_waiting_for_the_run_does_not_stop_the_looking(browser):
    context, page = _with_a_fake_clock(browser)
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    connect(page)
    page.click("#go")
    wait(page, "document.getElementById('msg').textContent.includes('Đã gửi')")
    settle(page, 2)                                                             # the list read before the send, and the first look after it
    assert page.is_disabled("#go")
    page.gh.routes[runs] = (500, {"message": "busy"})
    page.clock.fast_forward(10_000)                                                # the next look fails ...
    wait(page, "document.getElementById('msg').className.includes('bad')")
    settle(page, 3)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    page.gh.routes[runs] = (200, {"workflow_runs": [{"id": 77, "status": "completed", "conclusion": "success", "created_at": now}]})
    page.clock.fast_forward(10_000)                                                # ... and the one after it still happens
    wait(page, "document.getElementById('runs-body').children.length === 1")
    wait(page, "document.getElementById('go').disabled === false")
    assert "lượt bạn vừa gửi" in text(page, "#runs-body")
    context.close()


def test_the_lock_of_a_run_survives_looking_at_another_repository_and_coming_back(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    ui.gh.routes[runs] = (200, ui.gh.runs_after_dispatch([{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]))
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    ui.fill("#repo", "someone/else")                                               # a different repository has nothing of mine in flight
    assert ui.is_enabled("#go")
    ui.fill("#repo", REPO)                                                         # back: the run sent here is still queued
    assert ui.is_disabled("#go")
    ui.fill("#repo", "someone/else")
    ui.gh.routes[runs] = (200, {"workflow_runs": [{"id": 9, "status": "completed", "conclusion": "success", "created_at": now}]})
    ui.fill("#repo", REPO)                                                         # back again after it finished: found out without a click
    wait(ui, "document.getElementById('go').disabled === false")
    assert "Xong" in text(ui, "#runs-body")


def test_a_send_to_a_second_repository_does_not_forget_the_first_ones_run(ui):
    connect(ui)
    other = "someone/else"
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (
        200, ui.gh.runs_after_dispatch([{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]))
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    posts_here = len(ui.gh.posts())
    ui.gh.routes[("GET", f"/repos/{other}")] = (200, {"default_branch": "main"})
    ui.gh.routes[("GET", f"/repos/{other}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": []})
    ui.gh.routes[("POST", f"/repos/{other}/actions/workflows/radar.yml/dispatches")] = (204, None)
    ui.fill("#repo", other)
    ui.click("#go")                                                                # a send to the other repository: allowed, it has nothing in flight
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert len(ui.gh.posts()) == posts_here + 1
    ui.fill("#repo", REPO)
    assert ui.is_disabled("#go")                                                   # the first repository's run is still known to be queued


def test_the_same_repository_in_another_spelling_is_the_same_repository(ui):
    connect(ui)
    shouting = REPO.upper()                                                        # GitHub reads owner and name without regard to case
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ui.gh.routes[("GET", f"/repos/{shouting}")] = (200, {"default_branch": "main"})
    ui.gh.routes[("POST", f"/repos/{shouting}/actions/workflows/radar.yml/dispatches")] = (204, None)
    for spelling in (shouting, REPO, REPO.title()):                                # one repository: whatever the spelling, the same answer
        ui.gh.routes[("GET", f"/repos/{spelling}/actions/workflows/radar.yml/runs")] = (
            200, ui.gh.runs_after_dispatch([{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]))
    ui.fill("#repo", shouting)
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    ui.fill("#repo", REPO)                                                         # the same repository, written differently
    assert ui.is_disabled("#go")
    ui.fill("#repo", REPO.title())
    assert ui.is_disabled("#go")


def test_a_returning_repository_stays_locked_until_its_reload_has_succeeded_even_after_the_wait_ran_out(browser):
    context, page = _with_a_fake_clock(browser, hold=True)
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    connect(page)
    page.click("#go")
    wait(page, "document.getElementById('msg').textContent.includes('Đã gửi')")
    settle(page, 2)                                                                # accepted, nothing listed yet
    page.fill("#repo", "someone/else")                                             # leaving: the looking for this send stops
    page.clock.fast_forward(130_000)                                               # more than the two-minute wait passes unobserved
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    page.gh.routes[runs] = (200, {"workflow_runs": [{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]})
    page.evaluate("window.__hold = true")
    page.fill("#repo", REPO)                                                       # back: the reload starts but its answer is held
    wait(page, "window.__held.length === 1")
    assert page.is_disabled("#go")                                                 # not yet looked at: the run may well be there
    page.evaluate("window.__release()")
    wait(page, "document.getElementById('runs-body').children.length === 1")
    assert page.is_disabled("#go") and "Đang chờ" in text(page, "#runs-body")      # it was: still queued
    context.close()


def test_runs_of_another_repository_are_never_taken_for_mine(ui):
    connect(ui)
    other = "someone/else"
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (
        200, ui.gh.runs_after_dispatch([{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]))
    ui.gh.routes[("GET", f"/repos/{other}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 500, "status": "completed", "conclusion": "success", "created_at": now}]})
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    ui.fill("#repo", other)
    ui.click("#refresh")
    wait(ui, "document.getElementById('runs-body').textContent.includes('Xong')")
    assert "lượt bạn vừa gửi" not in text(ui, "#runs-body")                       # a larger id in another repository proves nothing about mine
    ui.fill("#repo", REPO)
    assert ui.is_disabled("#go")                                                   # and it did not mark my run as finished either


HOLD = """(() => { const real = window.fetch; window.__held = []; window.__hold = false; window.__holdPost = false;
  window.fetch = async (...args) => { const res = await real(...args); const url = String(args[0]);
    if ((window.__hold && url.includes('/runs?')) || (window.__holdPost && url.includes('/dispatches'))) {
      window.__hold = false; window.__holdPost = false; await new Promise((r) => window.__held.push(r));
      if (window.__rejectHeld) { window.__rejectHeld = false; throw new TypeError('Failed to fetch'); } }      // the held answer is lost instead of delivered
    return res; };
  window.__release = () => { window.__held.splice(0).forEach((r) => r()); };
  window.__releaseFirst = () => { const r = window.__held.shift(); if (r) r(); }; })();"""


def test_an_older_run_list_answer_arriving_late_changes_nothing(browser):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    context.add_init_script(HOLD)                                                  # lets the test keep one answer back and deliver it late
    page = context.new_page()
    page.goto(PAGE_URL)
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    connect(page)
    page.click("#go")                                                              # accepted; the list still shows nothing
    wait(page, "document.getElementById('msg').textContent.includes('Đã gửi')")
    page.evaluate("window.__hold = true")
    page.click("#refresh")                                                         # look A: answered (empty) but held back
    wait(page, "window.__held.length === 1")
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    gh.routes[runs] = (200, {"workflow_runs": [{"id": 40, "status": "queued", "conclusion": None, "created_at": now}]})
    page.click("#refresh")                                                         # look B, newer: sees the run queued
    wait(page, "document.getElementById('runs-body').children.length === 1")
    assert page.is_disabled("#go")
    page.evaluate("window.__release()")                                            # now A's older, empty answer arrives
    page.wait_for_timeout(500)
    assert page.is_disabled("#go") and "Đang chờ" in text(page, "#runs-body")      # it was discarded: the queued run is still known
    context.close()


def test_a_run_list_still_loading_for_the_old_repository_does_not_land_in_the_new_ones_table(browser):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    context.add_init_script(HOLD)
    page = context.new_page()
    page.goto(PAGE_URL)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 5, "status": "completed", "conclusion": "success", "created_at": now}]})
    connect(page)
    page.evaluate("window.__hold = true")
    page.click("#refresh")                                                         # the list for REPO is on its way, held back
    wait(page, "window.__held.length === 1")
    page.fill("#repo", "someone/else")                                             # the form now targets another repository
    page.evaluate("window.__release()")
    page.wait_for_timeout(500)
    assert page.eval_on_selector_all("#runs-body tr", "trs => trs.length") == 0    # the late answer for the old repository was dropped
    context.close()


def test_forgetting_the_token_while_a_send_is_under_way_leaves_no_lock_behind(browser):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    context.add_init_script(HOLD)
    page = context.new_page()
    page.goto(PAGE_URL)
    connect(page)
    page.evaluate("window.__holdPost = true")
    page.click("#go")                                                              # the send reaches GitHub, its answer is held back
    wait(page, "window.__held.length === 1")
    page.click("#forget")                                                          # the person ends the session meanwhile
    page.fill("#token", TOKEN)
    page.evaluate("window.__release()")                                            # now the answer arrives
    wait(page, "document.getElementById('msg').className.includes('warn')")
    assert "xóa token lúc đang gửi" in text(page, "#msg") and page.is_enabled("#go")      # told, and nothing is left locked
    assert text(page, "#busy-note") == ""
    context.close()


def test_forgetting_the_token_while_the_answer_to_a_send_is_lost_leaves_no_lock_behind(browser):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    context.add_init_script(HOLD)
    page = context.new_page()
    page.goto(PAGE_URL)
    connect(page)
    page.evaluate("window.__holdPost = true; window.__rejectHeld = true")
    page.click("#go")
    wait(page, "window.__held.length === 1")
    page.click("#forget")
    page.fill("#token", TOKEN)
    page.evaluate("window.__release()")                                            # the answer is lost, after the token was forgotten
    wait(page, "document.getElementById('msg').className.includes('warn')")
    assert "xóa token lúc đang gửi" in text(page, "#msg") and page.is_enabled("#go") and text(page, "#busy-note") == ""
    context.close()


def test_a_send_that_hangs_does_not_keep_the_button_off_after_the_token_was_forgotten(browser):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    context.add_init_script(HOLD)
    page = context.new_page()
    page.goto(PAGE_URL)
    connect(page)
    page.evaluate("window.__holdPost = true")
    page.click("#go")
    wait(page, "window.__held.length === 1")                                       # the answer never comes (it is held for as long as the test wants)
    assert page.is_disabled("#go")
    page.click("#forget")
    page.fill("#token", TOKEN)
    assert page.is_enabled("#go")                                                  # a new session does not wait for the old, stalled request
    context.close()


def test_the_end_of_an_old_send_does_not_free_the_button_while_a_newer_send_is_under_way(browser):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    context.add_init_script(HOLD)
    page = context.new_page()
    page.goto(PAGE_URL)
    connect(page)
    page.evaluate("window.__holdPost = true")
    page.click("#go")                                                              # send 1: its answer is held
    wait(page, "window.__held.length === 1")
    page.click("#forget")
    connect(page)                                                                  # a new session
    page.evaluate("window.__holdPost = true")
    page.click("#go")                                                              # send 2: its answer is held too
    wait(page, "window.__held.length === 2")
    assert page.is_disabled("#go")
    page.evaluate("window.__releaseFirst()")                                       # send 1 finally ends ...
    wait(page, "document.getElementById('msg').className.includes('warn')")
    assert page.is_disabled("#go")                                                 # ... and must not free the button: send 2 is still under way
    page.evaluate("window.__release()")
    wait(page, "document.getElementById('msg').textContent.includes('Đã gửi')")
    context.close()


def test_a_run_started_elsewhere_is_still_followed_after_a_failed_look(browser):
    context, page = _with_a_fake_clock(browser)
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    connect(page)
    page.gh.routes[runs] = (200, {"workflow_runs": [{"id": 3, "status": "in_progress", "conclusion": None, "created_at": now}]})
    page.click("#refresh")                                                         # someone else's run, no send of mine at all
    wait(page, "document.getElementById('runs-body').textContent.includes('Đang chạy')")
    settle(page, 1)
    page.gh.routes[runs] = (500, {"message": "x"})
    page.clock.fast_forward(10_000)                                                # the next look fails ...
    wait(page, "document.getElementById('msg').className.includes('bad')")
    settle(page, 2)
    page.gh.routes[runs] = (200, {"workflow_runs": [{"id": 3, "status": "completed", "conclusion": "success", "created_at": now}]})
    page.clock.fast_forward(10_000)                                                # ... and the page still looks again, by itself
    wait(page, "document.getElementById('runs-body').textContent.includes('Xong')")
    context.close()


def test_forgetting_the_token_before_the_send_goes_out_sends_nothing(browser):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    context.add_init_script(HOLD)
    page = context.new_page()
    page.goto(PAGE_URL)
    page.fill("#token", TOKEN)                                                     # no check first: the branch is looked up inside go()
    page.evaluate("window.__hold = true")                                          # holds the list read before the send
    page.click("#go")
    wait(page, "window.__held.length === 1")
    page.click("#forget")
    page.evaluate("window.__release()")
    wait(page, "document.getElementById('msg').className.includes('warn')")
    assert gh.posts() == [] and "chưa gửi gì" in text(page, "#msg")
    context.close()


def test_a_token_put_back_while_a_send_is_followed_makes_the_page_look_again(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    ui.gh.routes[runs] = (200, ui.gh.runs_after_dispatch([{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]))
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    assert "Đang theo dõi" in text(ui, "#busy-note")
    ui.fill("#token", "")                                                          # cleared by hand, the followed send stays
    ui.gh.routes[runs] = (200, {"workflow_runs": [{"id": 9, "status": "completed", "conclusion": "success", "created_at": now}]})
    ui.fill("#token", TOKEN)
    ui.press("#token", "Tab")                                                      # committed: the page looks again, without any other click
    wait(ui, "document.getElementById('go').disabled === false")
    assert text(ui, "#busy-note") == ""


def test_checking_the_token_while_a_send_is_followed_makes_the_page_look_again(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    ui.gh.routes[runs] = (200, ui.gh.runs_after_dispatch([{"id": 9, "status": "queued", "conclusion": None, "created_at": now}]))
    ui.click("#go")
    wait(ui, "document.getElementById('go').disabled === true && document.getElementById('runs-body').children.length === 1")
    ui.gh.routes[runs] = (200, {"workflow_runs": [{"id": 9, "status": "completed", "conclusion": "success", "created_at": now}]})
    ui.click("#check")
    wait(ui, "document.getElementById('go').disabled === false")


def test_the_table_of_runs_is_emptied_when_another_repository_is_typed(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 5, "status": "completed", "conclusion": "success", "created_at": now}]})
    ui.click("#refresh")
    wait(ui, "document.getElementById('runs-body').children.length === 1")
    ui.fill("#repo", "someone/else")
    assert ui.eval_on_selector_all("#runs-body tr", "trs => trs.length") == 0      # the rows belonged to the old repository


def test_a_dispatch_that_was_refused_does_not_start_a_wait(ui):
    connect(ui)
    ui.gh.routes[("POST", f"/repos/{REPO}/actions/workflows/radar.yml/dispatches")] = (422, {"message": "nope"})
    ui.click("#go")
    wait(ui, "document.getElementById('msg').className.includes('bad')")
    assert ui.is_enabled("#go")


@pytest.mark.parametrize("created_at", [(-3600,), (3600,), (-5,), (5,)])
def test_the_run_just_sent_is_recognised_whatever_the_clocks_say(ui, created_at):
    connect(ui)
    stamp = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=created_at[0])).isoformat()      # a clock hours ahead or behind GitHub's
    runs = ("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")
    ui.gh.routes[runs] = (200, ui.gh.runs_after_dispatch([{"id": 50, "status": "completed", "conclusion": "success", "created_at": stamp}]))
    ui.click("#go")
    wait(ui, "document.getElementById('runs-body').children.length === 1")
    assert "lượt bạn vừa gửi" in text(ui, "#runs-body")
    assert ui.is_enabled("#go")                                                    # found, finished: no two-minute lock


def test_a_run_that_was_already_listed_is_not_taken_for_the_one_just_sent(ui):
    connect(ui)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 3, "status": "in_progress", "conclusion": None, "created_at": now}]})                  # someone else's run, there before and after
    ui.click("#go")
    wait(ui, "document.getElementById('runs-body').children.length === 1")
    assert "lượt bạn vừa gửi" not in text(ui, "#runs-body")
    assert ui.is_disabled("#go")                                                   # the sent run is not listed yet: still waiting


def test_nothing_is_sent_when_the_runs_cannot_be_listed_first(ui):
    connect(ui)
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (500, {"message": "x"})
    ui.click("#go")
    wait(ui, "document.getElementById('msg').className.includes('bad')")
    assert "Chưa gửi" in text(ui, "#msg") and ui.gh.posts() == [] and ui.is_enabled("#go")


@pytest.mark.parametrize("branch", ["release@next", "feature+plus", "v1.0/hot_fix", "a" * 150, "a" * 150 + "/" + "b" * 150])
def test_any_branch_name_git_allows_can_be_dispatched(ui, branch):
    ui.gh.routes[("GET", f"/repos/{REPO}")] = (200, {"default_branch": branch})
    connect(ui)
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert ui.gh.posts()[0]["body"]["ref"] == branch


def test_a_branch_name_git_allows_is_also_accepted_when_sending_without_a_check_first(ui):
    ui.gh.routes[("GET", f"/repos/{REPO}")] = (200, {"default_branch": "release@next"})
    ui.fill("#token", TOKEN)
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert ui.gh.posts()[0]["body"]["ref"] == "release@next"


def test_the_bucket_choices_follow_the_buckets_the_scan_keeps(ui):
    options = lambda: ui.eval_on_selector_all("#single-bucket option", "os => os.map(o => o.value)")        # noqa: E731
    assert options() == ["", "ai", "software", "solutions", "startup"]
    ui.select_option("#single-bucket", "startup")
    ui.select_option("#preset", "ai-sau")                                          # a preset that keeps only the AI bucket
    assert options() == ["", "ai"] and ui.input_value("#single-bucket") == ""      # the choice that no longer exists is dropped, visibly
    ui.select_option("#preset", "none")
    assert options() == ["", "ai", "software", "solutions", "startup"]
    ui.select_option("#single-bucket", "software")
    ui.uncheck("#bucket-solutions")
    assert options() == ["", "ai", "software", "startup"] and ui.input_value("#single-bucket") == "software"      # a kept choice stays


def test_a_single_repository_is_sent_with_a_bucket_the_preset_kept_and_never_one_it_dropped(ui):
    connect(ui)
    ui.select_option("#preset", "ai-sau")
    ui.fill("#single", "owner/name")
    ui.select_option("#single-bucket", "ai")
    ui.click("#go")
    wait(ui, "document.getElementById('msg').textContent.includes('Đã gửi')")
    assert ui.gh.posts()[0]["body"]["inputs"]["bucket"] == "ai"
    # a choice smuggled into the select (not one of the options the page offers) is not sent either
    ui.evaluate("""() => { const o = document.createElement('option'); o.value = 'startup'; document.getElementById('single-bucket').append(o);
                           document.getElementById('single-bucket').value = 'startup'; }""")
    ui.gh.routes[("GET", f"/repos/{REPO}/actions/workflows/radar.yml/runs")] = (200, {"workflow_runs": [
        {"id": 99, "status": "completed", "conclusion": "success", "created_at": dt.datetime.now(dt.timezone.utc).isoformat()}]})
    ui.click("#refresh")
    wait(ui, "document.getElementById('go').disabled === false")
    ui.evaluate("document.getElementById('single-bucket').value = 'startup'")
    ui.click("#go")
    wait(ui, "document.querySelector('#msg').textContent.includes('Đã gửi')")
    assert ui.gh.posts()[-1]["body"]["inputs"]["bucket"] == ""


def test_a_dry_run_estimate_promises_no_model_calls_and_no_pauses(ui):
    dry = text(ui, "#estimate")
    assert "lượt tìm" in dry and "quét thử nên không gọi model và không nghỉ" in dry and "lượt gọi model và" not in dry
    ui.uncheck("#dry")
    real = text(ui, "#estimate")
    assert "6 lượt gọi model" in real and "90 giây nghỉ" in real and "không gọi model" not in real
    ui.check("#dry")
    assert text(ui, "#estimate") == dry


def test_the_estimate_for_one_repository_has_no_search_and_one_posts_worth_of_calls(ui):
    ui.uncheck("#dry")
    assert "lượt tìm" in text(ui, "#estimate") and "quét đúng một repo" not in text(ui, "#estimate")
    ui.fill("#single", "owner/name")
    estimate = text(ui, "#estimate")
    assert "quét đúng một repo" in estimate and "lượt tìm" not in estimate and " 2 lượt gọi model" in estimate and " 0 giây nghỉ" in estimate
    ui.check("#lang-en")
    assert " 4 lượt gọi model" in text(ui, "#estimate") and " 45 giây nghỉ" in text(ui, "#estimate")
    ui.fill("#single", "")
    assert "lượt tìm" in text(ui, "#estimate")


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
