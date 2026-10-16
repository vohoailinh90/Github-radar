"""What a reader needs from a long README: the sections that say how to do it, links to the places it names, its commands.

Everything here is arithmetic on text, never a model. A README is cut to a few thousand characters before it reaches a
model, and cutting the head off keeps the badges and the pitch while losing the install section that sits near the end
(crisng95/flowkit: character 8,220; a 28,000-character README whose Quick Start starts at 20,500). `select` keeps whole
sections, ranked by how much they help someone follow the project, and puts them back in their original order.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FENCE = re.compile(r"^\s{0,3}(```|~~~)")
HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
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
URL_CHARS = re.compile(r"https?://[A-Za-z0-9._~:/?#@!$&*+,;=%\-\[\]]+")
MD_LINK = re.compile(r"\[([^\]\n]{1,120})\]\((https?://[^\s)]+)(?:\s+\"[^\"]*\")?\)")
HTML_LINK = re.compile(r"<a\b[^>]*?href=[\"'](https?://[^\"'\s>]+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
BARE_URL = re.compile(r"https?://[^\s<>\"'`)\]]+")
LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "[::1]")
TRACKING = re.compile(r"[?&](?:utm_[a-z]+|aff|aff_id|affiliate|ref|referral|track_id|promo|campaign|source|from)=", re.I)


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


def split_sections(text: str) -> list[Section]:
    """Sections in order. The first holds everything before the first heading (it may be empty). A `#` line inside a fenced
    code block is a comment of that code, not a heading."""
    sections = [Section(0, "", [])]
    fence = None
    for line in text.splitlines(keepends=True):
        m = FENCE.match(line)
        if m:
            fence = None if fence == m.group(1) else (fence or m.group(1))
        head = None if fence else HEADING.match(line.rstrip("\n"))
        if head:
            sections.append(Section(len(head.group(1)), re.sub(r"[*_`]", "", head.group(2)).strip(), [line]))
        else:
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
        m = FENCE.match(line)
        if m:
            fence, fence_at = (None, None) if fence == m.group(1) else (fence or m.group(1), len(out) if not fence else fence_at)
        out.append(line)
        size += len(line)
    if fence is not None and fence_at is not None:
        out = out[:fence_at]
    return "".join(out).rstrip() + "\n"


def select(text: str, limit: int) -> str:
    """`text` itself when it fits; else its opening plus the most useful whole sections, in their original order."""
    if len(text) <= limit:
        return text
    sections = split_sections(text)
    if len(sections) == 1:                        # no headings to choose between: the start of it, as before
        return _head(sections[0].lines, limit).strip() or text[:limit]
    rank(sections)
    keep: dict[int, str] = {}
    room = limit
    if sections:                                  # the preamble, or the title section when the README opens with a heading
        keep[0] = _head(sections[0].lines, min(INTRO_CHARS, room))
    room -= sum(len(v) for v in keep.values())
    order = sorted(range(1, len(sections)), key=lambda i: (-sections[i].value, i))
    for i in order:
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
    out, prev = [], -1
    for i in sorted(keep):
        if i != prev + 1:
            out.append(GAP + "\n")
        out.append(keep[i])
        prev = i
    if prev != len(sections) - 1:
        out.append(GAP + "\n")
    return "\n\n".join(x.strip("\n") for x in out).strip()


def clean_label(text: str, url: str) -> str:
    """Link text as a single plain line: no markdown, HTML or brackets that could change how it renders."""
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"[\[\]()<>`*_|\\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = re.sub(r"^https?://", "", url).split("/")[0]
    return text[:60]


def url_ok(url: str) -> bool:
    if len(url) > 200 or not URL_CHARS.fullmatch(url):
        return False
    host = url.split("/")[2].lower()
    return bool(host) and not host.startswith("img.") and not any(bad in host for bad in BAD_HOSTS)


def links(text: str, limit: int = 40) -> list[list[str]]:
    """[[label, url], ...] for the http(s) links and addresses the README shows, without repeats. The model never writes a URL:
    it points at an entry by number and the renderer prints it. Anything that is not a plain http(s) address made of ordinary
    characters is left out, and so is anything with a tracking or affiliate parameter. Links in the sections about installing,
    configuring and running come first, so a long list of vendors in a features section cannot push out the page that says where
    to get a key; within a kind, README order."""
    found: list[tuple[int, str, str]] = []
    for m in MD_LINK.finditer(text):
        found.append((m.start(), m.group(2), m.group(1)))
    for m in HTML_LINK.finditer(text):
        found.append((m.start(), m.group(1), m.group(2)))
    for m in BARE_URL.finditer(text):
        found.append((m.start(), m.group(0).rstrip(".,;:!?"), ""))
    sections = split_sections(text)
    rank(sections)
    ends, total = [], 0
    for sec in sections:
        total += len(sec.text)
        ends.append(total)
    ranked, seen = [], set()
    for pos, url, label in sorted(found, key=lambda x: x[0]):
        if url in seen or not url_ok(url) or TRACKING.search(url):
            continue
        seen.add(url)
        value = next((sec.value for sec, end in zip(sections, ends) if pos < end), 0)
        ranked.append((-value, pos, [clean_label(label, url), url]))
    return [item for _, _, item in sorted(ranked, key=lambda x: (x[0], x[1]))[:limit]]


def is_local(url: str) -> bool:
    parts = url.split("/")
    host = parts[2] if len(parts) > 2 else ""
    return host.startswith(LOCAL_HOSTS) or host.rsplit("@", 1)[-1].startswith(LOCAL_HOSTS)


SHELL_LANGS = {"bash", "sh", "shell", "zsh", "console", "terminal", "powershell", "ps1", "cmd", "bat", "batch", "shell-session"}


def code_blocks(text: str) -> list[tuple[str, list[str]]]:
    """(language tag, logical lines) of each fenced code block, in order: a line ending in a backslash is joined with the next."""
    blocks: list[tuple[str, list[str]]] = []
    fence, lang, lines, pending = None, "", [], ""
    for line in text.splitlines():
        m = FENCE.match(line)
        if m:
            if fence is None:
                fence, lang, lines, pending = m.group(1), line.strip()[3:].strip().split(" ")[0].lower(), [], ""
            elif fence == m.group(1):
                if pending:
                    lines.append(pending)
                blocks.append((lang, lines))
                fence = None
            continue
        if fence is None:
            continue
        piece = line.strip()
        pending = f"{pending} {piece}".strip() if pending else piece
        if pending.endswith("\\"):
            pending = pending[:-1].rstrip()
            continue
        if pending:
            lines.append(pending)
        pending = ""
    if fence is not None:                         # an unclosed block runs to the end of the README
        blocks.append((lang, lines + ([pending] if pending else [])))
    return blocks


def code_lines(text: str) -> list[str]:
    """Every logical line inside the README's fenced code blocks, in order."""
    return [line for _, lines in code_blocks(text) for line in lines]


def setup_commands(text: str) -> list[str]:
    """What a person types, from the README's code blocks: every line of a block tagged as a shell, and in any other block the
    lines that start with a known program. Comments and a `$ ` prompt are dropped."""
    out = []
    for lang, lines in code_blocks(text):
        for line in lines:
            bare = re.sub(r"^(?:[$>]\s+)", "", line)
            if bare and not bare.startswith(("#", "//", "REM ", "::")) and (lang in SHELL_LANGS or is_command_line(line)):
                out.append(bare)
    return out
