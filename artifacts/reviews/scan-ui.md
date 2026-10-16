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

## Codex review of head 1549385 (1 finding, P2, confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | A run-list request still pending for repository A was not invalidated when the Repo field changed to a repository with no followed send, so its late answer filled the table while the form targeted B | true | every change of the Repo field now invalidates pending looks, stops the pending poll and empties the table; it looks again only when the new repository has a followed send; two tests (a held answer; a table with rows), mutations killed |

## Codex review of head b20e99f (1 finding, P2, confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | Changing one field made the page send its whole resolved snapshot as `conditions`; the runner applies that after its current preset and `radar.yaml`, so a page that had gone out of date pinned old values (and stale buckets could fail the run), against what `docs/ui.md` promised ("only the differences") | true: `dispatchInputs` serialised the whole object when anything differed | `delta`: only the fields that differ from the chosen preset go (`rising` setting by setting, `langs` and `buckets` whole, as the runner replaces those); tests: exact deltas for six changes, an empty delta for none and for key order, and the runner (`from_env`/`apply`) turns each delta into the values on the form; four mutations killed |

## Codex review of head 14f1979 (2 findings, both P2, both confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | Leaving a repository stopped the looking for its send; coming back after the two-minute wait the page treated the wait as over (nothing had been seen) and enabled the button before the reload could find the still-active run | true | the wait is over only when a look that SUCCEEDED after the deadline found nothing (`checked`); not looking or a failed look is not evidence; a held-reload test with a fake clock fails on the old page; mutations killed |
| 2 | Watches were keyed by the exact text, but GitHub reads owner and repository names without regard to case, so `Owner/Repo` and `owner/repo` were two repositories | true | keys (and the branch cache) are lower-cased (the pattern is ASCII only); a test sends to one spelling and checks two others |

## Codex review of head 35c6a28 (1 finding, P2, confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | "Quên token" pressed while the dispatch was in flight: the late answer recreated the watch, the token was empty so no look could follow, and putting the token back only refreshed the button, leaving it locked with nothing to resolve it | true | "Quên token" now ends the session: a send under way when it is pressed leaves no watch behind (guards after the branch lookup, the list read, the POST, and in the failure path) and says the command may have reached GitHub; a token put back while a send is followed makes the page look again (on leaving the field, which fires where `change` does not, and on "Kiểm tra token"); and the page says why the button is off. Tests for each, with a held and a lost answer; mutations killed. |

## Codex review of head d5cccb4 (1 finding, P2, confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | The branch check kept a 255-character cap that the git ref rules do not have, so a hierarchical default branch of more than 255 characters was refused | true: `git check-ref-format` sets no total length | the cap is gone (the value only goes into JSON; GitHub does its own checking); the name is cut to 80 characters where the page shows it; table cases at 256, 301 and 5000 characters; the mutation (cap back) is killed |

## Codex review of head dec9b1e (2 findings, both P2, both confirmed)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | After "Quên token" while a send hangs, the `sending` flag stayed set until the old request ended, so a new session's button stayed off (and an old send's `finally` could clear the flag of a newer one) | true | "Quên token" resets the flag; a send ended by it no longer touches the flag in its `finally`; two tests (a held answer; two sends, the first released while the second is still under way); mutations killed |
| 2 | The poll continued only while the current look saw an active run; after a failed look an externally started run's row went stale | true | the page remembers whether the last good look saw an active run and keeps looking after a failure; reset on repository change and "Quên token"; fake-clock test, mutations killed |

Note on the process: this was the eleventh Codex round on this one page. The later findings are all edge cases of the same lock (timing, identity, session end). Each was reproduced before it was fixed and each fix has a test that fails on the page before it; none was dropped except the one-second concurrent-dispatcher case (a P2 rejected with evidence, written in `docs/ui.md`).

## Codex review of head dec9b1e, as seen by Codex while the PR still showed that head (1 finding, P2)

(The branch was already at 7f24306; the pull request object lagged by seconds, so that review ran on the previous head and does not count for the current one. A new review was requested after this fix.)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | The list read before a send may already hold a queued `workflow_dispatch` (waiting behind a running scan); the page used it only for the baseline and sent anyway, replacing it (`concurrency: radar` keeps one waiting run) | true: replacement of a waiting run is GitHub's rule, documented from the start, but the page did nothing to tell the person | not refused (what GitHub calls a run held by the group, `pending` or `queued`, is unverified, so a hard refusal could block legitimate sends): the page asks once ("gửi lúc này có thể thay nó") and sends on the second click; running runs do not trigger it; the answer is for one send and one waiting set, and does not carry over to a changed queue or a new session; tests and mutations killed; the unverified status value is listed in `docs/ui.md` |

## Codex review (code and security) of head 928d53b

The ordinary review of `928d53b` found nothing ("Didn't find any major issues"). The security review of the same head returned two P2 findings, both confirmed:

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | The list read before a send was filtered by `event=workflow_dispatch`, so a scheduled scan waiting in the same `radar` concurrency group was not seen and a manual send could cancel it without the warning | true: the workflow's schedule and manual runs share the group | the filter is gone everywhere (the table now shows scheduled runs too); tests: no `event=` in any request, none in the page source; the mutation (filter back) is killed |
| 2 | `docs/ui.md` said the token "only has the right to run workflows", which understates *Actions: Read and write* | true: it also cancels, re-runs and deletes runs and logs, disables and enables workflows and deletes caches and artifacts of the repository (it does not read or write code, secrets or variables, and cannot edit the workflow file) | the text lists what the permission allows and what it does not, says that an existing branch with a modified workflow could be run through the API (the page only runs the default branch) and that the `radar` Environment limited to `main` is what closes that, and what a leaked token costs; README and the page's own text agree |
