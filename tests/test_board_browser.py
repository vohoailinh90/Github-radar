"""docs/ui/board.html in a real browser (Chromium through Playwright), with api.github.com answered by the test.

Skipped when Playwright or a browser is missing (CI installs neither): tests/test_board.py is what always runs. These prove what no source check can:
that the token goes only into one header to one host, that the page only reads, that text from GitHub stays text, and what a person sees."""

import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path

import pytest

from scripts import ui_sync

sync_api = pytest.importorskip("playwright.sync_api")

PAGE_URL = ui_sync.BOARD.as_uri()
TOKEN = "github_pat_TESTONLY_not_a_real_token_0123456789"
REPO = "demo/app"
STORE_KEY = "radar-board.v1"
CORS = {"access-control-allow-origin": "*", "access-control-expose-headers": "etag, x-ratelimit-remaining, x-ratelimit-limit, x-ratelimit-reset"}
PREFLIGHT = {**CORS, "access-control-allow-headers": "authorization, accept, x-github-api-version, if-none-match", "access-control-allow-methods": "GET, OPTIONS"}
EVIL = '<img src=x onerror="window.__pwn=1">'


def iso(seconds_ago: float = 0) -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=seconds_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def run_of(run_id, wf, number, status, conclusion, ago, event="push"):
    return {"id": run_id, "workflow_id": wf, "run_number": number, "status": status, "conclusion": conclusion, "event": event, "head_branch": "main", "actor": {"login": "me"},
            "created_at": iso(ago), "run_started_at": iso(ago), "updated_at": iso(ago - 100)}


def app_routes(repo: str = REPO) -> dict:
    """The answers of a small repository: one run in progress (with a job and three steps), one finished, one failed, a schedule, an agent PR, and a weekly
    workflow whose only run is older than the 40 newest of the repository (so it is missing from the repository's own list)."""
    base = f"/repos/{repo}"
    return {
        f"{base}/actions/workflows/1/runs": (200, {"workflow_runs": [run_of(101, 1, 8, "in_progress", None, 120), run_of(100, 1, 7, "completed", "success", 4000)]}),
        f"{base}/actions/workflows/2/runs": (200, {"workflow_runs": [run_of(90, 2, 3, "completed", "failure", 90000, "schedule"), run_of(80, 2, 2, "completed", "success", 180000, "schedule")]}),
        f"{base}/actions/workflows/3/runs": (200, {"workflow_runs": [run_of(70, 3, 1, "completed", "success", 500000)]}),
        f"{base}/contents/.github/workflows/weekly.yml": (200, "on:\n  schedule:\n    - cron: '0 3 * * 1'\n"),
        base: (200, {"full_name": repo, "description": "An app", "stargazers_count": 7, "private": False, "archived": False, "pushed_at": iso(300), "open_issues_count": 3, "default_branch": "main"}),
        f"{base}/actions/runs": (200, {"workflow_runs": [
            {"id": 101, "workflow_id": 1, "run_number": 8, "status": "in_progress", "conclusion": None, "event": "push", "head_branch": "claude/x", "actor": {"login": "me"},
             "created_at": iso(130), "run_started_at": iso(120), "updated_at": iso(5)},
            {"id": 100, "workflow_id": 1, "run_number": 7, "status": "completed", "conclusion": "success", "event": "push", "head_branch": "main", "actor": {"login": "me"},
             "created_at": iso(4000), "run_started_at": iso(4000), "updated_at": iso(3800)},
            {"id": 90, "workflow_id": 2, "run_number": 3, "status": "completed", "conclusion": "failure", "event": "schedule", "head_branch": "main", "actor": {"login": "me"},
             "created_at": iso(90000), "run_started_at": iso(90000), "updated_at": iso(89000)}]}),
        f"{base}/actions/workflows": (200, {"workflows": [
            {"id": 1, "name": EVIL + "CI", "path": ".github/workflows/ci.yml", "state": "active"},
            {"id": 2, "name": "Nightly", "path": ".github/workflows/nightly.yml", "state": "active"},
            {"id": 3, "name": "Weekly scan", "path": ".github/workflows/weekly.yml", "state": "active"}]}),
        f"{base}/pulls": (200, [{"number": 5, "title": "Fix <b>x</b>", "head": {"ref": "claude/fix-x"}, "user": {"login": "me", "type": "User"}, "draft": False, "updated_at": iso(60), "created_at": iso(60)}]),
        f"{base}/contents/.github/workflows/ci.yml": (200, "on:\n  push:\n  workflow_dispatch:\n"),
        f"{base}/contents/.github/workflows/nightly.yml": (200, "on:\n  schedule:\n    - cron: '0 18 * * *'\n"),
        f"{base}/contents/.claude/agents": (200, [{"name": "architect.md", "type": "file"}, {"name": "README.txt", "type": "file"}, {"name": "sub", "type": "dir"}]),
        f"{base}/actions/runs/101/jobs": (200, {"jobs": [{"id": 1, "name": "build", "status": "in_progress", "started_at": iso(100), "steps": [
            {"name": "Checkout", "status": "completed", "conclusion": "success", "number": 1}, {"name": "Test", "status": "in_progress", "conclusion": None, "number": 2},
            {"name": "Deploy", "status": "queued", "conclusion": None, "number": 3}]}]}),
        f"{base}/actions/runs/100/jobs": (200, {"jobs": [{"id": 2, "name": "build", "status": "completed", "conclusion": "success", "started_at": iso(4000), "completed_at": iso(3800), "steps": [
            {"name": "Checkout", "status": "completed", "conclusion": "success", "number": 1}]}]}),
        f"{base}/actions/runs/90/jobs": (200, {"jobs": [{"id": 3, "name": "nightly", "status": "completed", "conclusion": "failure", "started_at": iso(90000), "completed_at": iso(89000), "steps": [
            {"name": "Checkout", "status": "completed", "conclusion": "success", "number": 1}, {"name": "Run e2e", "status": "completed", "conclusion": "failure", "number": 2}]}]}),
    }


