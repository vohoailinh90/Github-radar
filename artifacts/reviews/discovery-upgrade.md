# Review: discovery upgrade (T2, `code-reviewer`, independent)

Verdict: approve with fixes. No blocker. The reviewer ran `python3 -m pytest -q` (224 passed at the time), `radar.py check`, `scripts/layout_check.py`,
and fed malformed history shapes to `velocity`/`prune`. Each finding was checked against the code before acting.

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | A corrupt, empty or hand-edited `state/stars.json` raised in `load`/`velocity`/`prune` and would fail every scheduled run | reproduced by reading the code paths | fixed: `history.load` cleans the file and reports what it dropped (`report["history"]["problems"]`); `velocity` and `prune` skip bad shapes. Tests: `test_history.py`, `test_pipeline.py::test_an_unreadable_history_file...` |
| 2 | Code waits `Retry-After + 1`, docs said "exactly" | true | docs and comment now say "plus 1 second" |
| 3 | Spacing is between request starts, docstring overstated | true | docstring corrected |
| 4 | `scan` printed `[rising]` even when the pass is off | true, cosmetic | tag shown only when the pass is on |
| 5 | `slots` is capped at half of `picks_per_run`; with `RADAR_PICKS=1` the default gives 0 slots silently | true | README and `radar.yaml` comment say so |
| 6a | Possible duplicated block in `test_a_young_climbing_repository_gets_the_rising_slot` | **not real**: the file has one copy (the reviewer saw the diff printed twice) | none |
| 6b | "no history = old score" compared two calls of the same function | true | pinned the literal value of the pre-change formula (14.2809 for 20,000 stars, 700 days, pushed 5 days ago) |

Not run by the reviewer (needs a studio checkout): `scripts/studio_contract.py diff|verify`. The export code and `contracts/` are untouched.
Not verifiable offline by anyone: real GitHub behaviour (the Search API, the 1,000-result cap, secondary limits). First real check: a `dry_run` workflow run.
