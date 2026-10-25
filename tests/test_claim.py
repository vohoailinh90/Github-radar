"""scripts/claim.py: the ledger of claims that keeps two sessions off one item.

Every test runs the real script in a real clone of a local bare repository (git's own server logic decides who wins a push), and the
races start real processes at the same moment. Nothing here needs a network or a GitHub token.
"""

import importlib.util
import json
import os
import stat
import subprocess
import sys
import time

import pytest

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
SCRIPT = os.path.join(SCRIPTS, "claim.py")
T0 = "2026-10-24T10:00:00Z"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull, "GIT_TERMINAL_PROMPT": "0"}
for var in ("CLAIM_NOW", "CLAIM_SESSION", "CLAUDE_SESSION_ID", "CODEX_SESSION_ID"):
    ENV.pop(var, None)
# waits for a start file, then runs the script: every racer is already running Python when the file appears
LAUNCH = ("import os, runpy, sys, time\ngo = sys.argv[1]\nwhile not os.path.exists(go):\n    time.sleep(0.0005)\n"
          "sys.argv = sys.argv[2:]\nrunpy.run_path(sys.argv[0], run_name='__main__')\n")
# the script with git failing as if the network went away from the nth fetch on (and, optionally, for every push after it)
FLAKY = ("import subprocess, sys\nsys.path.insert(0, {scripts!r})\nimport claim\nreal, seen = claim.git, {{'fetches': 0}}\n"
         "def flaky(*a, **k):\n    if a and a[0] == 'fetch':\n        seen['fetches'] += 1\n"
         "    if seen['fetches'] >= {nth} and a and (a[0] == 'fetch' or (a[0] == 'push' and {block_push})):\n"
         "        return subprocess.CompletedProcess(a, 128, '', 'fatal: injected outage')\n    return real(*a, **k)\n"
         "claim.git = flaky\nsys.exit(claim.main(sys.argv[1:]))\n")
# the script with the first call of one git command failing as a dying server would, with no reason given
TRANSIENT = ("import subprocess, sys\nsys.path.insert(0, {scripts!r})\nimport claim\nreal, failed = claim.git, set()\n"
             "def flaky(*a, **k):\n    if a and a[0] == {command!r} and a[0] not in failed:\n        failed.add(a[0])\n"
             "        return subprocess.CompletedProcess(a, 128, '', 'fatal: the remote end hung up unexpectedly')\n    return real(*a, **k)\n"
             "claim.git = flaky\nsys.exit(claim.main(sys.argv[1:]))\n")
# the same, but another session's claim lands just before the push that "dies": the loser of a real race that got no explanation
HANGUP = ("import subprocess, sys\nsys.path.insert(0, {scripts!r})\nimport claim\nreal, state = claim.git, {{'pushed': False}}\n"
          "def flaky(*a, **k):\n    if a and a[0] == 'push' and not state['pushed']:\n        state['pushed'] = True\n"
          "        subprocess.run([sys.executable, {script!r}, 'claim', '--session', 's-b', {key!r}], cwd={other!r}, check=True, capture_output=True)\n"
          "        return subprocess.CompletedProcess(a, 128, '', 'fatal: the remote end hung up unexpectedly')\n    return real(*a, **k)\n"
          "claim.git = flaky\nsys.exit(claim.main(sys.argv[1:]))\n")
# what Claude Code on the web was measured to do to a push: branches only, no delete, no tag, no other ref, no force
STRICT_SERVER = """#!/bin/sh
zero=0000000000000000000000000000000000000000
while read old new ref; do
  case "$ref" in refs/heads/*) ;; *) echo "only branches" >&2; exit 1 ;; esac
  [ "$new" = "$zero" ] && { echo "no deletes" >&2; exit 1; }
  if [ "$old" != "$zero" ]; then git merge-base --is-ancestor "$old" "$new" || { echo "no force pushes" >&2; exit 1; }; fi
done
exit 0
"""


_spec = importlib.util.spec_from_file_location("claim_under_test", SCRIPT)
claim_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = claim_module          # a dataclass looks its module up here
_spec.loader.exec_module(claim_module)


def slug_of(key):
    """The branch name the script gives an item: only for the tests that must put a branch of their own under that very name."""
    return claim_module.normalise(key)[1]


def git(cwd, *args, data=None):
    return subprocess.run(["git", *args], cwd=cwd, input=data, capture_output=True, text=True, env=ENV, check=True).stdout


@pytest.fixture
def origin(tmp_path):
    path = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(path)], check=True, env=ENV)
    return path


