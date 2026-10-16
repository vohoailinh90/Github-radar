"""What a reader needs from a long README: the sections that say how to do it, links to the places it names, its commands.

Everything here is arithmetic on text, never a model. A README is cut to a few thousand characters before it reaches a
model, and cutting the head off keeps the badges and the pitch while losing the install section that sits near the end
(crisng95/flowkit: character 8,220; a 28,000-character README whose Quick Start starts at 20,500). `select` keeps whole
sections, ranked by how much they help someone follow the project, and puts them back in their original order.
"""

from __future__ import annotations

import re
from bisect import bisect_right
from dataclasses import dataclass
from urllib.parse import urlsplit

FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")                # a code fence opens with three or more backticks or tildes
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")        # up to three spaces of indentation; four make a code block
SETEXT = re.compile(r"^ {0,3}(=+|-{3,})[ \t]*$")                 # the line under `Title`: === is level 1, --- is level 2
HTML_HEADING = re.compile(r"^\s*<h([1-6])\b[^>]{0,200}>(.{1,200}?)</h\1>\s*$", re.I)      # <h2 align="center">Install</h2>
NOT_TITLE = ("#", ">", "|", "-", "*", "+", "<", "`", "~", "!", "[")      # a line that starts like something else is not a Setext title
GAP = "[... other sections of the README omitted ...]"
INTRO_CHARS = 1800            # the opening (title and pitch) is always kept, up to this much
MIN_PART = 500                # a section that does not fit whole is kept in part only when at least this much room is left

# Words in a section title (English, Chinese, Japanese, Vietnamese). First matching rule decides; later sections without a
# match inherit the value of their parent, so "Run X" lifts "(1) Without prompt extension" under it.
RULES: list[tuple[int, str]] = [
    (-10, r"star history|stargazer|contribut|licen[cs]e|acknowledg|credits?\b|citation|cite\b|sponsor|donat|contact|changelog|"
          r"\bnews\b|roadmap|to-?do\b|table of contents|community|thanks|disclaimer|gallery|showcase|video demos?|demos?\b|"
          r"related projects?|authors?\b|backers|special thanks|star us|"
          r"特别感谢|感谢|反馈|许可证|授权|作品展示|界面预览|赞助|联系|贡献|更新日志|路线图|致谢|引用|"
          r"謝辞|ライセンス|スポンサー|お問い合わせ|ギャラリー|"
          r"giấy phép|liên hệ|đóng góp|lời cảm ơn"),
    (10, r"install|set-?up|quick ?start|getting started|get started|usage|how to (?:use|run)|\brun(?:ning)?\b|deploy|"
         r"prerequisite|requirement|environment|configur|\bconfig\b|settings|docker|clone|download|launch|start (?:the|up)|"
         r"build from|from source|first (?:run|steps)|"
         r"安装|安裝|部署|快速开始|快速開始|使用|配置|前提|环境|環境|启动|啟動|运行|運行|要求|下载|"
         r"インストール|使い方|使用方法|設定|セットアップ|クイックスタート|起動|実行|"
         r"cài đặt|bắt đầu|hướng dẫn|sử dụng|cấu hình|chạy"),
    (5, r"faq|troubleshoot|common (?:problems?|issues?|errors?)|known issues|tips|tutorial|example|workflow|cli\b|command|"
        r"\bapi\b|providers?|supported|models?\b|"
        r"常见问题|常見問題|示例|教程|命令|"
        r"よくある|トラブル|例\b|"
        r"câu hỏi|lỗi thường|ví dụ"),
    (2, r"feature|overview|introduction|about|what is|why\b|how it works|architecture|"
        r"功能|特性|简介|介绍|概述|"
        r"概要|特徴|機能|"
        r"tính năng|giới thiệu"),
]
COMMAND_WORDS = {"git", "pip", "pip3", "python", "python3", "py", "uv", "uvx", "npm", "npx", "pnpm", "yarn", "bun", "docker",
                 "docker-compose", "conda", "mamba", "cd", "cp", "mv", "mkdir", "curl", "wget", "huggingface-cli", "hf",
                 "modelscope", "apt", "apt-get", "brew", "winget", "choco", "bash", "sh", "make", "source", "export",
                 "set", "cargo", "go", "pipx", "poetry", "ollama", "ffmpeg", "streamlit", "torchrun", "chmod",
                 "dnf", "yum", "pacman", "apk", "zypper", "snap", "flatpak",
                 # shell basics and system tools
                 "ls", "cat", "echo", "rm", "touch", "tar", "unzip", "zip", "ssh", "scp", "rsync", "grep", "sed", "awk", "ln", "find",
                 "tee", "kill", "which", "pwd", "alias", "unset", "ulimit", "systemctl", "service", "journalctl", "crontab", "nano", "vim",
                 "nvidia-smi", "nvcc", "ldconfig", "ffprobe", "magick",
                 # languages and their package managers
                 "node", "nodejs", "deno", "java", "javac", "mvn", "gradle", "dotnet", "nuget", "php", "composer", "ruby", "gem", "bundle",
                 "rails", "rake", "mix", "iex", "swift", "flutter", "dart", "rustup", "rustc", "gcc", "g++", "clang", "cmake", "ninja",
                 "julia", "rscript", "sbt", "opam", "pytest", "tox", "nox", "ruff", "black", "mypy", "jupyter", "ipython", "virtualenv",
                 "pyenv", "nvm", "fnm", "volta", "corepack", "pdm", "hatch", "rye", "pixi", "accelerate", "deepspeed", "wandb",
                 # clouds, containers and hosting
                 "kubectl", "helm", "minikube", "terraform", "tofu", "pulumi", "ansible", "ansible-playbook", "vagrant", "podman", "nerdctl",
                 "aws", "az", "gcloud", "gsutil", "gh", "glab", "heroku", "vercel", "netlify", "firebase", "supabase", "flyctl", "wrangler",
                 # databases
                 "psql", "createdb", "pg_dump", "mysql", "mongosh", "redis-cli", "sqlite3"}
WRAPPERS = {"sudo", "doas", "time", "nohup", "exec", "command", "env", "nice", "xargs"}      # a command line may start with one of these before its program
WRAPPER_OPERANDS = {                                                 # the options of a wrapper that take the next word (`sudo -u postgres psql`)
    "sudo": {"-u", "-g", "-C", "-h", "-p", "-r", "-t", "-U", "-D", "-T", "--user", "--group", "--close-from", "--host", "--prompt", "--role",
             "--type", "--other-user", "--chdir", "--command-timeout"},
    "doas": {"-u", "-C", "-a"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"},
    "nice": {"-n", "--adjustment"},
    "time": {"-f", "-o", "--format", "--output"},
    "xargs": {"-a", "-d", "-E", "-I", "-L", "-n", "-P", "-s", "--arg-file", "--delimiter", "--max-args", "--max-lines", "--max-procs"},
    "exec": {"-a"}}
BAD_HOSTS = ("shields.io", "badgen.net", "star-history.com", "visitor-badge", "hits.seeyoufarcry")      # badges and counters
URL_CHARS = re.compile(r"https?://[A-Za-z0-9._~:/?#@!$&*+,;=%\-\[\]()]+")
MD_LINK = re.compile(r"\[([^\]\n]{1,120})\]\((https?://(?:[^\s()]|\([^\s()]*\))+)(?:\s+\"[^\"]*\")?\)")      # a target may hold pairs of parentheses
HTML_LINK = re.compile(r"<a\b[^>]{0,300}?href=[\"'](https?://[^\"'\s>]+)[\"'][^>]{0,300}>(.{0,200}?)</a>", re.I | re.S)
_URL_CHAR = r"(?:(?![,;]https?://)[^\s<>\"'`()\]])"            # any character of an address, but not the comma or semicolon that begins the next one
_URL_PIECE = r"(?:" + _URL_CHAR + r"|\(" + _URL_CHAR + r"*\))"      # a character, or a pair of parentheses with characters between: `Foo_(bar)`
BARE_URL = re.compile(r"https?://(?:\[[0-9A-Fa-f:.]+\]" + _URL_PIECE + r"*|" + _URL_PIECE + r"+)")      # `http://[::1]:8080/x` keeps its brackets
GLUED_URLS = re.compile(r"[,;]https?://")                        # `http://a:1,https://b`: two addresses with nothing between them, not one
LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "[::1]")
TRACKING = re.compile(r"[?&](?:utm_[a-z]+|aff|aff_id|affiliate|ref|referral|track_id|promo|campaign|source|from)=", re.I)


