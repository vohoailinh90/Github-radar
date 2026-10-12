# Plan: github-radar (T2, claude lane)

Requirement: a repo that twice a week (Wed + Sat) scans top-rated free GitHub repos on AI / software / solutions / startups,
writes deep, visual, easy digests the owner learns from, using free models per `docs/vps-team.md`, and hands content to
`tool-marketing-studio` for Facebook and other channels.

Routing: dimensions ambiguity 1, scope 2, architecture 1, dependencies 2, risk 1, verification 1 = 8 -> T2; signal
`adds-service-dependency` (cross-service-change, min T2). Required agent: `code-reviewer`; architect not fired (no contract changed).

## Design

1. **discover** (`discover.py`): GitHub Search per bucket topic; keep SPDX-free licences, not archived/fork, pushed recently,
   >= `min_stars`, not yet covered. Score = ln(stars) + 0.5 ln(30-day star velocity) + 1 if pushed in 30 days. Buckets rotate by date.
2. **facts** (`facts.py`): metadata, cleaned README (<= 12k chars), top-level tree plus children of src/docs/... The only source of claims.
3. **write** (`write.py`, `llm.py`): writer model returns strict JSON in the target language; a checker of another family lists
   blockers; one fix round; then `gates.py` decides. Held drafts are reported, never exported, and the repo is retried next run.
4. **render** (`svg.py`, `digest.py`): deterministic SVG (card, component flow, steps, stars chart) + Markdown.
5. **export** (`studio_export.py`, `contract.py`): studio campaign + posts (draft) + tool brief; validated against
   `contracts/studio-layouts.json` before anything is written.
6. **handoff** (`handoff.py`): draft PR into the studio from branch `radar/<campaign>`; token only in git's environment.
7. **schedule** (`radar.yml`): cron `0 1 * * 3,6` (Wed + Sat 08:00 ICT), manual run defaults to dry run, serialised, commits results.

## Acceptance criteria (each has a check)

- Pipeline end to end on fake GitHub + fake provider: `tests/test_pipeline.py`.
- Provider failure: fallback, retry, early abort without remembering anything: `tests/test_llm.py`, `test_pipeline.py`.
- Every gate rejects its defect (URL, number, hype, evidence, command, language, schema): `tests/test_gates.py`.
- Bundle accepted by the studio: `tests/test_svg_export.py` (vendored contract) and the REAL `studio.py check` via
  `scripts/studio_contract.py verify` = 0 errors 0 warnings on a 3-language sample; `studio.py render` produced images that were inspected.
- Handoff never touches `main`, never overwrites owner edits, never repeats a campaign, keeps the token off argv: `tests/test_handoff.py`.
- Schedule is Wed + Sat only and manual runs are dry by default: `tests/test_workflow.py`.

## Unresolved / not verifiable here (stated, not hidden)

- No real GitHub, API keys or free-model answers were available: real draft quality, current free model ids and quotas are unverified.
  First run must be `dry_run`, then `RADAR_PICKS=1`.
- GitHub topic names in `radar.yaml` are reasonable guesses; they may need tuning after the first dry run.
- A protected `main` blocks the bot's commit step. The handoff PR path needs `STUDIO_REPO_TOKEN`; untested against the real studio remote.
- The checker does not re-review the fix round; the gates do. Claims the gates cannot compute (a wrong mechanism that cites a real path)
  can still pass: every digest carries a "read the original repository" notice and the studio keeps the human approval.
- Template bilingual rule vs English CLI: decided to follow the studio's precedent (content is multilingual, tooling is English).