def strict(origin):
    hook = origin / "hooks" / "pre-receive"
    hook.write_text(STRICT_SERVER)
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)


def hook(origin, body):
    """A pre-receive hook on the test server: `body` sees $old, $new and $ref of every pushed ref and may `exit 1`."""
    path = origin / "hooks" / "pre-receive"
    path.write_text("#!/bin/sh\nzero=0000000000000000000000000000000000000000\nwhile read old new ref; do\n" + body + "\ndone\nexit 0\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def handmade(cwd, slug, message):
    """A branch claims/<slug> made by hand: one empty commit with `message`."""
    tree = git(cwd, "hash-object", "-t", "tree", "-w", "--stdin", data="").strip()
    who = {"GIT_AUTHOR_NAME": "x", "GIT_AUTHOR_EMAIL": "x@x", "GIT_COMMITTER_NAME": "x", "GIT_COMMITTER_EMAIL": "x@x"}
    commit = subprocess.run(["git", "commit-tree", tree, "-m", message], cwd=cwd, capture_output=True, text=True,
                            env={**ENV, **who}, check=True).stdout.strip()
    git(cwd, "push", "-q", "origin", f"{commit}:refs/heads/claims/{slug}")
    return commit


def clone(origin, tmp_path, name):
    path = tmp_path / name
    subprocess.run(["git", "clone", "-q", str(origin), str(path)], check=True, capture_output=True, env=ENV)
    return path


def run(cwd, *args, session=None, now=None, agent="claude"):
    argv = [sys.executable, SCRIPT, args[0], *(["--session", session] if session else []), "--agent", agent, *args[1:]]
    env = {**ENV, **({"CLAIM_NOW": now} if now else {})}
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, env=env)


def ledger(cwd):
    """{branch name: the record on its tip, or None when the tip is not JSON}, read straight from git, independently of the script."""
    git(cwd, "fetch", "-q", "--prune", "origin", "+refs/heads/claims/*:refs/tests/claims/*")
    out = git(cwd, "for-each-ref", "--format=%(refname)%1f%(contents:subject)%1e", "refs/tests/claims/")
    rows = [r.strip("\n").split("\x1f") for r in out.split("\x1e") if r.strip("\n")]
    result = {}
    for ref, subject in rows:
        try:
            result[ref.removeprefix("refs/tests/claims/")] = json.loads(subject)
        except ValueError:
            result[ref.removeprefix("refs/tests/claims/")] = None
    return result


def items(cwd):
    """{item key: record} for every branch (a branch made by hand shows as '(<branch>)'); the names of the branches do not matter."""
    return {(rec["key"] if rec else f"({name})"): rec for name, rec in ledger(cwd).items()}


def standing(cwd):
    """The items whose tip says claimed (a released item keeps its branch but is not held)."""
    return sorted(key for key, rec in items(cwd).items() if rec and rec.get("state", "claimed") == "claimed")


def branches(cwd):
    """Every item that has a branch, held or not."""
    return sorted(items(cwd))


def listing(cwd, session="x", now=None):
    return json.loads(run(cwd, "list", "--json", session=session, now=now).stdout)