def fence_opens(line: str):
    """((fence, columns of indentation), info string) if `line` opens a fenced code block, else None. The fence is the whole run of
    backticks or tildes: a block opened with four closes only on a run of at least four of the same kind, so it can hold a
    three-backtick example. The opening line may be indented as deep as its list item makes it."""
    m = FENCE.match(line.rstrip("\r\n"))
    if not m or (m.group(1)[0] == "`" and "`" in m.group(2)):       # ```code``` inside a sentence is not a fence
        return None
    return (m.group(1), _width(line)), m.group(2).strip()


def fence_closes(line: str, fence) -> bool:
    """A closing fence is the same character, at least as long, alone on its line and at most three columns deeper than the opening
    one: four more make it a line of the code."""
    chars, indent = fence
    m = re.match(r"^[ \t]*(`{3,}|~{3,})[ \t]*$", line.rstrip("\r\n"))
    return bool(m) and m.group(1)[0] == chars[0] and len(m.group(1)) >= len(chars) and _width(line) <= indent + 3


def fence_step(line: str, fence):
    """(the fence still open after `line`, whether `line` is a fence line). Inside a block only a matching closing fence counts."""
    if fence is None:
        opened = fence_opens(line)
        return (opened[0], True) if opened else (None, False)
    return (None, True) if fence_closes(line, fence) else (fence, False)


@dataclass
class Section:
    level: int
    title: str
    lines: list[str]            # the heading line and its body, up to the next heading of any level
    value: int = 0

    @property
    def text(self) -> str:
        return "".join(self.lines)

    @property
    def size(self) -> int:
        return sum(len(x) for x in self.lines)


def _is_comment(line: str) -> bool:
    """Whether a line of a code block is only a comment: `#`, `//`, `::` (cmd) or `REM` in any case, with an `@` before it or not (`rem note`, `@REM note`)."""
    text = line.strip().lstrip("@").lstrip()                        # `@REM note`: the `@` only keeps cmd from echoing the line
    return text.startswith(("#", "//", "::")) or text.lower() == "rem" or text[:4].lower() == "rem "


def is_command_line(line: str) -> bool:
    """A line of a code block that a person types: a known program first (after an optional `$ `), not a comment."""
    text = re.sub(r"^\s*(?:[$>]\s+|PS [^>]*>\s*)", "", SHELL_PROMPT.sub("", line.strip())).strip()
    if not text or text.startswith(("#", "//", "<", "{", "}")):
        return False
    words = text.split()
    i, wrapper = 0, ""
    while i < len(words) - 1:                       # `sudo -E pip install x`, `FOO=1 make`: the program is the first word after them
        word = words[i]
        if word.lower() in WRAPPERS:
            wrapper = word.lower()
        elif re.fullmatch(r"[A-Za-z_]\w*=\S*", word):
            pass
        elif i and word.startswith("-"):
            if word in WRAPPER_OPERANDS.get(wrapper, ()) and i + 1 < len(words) - 1:
                i += 1                              # `sudo -u postgres psql`: this option takes the next word as its operand
        else:
            break
        i += 1
    first = words[i].lower().lstrip("./")
    return first in COMMAND_WORDS or words[i].startswith(("./", ".\\"))


COMMENT = re.compile(r"<!--.*?-->", re.S)
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)


def _uncomment(text: str) -> str:
    """The text without its HTML comments, a fenced code block excepted (what looks like a comment there is the code's). A comment
    that is never closed is left as it is: it would otherwise swallow the rest of the README."""
    lines = text.splitlines(keepends=True)
    last_close = max((i for i, line in enumerate(lines) if "-->" in line), default=-1)
    out, fence, hidden = [], None, False
    for i, line in enumerate(lines):
        if hidden:                                # inside a comment: dropped up to the line that closes it
            end = line.find("-->")
            if end < 0:
                continue
            hidden, line = False, line[end + 3:]
        fence, on_fence = fence_step(line, fence)
        if fence is not None or on_fence:
            out.append(line)
            continue
        line = COMMENT.sub("", line)
        start = line.find("<!--")
        if start >= 0 and i < last_close:         # a comment that goes on over the next lines
            line, hidden = line[:start], True       # what comes before it joins what comes after the closing `-->`
        out.append(line)
    return "".join(out)


def clean_markup(text: str) -> str:
    """The README without HTML comments, images and badges, and with runs of blank lines folded, everywhere except inside a fenced
    code block: a configuration file, a template or a command there is kept exactly as the README has it, because a guide prints it."""
    parts, run, fence = [], [], None
    def flush():
        chunk = IMG_TAG.sub("", IMAGE.sub("", "".join(run)))
        parts.append(re.sub(r"\n{3,}", "\n\n", chunk))
        run.clear()
    for line in _uncomment(text).splitlines(keepends=True):
        fence, on_fence = fence_step(line, fence)
        if fence is None and not on_fence:
            run.append(line)
        else:
            flush()
            parts.append(line)
    flush()
    return "".join(parts).strip()


def split_sections(text: str) -> list[Section]:
    """Sections in order. The first holds everything before the first heading (it may be empty). A heading is an ATX line
    (`## Install`), a Setext title (`Install` over `-------`) or a one-line HTML heading (`<h2>Install</h2>`). A `#` line inside a
    fenced code block is a comment of that code, not a heading."""
    sections = [Section(0, "", [])]
    fence = None
    for line in text.splitlines(keepends=True):
        fence, on_fence = fence_step(line, fence)
        outside = fence is None and not on_fence
        bare = line.rstrip("\r\n")
        head = HEADING.match(bare) if outside else None
        if head:
            sections.append(Section(len(head.group(1)), re.sub(r"[*_`]", "", head.group(2)).strip(), [line]))
            continue
        html = HTML_HEADING.match(bare) if outside else None
        if html:
            title = re.sub(r"<[^>]*>|[*_`]", "", html.group(2)).strip()
            sections.append(Section(int(html.group(1)), title, [line]))
            continue
        under = SETEXT.match(bare) if outside else None
        if under and len(sections[-1].lines) > (1 if sections[-1].level else 0):
            title = sections[-1].lines[-1]
            if title.strip() and not title.lstrip().startswith(NOT_TITLE) and not SETEXT.match(title.rstrip("\r\n")):
                sections[-1].lines.pop()
                sections.append(Section(1 if under.group(1).startswith("=") else 2, re.sub(r"[*_`]", "", title).strip(), [title, line]))
                continue
        sections[-1].lines.append(line)
    if not sections[0].lines:
        sections.pop(0)
    return sections


def rank(sections: list[Section]) -> None:
    """Set `value` on each section from its title; one that matches nothing takes its nearest ancestor's value, so the
    sub-steps of "Run X" are as useful as "Run X". Document order breaks ties, so the first run a README describes comes
    before the variations of it (a count of commands per section was tried and put the variations first)."""
    stack: list[tuple[int, int]] = []             # (level, value) of the open ancestors
    for sec in sections:
        own = next((v for v, pat in RULES if re.search(pat, sec.title.lower())), None)
        while stack and stack[-1][0] >= sec.level:
            stack.pop()
        if own is None:
            own = stack[-1][1] if stack else 0
        sec.value = own
        stack.append((sec.level, own))


def _head(lines: list[str], room: int) -> str:
    """The start of a section that fits in `room` characters, ending on a whole line and never inside a code block."""
    out, size, fence, fence_at = [], 0, None, None
    for line in lines:
        if size + len(line) > room:
            break
        before = fence
        fence, _ = fence_step(line, fence)
        if before is None and fence is not None:
            fence_at = len(out)                       # a code block opens here
        out.append(line)
        size += len(line)
    if fence is not None and fence_at is not None:
        out = out[:fence_at]
    return "".join(out).rstrip() + "\n"


def _assemble(keep: dict[int, str], count: int) -> str:
    out, prev = [], -1
    for i in sorted(keep):
        if i != prev + 1:
            out.append(GAP)
        out.append(keep[i])
        prev = i
    if prev != count - 1:
        out.append(GAP)
    return "\n\n".join(x.strip("\n") for x in out).strip()