class Github:
    """api.github.com as the test wants it: records every request, answers from `routes` ({path: (status, body)}), with ETags and a rate limit."""

    def __init__(self):
        self.requests: list[dict] = []
        self.routes: dict = app_routes()
        self.remaining = 4990
        self.not_modified = 0

    def handle(self, route, request):
        if request.method == "OPTIONS":
            return route.fulfill(status=204, headers=PREFLIGHT)
        path = request.url.split("https://api.github.com", 1)[1]
        clean = path.split("?", 1)[0]
        self.requests.append({"method": request.method, "path": path, "clean": clean, "headers": request.headers})
        rate = {"x-ratelimit-remaining": str(self.remaining), "x-ratelimit-limit": "5000", "x-ratelimit-reset": str(int(time.time()) + 3000)}
        if clean not in self.routes:
            return route.fulfill(status=404, headers={**CORS, **rate}, content_type="application/json", body='{"message":"Not Found"}')
        status, body = self.routes[clean]
        if callable(body):
            status, body = body()
        if isinstance(body, str):
            etag = '"' + hashlib.sha1(body.encode()).hexdigest()[:10] + '"'
            if request.headers.get("if-none-match") == etag:
                self.not_modified += 1
                return route.fulfill(status=304, headers={**CORS, **rate, "etag": etag})
            return route.fulfill(status=status, headers={**CORS, **rate, "etag": etag}, content_type="text/plain", body=body)
        text = json.dumps(body)
        etag = '"' + hashlib.sha1(text.encode()).hexdigest()[:10] + '"'
        if request.headers.get("if-none-match") == etag:
            self.not_modified += 1
            return route.fulfill(status=304, headers={**CORS, **rate, "etag": etag})
        return route.fulfill(status=status, headers={**CORS, **rate, "etag": etag}, content_type="application/json", body=text)

    def conditional(self, since: int) -> list:
        """The requests made after the first `since`, each with whether it asked 'only if changed'."""
        return [("if-none-match" in r["headers"]) for r in self.requests[since:]]

    def paths(self, method="GET") -> list:
        return [r["clean"] for r in self.requests if r["method"] == method]


