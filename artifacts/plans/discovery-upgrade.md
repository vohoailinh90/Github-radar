# Plan: discovery upgrade (T2, claude lane)

Requirement (user, 2026-10-16): research which repositories scan other GitHub repositories and how, then improve this one.
Research and sources: `docs/research.md`.

Routing: ambiguity 1, scope 2, architecture 1, dependencies 1, risk 1, verification 1 = 7 -> T2, no signals
(`python3 scripts/route.py --dimensions 1,2,1,1,1,1`): `main_with_architect_and_reviewer`, required `code-reviewer`, budget 2.
No cross-service contract changes (`contracts/studio-layouts.json` untouched), so the architect was not spawned.

## Decisions

1. Measure star growth instead of guessing it (`radar/history.py`, `state/stars.json`). One point per repository per UTC day;
   velocity = difference / real gap to the stored point closest to 7 days (3..21); unknown is `None`, never 0; the lifetime
   average stays as the fallback so the first scan behaves as before. Saved before any model call so a timed-out run keeps it.
2. A second, "rising" search pass per topic (young repositories, lower stars floor) and `rising.slots` reserved picks (at most half
   of them). Without a reserved slot those repositories can never win on `ln(stars)`. Off with `rising.slots: 0`.
3. Search pacing (2.1 s) and a wait of `Retry-After` + 1 s (<= 60 s) on 403/429, instead of dropping the topic on the first 403.
4. Two report-only flags (`few-forks`, `star-spike`), `shortlist` and `history` in the run report. Flags never change score or drop a repo.
5. Not changed: facts, prompts, gates, studio export. Velocity is not given to the model, so no new claim can enter a draft.

## Acceptance (each has a check)

- Velocity arithmetic, gaps, unknown vs zero, prune, atomic save: `tests/test_history.py`.
- Score unchanged without history; measured beats lifetime; flags; rising pass queries and switch; slot rules: `tests/test_discover.py`.
- Pacing and `Retry-After` handling against a real local HTTP server: `tests/test_github.py`.
- Snapshot written on a real run and kept when every model fails, not written by a dry run, measured on a later scan,
  shortlist, rising pick: `tests/test_pipeline.py`.

## Not verifiable here

- Real GitHub: the fake server filters `stars:>=` and `created:>=` like the Search API, but the real topic names, result counts and
  how many repositories qualify for the rising pass are unknown until a `dry_run` workflow run. Check `dropped` and `history` in its log.
- The Search API's secondary-limit behaviour is implemented from GitHub's documented `Retry-After` contract (docs.github.com was not reachable from this environment).