def _cut(text: str, limit: int) -> str:
    """`text[:limit]`, without the code block it would leave open: half a command or a sample is worse than none."""
    cut, fence, at, pos = text[:limit], None, None, 0
    for line in cut.splitlines(keepends=True):
        before = fence
        fence, _ = fence_step(line, fence)
        if before is None and fence is not None:
            at = pos
        pos += len(line)
    return cut[:at] if fence is not None and at is not None else cut


def select(text: str, limit: int) -> str:
    """`text` itself when it fits; else its opening plus the most useful whole sections, in their original order, never more than
    `limit` characters (the gap markers and the blank lines between sections are counted)."""
    if len(text) <= limit:
        return text
    sections = split_sections(text)
    if len(sections) == 1:                        # no headings to choose between: the start of it, as before
        return _head(sections[0].lines, limit).strip() or _cut(text, limit)
    rank(sections)
    keep: dict[int, str] = {0: _head(sections[0].lines, min(INTRO_CHARS, limit))}   # the preamble, or the title section
    room = limit - len(keep[0])
    for i in sorted(range(1, len(sections)), key=lambda i: (-sections[i].value, i)):
        sec = sections[i]
        if sec.value < 0:
            continue
        need = sec.size + 1
        if need <= room:
            keep[i] = sec.text.rstrip() + "\n"
            room -= need
        elif room >= MIN_PART and sec.value >= 5:
            part = _head(sec.lines, room - len(GAP) - 2)
            keep[i] = part
            room -= len(part)
    result = _assemble(keep, len(sections))
    while len(result) > limit and len(keep) > 1:  # the markers and joins cost a little: drop the least useful kept section
        worst = min((i for i in keep if i), key=lambda i: (sections[i].value, -i))
        del keep[worst]
        result = _assemble(keep, len(sections))
    if len(result) > limit:                       # only the opening is left and it still does not fit
        keep[0] = _head(sections[0].lines, max(0, limit - len(GAP) - 2))
        result = _assemble(keep, len(sections))
    return _cut(result, limit)


def clean_label(text: str, url: str) -> str:
    """Link text as a single plain line: no markdown, HTML or brackets that could change how it renders (also when it is the host)."""
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"\s+", " ", re.sub(r"[\[\]()<>`*_|\\]", "", text)).strip()
    if not text:
        text = re.sub(r"[\[\]()<>`*_|\\]", "", re.sub(r"^https?://", "", url).split("/")[0])
    return text[:60]


def _split(url: str):
    """`urlsplit`, or None when the address cannot be parsed: a README placeholder such as `http://[HOST]:8080` raises ValueError."""
    try:
        parts = urlsplit(url)
        parts.hostname                           # a bracketed host is validated here too
        return parts
    except ValueError:
        return None


def _balanced(text: str) -> bool:
    """Every closing parenthesis closes an opening one and none stays open."""
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def url_ok(url: str) -> bool:
    if len(url) > 200 or not URL_CHARS.fullmatch(url) or GLUED_URLS.search(url) or not _balanced(url):
        return False
    parts = _split(url)
    if parts is None:
        return False
    host = (parts.hostname or "").lower()
    # no `user@` part: `http://127.0.0.1@evil.example/` goes to evil.example
    return bool(host) and parts.username is None and not host.startswith("img.") and not any(bad in host for bad in BAD_HOSTS)


MAX_SCAN = 200_000            # characters of README `links` and `blocks` look at (the pipeline passes far less: readme_max_chars)


def _value_at(text: str):
    """pos -> the value of the section that holds that position, by bisection over the section ends."""
    sections = split_sections(text)
    rank(sections)
    ends, total = [], 0
    for sec in sections:
        total += len(sec.text)
        ends.append(total)
    return lambda pos: sections[min(bisect_right(ends, pos), len(sections) - 1)].value if sections else 0


def links(text: str, limit: int = 40) -> list[list[str]]:
    """[[label, url], ...] for the http(s) links and addresses the README shows, without repeats. The model never writes a URL:
    it points at an entry by number and the renderer prints it. Anything that is not a plain http(s) address made of ordinary
    characters is left out, and so is anything with a tracking or affiliate parameter. Links in the sections about installing,
    configuring and running come first, so a long list of vendors in a features section cannot push out the page that says where
    to get a key; within a kind, README order."""
    text = text[:MAX_SCAN]
    found: list[tuple[int, str, str]] = []
    for m in MD_LINK.finditer(text):
        found.append((m.start(), m.group(2), m.group(1)))
    for m in HTML_LINK.finditer(text):
        found.append((m.start(), m.group(1), m.group(2)))
    for m in BARE_URL.finditer(text):
        if text[m.end():m.end() + 1] != "(":      # an address that stops at a parenthesis which never closes is cut short, not whole
            found.append((m.start(), m.group(0).rstrip(".,;:!?"), ""))
    value_at = _value_at(text)
    ranked, seen = [], set()
    for pos, url, label in sorted(found, key=lambda x: x[0]):
        if url in seen or not url_ok(url) or TRACKING.search(url):
            continue
        seen.add(url)
        ranked.append((-value_at(pos), pos, [clean_label(label, url), url]))
    return [item for _, _, item in sorted(ranked, key=lambda x: (x[0], x[1]))[:limit]]


def is_local(url: str) -> bool:
    """True for an address on this machine: the host is exactly localhost, 127.0.0.1, 0.0.0.0 or [::1] (not `localhost.example.org`)."""
    parts = _split(url)
    return parts is not None and (parts.hostname or "").lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1")


SHELL_LANGS = {"bash", "sh", "shell", "zsh", "fish", "ksh", "dash", "ash", "powershell", "pwsh", "ps1", "cmd", "bat", "batch"}      # every line is something to type
CONSOLE_LANGS = {"console", "shell-session", "terminal"}                                       # a transcript: only a line after a prompt is typed
POSIX_PROMPT = r"(?:\[[\w.+-]+@[\w.-]+[^\]\n]*\]|[\w.+-]+@[\w.-]+(?::[^\s$#]*)?)[ \t]?[$#]\s+"      # `user@host:~$ `, `[me@box ~]$ `, `root@host:/# `
_NOT_A_FILE = "(?i:" + "".join(f"(?<!\\.{ext})" for ext in ("exe", "bat", "cmd", "com", "ps1", "py", "sh", "js")) + ")"        # `run.exe>out`: a file, not a folder
CMD_PROMPT = (r"[A-Za-z]:\\(?:[^>\r\n]*[^\s>])?(?<![ \t]\d)(?<!&)"
              r"(?:>(?:\s+|$)|" + _NOT_A_FILE + r">(?=[^\s>]))")      # `C:\Users\me> dir`, `C:\test>dir /x`; a space before the `>` or `run.exe>out` is a redirection
VENV = r"(?:\([^()\r\n]{1,40}\)\s+)?"                                  # `(venv) `, `(.venv) `, `(base) `: the environment a shell prompt starts with
PROMPT = re.compile(r"^(?:[$>]\s+|PS [^>]*>\s*|" + VENV + r"(?:\$\s+|" + POSIX_PROMPT + ")|" + CMD_PROMPT + ")")      # a prompt in a transcript (`console`): `$ `, `> `, `PS C:\\>`, the two above
SHELL_PROMPT = re.compile(r"^(?:\$\s+|PS [^>]*>\s*|" + VENV + r"(?:\$\s+|" + POSIX_PROMPT + ")|" + CMD_PROMPT + ")")   # a prompt in any other block: `> file` there is a redirection, a command


TAB_STOP = 4


def _width(line: str) -> int:
    """The columns of leading whitespace of a line, a tab running to the next tab stop."""
    col = 0
    for ch in line:
        if ch == " ":
            col += 1
        elif ch == "\t":
            col += TAB_STOP - col % TAB_STOP
        else:
            break
    return col


def _drop_columns(line: str, count: int) -> str:
    """The line without its first `count` columns of leading whitespace (a tab cut in two leaves its remainder as spaces)."""
    col, i = 0, 0
    while i < len(line) and col < count:
        if line[i] == " ":
            col += 1
        elif line[i] == "\t":
            wide = TAB_STOP - col % TAB_STOP
            if col + wide > count:
                return " " * (col + wide - count) + line[i + 1:]
            col += wide
        else:
            break
        i += 1
    return line[i:]


def dedent(lines: list[str]) -> list[str]:
    """The lines without the indentation they all share (the Markdown container's), counted in columns so that a tab and
    spaces which draw the same margin are the same margin; a blank line has no indentation to give, it becomes empty."""
    margin = min((_width(line) for line in lines if line.strip()), default=0)
    return [_drop_columns(line, margin) if line.strip() else "" for line in lines]


