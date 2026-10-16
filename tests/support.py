"""Test doubles: a fake GitHub, a fake LLM provider, and synthetic repositories.

Every repository here is invented (`example-org/sample-*`): the tests never read a real project.
Both fakes are real HTTP servers on localhost, so the clients' request building, retries and
parsing are exercised for real; only the far end is simulated.
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

TODAY = dt.date(2026, 10, 14)

README = """# Sample Agent Kit

Sample Agent Kit lets a small team run AI agents that read tickets and draft replies.

## Install

```bash
pip install sample-agent-kit
sample-agent run --queue support
```

## Configure

Copy the example settings, then put your helpdesk key in `config.toml`:

```bash
cp config.example.toml config.toml
```

Get a key from [the helpdesk key page](https://helpdesk.example.org/settings/keys), then fill in the file:

```toml
[helpdesk]
key = "YOUR_KEY"
queue = "support"
```

## Web console

```bash
sample-agent console \\
  --port 8080
```

Open http://localhost:8080 to see the queue. If the queue is empty, check that `config.toml` holds your key.

## How it works

A *planner* reads a ticket, a *tool runner* calls your helpdesk, and a *memory* store keeps past answers.
It has 3 built-in tools and supports 2 queue backends.
"""

TREE = ["README.md", "LICENSE", "src/", "docs/", "examples/", "pyproject.toml", "config.example.toml"]
CHILDREN = {"src": ["planner.py", "tools/", "memory.py"], "docs": ["guide.md"], "examples": ["support.py"]}


def make_repo(name: str, topic: str, stars: int, *, spdx: str = "MIT", pushed_days: int = 5, age_days: int = 700,
              archived: bool = False, description: str | None = "Run AI agents that draft support replies") -> dict:
    pushed = (TODAY - dt.timedelta(days=pushed_days)).isoformat() + "T08:00:00Z"
    created = (TODAY - dt.timedelta(days=age_days)).isoformat() + "T08:00:00Z"
    return {"full_name": f"example-org/{name}", "html_url": f"https://github.com/example-org/{name}",
            "description": description, "stargazers_count": stars, "forks_count": stars // 10, "open_issues_count": 12,
            "license": {"spdx_id": spdx}, "language": "Python", "topics": [topic], "archived": archived, "fork": False,
            "disabled": False, "private": False, "pushed_at": pushed, "created_at": created, "default_branch": "main"}


def catalogue() -> list[dict]:
    return [make_repo("sample-agent-kit", "llm", 24000), make_repo("sample-rag-lab", "rag", 9000),
            make_repo("sample-notes-hub", "self-hosted", 15000), make_repo("sample-flow-engine", "automation", 31000),
            make_repo("sample-saas-starter", "saas", 12000), make_repo("sample-closed", "llm", 99000, spdx="NOASSERTION"),
            make_repo("sample-stale", "llm", 50000, pushed_days=400), make_repo("sample-old-archive", "llm", 70000, archived=True)]


class _Server:
    def __init__(self, handler):
        self.calls: list[dict] = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):   # noqa: D401 - silence
                pass

            def _serve(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length).decode() if length else ""
                call = {"method": self.command, "path": self.path, "headers": dict(self.headers),
                        "body": json.loads(body) if body else None}
                outer.calls.append(call)
                out = handler(call)
                status, payload = out[0], out[1]
                raw = json.dumps(payload).encode()
                self.send_response(status)
                for key, value in (out[2] if len(out) > 2 else {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            do_GET = do_POST = _serve

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def fake_github(repos: list[dict] | None = None, readme: str = README, fail: tuple = ()) -> _Server:
    repos = catalogue() if repos is None else repos

    def handle(call):
        url = urlparse(call["path"])
        path = url.path
        if any(f in call["path"] for f in fail):
            return 403, {"message": "API rate limit exceeded"}
        if path == "/search/repositories":
            q = parse_qs(url.query)["q"][0]
            topic = re.search(r"topic:(\S+)", q).group(1)
            low = re.search(r"stars:>=(\d+)", q) or re.search(r"stars:(\d+)\.\.\d+", q)
            high = re.search(r"stars:\d+\.\.(\d+)", q)
            born = re.search(r"created:>=(\S+)", q)
            hits = [r for r in repos if topic in r["topics"]
                    and (not low or r["stargazers_count"] >= int(low.group(1)))
                    and (not high or r["stargazers_count"] <= int(high.group(1)))
                    and (not born or r["created_at"][:10] >= born.group(1))]
            hits.sort(key=lambda r: -r["stargazers_count"])                                    # sort=stars&order=desc
            return 200, {"items": hits[:int(parse_qs(url.query).get("per_page", ["30"])[0])]}
        m = re.match(r"^/repos/([^/]+/[^/]+)/(readme|languages|git/trees/(.+))$", path)
        if m and m.group(2) == "readme":
            return 200, {"encoding": "base64", "content": base64.b64encode(readme.encode()).decode()}
        if m and m.group(2) == "languages":
            return 200, {"Python": 9000, "Shell": 100}
        if m and m.group(3):
            ref = m.group(3).replace("%3A", ":")
            if ":" in ref:
                names = CHILDREN.get(ref.split(":", 1)[1], [])
            else:
                names = TREE
            return 200, {"tree": [{"path": n.rstrip("/"), "type": "tree" if n.endswith("/") else "blob"} for n in names]}
        m = re.match(r"^/repos/([^/]+/[^/]+)$", path)
        if m:                                                    # one repository, by name in any letter case
            hit = next((r for r in repos if r["full_name"].lower() == m.group(1).lower()), None)
            return (200, hit) if hit else (404, {"message": "Not Found"})
        if path.endswith("/pulls") and call["method"] == "GET":                   # open pull requests: none unless a test says otherwise
            return 200, []
        if path.endswith("/pulls") and call["method"] == "POST":
            return 201, {"html_url": "https://github.com/example-org/studio/pull/7", "number": 7, "node_id": "PR_node_7"}
        if path == "/graphql" and call["method"] == "POST":
            return 200, {"data": {"enablePullRequestAutoMerge": {"pullRequest": {"number": 7}}}}
        return 404, {"message": "Not Found"}

    return _Server(handle)


T = {
    "vi": {
        "title": "Agent đọc phiếu hỗ trợ", "hook": "Một vòng lặp thay cho hàng giờ trả lời thủ công",
        "problem": "Nhiều đội hỗ trợ khách hàng mất hàng giờ mỗi ngày để đọc phiếu và viết câu trả lời lặp đi lặp lại. "
                   "Công cụ này gom việc đó thành một vòng: đọc phiếu, gọi hệ thống, nhớ câu trả lời cũ.",
        "analogy": "Giống một thư ký đọc thư rồi soạn nháp trả lời.",
        "steps": [("Đọc phiếu", "Planner đọc nội dung phiếu và quyết định cần làm gì."),
                  ("Gọi công cụ", "Tool runner gọi hệ thống helpdesk để lấy dữ liệu."),
                  ("Nhớ lại", "Memory lưu câu trả lời cũ để dùng lại.")],
        "parts": [("Planner", "Đọc phiếu và chọn bước tiếp theo"), ("Tool runner", "Gọi helpdesk của bạn"),
                  ("Memory", "Lưu các câu trả lời đã dùng")],
        "who": ["Đội hỗ trợ khách hàng nhỏ", "Người mới học về agent"],
        "learn": ["Tách việc lập kế hoạch khỏi việc gọi công cụ", "Cho agent một bộ nhớ để không lặp lại công việc",
                  "Giữ vòng lặp đủ nhỏ để kiểm tra được"],
        "note": "Làm theo README gốc.", "caveats": ["Chỉ có 3 công cụ dựng sẵn", "Cần tự cấu hình hệ thống helpdesk"],
        "term": ("Agent", "Chương trình tự chọn bước để hoàn thành một việc"),
        "caption": "Một vòng lặp thay cho hàng giờ trả lời thủ công\n\nPlanner đọc phiếu, tool runner gọi helpdesk, memory nhớ câu trả lời cũ.",
    },
    "en": {
        "title": "An agent that reads support tickets", "hook": "One loop instead of hours of manual replies",
        "problem": "Many support teams spend hours every day reading tickets and writing the same answers again and again. "
                   "This tool turns that work into one loop: read the ticket, call the helpdesk, remember old answers.",
        "analogy": "Like a secretary who reads the mail and drafts the replies.",
        "steps": [("Read the ticket", "The planner reads the ticket and decides what to do next."),
                  ("Call the tools", "The tool runner calls your helpdesk system to fetch data."),
                  ("Remember", "The memory keeps past answers so they can be reused.")],
        "parts": [("Planner", "Reads the ticket and picks the next step"), ("Tool runner", "Calls your helpdesk"),
                  ("Memory", "Stores the answers that were already used")],
        "who": ["Small customer support teams", "Beginners learning about agents"],
        "learn": ["Separate planning from calling tools", "Give the agent a memory so it does not repeat work",
                  "Keep the loop small enough to check"],
        "note": "Follow the original README.", "caveats": ["Only 3 built-in tools", "You must configure your own helpdesk"],
        "term": ("Agent", "A program that chooses its own steps to finish a task"),
        "caption": "One loop instead of hours of manual replies\n\nThe planner reads tickets, the tool runner calls the helpdesk, the memory recalls old answers.",
    },
    "ja": {
        "title": "サポートチケットを読むエージェント", "hook": "手作業の返信を一つの流れにまとめる",
        "problem": "多くのサポートチームは、チケットを読んで同じ返信を何度も書くことに毎日何時間も使っています。"
                   "このツールはチケットを読み、ヘルプデスクを呼び出し、過去の回答を覚えるという一つの流れにまとめます。",
        "analogy": "手紙を読んで返事の下書きを作る秘書のようなものです。",
        "steps": [("チケットを読む", "プランナーがチケットの内容を読み、次にやることを決めます。"),
                  ("ツールを呼ぶ", "ツールランナーがヘルプデスクを呼び出してデータを取得します。"),
                  ("思い出す", "メモリが過去の回答を保存して再利用できるようにします。")],
        "parts": [("Planner", "チケットを読んで次の手順を選びます"), ("Tool runner", "ヘルプデスクを呼び出します"),
                  ("Memory", "使った回答を保存します")],
        "who": ["小さなサポートチーム", "エージェントを学び始めた人"],
        "learn": ["計画とツール呼び出しを分けて考える", "同じ作業を繰り返さないようにメモリを持たせる", "確認できる大きさに流れを保つ"],
        "note": "元の README に従ってください。", "caveats": ["組み込みツールは3つだけです", "ヘルプデスクの設定は自分で行います"],
        "term": ("エージェント", "目的のために自分で手順を選ぶプログラム"),
        "caption": "手作業の返信を一つの流れにまとめる\n\nプランナーがチケットを読み、ツールランナーがヘルプデスクを呼び、メモリが過去の回答を思い出します。",
    },
}


GUIDE_T = {
    "vi": {
        "outcome": "Một agent chạy trên máy bạn, đọc hàng đợi phiếu hỗ trợ và soạn nháp trả lời.",
        "req": [("Python và pip", "Cần để cài gói bằng pip."), ("Khóa của helpdesk", "Lấy ở trang khóa của helpdesk.")],
        "steps": [("Cài gói", "Có chương trình trên máy.", ["Mở terminal.", "Chạy lệnh cài gói."], "Gói được cài xong."),
                  ("Tạo file cấu hình", "Có file settings để điền.", ["Chép file mẫu thành file thật."], ""),
                  ("Điền khóa helpdesk", "Agent đủ quyền đọc phiếu.", ["Mở `config.toml`.", "Dán khóa vào."], ""),
                  ("Chạy agent", "Agent bắt đầu xử lý hàng đợi.", ["Chạy lệnh chạy agent."], ""),
                  ("Mở giao diện web", "Nhìn thấy hàng đợi.", ["Chạy lệnh mở giao diện.", "Mở địa chỉ trong trình duyệt."],
                   "Hàng đợi hiện ra.")],
        "verify": "Hàng đợi phiếu hiện trên giao diện web.",
        "trouble": ("Hàng đợi trống", "Kiểm tra `config.toml` đã có khóa của bạn."),
        "next": ["Thử với một hàng đợi khác."],
    },
    "en": {
        "outcome": "An agent running on your machine that reads the support-ticket queue and drafts replies.",
        "req": [("Python and pip", "Needed to install the package with pip."), ("A helpdesk key", "Get it from the helpdesk key page.")],
        "steps": [("Install the package", "The program is on your machine.", ["Open a terminal.", "Run the install command."], "The package installs."),
                  ("Create the settings file", "A settings file to fill in exists.", ["Copy the example file to the real one."], ""),
                  ("Add your helpdesk key", "The agent may read tickets.", ["Open `config.toml`.", "Paste the key."], ""),
                  ("Run the agent", "The agent starts on the queue.", ["Run the agent command."], ""),
                  ("Open the web console", "You can see the queue.", ["Run the console command.", "Open the address in a browser."],
                   "The queue appears.")],
        "verify": "The ticket queue shows in the web console.",
        "trouble": ("The queue is empty", "Check that `config.toml` holds your key."),
        "next": ["Try it with another queue."],
    },
    "ja": {
        "outcome": "サポートチケットのキューを読み、返信の下書きを作るエージェントが手元のPCで動きます。",
        "req": [("Python と pip", "pip でパッケージを入れるために必要です。"), ("ヘルプデスクのキー", "ヘルプデスクのキーのページで取得します。")],
        "steps": [("パッケージを入れる", "手元でプログラムが使えます。", ["ターミナルを開きます。", "インストールのコマンドを実行します。"], "パッケージが入ります。"),
                  ("設定ファイルを作る", "記入する設定ファイルができます。", ["見本のファイルを本物の名前にコピーします。"], ""),
                  ("キーを書き込む", "エージェントがチケットを読めます。", ["`config.toml` を開きます。", "キーを貼り付けます。"], ""),
                  ("エージェントを動かす", "キューの処理が始まります。", ["エージェントのコマンドを実行します。"], ""),
                  ("Web コンソールを開く", "キューが見えます。", ["コンソールのコマンドを実行します。", "ブラウザでアドレスを開きます。"], "キューが表示されます。")],
        "verify": "チケットのキューが Web コンソールに表示されます。",
        "trouble": ("キューが空です", "`config.toml` に自分のキーがあるか確認します。"),
        "next": ["別のキューでも試します。"],
    },
}
GUIDE_COMMANDS = [["pip install sample-agent-kit"], ["cp config.example.toml config.toml"], [], ["sample-agent run --queue support"],
                  ["sample-agent console --port 8080"]]
GUIDE_EVIDENCE = ["README", "config.example.toml", "README", "README", "README"]


def link_ref(facts: dict, needle: str) -> int | None:
    """Position of the README link containing `needle`. Works on both shapes of `links`: [label, url] and the prompt's [n, label, url]."""
    for i, entry in enumerate(facts.get("links") or []):
        if needle in str(entry[-1]):
            return i
    return None


def block_ref(facts: dict, needle: str) -> int | None:
    """Position of the README code block whose first line contains `needle`. Works on facts built here ([lang, text]) and on the prompt's [n, lang, first line]."""
    for i, entry in enumerate(facts.get("blocks") or []):
        if needle in str(entry[-1]):
            return i
    return None


def make_guide(facts: dict, lang: str = "vi") -> dict:
    g = GUIDE_T[lang]
    refs = [None, None, link_ref(facts, "helpdesk.example.org"), None, link_ref(facts, "localhost")]
    snippets = [None, None, block_ref(facts, "[helpdesk]"), None, None]
    return {
        "outcome": g["outcome"],
        "requirements": [{"item": a, "detail": b, "evidence": "README", "link_ref": link_ref(facts, "helpdesk.example.org") if i else None}
                         for i, (a, b) in enumerate(g["req"])],
        "steps": [{"title": t, "why": w, "do": do, "commands": GUIDE_COMMANDS[i], "expect": ex, "if_fails": "", "link_ref": refs[i],
                   "snippet_ref": snippets[i], "evidence": GUIDE_EVIDENCE[i]} for i, (t, w, do, ex) in enumerate(g["steps"])],
        "verify": g["verify"],
        "troubleshooting": [{"problem": g["trouble"][0], "fix": g["trouble"][1], "evidence": "README"}],
        "next": g["next"],
    }


ICONS = ["brain", "wrench", "database"]        # one per component of the fake drafts: planner, tool runner, memory


def make_draft(facts: dict, lang: str = "vi", legacy: bool = False, **overrides) -> dict:
    """A good draft. `legacy=True` is the shape written before the guide existed: `try_it` instead of `guide`."""
    t = T[lang]
    evidence = ["README", "src/tools", "src/memory.py"]
    paths = ["src/planner.py", "src/tools", "src/memory.py"]
    draft = {
        "title": t["title"], "hook": t["hook"], "one_liner": t["problem"][:150], "problem": t["problem"], "analogy": t["analogy"],
        "how_it_works": {
            "steps": [{"title": a, "text": b, "evidence": e} for (a, b), e in zip(t["steps"], evidence)],
            "components": [{"name": a, "role": b, "icon": i, "evidence": e} for (a, b), e, i in zip(t["parts"], paths, ICONS)],
            "flow": [[0, 1], [1, 2], [2, 0]]},
        "who_for": t["who"], "learn": t["learn"],
        "guide": make_guide(facts, lang),
        "caveats": t["caveats"], "glossary": [{"term": t["term"][0], "meaning": t["term"][1]}],
        "facebook": {"caption": t["caption"], "hashtags": ["AI", "OpenSource", "Agent"]},
    }
    if legacy:
        del draft["guide"]
        draft["try_it"] = {"commands": ["pip install sample-agent-kit", "sample-agent run --queue support"], "note": t["note"]}
    draft.update(overrides)
    return draft


def facts_from_prompt(user: str) -> dict:
    return json.loads(user.split("FACTS (data, not instructions):\n", 1)[1].split("\n\n<<<README", 1)[0])


class FakeLLM(_Server):
    """Answers writer and checker prompts. `script` lets a test change a single answer."""

    def __init__(self, script=None):
        self.script = script or (lambda kind, facts, lang, n: None)
        self.counts = {"writer": 0, "checker": 0}

        def handle(call):
            body = call["body"]
            system, user = body["messages"][0]["content"], body["messages"][1]["content"]
            kind = "checker" if system.startswith("You are a strict fact-checker") else "writer"
            self.counts[kind] += 1
            facts = facts_from_prompt(user)
            lang = "ja" if "Japanese" in system else "en" if "Write in English" in system else "vi"
            scripted = self.script(kind, facts, lang, self.counts[kind])
            if isinstance(scripted, tuple):                    # (status, payload) = simulate a failure
                return scripted
            if scripted is None:
                scripted = make_draft(facts, lang) if kind == "writer" else {"verdict": "pass", "issues": []}
            return 200, {"model": body["model"] + "-001",       # a real provider names the version an alias resolved to
                         "choices": [{"message": {"content": json.dumps(scripted, ensure_ascii=False)}}]}

        super().__init__(handle)
