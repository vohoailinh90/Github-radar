# Review: claims for shared work, and standing authority for Moda reports (T2)

Reviewer: `code-reviewer` (independent, one spawn; base budget 1 of 2 used, no reserve) and then the pull request's Codex review. Verdict on the first build:
**CHANGES_REQUIRED** (one real concurrency defect, the rest low). All findings are fixed in the final head, each with a test that fails
without the fix (mutation-checked).

## Findings and what was done

| # | Severity | Finding | Outcome |
|---|---|---|---|
| F1 | high | A claim or `renew` of your **own expired** claim was labelled "renewed", which skipped the overlap check. Scenario (reproduced by hand before the fix): A holds `docs/reports/x` for 1h, B claims `docs/reports/x/deck.json` two hours later (legitimate, A lapsed), A claims the folder again: both stood. | Fixed: only a still-live own claim is a renewal; a lapsed one is "claimed" and checked again (`take`). Tests: `test_a_lapsed_claim_of_your_own_is_not_a_renewal_when_someone_overlapped_it_meanwhile`, `..._with_nothing_in_the_way_is_claimed_afresh_and_a_live_one_is_renewed`. Reverting the fix is caught. |
| F2 | low | A `Remote` error while yielding, or in the middle of a multi-claim, escaped as "nothing was claimed" while a claim stood. | Fixed: `Remote.partial`; a failed yield or rollback reports "a claim of yours may still stand until it expires" and names it. Tests with a server whose hook refuses releases or one branch. |
| F3 | low | `prune` could delete a hand-made `claims/*` branch older than 30 days. | Fixed: records that are not ours are skipped; documented. |
| F4 | low | `release` refused another session's already **expired** claim (pure friction). | Fixed: refused only while the claim is live. |
| F5 | nit | `session_id` traceback on a read-only git dir; `valid()` accepted `ttl_s: true`; remote text printed with control characters. | Fixed: usage error naming `--session`; `type(...) is int`; `plain()` strips control characters from keys, holders and notes. Tests for the last two. |

Confirmed by the reviewer and not changed: claim vs claim and takeover vs takeover are sound (every change is a child of the tip that
was read; `settle` reads a stale parent as a lost race and a hook or policy refusal as an error); folder vs file can at worst both
yield (a livelock, never a double hold); release vs takeover has no double hold; no injection path (keys never reach git's argv, the
slug is `[a-z0-9._-]`, `..` and `.lock` refused, a leading `-` is argparse's); the docstring, `docs/claims.md` and CLAUDE.md agree on
the exit codes (the table now also says an exit 3 can leave a claim standing); the generated team-onboarding block of CLAUDE.md is
untouched; the new sections do not contradict "Drafts only", the pull request lifecycle or "hooks are not wired".

## Codex review, round 1 (head f7d5555): two P2 findings, both reproduced, both fixed

| Finding | Reproduction | Fix and test |
|---|---|---|
| The overlap check after a successful push can fail on the network, and the command said "nothing was claimed" while the claim stood. | Injected an outage at the second fetch: exit 3, and `list` still showed the claim live. | `take` now withdraws the claim (a `released` commit) and, when even that push fails, reports that it may still stand (`partial`). Test `..._gives_the_claim_back_or_says_it_stands` (both branches, with a network that fails mid-call). |
| Distinct keys shared one branch (`docs/reports/x` and `docs-reports-x`): the second claim was a "renewal" that replaced the first's key, and a file inside the folder could then be claimed by another session. | Reproduced: the second command printed `renewed`, B's claim on `docs/reports/x/deck.json` succeeded. | Every branch name carries 10 hex characters of the hash of the whole key. Test `test_two_keys_that_read_alike_are_two_items_and_neither_replaces_the_other` (also two keys with one 80-character prefix). |

## Codex review, rounds 2 to 8: one P2 finding each, every one reproduced, fixed, answered on its thread

Each test below fails on the previous script, and each part of each fix has a mutation in the manifest.

| Round (head) | Finding, as reproduced | Fix and test |
|---|---|---|
| 2 (228c63e) | A renewal skipped the overlap check: A reads its live claim just before it lapses, B claims a file inside it once it has, A's delayed push lands; both stood. | The check follows every push, a renewal included; if it cannot be made for a renewal the error says the claim stands. `test_a_renewal_that_crosses_its_own_expiry_rechecks_overlap`. |
| 3 (26a64c4) | The lost-race rule read a branch already at **our** commit (push accepted, acknowledgment lost) as somebody else's win: `claim o/new o/held` left `o/new` live, not rolled back. | A tip equal to the pushed commit is a success, checked before the lost-race test. `test_a_push_the_server_accepted_but_whose_acknowledgment_was_lost_is_a_success`. |
| 4 (d59703b) | `renew` of several lapsed claims did not give back the first when the second yielded. | `claim` and `renew` share one loop (`take_all`) with the rollback; a genuine renewal is not given back. `test_renewing_several_items_is_all_or_nothing_for_the_ones_it_has_to_claim_afresh`. |
| 5 (b2c7e8c) | A failed push followed by a failed `ls-remote` said "nothing was claimed" while the claim stood. | That case is `partial`: the claim may still stand and is named. `test_a_failed_push_whose_outcome_cannot_be_read_back_says_the_claim_may_still_stand`. |
| 6 (ddb5638) | `--ttl 1s`, the clock moves at the overlap check, B takes the item over: A exited 0 with a deadline calculated after the call. | The same fetch checks the item's own tip is still ours and live (clock read after the fetch); else read again. A success prints the stored expiry. Three tests (taken over, lapsed, stored expiry). |
| 7 (7b1e1cf) | Two items, `--ttl 1s`, the clock moves at the second item, B takes the first: both exited 0. | A call with several items fetches once more and every item must be ours and live; else what it took afresh is given back, exit 1. A single item pays nothing. Three tests (taken over, ran out, final check unreachable). |
| 8 (b2b65e8) | `prune --older 1h` selected a 24 h claim one second after it expired: the retention was counted from the acquisition. | It counts from the release, or from the expiry of a lease that lapsed. `test_prune_counts_the_retention_from_when_a_claim_ended_not_from_when_it_began`. |

Round 7 reached the PR under the owner's account: the standard review requested on 0bcaf79 showed "running" for over an hour and delivered nothing.

## CI failure on f7d5555 (git 2.55 on the hosted runner)

`test_exactly_one_of_many_simultaneous_takeovers_of_a_stale_claim_wins` failed in CI in its first round: codes `[1, 1, 3, 0, 3]`, two losers
exited 3 ("the ledger cannot be used") instead of 1 ("held"). It did not reproduce locally (git 2.43; 8 parallel copies; pinned to one
core). Cause class, reproduced with a wrapper that makes a push die with "the remote end hung up unexpectedly" just after another session's
claim landed: the script read **what git said** about a refused push, and a loser whose push is refused without a "!" line was taken for
an outage. It is not an outage when the branch is no longer where the loser built on it.

Fix: `Ledger.push(slug, sha, parent)` decides by the branch's tip (`ls-remote`): moved means a lost race, whatever git called it; only a
refusal with the tip unmoved (a hook, a policy, an outage) is an error, after one more try. `fetch` also gets one retry. The three new
tests fail on the old script with the same exit 3, pass on the new one, and each new branch of the logic has a mutation. The race tests
now print the racers' stderr when an assertion fails, so a recurrence explains itself. Not reproduced on git 2.55 itself (its source could
not be downloaded here), so the claim is: same failure class, same exit codes, fixed by a rule that does not depend on the wording.

