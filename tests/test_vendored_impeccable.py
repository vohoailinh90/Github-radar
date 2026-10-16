import importlib.util
import json
import re
import shutil

import pytest

from radar import config

_spec = importlib.util.spec_from_file_location("vendor_impeccable", config.ROOT / "scripts" / "vendor_impeccable.py")
vendor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vendor)

LOCK = json.loads((config.ROOT / vendor.LOCK).read_text(encoding="utf-8"))


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


def test_the_launcher_must_stay_executable(copy):
    (copy / ".claude" / "skills" / "impeccable" / "scripts" / "impeccable").chmod(0o644)
    assert vendor.problems(copy) == ["not executable .claude/skills/impeccable/scripts/impeccable"]


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
