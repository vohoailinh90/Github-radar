import re

import yaml

from radar import config

W = yaml.safe_load((config.ROOT / ".github" / "workflows" / "radar.yml").read_text(encoding="utf-8"))
TEXT = (config.ROOT / ".github" / "workflows" / "radar.yml").read_text(encoding="utf-8")


def test_runs_on_wednesday_and_saturday_only():
    crons = [s["cron"] for s in W[True]["schedule"]]          # PyYAML reads the key `on` as True
    assert crons == ["0 1 * * 3,6"]
    minute, hour, dom, month, dow = crons[0].split()
    assert dom == month == "*" and dow.split(",") == ["3", "6"]       # 3 = Wednesday, 6 = Saturday in cron


def test_manual_runs_default_to_a_dry_run():
    assert W[True]["workflow_dispatch"]["inputs"]["dry_run"]["default"] is True


def test_uses_the_ci_runner_switch_and_serialises_runs():
    job = W["jobs"]["radar"]
    assert job["runs-on"] == "${{ vars.CI_RUNNER || 'ubuntu-latest' }}"
    assert W["concurrency"] == {"group": "radar", "cancel-in-progress": False}


def test_permissions_are_the_minimum_and_user_inputs_never_reach_the_shell_directly():
    assert W["permissions"] == {"contents": "write"}
    for run in re.findall(r"run: \|?\s*(.*?)(?=\n      - |\Z)", TEXT, re.S):
        assert "${{ inputs." not in run and "${{ github.event.inputs" not in run


def test_secrets_are_only_passed_as_environment_to_the_steps_that_need_them():
    assert "secrets.STUDIO_REPO_TOKEN" in TEXT
    steps = W["jobs"]["radar"]["steps"]
    carrying = [s["name"] for s in steps if any("secrets." in str(v) for v in (s.get("env") or {}).values())]
    assert carrying == ["Doctor (keys)", "Doctor (is each model still offered?)", "Scan, write, check, export",
                        "Hand off to tool-marketing-studio (draft pull request)"]
    ping = next(s for s in steps if s.get("name", "").startswith("Doctor (is each"))
    assert ping["continue-on-error"] is True and "--ping" in ping["run"]
    assert "--ping" not in next(s for s in steps if s.get("name") == "Doctor (keys)")["run"]


def test_the_scan_conditions_inputs_match_the_saved_presets_and_reach_only_the_scan_step():
    from radar import conditions
    inputs = W[True]["workflow_dispatch"]["inputs"]
    assert inputs["preset"]["type"] == "choice" and inputs["preset"]["default"] == "none"
    assert inputs["preset"]["options"] == ["none", *conditions.load_presets()]          # a preset added to the file must be offered here
    assert inputs["conditions"]["type"] == "string" and inputs["conditions"]["default"] == ""
    steps = W["jobs"]["radar"]["steps"]
    users = [s.get("name") for s in steps if any("inputs.preset" in str(v) or "inputs.conditions" in str(v) for v in (s.get("env") or {}).values())]
    assert users == ["Scan, write, check, export"]                                      # the doctor steps and the hand-off do not need them
    scan = next(s for s in steps if s.get("name") == "Scan, write, check, export")
    assert scan["env"]["RADAR_PRESET"] == "${{ inputs.preset }}" and scan["env"]["RADAR_CONDITIONS"] == "${{ inputs.conditions }}"
    # data in an environment variable, never text in a command: the two inputs appear nowhere else in the file
    assert TEXT.count("inputs.preset") == 1 and TEXT.count("inputs.conditions") == 1


def test_the_schedule_does_not_set_any_condition():
    assert W[True]["schedule"] and "inputs.preset" not in str(W[True]["schedule"])   # a scheduled run has empty inputs: radar.yaml as it is


# --- the commit step, run for real in a throwaway repository -------------------------------------------------------
import os
import subprocess

import pytest


def commit_script():
    step = next(s for s in W["jobs"]["radar"]["steps"] if s.get("name") == "Commit digests, export and state")
    return step["run"]


def sh(*args, cwd, env=None, check=True):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=check, env={**os.environ, **(env or {}), "GIT_TERMINAL_PROMPT": "0"})


@pytest.fixture
def checkout(tmp_path):
    bare, work = tmp_path / "remote.git", tmp_path / "work"
    sh("git", "init", "-q", "--bare", "-b", "main", str(bare), cwd=tmp_path)
    sh("git", "clone", "-q", str(bare), str(work), cwd=tmp_path)
    (work / "README.md").write_text("x\n")
    sh("git", "add", ".", cwd=work)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init", cwd=work)
    sh("git", "push", "-q", "origin", "HEAD:main", cwd=work)
    return bare, work


def run_commit_step(work, tmp_path):
    return sh("bash", "-e", "-c", commit_script(), cwd=work, env={"GITHUB_REF_NAME": "main"}, check=False)


def test_the_commit_step_succeeds_when_the_run_wrote_nothing(checkout, tmp_path):
    bare, work = checkout                             # the run that failed on GitHub: no digests/, export/ or state/ at all
    out = run_commit_step(work, tmp_path)
    assert out.returncode == 0 and "nothing was written" in out.stdout
    assert sh("git", "log", "--oneline", cwd=bare).stdout.count("\n") == 1


def test_the_commit_step_keeps_partial_output_when_only_some_folders_exist(checkout, tmp_path):
    bare, work = checkout                             # digests written, export refused: the old `git add digests export state` died here
    (work / "digests" / "2026-10-14").mkdir(parents=True)
    (work / "digests" / "2026-10-14" / "x.md").write_text("bài đã viết\n")
    out = run_commit_step(work, tmp_path)
    assert out.returncode == 0, out.stderr
    assert "digests/2026-10-14/x.md" in sh("git", "ls-tree", "-r", "--name-only", "main", cwd=bare).stdout
    again = run_commit_step(work, tmp_path)           # nothing changed: no empty commit
    assert again.returncode == 0 and "nothing new to commit" in again.stdout


def test_the_commit_step_rebases_when_main_moved_during_the_scan(checkout, tmp_path):
    bare, work = checkout
    other = tmp_path / "other"
    sh("git", "clone", "-q", str(bare), str(other), cwd=tmp_path)
    (other / "NOTES.md").write_text("someone else\n")
    sh("git", "add", ".", cwd=other)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "other", cwd=other)
    sh("git", "push", "-q", "origin", "HEAD:main", cwd=other)
    (work / "state").mkdir()
    (work / "state" / "seen.json").write_text("{}\n")
    out = run_commit_step(work, tmp_path)
    assert out.returncode == 0, out.stderr
    tree = sh("git", "ls-tree", "-r", "--name-only", "main", cwd=bare).stdout
    assert "state/seen.json" in tree and "NOTES.md" in tree
