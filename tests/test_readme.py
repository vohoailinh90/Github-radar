from radar import facts as factslib, readme

INTRO = "# Big Project\n\nA tool that makes short videos from a topic.\n\n"


def long_readme(filler_sections: int = 14, filler: int = 1200) -> str:
    """A README whose useful part sits far from the top, as in real projects: pitch, galleries and thanks first."""
    parts = [INTRO]
    for i in range(filler_sections):
        parts.append(f"## Showcase {i}\n\n" + ("a picture of something nice. " * (filler // 28)) + "\n\n")
    parts.append("## Quick Start\n\n```bash\ngit clone https://github.com/example-org/big-project\ncd big-project\n"
                 "pip install -r requirements.txt\n```\n\n")
    parts.append("### Configure\n\nCopy `config.example.toml` to `config.toml` and add your key.\n\n")
    parts.append("## FAQ\n\nQ: It cannot find ffmpeg. A: install ffmpeg and restart.\n\n")
    parts.append("## License\n\nMIT\n\n## Star History\n\nchart\n")
    return "".join(parts)


def test_a_readme_that_fits_is_returned_untouched():
    text = "# T\n\nshort\n\n## License\n\nMIT\n"
    assert readme.select(text, 12000) == text


def test_the_install_section_survives_when_it_sits_past_the_cut():
    text = long_readme()
    assert text.index("## Quick Start") > 12000                       # the old head-cut would have lost it
    out = readme.select(text, 6000)
    assert len(out) <= 6000
    assert "pip install -r requirements.txt" in out and "config.example.toml" in out and "ffmpeg" in out
    assert "Big Project" in out                                      # the opening is kept


def test_boilerplate_goes_first_and_the_order_of_the_rest_is_kept():
    out = readme.select(long_readme(), 6000)
    assert "Star History" not in out and "## License" not in out
    assert out.index("Quick Start") < out.index("Configure") < out.index("FAQ")
    assert "other sections of the README omitted" in out              # the model is told something was left out


def test_headings_in_chinese_and_japanese_rank_like_english_ones():
    text = INTRO + "".join(f"## 作品展示 {i}\n\n" + "图片说明。" * 200 + "\n\n" for i in range(6))
    text += "## 快速开始\n\n```bash\npip install foo\n```\n\n## インストール\n\n```bash\nnpm install bar\n```\n\n## 特别感谢\n\n名单\n"
    out = readme.select(text, 3000)
    assert "pip install foo" in out and "npm install bar" in out and "特别感谢" not in out


def test_a_hash_line_inside_a_code_block_is_a_comment_not_a_heading():
    text = "# T\n\nintro\n\n## Install\n\n```bash\n# install it\npip install x\n```\n\nafter\n"
    titles = [s.title for s in readme.split_sections(text)]
    assert titles == ["T", "Install"]


def test_a_section_is_never_cut_inside_a_code_block():
    body = "```bash\n" + "\n".join(f"pip install package-{i}" for i in range(80)) + "\n```\n"
    text = INTRO + "## Install\n\nSteps:\n\n" + body + "\n## Usage\n\n" + "words " * 3000
    out = readme.select(text, 2600)
    assert out.count("```") % 2 == 0


def test_a_readme_without_headings_keeps_its_start():
    text = "line of text\n" * 3000
    out = readme.select(text, 5000)
    assert 4000 < len(out) <= 5000


def test_clean_readme_removes_images_and_cuts_by_section():
    text = "![badge](https://img.shields.io/x.svg)\n" + long_readme()
    out = factslib.clean_readme(text, 6000)
    assert "shields.io" not in out and "pip install -r requirements.txt" in out


def test_links_are_collected_from_markdown_html_and_bare_addresses_without_repeats():
    text = ('Get a key at [the key page](https://keys.example.org/new) or <a href="https://docs.example.org/start">the docs</a>.\n'
            'Then open http://localhost:8501 and again [the key page](https://keys.example.org/new).\n')
    assert readme.links(text) == [["the key page", "https://keys.example.org/new"], ["the docs", "https://docs.example.org/start"],
                                  ["localhost:8501", "http://localhost:8501"]]


def test_unsafe_or_noisy_links_are_left_out_and_labels_are_plain_text():
    text = ("[x](javascript:alert(1)) [y](ftp://files.example.org/a) [z](https://img.shields.io/badge/a-b-green) "
            "[w](https://example.org/a_(b)) [long](https://example.org/" + "a" * 250 + ")\n"
            "[**bold `label` <b>here</b>**](https://ok.example.org/page)\n")
    assert readme.links(text) == [["w", "https://example.org/a_(b)"], ["bold label here", "https://ok.example.org/page"]]      # a pair of parentheses is part of an address


def test_a_local_address_is_told_apart_from_a_website():
    assert readme.is_local("http://localhost:8501") and readme.is_local("http://0.0.0.0:8000/docs")
    assert readme.is_local("http://127.0.0.1:5000") and not readme.is_local("https://example.org/localhost")


def test_a_command_written_over_several_lines_is_one_command():
    text = "```bash\n$ torchrun --nproc_per_node=8 generate.py \\\n  --task t2v \\\n  --size 1280\n# comment\npip install x\n```\n"
    assert readme.code_lines(text) == ["$ torchrun --nproc_per_node=8 generate.py --task t2v --size 1280", "# comment", "pip install x"]
    assert readme.setup_commands(text) == ["torchrun --nproc_per_node=8 generate.py --task t2v --size 1280", "pip install x"]


def test_only_command_lines_of_code_blocks_count_as_setup():
    text = ("Run pip install outside\n\n```text\nOutput: done\nmy-tool --flag\n```\n\n```bash\ndocker compose up\nmy-tool --flag\n"
            "# comment\n```\n\n```\npip install y\n```\n")
    # a shell-tagged block counts every line; an untagged one only lines that start with a known program; prose and output never count
    assert readme.setup_commands(text) == ["docker compose up", "my-tool --flag", "pip install y"]


def test_an_unclosed_code_block_runs_to_the_end_of_the_readme():
    assert readme.code_lines("```bash\npip install a\npip install b\n") == ["pip install a", "pip install b"]


def test_links_from_the_setup_sections_come_before_a_long_list_of_vendors_and_tracked_links_are_dropped():
    vendors = "".join(f"[Vendor{i}](https://vendor{i}.example.org/) " for i in range(60))
    text = ("# Tool\n\nIntro [site](https://site.example.org/).\n\n## Features\n\n" + vendors + "\n\n## Sponsors\n\n"
            "[Sponsor](https://sponsor.example.org/?utm_source=readme) [Deal](https://deal.example.org/x?aff=tool)\n\n"
            "## Installation\n\nGet a key at [Pexels](https://www.pexels.com/api/) and read [uv](https://docs.astral.sh/uv/).\n")
    got = readme.links(text)
    assert [u for _, u in got[:2]] == ["https://www.pexels.com/api/", "https://docs.astral.sh/uv/"]
    assert len(got) == 40 and not any("sponsor" in u or "deal" in u for _, u in got)


def test_select_never_returns_more_than_the_limit_and_keeps_code_blocks_whole():
    import random
    rng = random.Random(7)
    titles = ["Install", "Run", "Showcase", "License", "Notes", "FAQ", "Config", "Thanks"]
    for _ in range(300):
        parts = []
        for i in range(rng.randint(2, 40)):
            parts.append("#" * rng.randint(1, 3) + f" {rng.choice(titles)} {i}\n\n" + "text line\n" * rng.randint(0, 60)
                         + ("```bash\npip install x\n```\n" if rng.random() < .5 else "") + "\n")
        text, limit = "".join(parts), rng.choice([300, 800, 2000, 6000])
        out = readme.select(text, limit)
        assert len(out) <= limit, (len(out), limit)
        assert out.count("```") % 2 == 0


def test_a_very_long_hostile_readme_is_handled_in_reasonable_time():
    import time
    start = time.monotonic()
    readme.links("<a href='https://a.example'>" * 40000)
    readme.links("".join(f"## S{i}\n[l](https://e{i}.example)\n" for i in range(15000)))
    readme.blocks("```yaml\n" * 20000)
    assert time.monotonic() - start < 8


def test_an_address_is_local_only_when_the_host_is_exactly_a_local_one():
    for url in ("http://localhost.evil.example/", "http://127.0.0.1.evil.example/", "http://localhost@evil.example/", "https://evil.example/localhost"):
        assert not readme.is_local(url), url
    assert readme.is_local("http://[::1]:8080/x")
    assert readme.is_local("http://0.0.0.0:8501") and readme.is_local("http://LOCALHOST:3000/a")


def test_an_address_with_a_user_part_is_not_a_link_at_all():
    assert readme.links("[x](http://127.0.0.1@evil.example/) [y](https://user:pw@host.example/) [z](https://host.example/@name)") == \
        [["z", "https://host.example/@name"]]


def test_code_blocks_that_are_not_shell_come_out_as_the_readme_has_them_with_indentation():
    text = ("## Configure\n\n```yaml\nllm:\n  model: <MODEL>\n  api_key: <KEY>\n```\n\n```bash\npip install x\n```\n\n```\nsample-tool run\n```\n\n"
            "```\nExample output\n```\n\n## Thanks\n\n```toml\n[a]\nb = 1\n```\n")
    # an untagged block counts as shell only when its lines start with a known program, so `sample-tool run` comes out too
    assert readme.blocks(text) == [["yaml", "llm:\n  model: <MODEL>\n  api_key: <KEY>"], ["", "sample-tool run"], ["", "Example output"],
                                   ["toml", "[a]\nb = 1"]]


def test_a_block_that_is_too_long_or_has_an_odd_language_tag_is_dropped_or_cleaned():
    big = "```yaml\n" + "k: v\n" * 60 + "```\n"
    odd = "```<script>x\nvalue\n```\n"
    assert readme.blocks(big) == [] and readme.blocks(odd) == [["", "value"]]


def test_a_bracketed_placeholder_host_is_ignored_not_a_crash():
    """`http://[HOST]:8080` passes the character check but urlsplit raises ValueError: it used to fail facts.build and hold the repo."""
    text = "Open http://[HOST]:8080 or [x](http://[::1:8080/) or [ok](https://ok.example.org/p) or http://[]:1/ or http://[ab/"
    assert readme.links(text) == [["ok", "https://ok.example.org/p"]]
    for url in ("http://[HOST]:8080", "http://[::1:8080/", "http://[]:1", "https://[1:2"):
        assert readme.url_ok(url) is False and readme.is_local(url) is False


def test_links_never_raise_on_address_like_noise():
    import random
    rng = random.Random(3)
    alphabet = ["http://", "https://", "[", "]", "(", ")", ":", "/", ".", "@", "1", "a", "::", "%", "-", " ", "\n", "<a href='", "'>", "</a>"]
    for _ in range(2000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 30)))
        readme.links(text)
        readme.blocks(text)
        readme.is_local(text)


def test_a_console_transcript_counts_only_the_lines_after_a_prompt_as_typed():
    text = ("```console\n$ my-tool run\nStarting server on port 8000\nSet up complete\nPS C:\\> third-tool\n```\n\n"
            "```bash\nmy-tool --flag\n```\n\n```terminal\nOutput only\n```\n")
    assert readme.setup_commands(text) == ["my-tool run", "third-tool", "my-tool --flag"]


def test_a_sample_that_runs_to_the_end_of_the_readme_is_kept_like_the_block_the_command_reader_sees():
    text = "# T\n\n## Configuration\n\n```yaml\nkey: 1\n\nother: 2\n"
    assert readme.code_blocks(text) == [("yaml", ["key: 1", "", "other: 2"])]
    assert readme.blocks(text) == [["yaml", "key: 1\n\nother: 2"]]
    assert readme.blocks("```bash\npip install x\n") == []                  # an unclosed shell block is still a command block, not a sample


def test_a_console_block_without_typed_lines_is_a_sample_and_one_with_them_is_not():
    output_only = "```console\nStarting server on port 8000\nDone\n```\n"
    transcript = "```console\n$ my-tool run\nStarted\n```\n"
    assert readme.blocks(output_only) == [["console", "Starting server on port 8000\nDone"]]
    assert readme.blocks(transcript) == []


def test_setext_and_html_headings_are_section_boundaries_so_a_late_install_section_survives():
    """`Installation` over `-----` and `<h2>Install</h2>` are headings: with ATX-only parsing the README was one section and the cut kept its start."""
    text = ("My Tool\n=======\n\nPitch.\n\n"
            + "".join(f"Gallery {i}\n---------\n\n" + "pretty picture words. " * 60 + "\n\n" for i in range(12))
            + "Installation\n------------\n\n```bash\npip install my-tool\n```\n\n<h2 align=\"center\">Configuration</h2>\n\nSet the key.\n")
    sections = readme.split_sections(text)
    assert [(s.level, s.title) for s in sections][:2] == [(1, "My Tool"), (2, "Gallery 0")]
    assert [(s.level, s.title) for s in sections][-2:] == [(2, "Installation"), (2, "Configuration")]
    out = readme.select(text, 3000)
    assert "pip install my-tool" in out and "Set the key." in out and "Gallery 11" not in out and len(out) <= 3000


def test_an_atx_heading_indented_by_up_to_three_spaces_is_a_section_boundary_and_one_by_four_is_code():
    """Markdown allows 0-3 spaces before the #'s: with column zero only, the install section stayed glued to the showcase before it."""
    text = ("# Tool\n\nPitch.\n\n  ## Showcase\n\n" + "pretty picture words. " * 400 + "\n\n"
            "   ## Installation\n\n```bash\npip install my-tool\n```\n\n"
            "    ## four spaces is a code block\n\n #hashtag is not a heading\n")
    assert [(s.level, s.title) for s in readme.split_sections(text)] == [(1, "Tool"), (2, "Showcase"), (2, "Installation")]
    out = readme.select(text, 1500)
    assert "pip install my-tool" in out and len(out) <= 1500


def test_a_code_block_is_kept_verbatim_by_the_cleaning_of_the_readme_and_the_prose_around_it_is_cleaned():
    """A sample is printed 'as the README has it': an HTML comment, an image or a run of blank lines inside a fence is the code's own."""
    text = ("# Tool\n<!-- hidden note -->\nBadge ![b](http://x/y.svg) text <img src=\"a.png\"> more\n\n\n\nPara after blank run.\n\n"
            "## Configuration\n\n```html\n<!-- keep this comment -->\n<img src=\"logo.png\">\n![alt](pic.png)\n\n\ntwo blank lines above\n```\n\n"
            "<!--\n```bash\nrm -rf /hidden\n```\n-->\n\n## Install\n\n```bash\npip install tool\n```\n")
    cleaned = factslib.clean_readme(text, 5000)
    for kept in ("<!-- keep this comment -->", '<img src="logo.png">', "![alt](pic.png)", "\n\n\ntwo blank lines above"):
        assert kept in cleaned, kept
    for gone in ("hidden note", "rm -rf /hidden", "Badge ![b]", 'src="a.png"', "more\n\n\n"):
        assert gone not in cleaned, gone
    assert "text  more\n\nPara after blank run." in cleaned
    assert readme.blocks(cleaned) == [["html", '<!-- keep this comment -->\n<img src="logo.png">\n![alt](pic.png)\n\n\ntwo blank lines above']]
    assert "pip install tool" in readme.setup_commands(cleaned)


def test_a_comment_that_is_never_closed_does_not_swallow_the_readme():
    assert "still here" in readme.clean_markup("# T\n\ntext <!-- oops\n\nstill here\n")


def test_cleaning_a_readme_without_code_blocks_is_what_the_plain_regexes_did():
    import random
    import re

    def plain(text):
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
        text = re.sub(r"<img\b[^>]*>", "", text, flags=re.I)
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    pieces = ["# T\n", "text\n", "\n", "\n\n", "<!-- one -->\n", "<!--\n", "-->\n", "a <!-- x --> b\n", "![b](u.svg) tail\n", "<img src=x>\n",
              "<!-- start\n", "end -->\n", "tail <!-- open\n", "x --> after\n"]
    rng = random.Random(7)
    for _ in range(1500):
        text = "".join(rng.choice(pieces) for _ in range(rng.randint(1, 12)))
        assert readme.clean_markup(text) == plain(text), repr(text)


def test_an_address_with_pairs_of_parentheses_is_kept_whole_and_one_with_a_stray_parenthesis_is_not_cut_short():
    text = ("See [docs](https://example.org/wiki/Foo_(bar)) and https://en.wikipedia.org/wiki/Baz_(qux). Or (see https://x.example.com/a) and\n"
            "[b](https://x.example.com/b)** done. Not https://y.example.com/p(note or <a href=\"https://z.example.com/q(r\">z</a>.\n")
    assert [u for _, u in readme.links(text)] == ["https://example.org/wiki/Foo_(bar)", "https://en.wikipedia.org/wiki/Baz_(qux)",
                                                  "https://x.example.com/a", "https://x.example.com/b"]
    assert readme.url_ok("https://example.org/wiki/Foo_(bar)")
    for bad in ("https://example.org/a)", "https://example.org/a(", "https://example.org/)a(", "https://example.org/a)b"):
        assert not readme.url_ok(bad), bad


def test_the_cut_of_a_readme_with_no_headings_never_ends_inside_a_code_block():
    big = "```bash\n" + "x" * 300 + "\n```\n"
    assert readme.select(big + "tail\n", 100) == ""                         # nothing whole fits: no half command
    assert readme.code_blocks(readme.select("intro\n" + big, 120)) == []
    assert readme._cut("intro\n```bash\nabcdef\n```\n", 17) == "intro\n"
    assert readme._cut("intro\n```bash\nabcdef\n```\n", 200) == "intro\n```bash\nabcdef\n```\n"
    import random
    rng = random.Random(3)

    def piece():
        k = rng.random()
        if k < .2:
            return "## " + rng.choice(["Install", "Showcase", "Usage", "About", "Config"]) + "\n"
        if k < .5:
            return "word " * rng.randint(1, 30) + "\n"
        if k < .8:
            lang = rng.choice(["bash", "", "yaml", "python"])
            return f"```{lang}\n" + "".join(f"line {i} " + "x" * rng.randint(1, 60) + "\n" for i in range(rng.randint(1, 12))) + "```\n"
        return "\n"

    for _ in range(600):
        text = "".join(piece() for _ in range(rng.randint(1, 25)))
        limit = rng.randint(20, 900)
        out = readme.select(text, limit)
        whole = {tuple(lines) for _, lines in readme.code_blocks(text)}
        assert len(out) <= limit and all(tuple(lines) in whole for _, lines in readme.code_blocks(out)), (limit, text, out)


def test_a_trailing_backslash_continues_a_line_only_where_the_shell_means_it():
    text = ("```bat\ncd C:\\\ndir\n```\n\n```powershell\ncd C:\\\nls\n```\n\n```console\nPS C:\\> cd C:\\\nPS C:\\> dir\n```\n\n"
            "```bash\ncd C:\\\nls\ndocker run \\\n  -p 1:1 \\\n  img\n```\n")
    assert readme.code_blocks(text) == [("bat", ["cd C:\\", "dir"]), ("powershell", ["cd C:\\", "ls"]), ("console", ["PS C:\\> cd C:\\", "PS C:\\> dir"]),
                                        ("bash", ["cd C:\\", "ls", "docker run -p 1:1 img"])]
    assert readme.setup_commands(text) == ["cd C:\\", "dir", "cd C:\\", "ls", "cd C:\\", "dir", "cd C:\\", "ls", "docker run -p 1:1 img"]


def test_the_body_of_a_heredoc_is_data_a_backslash_at_the_end_of_its_lines_included():
    text = ("```bash\ncat > conf.ini <<'EOF'\npath=C:\\tmp\\\n  indented = 1\n\nregex=a\\\nEOF\ndocker run \\\n  img\ncat <<-X <<'Y'\n  one \\\nX\ntwo \\\nY\n"
            "echo done\nfoo <<< bar \\\n  baz\n```\n")
    assert readme.code_blocks(text) == [("bash", ["cat > conf.ini <<'EOF'", "path=C:\\tmp\\", "  indented = 1", "", "regex=a\\", "EOF", "docker run img",
                                                 "cat <<-X <<'Y'", "  one \\", "X", "two \\", "Y", "echo done", "foo <<< bar baz"])]
    assert readme._heredoc_ends("cat <<EOF > f") == ["EOF"] and readme._heredoc_ends("x <<< word") == [] and readme._heredoc_ends("echo $((1 << 2))") == []


def test_a_powershell_backtick_and_a_cmd_caret_continue_a_line_and_a_doubled_mark_does_not():
    text = ("```powershell\nInvoke-WebRequest `\n  -Uri x `\n  -Method Get\nWrite-Host ``\n```\n\n```bat\necho a ^\n  b\necho ^^\n```\n\n"
            "```console\nPS C:\\> Get-Item `\n>> -Path x\n$ tool \\\n> --flag\n```\n")
    assert readme.code_blocks(text) == [("powershell", ["Invoke-WebRequest -Uri x -Method Get", "Write-Host ``"]), ("bat", ["echo a b", "echo ^^"]),
                                        ("console", ["PS C:\\> Get-Item -Path x", "$ tool --flag"])]


def test_the_shell_a_readme_writes_a_command_line_for_is_known_when_it_is_not_a_unix_shell():
    text = ("```powershell\n.\\webui.bat\n# a comment\nWrite-Host   hi\n```\n\n```bat\nwebui.bat\nREM remark\n```\n\n```bash\nls -la\n.\\webui.bat\n```\n\n"
            "```console\nPS C:\\> Get-Item x\n$ ls\n```\n")
    assert readme.shells(text) == {".\\webui.bat": "powershell", "Write-Host hi": "powershell", "webui.bat": "bat", "Get-Item x": "powershell"}
    assert readme.shells("```bash\nls\n```\n") == {} and readme.shells("no code") == {}


def test_only_an_unescaped_backslash_continues_a_line():
    text = "```bash\nprintf '%s\\n' C:\\\\\necho next\nprintf a \\\\\n  b\nprintf c \\\\\\\n  d\ndocker run \\\n  img\n```\n"
    assert readme.code_blocks(text) == [("bash", ["printf '%s\\n' C:\\\\", "echo next", "printf a \\\\", "  b", "printf c \\\\ d", "docker run img"])]


def test_a_heredoc_is_one_group_from_its_opening_line_to_its_closing_word():
    text = ("```bash\ncat > conf.yml <<EOF\nmodel: x\n\nkey: y\nEOF\npip install tool\ncat <<-'A' <<B\n  one\nA\ntwo\nB\n```\n"
            "\n```powershell\nGet-Item x\n```\n")
    groups, loose = readme.heredocs(text)
    assert groups == [["cat > conf.yml <<EOF", "model: x", "", "key: y", "EOF"], ["cat <<-'A' <<B", "  one", "A", "two", "B"]]
    assert loose == ["cat > conf.yml <<EOF", "pip install tool", "cat <<-'A' <<B", "Get-Item x"]                      # the openers and the lines outside any heredoc
    assert readme.heredocs("```bash\nls\n```\n") == ([], ["ls"]) and readme.heredocs("no code") == ([], [])


def test_a_heredoc_marker_in_a_quote_a_comment_or_after_a_backslash_opens_nothing():
    ends = readme._heredoc_ends
    assert ends("cat <<EOF > f") == ["EOF"] and ends("cat <<-'EOF' <<\"B\"") == ["EOF", "B"] and ends("cat << EOF") == ["EOF"]
    for line in ("# Example: cat <<EOF", 'echo "write <<EOF to begin"', "echo 'a <<EOF'", "x <<< word", "echo $((1 << 2))", "echo a\\<<EOF"):
        assert ends(line) == [], line
    assert ends("echo 'a <<EOF' && cat <<X") == ["X"] and ends('echo "a \\" <<EOF" <<Z') == ["Z"] and ends("echo $# <<EOF") == ["EOF"]
    text = "```bash\n# Example: cat <<EOF\npip install pkg\necho \"write <<EOF to begin\"\npip install other\n```\n"
    assert readme.heredocs(text) == ([], ["# Example: cat <<EOF", "pip install pkg", 'echo "write <<EOF to begin"', "pip install other"])


def test_a_heredoc_delimiter_is_the_whole_shell_word_and_arithmetic_opens_nothing():
    ends = readme._heredoc_ends
    assert ends("cat <<END-MARK") == ["END-MARK"] and ends("cat <<'END MARK' > f") == ["END MARK"] and ends("cat <<EOF>f") == ["EOF"]
    assert ends("cat <<-\"A.B\" <<C_D;") == ["A.B", "C_D"] and ends("cat <<EOF # note") == ["EOF"]
    for line in ("echo $((mask << SHIFT))", "(( x = 1 << SH ))", "echo $((1<<2))", "echo $(( (1 << 2) | 3 ))", "echo $((1 << 2"):
        assert ends(line) == [], line
    assert ends("echo $(( (1 << 2) | 3 )) && cat <<EOF") == ["EOF"] and ends("echo $((1<<2)) | cat <<'END'") == ["END"]
    assert ends("echo $(( $((1 << 2)) << 3 )) <<X") == ["X"]
    text = "```bash\ncat <<END-MARK\nline\nEND-MARK\necho $((mask << SHIFT))\npip install pkg\n```\n"
    assert readme.heredocs(text) == ([["cat <<END-MARK", "line", "END-MARK"]], ["cat <<END-MARK", "echo $((mask << SHIFT))", "pip install pkg"])


def test_a_cmd_transcript_continues_a_line_with_a_caret_and_drops_the_more_prompt():
    text = "```console\nC:\\repo> echo hello ^\nMore? world\nC:\\repo> echo done ^^\nC:\\repo> dir\n```\n"
    assert readme.code_blocks(text) == [("console", ["C:\\repo> echo hello world", "C:\\repo> echo done ^^", "C:\\repo> dir"])]
    assert readme.setup_commands(text) == ["echo hello world", "echo done ^^", "dir"]


def test_a_comment_is_stripped_only_when_the_shell_would_read_it_as_one():
    strip = readme.strip_trailing_comment
    assert strip("pip install x  # note") == "pip install x" and strip("echo 'a # b' # c") == "echo 'a # b'" and strip("echo # x") == "echo"
    for line in ('export MESSAGE="hello # world"', "echo 'a # b'", "echo a\\ # b", "echo a #b", "echo a#", 'echo "x \\" # y"'):
        assert strip(line) == line, line


def test_a_heredoc_ends_on_the_closing_word_alone_on_its_line_and_only_tabs_may_precede_it_after_a_dash():
    plain = "```bash\ncat <<EOF\n  EOF\nreal body\nEOF\npip install pkg\n```\n"
    assert readme.heredocs(plain) == ([["cat <<EOF", "  EOF", "real body", "EOF"]], ["cat <<EOF", "pip install pkg"])
    dashed = "```bash\ncat <<-EOF\n\tbody\n\tEOF\npip install pkg\n```\n"
    assert readme.heredocs(dashed) == ([["cat <<-EOF", "\tbody", "\tEOF"]], ["cat <<-EOF", "pip install pkg"])
    spaces = "```bash\ncat <<-EOF\n  body\n  EOF\npip install pkg\n```\n"                    # spaces do not count as tabs: it never closes ...
    assert readme.heredocs(spaces) == ([], []) and readme.code_blocks(spaces) == [("bash", [])]          # ... and a heredoc that never closes is no command
    assert readme._heredoc_openers("cat <<-EOF <<'B'") == [("EOF", True), ("B", False)]


def test_a_backslash_followed_by_a_space_does_not_continue_the_line():
    text = "```bash\necho a\\  \necho next\ndocker run \\\n  img\n```\n\n```console\nPS C:\\> Get-Item `\n-Path x `\n-Force\n$ tool \\ \n> --flag\n```\n"
    assert readme.code_blocks(text) == [("bash", ["echo a\\", "echo next", "docker run img"]), ("console", ["PS C:\\> Get-Item -Path x -Force", "$ tool \\", "> --flag"])]


def test_a_heredoc_in_a_transcript_closes_on_its_closing_word_after_the_continuation_prompt():
    text = "```console\n$ cat <<EOF\n> body\n> EOF\n$ pip install pkg\nInstalled\n```\n"
    assert readme.heredocs(text) == ([["$ cat <<EOF", "> body", "> EOF"]], ["$ cat <<EOF", "$ pip install pkg", "Installed"])
    assert readme.setup_commands(text) == ["cat <<EOF", "body", "EOF", "pip install pkg"]


def test_a_closing_fence_is_at_most_three_columns_deeper_than_the_opening_one():
    text = "```bash\npip install a\n    ```\npip install b\n```\n\nPara\n"
    assert readme.code_blocks(text) == [("bash", ["pip install a", "    ```", "pip install b"])]          # four more: a line of the code
    assert readme.code_blocks("* item\n\n    ```bash\n    pip install a\n    ```\n\n* two\n") == [("bash", ["pip install a"])]      # nested: any depth
    assert readme.code_blocks("  ```bash\n  pip install a\n     ```\n\ntext\n") == [("bash", ["pip install a"])]                     # 2 + 3 columns
    assert readme.code_blocks("  ```bash\n  pip install a\n      ```\ntext\n") == [("bash", ["  pip install a", "      ```", "text"])]      # 2 + 4: not a closing fence


def test_a_heredoc_counts_as_one_command_in_a_list_of_commands():
    heredoc = ["cat > f <<EOF"] + ["k: v"] * 19 + ["EOF"]
    assert readme.command_count(heredoc) == 1 and readme.command_count(heredoc + ["pip install x", "", "echo ok"]) == 3
    assert readme.command_count(["cat <<-'A'", "\tone", "\tA", "pip install y"]) == 2
    assert readme.command_count(["cat <<EOF", "body"]) == 1 and readme.command_count([]) == 0
    assert readme.command_count(None) == 0 and readme.command_count("pip install x") == 0 and readme.command_count([1, None, "ls"]) == 1


def test_a_secondary_prompt_continues_the_command_before_it_only_when_that_command_is_incomplete():
    text = ("```console\n$ printf foo |\n> sed s/foo/bar/\n$ echo \"multi\n> line\"\n$ (cd x &&\n> ls)\n"
            "$ npm start\n> myapp@1.0.0 start\n> node index.js\nServer started\n```\n")
    assert readme.code_blocks(text) == [("console", ["$ printf foo | sed s/foo/bar/", '$ echo "multi', '> line"', "$ (cd x &&", "> ls)", "$ npm start",
                                                    "> myapp@1.0.0 start", "> node index.js", "Server started"])]     # an open quote is a group, not a join
    assert readme.setup_commands(text)[:5] == ["printf foo | sed s/foo/bar/", 'echo "multi', 'line"', "(cd x &&", "ls)"]
    assert readme.code_blocks("```console\n> npm install x\n> npm run build\n```\n") == [("console", ["> npm install x", "> npm run build"])]
    for done in ("pip install x", "echo 'a | b'", "echo \"a\" && ls", "echo a \\| b", "(ls)"):
        assert not readme._incomplete(done), done
    for open_ in ("ls |", "make &&", "a ||", "echo \"x", "echo 'x", "(cd x", "echo $(ls"):
        assert readme._incomplete(open_), open_


def test_a_heredoc_that_never_reaches_its_closing_word_is_not_a_command():
    text = "```bash\nls\ncat <<EOF\nline one\npip install pkg\n```\n\n```bash\ncat <<EOF\nbody\nEOF\n```\n"
    assert readme.code_blocks(text) == [("bash", ["ls"]), ("bash", ["cat <<EOF", "body", "EOF"])]
    assert readme.heredocs(text) == ([["cat <<EOF", "body", "EOF"]], ["ls", "cat <<EOF"])           # the first block's opener and body are gone


def test_a_continuation_mark_inside_a_comment_or_at_the_end_of_a_block_continues_nothing():
    text = "```bash\necho first # note \\\necho second\n# whole line comment \\\necho third\necho 'a # b' \\\n  c\necho x#y \\\n  z\n```\n"
    assert readme.code_blocks(text) == [("bash", ["echo first # note \\", "echo second", "# whole line comment \\", "echo third", "echo 'a # b' c", "echo x#y z"])]
    assert readme.code_blocks("```powershell\nGet-Item x # note `\nGet-Item y `\n  -Force\n```\n") == [("powershell", ["Get-Item x # note `", "Get-Item y -Force"])]
    for text in ("```bash\nls\ndocker run \\\n```\n", "```bash\nls\ndocker run \\\n\n```\n", "```powershell\nls\nGet-Item `\n```\n", "```bat\nls\necho a ^\n```\n"):
        assert [line for _, lines in readme.code_blocks(text) for line in lines] == ["ls"], text
    assert readme._has_comment("a # b") and readme._has_comment("# b") and not readme._has_comment("a#b") and not readme._has_comment("'a # b'")


def test_a_cmd_prompt_needs_no_space_after_it_unless_the_path_is_a_file_or_the_arrow_is_doubled():
    text = ("```console\nC:\\test>dir /x\nC:\\x\\run.exe>out.txt\nC:\\X\\RUN.EXE>out.txt\nC:\\logs\\app>>x\nC:\\v1.2>dir\n"
            "C:\\tools\\run.exe > out.txt\nC:\\run.exe 2> err.txt\nC:\\a\\b.ps1>log\n```\n")
    assert readme.setup_commands(text) == ["dir /x", "dir"]
    assert readme.shells(text) == {"dir /x": "bat", "dir": "bat"}


def test_a_cmd_prompt_may_hold_a_path_with_spaces_and_a_redirection_is_still_not_a_prompt():
    text = ("```console\nC:\\Program Files\\repo> winget install pkg\nC:\\tools\\run.exe > out.txt\nC:\\> dir\nC:\\x\\run.exe>out.txt\n```\n")
    assert readme.setup_commands(text) == ["winget install pkg", "dir"]
    assert readme.shells(text) == {"winget install pkg": "bat", "dir": "bat"}
    assert readme.SHELL_PROMPT.sub("", "C:\\Program Files\\My Repo> ls") == "ls"
    for not_a_prompt in ("C:\\tools\\run.exe > out.txt", "C:\\x\\run.exe>out.txt", "C:\\run.exe 2> err.txt"):
        assert readme.SHELL_PROMPT.sub("", not_a_prompt) == not_a_prompt, not_a_prompt


def test_a_command_that_the_shell_grammar_leaves_unfinished_is_joined_in_any_posix_block():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```bash\nprintf foo |\nsed s/foo/bar/\necho \"hello\nworld\"\n```\n") == ["printf foo | sed s/foo/bar/", 'echo "hello', 'world"']
    assert lines("```bash\ncurl -X POST http://x -d '{\n  \"a\": 1\n}'\npip install y\n```\n") == ["curl -X POST http://x -d '{", '  "a": 1', "}'", "pip install y"]
    assert lines("```sh\n(cd x &&\n ls)\nmake &&\nmake test\n```\n") == ["(cd x &&", " ls)", "make && make test"]
    # the same for a transcript, where the secondary prompt is dropped
    assert lines("```console\n$ printf foo |\n> sed s/foo/bar/\n```\n") == ["$ printf foo | sed s/foo/bar/"]


def test_an_apostrophe_in_sample_output_a_comment_or_a_blank_line_joins_nothing():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```bash\n./run\nIt's working\npip install x\n```\n") == ["./run", "pip install x"]          # the quote never closes: it joins nothing and is not a command
    assert lines("```bash\n# don't do this\npip install x\nls # it's |\necho a |\n\nls\n```\n") == ["# don't do this", "pip install x", "ls # it's |", "", "ls"]
    assert lines("```bash\necho \"a\n" + "line\n" * 25 + "z\"\npip install x\n```\n")[-1] == "pip install x"      # too far away to be the rest of it
    assert lines("```powershell\nGet-Item 'it's\nGet-Item x |\nSelect y\n```\n") == ["Get-Item 'it's", "Get-Item x | Select y"]        # PowerShell has its own grammar: a pipe at the end of a line continues it


def test_a_backslash_inside_single_quotes_is_literal_and_inside_double_quotes_it_continues():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```bash\necho 'abc\\\ndef'\n```\n") == ["echo 'abc\\", "def'"]            # in 'single quotes' the backslash is literal: a string over two lines
    assert lines("```bash\necho \"abc\\\ndef\"\n```\n") == ['echo "abcdef"']          # the shell removes the backslash and the newline, and nothing else
    assert lines("```bash\necho it\\\n  works\n```\n") == ["echo it works"]


def test_a_fish_fence_and_the_other_common_shells_are_shells_and_only_fish_has_no_heredoc():
    assert readme.setup_commands("```fish\nfisher install jorgebucaran/nvm.fish\n```\n") == ["fisher install jorgebucaran/nvm.fish"]
    for tag in ("fish", "ksh", "dash", "ash"):
        assert readme.setup_commands(f"```{tag}\nmy-tool --flag\n```\n") == ["my-tool --flag"], tag
    assert readme.heredocs("```fish\ncat <<EOF\nx\nEOF\n```\n") == ([], ["cat <<EOF", "x", "EOF"])
    assert readme.heredocs("```dash\ncat <<EOF\nx\nEOF\n```\n")[0] == [["cat <<EOF", "x", "EOF"]]


def test_the_data_of_a_heredoc_in_a_list_of_commands_is_told_from_the_commands():
    commands = ["cat <<EOF", "$ literal price", "EOF", "$ ls", "cat <<-'A'", "\tone", "\tA"]
    assert readme.heredoc_data(commands) == [False, True, True, False, False, True, True]
    assert readme.command_count(commands) == 3 and readme.heredoc_data(None) == [] and readme.heredoc_data([1, "ls"]) == [False, False]


def test_a_virtual_environment_prefix_does_not_hide_a_prompt_and_a_subshell_redirection_is_not_one():
    text = "```console\n(venv) $ pip install pkg\n(.venv) user@host:~$ ls\n(base) $ conda list\n$ plain\n(echo a) > out.txt\n(cd x && ls)\n```\n"
    assert readme.setup_commands(text) == ["pip install pkg", "ls", "conda list", "plain"]
    for prompted in ("(venv) $ x", "(.venv) user@host:~$ x", "(base) [me@box ~]$ x"):
        assert readme.SHELL_PROMPT.sub("", prompted) == "x", prompted
    for plain in ("(echo a) > out.txt", "(cd x && ls)", "(venv) x"):
        assert readme.SHELL_PROMPT.sub("", plain) == plain, plain


def test_a_heredoc_delimiter_may_be_made_of_quoted_and_escaped_pieces():
    ends = readme._heredoc_ends
    for line in ("cat <<E\\OF", "cat <<'E'OF", "cat <<\"E\"'O'F", "cat <<\\EOF", "cat <<\"EOF\"", "cat << 'EOF'"):
        assert ends(line) == ["EOF"], line
    assert ends("cat <<END-MARK") == ["END-MARK"] and ends("cat <<'END MARK' > f") == ["END MARK"] and ends("cat <<-\"A.B\" <<C_D;") == ["A.B", "C_D"]
    text = "```bash\ncat <<'E'OF\nbody\nEOF\npip install pkg\n```\n"
    assert readme.heredocs(text) == ([["cat <<'E'OF", "body", "EOF"]], ["cat <<'E'OF", "pip install pkg"])


def test_a_command_wrapper_or_an_assignment_before_the_program_does_not_hide_it_in_an_untagged_block():
    text = "```\nsudo apt-get install ffmpeg\nsudo -E pip install x\nFOO=1 BAR=2 make\nsudo dnf install y\nsudo\nwho cares\n```\n"
    assert readme.setup_commands(text) == ["sudo apt-get install ffmpeg", "sudo -E pip install x", "FOO=1 BAR=2 make", "sudo dnf install y"]
    assert readme.is_command_line("$ sudo -E git status") and not readme.is_command_line("sudo") and not readme.is_command_line("sudo hello")


def test_a_pwsh_fence_is_powershell():
    text = "```pwsh\nInstall-Module -Name Pester `\n  -Force\nGet-Item x\n```\n"
    assert readme.code_blocks(text) == [("pwsh", ["Install-Module -Name Pester -Force", "Get-Item x"])]
    assert readme.setup_commands(text) == ["Install-Module -Name Pester -Force", "Get-Item x"]
    assert readme.shells(text) == {"Install-Module -Name Pester -Force": "powershell", "Get-Item x": "powershell"}


def test_the_prompts_a_terminal_usually_shows_are_prompts_and_a_redirection_is_not():
    text = ("```console\nuser@host:~$ pip install pkg\nC:\\Users\\me> winget install pkg\n[me@box ~]$ ls\nroot@host:/# apt install x\n$ plain\n"
            "C:\\tools\\run.exe > out.txt\noutput line\n```\n")
    assert readme.setup_commands(text) == ["pip install pkg", "winget install pkg", "ls", "apt install x", "plain"]
    assert readme.shells(text) == {"winget install pkg": "bat"}
    for prompt in ("user@host:~$ ", "me@box $ ", "[me@box ~]$ ", "root@host:/# ", "C:\\Users\\me> ", "C:\\> "):
        assert readme.SHELL_PROMPT.sub("", prompt + "ls") == "ls", prompt
    for not_a_prompt in ("C:\\tools\\run.exe > out.txt", "ssh user@host ls", "git clone git@github.com:org/repo.git", "> out.txt", "echo $ x"):
        assert readme.SHELL_PROMPT.sub("", not_a_prompt) == not_a_prompt, not_a_prompt


def test_adjacent_addresses_with_nothing_between_them_are_separate_links():
    text = ("Set `CORS_ALLOWED_ORIGINS=http://localhost:3000,https://frontend.example.com;http://[::1]:8080,https://b.example.org/x` first.\n"
            "Also [both](http://a.example.com,https://b.example.com) and https://c.example.com/list?ids=1,2 here.\n")
    urls = [u for _, u in readme.links(text)]
    assert urls == ["http://localhost:3000", "https://frontend.example.com", "http://[::1]:8080", "https://b.example.org/x",
                    "http://a.example.com", "https://b.example.com", "https://c.example.com/list?ids=1,2"]      # the glued target of [both](...) is no link itself
    assert not readme.url_ok("http://localhost:3000,https://frontend.example.com")
    assert readme.url_ok("https://c.example.com/list?ids=1,2") and readme.url_ok("http://[::1]:8080/ui")


def test_lines_that_only_look_like_a_setext_underline_are_not_headings():
    text = ("# Title\n\nPara\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n- item\n---\n\nText\n\n---\n\n```\nTitle\n=====\n```\n\n"
            "> quote\n---\n\n---\nfront\n")
    assert [s.title for s in readme.split_sections(text)] == ["Title"]


def test_a_redirection_at_the_start_of_a_line_of_a_shell_block_is_kept_but_a_prompt_is_dropped():
    text = "```bash\n> output.log\n$ make\nPS C:\\> dir\n```\n\n```console\n> make test\n```\n"
    assert readme.setup_commands(text) == ["> output.log", "make", "dir", "make test"]
    assert readme.prose_lines("a\n```\nb\n```\nc\n") == ["a", "c"]


def test_a_bare_address_with_a_bracketed_host_is_kept_whole():
    text = "Open http://[::1]:8080/ui now, or http://[2001:db8::1]/x. Not http://[HOST]:8080 or http://[ab/."
    assert readme.links(text) == [["::1:8080", "http://[::1]:8080/ui"], ["2001:db8::1", "http://[2001:db8::1]/x"]]
    assert readme.is_local("http://[::1]:8080/ui")


def test_the_secondary_prompt_of_a_wrapped_transcript_command_is_not_part_of_the_command():
    transcript = "```console\n$ tool \\\n> --flag \\\n> --other\n$ next\n```\n"
    assert readme.setup_commands(transcript) == ["tool --flag --other", "next"]
    assert readme.code_lines(transcript) == ["$ tool --flag --other", "$ next"]
    shell = "```bash\ntool \\\n> out.log\n```\n"                  # in a shell block `> out.log` is a redirection that continues the command
    assert readme.setup_commands(shell) == ["tool > out.log"]


FOUR = "## Install\n\n````bash\nmy-tool --flag\n```\n# not a heading\n```\nmy-tool run\n````\n\n## After\n\ntext\n"


def test_a_block_opened_with_four_backticks_holds_a_three_backtick_example():
    """The fence is the whole run: a closing fence needs at least as many characters of the same kind, and the language is `bash`."""
    assert readme.code_blocks(FOUR) == [("bash", ["my-tool --flag", "```", "# not a heading", "```", "my-tool run"])]
    assert readme.setup_commands(FOUR)[0] == "my-tool --flag" and readme.setup_commands(FOUR)[-1] == "my-tool run"
    assert readme.blocks(FOUR) == []                                  # a shell block is not offered as a config sample
    assert [s.title for s in readme.split_sections(FOUR)] == ["Install", "After"]          # the `#` line inside is not a heading
    assert readme.prose_lines(FOUR) == ["## Install", "", "", "## After", "", "text"]


def test_a_cut_never_lands_inside_a_four_backtick_block():
    text = "# T\n\nintro\n\n## Install\n\nsteps\n\n````md\n" + "line\n```\ninner\n```\n" * 40 + "````\n\n## Tail\n\n" + "words " * 400
    out = readme.select(text, 900)
    assert len(out) <= 900 and out.count("````") % 2 == 0


def test_fences_of_each_kind_open_and_close_only_on_their_own():
    tilde = "~~~~sh\nmy-tool a\n~~~\nmy-tool b\n~~~~\n\n```sh\nmy-tool c\n~~~\nmy-tool d\n```\n"
    assert readme.code_blocks(tilde) == [("sh", ["my-tool a", "~~~", "my-tool b"]), ("sh", ["my-tool c", "~~~", "my-tool d"])]
    assert readme.fence_opens("```code``` in a sentence") is None and readme.fence_opens("``") is None
    assert readme.fence_opens("   ````yaml extra") == (("````", 3), "yaml extra")                      # the fence and its indentation, then the info


def test_a_fence_nested_in_a_list_item_is_found_whatever_its_indentation():
    text = "1. Install:\n\n     ```bash\n     pip install x\n     ```\n"
    assert readme.setup_commands(text) == ["pip install x"]


def test_a_shell_block_keeps_the_indentation_and_blank_lines_of_its_lines():
    """The body of a heredoc (or a YAML sample) is indented on purpose; only the indentation of the container is removed."""
    text = "```bash\ncat > config.yaml <<EOF\nllm:\n  model: x\n\n  key: y\nEOF\n```\n"
    assert readme.code_blocks(text) == [("bash", ["cat > config.yaml <<EOF", "llm:", "  model: x", "", "  key: y", "EOF"])]
    assert readme.setup_commands(text) == ["cat > config.yaml <<EOF", "llm:", "model: x", "key: y", "EOF"]    # what is typed: no blank, no indent
    nested = "1. Run:\n\n   ```bash\n   cat <<EOF\n     indented\n   EOF\n   ```\n"
    assert readme.code_blocks(nested) == [("bash", ["cat <<EOF", "  indented", "EOF"])]                    # the list item's own indent is gone
    assert readme.code_blocks("```bash\n\n\nls\n\n\n```\n") == [("bash", ["ls"])]                         # blank edges are dropped


def test_a_margin_drawn_with_a_tab_on_some_lines_and_spaces_on_others_is_still_one_margin():
    # pyvideotrans: the fence sits in a list item, the first line has 4 spaces, the others a tab (both are 4 columns)
    text = "  * macOS:\n  ```\n    brew install git\n\t\n\tbrew tap tool/ffmpeg\n\t\n\tbrew install tool/ffmpeg\n  ```\n"
    assert readme.code_blocks(text) == [("", ["brew install git", "", "brew tap tool/ffmpeg", "", "brew install tool/ffmpeg"])]


def test_a_tab_that_is_part_of_the_content_is_kept_when_no_margin_is_shared():
    text = "```make\nall:\n\tcc -o app main.c\n```\n"
    assert readme.code_blocks(text) == [("make", ["all:", "\tcc -o app main.c"])]


def test_a_tab_cut_by_the_margin_leaves_its_remainder_as_spaces():
    assert readme.dedent(["  a", "\tb"]) == ["a", "  b"]
    assert readme.dedent(["", "  ", "\t\tx"]) == ["", "", "x"]


def test_a_sample_keeps_its_own_indentation_when_the_margin_is_drawn_with_tabs():
    text = "* step\n\t```toml\n\t[server]\n\t  port = 1\n\t```\n"
    assert readme.blocks(text) == [["toml", "[server]\n  port = 1"]]


def test_the_padding_of_a_continuation_line_is_dropped_but_the_indentation_of_a_first_line_stays():
    text = "```bash\ntool a \\\n      --b \\\n      --c\n  indented\n```\n"
    assert readme.code_blocks(text) == [("bash", ["tool a --b --c", "  indented"])]
    assert readme.code_lines(text) == readme.code_blocks(text)[0][1]


def test_the_lines_npm_prints_after_a_typed_command_are_output_not_commands():
    text = "```console\n$ npm start\n> myapp@1.0.0 start\n> node index.js\nServer started\n$ npm test\n```\n"
    assert readme.setup_commands(text) == ["npm start", "npm test"]
    assert [command for command in readme.setup_commands(text) if "node" in command or "myapp" in command] == []
    assert readme.command_count(readme.setup_commands(text)) == 2


def test_a_transcript_with_no_other_prompt_types_its_lines_after_the_greater_than_sign_and_a_heredoc_body_after_a_dollar_prompt_too():
    only = "```console\n> npm install x\n> npm run build\nBuilt in 3s\n```\n"
    assert readme.setup_commands(only) == ["npm install x", "npm run build"]
    heredoc = "```console\n$ cat <<EOF\n> body one\n> EOF\n$ ls\n```\n"
    assert readme.heredocs(heredoc) == ([["$ cat <<EOF", "> body one", "> EOF"]], ["$ cat <<EOF", "$ ls"])
    assert readme.setup_commands(heredoc) == ["cat <<EOF", "body one", "EOF", "ls"]


def test_the_prompt_of_root_is_a_prompt_when_a_command_follows_it_and_no_other_prompt_came_before():
    text = "```console\n# apt-get update\n# apt-get install ffmpeg\nReading package lists...\n```\n"
    assert readme.setup_commands(text) == ["apt-get update", "apt-get install ffmpeg"]
    comment = "```console\n$ ls\n# this is a comment\n# apt-get install x\n```\n"
    assert readme.setup_commands(comment) == ["ls"]                    # after a `$` prompt a `#` line is a comment, never root's prompt
    assert readme.setup_commands("```console\n# this is a comment\nOutput\n```\n") == []


def test_the_lines_npm_prints_after_a_root_prompt_are_output_too():
    text = "```console\n# npm start\n> app@1.0.0 start\n> node index.js\nServer started\n# npm test\n```\n"
    assert readme.setup_commands(text) == ["npm start", "npm test"]          # `# npm test` after the output is still root's prompt
    assert readme.setup_commands("```console\n$ npm start\n> app@1.0.0 start\n# npm test\n```\n") == ["npm start"]      # but not after a `$` prompt


def test_a_comment_after_a_control_operator_opens_no_heredoc_and_hides_no_command():
    text = "```bash\necho hi;# example <<EOF\nnpm install x\npip install y\n```\n"
    assert readme.code_blocks(text) == [("bash", ["echo hi;# example <<EOF", "npm install x", "pip install y"])]
    assert readme.setup_commands(text) == ["echo hi;# example <<EOF", "npm install x", "pip install y"]
    for line in ("echo hi;# x", "make && # x", "a | # x", "(# x", "# x", "echo hi # x"):
        assert readme._has_comment(line), line
        assert readme._heredoc_openers(line + " <<EOF") == [], line
    for line in ("echo $#", "echo ${#x}", "echo a#b", "echo 'a;# b'", 'echo "(# b"', r"echo a\;# b"):
        assert not readme._has_comment(line), line
    assert readme._heredoc_openers("cat <<EOF;# note") == [("EOF", False)]
    assert not readme._incomplete("echo hi;# it's here") and readme._incomplete("echo hi; echo 'it")


def test_the_common_programs_of_other_ecosystems_are_commands_in_an_untagged_block():
    for command in ("kubectl apply -f deployment.yaml", "terraform init", "dotnet run", "ls -la", "cat config.yaml", "Rscript run.R",
                    "az login", "gcloud auth login", "helm install x ./chart", "mvn package", "sudo systemctl start x"):
        text = f"## Install\n\n```\n{command}\n```\n"
        assert readme.is_command_line(command), command
        assert readme.setup_commands(text) == [command], command
        assert readme.blocks(text) == [], command                             # a command block, not a sample to copy
    for line in ("hello world", "Next steps are below", "Server started on port 8000", "name: value"):
        assert not readme.is_command_line(line), line
        assert readme.setup_commands(f"```\n{line}\n```\n") == []


def test_a_backslash_newline_joins_the_words_that_touch_and_keeps_the_break_the_reader_sees():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```bash\nprintf '%s\\n' foo\\\nbar\n```\n") == ["printf '%s\\n' foobar"]            # `foo\` over `bar` is `foobar`
    assert lines("```bash\necho a \\\nb\necho c\\\n  d\necho e \\\n    f\n```\n") == ["echo a b", "echo c d", "echo e f"]
    assert lines("```console\n$ printf x foo\\\n> bar\n$ echo a \\\n> b\n```\n") == ["$ printf x foobar", "$ echo a b"]
    assert lines("```powershell\nGet-Item x`\n-Force\n```\n") == ["Get-Item x -Force"]                     # the other shells keep the word break
    assert readme.setup_commands("```bash\nprintf '%s\\n' foo\\\nbar\n```\n") == ["printf '%s\\n' foobar"]


def test_the_options_of_a_wrapper_that_take_a_word_are_skipped_with_that_word():
    for command in ("sudo -u postgres psql", "env -u HOME make", "sudo -E -u root git pull", "sudo --user root git status", "sudo --user=root git status",
                    "nice -n 10 make", "time -p make", "xargs -n 1 git status", "doas -u me git status", "sudo -g docker -u me docker ps"):
        assert readme.is_command_line(command), command
        assert readme.setup_commands(f"```\n{command}\n```\n") == [command], command
    for command in ("sudo -u postgres", "sudo hello", "env -u HOME", "sudo -u me hello", "env -i hello"):
        assert not readme.is_command_line(command), command


def test_a_command_that_never_becomes_complete_is_not_a_command_but_output_and_samples_are_kept():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```bash\nls\nprintf foo |\n```\n") == ["ls"]
    assert lines("```bash\necho \"abc\n\nnpm install x\n```\n") == ["", "npm install x"]
    assert lines("```sh\nmake &&\n\nmake test\n```\n") == ["", "make test"]
    assert lines("```console\n$ printf foo |\nDon't worry\n$ ls\n```\n") == ["Don't worry", "$ ls"]              # a typed line is dropped, an output line is not
    assert lines("```\nmessage: Don't panic\n```\n") == ["message: Don't panic"]                                # a sample in another language is not shell
    assert lines("```yaml\nmessage: it's \"x\n```\n") == ["message: it's \"x"]
    assert lines("```bash\nls\nprintf foo |\nsed s/foo/bar/\n```\n") == ["ls", "printf foo | sed s/foo/bar/"]          # one that does complete is still joined
    assert readme.setup_commands("```bash\nnpm install x\nprintf foo |\n```\n") == ["npm install x"]


def test_a_backslash_in_a_double_quoted_heredoc_delimiter_stays_unless_it_escapes_a_special_character():
    assert readme._heredoc_openers('cat <<"E\\OF"') == [("E\\OF", False)]                  # `\O` is not an escape inside double quotes
    assert readme._heredoc_openers('cat <<"E\\$F"') == [("E$F", False)]
    assert readme._heredoc_openers('cat <<"E\\\\F"') == [("E\\F", False)]
    assert readme._heredoc_openers("cat <<E\\OF") == [("EOF", False)]                      # unquoted, a backslash escapes any character
    assert readme._heredoc_openers("cat <<'E\\OF'") == [("E\\OF", False)]                  # in single quotes it is literal
    text = "```bash\ncat <<\"E\\OF\"\nbody\nE\\OF\nls\n```\n"
    assert readme.heredocs(text) == ([['cat <<"E\\OF"', "body", "E\\OF"]], ['cat <<"E\\OF"', "ls"])         # the closing line is found, `ls` is a command


def test_a_powershell_command_split_after_a_pipe_a_comma_or_an_open_bracket_is_one_command():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```powershell\nGet-ChildItem *.mp4 |\n  Where-Object Length -gt 1MB\nWrite-Host done\n```\n") == [
        "Get-ChildItem *.mp4 | Where-Object Length -gt 1MB", "Write-Host done"]
    assert lines("```pwsh\nforeach ($f in Get-ChildItem) {\n  Write-Host $f\n  Remove-Item $f\n}\n```\n") == [
        "foreach ($f in Get-ChildItem) { Write-Host $f; Remove-Item $f }"]                       # a line break inside { } ends a statement
    assert lines("```powershell\n$h = @{\n a = 1\n b = 2\n}\n$a = @(\n 1,\n 2\n)\n$i = $a[\n0\n]\n```\n") == [
        "$h = @{ a = 1; b = 2 }", "$a = @( 1, 2 )", "$i = $a[ 0 ]"]
    assert lines("```console\nPS C:\\> Get-ChildItem |\n>> Select Name\n```\n") == ["PS C:\\> Get-ChildItem | Select Name"]
    assert readme.setup_commands("```powershell\nGet-ChildItem |\n  Select Name\n```\n") == ["Get-ChildItem | Select Name"]
    assert readme.command_count(readme.setup_commands("```powershell\nGet-ChildItem |\n  Select Name\n```\n")) == 1


