# Review: saved scan conditions (T3, `architecture-critic` on the design, `code-reviewer-t3` on the code)

Route: `python3 scripts/route.py --dimensions 1,2,2,1,2,1 --signals adds-service-dependency,changes-service-contract` -> T3,
`main_with_critic_and_reviewer`, budget 3. Used: the critic (design), the T3 reviewer (code). The page (PR B) gets its own review.

## Design (critic, verdict accept with changes): what was changed because of it

| Finding | Outcome |
|---|---|
| A PAT with Contents:write + Actions:write is every secret (dispatch a pushed branch) | The page's token will have Actions only; moving the secrets into a main-only Environment is the owner's act, documented, not done |
| A PAT in localStorage breaks "secrets only in the environment" | Memory only, pasted each time. CLAUDE.md was NOT edited |
| Weak CSP, `__RADAR_API__` hook, injection | CSP by hash and `page.route` tests are for PR B; topics are held to GitHub's pattern with `fullmatch` in `config.validate` (radar.yaml too); strict JSON; `!r`-truncated errors |
| Layering `file < preset < conditions < env` was unspecified | One layer, validated once at the end, `apply()` copies, report stores resolved values |
| Efficiency claims wrong | Corrected in docs/scan-conditions.md: the models, not the search, take the time; `incomplete_results` and a wait on secondary limits left out until a total cap exists |

## Code (T3 reviewer, verdict approve with fixes)

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | A preset plus inline conditions REPLACED the preset but kept its label | true: `quet-nhanh` + `{"min_stars":3000}` ran 3 posts labelled `quet-nhanh`; an unknown preset name was accepted with inline JSON | fixed: they add up (inline wins per key, `rising` per setting, `buckets` replace), label `name+custom`, a named preset must exist |
| 2 | `[b["id"] for b in cfg["buckets"]]` raised KeyError/TypeError for a malformed radar.yaml | true, a regression against the old clean error | fixed: bucket shape checked first (`validate_buckets`), clean ValueError and exit 2 |
| 3 | The RecursionError branch of `parse_json` was never exercised | true | test added (Python 3.13 parses 1,990 levels, 3.11 raises; both must stay a clean error) |
| 4 | `.strip()` on RADAR_PRESET untested | true, mutation survived | test added, mutation killed |
| 5 | The search spent the rising queries even when half the picks is 0 | true (one pick, slots 1) | fixed: one `conditions.rising_slots()` for search, pick and estimate |
| 5b | A narrowing preset also restricts `--repo --bucket` | harmless, fallback bucket logic covers it | none |

Mutations killed by the tests: topic `match` instead of `fullmatch`, `apply()` without copy, shallow `DEFAULTS`, no bool check, no duplicate-key hook,
no topic check in `validate`, no `report["conditions"]`, preset beating inline, no langs checks, ignoring RADAR_PICKS, no length cap,
inline replacing the preset, no strip, slots ignoring the half-of-picks cap.

Not verified offline: a real `workflow_dispatch` with the new inputs (`docs/scan-conditions.md` has the manual checklist).
