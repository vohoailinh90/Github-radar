# Review: github-radar (T2, `code-reviewer`, 1 of 2 agent slots)

Reviewer verdict: **APPROVE with fixes** (13 findings, none unsafe in a normal scheduled run). It re-ran 62 tests, flake8, the real
`studio.py check` (0 errors, 0 warnings), and 17 mutation probes; 14 were caught, 3 were not. All dispositions below were
re-verified by tests after the fix (97 pass); the 3 missed mutations were re-probed.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | high | URL gate used a short TLD allow-list; many hidden links passed, and it differed from the studio's rule (`planner.py` passed here, failed `studio.py check`) | Fixed: `radar/urls.py` uses the studio's own pattern and TLD file (`contracts/tlds.txt`, drift-checked), plus NFKC, zero-width, `[.]`, `。`; `javascript:`, `](`; bundle re-validated; domain-shaped tokens stripped from posts |
| 2 | high | One GitHub error aborted the run and lost state | Fixed: per-repo errors hold that repo; a failing search is counted, not fatal |
| 3 | med | Second run the same day clobbered the campaign | Fixed: `radar-<date>-2` slug for digests, campaign and run report; `validate` accepts many campaigns |
| 4 | med | Repos remembered even when the bundle was refused | Fixed: remembered only after the bundle is written |
| 5 | med | Checker silently fell back to the writer's family; `family()` guessed from provider | Fixed: vendor table by model name; run report flags `independent_checker: false` and warns |
| 6 | med | Number gate: `1.5k` passed for 15,234 stars (read as 15 x 1000), `v2.3.1`/`0.5` false positives, `100 %`, `game changer` | Fixed: Decimal readings, unit counts need a decimal reading within 5% of a real count, flattened hype match |
| 7 | med | Command check was a substring test; fence breakout | Fixed: whole README line or inline-code span, no backtick/newline; digest text is Markdown-escaped |
| 8-10 | low | `readme-*` evidence, hashtags unchecked, raw Markdown fields | Fixed |
| 11 | low | `doctor --ping` could redden a scheduled run | Fixed: keys check is required, model listing is informational |
| 12 | low | Existing remote branch made the handoff exit 2 | Fixed: reported as `branch-exists` |
| 13 | low | Checker is not re-run after the fix round | Accepted: the deterministic gates re-run; documented |

Mutations missed by the first suite: (a) cross-family filter, (b) primary-language rule, (c) `protocol.ext.allow=never`.
(a) and (b) now fail a test. (c): git 2.43 already denies `ext::` by default, so only the pinned-config test can notice the line.

Unresolved: written-out numbers ("one hundred") are not checked; the gates cannot judge a wrong mechanism that cites a real path;
nothing was run against real GitHub, keys or models.
