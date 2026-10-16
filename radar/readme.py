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
                 "set", "cargo", "go", "pipx", "poetry", "ollama", "ffmpeg", "streamlit", "torchrun", "chmod"}
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


def is_command_line(line: str) -> bool:
    """A line of a code block that a person types: a known program first (after an optional `$ `), not a comment."""
    text = re.sub(r"^\s*(?:[$>]\s+|PS [^>]*>\s*)", "", line).strip()
    if not text or text.startswith(("#", "//", "<", "{", "}")):
        return False
    first = text.split()[0].lower().lstrip("./")
    return first in COMMAND_WORDS or text.startswith(("./", ".\\"))


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


SHELL_LANGS = {"bash", "sh", "shell", "zsh", "powershell", "ps1", "cmd", "bat", "batch"}      # every line is something to type
CONSOLE_LANGS = {"console", "shell-session", "terminal"}                                       # a transcript: only a line after a prompt is typed
POSIX_PROMPT = r"(?:\[[\w.+-]+@[\w.-]+[^\]\n]*\]|[\w.+-]+@[\w.-]+(?::[^\s$#]*)?)[ \t]?[$#]\s+"      # `user@host:~$ `, `[me@box ~]$ `, `root@host:/# `
CMD_PROMPT = r"[A-Za-z]:\\[^\s>]*>\s*"                                                             # `C:\Users\me> `: a path, then `>` (a path with a space is not told)
PROMPT = re.compile(r"^(?:[$>]\s+|PS [^>]*>\s*|" + POSIX_PROMPT + "|" + CMD_PROMPT + ")")             # a prompt in a transcript (`console`): `$ `, `> `, `PS C:\\>`, the two above
SHELL_PROMPT = re.compile(r"^(?:\$\s+|PS [^>]*>\s*|" + POSIX_PROMPT + "|" + CMD_PROMPT + ")")        # a prompt in any other block: `> file` there is a redirection, a command


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


SECONDARY_PROMPT = re.compile(r"^>\s+")                                        # what a shell shows when a command goes on over several lines
PRIMARY_PROMPT = re.compile(r"^(?:\$\s+|" + POSIX_PROMPT + ")")                # a prompt after which `> ` is that secondary prompt and not a new command
POWERSHELL_LANGS = {"powershell", "ps1"}                                   # a backtick at the end of a line continues it
CMD_LANGS = {"cmd", "bat", "batch"}                                        # a caret at the end of a line continues it
POWERSHELL_PROMPT = re.compile(r"^\s*PS [^>]*>")
DRIVE_ROOT = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:\\$")            # `cd C:\`: the root of a drive, not a line continued
HEREDOC_WORD = re.compile(r"-?[ \t]*(?:'([^']+)'|\"([^\"]+)\"|\\?([^\s;&|<>()'\"\\]+))")      # what follows `<<`: `EOF`, `-'END MARK'`, ` "EOF"`, `END-MARK`
HEREDOC_LANGS = {"", "bash", "sh", "shell", "zsh"} | CONSOLE_LANGS


def _continues(lang: str, line: str, physical: str | None = None) -> bool:
    """True when the line goes on in the next one, by the mark of its shell: a backslash (not the end of a Windows path such as
    `cd C:\\`), a backtick in PowerShell or a line after a PowerShell prompt, a caret in `cmd`, `bat` or after a cmd prompt. `line` is
    the command so far (its start tells the shell) and `physical` the line as written: the mark must be its very last character, a
    space after it escapes the space and the line ends there."""
    physical = line if physical is None else physical
    if lang in POWERSHELL_LANGS or POWERSHELL_PROMPT.match(line):
        return re.search(r"(?<!`)`$", physical) is not None
    if lang in CMD_LANGS or re.match(CMD_PROMPT, line):
        return re.search(r"(?<!\^)\^$", physical) is not None
    return (len(physical) - len(physical.rstrip("\\"))) % 2 == 1 and not DRIVE_ROOT.search(physical)       # `\\` at the end is an escaped backslash


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


def _incomplete(command: str) -> bool:
    """True when the shell would ask for more of this command (and show its secondary prompt): it ends in `|`, `&&` or `||`, or a quote
    or a parenthesis is still open. A command that is complete is followed by output, and `> ` there (npm prints `> pkg@1.0.0 start`) is not a prompt."""
    quote, depth, i = "", 0, 0
    while i < len(command):
        ch = command[i]
        if quote:
            i += 2 if ch == "\\" and quote == '"' else 1
            quote = "" if i <= len(command) and ch == quote else quote
            continue
        if ch == "\\":
            i += 2
            continue
        if ch in "'\"":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        i += 1
    return bool(quote) or depth > 0 or command.rstrip().endswith(("|", "&&", "||"))


def _heredoc_ends(line: str) -> list[str]:
    """The words that end the heredocs a command line opens (`cat <<'EOF' > f` -> ["EOF"]); the lines after it are data until each."""
    return [word for word, _ in _heredoc_openers(line)]