def test_a_powershell_command_that_cannot_be_told_is_left_as_it_is_and_one_that_never_completes_is_dropped():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```powershell\nGet-ChildItem |\n```\n") == []                                # a trailing pipe with nothing after it
    assert lines("```powershell\nforeach ($f in $x) {\n\nRemove-Item $f\n```\n") == ["", "Remove-Item $f"]       # a blank line ends it
    assert lines("```powershell\nfoo { # note\n bar\n}\n```\n") == ["foo { bar }"]                                  # a comment inside is left out of the join
    assert lines("```powershell\nfoo <# a #> {\n bar\n}\n```\n") == ["foo  { bar }"]                                # a block comment is cut out, then the rest is grouped
    assert lines("```powershell\nGet-Item 'it's\nGet-Item x\n```\n") == ["Get-Item 'it's", "Get-Item x"]       # `'it'` closes, then `s`: complete
    assert lines("```powershell\nGet-Item 'it\nGet-Item x\n```\n") == ["Get-Item x"]                            # a quote that never closes: PowerShell waits
    assert lines("```powershell\nWrite-Host \"a | b\" # |\nWrite-Host 'x,'\n```\n") == ["Write-Host \"a | b\" # |", "Write-Host 'x,'"]
    assert readme._ps_open("Get-ChildItem |") and readme._ps_open("foo (") and readme._ps_open("1,2,")
    assert readme._ps_open("Write-Host 'a |'") is False and readme._ps_open("foo { bar }") is False and readme._ps_open("foo 'x") is True
    assert readme._ps_open("$x = @\"") is None and readme._ps_open("foo <# c") is None                             # a here-string, a block comment: not told


