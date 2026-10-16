# Review: the on-demand scan page (T2, `code-reviewer`, independent)

Route: `python3 scripts/route.py --dimensions 1,1,1,1,2,2 --signals ""` -> T2, required `code-reviewer`, budget 2. Used: 1.
Verdict: approve. The reviewer ran the suites, then 28 one-line mutations of a copy of the page (re-synced hashes after each); 24 were killed, 4 survived.
It tried to break each promise (token never kept, nothing from GitHub becomes markup, CSP and framing, parity with Python, safeguards on sending) and could not
break promises 1 to 3 and 4. Defects were minor; each was reproduced before it was fixed.

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | "My run is active" flag survived "Quên token" and a failed run list: the button stayed off | true (reproduced in Chromium) | the flag is cleared on forget, on a failed or non-200 list, and when the repository field changes; tests `test_forgetting_the_token_frees_the_button...`, `test_a_failed_run_list_does_not_leave_the_button_off` fail on the old page |
| 2 | Run links read the repository field again after the request: typed text could end up in a link | true (path mismatch only: fixed `https://github.com/` prefix, `SEGMENT` characters) | one validated `repo` for the request and every link; `test_run_links_point_at_the_repository_the_list_was_asked_for` fails on the old page |
| 3 | `go()` and `checkToken` re-read repo, single repo, bucket and branch after an `await`; a branch read for one repo could be applied to another; `go()` did not check the single repo itself | true | all fields read once at the start; the single repo is validated in `go()`; the branch is kept with the repository it was read for; three tests fail on the old page, the single-repo guard has a forced-click test whose mutation is killed |
| 4 | "Mine" detection compares the client clock with `created_at` (5 s margin); a clock that is slow by more than that can lock the button while an old run is active | plausible, not reproduced | first documented only; Codex raised the mirror case (clock ahead) on the next head and it was fixed at the root, see the second Codex round below |
| 5 | Test gaps: the `QUET` guard in `go()` and "bucket only with a single repo" were untested at the code level | true (mutants survived) | forced-click test for a real scan without the word, test for the bucket; both mutations now killed |
| - | Not fixed on purpose: the grep list in `test_ui.py` can be bypassed by string concatenation | true | the hostile-text browser test is the real guard; the grep list is a tripwire for honest edits |
| - | Equivalent mutants: `\d` vs `[\d.]` in the integer reader (`Number.isInteger` still rejects), `roundHalfEven` on `pace_seconds` (an integer today; Python rounds it) | true | left as is; if `pace_seconds` becomes fractional the Node parity test over the estimate will fail |

Not covered by anyone: real CORS from `file://`, the real dispatch answer (204), real fine-grained permission names, the real concurrency cancellation text
(`docs/ui.md` has the 5-minute checklist; Codex review is the second reader).

## Codex review of head f05dbea (2 findings, both P2, both confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | "Kiểm tra token" said the token is usable although only read access was proved (two GETs); a read-only Actions token then gets 403 on the first send | true: both GETs succeed with Actions read | the message now says what was checked and that write access shows only on the first send; `docs/ui.md` says the same; `test_the_token_check_says_only_what_it_checked` fails on the old page |
| 2 | After an accepted dispatch the run list may not show the run yet; the button re-enabled and a second send could replace the waiting run | true: the flag only covered a run already listed | the page stays locked from an accepted dispatch until a listed run is "mine" or 2 minutes pass; `go()` enforces it (a forced click is refused); a refused dispatch starts no wait; four tests, each mutation killed |

## Codex review of head 8edbc94 (4 findings, all P2, all confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | The single-repository bucket list offered every bucket although a preset or an unticked bucket removes some; the runner (`discover.requested`) refuses a bucket not in the resolved configuration | true: `bucket not in ids` raises, `ids` come from the resolved `cfg["buckets"]` | the list follows the buckets the scan keeps, a dropped choice is reset visibly, and `bucketFor` refuses one that is not kept (Node-tested); browser tests incl. a value smuggled into the select |
| 2 | "Mine" used the client clock against `created_at`: a clock more than 5 s ahead never recognised the run, so the button stayed locked for two minutes (the mirror of review finding 4) | true | the run list is read before the send and the run with a larger id than any listed then is "mine" (ids only grow); no clock involved; if the list cannot be read nothing is sent; tests with clocks one hour behind and ahead, a run listed before the send, and a failing list |
| 3 | The branch allowlist (`[A-Za-z0-9._/-]`, 100 characters) refused names GitHub allows (`release@next`, `feature+plus`, long names) | true | `isBranch` follows `git check-ref-format` (it only ever goes into JSON, never a shell or URL); hostile values with spaces, `..`, `@{`, control characters are still refused; Node table test and browser tests on both entry paths |
| 4 | The estimate for a single repository still counted every topic and `picks_per_run` posts, although the runner skips the search and writes one repository | true: `pipeline.run` calls `discover.requested` and no search | `estimateFor` (0 searches, one post per language), same arithmetic as `conditions.estimate`, compared with Python; browser test on the text |

