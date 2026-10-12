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