def test_only_a_typed_command_chooses_the_shell_of_a_line_not_a_sample_an_output_line_or_heredoc_data():
    text = ("```text\nGet-ChildItem\n```\n\n```powershell\nGet-ChildItem\nWrite-Host hi\n```\n\n"
            "```bash\ncat <<EOF\nWrite-Host hi\nEOF\n```\n\n```console\n$ ls\ndir\n```\n\n```cmd\ndir\n```\n")
    assert readme.shells(text) == {"Get-ChildItem": "powershell", "Write-Host hi": "powershell", "dir": "bat"}
    assert readme.shells("```console\nPS C:\\> Get-Item x\nGet-Item y\n```\n") == {"Get-Item x": "powershell"}      # `Get-Item y` is output


def test_a_command_that_ends_in_a_redirection_operator_is_dropped_but_an_angle_bracket_placeholder_is_not():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```bash\nls\necho hi >\ncat <\ncat file >>\nrun 2>\nnpm install x\n```\n") == ["ls", "npm install x"]
    assert lines("```bash\ngit clone <repo-url>\ncd <your folder>\nrun --in <path> --out <dir>\nrun a >b >\n```\n") == [
        "git clone <repo-url>", "cd <your folder>", "run --in <path> --out <dir>"]              # `<url>` closes its `<`; `a >b >` has a `>` too many
    assert lines("```bash\necho a\\>\necho '>'\necho \"a >\"\necho hi > # note\necho ok # >\n```\n") == ["echo a\\>", "echo '>'", 'echo "a >"', "echo ok # >"]
    assert lines("```console\n$ echo hi >\nok >\n$ ls\n```\n") == ["ok >", "$ ls"]                 # a typed line is dropped, an output line is not
    assert readme.setup_commands("```bash\necho hi >\npip install x\n```\n") == ["pip install x"]
    assert readme._ends_in_redirection("echo hi >") and readme._ends_in_redirection("cat <") and not readme._ends_in_redirection("git clone <u>")