POWERSHELL_LANGS = {"powershell", "pwsh", "ps1"}                                   # a backtick at the end of a line continues it
CMD_LANGS = {"cmd", "bat", "batch"}                                        # a caret at the end of a line continues it
POWERSHELL_PROMPT = re.compile(r"^\s*PS [^>]*>")
DRIVE_ROOT = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:\\$")            # `cd C:\`: the root of a drive, not a line continued


def _comment_at(line: str, i: int) -> bool:
    """True when the `#` at `line[i]` starts a shell comment: it is the first character of a word, so it follows whitespace, a control
    operator (`echo hi;# note`) or a parenthesis, or the start of the line. `a#b`, `$#` and `${#x}` are not comments."""
    if line[i] != "#":
        return False
    if i == 0 or line[i - 1].isspace():
        return True
    slashes = len(line[:i - 1]) - len(line[:i - 1].rstrip("\\"))
    return line[i - 1] in ";&|()" and slashes % 2 == 0                # `echo a\;# b`: the `;` is escaped, so it is part of a word


def _shell_word(line: str, i: int) -> tuple[str, int]:
    """(the word that starts at `i` with its quotes and backslashes removed, where it ends): a word is made of plain characters and
    'single', "double" and backslash-escaped pieces, and ends at whitespace or one of `; & | < > ( )` outside quotes (`E\\OF`, `'E'OF`, `END-MARK`)."""
    word, quote = "", ""
    while i < len(line):
        ch = line[i]
        if quote:
            if ch == quote:
                quote = ""
            elif ch == "\\" and quote == '"' and line[i + 1:i + 2] and line[i + 1] in '$`"\\':
                i += 1                                  # in "double quotes" a backslash goes only before $ ` " and a backslash: `"E\OF"` is `E\OF`
                word += line[i]
            else:
                word += ch
        elif ch in "'\"":
            quote = ch
        elif ch == "\\" and i + 1 < len(line):
            i += 1
            word += line[i]
        elif ch.isspace() or ch in ";&|<>()":
            break
        else:
            word += ch
        i += 1
    return word, i

HEREDOC_LANGS = {"", "bash", "sh", "shell", "zsh", "ksh", "dash", "ash"} | CONSOLE_LANGS          # fish has no heredoc


def _continues(lang: str, line: str, physical: str | None = None) -> bool:
    """True when the line goes on in the next one, by the mark of its shell: a backslash (not the end of a Windows path such as
    `cd C:\\`), a backtick in PowerShell or a line after a PowerShell prompt, a caret in `cmd`, `bat` or after a cmd prompt. `line` is
    the command so far (its start tells the shell) and `physical` the line as written: the mark must be its very last character, a
    space after it escapes the space and the line ends there."""
    physical = line if physical is None else physical
    if lang in POWERSHELL_LANGS or POWERSHELL_PROMPT.match(line):
        return re.search(r"(?<!`)`$", physical) is not None and not _has_comment(physical)
    if lang in CMD_LANGS or re.match(CMD_PROMPT, line):
        return re.search(r"(?<!\^)\^$", physical) is not None
    quote, _, commented, _ = _shell_state(line)
    if commented or quote == "'":                 # `echo a # note \`: the backslash belongs to the comment; in 'single quotes' it is literal
        return False
    return (len(physical) - len(physical.rstrip("\\"))) % 2 == 1 and not DRIVE_ROOT.search(physical)       # `\\` at the end is an escaped backslash


def _has_comment(line: str) -> bool:
    """True when the line has a `#` that starts a shell comment (see `_comment_at`), outside quotes and not escaped."""
    quote, i = "", 0
    while i < len(line):
        ch = line[i]
        if quote:
            i += 2 if ch == "\\" and quote == '"' else 1
            quote = "" if i <= len(line) and ch == quote else quote
        elif ch == "\\":
            i += 2
        elif ch in "'\"":
            quote, i = ch, i + 1
        elif _comment_at(line, i):
            return True
        else:
            i += 1
    return False


def strip_trailing_comment(line: str) -> str:
    """The line without a trailing ` # comment`: a `#` that follows whitespace and is followed by whitespace, outside quotes and not escaped
    (`export MESSAGE="hello # world"` keeps its `#`)."""
    quote, i = "", 0
    while i < len(line):
        ch = line[i]
        if quote:
            i += 2 if ch == "\\" and quote == '"' else 1
            quote = "" if i <= len(line) and ch == quote else quote
        elif ch == "\\":
            i += 2
        elif ch in "'\"":
            quote, i = ch, i + 1
        elif ch.isspace() and line[i + 1:i + 2] == "#" and (i + 2 >= len(line) or line[i + 2].isspace()):
            return line[:i].rstrip()
        else:
            i += 1
    return line


def _shell_state(text: str) -> tuple[str, int, bool, int]:
    """(the quote or backquote still open at the end, the parentheses still open, whether a `# comment` starts, where the code ends: at the
    comment or at the end of the line) for a POSIX shell command line."""
    quote, depth, backquote, i = "", 0, False, 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "`" and quote == '"':
                backquote = not backquote         # a backquoted substitution inside double quotes
            i += 2 if ch == "\\" and quote == '"' else 1
            quote = "" if i <= len(text) and ch == quote else quote
            continue
        if ch == "\\":
            i += 2
            continue
        if ch in "'\"":
            quote = ch
        elif ch == "`":
            run = len(text[i:]) - len(text[i:].lstrip("`"))
            if run >= 3:
                i += run                          # three or more: the residue of a Markdown fence, never a substitution
                continue
            backquote = not backquote             # `` `cmd` ``: a command substitution that may go on over several lines
        elif _comment_at(text, i):
            return "", 0, True, i                 # the rest of the line is the comment's: it opens and closes nothing
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        i += 1
    return quote or ("`" if backquote else ""), depth, False, len(text)


def _incomplete(command: str) -> bool:
    """True when the shell would ask for more of this command (and show its secondary prompt): it ends in `|`, `|&`, `&&` or `||`, or a quote
    or a parenthesis is still open; a comment opens and closes nothing. A command that is complete is followed by output, and `> ` there
    (npm prints `> pkg@1.0.0 start`) is not a prompt."""
    quote, depth, commented, _ = _shell_state(command)
    code = command.rstrip()
    return not commented and (bool(quote) or depth > 0 or (code.endswith(("|", "&&", "||", "|&")) and not code.endswith(">|")))     # `>|` is a redirection


def _closes_placeholder(code: str) -> bool:
    """Whether the `>` that ends the code closes a placeholder in angle brackets (`<repo-url>`, `<your folder>`): it touches the word before
    it, and the last `<` that touches the character after it has no `>` between it and this one. A `<` or `>` with a space after or before it, as in
    `cat < input >`, is a redirection and says nothing about a placeholder."""
    if not code.endswith(">") or len(code) < 2 or code[-2].isspace() or code[-2] in "<>&|":
        return False
    opens = [m.start() for m in re.finditer(r"(?<![<>&])<(?=[^\s<>])", code)]                  # `<user>@<server>`: a placeholder may sit inside a word
    return bool(opens) and ">" not in code[opens[-1] + 1:-1]


def _ends_in_redirection(command: str) -> bool:
    """True when the code of a POSIX command line (a trailing comment cut off) ends in a redirection operator with no word after it
    (`echo hi >`, `cat <`, `cmd >>`, `echo hi >&`, `exec 3<>`, `cmd &>`): the shell reports a syntax error and does not go on in the next line. A placeholder in angle
    brackets (`git clone <repo-url>`, `cd <your folder>`) is not one: its `>` closes a `<`."""
    quote, _, _, end = _shell_state(command)
    code = command[:end].rstrip()
    found = re.search(r"(\\*)((?:\d+|&)?(?:>>|>&|>\||<>|<&|<<<|<<-|<<|>|<))$", code)
    if quote or not found or len(found.group(1)) % 2:
        return False
    return found.group(2) != ">" or not _closes_placeholder(code)                # a lone `>` may close a `<url>` placeholder


GRAMMAR_LOOKAHEAD = 20            # lines after an unfinished command in which the rest of it has to come


