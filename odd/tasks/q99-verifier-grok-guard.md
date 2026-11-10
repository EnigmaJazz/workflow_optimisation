# Q99 — Guard the verifier seat against Grok

## Identity and authority

- Unit: `q99-verifier-grok-guard-u1`.
- Project: `worktrees` (repository `workflow_optimisation`, worktree `q105-unhide-planner`).
- Branch: `fix/q105-unhide-planner`. Class: global tooling change. Route: `workflow-odd-secure`.
- Owner authorization: 2026-11-10 dispatch — add a verifier check and a test that Grok appears only on
  `review-refuter` and `asi-review-refuter`, in V1 and in the derived V2 config, with a positive control.
- Spec: `docs/TODO.md` Q99 (`:2732-2740`).

## Problem

One `gentle-ai-verify` run on `opencode-go/grok-4.7` consumed 10% of a weekly allowance (owner,
2026-11-02). Commit `9d33338` on `chore/coordinator-selection` had restored a stale `opencode.json` that
put Grok on the verifier seat, and nothing in the verifier failed when a Grok model landed on the wrong
agent.

## Observed evidence

- **observed** — V1 `global-config/opencode.json` has three `grok` matches: `review-refuter` (`:1142`),
  `asi-review-refuter` (`:1668`) and the provider model catalog entry `grok-4.7` (`:3383`). The catalog
  is not an agent seat.
- **observed** — the live V2 file had been restored to `openai/gpt-6.1-sol` by change set
  `verifier-off-grok-v2`, and `chore/coordinator-selection` `7599b56` pinned the branch. That branch is
  not this one; the rule was therefore not enforced here.
- **not applicable** — no model assignment needed changing: the checked-in config already complied.

## Spec

- S1. A verifier rule fails when any agent other than `review-refuter` and `asi-review-refuter` carries
  a model matching `grok` (case-insensitive).
- S2. The rule inspects only each agent's top-level `model`. Provider/model catalogs, tools, prompts and
  permissions are never scanned, so `provider.opencode-go.models["grok-4.7"]` cannot be flagged.
- S3. Tests cover V1 and the derived V2 config, with positive controls.
- S4. Non-goals: no model change, no permission change, no deploy, no `derive --apply`, no restart.

## Tasks

- T1 — add the `grok-seat-policy` block and `grokSeatFailures(agents)` to
  `verify/checkers/check-runtime-agents.cjs`, wired via `grokSeatFailures(deployedAgents).forEach(fail)`
  (done).
- T2 — `tests/test_grok_seat_policy.py` with RED observed first (done).
- T3 — manifest and pin regeneration (done).
- T4 — router-log row and `docs/TODO.md` status (done).

## Acceptance criteria

- `GROK_OUTSIDE_REFUTER: <name>=<model>` for a Grok model on any non-refuter agent.
- `[]` for Grok on `review-refuter` alone and on `asi-review-refuter` alone.
- `[]` for the real V1 config and for the derived V2 config; both carry exactly the two refuter seats.
- `[]` for an agents map with no Grok agent even when a provider-style nested object contains
  `grok-4.7`.
- `python3 scripts/verifier_manifest.py check` reports current.

## Checks observed

- **RED, before implementation** — `python3 -m unittest tests.test_grok_seat_policy` failed because the
  `grok-seat-policy` marker block was missing: `AssertionError: Grok seat policy marker block is
  missing`.
- Writer environment — `tests.test_grok_seat_policy`: 7 passed, 1 skipped (the V2 derivation case skips
  because `~/agent-sandbox-integration` is absent in the sandbox).
- Regression — `tests.test_q90_planner tests.test_spec_advisor_seats
  tests.test_planner_advisor_visibility tests.test_advisor_checker_policy`: 41 OK.
- **Host suite** (`workflow-tests`, broker runner on this host, which has the integration checkout) —
  925 tests, and the count rose by exactly 8 with the skip count unchanged at 1, so the derived-V2 case
  executed rather than skipping. Remaining failures are the same four pre-existing ones listed under
  Advisories.
- `python3 scripts/verifier_manifest.py update` then `check` — `manifest regenerated`, `plugin pin
  updated`, `ok: manifest and pin are current`.

## Advisories carried from Q105

- `tests.test_orchestrator_prompt_source...test_nonprompt_config_tree_matches_the_pinned_digest` —
  pre-existing stale pin on main; Tier 2 ruled it out of scope.
- `tests.test_derive_v2_config.RealConfig.test_everything_except_the_plugin_list_is_carried_over_unchanged`
  (`53 != 55`, stale hardcoded `48` after Q131) and `...test_no_prompt_is_taken_from_the_live_root_any_more`
  (environment) are pre-existing.
- `tests.test_verifier_split.Manifest.test_manifest_matches_the_module_files_in_order` fails only while
  generated `verify/checkers/__pycache__/*.pyc` exist in the working tree; clearing that directory
  removes the failure.

## Next step

None for this unit at source. No deployment was performed.


## Revisions
- r1 2026-11-10T15:57:21Z gentle-orchestrator: Create the Q99 tracker: refuter-only Grok rule, V1 and derived V2 evidence