def test_a_fish_only_command_keeps_its_shell_but_a_line_a_bash_block_shows_too_needs_no_caption():
    text = "```fish\nset -Ux EDITOR vim\npip install x\n```\n\n```bash\npip install x\nexport EDITOR=vim\n```\n"
    assert readme.shells(text) == {"set -Ux EDITOR vim": "fish"}
    assert readme.shells("```fish\nset -Ux EDITOR vim\n```\n\n```powershell\nGet-Item x\n```\n") == {"set -Ux EDITOR vim": "fish", "Get-Item x": "powershell"}


def test_a_powershell_comment_after_a_statement_separator_hides_the_pipe_in_it():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```powershell\nWrite-Host hi;# note |\nGet-Item x\n```\n") == ["Write-Host hi;# note |", "Get-Item x"]       # the `|` is in the comment
    assert lines("```powershell\nWrite-Host hi # note |\nGet-Item x\n```\n") == ["Write-Host hi # note |", "Get-Item x"]
    assert lines("```powershell\nGet-ChildItem | # sort them\n  Sort-Object Name\n```\n") == ["Get-ChildItem | Sort-Object Name"]       # the comment is dropped, not joined into
    assert lines("```powershell\nGet-Item a#b |\n  Select x\n```\n") == ["Get-Item a#b | Select x"]     # `#` inside a word is not a comment
    assert lines("```pwsh\nforeach ($x in $y) {# go\n  Write-Host $x\n}\n```\n") == ["foreach ($x in $y) { Write-Host $x }"]
    assert readme._ps_open("Write-Host hi;# note |") is False and readme._ps_open("Write-Host hi |") is True


