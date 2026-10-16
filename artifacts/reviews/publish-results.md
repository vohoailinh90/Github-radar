# Review: publish a scan's results as a pull request (T2, `code-reviewer`, independent)

Route: `python3 scripts/route.py --dimensions 1,1,1,1,2,2 --signals ""` -> T2, required `code-reviewer`, budget 2. Used: 1.
Verdict: approve with fixes. The reviewer also ran an experiment of its own: a local HTTP server recording Authorization headers, with a stored
`http.<url>.extraheader` like the one `actions/checkout` leaves. Result: the PAT alone gives TWO headers (the workflow's and the PAT's); an empty value
first, then the PAT, gives ONE. So `reset_header` is needed and works.

| # | Finding | Checked | Outcome |
|---|---|---|---|
| 1 | The secret-scope test looked at step env only: a job- or workflow-level `secrets.RADAR_PR_TOKEN` would pass | true | the test now counts the secret and the variable in the whole file and refuses secrets in job and workflow env; mutation (secret at job level) killed |
| 2 | The argv check looked for the plain token only: the base64 form in argv would pass | true | base64 asserted absent too |
| 3 | `ls-remote --exit-code` hid an auth or network failure as "no such branch"; a non-dict PR answer raised AttributeError | true | `ls-remote` without `--exit-code` (empty = absent, a failure raises with its own message); a non-object answer is reported as `branch-pushed` |
| 4 | Docs stated plausible permission names and auto-merge as fact; unverified list incomplete | true | listed as unverified: permission names, CI trigger by PAT, GraphQL auto-merge with a fine-grained PAT, the real `actions/checkout` layout |
| 5 | Two unmerged scan pull requests conflict in `state/*.json`; "Update branch" cannot fix it | true: a real operational trap | the new pull request names the open `radar/scan-*` ones (best effort, `earlier_scan_prs`), the docs say how to resolve; not enforced |
| 6 | Auto-merge with "require up to date" waits silently when main moves | true | documented ("đứng chờ im lặng"); nothing automates the update |
| residual | git echoes stderr, so a server answer that repeated a credential would be echoed | plausible | `_git` now replaces the token and its base64 form with `***` in error messages; test, mutation killed |

Not covered by anyone: the real Actions checkout, real PAT permissions, real CI triggering, real auto-merge (docs/branch-protection.md step 2 is that test).