def _piece(lang: str, line: str, command: str = "") -> str:
    """A physical line as it joins the command before it: without its margin and, in a transcript or after a command that was typed at a
    prompt (`$ docker run \\` over `> --rm image` in a `bash` fence), without the secondary prompt (`> `, PowerShell's `>> `, cmd's `More? `)."""
    piece = line.strip()
    if lang in CONSOLE_LANGS or SHELL_PROMPT.match(command):
        return PROMPT.sub("", re.sub(r"^(?:>>|More\?)\s+", "", piece))
    return piece


def _is_powershell(lang: str, command: str) -> bool:
    return lang in POWERSHELL_LANGS or bool(POWERSHELL_PROMPT.match(command))


PS_WORD_OPERATORS = ("and", "or", "xor", "eq", "ne", "gt", "ge", "lt", "le", "like", "notlike", "match", "notmatch", "contains", "notcontains",
                     "in", "notin", "is", "isnot", "as", "join", "split", "replace", "band", "bor", "bxor", "shl", "shr")      # `-f` is also the abbreviation of `-Force`: not here
PS_EXPRESSION = re.compile(r"^\s*(?:\$|\(|\[|\d|['\"])")                  # a statement that starts like an expression, not with a command name
PS_OPERAND_THEN_OPERATOR = re.compile(r"(?:\$[\w:.]+|\b\d[\w.]*|[)\]}'\"])\s+[-*/%]$")     # `$x = 4 -`: an operand and then a binary operator


def _ps_continues(code: str, last: str) -> bool:
    """Whether the code of a PowerShell line, which ends in the character `last`, ends in something that wants the next line: a pipe or a
    comma, an operator (`+`, `=`, a pipeline chain's `&&` and `||`, `-and`, `-eq`, `-join` ...), or `-`, `*`, `/`, `%` after an operand in
    a statement that is an expression (`$x = 4 -`). A wildcard or a path ends a command (`Get-ChildItem *`, `Copy-Item $src *`)."""
    code = code.rstrip()
    return (last in ("|", ",") or code.endswith(("&&", "||", "+", "=")) or bool(re.search(r"(?:^|\s)-(?:" + "|".join(PS_WORD_OPERATORS) + r")$", code, re.I))
            or bool(PS_EXPRESSION.match(code) and PS_OPERAND_THEN_OPERATOR.search(code)))


def _ps_state(text: str):
    """(brackets still open, whether the code ends in something that wants the next line (see `_ps_continues`), where the code ends: at a `# comment` or at the end of the line, the quote
    of a string that does not close on the line or "") for a PowerShell command line, or None when it cannot be told: a `<# block comment #>`
    or a here-string (`@"` at the end of a line), whose line breaks are part of the data."""
    stack, last, i = [], "", 0
    while i < len(text):
        ch = text[i]
        if text.startswith("<#", i):
            return None
        if ch == "#" and (i == 0 or text[i - 1].isspace() or text[i - 1] in ";|(){}[]&,"):          # a `#` that begins a token: `Write-Host hi;# note`
            return stack, _ps_continues(text[:i], last), i, ""
        if ch == "@" and text[i + 1:i + 2] in ("'", '"') and not text[i + 2:].strip():
            return None
        if ch in "'\"":
            end = i + 1
            while end < len(text):
                if ch == '"' and text[end] == "`":
                    end += 2
                elif text[end] == ch and text[end + 1:end + 2] == ch:
                    end += 2                           # a doubled quote is a quote inside the string
                elif text[end] == ch:
                    break
                else:
                    end += 1
            else:
                return stack, False, len(text), ch      # the string goes on in the next line
            i, last = end + 1, ch
            continue
        if ch == "`":
            i += 2
            continue
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}" and stack:
            stack.pop()
        if not ch.isspace():
            last = ch
        i += 1
    return stack, _ps_continues(text, last), len(text), ""


def _ps_open(text: str):
    """True when PowerShell would ask for more of the command (the code ends in `|` or `,`, a bracket is open, or a string is), False when
    it is complete, None when that cannot be told (see `_ps_state`). A comment is not code."""
    state = _ps_state(text)
    return None if state is None else bool(state[0]) or state[1] or bool(state[3])


def _ps_joiner(code: str, piece: str) -> str:
    """What joins the next line to the code of a PowerShell command that is not finished: a space after a pipe, a comma or an opening
    bracket, before a closing bracket and inside `[ ]`; `; ` between two statements inside `{ }` or `( )`, where a line break ends one."""
    state = _ps_state(code)
    stack = state[0] if state else []
    if (state and (state[1] or state[3])) or code.endswith(("(", "[", "{")) or piece[:1] in (")", "]", "}", "|") or not stack or stack[-1] == "[":
        return " "                                    # inside a string the line break is part of the string: a space stands for it
    return "; "


def _join(lang: str, text: str, line: str, glue) -> str:
    """The command so far and the next physical line as one logical line. `glue` is what a continuation mark leaves between them (see
    `_glue`), or None when the grammar of the shell, not a mark, joins them."""
    piece = _piece(lang, line, text)
    if glue is None:
        if _is_powershell(lang, text):
            state = _ps_state(text)
            code = text[:state[2]].rstrip() if state else text         # the comment at the end of the line before is dropped: the rest would be in it
            return code + _ps_joiner(code, piece) + piece
        return text + " " + piece
    return text + (glue if not line[:1].isspace() else " ") + piece


def _strip_ps_block_comments(lines: list[str]) -> list[str]:
    """The lines of a PowerShell block without its `<# ... #>` comments (one or several lines, outside strings, here-strings and `#` comments):
    everything from `<#` through `#>` is comment text, even a line that looks like a command. A line that is only comment is dropped; a
    comment that never closes runs to the end of the block. The lines of a here-string, up to the one that begins with its closing mark,
    are data and stay as they are."""
    out, inside, here_end = [], False, ""
    for line in lines:
        if here_end:
            out.append(line)
            if line.startswith(here_end):
                here_end = ""
            continue
        kept, i, quote = "", 0, ""
        while i < len(line):
            if inside:
                end = line.find("#>", i)
                if end < 0:
                    i = len(line)
                else:
                    inside, i = False, end + 2
                continue
            ch = line[i]
            if quote:
                if ch == "`" and quote == '"':
                    kept, i = kept + line[i:i + 2], i + 2
                    continue
                quote = "" if ch == quote else quote
            elif ch in "'\"":
                quote = ch
            elif line.startswith("<#", i):
                inside, i = True, i + 2
                continue
            elif ch == "#" and (i == 0 or line[i - 1].isspace() or line[i - 1] in ";|(){}[]&,"):
                kept, i = kept + line[i:], len(line)                           # a `#` comment: `<#` after it is part of it
                continue
            kept, i = kept + ch, i + 1
        if kept.strip() or not line.strip():
            out.append(kept.rstrip() if kept.strip() else kept)
        if not inside:                                                         # `@"` leaves a quote open at the end of the line: it is a here-string
            opens = _here_string_openers(kept)
            here_end = opens[0][0] if opens else ""
    return out


def _typed(lang: str, command: str) -> bool:
    """Whether a logical line of a code block is something a reader types, for the grammar of a shell to apply to it: a line of a block tagged
    as a shell, the lines after a prompt in a transcript, an untagged line that starts with a known program. The output of a transcript and
    the lines of a block in another language (a YAML or Python sample) are not."""
    if lang in CONSOLE_LANGS:
        return bool(PROMPT.match(command))
    if lang in SHELL_LANGS:
        return True
    return not lang and is_command_line(command)


COMPOUND_OPEN = {"if", "for", "while", "until", "case", "select"}      # a construct that goes on to its closing word, over several lines
COMPOUND_CLOSE = {"fi", "done", "esac"}
COMMAND_FOLLOWS = {"then", "do", "else", "elif", "if", "while", "until", "!", "{", "time", "and", "or", "not"}      # the word after one of these begins a command
FISH_OPEN = {"if", "for", "while", "function", "switch", "begin"}                                     # fish closes each of them with `end`
FISH_CLOSE = {"end"}


