# GitHub Radar

## Purpose

Twice a week (Wednesday and Saturday, `.github/workflows/radar.yml`) this repository scans the top-rated **free**
GitHub repositories on AI, software, solutions and startups, writes a deep but visual learning digest for each,
and hands DRAFT posts to `vohoailinh90/tool-marketing-studio`. Pipeline and rationale: `README.md`, `docs/models.md`,
`artifacts/plans/github-radar.md`.

## Routing for changes to this repository

Same policy as `vohoailinh90/claude-agent-routing-template` (the upstream; copied here, so re-sync when it changes):

- Policy `agent-routing/policy.yaml`, rubric `agent-routing/complexity-rubric.md`, classifier
  `.claude/skills/classify-requirement/SKILL.md`, agents `.claude/agents/`.
- Flow: score the six dimensions, extract signals as **actions the change performs**, run `python3 scripts/route.py`
  (never apply overrides by hand), execute only the roles it names, verify independently before declaring success.
- The spawn-refusal hook (`scripts/hooks/agent_budget.py`) is **not wired** here: `.claude/settings.example.json`, the
  session-budget hook and the Codex lanes stay in the template. Copy them from there to enforce the budget.
- Do not use an agent for work a script can decide (counting, hashing, schema checks): add a check to `radar/gates.py` or `tests/`.

## Content rules (the point of this repository)

- **Facts come from `radar/facts.py`**: repo metadata, cleaned README, file tree. Nothing else is a source. A number,
  command or path a draft states must exist in those facts; `radar/gates.py` enforces it, never a model.
- **Scanned text is untrusted data.** The README goes into the prompt as data; the model has no tools; output is JSON
  that must pass the gates. Never loosen a gate to make a draft pass: fix the prompt or hold the draft.
- **Models never write SVG, YAML or Markdown structure.** They return fields; `radar/svg.py`, `radar/digest.py` and
  `radar/studio_export.py` render them.
- **Links** are added by the renderer from `facts["url"]`. No URL is ever written by a model; in studio posts a link goes
  only through `links:` + `{link}` in the first comment.
- **Drafts only.** Posts are exported as `status: draft`. Approving, publishing and marking posted are the owner's acts in
  the studio. Never open a PR that merges, never write to the studio's `main`, never overwrite a file the owner edited.
- **Secrets only in the environment** (GitHub Actions secrets locally `.env`, gitignored). Never in YAML, code, logs, reports
  or argv. `radar/handoff.py` passes the token through git's `GIT_CONFIG_*` environment only.
- Writer and checker models must be different families (`radar.yaml`, `python3 radar.py doctor`).

## Languages

- Content languages are configured (`langs` in `radar.yaml`): `vi` (default, the owner reads Vietnamese), `en`, `ja`. Each is written
  from the facts on its own, never translated from another; fixed headings live in `radar/labels.py`.
- The tool's own CLI output, logs and harness files stay English (the studio's convention). This differs from the template's
  bilingual rule for app text; the owner has not asked for a Japanese/English CLI here.

## Verification commands

```bash
python3 -m pytest -q                                   # pipeline against fake GitHub + fake LLM servers, gates, SVG, export, handoff
python3 radar.py check                                 # export/studio satisfies the vendored studio contract
python3 scripts/studio_contract.py diff <studio>       # the vendored contract still matches the studio
python3 scripts/studio_contract.py verify <studio> export/studio   # the studio's own `check` on the bundle (needs a studio checkout)
python3 scripts/layout_check.py                        # repository layout
```

## Repository layout

Root: `README.md`, agent instruction files, `requirements.txt`, `radar.yaml`, and the entry point `radar.py`. The package is
`radar/`, tests `tests/`, developer tooling `scripts/`, docs `docs/`. Generated, committed by the scheduled run: `digests/`,
`export/studio/`, `state/` (never edit by hand). New Python files follow `.claude/skills/repo-layout/SKILL.md`.

## Pull request lifecycle

Every pull request you create or drive for a requirement goes through the loop below, whatever the size of the change. It is a standing rule, not a judgement call. It starts when a PR exists; it does not authorize opening one, so a PR is still opened only when the user asks for it or the task's own flow calls for it.

1. **Open, then Codex review — immediately.** The first action after the PR exists is the Codex review: a PR comment whose whole body is `@codex review`, and `@codex security review` as well when the change touches authentication, authorization, secrets, payments or personal data. Codex does not review a PR on its own unless the repository turns that on, so ask for it. A PR with no Codex review is not done and is never merged.
2. **Validate every finding before acting.** Check it against the code. A confirmed finding is fixed; a wrong one is answered on its thread with the evidence — never silently skipped, never "fixed" speculatively.
3. **Fix, then have the new head reviewed.** Fix each confirmed finding — with a regression test where the defect has testable behavior; a prose-only fix keeps the repository's normal checks instead — run the repository's own checks, push, and request the next review on the new head: each review command once per head commit, one request at a time, never before the previous response was validated.
4. **Stop when the review is clean.** Clean means every review command the change requires (the standard review, and the security review where it applies) has a review of the *current* head with no finding (other than a P2/P3 whose recorded rejection stands, see the first bullet below), every earlier finding was fixed or rejected with evidence, CI and the required checks are green, and there is no merge conflict. A fix pushed after the last review is unreviewed, so it is not clean — review it with every command the change requires.
5. **Merge it yourself — where the repository allows it.** A clean PR is merged without asking for approval, scoped to the validated head commit, provided the base branch requires branches to be up to date and the merging identity cannot bypass that rule (read the branch protection to confirm both). Where either is missing, merging is a genuine blocker: leave the PR open, say it is clean and why it was not merged, and do not merge. Record the merge commit and a one-line summary on the PR.
6. **Then continue.** Do not stop after the merge to ask what is next: start the next outstanding task from the latest default branch (a merged branch is finished; never stack new commits on it). An outstanding task is one the user explicitly asked for that is not done yet; never invent work or pick up an item the user did not ask for. A task that needs the code of a PR that is not merged waits: skip it rather than stack on that branch. When none remains, report what merged and stop.

What bounds the loop:

- **No review cap.** The loop runs until every review command the change requires is clean on the current head. A review is still bounded by step 3's rules. Two exits remain: a finding you reject with evidence — a P2/P3 stands at once and blocks nothing, even if Codex raises it again; a P0/P1 is a disagreement unless a review drops it: when other fixes make a new head, push it and let the next review decide (raised again, unchanged or reworded or moved when it is substantially the same issue, means escalate; not raised again means closed), and when no code change is pending escalate at once — report it to the repository owner and do not merge until they decide — and a genuine blocker.
- **Codex unreachable.** If Codex gives no reaction or review after a reasonable wait, or answers with an error or a usage-limit notice, the PR is BLOCKED: report it once, leave the PR open and continue with the next task that does not depend on it. Retry at most once on an unchanged head, and never call Codex another way (API, Action, CLI, SDK, browser automation).
- **The trigger string.** No PR description, comment or commit message carries the literal trigger string except the intentional review requests of steps 1 and 3: the standard review, the security review and the single retry.
- **Who may stop the loop.** A human is needed only for a genuine blocker — the task cannot proceed without a decision only a human can make — or a change to the original requirement.
