import importlib.util
import json
import re
import shutil
import subprocess

import pytest

from radar import config

_spec = importlib.util.spec_from_file_location("vendor_impeccable", config.ROOT / "scripts" / "vendor_impeccable.py")
vendor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vendor)

LOCK = json.loads((config.ROOT / vendor.LOCK).read_text(encoding="utf-8"))
posix_only = pytest.mark.skipif(not vendor.POSIX, reason="the executable bit exists only in POSIX file modes")


@pytest.fixture
def copy(tmp_path):
    """A scratch copy of just the vendored files and their lock, to break on purpose."""
    for rel in [*LOCK["files"], vendor.LOCK.as_posix()]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config.ROOT / rel, tmp_path / rel)
    return tmp_path


def test_the_vendored_copy_is_exactly_what_the_lock_records():
    assert vendor.problems(config.ROOT) == []


def test_an_edited_file_is_reported(copy):
    target = copy / ".claude" / "skills" / "impeccable" / "SKILL.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nlocal tweak\n", encoding="utf-8")
    assert vendor.problems(copy) == ["changed .claude/skills/impeccable/SKILL.md"]


def test_a_deleted_file_is_reported(copy):
    (copy / ".claude" / "skills" / "impeccable" / "reference" / "polish.md").unlink()
    assert vendor.problems(copy) == ["missing .claude/skills/impeccable/reference/polish.md"]


def test_a_stray_file_next_to_the_skill_is_reported(copy):
    (copy / ".claude" / "agents" / "impeccable-extra.md").write_text("x", encoding="utf-8")
    (copy / ".claude" / "skills" / "impeccable" / "notes.md").write_text("x", encoding="utf-8")
    assert vendor.problems(copy) == ["not in the lock: .claude/agents/impeccable-extra.md",
                                     "not in the lock: .claude/skills/impeccable/notes.md"]


@posix_only
def test_the_launcher_must_stay_executable(copy):
    (copy / ".claude" / "skills" / "impeccable" / "scripts" / "impeccable").chmod(0o644)
    assert vendor.problems(copy) == ["not executable .claude/skills/impeccable/scripts/impeccable"]


def test_where_there_is_no_executable_bit_it_is_not_checked_and_snapshot_refuses(copy, monkeypatch):
    """A Windows checkout reports no executable bit for the (extension-less) launcher: that is not drift."""
    monkeypatch.setattr(vendor, "POSIX", False)
    (copy / ".claude" / "skills" / "impeccable" / "scripts" / "impeccable").chmod(0o644)
    assert vendor.problems(copy) == []
    with pytest.raises(SystemExit, match="Linux, macOS or WSL"):
        vendor.snapshot(copy / "nowhere", copy)
    assert vendor.problems(copy) == []


def test_a_missing_lock_is_reported(tmp_path):
    assert vendor.problems(tmp_path) == [f"missing {vendor.LOCK.as_posix()}"]


def test_the_skill_stays_loadable_and_its_version_matches_the_lock():
    text = (config.ROOT / vendor.SKILL / "SKILL.md").read_text(encoding="utf-8")
    front = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    assert re.search(r"^name: impeccable$", front, re.M)
    assert re.search(r"^description: \S", front, re.M)
    assert re.search(rf"^version: {re.escape(LOCK['skill_version'])}$", front, re.M)
    assert LOCK["license"] == "Apache-2.0"
    assert (config.ROOT / vendor.THIRD_PARTY / "LICENSE").read_text(encoding="utf-8").lstrip().startswith("Apache License")


def test_the_agents_cannot_collide_with_the_routing_roster():
    routing = {p.name for p in (config.ROOT / vendor.AGENTS).glob("*.md") if not p.name.startswith("impeccable-")}
    vendored = {p.rsplit("/", 1)[1] for p in LOCK["files"] if p.startswith(".claude/agents/")}
    assert vendored and not (vendored & routing)
    assert all(name.startswith("impeccable-") for name in vendored)


def _git(path, *args):
    return subprocess.run(["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def upstream(tmp_path):
    """A tiny committed stand-in for the impeccable checkout."""
    up = tmp_path / "up"
    skill = up / ".claude" / "skills" / "impeccable"
    (skill / "scripts").mkdir(parents=True)
    (up / ".claude" / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: impeccable\nversion: 9.9.9\n---\nbody\n", encoding="utf-8")
    (skill / "scripts" / "VERSION").write_text("1.2.3\n", encoding="utf-8")
    (skill / "scripts" / "impeccable").write_text("#!/bin/sh\n", encoding="utf-8")
    (skill / "scripts" / "impeccable").chmod(0o755)
    (up / ".claude" / "agents" / "impeccable-a.md").write_text("a", encoding="utf-8")
    (up / "LICENSE").write_text("Apache License", encoding="utf-8")
    (up / "NOTICE.md").write_text("notice", encoding="utf-8")
    _git(up, "init", "-q")
    _git(up, "add", "-A")
    _git(up, "commit", "-q", "-m", "x")
    return up


@posix_only
def test_snapshot_vendors_a_checkout_and_drops_what_upstream_removed(tmp_path, upstream):
    root = tmp_path / "root"
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "agents" / "impeccable-gone.md").write_text("stale", encoding="utf-8")
    (root / ".claude" / "agents" / "architect.md").write_text("routing roster", encoding="utf-8")
    vendor.snapshot(upstream, root)
    lock = json.loads((root / vendor.LOCK).read_text(encoding="utf-8"))
    assert vendor.problems(root) == []
    assert lock["commit"] == _git(upstream, "rev-parse", "HEAD")
    assert (lock["skill_version"], lock["engine_version"]) == ("9.9.9", "1.2.3")
    assert lock["executable"] == [".claude/skills/impeccable/scripts/impeccable"]
    assert ".claude/agents/impeccable-gone.md" not in lock["files"]
    assert not (root / ".claude" / "agents" / "impeccable-gone.md").exists()
    assert (root / ".claude" / "agents" / "architect.md").read_text(encoding="utf-8") == "routing roster"


@posix_only
def test_snapshot_changes_nothing_when_upstream_is_not_what_it_expects(tmp_path, upstream):
    root = tmp_path / "root"
    vendor.snapshot(upstream, root)
    before = {p: (root / p).read_bytes() for p in vendor.vendored_files(root)}
    _git(upstream, "rm", "-q", "NOTICE.md")
    _git(upstream, "commit", "-q", "-m", "drop notice")
    with pytest.raises(SystemExit, match="NOTICE.md"):
        vendor.snapshot(upstream, root)
    assert {p: (root / p).read_bytes() for p in vendor.vendored_files(root)} == before
    assert vendor.problems(root) == []


@posix_only
def test_snapshot_refuses_a_dirty_checkout(tmp_path, upstream):
    (upstream / "LICENSE").write_text("edited", encoding="utf-8")
    with pytest.raises(SystemExit, match="uncommitted"):
        vendor.snapshot(upstream, tmp_path / "root")
    assert not (tmp_path / "root").exists()


@pytest.mark.skipif(shutil.which("git") is None or not (config.ROOT / ".git").exists(), reason="needs a git checkout")
def test_every_locked_file_is_exempt_from_end_of_line_conversion():
    """With core.autocrlf=true a checkout would turn the LF bytes the lock hashes (and the launcher's shebang) into CRLF."""
    out = subprocess.run(["git", "-C", str(config.ROOT), "check-attr", "text", "--", *LOCK["files"]],
                         check=True, capture_output=True, text=True).stdout
    unset = {line.rsplit(": text: ", 1)[0] for line in out.splitlines() if line.endswith(": text: unset")}
    assert unset == set(LOCK["files"])