def _heredoc_openers(line: str) -> list[tuple[str, bool]]:
    """(word that ends the heredoc, whether `<<-` lets leading tabs be dropped before it) for each heredoc a command line opens.
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
        elif ch == "#" and (i == 0 or line[i - 1].isspace()):
            break
        elif line.startswith("$((", i) or (line.startswith("((", i) and (i == 0 or line[i - 1] in " \t;&|")):
            arithmetic, i = arithmetic + 1, i + (3 if line.startswith("$((", i) else 2)
        elif line.startswith("<<<", i):
            i += 3
        elif line.startswith("<<", i):
            word = HEREDOC_WORD.match(line, i + 2)
            if word:
                ends.append((next(g for g in word.groups() if g), line.startswith("-", i + 2)))
            i = word.end() if word else i + 2
        else:
            i += 1
    return ends


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
        while body and not body[0].strip():       # blank lines at the start and end of a block are dropped
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        logical, owners, pending, ends, opener = [], [], "", [], None
        for line in body:
            if ends:                              # inside a heredoc every line is data, a backslash at its end included
                logical.append(line.rstrip())
                owners.append(opener)
                bare = PROMPT.sub("", line) if lang in CONSOLE_LANGS else line         # a transcript shows `> ` before each line of the body
                if (bare.lstrip("\t") if ends[0][1] else bare) == ends[0][0]:           # the closing word alone on its line (`<<-`: after tabs)
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
            if (lang in CONSOLE_LANGS and not pending and logical and owners[-1] is None and SECONDARY_PROMPT.match(line.strip())
                    and PRIMARY_PROMPT.match(logical[-1]) and _incomplete(logical[-1])):      # `$ printf foo |` then `> sed ...`: the shell asked for more
                logical[-1] = f"{logical[-1]} {SECONDARY_PROMPT.sub('', line.strip()).rstrip()}"
                if _continues(lang, logical[-1], line):
                    logical[-1] = logical[-1][:-1].rstrip()
                continue
            if pending:
                piece = line.strip()
                if lang in CONSOLE_LANGS:             # `$ tool \` then `> --flag` (`>> -Flag` in PowerShell, `More? ` in cmd): the shell's secondary prompt
                    piece = PROMPT.sub("", re.sub(r"^(?:>>|More\?)\s+", "", piece))
                pending = f"{pending} {piece}"
            else:
                pending = line.rstrip()
            if _continues(lang, pending, line):
                pending = pending[:-1].rstrip()
                continue
            logical.append(pending)
            owners.append(None)
            if lang in HEREDOC_LANGS:
                ends = _heredoc_openers(pending)
                opener = len(logical) - 1
            pending = ""
        if pending:
            logical.append(pending)
            owners.append(None)
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


def block_lines(text: str) -> list[tuple[str, str, bool]]:
    """(language tag, logical line, whether it is part of a heredoc: its opening line, its body or its closing word) for every logical
    line of the README's code blocks."""
    out = []
    for lang, logical, owners in _scan(text):
        openers = {owner for owner in owners if owner is not None}
        out += [(lang, line, owner is not None or i in openers) for i, (line, owner) in enumerate(zip(logical, owners))]
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


def command_count(commands) -> int:
    """How many commands a list of command lines holds: a heredoc (its opening line, body and closing word, one entry each) is one."""
    count, ends = 0, []
    for command in commands if isinstance(commands, list) else []:
        text = command if isinstance(command, str) else ""
        if ends:
            if (text.lstrip("\t") if ends[0][1] else text) == ends[0][0]:
                ends.pop(0)
        elif text.strip():
            count += 1
            ends = _heredoc_openers(text)
    return count


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
    """{comparable form of a command: "powershell" or "bat"} for the lines the README writes in a PowerShell or cmd block (or after a
    `PS ...>` prompt of a transcript), so that the guide can say which shell a line is for. A line a Unix shell block also holds, or one
    the README shows first in a Unix shell block, is not listed: the guide's default is a Unix shell."""
    found: dict[str, str] = {}
    for lang, lines in code_blocks(text):
        for line in lines:
            key = norm_command(line)
            if not key or key.startswith(("#", "//", "REM ", "::")):
                continue
            if lang in POWERSHELL_LANGS or (lang in CONSOLE_LANGS and POWERSHELL_PROMPT.match(line)):
                shell = "powershell"
            elif lang in CMD_LANGS or (lang in CONSOLE_LANGS and re.match(CMD_PROMPT, line)):
                shell = "bat"
            else:
                shell = "bash"
            found.setdefault(key, shell)
    return {key: shell for key, shell in found.items() if shell != "bash"}


def setup_commands(text: str) -> list[str]:
    """What a person types, from the README's code blocks: every line of a block tagged as a shell; in a `console` transcript only
    the lines after a prompt (`$ `, `> `, `PS C:\\>`), because the rest is output; in any other block the lines that start with a
    known program. A prompt is dropped where it is one: a leading `> ` in a `bash` block is a redirection and stays."""
    out = []
    for lang, lines in code_blocks(text):
        rx = prompt_for(lang)
        for line in (l.strip() for l in lines):
            prompt = rx.match(line)
            bare = line[prompt.end():] if prompt else line
            if not bare or bare.startswith(("#", "//", "REM ", "::")):
                continue
            typed = bool(prompt) if lang in CONSOLE_LANGS else (lang in SHELL_LANGS or is_command_line(line))
            if typed:
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
