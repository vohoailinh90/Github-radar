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
    assert readme.links(text) == [["bold label here", "https://ok.example.org/page"]]


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
