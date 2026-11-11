# Q135 — pin the `host_review_acknowledge_approved` grant

**Objective:** make the owner's 2026-11-10 decision (item 8, verbatim: "Yes allow, does not need to ask")
executable: `host_review_acknowledge_approved` is `allow` for exactly `gentle-orchestrator`, `pm-odd` and
`pm-systematic`, and `deny` by global default for every other agent. Rationale: acknowledgement only burns
the authority the provider already issued for the exact lineage, and consent was given earlier, so an `ask`
gate stalls an approved review for no benefit.

**Branch:** `feat/q135-ack-grant-pin` (worktree `~/ai-workspace/worktrees/workflow_optimisation/q135-ack-grant-pin`),
off `main` `f1cbf3c`. The grant itself is already in `global-config/opencode.json`; this unit adds the evidence and pins it.

**Delivery:** the owner commits. `scripts/**` and the verifier manifest (`VERIFY_MODULES` in
`verify-workflow.sh` plus the `VERIFY_SCRIPT_SHA256` pin in `global-config/plugins/workflow-health-check.ts`)
are S17-protected, so the unit leaves its diff applied and uncommitted for the owner, with no partial commit
(HEAD must never reference a checker the manifest has not pinned).

**Test runner:** `python3 -m unittest tests.test_acknowledge_grant_pin -v`, then
`python3 -m unittest discover -s tests`. Bun suites, if run, use a temporary `HOME`.

**Risk:** item 2 (permissions) → Tier 4 Codex review with a SECURITY section before merge.

## Tasks

| ID | Task | Status | Evidence |
|---|---|---|---|
| T1 | New pinning test `tests/test_acknowledge_grant_pin.py`: source and derived-V2 holder sets, every other agent resolves deny/absent, positive controls for a fourth agent (allow, ask, wildcard) and for a coordinator losing its exact allow | pending | |
| T2 | Tighten the `verify/checkers/check-runtime-agents.cjs` non-coordinator sweep from "not allow" to "deny or absent", behind an `acknowledge-grant-policy` marker block the test executes | pending | |
| T3 | Re-pin: `python3 scripts/verifier_manifest.py update`, then `check` | pending | |
| T4 | State the holder set, the owner decision and the rationale in `WORKFLOW.md` (review-relay section) | pending | |

## Acceptance criteria

- The source config and the derived V2 config expose exactly the three holders; the set of agents resolving
  `allow` equals the three, and every other agent resolves `deny` or has no rule (inherits the global `deny`).
- The test fails when a fourth agent receives `allow` or `ask` (exact or wildcard), when one of the three loses
  its exact `allow` (removed, `ask`, or wildcard-only), and when the global default leaves `deny`.
- `python3 scripts/verifier_manifest.py check` reports the manifest and pin current.
- The three coordinators keep an exact explicit key: a wildcard alone never satisfies the coordinator check.

## Authorized scope

`tests/test_acknowledge_grant_pin.py`, `verify/checkers/check-runtime-agents.cjs`, `verify-workflow.sh` (manifest
regeneration only), `global-config/plugins/workflow-health-check.ts` (pin regeneration only), `WORKFLOW.md`.
No change to `global-config/opencode.json` and no change to the grant itself.

## Route and trigger evidence

ROUTE: Global tooling change (permission pin + verifier enforcement test + docs) | intent: authorized change |
route: workflow-odd-secure | specialist: `general` (direct orchestrator-dispatched sandbox writer) |
basis: WORKFLOW.md. The PM/Planner coordinator layer cannot run here: `docs/specs/pm-handoff.md` mandates
BLOCKED when the checked-out HEAD lives under `.git/worktrees/`, so the unit uses direct bounded writer dispatch.

Advice budget: enforcement-test/security unit → one pre-advice phase, one post-code check, one independent
verifier (`gentle-ai-verify`, high-risk seat). Pre-code advice was dispatched as `advisor-security-pre` because
no PM/Planner owns advisor dispatch in this worktree; its findings are recorded below.

## Log

- Created before the first implementation edit. Pre-code advice (`advisor-security-pre`) findings applied:
  add a coordinator-with-wildcard-only control; stage test-first as behavior-preserving extraction first, then
  the tightening, so the RED is behavioral rather than "marker missing"; do not let derived `-astra` aliases
  become extra holders silently.


## Revisions
- r1 2026-11-11T22:15:23Z gentle-orchestrator: Create Q135 tracker: pin the acknowledge-approved grant (owner decision 2026-11-10 item 8).