def test_the_secondary_prompt_of_a_command_typed_at_a_prompt_is_dropped_in_any_shell_fence():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```bash\n$ docker run \\\n> --rm image\n$ ls\n```\n") == ["$ docker run --rm image", "$ ls"]
    assert readme.setup_commands("```bash\n$ docker run \\\n> --rm image\n```\n") == ["docker run --rm image"]
    assert lines("```bash\n$ printf foo |\n> sed s/foo/bar/\n```\n") == ["$ printf foo | sed s/foo/bar/"]
    assert lines("```powershell\nPS C:\\> Get-Item x `\n>> -Force\n```\n") == ["PS C:\\> Get-Item x -Force"]
    assert lines("```bash\ntool \\\n> out.log\n```\n") == ["tool > out.log"]                  # no prompt: `> out.log` is a redirection, as before


def test_a_heredoc_typed_at_a_prompt_in_a_shell_fence_closes_and_loses_the_prompt_of_its_lines_but_a_plain_one_keeps_its_data():
    prompted = "```bash\n$ cat <<EOF\n> body one\n> EOF\n$ ls\n```\n"
    assert readme.heredocs(prompted) == ([["$ cat <<EOF", "> body one", "> EOF"]], ["$ cat <<EOF", "$ ls"])
    assert readme.setup_commands(prompted) == ["cat <<EOF", "body one", "EOF", "ls"]
    plain = "```bash\ncat <<EOF\n> not a prompt\n$ nor this\nEOF\n```\n"
    assert readme.setup_commands(plain) == ["cat <<EOF", "> not a prompt", "$ nor this", "EOF"]          # the data of a plain heredoc is data


