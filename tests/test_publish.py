import datetime as dt
import json
import subprocess

import pytest

from radar import cli, handoff, publish
from tests.support import _Server, fake_github

NOW = dt.datetime(2026, 10, 16, 6, 30, 5, tzinfo=dt.timezone.utc)


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True).stdout


@pytest.fixture
def checkout(tmp_path):
    """A bare 'origin' with main, and a clone of it holding one new results commit, like a runner after the scan."""
    bare, work = tmp_path / "origin.git", tmp_path / "work"
    git("init", "-q", "--bare", "-b", "main", str(bare), cwd=tmp_path)
    git("clone", "-q", str(bare), str(work), cwd=tmp_path)
    (work / "README.md").write_text("x\n")
    git("add", ".", cwd=work)
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init", cwd=work)
    git("push", "-q", "origin", "HEAD:main", cwd=work)
    (work / "digests").mkdir()
    (work / "digests" / "x.md").write_text("bài đã viết\n")
    git("add", ".", cwd=work)
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "radar: scan 2026-10-16", cwd=work)
    return bare, work


def go(work, api, **kw):
    return publish.publish(repo="o/r", token="tok", cwd=work, api=api.url, now=NOW, run_id="12345", attempt="2", **kw)


def pulls(api):
    return [c for c in api.calls if c["path"].endswith("/pulls")]


def test_the_results_go_to_a_new_branch_and_a_pull_request_never_to_main(checkout):
    bare, work = checkout
    api = fake_github()
    try:
        out = go(work, api, run_url="https://github.com/o/r/actions/runs/12345")
    finally:
        api.close()
    assert out == {"status": "opened", "branch": "radar/scan-2026-10-16-12345-2", "url": "https://github.com/example-org/studio/pull/7", "number": 7}
    assert sorted(git("branch", "--list", "--format=%(refname:short)", cwd=bare).split()) == ["main", "radar/scan-2026-10-16-12345-2"]
    assert "digests/x.md" not in git("ls-tree", "-r", "--name-only", "main", cwd=bare)                # main is untouched
    assert "digests/x.md" in git("ls-tree", "-r", "--name-only", "radar/scan-2026-10-16-12345-2", cwd=bare)
    (call,) = pulls(api)
    payload = call["body"]
    assert payload["title"] == "radar: scan 2026-10-16" and payload["head"] == "radar/scan-2026-10-16-12345-2" and payload["base"] == "main"
    assert "draft" not in payload                                          # ready for review: a draft would not be merged by auto-merge
    assert "actions/runs/12345" in payload["body"] and "Update branch" in payload["body"]
    assert call["headers"]["Authorization"] == "Bearer tok"


def test_the_branch_name_is_unique_per_run_and_never_built_from_free_text():
    name = lambda run, attempt: publish.branch_name("2026-10-16", run, attempt, NOW)  # noqa: E731
    assert name("12345", "2") == "radar/scan-2026-10-16-12345-2"
    assert name("12345", "3") != name("12345", "2")                          # a re-run of the same workflow run
    assert name("", "1") == name("abc; rm -rf /", "1") == "radar/scan-2026-10-16-063005"
    assert name("1" * 21, "1") == "radar/scan-2026-10-16-063005"            # more digits than a run id has


def test_the_token_is_only_in_the_environment_of_git_and_the_workflow_token_is_cleared(checkout, monkeypatch):
    bare, work = checkout
    seen = []
    real = subprocess.run

    def spy(args, **kw):
        seen.append((list(args), dict(kw.get("env") or {})))
        return real(args, **kw)
    monkeypatch.setattr(handoff.subprocess, "run", spy)
    api = fake_github()
    try:
        go(work, api)
    finally:
        api.close()
    import base64
    packed = base64.b64encode(b"x-access-token:tok").decode()
    assert seen and all("tok" not in part and packed not in part for args, _ in seen for part in args)  # not plain, not base64, in argv
    pushes = [env for args, env in seen if "push" in args]
    assert len(pushes) == 1
    env = pushes[0]
    # actions/checkout stores the workflow token under the same key and git sends every value: the first entry clears that list
    assert env["GIT_CONFIG_COUNT"] == "2" and env["GIT_CONFIG_VALUE_0"] == "" and env["GIT_CONFIG_KEY_0"] == env["GIT_CONFIG_KEY_1"]
    assert env["GIT_CONFIG_VALUE_1"].startswith("AUTHORIZATION: basic ") and "tok" not in env["GIT_CONFIG_VALUE_1"]    # base64, not plain
    assert "tok" not in json.dumps(pulls(api)[0]["body"])                                              # nor in the pull request text


def test_auto_merge_is_asked_for_only_when_it_is_switched_on(checkout):
    bare, work = checkout
    api = fake_github()
    try:
        plain = go(work, api)
    finally:
        api.close()
    assert "automerge" not in plain and not [c for c in api.calls if c["path"] == "/graphql"]
    api = fake_github()
    try:
        out = publish.publish(repo="o/r", token="tok", cwd=work, api=api.url, now=NOW, run_id="999", attempt="1", automerge=True)
    finally:
        api.close()
    assert out["automerge"] == "requested"
    (call,) = [c for c in api.calls if c["path"] == "/graphql"]
    assert call["body"]["variables"] == {"id": "PR_node_7"} and "MERGE" in call["body"]["query"] and call["headers"]["Authorization"] == "Bearer tok"


