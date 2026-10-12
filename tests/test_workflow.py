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
    assert carrying == ["Doctor (keys and models)", "Scan, write, check, export", "Hand off to tool-marketing-studio (draft pull request)"]
