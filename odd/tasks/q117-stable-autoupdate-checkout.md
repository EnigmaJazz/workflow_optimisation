# Q117 — Run the V2 plugin auto-update timer from a stable checkout of main

## Status

Implementation installed and tested in the working tree, deliberately UNCOMMITTED: its `scripts/**` paths
are S17 owner-only, so `host_git_commit` refuses them and the owner commits. Includes Codex finding F3.
No unit installed, no checkout created, no deploy, no restart.

## Identity and authority

- Unit: `q117-stable-autoupdate-checkout-u1`.
- Project: `worktrees` (repository `workflow_optimisation`, worktree `q105-unhide-planner`).
- Branch: `fix/q105-unhide-planner`. Class: global tooling change. Route: `workflow-odd-secure`.
- Owner authorization: 2026-11-10 dispatch; Codex finding F3 relayed the same day.
- Spec: `docs/TODO.md` Q117 (`:2574-2582`, owner approved 2026-11-08).

## Problem

`v2-plugin-autoupdate.service` ran `scripts/v2-plugin-autoupdate.py` from the owner's working checkout
`~/ai-workspace/workflow_optimisation`, which is on `chore/coordinator-selection` and carries uncommitted
edits, so the daily timer executed whichever script version happened to be checked out.

## Build

- T1 — template points at `%h/ai-workspace/workflow_optimisation-main`, documents the owner's clone and
  fast-forward commands, and passes `--require-branch main`.
- T2 — `check_autoupdate_checkout` in `scripts/opencode-v2-preflight.py`.
- T3 — `--require-branch` guard in `scripts/v2-plugin-autoupdate.py`, default off so the owner's manual
  dry-run from a feature branch still works.
- T4 — tests in both modules with positive controls.
- T5 — operations doc, router-log row and TODO status.

## Codex finding F3 and correction

The preflight derived the checkout from the *declared* `ExecStart` path. It now resolves the executable
the way `scripts/v2-plugin-autoupdate.py:231` resolves its own location (`Path(__file__).resolve()`),
derives the checkout from the resolved path, reports the resolved path and checkout in every detail that
names a path, and rejects unapproved symlink indirection: when the declared path resolves elsewhere and
the resolved checkout lies outside the expected stable checkout it FAILs with
`declared=<path>, resolved=<path>, resolved checkout=<checkout>; unapproved symlink indirection`.
Indirection that resolves inside the expected checkout stays allowed.

RED first: the real-symlink control returned `PASS` against the old code, then failed as expected.

Advisory: the final `checkout != expected` comparison still uses the unresolved `expected` path while the
symlink branch uses `expected.resolve()`. That can only produce a spurious WARN (never a false PASS) on a
host whose home or workspace directory is itself symlinked.

## Checks observed

- Targeted: `python3 -m unittest tests.test_opencode_v2_preflight tests.test_v2_plugin_autoupdate` —
  46 tests, OK, after the F3 correction.
- `git diff --check` — clean.
- Host broker suite: 943 tests with only the four known pre-existing failures.

## BLOCKED at the commit boundary (authority, not code)

`host_git_commit` refuses `scripts/opencode-v2-preflight.py` and `scripts/v2-plugin-autoupdate.py` as S17
protected paths. `global-config/AGENTS.md:281` and `docs/upgrades/opencode-v2-operations.md:99` make
`scripts/**` owner-only. The installed tree is coherent and fully tested; the owner commits these exact
paths. No partial commit was made, because committing only the non-script paths would leave `HEAD`'s tests
referencing functions that do not exist there.

Owner command (Fish), unchanged path set, updated message:

```fish
cd /home/james/ai-workspace/worktrees/workflow_optimisation/q105-unhide-planner
git add docs/TODO.md ROUTER-LOG.md docs/systemd/v2-plugin-autoupdate.service.template docs/upgrades/opencode-v2-operations.md scripts/opencode-v2-preflight.py scripts/v2-plugin-autoupdate.py tests/test_opencode_v2_preflight.py tests/test_v2_plugin_autoupdate.py
git commit -m "fix(autoupdate): run the V2 plugin timer from a main-only checkout" -m "The timer executes a dedicated main-only checkout; --require-branch main makes the job refuse a non-main checkout, and the preflight resolves the executable, reports the checkout, branch and commit it would run, and rejects symlink indirection outside that checkout." -m "— ROUTED: global-tooling-change@tier2-queue (2026-11-10)"
```

After that commit, `ROUTER-LOG.md` Q117 and `docs/TODO.md` Q117 still need the commit id backfilled.

## Next step

Owner commits the eight paths, creates the checkout, installs the unit, and runs
`python3 scripts/opencode-v2-preflight.py` to see the reported checkout, branch and commit.


## Revisions
- r1 2026-11-10T16:45:52Z gentle-orchestrator: Create the Q117 tracker: installed and tested, commit blocked at the S17 owner boundary
- r2 2026-11-10T18:16:53Z gentle-orchestrator: Record Codex F3 resolved-executable and symlink rejection, plus the updated owner commit command
