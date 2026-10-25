# Plan: claims for shared work, and standing authority for Moda reports (T2, claude lane)

Requirement (user, 2026-10-24, Vietnamese): a mechanism so that several Claude or Codex sessions working on one shared list of
files do not duplicate each other; and when Claude creates a report in Moda it must not ask again and again, it has full authority.
Builds on `radar-dedup-rules` (merged, #29), which stops a second *post*; this stops two sessions working one item at the same time.

Routing: ambiguity 1, scope 1, architecture 1, dependencies 1, risk 1, verification 2 = 7 -> T2, no signals
(`python3 scripts/route.py --dimensions 1,1,1,1,1,2`): `main_with_architect_and_reviewer`, required `code-reviewer`, budget 2; the
architect is not fired (architecture is 1, no signal). The one reserve is `test-engineer` only, after a formal escalation.

## Decisions

1. **Sessions cannot see each other, so the ledger is on the remote.** Each session is its own checkout (a cloud container, a
   worktree); a file in the working tree coordinates nothing.
2. **One branch per item, `claims/<slug>`, and every change is a new commit on top of the tip.** A plain fast-forward push. The server
   lets exactly one of several simultaneous pushes on one tip through, and the first push of a branch fails when the branch exists:
   "exactly one winner" is git's guarantee, not ours. The log of the branch is an audit trail.
3. **Why branches, not refs, tags or deletes (measured, not assumed).** First design: `refs/claims/*` with force-with-lease and
   delete. On the real remote, from a Claude Code session on the web, a push to `refs/claims/*` and to a tag got HTTP 403, deleting a
   branch by push got 403, and the API delete was refused by the proxy ("Write access to this GitHub API path is not permitted").
   Only creating and advancing a branch works. So no transition may need a force-push, a delete, a tag or a non-branch ref.
4. **Each commit has an empty tree and the claim as JSON in its message** (key, session, agent, taken_at, ttl_s, state, note, nonce):
   no file in any tree, nothing to merge. CI runs only for `main` and pull requests (`ci.yml`), so a claim starts no run.
5. **A claim expires.** `taken_at + ttl_s` (default 2 h, max 24 h; `renew` extends). Only an expired or released item can be claimed by
   another session; that is a child commit on the tip that was read, so two sessions taking over one stale claim cannot both win.
   Release is a `released` commit (not a delete). A finished item keeps its branch; `prune` (owner, a machine that may delete) removes
   old finished ones, never a live one, with a lease on the exact tip.
6. **Items are strings.** A repository, a report folder or a file path, lower-cased, `[a-z0-9._-]` and `/` only. The branch name is a
   readable part (at most 80 characters) plus 10 hex characters of the hash of the **whole** key, so `a/b` and `a-b` are two items on two
   branches (a first design shared one branch for keys that read alike; review round 1 showed that a second key then overwrote the
   first one's record). `..`, absolute, empty and over-long keys are refused: the name becomes a branch name.
7. **Overlap by path.** A folder claim must exclude a claim on a file inside it. The push is atomic for one branch only, so after
   pushing, a claimant lists the live claims and **yields (pushes a release) whenever another session's live claim overlaps**, with no
   ordering by time (clocks differ). Both may yield and retry; both can never stand. The same session overlaps itself freely.
8. **All-or-nothing for several keys**; a failure after the first key releases the ones this call took (not renewals).
9. **Fail closed, and tell a lost race from a refusal.** Unreachable remote: exit 3, nothing claimed. A push refused because the tip
   moved is a lost race (read again); a refusal by a hook or policy is an error, never "someone else won".
10. **Session identity.** `--session`, then `CLAIM_SESSION`, `CLAUDE_SESSION_ID`, `CODEX_SESSION_ID`, then a random id kept in the
    checkout's git dir. Two sessions sharing one worktree must pass their own; CLAUDE.md says so.
11. **Moda authority is a permission, not a sentence.** The questions are Claude Code's own tool-permission prompts, so
    `.claude/settings.json` lists the Moda tools that create and edit a private report canvas, read, screenshot and export. Not
    listed (tool descriptions read, not names): `canvas_delete`, `canvas_share`, `canvas_update` (its template flag publishes to the
    team), `canvas_edit_image` and `task_delegate` (credits), `drive_*`, `brand_*` writes, `media_*`, `site_*`, `upload`, `edit_*`.
    `tests/test_moda_settings.py` pins both lists. CLAUDE.md "Moda reports" holds the rest of the standing rule.
12. **One canvas per report.** `deck.json` holds the canvas link: an existing link is edited, never a second canvas created.

## Files

- `scripts/claim.py` (stdlib): `claim`, `renew`, `release`, `list`, `check`, `prune`; exit 0 ok, 1 held, 2 usage, 3 remote.
- `tests/test_claim.py` (42 tests: local bare repo, real subprocesses, races, servers with refusing hooks, a network that fails mid-call), `tests/test_moda_settings.py` (4).
- `.claude/settings.json` (`permissions.allow` only, no hooks), `CLAUDE.md` (two sections, two lines), `docs/claims.md`
  (Vietnamese guide), `docs/reports/README.md` (one paragraph), this plan and `artifacts/reviews/radar-claims.md`.

## Acceptance (each has a check)

- One winner among 6 simultaneous claimants of one key, 4 rounds, and among 5 simultaneous takeovers of a stale claim, 3 rounds;
  the ledger names the process that got exit 0. A folder and a file inside it never both stand under a race (8 rounds).
- A live claim is refused (exit 1, names the holder); the same session renews; a release by another session is refused; a released
  item is free at once; an expired one is taken over; a branch made by hand is a held item and the new tip sits on top of it.
- All of that on a server that refuses deletes, force-pushes, tags and non-branch refs (a pre-receive hook copying the measured policy).
- The history of a branch is append-only and every commit has the empty tree.
- Mutation check (scratch copies of the script, 24 breakages: forced push, no parent, no overlap check, live claim taken over,
  released still live, no rollback, self-overlap, no prune of the local copy, policy refusal read as a lost race, no yield, ...): all caught.
- Real remote, once: a throwaway branch went through read, held, take over, held by another, renew, release, claim, release, all as
  fast-forward pushes, with no new branch.

## Risks and what is not verified here

- **A leftover branch.** The probe that measured the policy created `claims/_probe1792885729` (one commit, "probe") and the smoke test
  then advanced it; deleting it is refused from this session. It is harmless (empty trees) and the owner can delete it.
- Concurrency on GitHub itself (not git's local server) was not raced: the race tests use a local bare repository, whose receive-pack
  is the same code path; GitHub's single-tip acceptance is its documented behaviour, not measured here.
- Clock skew shifts expiry by the skew; the 2 h default tolerates minutes.
- Whether Claude Code applies a project `.claude/settings.json` to every cloud session is the product's behaviour; it cannot be
  tested from inside a session. The rule in CLAUDE.md holds either way.
- Nothing forces an agent to call the script. A hook that refuses a write to a claimed path is possible later and is not part of this change.