def test_a_powershell_string_over_several_lines_is_a_group_and_one_that_never_closes_is_dropped():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines('```powershell\nWrite-Host "hello\nworld"\nGet-Item x\n```\n') == ['Write-Host "hello', 'world"', "Get-Item x"]
    assert lines("```pwsh\nWrite-Host 'a\n  b' | Out-Null\n```\n") == ["Write-Host 'a", "  b' | Out-Null"]
    assert lines('```powershell\nWrite-Host "it\'s"\nWrite-Host \'say "hi\'\n```\n') == ['Write-Host "it\'s"', 'Write-Host \'say "hi\'']      # a quote inside the other kind
    assert lines('```powershell\nWrite-Host "hello\n```\n') == []
    assert lines("```powershell\nWrite-Host # it's\nGet-Item x\n```\n") == ["Write-Host # it's", "Get-Item x"]           # an apostrophe in a comment
    assert lines('```powershell\n$x = @"\ntext\n"@\n```\n')[0] == '$x = @"'                                       # a here-string is not joined into one line


def test_the_compound_redirection_operators_need_a_word_after_them_too():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    dangling = ("echo hi >&", "cat <&", "exec 3<>", "cmd &>", "cmd &>>", "echo hi >|", "cmd 2>&", "cat <<", "cat <<-", "cat <<<", "cmd 2>>", "cmd >>")
    assert lines("```bash\nls\n" + "\n".join(dangling) + "\nnpm i\n```\n") == ["ls", "npm i"]
    complete = ("sleep 1 &", "echo ok 2>&1", "echo hi >&2", "cmd &> out.log", "echo hi >| out", "cat <<<hello", "cat <&3", "cmd >&-", "git clone <url>")
    assert lines("```bash\n" + "\n".join(complete) + "\n```\n") == list(complete)
    assert lines("```bash\necho hi >|\nsleep 1 &\n```\n") == ["sleep 1 &"]                # `>|` is a redirection, not a pipe that joins the next line


