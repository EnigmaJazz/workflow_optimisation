# Q65 — Retire pm-sdd

**Feature:** gentle-ai v4 upgrade / queue Q65 (retire the SDD route PM)
**Task ID:** q65-retire-pm-sdd (stable)
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0 IN PROGRESS (tracker created; implementation T1 pending)
**Model:** cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07)
**Decision:** RETIRE (owner-confirmed 2026-10-11; gentle-ai v4 leaves `pm-sdd` no route to coordinate)

## Objective

Retire the `pm-sdd` agent and every remaining reference so the SDD route PM no longer exists, without losing the verifier's ability to catch a reintroduction.

## Problem

`docs/TODO.md:1081-1093` (Q65). DECISION MADE: retire (default), not repurpose.

The remaining surface: `global-config/opencode.json:540` (`"pm-sdd": "allow"` in the orchestrator `permission.task`) and the `pm-sdd` agent block `:2165-2285` (its prompt loads the retired `workflow-sdd-secure` at `:2171`); `global-config/plugins/lib/routing-guard-helpers.ts:35` still maps `pm-sdd` → `workflow-sdd-secure`; `verify-workflow.sh:371` (`required_agents`), `:2796` (`pmAgents`) and `:2854` (`ordinaryMemoryAgents`) still list `pm-sdd`; `tests/routing-guard/routing-guard.test.ts` asserts the mapping; and `global-config/plugins/systematic-routing-guard.ts:224` still keeps the retired `host_sdd_archive_compose` in `ROUTING_GATE_TOOLS`. Q33 (`f10468b`) already removed `workflow-sdd-secure` from `ADAPTER_WORKFLOW_SKILLS` and the `host_sdd_` prefix rule, so the map at `helpers:35` is now the last guard-side SDD residue.

## Scope

### In scope

The config, helper, guard, verifier and test edits in T1, the `PM_SDD_REAPPEARED` sentinel, and the FOLDED-IN documentation update (`docs/TODO.md` status reconciliation: close Q15 as obsolete, mark Q32/Q33/Q65 done-at-source, apply the Q61 correction; plus this tracker and `ROUTER-LOG.md`).

### Out of scope (preserved)

Q30 (deleting `global-config/skills/workflow-sdd-secure/`); the external `sandbox-tools.ts READ_ONLY_AGENTS` entry (lives in the separate agent-sandbox-integration project — a follow-up); Q66; Q34-Q39; deployment.

## Constraints

- The change is ATOMIC — `opencode.json` + `routing-guard-helpers.ts` + `verify-workflow.sh` + the digest re-pin in `global-config/plugins/workflow-health-check.ts:93` + the tests must land together, or recovery aborts (`verify-workflow.sh:479-482`), the pin mismatches, or the suite fails.
- Re-pin LAST (the pin hashes the edited script).
- `COORDINATOR_PATTERNS` (`helpers:22-25`) stays generic.
- Branch `feat/gentle-ai-v4`; never switch branches; never commit.
- `bash -n` is NOT evidence.
- The verifier is not run against the host tree.
- Docs statuses use DONE-AT-SOURCE, never DONE (deploy is pending).

## Acceptance criteria

- No `pm-sdd` reference remains in the guard, config, verifier or tests.
- The guard suite passes.
- The retirement has a NON-vacuous positive control.
- The verifier can still catch a reintroduced `pm-sdd`.
- The digest pin equals `sha256sum verify-workflow.sh`.

## Authorized scope

Source edits: `global-config/opencode.json`, `global-config/plugins/lib/routing-guard-helpers.ts`, `global-config/plugins/systematic-routing-guard.ts`, `verify-workflow.sh`, `global-config/plugins/workflow-health-check.ts` (digest pin only), `tests/routing-guard/routing-guard.test.ts`, `docs/TODO.md`, `ROUTER-LOG.md`, plus this tracker and the advice record. No deployment.

## Checks

- `HOME="$(mktemp -d)" bun test tests/routing-guard` green.
- `python3 -m unittest discover -s tests` green.
- The extracted verifier predicate executed against fixtures (a planted `pm-sdd` agent trips `PM_SDD_REAPPEARED`).
- Digest pin == `sha256sum verify-workflow.sh`.

## Tasks

- [ ] T1 — remove "pm-sdd" from the orchestrator permission.task (opencode.json:540) and delete the pm-sdd agent block (:2165-2285); remove the pm-sdd row from PM_ROUTE_ADAPTER_SKILLS (helpers:35); remove "host_sdd_archive_compose" from ROUTING_GATE_TOOLS (guard:224); remove "pm-sdd" from verify-workflow.sh:371/:2796/:2854 and ADD a PM_SDD_REAPPEARED sentinel parallel to the SDD_AGENT_REAPPEARED check (~:2819); update the tests (:773 tuple, :968 assertion, :908-916 → negative assertion, the :898 region) and ADD the positive controls in describe 9; re-pin VERIFY_SCRIPT_SHA256 LAST.

## Progress

- 2026-10-11: T0 — tracker and advice record created; owner confirmed RETIRE. Route: delegated. No source edit yet.

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply` writer (direct; PM layer unusable — see the PM-layer note).
- Trigger: secure no-inline-mutation policy (any file change delegated); multiple non-trivial files → bounded sandbox writer.

## Next step

T1 implementation, then Q30 (delete the skill directory), then the owner's deployment (verifier mirror + OpenCode restart), then re-verify.