def test_a_free_item_is_claimed_and_listed(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    done = run(a, "claim", "Docs/Reports/Genai-Agents", "--note", "deck", session="s-a", now=T0)
    assert done.returncode == 0 and done.stdout.startswith("claimed docs/reports/genai-agents until 2026-10-24T12:00:00Z"), done.stdout
    assert standing(a) == ["docs/reports/genai-agents"]
    [row] = listing(a, "s-a", T0)
    assert (row["key"], row["state"], row["mine"], row["note"]) == ("docs/reports/genai-agents", "live", True, "deck")
    assert "s-a (claude)" == row["holder"] and row["until"] == "2026-10-24T12:00:00Z"


def test_a_second_session_is_refused_and_told_who_holds_it(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    assert run(a, "claim", "o/orca", session="s-a", now=T0).returncode == 0
    refused = run(b, "claim", "o/orca", session="s-b", now=T0)
    assert refused.returncode == 1
    assert "HELD o/orca" in refused.stdout and "s-a (claude)" in refused.stdout and "until 2026-10-24T12:00:00Z" in refused.stdout
    assert [r["mine"] for r in listing(b, "s-b", T0)] == [False]


def test_the_same_session_renews_and_a_checkout_keeps_one_session_id(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    first = run(a, "claim", "o/orca", now=T0)                       # no --session: the id is made once and kept in the checkout
    second = run(a, "claim", "o/orca", now="2026-10-24T10:30:00Z")
    assert first.stdout.startswith("claimed") and second.stdout.startswith("renewed"), second.stdout
    assert branches(a) == ["o/orca"] and git(a, "rev-list", "--count", f"refs/tests/claims/{slug_of('o/orca')}") == "2\n"       # one branch, two commits
    assert run(b, "claim", "o/orca", now="2026-10-24T10:31:00Z").returncode == 1          # another checkout is another session
    assert listing(a, "x", "2026-10-24T10:31:00Z")[0]["until"] == "2026-10-24T12:30:00Z"   # the renewal moved the end


def test_release_frees_the_item_and_only_the_holder_or_force_does(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "o/orca", session="s-a", now=T0)
    refused = run(b, "release", "o/orca", session="s-b", now=T0)
    assert refused.returncode == 1 and "REFUSED" in refused.stdout and standing(a) == ["o/orca"]
    assert run(a, "release", "o/orca", session="s-a", now=T0).stdout.startswith("released")
    assert standing(a) == [] and branches(a) == ["o/orca"]                                  # released, and the branch stays
    assert [r["state"] for r in listing(a, "s-a", T0)] == ["released"]
    assert run(a, "release", "o/orca", session="s-a", now=T0).stdout.startswith("not held")      # idempotent
    assert run(b, "claim", "o/orca", session="s-b", now=T0).stdout.startswith("claimed")        # a released item is free at once
    assert run(a, "release", "--force", "o/orca", session="s-a", now=T0).returncode == 0 and standing(a) == []


def test_a_live_claim_is_never_taken_over_and_an_expired_one_is(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "o/orca", "--ttl", "1h", session="s-a", now=T0)
    assert run(b, "claim", "o/orca", session="s-b", now="2026-10-24T10:59:00Z").returncode == 1
    took = run(b, "claim", "o/orca", session="s-b", now="2026-10-24T11:01:00Z")
    assert took.returncode == 0 and took.stdout.startswith("took over"), took.stdout
    assert listing(b, "s-b", "2026-10-24T11:01:00Z")[0]["holder"] == "s-b (claude)"
    assert [r["state"] for r in listing(a, "s-a", "2026-10-24T11:01:00Z")] == ["live"]
    assert run(a, "claim", "o/orca", session="s-a", now="2026-10-24T11:02:00Z").returncode == 1     # the old holder is now the stranger
    assert [r["state"] for r in listing(a, "s-a", "2026-10-24T14:00:00Z")] == ["expired"]
    assert run(a, "list", "--live", "--json", session="s-a", now="2026-10-24T14:00:00Z").stdout.strip() == "[]"


def test_renew_extends_only_what_you_hold(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "o/orca", session="s-a", now=T0)
    assert run(b, "renew", "o/orca", session="s-b", now=T0).returncode == 1
    assert run(a, "renew", "o/nothing", session="s-a", now=T0).returncode == 1
    assert run(a, "renew", "o/orca", "--ttl", "5h", session="s-a", now="2026-10-24T11:00:00Z").returncode == 0
    assert listing(a, "s-a", T0)[0]["until"] == "2026-10-24T16:00:00Z"
    run(a, "release", "o/orca", session="s-a", now=T0)
    assert run(a, "renew", "o/orca", session="s-a", now=T0).returncode == 1                       # a released item is not yours any more


@pytest.mark.parametrize("key", ["", "   ", "/etc/passwd", "../x", "a/../b", "a..b", "x;rm", "a?b", "é/é", "x" * 301])
def test_an_item_that_cannot_be_a_branch_name_is_refused_and_nothing_is_claimed(origin, tmp_path, key):
    a = clone(origin, tmp_path, "a")
    refused = run(a, "claim", key, session="s-a", now=T0)
    assert refused.returncode == 2 and branches(a) == [], refused.stderr


def test_a_bad_ttl_session_or_agent_is_a_usage_error(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    for extra in (["--ttl", "0"], ["--ttl", "25h"], ["--ttl", "soon"], ["--ttl", "2d"]):
        assert run(a, "claim", "o/x", *extra, session="s-a", now=T0).returncode == 2, extra
    assert run(a, "claim", "o/x", session="bad session!", now=T0).returncode == 2
    assert run(a, "claim", "o/x", session="s-a", now=T0, agent="Bad Agent").returncode == 2
    assert branches(a) == []


def test_several_items_are_all_or_nothing(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(b, "claim", "o/second", session="s-b", now=T0)
    refused = run(a, "claim", "o/first", "o/second", session="s-a", now=T0)
    assert refused.returncode == 1 and "o/second" in refused.stdout
    assert standing(a) == ["o/second"]                                 # o/first was given back (its branch stays, released)
    assert run(a, "claim", "o/first", "o/third", session="s-a", now=T0).returncode == 0
    assert standing(a) == ["o/first", "o/second", "o/third"]


def test_a_failed_multi_claim_keeps_what_the_session_already_held(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "o/mine", session="s-a", now=T0)
    run(b, "claim", "o/theirs", session="s-b", now=T0)
    assert run(a, "claim", "o/mine", "o/theirs", session="s-a", now=T0).returncode == 1
    assert standing(a) == ["o/mine", "o/theirs"]                       # a renewal is not something this call took, so it stays


def test_a_folder_and_a_file_inside_it_overlap_in_both_orders_and_one_session_may_hold_both(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "docs/reports/x", session="s-a", now=T0)
    refused = run(b, "claim", "docs/reports/x/report.md", session="s-b", now=T0)
    assert refused.returncode == 1 and "overlaps a claim of docs/reports/x" in refused.stdout
    assert standing(a) == ["docs/reports/x"]                           # b yielded: its own tip says released
    run(a, "release", "docs/reports/x", session="s-a", now=T0)
    run(b, "claim", "docs/reports/x/report.md", session="s-b", now=T0)
    assert run(a, "claim", "docs/reports/x", session="s-a", now=T0).returncode == 1
    assert standing(a) == ["docs/reports/x/report.md"]
    assert run(b, "claim", "docs/reports/x", session="s-b", now=T0).returncode == 0       # the same session overlaps itself freely
    assert run(a, "claim", "docs/reports/y", session="s-a", now=T0).returncode == 0       # a sibling folder is no overlap


def test_check_reports_without_writing(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "docs/reports/x", session="s-a", now=T0)
    assert run(b, "check", "docs/reports/x/report.md", session="s-b", now=T0).returncode == 1
    free = run(b, "check", "docs/reports/z", "o/orca", session="s-b", now=T0)
    assert free.returncode == 0 and free.stdout.count("free ") == 2
    assert run(a, "check", "docs/reports/x", session="s-a", now=T0).returncode == 0      # your own claim is not in your way
    assert branches(b) == ["docs/reports/x"]


def test_an_unreachable_remote_exits_3_and_claims_nothing(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    git(a, "remote", "set-url", "origin", str(tmp_path / "no-such-repository.git"))
    lost = run(a, "claim", "o/orca", session="s-a", now=T0)
    assert lost.returncode == 3 and "cannot be used" in lost.stderr and "nothing was claimed" in lost.stderr
    assert run(a, "list", session="s-a", now=T0).returncode == 3


def test_a_url_with_a_password_is_not_echoed(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    git(a, "remote", "set-url", "origin", "https://user:s3cret-token@127.0.0.1:1/x.git")
    lost = run(a, "claim", "o/orca", session="s-a", now=T0)
    assert lost.returncode == 3 and "s3cret-token" not in lost.stderr + lost.stdout


def test_a_branch_made_by_hand_under_claims_is_a_held_item_not_a_crash(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    junk = slug_of("junk")
    commit = handmade(a, junk, "hello, not json")
    [row] = listing(a, "s-a")
    assert row["key"] == f"({junk})" and row["holder"].startswith("unknown")
    assert run(a, "claim", "junk", session="s-a").returncode == 1                         # a fresh commit of unknown origin is live
    later = run(a, "claim", "junk", session="s-a", now="2099-01-01T00:00:00Z")           # ... until the default time-to-live is over
    assert later.returncode == 0 and later.stdout.startswith("took over")
    assert ledger(a)[junk]["session"] == "s-a"
    assert git(a, "rev-parse", f"refs/tests/claims/{junk}^").strip() == commit              # built on top of the foreign commit, never over it


def test_a_branch_deleted_by_hand_is_gone_for_every_checkout_even_one_that_saw_it(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    handmade(a, slug_of("junk"), "by hand")
    assert [r["state"] for r in listing(b, "s-b")] == ["live"]                       # b has now cached it
    git(a, "push", "-q", "origin", f":refs/heads/claims/{slug_of('junk')}")                       # what the holder text tells the owner to do
    assert run(b, "claim", "junk", session="s-b").stdout.startswith("claimed")      # not "held" by a claim that no longer exists


def test_prune_never_deletes_a_live_claim_however_old(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    run(a, "claim", "o/live", "--ttl", "24h", session="s-a", now=T0)
    run(a, "claim", "o/done", session="s-a", now=T0)
    run(a, "release", "o/done", session="s-a", now=T0)
    done = run(a, "prune", "--older", "1s", session="s-a", now="2026-10-24T13:00:00Z")       # o/live began three hours ago and runs for 24
    assert done.returncode == 0 and "deleted o/done" in done.stdout and "o/live" not in done.stdout
    assert branches(a) == ["o/live"] and standing(a) == ["o/live"]


def test_a_lapsed_claim_of_your_own_is_not_a_renewal_when_someone_overlapped_it_meanwhile(origin, tmp_path):
    """Found in review: A's folder claim lapsed, B legitimately claimed a file inside it, and A claiming the folder again was called a
    'renewal', which skipped the overlap check and left both standing."""
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "docs/reports/x", "--ttl", "1h", session="s-a", now="2026-10-24T00:00:00Z")
    assert run(b, "claim", "docs/reports/x/deck.json", session="s-b", now="2026-10-24T02:00:00Z").returncode == 0     # A's claim has lapsed
    again = run(a, "claim", "docs/reports/x", session="s-a", now="2026-10-24T02:00:00Z")
    assert again.returncode == 1 and "overlaps a claim of docs/reports/x/deck.json" in again.stdout, again.stdout
    assert standing(a) == ["docs/reports/x/deck.json"]                                                 # only B stands; A yielded
    assert run(a, "renew", "docs/reports/x", session="s-a", now="2026-10-24T02:01:00Z").returncode == 1     # (and it is not A's to renew now)


def test_a_lapsed_claim_of_your_own_with_nothing_in_the_way_is_claimed_afresh_and_a_live_one_is_renewed(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    run(a, "claim", "o/orca", "--ttl", "1h", session="s-a", now=T0)
    assert run(a, "claim", "o/orca", session="s-a", now="2026-10-24T10:30:00Z").stdout.startswith("renewed")
    assert run(a, "claim", "o/orca", session="s-a", now="2026-10-24T13:00:00Z").stdout.startswith("claimed")
    assert run(a, "renew", "o/orca", session="s-a", now="2026-10-24T20:00:00Z").stdout.startswith("claimed")   # renewing a lapsed one re-checks too


def test_release_of_another_sessions_expired_claim_is_allowed_but_not_of_a_live_one(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "o/orca", "--ttl", "1h", session="s-a", now=T0)
    assert run(b, "release", "o/orca", session="s-b", now="2026-10-24T10:30:00Z").returncode == 1
    assert run(b, "release", "o/orca", session="s-b", now="2026-10-24T11:30:00Z").stdout.startswith("released")


def test_a_yield_the_server_refuses_leaves_a_claim_standing_and_says_so(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "docs/reports/x", session="s-a", now=T0)
    hook(origin, '  [ "$new" = "$zero" ] && continue\n  git log -1 --format=%s "$new" | grep -q \'"state":"released"\' && { echo "no releases" >&2; exit 1; }')
    lost = run(b, "claim", "docs/reports/x/report.md", session="s-b", now=T0)
    assert lost.returncode == 3 and "may still stand until it expires" in lost.stderr and "nothing was claimed" not in lost.stderr, lost.stderr
    assert standing(a) == ["docs/reports/x", "docs/reports/x/report.md"]                              # the stray claim is real, and was reported
    (origin / "hooks" / "pre-receive").unlink()
    assert run(b, "release", "docs/reports/x/report.md", session="s-b", now=T0).returncode == 0 and standing(a) == ["docs/reports/x"]


def test_a_multi_claim_that_fails_in_the_middle_gives_back_what_it_took_or_says_what_remains(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    hook(origin, '  case "$ref" in refs/heads/claims/' + slug_of("o/bad") + ') echo "refused" >&2; exit 1 ;; esac')
    failed = run(a, "claim", "o/good", "o/bad", session="s-a", now=T0)
    assert failed.returncode == 3 and "nothing was claimed" in failed.stderr and standing(a) == []         # o/good was given back
    hook(origin, '  case "$ref" in refs/heads/claims/' + slug_of("o/bad") + ') echo "refused" >&2; exit 1 ;; esac\n'
                 '  [ "$new" = "$zero" ] && continue\n  git log -1 --format=%s "$new" | grep -q \'"state":"released"\' && { echo "no releases" >&2; exit 1; }')
    stuck = run(a, "claim", "o/good", "o/bad", session="s-a", now=T0)
    assert stuck.returncode == 3 and "may still stand until they expire: o-good" in stuck.stderr, stuck.stderr
    assert standing(a) == ["o/good"]


def test_prune_leaves_a_branch_made_by_hand_alone(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    handmade(a, "junk", "by hand")
    run(a, "claim", "o/old", session="s-a", now=T0)
    run(a, "release", "o/old", session="s-a", now=T0)
    done = run(a, "prune", "--older", "1s", session="s-a", now="2099-01-01T00:00:00Z")
    assert done.returncode == 0 and "deleted o/old" in done.stdout and "junk" not in done.stdout
    assert branches(a) == ["(junk)"]


def test_text_from_the_remote_is_printed_without_control_characters_and_a_bool_is_not_a_ttl(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    record = {"key": "a\u001b[31mred", "session": "s-x\u0007", "ttl_s": 3600, "taken_at": "2026-10-24T09:30:00Z", "note": "\u001b]0;title\u0007hi"}
    handmade(a, "escape", json.dumps(record))
    handmade(a, "boolean", json.dumps({**record, "key": "boolean", "ttl_s": True}))
    listed = run(a, "list", session="s-a", now=T0)
    assert "\x1b" not in listed.stdout and "\x07" not in listed.stdout, repr(listed.stdout)
    rows = {r["key"]: r for r in listing(a, "s-a", T0)}
    assert rows["a?[31mred"]["state"] == "live" and rows["(boolean)"]["holder"].startswith("unknown")       # ttl_s: true is not a record


def test_two_keys_that_read_alike_are_two_items_and_neither_replaces_the_other(origin, tmp_path):
    """Codex finding: `docs/reports/x` and `docs-reports-x` shared one branch, so the second claim 'renewed' the first and overwrote its
    key, and a file inside the folder could then be claimed by someone else."""
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    assert run(a, "claim", "docs/reports/x", session="s-a", now=T0).stdout.startswith("claimed")
    assert run(a, "claim", "docs-reports-x", session="s-a", now=T0).stdout.startswith("claimed")          # not 'renewed'
    assert standing(a) == ["docs-reports-x", "docs/reports/x"] and len(ledger(a)) == 2
    refused = run(b, "claim", "docs/reports/x/deck.json", session="s-b", now=T0)
    assert refused.returncode == 1 and "docs/reports/x" in refused.stdout                                 # the folder is still protected
    shared = "r" * 90
    assert run(a, "claim", shared + "/one", shared + "/two", session="s-a", now=T0).returncode == 0       # one 80-character prefix, two items
    assert len(standing(a)) == 4 and len(ledger(a)) == 5                                                    # B's refused attempt left its released branch
    assert all(len(name) <= 91 and not name.endswith(".lock") for name in ledger(a))


@pytest.mark.parametrize("block_push", [False, True])
def test_a_failure_of_the_overlap_check_after_the_push_gives_the_claim_back_or_says_it_stands(origin, tmp_path, block_push):
    """Codex finding: the push succeeded, the fetch of the overlap check did not, and the command said 'nothing was claimed' while the
    claim stood. Now it withdraws the claim, and when even that fails it names the claim that may remain."""
    a = clone(origin, tmp_path, "a")
    code = FLAKY.format(scripts=SCRIPTS, nth=2, block_push=block_push)                  # fetch 1 reads the ledger, fetch 2 is the overlap check
    lost = subprocess.run([sys.executable, "-c", code, "claim", "--session", "s-a", "o/inject"], cwd=a, capture_output=True, text=True,
                          env={**ENV, "CLAIM_NOW": T0})
    assert lost.returncode == 3 and "injected outage" in lost.stderr, lost.stderr
    if block_push:
        assert "may still stand until it expires" in lost.stderr and "nothing was claimed" not in lost.stderr
        assert standing(a) == ["o/inject"]                                                 # and it really does stand
    else:
        assert "nothing was claimed" in lost.stderr and standing(a) == []                  # withdrawn before giving up


@pytest.mark.parametrize("command", ["push", "fetch"])
def test_one_transient_failure_of_a_push_or_a_fetch_is_retried(origin, tmp_path, command):
    a = clone(origin, tmp_path, "a")
    done = subprocess.run([sys.executable, "-c", TRANSIENT.format(scripts=SCRIPTS, command=command), "claim", "--session", "s-a", "o/x"],
                          cwd=a, capture_output=True, text=True, env={**ENV, "CLAIM_NOW": T0})
    assert done.returncode == 0 and done.stdout.startswith("claimed"), (done.stdout, done.stderr)
    assert standing(a) == ["o/x"]


def test_a_push_that_dies_without_a_reason_after_somebody_else_won_is_a_lost_race_not_an_outage(origin, tmp_path):
    """Found by CI (git 2.55): two of five simultaneous takeovers exited 3 'cannot be used' instead of 1 'held'. What git says about a
    refused push differs between versions and a server that dies on a lock says nothing, so who won is decided by where the branch is."""
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    code = HANGUP.format(scripts=SCRIPTS, script=SCRIPT, key="o/x", other=str(b))
    lost = subprocess.run([sys.executable, "-c", code, "claim", "--session", "s-a", "o/x"], cwd=a, capture_output=True, text=True,
                          env={**ENV, "CLAIM_NOW": T0})
    assert lost.returncode == 1 and "HELD o/x" in lost.stdout and "s-b (unknown)" in lost.stdout, (lost.stdout, lost.stderr)
    assert standing(a) == ["o/x"] and items(a)["o/x"]["session"] == "s-b"                 # the winner's claim is untouched


def test_a_claim_is_an_append_only_chain_of_empty_commits_on_one_branch(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    run(a, "claim", "o/orca", session="s-a", now=T0)
    orca = slug_of("o/orca")
    first = git(a, "ls-remote", "origin", f"refs/heads/claims/{orca}").split()[0]
    run(a, "release", "o/orca", session="s-a", now=T0)
    run(b, "claim", "o/orca", session="s-b", now=T0)
    git(a, "fetch", "-q", "origin", "+refs/heads/claims/*:refs/tests/claims/*")
    log = git(a, "rev-list", "--reverse", "--parents", f"refs/tests/claims/{orca}").splitlines()
    assert len(log) == 3 and log[0].split()[0] == first and len(log[0].split()) == 1                     # a root, then two children
    assert [line.split()[1] for line in log[1:]] == [log[0].split()[0], log[1].split()[0]]               # each on the one before: never rewritten
    assert {git(a, "rev-parse", c.split()[0] + "^{tree}").strip() for c in log} == {EMPTY_TREE}           # no file in any commit
    assert [json.loads(git(a, "log", "-1", "--format=%s", c.split()[0]))["state"] for c in log] == ["claimed", "released", "claimed"]
    assert git(a, "ls-remote", "--tags", "origin").strip() == "" and git(a, "status", "--porcelain").strip() == ""
    assert git(a, "ls-remote", "--heads", "origin").count("\n") == 1                                      # the one branch, nothing else


def test_the_whole_cycle_works_on_a_server_that_refuses_deletes_force_pushes_tags_and_other_refs(origin, tmp_path):
    """The policy Claude Code on the web was measured to apply (HTTP 403 on each of those): claim, renew, release, take over, yield and
    roll back all have to be plain pushes of new commits on a branch."""
    strict(origin)
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    assert run(a, "claim", "o/orca", "--ttl", "1h", session="s-a", now=T0).stdout.startswith("claimed")
    assert run(a, "renew", "o/orca", session="s-a", now="2026-10-24T10:10:00Z").stdout.startswith("renewed")
    assert run(b, "claim", "o/orca", session="s-b", now="2026-10-24T10:20:00Z").returncode == 1
    assert run(a, "release", "o/orca", session="s-a", now="2026-10-24T10:30:00Z").returncode == 0
    assert run(b, "claim", "o/orca", session="s-b", now="2026-10-24T10:40:00Z").stdout.startswith("claimed")
    assert run(a, "claim", "o/orca", session="s-a", now="2026-10-25T10:40:00Z").stdout.startswith("took over")
    run(a, "claim", "docs/reports/x", session="s-a", now=T0)
    assert run(b, "claim", "o/free", "docs/reports/x/report.md", session="s-b", now=T0).returncode == 1       # yield + roll back
    assert run(b, "claim", "docs/reports/x/report.md", session="s-b", now=T0).returncode == 1
    assert standing(a) == ["docs/reports/x", "o/orca"]
    refused = run(a, "prune", "--older", "1s", session="s-a", now="2099-01-01T00:00:00Z")           # the server refuses deletes
    assert refused.returncode == 3 and "run prune on a machine that may delete branches" in refused.stderr
    assert branches(a) == ["docs/reports/x", "docs/reports/x/report.md", "o/free", "o/orca"]


def test_prune_deletes_only_old_finished_claims_and_can_be_a_dry_run(origin, tmp_path):
    a = clone(origin, tmp_path, "a")
    run(a, "claim", "o/old", session="s-a", now=T0)
    run(a, "release", "o/old", session="s-a", now=T0)
    run(a, "claim", "o/recent", session="s-a", now="2026-10-26T09:00:00Z")
    run(a, "release", "o/recent", session="s-a", now="2026-10-26T09:00:00Z")
    run(a, "claim", "o/fresh", session="s-a", now="2026-10-26T10:00:00Z")
    run(a, "claim", "o/lapsed", session="s-a", now=T0)                                     # never released: it expired long ago
    later = "2026-10-26T10:30:00Z"
    dry = run(a, "prune", "--older", "1d", "--dry-run", session="s-a", now=later)
    assert dry.returncode == 0 and "would delete o/old" in dry.stdout and "would delete o/lapsed" in dry.stdout
    assert "o/recent" not in dry.stdout and "o/fresh" not in dry.stdout
    assert branches(a) == ["o/fresh", "o/lapsed", "o/old", "o/recent"]                      # a dry run deletes nothing
    done = run(a, "prune", "--older", "1d", session="s-a", now=later)
    assert done.returncode == 0 and "deleted o/old" in done.stdout and "deleted o/lapsed" in done.stdout
    assert branches(a) == ["o/fresh", "o/recent"]
    assert run(a, "prune", "--older", "forever", session="s-a", now=later).returncode == 2


def race(tmp_path, rounds, jobs):
    """`jobs(round)` is a list of (clone, argv tail, session); all of one round start together. Yields each round's exit codes."""
    for number in range(rounds):
        go = tmp_path / f"go-{number}"
        procs = [subprocess.Popen([sys.executable, "-c", LAUNCH, str(go), SCRIPT, args[0], "--session", session, "--agent", "claude", *args[1:]],
                                  cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                  env={**ENV, "CLAIM_NOW": T0}) for cwd, args, session in jobs(number)]
        time.sleep(0.4)                                                  # every racer is waiting on the start file by now
        go.write_text("go")
        codes = [p.wait(timeout=120) for p in procs]
        race.errors = [p.stderr.read() for p in procs]            # what the racers said, for the message of a failing assertion
        yield codes


def test_exactly_one_of_many_simultaneous_claimants_wins(origin, tmp_path):
    clones = [clone(origin, tmp_path, f"c{i}") for i in range(6)]
    for number, codes in enumerate(race(tmp_path, 4, lambda n: [(c, ["claim", f"o/item-{n}"], f"s-{i}") for i, c in enumerate(clones)])):
        assert sorted(codes) == [0, 1, 1, 1, 1, 1], (number, codes, race.errors)
        winner = codes.index(0)
        assert items(clones[0])[f"o/item-{number}"]["session"] == f"s-{winner}"        # the ledger names the one that got exit 0


def test_exactly_one_of_many_simultaneous_takeovers_of_a_stale_claim_wins(origin, tmp_path):
    clones = [clone(origin, tmp_path, f"c{i}") for i in range(5)]
    for n in range(3):
        subprocess.run([sys.executable, SCRIPT, "claim", "--session", "old", "--ttl", "1m", f"o/stale-{n}"], cwd=clones[0], check=True,
                       capture_output=True, env={**ENV, "CLAIM_NOW": "2026-10-24T01:00:00Z"})
    for number, codes in enumerate(race(tmp_path, 3, lambda n: [(c, ["claim", f"o/stale-{n}"], f"s-{i}") for i, c in enumerate(clones)])):
        assert sorted(codes) == [0, 1, 1, 1, 1], (number, codes, race.errors)        # T0 is hours after the stale claim's end
        assert items(clones[0])[f"o/stale-{number}"]["session"] == f"s-{codes.index(0)}"


def test_a_folder_and_a_file_inside_it_never_both_stand_under_a_race(origin, tmp_path):
    a, b = clone(origin, tmp_path, "a"), clone(origin, tmp_path, "b")
    rounds = list(race(tmp_path, 8, lambda n: [(a, ["claim", f"docs/reports/r{n}"], "s-a"), (b, ["claim", f"docs/reports/r{n}/report.md"], "s-b")]))
    for number, codes in enumerate(rounds):
        held = [s for s in standing(a) if s.startswith(f"docs/reports/r{number}")]
        assert codes.count(0) == len(held) <= 1, (number, codes, held, race.errors)           # both may yield; both can never stand
    assert len(rounds) == 8