def test_a_powershell_here_string_is_a_group_of_data_lines_up_to_the_mark_that_begins_a_line():
    text = '```powershell\n$x = @"\nline one\n\n  line two\n"@ | Set-Content f.txt\nGet-Item x\n```\n'
    assert readme.heredocs(text) == ([['$x = @"', "line one", "", "  line two", '"@ | Set-Content f.txt']], ['$x = @"', "Get-Item x"])
    assert readme.setup_commands(text) == ['$x = @"', "line one", "line two", '"@ | Set-Content f.txt', "Get-Item x"]
    single = "```pwsh\n$y = @'\nraw $text\n'@\nls\n```\n"
    assert readme.heredocs(single) == ([["$y = @'", "raw $text", "'@"]], ["$y = @'", "ls"])
    assert readme.heredocs('```powershell\n$x = @"\nnever closed\nGet-Item x\n```\n') == ([], [])         # a here-string that never closes is not a command
    assert readme.heredocs("```powershell\nWrite-Host 'a@\"'\nGet-Item x\n```\n") == ([], ["Write-Host 'a@\"'", "Get-Item x"])       # `@\"` inside a string opens nothing
    transcript = '```console\nPS C:\\> $x = @"\n>> text\n>> "@\nPS C:\\> ls\n```\n'
    assert readme.heredocs(transcript) == ([['PS C:\\> $x = @"', ">> text", '>> "@']], ['PS C:\\> $x = @"', "PS C:\\> ls"])


def test_a_string_over_several_lines_is_a_group_whose_line_breaks_are_kept_in_a_shell_fence():
    blank = '```bash\npython -c "\nimport torch\n\nprint(torch.cuda.is_available())\n"\nls\n```\n'
    assert readme.heredocs(blank)[0] == [['python -c "', "import torch", "", "print(torch.cuda.is_available())", '"']]    # a blank line is part of the string
    assert readme.heredocs('```bash\necho "it\n' + "line\n" * 25 + 'x"\nls\n```\n')[0] == []                      # too far away to be its end
    script = '```bash\npython -c "\nimport torch\nprint(torch.cuda.is_available())\n"\nls\n```\n'
    assert readme.heredocs(script) == ([['python -c "', "import torch", "print(torch.cuda.is_available())", '"']], ['python -c "', "ls"])
    assert readme.setup_commands(script) == ['python -c "', "import torch", "print(torch.cuda.is_available())", '"', "ls"]
    assert readme.command_count(readme.setup_commands(script)) == 2
    triple = '```bash\nidea = """\nIf a cat\n"""\nnpm i\n```\n'
    assert readme.heredocs(triple)[0] == [['idea = """', "If a cat", '"""']]
    yaml = "```yaml\ntitle: Don't panic\nother: \"it's\"\n```\n\n```python\nname = \"don't\"\ntext = '''a\nb'''\n```\n"
    assert [owners for _, _, owners in readme._scan(yaml)] == [[None, None], [None, None, None]]          # samples in other languages are not shell
    flags = readme.heredoc_data(['python -c "', "import torch", '"', "ls", 'echo "a', 'b" | cat', "pwd"])
    assert flags == [False, True, True, False, False, True, False]


def test_the_lines_of_a_string_or_a_here_string_are_printed_as_they_are_in_one_block():
    from radar import digest
    lines = digest._command_blocks({}, ['python -c "', "  import torch", '"', "ls"], {"shell_bash": "bash"})
    assert lines == ["```bash", 'python -c "', "  import torch", '"', "ls", "```"]
    lines = digest._command_blocks({"shells": {"Get-Item x": "powershell"}}, ['$x = @"', "  text", '"@ | Set-Content f', "Get-Item x"],
                                   {"shell_bash": "bash", "shell_powershell": "PowerShell"})
    assert '  text' in lines and lines.count("```bash") == 1


def test_a_powershell_block_comment_is_not_code_through_its_terminator_and_rem_is_a_comment_in_any_case():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    text = ("```powershell\n<# Remove-Item -Recurse output #>\nGet-Item x <# note #> | Select y\n<#\n.SYNOPSIS\nRemove-Item -Recurse output\n#>\n"
            "Write-Host \"a <# b\"\n# <# not a block\nGet-Item z\n```\n")
    assert lines(text) == ["Get-Item x  | Select y", 'Write-Host "a <# b"', "# <# not a block", "Get-Item z"]
    assert lines("```pwsh\nGet-Item x\n<# never closed\nRemove-Item all\n```\n") == ["Get-Item x"]             # it runs to the end of the block
    assert lines("```bash\necho '<# not powershell'\nls\n```\n") == ["echo '<# not powershell'", "ls"]
    assert readme.setup_commands(text)[:1] == ["Get-Item x  | Select y"] and "Remove-Item -Recurse output" not in readme.setup_commands(text)
    assert readme.setup_commands("```cmd\nrem note\nREM Note\nRem\nsetup.bat\n```\n") == ["setup.bat"]
    assert readme.shells("```cmd\nrem note\nsetup.bat\n```\n") == {"setup.bat": "bat"}


def test_a_compound_command_over_several_lines_is_a_group_that_is_copied_whole():
    def groups(text):
        return readme.heredocs(text)
    iffy = "```bash\nif [ -d build ]; then\n  rm -rf build\nfi\nls\n```\n"
    assert groups(iffy) == ([["if [ -d build ]; then", "  rm -rf build", "fi"]], ["if [ -d build ]; then", "ls"])
    assert readme.command_count(readme.setup_commands(iffy)) == 2
    loop = "```sh\nfor f in *.mp4; do\n  ffmpeg -i \"$f\" out/\"$f\"\ndone\nwhile read l; do echo $l; done < list.txt\n```\n"
    assert groups(loop)[0] == [["for f in *.mp4; do", '  ffmpeg -i "$f" out/"$f"', "done"]]            # the one-line loop is a command of its own
    case = "```bash\ncase $OS in\n  mac) brew install ffmpeg;;\n  *) apt install ffmpeg;;\nesac\n```\n"
    assert groups(case)[0] == [["case $OS in", "  mac) brew install ffmpeg;;", "  *) apt install ffmpeg;;", "esac"]]
    func = "```bash\nsetup() {\n  pip install x\n}\nsetup\n```\n"
    assert groups(func) == ([["setup() {", "  pip install x", "}"]], ["setup() {", "setup"])
    transcript = "```console\n$ if true; then\n>   echo yes\n> fi\n$ ls\n```\n"
    assert groups(transcript)[0] == [["$ if true; then", ">   echo yes", "> fi"]]
    assert readme.setup_commands(transcript) == ["if true; then", "echo yes", "fi", "ls"]


