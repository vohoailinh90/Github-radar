import subprocess

import pytest
import yaml

from radar import handoff, studio_export
from tests.support import fake_github, make_draft
from tests.test_svg_export import CFG, FACTS


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True).stdout


@pytest.fixture
def studio_remote(tmp_path):
    bare = tmp_path / "studio.git"
    seed = tmp_path / "seed"
    git("init", "-q", "--bare", "-b", "main", str(bare), cwd=tmp_path)
    git("init", "-q", "-b", "main", str(seed), cwd=tmp_path)
    (seed / "tools" / "github-radar").mkdir(parents=True)
    (seed / "tools" / "github-radar" / "brief.yaml").write_text("slug: github-radar\nname: Edited by the owner\n")
    git("add", ".", cwd=seed)
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "seed", cwd=seed)
    git("push", "-q", str(bare), "main", cwd=seed)
    return bare


def bundle():
    return studio_export.bundle([{"facts": FACTS, "drafts": {"vi": make_draft(FACTS, "vi")}}], CFG, "2026-10-14")


def test_open_pr_pushes_a_branch_not_main_and_opens_a_draft_pr(studio_remote, tmp_path):
    api = fake_github()
    try:
        out = handoff.open_pr(bundle(), remote=str(studio_remote), repo="o/studio", campaign="radar-2026-10-14", token="tok",
                              title="t", body="b", api=api.url)
    finally:
        api.close()
    assert out["status"] == "opened" and out["url"].endswith("/pull/7")
    pr = [c for c in api.calls if c["path"].endswith("/pulls")][0]
    assert pr["body"]["draft"] is True and pr["body"]["head"] == "radar/radar-2026-10-14" and pr["body"]["base"] == "main"
    assert pr["headers"]["Authorization"] == "Bearer tok"
    assert git("branch", "--list", "--format=%(refname:short)", cwd=studio_remote).split() == ["main", "radar/radar-2026-10-14"]
    assert "radar-2026-10-14" not in git("ls-tree", "-r", "--name-only", "main", cwd=studio_remote)
    tree = git("ls-tree", "-r", "--name-only", "radar/radar-2026-10-14", cwd=studio_remote)
    assert "campaigns/radar-2026-10-14/campaign.yaml" in tree and "posts/vi/01-sample-agent-kit.yaml" in tree


def test_the_owners_edited_brief_is_never_overwritten(studio_remote, tmp_path):
    api = fake_github()
    try:
        out = handoff.open_pr(bundle(), remote=str(studio_remote), repo="o/studio", campaign="radar-2026-10-14", token="tok",
                              title="t", body="b", api=api.url)
    finally:
        api.close()
    assert "tools/github-radar/brief.yaml" not in out["files"]
    brief = yaml.safe_load(git("show", "radar/radar-2026-10-14:tools/github-radar/brief.yaml", cwd=studio_remote))
    assert brief["name"] == "Edited by the owner"


def test_a_campaign_already_in_the_studio_is_not_handed_off_twice(studio_remote, tmp_path):
    api = fake_github()
    try:
        git("clone", "-q", str(studio_remote), str(tmp_path / "w"), cwd=tmp_path)
        (tmp_path / "w" / "campaigns" / "radar-2026-10-14").mkdir(parents=True)
        (tmp_path / "w" / "campaigns" / "radar-2026-10-14" / "campaign.yaml").write_text("tool: x\n")
        git("add", ".", cwd=tmp_path / "w")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "c", cwd=tmp_path / "w")
        git("push", "-q", "origin", "main", cwd=tmp_path / "w")
        out = handoff.open_pr(bundle(), remote=str(studio_remote), repo="o/studio", campaign="radar-2026-10-14", token="tok",
                              title="t", body="b", api=api.url)
    finally:
        api.close()
    assert out["status"] == "already-handed-off" and not any(c["path"].endswith("/pulls") for c in api.calls)


def test_the_token_never_appears_on_a_command_line(monkeypatch):
    seen = []
    real = subprocess.run

    def spy(cmd, **kw):
        seen.append((cmd, kw.get("env", {})))
        return real(cmd, **kw)
    monkeypatch.setattr(handoff.subprocess, "run", spy)
    handoff._git(["--version"], cwd=__import__("pathlib").Path("."), token="SECRET-TOKEN")
    cmd, env = seen[0]
    assert all("SECRET-TOKEN" not in part for part in cmd)
    assert "SECRET-TOKEN" not in "".join(env.values()) and "AUTHORIZATION: basic" in env["GIT_CONFIG_VALUE_0"]