def test_a_refused_auto_merge_is_reported_and_the_pull_request_stays(checkout):
    bare, work = checkout
    for answer, expect in (((200, {"errors": [{"message": "Pull request is in clean status"}]}), "not enabled: Pull request is in clean status"),
                           ((403, {"message": "forbidden"}), "not enabled (HTTP 403)")):
        def handle(call, answer=answer):
            if call["path"] == "/graphql":
                return answer
            return 201, {"html_url": "u", "number": 7, "node_id": "n"}
        api = _Server(handle)
        try:
            out = publish.publish(repo="o/r", token="tok", cwd=work, api=api.url, now=NOW, run_id=str(len(expect)), attempt="1", automerge=True)
        finally:
            api.close()
        assert out["status"] == "opened" and out["automerge"] == expect


def test_a_pull_request_that_cannot_be_opened_leaves_the_results_on_the_branch(checkout):
    bare, work = checkout
    api = _Server(lambda call: (403, {"message": "Resource not accessible by personal access token"}))
    try:
        out = go(work, api)
    finally:
        api.close()
    assert out["status"] == "branch-pushed" and "HTTP 403" in out["error"] and out["branch"] in git("branch", cwd=bare)
    assert "digests/x.md" in git("ls-tree", "-r", "--name-only", out["branch"], cwd=bare)                # nothing is lost


def test_a_second_publish_of_the_same_run_does_not_open_a_second_pull_request(checkout):
    bare, work = checkout
    api = fake_github()
    try:
        first, second = go(work, api), go(work, api)
    finally:
        api.close()
    assert first["status"] == "opened" and second == {"status": "branch-exists", "branch": first["branch"]} and len(pulls(api)) == 1


def test_bad_inputs_are_refused_before_anything_is_pushed(checkout):
    bare, work = checkout
    for kw, match in (({"repo": "a/b/c"}, "owner/name"), ({"repo": "../x"}, "owner/name"), ({"repo": "o"}, "owner/name"),
                      ({"base": "ma in"}, "branch name"), ({"base": "a..b"}, "branch name"), ({"token": ""}, "RADAR_PR_TOKEN")):
        args = {"repo": "o/r", "token": "tok", "cwd": work, "now": NOW, **kw}
        with pytest.raises(ValueError, match=match):
            publish.publish(**args)
    assert git("branch", "--list", "--format=%(refname:short)", cwd=bare).split() == ["main"]


def test_a_push_that_fails_raises_so_the_step_goes_red(checkout, tmp_path):
    bare, work = checkout
    git("remote", "set-url", "origin", str(tmp_path / "missing.git"), cwd=work)
    api = fake_github()
    try:
        with pytest.raises(RuntimeError, match="git ls-remote failed"):                                  # the first call says what is wrong
            go(work, api)
    finally:
        api.close()
    assert not pulls(api)


def test_the_command_publishes_from_the_checkout_it_runs_in(checkout, monkeypatch, capsys):
    bare, work = checkout
    api = fake_github()
    monkeypatch.chdir(work)
    for key, value in (("GITHUB_API_URL", api.url), ("RADAR_PR_TOKEN", "tok"), ("GITHUB_REPOSITORY", "o/r"), ("GITHUB_RUN_ID", "777"),
                       ("GITHUB_RUN_ATTEMPT", "1"), ("RADAR_AUTOMERGE", "true")):
        monkeypatch.setenv(key, value)
    try:
        assert cli.main(["publish"]) == 0
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "opened" and out["branch"].endswith("-777-1") and out["automerge"] == "requested"
        assert "actions/runs/777" in pulls(api)[0]["body"]["body"]
        monkeypatch.delenv("RADAR_PR_TOKEN")
        assert cli.main(["publish"]) == 2 and "RADAR_PR_TOKEN is not set" in capsys.readouterr().err
    finally:
        api.close()


def test_an_error_from_git_never_repeats_the_token_or_its_base64_form():
    import base64
    packed = base64.b64encode(b"x-access-token:secret-tok-123").decode()
    for echoed in ("secret-tok-123", packed):
        with pytest.raises(RuntimeError) as err:
            handoff._git(["checkout", echoed], ".", token="secret-tok-123")                         # git echoes the unknown name back
        assert "secret-tok-123" not in str(err.value) and packed not in str(err.value) and "***" in str(err.value)


def test_an_answer_that_is_not_a_pull_request_is_reported_not_a_traceback(checkout):
    bare, work = checkout
    api = _Server(lambda call: (200, ["not", "an", "object"]) if call["method"] == "POST" else (200, []))
    try:
        out = go(work, api)
    finally:
        api.close()
    assert out["status"] == "branch-pushed" and "not an object" in out["error"]


def test_earlier_scan_pull_requests_that_are_still_open_are_named_in_the_new_one(checkout):
    bare, work = checkout
    listing = [{"number": 41, "head": {"ref": "radar/scan-2026-10-14-1-1"}}, {"number": 12, "head": {"ref": "claude/something"}},
               {"number": 40, "head": {"ref": "radar/scan-2026-10-11-9-1"}}, "junk", {"number": 3}]

    def handle(call):
        if call["method"] == "GET":
            return 200, listing
        return 201, {"html_url": "u", "number": 42, "node_id": "n"}
    api = _Server(handle)
    try:
        out = go(work, api)
    finally:
        api.close()
    assert out["earlier_scan_prs"] == [40, 41]                                       # only radar/scan-* heads, oldest number first
    body = [c for c in api.calls if c["method"] == "POST"][0]["body"]["body"]
    assert "#40, #41" in body and "oldest first" in body and "run the scan again" in body


def test_a_failed_listing_of_open_pull_requests_changes_nothing(checkout):
    bare, work = checkout
    api = _Server(lambda call: (403, {"message": "no"}) if call["method"] == "GET" else (201, {"html_url": "u", "number": 7, "node_id": "n"}))
    try:
        out = go(work, api)
    finally:
        api.close()
    assert out["status"] == "opened" and "earlier_scan_prs" not in out
    assert "Earlier scan pull requests" not in [c for c in api.calls if c["method"] == "POST"][0]["body"]["body"]