def test_a_compound_command_that_never_closes_is_dropped_and_words_that_are_not_keywords_open_nothing():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert lines("```bash\nls\nif [ -d build ]; then\nls build\n```\n")[0] == "ls" and "if [ -d build ]; then" not in lines("```bash\nls\nif [ -d build ]; then\nls build\n```\n")
    c = readme._compound_depth
    for text, depth in (("if true; then echo x; fi", 0), ("echo if", 0), ('echo "if"', 0), ("echo ${x}", 0), ("echo a # if", 0), ("make if", 0), ("echo done", 0),
                        ("echo $(if a; then b; fi)", 0), ("{ echo a; }", 0), ("(cd x && ls)", 0), ("if a; then b; elif c; then d; else e; fi", 0),
                        ("if [ -d build ]; then", 1), ("for i in 1 2; do", 1), ("foo() {", 1), ("$ if true; then", 1), ("case $x in\n a) b;;", 1)):
        assert c(text) == depth, text
    yaml = "```yaml\nif: true\nfor: x\n```\n\n```python\nif x:\n    print(1)\n```\n"
    assert [owners for _, _, owners in readme._scan(yaml)] == [[None, None], [None, None]]               # samples in other languages are not shell
    assert readme.heredoc_data(["if true; then", "  ls", "fi", "pwd"]) == [False, True, True, False]


def test_a_powershell_string_with_an_escaped_quote_before_its_line_break_stays_in_its_fence():
    from radar import digest
    text = "```powershell\nWrite-Host \"say `\"\nhi\"\nGet-Item x\n```\n"
    assert readme.heredocs(text) == ([['Write-Host "say `"', 'hi"']], ['Write-Host "say `"', "Get-Item x"])
    table = readme.shells(text)
    assert table == {'Write-Host "say `"': "powershell", "Get-Item x": "powershell"}
    commands = ['Write-Host "say `"', 'hi"', "Get-Item x"]
    assert readme.heredoc_data(commands, table) == [False, True, False]                       # with the shell told, as the scanner read it
    assert readme.heredoc_data(commands) != [False, True, False]                              # POSIX rules read the escape of PowerShell differently
    lines = digest._command_blocks({"shells": table}, commands, {"shell_bash": "bash", "shell_powershell": "PowerShell"})
    assert lines == ["_PowerShell_", "", "```powershell", 'Write-Host "say `"', 'hi"', "Get-Item x", "```"]        # one block, in the opener's shell


def test_a_function_defined_with_the_function_keyword_and_a_pipe_with_stderr_are_unfinished_constructs():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    c = readme._compound_depth
    for text, depth in (("function setup {", 1), ("function setup {\n  rm -rf build\n}", 0), ("function f { echo hi; }", 0), ("function f() {", 1),
                        ("function f()\n{", 1), ("echo function {", 0), ("function f", 1), ("function f; echo {", 0), ("function f() { echo a; }", 0)):
        assert c(text) == depth, text
    text = "```bash\nfunction setup {\n  rm -rf build\n}\nsetup\n```\n"
    assert readme.heredocs(text) == ([["function setup {", "  rm -rf build", "}"]], ["function setup {", "setup"])
    assert lines("```bash\nproducer |&\ntee log\nls\n```\n") == ["producer |& tee log", "ls"]                 # `|&` is a pipeline operator: it takes the next line
    assert lines("```bash\nls\nproducer |&\n```\n") == ["ls"]                                              # one that has no next line is dropped
    assert lines("```bash\nsleep 1 &\nls\n```\n") == ["sleep 1 &", "ls"]                                  # a lone `&` is a background job, complete


def test_at_rem_is_a_comment_and_a_function_header_with_its_brace_on_the_next_line_is_one_group():
    assert readme.setup_commands("```cmd\n@REM note\n@rem x\n@  Rem y\nrem z\n@echo off\nsetup.bat\n```\n") == ["@echo off", "setup.bat"]
    assert readme.shells("```bat\n@REM note\nsetup.bat\n```\n") == {"setup.bat": "bat"}
    c = readme._compound_depth
    for text, depth in (("setup()", 1), ("setup ()\n{", 1), ("setup()\n{\n  rm -rf build\n}", 0), ("setup() { rm x; }", 0), ("function f\n{", 1), ("function f\n{\n a\n}", 0),
                        ("setup()\necho hi", 0), ("foo (bar)", 0), ("echo a) b", 0), ("case $x in\n a) b;;\nesac", 0)):
        assert c(text) == depth, text
    text = "```bash\nsetup()\n{\n  rm -rf build\n}\nsetup\n```\n"
    assert readme.heredocs(text) == ([["setup()", "{", "  rm -rf build", "}"]], ["setup()", "setup"])


def test_a_redirection_with_a_space_after_an_angle_bracket_is_not_a_placeholder_whatever_the_line_holds_before_it():
    r = readme._ends_in_redirection
    for line in ("cat < input >", "cat <in >", "echo hi >", "run a >b >", "cat <", "cat < in > out >", "cat <in> >"):
        assert r(line), line
    for line in ("git clone <repo-url>", "cd <your folder>", "run --in <path> --out <dir>", "cat <in>", "cat < in > out", "echo '>'",
                 "ssh -N -L 4173:127.0.0.1:4173 <user>@<server>", "scp <file> <user>@<host>:<dir>"):
        assert not r(line), line
    lines = [line for _, block in readme.code_blocks("```bash\nls\ncat < input >\ngit clone <repo-url>\n```\n") for line in block]
    assert lines == ["ls", "git clone <repo-url>"]


def test_a_backquoted_substitution_over_several_lines_is_a_group_and_an_unclosed_one_is_dropped():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    assert readme.heredocs("```bash\necho `printf hi;\nprintf there`\nls\n```\n") == ([["echo `printf hi;", "printf there`"]], ["echo `printf hi;", "ls"])
    assert lines("```bash\nls\necho `date\n```\n") == ["ls"]                                              # a backquote that never closes
    assert lines('```bash\necho "`date`"\necho `pwd`\necho \\`not a substitution\\`\n```\n') == ['echo "`date`"', "echo `pwd`", "echo \\`not a substitution\\`"]
    assert readme._shell_state("echo `a")[0] == "`" and readme._shell_state("echo `a`")[0] == "" and readme._shell_state("echo '`a'")[0] == ""
    assert readme.heredoc_data(["echo `printf hi;", "printf there`", "ls"]) == [False, True, False]


def test_a_powershell_line_that_ends_in_a_binary_operator_or_a_pipeline_chain_goes_on_in_the_next():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    text = "```powershell\n$x = 1 +\n2\nGet-Item a &&\nGet-Item b\n$y = 1 -and\n$true\n$z =\n5\nGet-Item c ||\nGet-Item d\n```\n"
    assert lines(text) == ["$x = 1 + 2", "Get-Item a && Get-Item b", "$y = 1 -and $true", "$z = 5", "Get-Item c || Get-Item d"]
    assert lines("```powershell\n$x = 1 + # add\n2\n```\n") == ["$x = 1 + 2"]
    assert lines("```powershell\nGet-ChildItem *\nGet-ChildItem C:\\tmp\\\nRemove-Item x -f\nRemove-Item y -Force\n```\n") == [
        "Get-ChildItem *", "Get-ChildItem C:\\tmp\\", "Remove-Item x -f", "Remove-Item y -Force"]           # a wildcard, a path and `-f` do not want a next line
    assert lines("```powershell\nGet-Item x &&\n```\n") == []                                              # a chain with nothing after it is dropped


def test_a_subshell_or_substitution_over_several_lines_is_a_group_because_a_line_break_separates_statements():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    text = "```bash\nx=$(\n  echo one\n  echo two\n)\n(cd x &&\n  ls)\nmake &&\nmake test\nls\n```\n"
    assert readme.heredocs(text) == ([["x=$(", "  echo one", "  echo two", ")"], ["(cd x &&", "  ls)"]], ["x=$(", "(cd x &&", "make && make test", "ls"])
    assert lines(text)[-2:] == ["make && make test", "ls"]                          # a pipe or `&&` at the end of a line is still joined
    assert lines("```bash\nls\n(cd x\n```\n") == ["ls"]                         # a parenthesis that never closes
    assert readme.heredoc_data(["x=$(", "echo one", "echo two", ")", "ls"]) == [False, True, True, True, False]


def test_a_here_string_keeps_a_block_comment_marker_in_its_data():
    text = '```powershell\n$x = @"\nliteral <# not a comment #> text\n"@\nGet-Item <# note #> y\n```\n'
    assert readme.heredocs(text) == ([['$x = @"', "literal <# not a comment #> text", '"@']], ['$x = @"', "Get-Item  y"])
    raw = "```powershell\n$y = @'\n<# raw #>\n'@ | Out-Null\nGet-Item z\n```\n"
    assert readme.heredocs(raw) == ([["$y = @'", "<# raw #>", "'@ | Out-Null"]], ["$y = @'", "Get-Item z"])


def test_a_powershell_expression_that_ends_in_any_binary_operator_goes_on_but_a_wildcard_argument_does_not():
    def lines(text):
        return [line for _, block in readme.code_blocks(text) for line in block]
    text = ("```powershell\n$x = 4 -\n2\n$y = 3 *\n4\n$z = $y /\n2\n$w = ($x + 1) %\n2\n$a = 1 -as\n[string]\n$b = 5 -is\n[int]\n"
            "$c = 'a' -in\n@('a')\n```\n")
    assert lines(text) == ["$x = 4 - 2", "$y = 3 * 4", "$z = $y / 2", "$w = ($x + 1) % 2", "$a = 1 -as [string]", "$b = 5 -is [int]", "$c = 'a' -in @('a')"]
    keep = ("Get-ChildItem *", "Copy-Item $src *", "$files = Get-ChildItem C:\\tmp\\*", "Get-ChildItem C:\\tmp\\", "Remove-Item $p -f", "Get-Process | %x")
    assert lines("```powershell\n" + "\n".join(keep) + "\n```\n") == list(keep)                             # a wildcard, a path, `-f` end a command
