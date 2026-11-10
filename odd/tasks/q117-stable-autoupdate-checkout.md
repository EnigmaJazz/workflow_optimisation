# Q117 — Run the V2 plugin auto-update timer from a stable checkout of main

## Identity and authority

- Unit: `q117-stable-autoupdate-checkout-u1`.
- Project: `worktrees` (repository `workflow_optimisation`, worktree `q105-unhide-planner`).
- Branch: `fix/q105-unhide-planner`. Class: global tooling change. Route: `workflow-odd-secure`.
- Owner authorization: 2026-11-10 dispatch. Spec: `docs/TODO.md` Q117 (`:2574-2582`, owner approved 2026-11-08).
- Owner installs the unit and creates the checkout; no repo script does either.

## Problem

`v2-plugin-autoupdate.service` ran `scripts/v2-plugin-autoupdate.py` from the owner's working checkout
`~/ai-workspace/workflow_optimisation`, which is on `chore/coordinator-selection` and carries uncommitted
edits. The daily timer therefore executed whichever script version happened to be checked out.

## Spec

- S1. The unit runs from a dedicated checkout that tracks `main` only.
- S2. The template is updated; the owner installs it.
- S3. The preflight reports which checkout, branch and commit the timer would run.
- S4. Non-goals: no unit installation, no checkout creation, no deploy, no restart, no push.

## Tasks

- T1 — template points at `%h/ai-workspace/workflow_optimisation-main`, documents the owner's clone and
  fast-forward commands, and passes `--require-branch main` (done).
- T2 — `check_autoupdate_checkout` in `scripts/opencode-v2-preflight.py` (done).
- T3 — `--require-branch` guard in `scripts/v2-plugin-autoupdate.py`, default off so the owner's manual
  dry-run from a feature branch still works (done).
- T4 — tests in both modules with positive controls (done).
- T5 — operations doc, router-log row and TODO status (done).

## Behaviour as built

- Preflight `check_autoupdate_checkout` reads the installed unit, resolves `%h`, takes the first `.py`
  token from `ExecStart`, and reports `checkout=<path>, branch=main, commit=<sha>` on PASS. It FAILs on a
  non-`main` branch (naming branch, short commit and path), on a dirty tree (naming the count and path),
  on an unreadable unit or a missing `.py` token, and on any git failure. It WARNs when the unit is not
  installed or when the checkout is not the expected stable path, naming both paths.
- The job refuses with exit 2 when `--require-branch main` is set and the script's own checkout is on
  another branch, naming the observed and expected branch and the checkout path.

## Checks observed

- RED first: `python3 -m unittest tests.test_opencode_v2_preflight tests.test_v2_plugin_autoupdate` —
  `Ran 43 tests`, `FAILED (failures=3, errors=9)`: the guard rejected the unknown flag, the template test
  found the old checkout path, and the preflight tests had no `check_autoupdate_checkout`.
- Final targeted: same command — `Ran 44 tests in 0.551s`, `OK`.
- Host broker suite (`workflow-tests`): 937 tests, up 12 from 925; the same four pre-existing failures
  listed in the Q99 tracker, none new.
- `git diff --check` — no output.

## Deviation recorded

The writer made the pre-existing `Report` fixtures in `tests/test_opencode_v2_preflight.py` hermetic by
pointing `V2_ROOT` at a temp directory and stubbing `check_version`, because the sandbox has no host V2
install and those tests errored there. This is a test-only change; the host suite passes with it.

## BLOCKED at the commit boundary (authority, not code)

`host_git_commit` refused the unit's commit:
`refusing to commit protected paths (S17): scripts/opencode-v2-preflight.py, scripts/v2-plugin-autoupdate.py`.

`global-config/AGENTS.md:281` and `docs/upgrades/opencode-v2-operations.md:99` make `scripts/**` owner-only.
The installed working tree is coherent and fully tested; the owner commits these exact paths. No
workaround was attempted and no partial commit was made, because committing only the non-script paths
would leave tests in `HEAD` referencing a function that does not exist there.

Owner command (Fish):

```fish
cd /home/james/ai-workspace/worktrees/workflow_optimisation/q105-unhide-planner
git add docs/TODO.md ROUTER-LOG.md docs/systemd/v2-plugin-autoupdate.service.template docs/upgrades/opencode-v2-operations.md scripts/opencode-v2-preflight.py scripts/v2-plugin-autoupdate.py tests/test_opencode_v2_preflight.py tests/test_v2_plugin_autoupdate.py
git commit -m "fix(autoupdate): run the V2 plugin timer from a main-only checkout" -m "Timer executes a dedicated main-only checkout; the job refuses a non-main checkout with --require-branch main, and the preflight reports the checkout, branch and commit it would run." -m "— ROUTED: global-tooling-change@tier2-queue (2026-11-10)"
```

After that commit, `ROUTER-LOG.md` Q117 and `docs/TODO.md` Q117 still need the commit id backfilled.

## Next step

Owner commits the eight paths, creates the checkout, installs the unit, and runs
`python3 scripts/opencode-v2-preflight.py` to see the reported checkout and commit.


## Revisions
- r1 2026-11-10T16:45:52Z gentle-orchestrator: Create the Q117 tracker: installed and tested, commit blocked at the S17 owner boundary
