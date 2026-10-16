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
| 4 | "Mine" detection compares the client clock with `created_at` (5 s margin); a clock that is slow by more than that can lock the button while an old run is active | plausible, not reproduced | documented in `docs/ui.md` (clears when that run ends or on "Quên token"); no code, the cost of an extra request per send is more than the case is worth |
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