def _compound_depth(text: str, fish: bool = False) -> int:
    """How many compound commands of a POSIX shell are still open at the end of the text: `if`, `for`, `while`, `until`, `case` and `select`
    until `fi`, `done` or `esac`, and a `{ ... }` group (also the body of `name() {`); for fish `if`, `for`, `while`, `function`, `switch` and
    `begin` until `end`. A keyword counts where a command begins, outside quotes and comments, so `echo if`, `"fi"` and `${x}` are not
    keywords."""
    opens, closes = (FISH_OPEN, FISH_CLOSE) if fish else (COMPOUND_OPEN, COMPOUND_CLOSE)
    text = SHELL_PROMPT.sub("", text.lstrip(), count=1)
    depth, word, quote, command_start, i = 0, "", "", True, 0
    names, defining, name_before_paren, empty_parens, previous = 0, False, False, False, ""

    def end_word() -> None:
        nonlocal depth, word, command_start, names, defining, name_before_paren, previous
        if not word:
            return
        else_if = fish and word == "if" and previous == "else"          # fish: `else if` goes on the same block, it has no `end` of its own
        previous = word
        if command_start and (word in opens or (word == "{" and not fish)) and not else_if or defining and word == "{":
            depth += 1                                       # `function name {`, `name()` over `{`: the brace follows the head of the definition
            defining = False
        elif command_start and (word in closes or (word == "}" and not fish)):
            depth = max(0, depth - 1)
        elif defining and names:
            names -= 1                                       # the name after `function`
        else:
            defining = False
        if command_start and word == "function" and not fish:
            defining, names = True, 1
        name_before_paren = (not fish and command_start and bool(re.fullmatch(r"[A-Za-z_][\w:.-]*", word))
                             and word not in COMMAND_FOLLOWS | COMPOUND_OPEN)
        command_start = command_start and word in COMMAND_FOLLOWS
        word = ""

    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\" and quote == '"':
                word += "xx"
                i += 2
                continue
            quote = "" if ch == quote else quote
            word += "x"
        elif ch == "\\":
            word += "x"                                      # an escaped character is part of a word, never a keyword
            i += 2
            continue
        elif ch in "'\"":
            quote = ch
            word += "x"
        elif _comment_at(text, i):
            end_word()
            i = text.find("\n", i) if "\n" in text[i:] else len(text)
            continue
        elif ch.isspace() and ch != "\n":
            end_word()
        elif ch == "(":
            end_word()
            empty_parens = name_before_paren                 # `name(`: perhaps a function definition
            command_start = True
        elif ch == ")":
            end_word()
            if empty_parens and text[:i].rstrip().endswith("("):
                defining, names = True, 0                    # `name()`: the body follows, as `{` on this line or on the next
            command_start, empty_parens = True, False        # `a) cmd` in a `case`
        elif ch in "\n;&|":
            end_word()
            command_start, name_before_paren, empty_parens = True, False, False
            if ch != "\n":
                defining = False
        elif ch in "<>":
            end_word()
            command_start = False
        else:
            word += ch
        i += 1
    end_word()
    return depth + (1 if defining else 0)              # a definition whose body has not begun is open


def _cmd_depth(text: str) -> int:
    """How many parentheses of a batch (cmd) block are still open at the end of the text: `IF EXIST build (` over its commands and `)`. A
    parenthesis in double quotes or after the escape `^`, and a `REM` or `::` line, does not count; a `)` with nothing open counts for nothing."""
    depth = 0
    for line in text.splitlines():
        line = re.sub(CMD_PROMPT, "", line.lstrip(), count=1) if re.match(CMD_PROMPT, line.lstrip()) else line
        if _is_comment(line):
            continue
        quote, i = False, 0
        while i < len(line):
            ch = line[i]
            if ch == "^":
                i += 2
                continue
            if ch == '"':
                quote = not quote
            elif not quote and ch == "(":
                depth += 1
            elif not quote and ch == ")":
                depth = max(0, depth - 1)
            i += 1
    return depth


def _construct_open(lang: str, text: str) -> bool:
    """True when a construct that goes on over several lines is still open at the end of the text: a string (a quote of a POSIX shell, a
    PowerShell string), a parenthesis (a subshell, a command substitution) or a compound command of a POSIX shell (`if [ -d build ]; then`
    until `fi`). A line break inside one of these separates statements, so the lines are not joined with a space."""
    if lang in CMD_LANGS or re.match(CMD_PROMPT, text):
        return _cmd_depth(text) > 0
    if _is_powershell(lang, text):
        state = _ps_state(text)
        return bool(state and state[3])
    quote, parens, _, _ = _shell_state(text)
    return bool(quote) or parens > 0 or _compound_depth(text, lang == "fish") > 0


def _open_group(lang: str, command: str, following: list[str]) -> int:
    """How many of the next lines finish a construct that is open at the end of the command (`python -c "` over the script and `"`, `if ...;
    then` over its body and `fi`), 0 when it is not open or does not close within GRAMMAR_LOOKAHEAD lines. The line breaks, blank lines
    included, are part of it (a string's content, a script's statements), so the lines are kept apart as the data of the command, like the
    body of a heredoc, and not joined."""
    if not _typed(lang, command) or not _construct_open(lang, command):
        return 0
    text = command
    for n, line in enumerate(following[:GRAMMAR_LOOKAHEAD], 1):
        text += "\n" + _piece(lang, line, command)
        if not _construct_open(lang, text):
            return n
    return 0


def _grammar_open(lang: str, command: str, following: list[str]) -> bool:
    """True when the shell's grammar leaves the command unfinished (`printf foo |`; in PowerShell a pipe, a comma or an open bracket at the
    end of a line) and the next lines finish it within GRAMMAR_LOOKAHEAD lines, a blank line not crossed, so that the lines are one command.
    A string or a compound command left open is not joined (see `_open_group`): the line break is part of it."""
    if lang in CMD_LANGS or re.match(CMD_PROMPT, command) or _construct_open(lang, command):
        return False
    powershell = _is_powershell(lang, command)
    unfinished = _ps_open if powershell else _incomplete
    text = command
    if unfinished(text) is not True:
        return False
    for line in following[:GRAMMAR_LOOKAHEAD]:
        if not line.strip():
            return False
        text = _join(lang, text, line, None)
        if _construct_open(lang, text):
            return False
        state = unfinished(text)
        if state is None:
            return False
        if not state:
            return True
    return False


HERE_STRING_ENDS = ('"@', "'@")


def _here_string_openers(line: str) -> list[tuple[str, bool]]:
    """[(closing mark, False)] when a PowerShell line ends in the start of a here-string (`$x = @"`, `@'`) that is not inside a string or a
    comment: every line up to the one that begins with the mark (`"@`, which may be followed by more code) is data."""
    found = re.search(r"@(['\"])\s*$", line)
    if not found:
        return []
    state = _ps_state(line[:found.start()])
    return [(found.group(1) + "@", False)] if state and not state[3] and state[2] == found.start() else []


def _closes(line: str, end: tuple[str, bool]) -> bool:
    """Whether a line ends the heredoc or here-string that `end` (as `_heredoc_openers` gives it) belongs to."""
    word, dash = end
    if word in HERE_STRING_ENDS:
        return line.startswith(word)
    return (line.lstrip("\t") if dash else line) == word


def _unprompt(line: str) -> str:
    """A line of a transcript without its prompt: `$ `, `> `, PowerShell's `>> `, cmd's `More? `."""
    return PROMPT.sub("", re.sub(r"^(?:>>|More\?)\s+", "", line))


def _heredoc_ends(line: str) -> list[str]:
    """The words that end the heredocs a command line opens (`cat <<'EOF' > f` -> ["EOF"]); the lines after it are data until each."""
    return [word for word, _ in _heredoc_openers(line)]


def _heredoc_openers(line: str) -> list[tuple[str, bool]]:
    """(word that ends the heredoc, whether `<<-` lets leading tabs be dropped before it) for each heredoc a command line opens, and the
    closing mark of a PowerShell here-string it ends in (see `_here_string_openers`).
    A `<<` inside quotes, after a backslash, in a `# comment`, in `$(( ))` or `(( ))` arithmetic, or as `<<<` (a here-string) opens nothing."""
    ends, i, quote, arithmetic = [], 0, "", 0
    while i < len(line):
        ch = line[i]
        if quote:
            i += 2 if ch == "\\" and quote == '"' else 1
            quote = "" if i <= len(line) and ch == quote else quote
        elif arithmetic:                          # inside `$(( ))`: nothing opens a heredoc, a nested `$((` needs its own `))`
            if line.startswith("))", i):
                arithmetic, i = arithmetic - 1, i + 2
            elif line.startswith("$((", i):
                arithmetic, i = arithmetic + 1, i + 3
            else:
                i += 1
        elif ch == "\\":
            i += 2
        elif ch in "'\"":
            quote, i = ch, i + 1
        elif _comment_at(line, i):
            break
        elif line.startswith("$((", i) or (line.startswith("((", i) and (i == 0 or line[i - 1] in " \t;&|")):
            arithmetic, i = arithmetic + 1, i + (3 if line.startswith("$((", i) else 2)
        elif line.startswith("<<<", i):
            i += 3
        elif line.startswith("<<", i):
            dash = line.startswith("-", i + 2)
            start = i + 2 + dash
            while start < len(line) and line[start] in " \t":
                start += 1
            word, i = _shell_word(line, start)
            if word:
                ends.append((word, dash))
            i = max(i, start)
        else:
            i += 1
    return ends + _here_string_openers(line)


