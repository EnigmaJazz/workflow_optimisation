# Q99 — Guard the verifier seat against Grok

## Status

DONE at source, including the Codex follow-up. Commits: `5b0b84e` (base rule) and `85cf550` (F1/F2
reachable-seat correction); trackers `3cf5cb7`, `5507fc5`. No model assignment changed and no deployment
was performed. The `ROUTER-LOG.md` row still reads `PENDING-COMMIT` because that file belongs to the Q117
unit whose commit is blocked at the S17 owner boundary; the owner's single commit carries it.

## Identity and authority

- Unit: `q99-verifier-grok-guard-u1`.
- Project: `worktrees` (repository `workflow_optimisation`, worktree `q105-unhide-planner`).
- Branch: `fix/q105-unhide-planner`. Class: global tooling change. Route: `workflow-odd-secure`.
- Owner authorization: 2026-11-10; Codex FINDINGS F1 and F2 relayed the same day.
- Spec: `docs/TODO.md` Q99 (`:2732-2740`) plus the Tier 2 invariant: **any agent, any reachable seat**.

## Problem

One `gentle-ai-verify` run on `opencode-go/grok-4.7` consumed 10% of a weekly allowance (owner,
2026-11-02). Commit `9d33338` had restored a stale `opencode.json` that put Grok on the verifier seat,
and nothing in the verifier failed when a Grok model landed on the wrong agent.

## Spec

- S1. Fail when any agent other than `review-refuter` and `asi-review-refuter` carries a Grok model.
- S2. Cover every reachable seat: the deployed config's `agent.model`, the effective Systematic seat
  resolved for the base profile and each reviewed profile, and every reachable fallback target.
- S3. Provider/model catalogs are never scanned; only agent seats and resolved chains.
- S4. Non-goals: no model change, no permission change, no deploy, no `derive --apply`, no restart.

## Codex findings and correction (`85cf550`)

- **F1** — the rule only read each agent's top-level `model`, so a Grok model inherited or overridden
  through Systematic (`systematic.jsonc` `agents.*.model`, `categories.*.model`, and per-profile
  overlays) passed. Now resolved for `base` plus every reviewed profile via the same overlay semantics
  and reported as `GROK_REACHABLE_SEAT: <agent>=<model> (systematic:<profile>)`.
- **F2** — fallback targets were unchecked. Now resolved through the same agent / exact-source / provider
  / global precedence and the same `startProviders` and same-provider filtering, reported as
  `GROK_REACHABLE_SEAT: <agent>=<target> (fallback)`. The scan covers the union of the Systematic
  inventory and every configured agent, so a Grok fallback for a config-only seat such as `pm-odd` is
  caught too.
- The config-seat rule and its `GROK_OUTSIDE_REFUTER` message are unchanged.

## Two defects caught during review before install

- The first correction batch renamed the Q105 call site to an undefined `plannerAdvisorVisibility(...)`,
  which would have made the checker throw `ReferenceError` and crash the whole runtime-agent
  verification. Caught by diff review before install; corrected to
  `plannerAdvisorVisibilityFailures(...)` and verified by grep (definition line 603, call line 676).
- The fallback loop iterated only the Systematic inventory, so a config-only agent's fallback was
  computed and then ignored. Widened to the union and pinned by a dedicated `pm-odd` test.

## Checks observed

- RED first, both batches: the new controls returned `[]` instead of the expected
  `GROK_REACHABLE_SEAT` strings before implementation.
- `tests.test_grok_seat_policy`: 12 tests, OK, 1 skipped in the writer environment (the derived-V2 case
  needs `~/agent-sandbox-integration`).
- Regression: `tests.test_q90_planner tests.test_spec_advisor_seats tests.test_planner_advisor_visibility
  tests.test_advisor_checker_policy` — 41 OK.
- Host broker suite after the correction: 943 tests, up 6 from 937, with only the four known pre-existing
  failures (stale `NONPROMPT_CONFIG_SHA256` pin ruled out of scope by Tier 2, the two `RealConfig` derive
  drifts, and `test_verifier_split` while `verify/checkers/__pycache__/*.pyc` exist).
- `python3 scripts/verifier_manifest.py update` then `check` — regenerated, then
  `ok: manifest and pin are current`.

## Advisories

- The fallback resolver re-implements the precedence rather than calling `configuredFallbacks`; it is
  behaviourally aligned for `agentFallbackModels`, `fallbackModels`, `providerFallbacks` and
  `fallbackModel`, but a future change to the shared resolver must be mirrored here.
- `sameProviderFallbackMode: "model-specific"` is treated as permitting a same-provider target; that is
  conservative for this rule (it can only over-report, not under-report).

## Next step

Owner commits the Q117 path set, which also carries this unit's router-log row, then derives and
restarts; the rule activates in the verifier afterwards.


## Revisions
- r1 2026-11-10T15:57:21Z gentle-orchestrator: Create the Q99 tracker: refuter-only Grok rule, V1 and derived V2 evidence
- r2 2026-11-10T16:46:04Z gentle-orchestrator: Record commit 5b0b84e and the host-suite verification for Q99
- r3 2026-11-10T18:16:53Z gentle-orchestrator: Record Codex F1/F2 correction commit 85cf550, the two caught defects and the host-suite evidence