## Codex review of head 84e6615 (2 findings, both P2)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | Another dispatcher's run that gets an id above the snapshot (listed already finished or cancelled) can be taken for the run just sent, so the button unlocks while the real one is still unindexed and a quick second send could replace it | the path exists but is far-fetched: it needs a foreign dispatch in the roughly one-second gap between the page's snapshot and its own send, and that run to be finished or cancelled before ours is indexed; a scan job needs well over the indexing delay to finish, so only an instant cancellation by the concurrency group fits; one owner, one repository | **rejected, no code** (a P2; a fix needs a unique correlation id as a new workflow input, a change to the workflow's contract for a one-second window); the limit is written in `docs/ui.md`; reported to the owner in the PR thread |
| 2 | The estimate for a dry run (the default) still showed model calls and pauses, although `pipeline.run` returns before them (`if dry_run or not picks`) | true | `estimateRun`: a dry run keeps the search and shows no model calls and no pauses; Node test against Python and mutation-killed browser tests |

## Codex review of head b565a20 (1 finding, P2, confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | After an accepted dispatch, a failed answer from the run list (non-200 or a network error) left `loadRuns` without scheduling the next look, so the run never appeared and the button stayed off until the person refreshed | true: the failure paths returned before the scheduling line | the scheduling moved into a `finally`, so the page keeps looking while a run is active or the run just sent is not listed yet, also after a bad answer; `test_a_failed_answer_while_waiting_for_the_run_does_not_stop_the_looking` (fake clock) fails on the old page, and the mutation (no look after a failure) is killed |

## Codex review of head 58e8f78 (2 findings, both P2, both confirmed; one root cause)

Both came from the page treating "I do not know" as "finished/not sent". The rule now: when unsure, keep the lock (never send a second time on a guess).

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | A failed or malformed run-list answer cleared the active-run flag, so the button re-enabled while the run was still queued | true (my own fix for review finding 1 did this) | a failed look keeps the last known state and the page keeps looking until a good answer says the run ended; "Quên token" or a reload frees it; tests with a fake clock, mutations killed |
| 2 | If the answer to the dispatch is lost (connection drop after the server accepted it), the button re-enabled and a retry could replace the first run | true | an unanswered send, or a 5xx, is treated as possibly sent: the page enters the discovery wait, recognises the run by id, asks for the word again, and does not allow a second send at once; tests for a dropped connection, 502, 504, a forced second click, and the wait ending after 2 minutes |

## Codex review of head fbf4e4e (2 findings, both P2, both confirmed; the cause was how the tracking state was kept)

The state of "the send I am following" lived in four loose variables that were reset from several places. Instead of patching each path it became one object, kept per repository.

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | Typing another repository wiped the tracking; typing the original back showed an unlocked button while its run was still queued | true | `watch = { repo, sentAt, baseline, seen, active }`; the lock applies only to its own repository and survives going away and coming back; returning triggers a look; runs of another repository are never marked "mine"; three tests, each mutation killed |
| 2 | Overlapping run-list requests: an older (empty) answer arriving after a newer one cleared the active flag while `seen` stayed true, enabling a second send | true | requests are numbered and only the newest answer may change state, schedule polling or refresh; a test holds one answer back with a fetch wrapper and delivers it late; fails on the old page |

## Codex review of head 194f5d4 (1 finding, P2, confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | The "per repository" tracking was still one object: a send to repository B replaced the one for A, so going back to A unlocked it while its run was queued | true | a `Map` keyed by repository; a send adds or replaces only its own repository's entry; "Quên token" clears all; test fails on the old page, mutations killed |

Test hygiene found on the way: the fake-clock tests waited with `time.sleep`, which does not let Playwright run the route handlers, so a clock jump could precede the page's own timer (a test race, not a page defect). They now wait with `wait_for_timeout` until the expected request count is reached; repeated runs are stable.