def _glue(lang: str, command: str) -> str:
    """What joins a command line that ends in its continuation mark to the line after it. A POSIX shell removes the backslash and the
    newline and nothing else, so `foo\\` over `bar` is `foobar`; a space before the mark, or one at the start of the next line, is the
    word break the reader sees. The other shells' marks are read as a word break."""
    if lang in POWERSHELL_LANGS or lang in CMD_LANGS or POWERSHELL_PROMPT.match(command) or re.match(CMD_PROMPT, command):
        return " "
    before = command[:-1]
    return "" if before and not before[-1].isspace() else " "


def _dangling(lang: str, command: str) -> bool:
    """True when a command line of a POSIX shell or PowerShell is left unfinished for good (`printf foo |`, a quote that never closes):
    the shell waits for more input, so it is not a command the README gives. Only what is typed counts: the output lines of a transcript and the
    lines of a block in another language (a sample with an apostrophe in it) are kept as they are."""
    typed = _typed(lang, command)
    if lang in CMD_LANGS or re.match(CMD_PROMPT, command):
        return typed and _cmd_depth(command) > 0
    if _is_powershell(lang, command):
        return typed and _ps_open(command) is True
    return typed and (_incomplete(command) or _ends_in_redirection(command) or _compound_depth(command, lang == "fish") > 0)


def _scan(text: str) -> list[tuple[str, list[str], list]]:
    """(language tag, logical lines, owners) of each fenced code block, in order; `owners[i]` is None for an ordinary line and, for a
    line of the body of a heredoc (its closing word included), the index of the line that opened it."""
    raw: list[tuple[str, list[str]]] = []
    fence, lang, lines = None, "", []
    for line in text.splitlines():
        before = fence
        fence, on_fence = fence_step(line, fence)
        if on_fence:
            if before is None:
                info = fence_opens(line)[1]
                lang, lines = (info.split(" ")[0].lower() if info else ""), []
            else:
                raw.append((lang, lines))
        elif fence is not None:
            lines.append(line)
    if fence is not None:                         # an unclosed block runs to the end of the README
        raw.append((lang, lines))
    blocks: list[tuple[str, list[str], list]] = []
    for lang, lines in raw:
        body = dedent(lines)
        if lang in POWERSHELL_LANGS:
            body = _strip_ps_block_comments(body)
        while body and not body[0].strip():       # blank lines at the start and end of a block are dropped
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        logical, owners, pending, ends, opener, glue, skip = [], [], "", [], None, " ", 0
        for index, line in enumerate(body):
            if skip:                              # a line of the string that the line before opened: it is in the logical lines already
                skip -= 1
                continue
            if ends:                              # inside a heredoc every line is data, a backslash at its end included
                logical.append(line.rstrip())
                owners.append(opener)
                prompted = lang in CONSOLE_LANGS or bool(SHELL_PROMPT.match(logical[opener]))
                bare = _unprompt(line) if prompted else line                           # a transcript shows `> ` before each line of the body
                if _closes(bare, ends[0]):        # the closing word alone on its line (`<<-`: after tabs); a here-string's mark begins its line
                    ends.pop(0)
                continue
            if not line.strip():                  # a blank line ends a pending continuation and is kept
                if pending:
                    logical.append(pending)
                    owners.append(None)
                    pending = ""
                logical.append("")
                owners.append(None)
                continue
            if pending:
                pending = _join(lang, pending, line, glue)             # `$ tool \` then `> --flag`: the shell's secondary prompt is not the command's
            else:
                pending = line.rstrip()
            if _continues(lang, pending, line):
                glue = _glue(lang, pending)
                pending = pending[:-1].rstrip()
                continue
            if _grammar_open(lang, pending, body[index + 1:]):         # `printf foo |` over `sed ...`
                glue = None
                continue
            lines_in_string = _open_group(lang, pending, body[index + 1:])
            if lines_in_string:                   # `python -c "` over its script and `"`, `if ...; then` over `fi`: the line breaks are data, like those of a heredoc
                logical.append(pending)
                owners.append(None)
                opener = len(logical) - 1
                for extra in body[index + 1:index + 1 + lines_in_string]:
                    logical.append(extra.rstrip())
                    owners.append(opener)
                skip, pending = lines_in_string, ""
                continue
            if _dangling(lang, pending):                              # the shell would wait for more input: not a command the README gives
                pending = ""
                continue
            logical.append(pending)
            owners.append(None)
            if lang in HEREDOC_LANGS:
                ends = _heredoc_openers(pending)
                opener = len(logical) - 1
            elif _is_powershell(lang, pending):
                ends = _here_string_openers(pending)
                opener = len(logical) - 1
            pending = ""
        # a block that ends on a continuation mark (`docker run \`) never gives the rest of the command: `pending` is dropped
        if ends:                                  # the block ends before the closing word: a command that waits for ever is not one the README gives
            del logical[opener:]
            del owners[opener:]
        blocks.append((lang, logical, owners))
    return blocks


def code_blocks(text: str) -> list[tuple[str, list[str]]]:
    """(language tag, logical lines) of each fenced code block, in order. A line ending in its shell's continuation mark is joined with
    the next (the padding of the continuation is dropped), except in the body of a heredoc, which is data. Everything else is kept as
    the README has it: the indentation of a line (a heredoc body, a YAML sample) and the blank lines between lines; only the
    indentation common to the whole block, which belongs to the Markdown container (a list item), is removed. Blank lines at the
    start and end of a block are dropped."""
    return [(lang, logical) for lang, logical, _ in _scan(text)]


NO_PROMPT = re.compile(r"(?!)")                 # matches nothing: a line with no prompt to drop
ROOT_PROMPT = re.compile(r"^#\s+")              # the prompt of root in a transcript: `# apt-get update`
SECONDARY_PROMPT = re.compile(r"^>\s+")         # what a shell shows when a command goes on over several lines


def transcript_prompts(lines: list[str], roles: list[str]) -> list:
    """For each logical line of a `console` transcript: the prompt pattern that precedes what was typed, or None when the line is output.
    `> ` is the prompt of a line typed in a transcript that has no other prompt; after a `$`-style prompt it is the shell's secondary
    prompt or output (npm prints `> pkg@1.0.0 start` after `$ npm start`), typed only inside a heredoc; the same after root's prompt.
    A bare `# ` is root's prompt when no `$`-style prompt came before and what follows is a command, otherwise a comment."""
    seen, rooted, out = False, False, []        # a `$`-style prompt came before / a root prompt came before
    for line, role in zip(lines, roles):
        if SHELL_PROMPT.match(line):
            seen = True
            out.append(PROMPT)
        elif SECONDARY_PROMPT.match(line):
            out.append(None if (seen or rooted) and role != "body" else PROMPT)
        elif not seen and ROOT_PROMPT.match(line) and is_command_line(ROOT_PROMPT.sub("", line, count=1)):
            rooted = True
            out.append(ROOT_PROMPT)
        else:
            out.append(None)
    return out


def block_lines(text: str) -> list[tuple[str, str, str, object]]:
    """(language tag, logical line, role, prompt) for every logical line of the README's code blocks. The role is "opener" for a line that
    opens a heredoc, "body" for a line of its body or its closing word, and "" for any other. The prompt is the pattern to drop from the
    line; in a transcript it is None for a line that was not typed."""
    out = []
    for lang, logical, owners in _scan(text):
        openers = {owner for owner in owners if owner is not None}
        roles = ["body" if owner is not None else "opener" if i in openers else "" for i, owner in enumerate(owners)]
        if lang in CONSOLE_LANGS:
            prompts = transcript_prompts(logical, roles)
        else:                                          # the data of a heredoc is data, but a prompted opener shows `> ` before each line of it
            prompts = [prompt_for(lang) if owner is None else PROMPT if SHELL_PROMPT.match(logical[owner]) else NO_PROMPT for owner in owners]
        out += [(lang, line, role, prompt) for line, role, prompt in zip(logical, roles, prompts)]
    return out


