# Plan: a page to start a scan on demand (T2, claude lane)

Requirement (user, 2026-10-16): "tạo giao diện UI để mình có thể chủ động quét repo mà không cần đợi tới ngày chỉ định".
Builds on the saved conditions (`docs/scan-conditions.md`); the design was challenged by `architecture-critic` as part of that work
(`artifacts/reviews/scan-conditions.md`). Page: `docs/ui/index.html`; guide: `docs/ui.md`.

Routing: ambiguity 1, scope 1, architecture 1, dependencies 1, risk 2 (it takes a token), verification 2 = 8 -> T2, no signals
(`python3 scripts/route.py --dimensions 1,1,1,1,2,2`): `main_with_architect_and_reviewer`, required `code-reviewer`, budget 2.

## Decisions

1. **The page only sends `workflow_dispatch`.** Scanning, models, secrets, writing and the studio hand-off stay in GitHub Actions. The page never sees a model key.
2. **A token with Actions read/write on this one repository, nothing else.** Typed into a password field every time; it is read from that field, emptied
   on "Quên token" and on `pagehide`, never stored (no web storage, cookie, URL). It is not `RADAR_PR_TOKEN` and not in CLAUDE.md's scope: no repository
   secret is created, and the file does not change the repository's secret rules.
3. **The workflow stays the authority.** The page sends only what differs from the chosen preset as `conditions`; `radar/conditions.py` re-checks it. The
   page's own checks are for fast feedback, and a test proves they accept and refuse exactly what Python does (Node runs the page's logic block).
4. **One static file, no dependency.** CSP by hash (`script-src` and `style-src` each one `sha256`, `connect-src https://api.github.com`,
   `default-src 'none'`, `base-uri`/`form-action` `'none'`), `scripts/ui_sync.py` rewrites the copy of Python's values and the hashes, and a test
   fails when they drift. A meta CSP cannot forbid framing, so the script refuses to run in a frame.
5. **Safe defaults for a costly action.** Dry run is the default; a real scan needs `QUET` typed; the button is off while the page's own run is queued or running
   (the `radar` concurrency group would otherwise replace a waiting run).
6. **Everything from GitHub is text.** `textContent`/`createElement` only; run links are built from a checked `owner/name` and an integer id.

## Acceptance (each has a check)

- No API that can run foreign code or send the token elsewhere; only `api.github.com` and `github.com/<repo>/actions/runs/<id>`; CSP exact: `tests/test_ui.py`.
- Presets, merge, estimate (round half to even), slot rule, validity: page logic under Node equals `radar/conditions.py`: `tests/test_ui.py`.
- Behaviour in Chromium against a fake `api.github.com`: payload, typed confirmation, token never stored, hostile text, bad names send nothing, frame refusal, CSP
  blocking injected script: `tests/test_ui_browser.py` (skipped where Playwright/Chromium is missing, as in CI).

## Not verifiable here

CORS from `file://` and from a Pages origin, the real dispatch answer (204), the real permission names of a fine-grained token, the real concurrency
cancellation text. `docs/ui.md` has a 5-minute checklist.