## Moda grant (`.claude/settings.json`)

The reviewer could judge by name only. The tool descriptions were read when the list was made: `canvas_edit` is a sandboxed JS batch edit
of existing nodes (no generation, no credits); `export` is free and returns a short-lived download link to the file, not a share of the
canvas; `ask_expert`, `template_*`, `brand_list/show`, `canvas_list/read/search/screenshot`, `task_status`, `moda_bootstrap` and
`load_skill` read. Not granted and pinned by `tests/test_moda_settings.py`: delete, share, `canvas_update` (its template flag publishes
to the team), `canvas_edit_image` and `task_delegate` (credits), `drive_*`, `brand_*` writes, `media_*`, `site_*`, `upload`, `edit_*`.

## Verification (final head)

- `python3 -m pytest -q`: 1195 passed, 1 skipped. `tests/test_claim.py` 58 and `tests/test_moda_settings.py` 4 are among them.
- CI's blocking lint (`flake8 --select=E9,F63,F7,F82`): 0. The non-blocking style report has long lines in the new script, as the repo does elsewhere (586 in all).
- Mutation check: 46 breakages of the script in scratch copies (the 16 of the first build, the reverse of each fix above, the Codex fixes of rounds 1 to 8, the three of the CI fix, and others); all 46 caught on the final code. One survived at first (the retry masked the rule that a moved branch is a lost race, so a single injected hang-up never reached it); the hang-up test now also runs against a server that keeps dying.
- Real remote, once, before the review: a throwaway branch went through take over, held, renew, release, claim, release as fast-forward pushes.
- `python3 scripts/layout_check.py`, `python3 radar.py check`, `python3 scripts/vendor_impeccable.py check`, `team_onboard.py apply --check`: clean.

## Unresolved

- **A leftover branch `claims/_probe1792885729`** on the real remote (empty-tree commits, state released). Measuring which pushes the web
  environment allows created it, and deleting it is refused from here (HTTP 403 by push and by API). Harmless; the owner can delete it.
- GitHub itself was not raced (the race tests use a local bare repository, the same receive-pack code path).
- Nothing forces an agent to call `claim.py`; a hook that refuses a write to a claimed path is possible later.
- Whether Claude Code applies a project `.claude/settings.json` to every cloud session cannot be tested from inside a session.
- Clock skew shifts expiry by the skew; the 2 h default tolerates minutes.