def heredocs(text: str) -> tuple[list[list[str]], list[str]]:
    """(groups, loose) for the README's code blocks. A group is a heredoc as [the line that opens it, its body lines..., the closing
    word]: a body line is not a command on its own, the whole group is what a reader types. `loose` is every other logical line."""
    groups: list[list[str]] = []
    loose: list[str] = []
    for _, logical, owners in _scan(text):
        by_opener: dict[int, list[str]] = {}
        for line, owner in zip(logical, owners):
            if owner is None:
                loose.append(line)
            else:
                by_opener.setdefault(owner, [logical[owner]]).append(line)
        groups += by_opener.values()
    return groups, loose


def heredoc_data(commands, shells=None) -> list[bool]:
    """For each entry of a list of command lines: whether it is data of a heredoc, a PowerShell here-string, a string that goes on over
    several lines or a compound command (`if ...; then` over its body and `fi`), that is its body, its closing word, the lines that finish
    it, so that it is printed as it is. `shells` says which shell the commands are for, to read a string with that shell's rules: a name
    ("powershell") for all of them, or {comparable form of a command: shell} as `shells()` gives it."""
    flags, ends, text_so_far, shell = [], [], None, ""
    for command in commands if isinstance(commands, (list, tuple)) else []:
        text = command if isinstance(command, str) else ""
        if ends:
            flags.append(True)
            if _closes(text, ends[0]):
                ends.pop(0)
        elif text_so_far is not None:
            flags.append(True)
            text_so_far += "\n" + text
            if not _list_construct_open(text_so_far, shell):
                text_so_far = None
        else:
            flags.append(False)
            if text.strip():
                ends = _heredoc_openers(text)
                shell = shells if isinstance(shells, str) else (shells or {}).get(norm_command(text), "")
                if not ends and _list_construct_open(text, shell):
                    text_so_far = text
    return flags


def _list_construct_open(text: str, shell: str) -> bool:
    """`_construct_open` for the text of a command in a list, where the shell ("powershell", "bat", "fish" or "" for a POSIX shell) is told by
    the caller and not by a fence or a prompt."""
    if shell == "bat":
        return _cmd_depth(text) > 0
    if shell == "powershell":
        state = _ps_state(text)
        return bool(state and state[3])
    quote, parens, _, _ = _shell_state(text)
    return bool(quote) or parens > 0 or _compound_depth(text, shell == "fish") > 0


def command_count(commands, shells=None) -> int:
    """How many commands a list of command lines holds: a heredoc (its opening line, body and closing word, one entry each) is one."""
    return sum(1 for command, data in zip(commands if isinstance(commands, (list, tuple)) else [], heredoc_data(commands, shells))
               if not data and isinstance(command, str) and command.strip())


def code_lines(text: str) -> list[str]:
    """Every non-blank logical line inside the README's fenced code blocks, in order."""
    return [line for _, lines in code_blocks(text) for line in lines if line]


def prompt_for(lang: str):
    """The prompt pattern that applies to a code block: all of them in a transcript, only the unambiguous ones elsewhere."""
    return PROMPT if lang in CONSOLE_LANGS else SHELL_PROMPT


def prose_lines(text: str) -> list[str]:
    """The README's lines outside its fenced code blocks (the fence lines themselves are left out too)."""
    out, fence = [], None
    for line in text.splitlines():
        fence, on_fence = fence_step(line, fence)
        if fence is None and not on_fence:
            out.append(line)
    return out


def norm_command(text) -> str:
    """A command or README line in one comparable form: whitespace collapsed, a shell prompt (`$ `, `> `, `PS C:\\>`) dropped."""
    return PROMPT.sub("", re.sub(r"\s+", " ", str(text)).strip())


def shells(text: str) -> dict[str, str]:
    """{comparable form of a command: "powershell", "bat" or "fish"} for the lines the README writes in a PowerShell, cmd or fish block (or
    after a `PS ...>` prompt of a transcript), so that the guide can say which shell a line is for. A fish line that a bash-like block
    shows too is left out: both run it. Only a line that is typed counts: not the
    output of a transcript, the data of a heredoc or a line of a sample. A line a Unix shell block also holds, or one the README shows
    first in a Unix shell block, is not listed: the guide's default is a Unix shell."""
    found: dict[str, str] = {}
    posix: set[str] = set()                                   # the lines a bash-like block shows: fish runs them too, so they need no caption
    for lang, line, role, prompt in block_lines(text):
        if prompt is None or role == "body":                  # transcript output and the data of a heredoc are not commands of any shell
            continue
        key = norm_command(line)
        if not key or _is_comment(key):
            continue
        if not (role or lang in SHELL_LANGS or lang in CONSOLE_LANGS or is_command_line(line)):
            continue                                          # a sample or an output line of a block that is not a shell's
        if lang in POWERSHELL_LANGS or (lang in CONSOLE_LANGS and POWERSHELL_PROMPT.match(line)):
            shell = "powershell"
        elif lang in CMD_LANGS or (lang in CONSOLE_LANGS and re.match(CMD_PROMPT, line)):
            shell = "bat"
        elif lang == "fish":
            shell = "fish"
        else:
            shell = "bash"
            posix.add(key)
        found.setdefault(key, shell)
    return {key: shell for key, shell in found.items() if shell != "bash" and not (shell == "fish" and key in posix)}


def setup_commands(text: str) -> list[str]:
    """What a person types, from the README's code blocks: every line of a block tagged as a shell; in a `console` transcript only
    the lines after a prompt (see `transcript_prompts`), because the rest is output; in any other block the lines that start with a
    known program. A prompt is dropped where it is one: a leading `> ` in a `bash` block is a redirection and stays."""
    out = []
    for lang, line, _, prompt in block_lines(text):
        if prompt is None:
            continue
        line = line.strip()
        found = prompt.match(line)
        bare = line[found.end():] if found else line
        if not bare or _is_comment(bare):
            continue
        if lang in CONSOLE_LANGS or lang in SHELL_LANGS or is_command_line(line):
            out.append(bare)
    return out


SNIPPET_LINES = 40                    # the most physical lines (blank ones included) of a sample the guide prints
SNIPPET_CHARS = 1800


def blocks(text: str, limit: int = 12, max_lines: int = SNIPPET_LINES, max_chars: int = SNIPPET_CHARS) -> list[list[str]]:
    """[[language, text], ...] for the README's code blocks that are not shell commands: a configuration file, a YAML/TOML/JSON
    sample, an example prompt. A guide points at one by number and the renderer prints it as the README has it, indentation
    included, so a model never retypes a setting. Blocks of the sections about installing and configuring come first."""
    text = text[:MAX_SCAN]
    value_at = _value_at(text)
    found, fence, lang, lines, start, pos = [], None, "", [], 0, 0
    for line in text.splitlines(keepends=True):
        before = fence
        fence, on_fence = fence_step(line, fence)
        if on_fence and before is None:
            info = fence_opens(line)[1]
            lang, lines, start = (info.split(" ")[0].lower() if info else ""), [], pos
        elif on_fence:
            found.append((start, lang, "\n".join(dedent(lines)).strip("\n")))
        elif fence is not None:
            lines.append(line.rstrip("\r\n"))
        pos += len(line)
    if fence is not None:                             # an unclosed block runs to the end of the README, as `code_blocks` reads it
        found.append((start, lang, "\n".join(dedent(lines)).strip("\n")))
    found = [(start, lang if re.fullmatch(r"[a-z0-9+#.-]{1,16}", lang) else "", body) for start, lang, body in found]
    ranked = []
    for start, lang, body in found:
        rows = [r for r in body.splitlines() if r.strip()]
        if not rows or len(body.splitlines()) > max_lines or len(body) > max_chars or lang in SHELL_LANGS:
            continue
        if lang in CONSOLE_LANGS and any(PROMPT.match(r) for r in rows):      # a transcript with typed lines is a shell block, not a sample
            continue
        if not lang and all(is_command_line(r) for r in rows):      # an untagged block of commands is a shell block
            continue
        ranked.append((-value_at(start), start, [lang, body]))
    return [item for _, _, item in sorted(ranked, key=lambda x: (x[0], x[1]))[:limit]]