def new_page(browser, repos=(REPO,), width=1280, interval=0, tz="Asia/Ho_Chi_Minh"):
    """A fresh context whose saved list holds `repos` (set once, so a reload keeps whatever the page saved since)."""
    context = browser.new_context(viewport={"width": width, "height": 900}, timezone_id=tz, locale="vi-VN")
    seed = json.dumps({"repos": list(repos), "interval": interval})
    context.add_init_script(f"if (!window.localStorage.getItem('{STORE_KEY}')) window.localStorage.setItem('{STORE_KEY}', {json.dumps(seed)});")
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    page = context.new_page()
    seen, problems = [], []
    page.on("request", lambda r: seen.append(r.url))
    page.on("pageerror", lambda e: problems.append(str(e)))
    page.on("console", lambda m: problems.append(m.text) if m.type in ("error", "warning") else None)
    page.gh, page.seen, page.problems = gh, seen, problems
    return context, page


@pytest.fixture
def ui(browser):
    context, page = new_page(browser)
    page.goto(PAGE_URL)
    wait(page, "document.querySelector('.repo h3 a') !== null")
    yield page
    context.close()


def wait(page, expression, seconds=8):
    """Wait until a JavaScript expression is true. Playwright's own wait_for_function evals a string, which the page's CSP (no unsafe-eval, on
    purpose) refuses; evaluate() goes through the debugging protocol instead."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if page.evaluate(f"() => Boolean({expression})"):
            return
        time.sleep(0.05)
    raise AssertionError(f"still false after {seconds}s: {expression}")


def text(page, selector):
    return page.inner_text(selector)


# ---- what a person sees --------------------------------------------------------------------------------------------------------

def test_the_page_loads_clean_and_only_reads(ui):
    assert ui.problems == []                                                         # no CSP violation, no script error
    assert ui.title() == "GitHub Radar: bảng theo dõi repo"
    assert ui.gh.requests and all(r["method"] == "GET" for r in ui.gh.requests)
    assert all("authorization" not in r["headers"] for r in ui.gh.requests)          # no token, no header
    assert {u.split("/")[2] for u in ui.seen if u.startswith("http")} == {"api.github.com"}


def test_a_running_task_shows_its_job_and_each_step(ui):
    wait(ui, "document.querySelectorAll('.task .step').length === 3")
    task = text(ui, ".task")
    assert "Đang chạy" in task and "demo/app" in task and "lượt #8" in task and "nhánh claude/x" in task and "1/3 bước" in task
    assert ui.eval_on_selector_all(".task .step", "els => els.map(e => e.className.split(' ').find(c => c.startsWith('st-')))") == ["st-success", "st-running", "st-queued"]
    assert ui.get_attribute(".task progress", "value") == "1" and ui.get_attribute(".task progress", "max") == "3"
    assert text(ui, "#tiles").replace("\n", " ").startswith("1 Repo đã liên kết")
    assert "đã chạy 2 phút" in text(ui, ".task")


def test_a_row_for_a_finished_workflow_loads_its_steps_when_opened(ui):
    row = ui.locator("details.wf", has_text="Nightly")
    assert "Lỗi" in row.inner_text() and not [p for p in ui.gh.paths() if p.endswith("/runs/90/jobs")]            # nothing is read until it is opened
    row.locator("summary").click()
    wait(ui, "document.querySelectorAll('details.wf[open] .step.st-failure').length === 1")
    assert [p for p in ui.gh.paths() if p.endswith("/runs/90/jobs")] and "Run e2e" in row.inner_text()


def test_a_workflow_crowded_out_of_the_repository_list_still_shows_its_own_history(ui):
    weekly = ui.locator("details.wf", has_text="Weekly scan")
    assert "Thành công" in weekly.inner_text() and "Chưa thấy lượt chạy" not in weekly.inner_text()
    assert [p for p in ui.gh.paths() if p.endswith("/actions/workflows/3/runs")]
    nightly = ui.locator("details.wf", has_text="Nightly")
    assert nightly.locator(".spark").get_attribute("aria-label") == "2 lượt gần nhất: 1 thành công, 1 lỗi"          # run 90 came from both lists and counts once
    assert "Lỗi" in nightly.inner_text()                                                                          # the newest finished run decides, not the older success


def test_the_schedule_is_read_from_the_workflow_file_and_shown_in_words_and_on_the_week(ui):
    wait(ui, "document.querySelector('.sched') !== null")
    sched = text(ui, ".sched")
    assert "hằng ngày 18:00 UTC" in sched and "kế tiếp" in sched
    assert ui.locator("#week .day li", has_text="Nightly").count() >= 6                  # one a day for the week
    assert ui.get_attribute(".sched", "title") == "0 18 * * * (UTC)"


def test_agents_are_guessed_from_names_and_the_declared_ones_are_listed(ui):
    body = text(ui, "#agents-body")
    assert "architect" in body and "README" not in body and "sub" not in body.split("agents/:")[1].split("\n")[0]        # only .md files
    assert "claude" in body and "#5" in body
    assert "(1 từ agent)" in text(ui, "#tiles").replace("\n", " ")
    assert "suy đoán theo tên" in text(ui, "#agents")


def test_text_from_github_stays_text(ui):
    assert ui.evaluate("window.__pwn") is None and ui.query_selector("img") is None
    assert EVIL + "CI" in text(ui, "details.wf .name")                                  # shown as the characters it is made of
    assert ui.query_selector("#agents-body li b") is None and "Fix <b>x</b>" in text(ui, "#agents-body")


def test_a_sparkline_and_the_states_say_it_in_words_too(ui):
    label = ui.get_attribute("details.wf >> nth=0 >> .spark", "aria-label")
    assert label.startswith("2 lượt gần nhất") or label.startswith("1 lượt gần nhất")
    assert ui.get_attribute("details.wf >> nth=0 >> .spark", "role") == "img"


# ---- the token -----------------------------------------------------------------------------------------------------------------

def test_the_token_goes_only_into_one_header_and_is_kept_nowhere(ui):
    ui.gh.requests.clear()
    ui.fill("#token", TOKEN)
    ui.press("#token", "Tab")
    wait(ui, "document.getElementById('connect-msg').className.includes('ok')")
    wait(ui, "document.querySelector('.repo h3 a') !== null")
    sent = ui.gh.requests
    assert sent and all(r["method"] == "GET" and r["headers"].get("authorization") == "Bearer " + TOKEN for r in sent)
    assert all(r["path"].startswith("/repos/") for r in sent)
    stores = ui.evaluate("() => ({ local: Object.entries(window.localStorage), session: Object.keys(window.sessionStorage), cookie: document.cookie, body: document.body.innerText })")
    assert TOKEN not in json.dumps(stores) and stores["session"] == [] and stores["cookie"] == "" and ui.context.cookies() == []
    assert TOKEN not in ui.url and ui.input_value("#token") == TOKEN
    assert "5.000" in text(ui, "#rate") or "4.990/5.000" in text(ui, "#rate")
    ui.gh.requests.clear()
    ui.click("#forget")
    wait(ui, "document.getElementById('connect-msg').textContent.includes('quên')")
    wait(ui, "document.querySelector('.repo h3 a') !== null")
    assert ui.input_value("#token") == "" and ui.gh.requests and all("authorization" not in r["headers"] for r in ui.gh.requests)


def test_a_private_repo_is_unreadable_without_a_token_and_forgetting_the_token_drops_what_it_loaded(browser):
    context, page = new_page(browser)
    secret = app_routes()
    page.gh.routes = {path: (404, {"message": "Not Found"}) for path in secret}
    page.goto(PAGE_URL)
    wait(page, "document.querySelector('.repo p.bad') !== null")
    assert "private hoặc sai tên" in text(page, ".repo p.bad")
    page.gh.routes = secret                                                              # with a token the same repo answers
    page.fill("#token", TOKEN)
    page.press("#token", "Tab")
    wait(page, "document.querySelector('.repo h3 a') !== null")
    page.gh.routes = {path: (404, {"message": "Not Found"}) for path in secret}
    page.click("#forget")
    wait(page, "document.querySelector('.repo p.bad') !== null")                         # what the token fetched is gone from the page
    assert page.query_selector(".task") is None
    context.close()


def test_a_page_served_from_github_io_never_sends_a_token(browser):
    context = browser.new_context()
    gh = Github()
    context.route("https://api.github.com/**", gh.handle)
    context.route("https://someone.github.io/**", lambda route: route.fulfill(status=200, content_type="text/html; charset=utf-8", body=ui_sync.BOARD.read_text(encoding="utf-8")))
    page = context.new_page()
    page.goto("https://someone.github.io/ui/board.html")
    assert page.is_visible("#origin-warning") and page.is_disabled("#token")
    page.evaluate("document.getElementById('token').disabled = false; document.getElementById('token').value = 'github_pat_x';"
                  "document.getElementById('token').dispatchEvent(new Event('change'))")
    page.wait_for_timeout(500)
    assert gh.requests and all("authorization" not in r["headers"] for r in gh.requests)          # a token forced into the field is not used
    context.close()


# ---- repositories ---------------------------------------------------------------------------------------------------------------

def test_a_wrong_name_sends_nothing_and_a_right_one_is_linked_saved_and_removable(ui):
    before = len(ui.gh.requests)
    ui.fill("#add-repo", "not a repo")
    ui.click("#add")
    assert "chủ/tên" in text(ui, "#link-msg") and len(ui.gh.requests) == before
    ui.fill("#add-repo", "https://github.com/demo/other.git")
    ui.press("#add-repo", "Enter")
    wait(ui, "document.querySelectorAll('.chip').length === 2")
    wait(ui, "document.querySelectorAll('.repo').length === 2 && document.querySelector('.repo p.bad') !== null")
    assert "/repos/demo/other" in ui.gh.paths() and "Không thấy repo" in text(ui, ".repo p.bad")
    ui.fill("#add-repo", "DEMO/app")
    ui.click("#add")
    assert "đã được liên kết" in text(ui, "#link-msg") and ui.locator(".chip").count() == 2            # the same repo in other letters is the same repo
    ui.reload()
    wait(ui, "document.querySelectorAll('.chip').length === 2")                                          # it was saved
    assert ui.evaluate(f"() => JSON.parse(window.localStorage.getItem('{STORE_KEY}')).repos") == ["demo/app", "demo/other"]
    ui.click("button[aria-label='Bỏ liên kết demo/other']")
    wait(ui, "document.querySelectorAll('.chip').length === 1")
    ui.reload()
    wait(ui, "document.querySelectorAll('.chip').length === 1")
    assert text(ui, ".chip") .startswith("demo/app")


def test_a_refused_read_gets_a_plain_explanation(browser):
    context, page = new_page(browser)
    page.gh.remaining = 0
    page.gh.routes = {f"/repos/{REPO}": (403, {"message": "API rate limit exceeded"})}
    page.goto(PAGE_URL)
    wait(page, "document.querySelector('.repo p.bad') !== null")
    assert "Hết hạn mức GitHub" in text(page, ".repo p.bad") and "token chỉ-đọc" in text(page, ".repo p.bad")
    context.close()


@pytest.mark.parametrize("status,body,words", [
    (403, {"message": "You have exceeded a secondary rate limit"}, "giới hạn tốc độ"), (429, {"message": "Too many requests: rate limit"}, "giới hạn tốc độ"),
    (403, {"message": "Resource not accessible by personal access token"}, "token thiếu quyền"), (401, {"message": "Bad credentials"}, "Token sai"), (500, None, "mã 500")])
def test_each_refusal_is_told_apart(browser, status, body, words):
    context, page = new_page(browser)
    page.gh.routes = {f"/repos/{REPO}": (status, body)}
    page.goto(PAGE_URL)
    wait(page, "document.querySelector('.repo p.bad') !== null")
    assert words in text(page, ".repo p.bad") and page.locator(".repo button", has_text="Thử lại").count() == 1
    context.close()


def test_repos_can_be_picked_from_an_account(browser):
    context, page = new_page(browser, repos=())
    page.gh.routes = {"/users/demo/repos": (200, [{"full_name": "demo/app", "owner": {"login": "demo"}, "private": False, "pushed_at": iso(60)},
                                                  {"full_name": "demo/tool", "owner": {"login": "demo"}, "private": False, "pushed_at": iso(600)},
                                                  {"full_name": "bad name/x y", "owner": {"login": "demo"}}]), **{k: v for k, v in app_routes("demo/tool").items()}}
    page.goto(PAGE_URL)
    page.click("#pick")
    page.fill("#pick-owner", "demo")
    page.click("#pick-load")
    wait(page, "document.querySelectorAll('#pick-list input').length === 2")                              # the malformed name is not offered
    page.check("#pick-list label >> nth=1 >> input")
    page.click("#pick-add")
    wait(page, "document.querySelectorAll('.chip').length === 1")
    assert text(page, ".chip").startswith("demo/tool")
    context.close()


def test_the_list_can_be_exported_and_added_from_text(ui):
    ui.click("details.io summary")
    ui.click("#export")
    assert json.loads(ui.input_value("#io")) == {"repos": ["demo/app"]}
    ui.fill("#io", "demo/a\nhttps://github.com/demo/b, nonsense")
    ui.click("#import")
    wait(ui, "document.querySelectorAll('.chip').length === 3")
    assert "bỏ qua 1 mục không hợp lệ" in text(ui, "#link-msg")


# ---- cost: the page asks GitHub as little as it can --------------------------------------------------------------------------------

def test_a_second_look_asks_only_if_changed_and_a_not_modified_answer_changes_nothing(ui):
    before = text(ui, "#repo-grid")
    count, answered = len(ui.gh.requests), ui.gh.not_modified
    ui.click("#refresh")
    deadline = time.monotonic() + 8
    while len(ui.gh.requests) < count + 12 and time.monotonic() < deadline:                # repo, runs, workflows, pulls, jobs, three workflow files, agents, three histories
        ui.wait_for_timeout(100)
    ui.wait_for_timeout(300)
    asked = ui.gh.conditional(count)
    assert len(asked) == 12 and all(asked)                                                 # every one of them was conditional ...
    assert ui.gh.not_modified - answered == len(asked)                                     # ... and every one was answered "not modified"
    assert text(ui, "#repo-grid") == before and ui.query_selector(".task .step") is not None


# ---- the demo, the Office snapshot, small screens, frames -------------------------------------------------------------------------

def test_the_demo_contacts_nobody_and_leaving_it_brings_the_list_back(ui):
    seen = len(ui.seen)
    ui.click("#demo")
    wait(ui, "document.querySelectorAll('.task').length === 3")
    assert ui.is_visible("#banner") and len(ui.seen) == seen and ui.is_disabled("#add")
    assert "Đang chạy" in text(ui, ".task") and ui.locator("#repo-grid .repo").count() == 4
    assert "Mô phỏng" not in text(ui, "body") and "REQ-031" in text(ui, "#office-body")
    ui.click("#demo")
    wait(ui, "document.getElementById('banner').hidden")
    assert ui.locator(".chip").count() == 1 and text(ui, ".chip").startswith("demo/app") and ui.is_enabled("#add")
    assert ui.evaluate(f"() => JSON.parse(window.localStorage.getItem('{STORE_KEY}')).repos") == ["demo/app"]      # the demo never overwrote the saved list


def test_an_office_snapshot_is_read_in_the_browser_and_kept_nowhere(ui, tmp_path):
    snap = {"version": 1, "mode": "claude", "now": time.time(), "live": True, "requirement": {"id": "REQ-9", "tier": "T2", "strategy": "main_with_architect_and_reviewer"},
            "progress": {"pct": 50, "agents": 2, "total": 2, "running": 1, "done": 1, "blocked": 0}, "phase": {"steps": ["analysis", "verify"], "current": "verify"},
            "agents": {"x": {"id": "x", "state": "working", "task": EVIL, "progress": 0.4, "model": "sonnet", "tokens": 1200}}}
    good = Path(tmp_path) / "snapshot.json"
    good.write_text(json.dumps(snap), encoding="utf-8")
    seen = len(ui.seen)
    ui.set_input_files("#office-file", str(good))
    wait(ui, "document.querySelector('.oa') !== null")
    assert "REQ-9" in text(ui, "#office-body") and EVIL in text(ui, ".oa") and ui.query_selector("#office-body img") is None and ui.evaluate("window.__pwn") is None
    assert len(ui.seen) == seen                                                          # the file went nowhere
    assert "REQ-9" not in json.dumps(ui.evaluate("() => Object.entries(window.localStorage)"))
    bad = Path(tmp_path) / "other.json"
    bad.write_text(json.dumps({**snap, "version": 2}), encoding="utf-8")
    ui.set_input_files("#office-file", str(bad))
    wait(ui, "document.getElementById('office-msg').className.includes('bad')")
    assert "version 1" in text(ui, "#office-msg") and "REQ-9" in text(ui, "#office-body")            # the good one stays
    notjson = Path(tmp_path) / "x.json"
    notjson.write_text("not json", encoding="utf-8")
    ui.set_input_files("#office-file", str(notjson))
    wait(ui, "document.getElementById('office-msg').textContent.includes('không phải JSON')")


def test_the_week_has_a_column_for_every_day_the_next_seven_days_touch(browser):
    """Seven times 24 hours from Sunday midday end on the next Sunday: its 01:30 run needs a column of its own, not a silent drop."""
    context, page = new_page(browser, tz="UTC")
    page.clock.set_fixed_time(dt.datetime(2026, 10, 18, 12, 0, tzinfo=dt.timezone.utc))
    page.goto(PAGE_URL)
    page.click("#demo")
    wait(page, "document.querySelectorAll('.task').length === 3")
    assert page.locator("#week .day").count() == 8
    last = page.locator("#week .day").nth(7).inner_text()
    assert "25-10" in last and "Deploy docs" in last and "01:30" in last
    assert "Hôm nay" in page.locator("#week .day").nth(0).inner_text()
    context.close()


def test_forgetting_the_token_also_clears_the_account_list_the_token_loaded(browser):
    context, page = new_page(browser)
    page.gh.routes = {**app_routes(), "/user/repos": (200, [{"full_name": "me/secret-private", "owner": {"login": "me"}, "private": True, "pushed_at": iso(60)}])}
    page.goto(PAGE_URL)
    page.fill("#token", TOKEN)
    page.press("#token", "Tab")
    page.click("#pick")
    page.fill("#pick-owner", "me")
    page.click("#pick-load")
    wait(page, "document.querySelectorAll('#pick-list input').length === 1")
    assert "secret-private" in text(page, "#pick-list")
    page.click("details.io summary")
    page.click("#export")
    assert page.input_value("#io") != ""
    page.click("#forget")
    wait(page, "document.getElementById('connect-msg').textContent.includes('quên')")
    assert page.locator("#pick-list li").count() == 0 and page.input_value("#io") == "" and "secret-private" not in text(page, "body")
    context.close()


def test_out_of_quota_the_page_stops_sending_until_the_reset(browser):
    repos = [f"demo/r{i}" for i in range(6)]
    context, page = new_page(browser, repos=repos)
    page.gh.remaining = 0
    page.gh.routes = {f"/repos/{r}": (403, {"message": "API rate limit exceeded"}) for r in repos}
    page.goto(PAGE_URL)
    wait(page, "document.querySelectorAll('.repo p.bad').length === 6")
    assert len(page.gh.requests) == 12                                            # three repos at a time, four calls each; the other three were never sent
    assert all("Hết hạn mức GitHub" in t for t in page.eval_on_selector_all(".repo p.bad", "els => els.map(e => e.textContent)"))
    page.fill("#token", TOKEN)                                                   # a new token is a new quota: the page asks again
    page.press("#token", "Tab")
    wait(page, "document.getElementById('connect-msg').className.includes('ok')")
    page.wait_for_timeout(300)
    assert len(page.gh.requests) > 12
    context.close()


def test_auto_refresh_pauses_when_the_quota_runs_low_and_goes_on_when_it_recovers(browser):
    context, page = new_page(browser, interval=30)
    page.clock.install(time=dt.datetime.now(dt.timezone.utc))
    page.gh.remaining = 100                                                      # of 5000: below the 5 % the page keeps back
    page.goto(PAGE_URL)
    page.fill("#token", TOKEN)
    page.press("#token", "Tab")
    wait(page, "document.querySelector('.repo h3 a') !== null")
    wait(page, "document.getElementById('rate').textContent.includes('tạm dừng')")
    seen = len(page.gh.requests)
    page.clock.run_for(65_000)
    page.wait_for_timeout(400)
    assert len(page.gh.requests) == seen                                         # two timer ticks, nothing sent
    page.gh.remaining = 4000
    page.click("#refresh")                                                       # the person asks: this goes through and reads the new quota
    wait(page, "document.getElementById('rate').textContent.includes('4.000')")
    assert "tạm dừng" not in text(page, "#rate")
    seen = len(page.gh.requests)
    page.clock.run_for(31_000)
    deadline = time.monotonic() + 6
    while len(page.gh.requests) == seen and time.monotonic() < deadline:
        page.wait_for_timeout(100)
    assert len(page.gh.requests) > seen                                          # and the timer works again by itself
    context.close()


@pytest.mark.parametrize("width", [320, 390, 768])
def test_nothing_scrolls_sideways_on_a_phone_or_tablet(browser, width):
    context, page = new_page(browser, width=width)
    page.goto(PAGE_URL)
    wait(page, "document.querySelector('.repo h3 a') !== null")
    page.click("#demo")
    wait(page, "document.querySelectorAll('.task').length === 3")
    for summary in page.query_selector_all("details.wf > summary"):
        summary.click()
    page.wait_for_timeout(200)
    sizes = page.evaluate("() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth })")
    assert sizes["scroll"] <= sizes["client"], sizes
    context.close()


def test_the_page_refuses_to_run_inside_a_frame(browser, tmp_path):
    outer = Path(tmp_path) / "outer.html"
    outer.write_text(f'<!doctype html><iframe id="f" src="{PAGE_URL}" width="600" height="400"></iframe>', encoding="utf-8")
    context = browser.new_context()
    page = context.new_page()
    page.goto(outer.as_uri())
    page.wait_for_timeout(300)
    assert "không chạy trong khung nhúng" in page.frame_locator("#f").locator("html").inner_text()
    assert page.frame_locator("#f").locator("#refresh").count() == 0
    context.close()


def test_the_content_security_policy_really_blocks_injected_script(ui):
    ui.evaluate("""() => { const s = document.createElement('script'); s.textContent = 'window.__ran = 1'; document.body.append(s); }""")
    assert ui.evaluate("window.__ran") is None                                           # the hash allows our script and nothing else
    ui.evaluate("() => { fetch('https://example.com/x').catch(() => { window.__blocked = true; }); }")
    wait(ui, "window.__blocked === true")
    assert not [u for u in ui.seen if "example.com" in u]


def test_the_page_can_be_used_from_the_keyboard(ui):
    ui.focus("#add-repo")
    ui.keyboard.press("Shift+Tab")
    assert ui.evaluate("document.activeElement.tagName") in ("SELECT", "INPUT", "BUTTON")
    summary = ui.locator("details.wf summary >> nth=0")
    summary.focus()
    ui.keyboard.press("Enter")
    assert ui.evaluate("document.querySelector('details.wf').open") is True
    assert ui.evaluate("document.activeElement.tagName") == "SUMMARY"                  # a refresh does not take the focus away
    ui.click("#refresh")
    ui.wait_for_timeout(600)
    assert ui.evaluate("document.querySelector('details.wf').open") is True
