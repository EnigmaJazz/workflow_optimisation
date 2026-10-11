# Q33 — Guard and plugins (de-SDD)

**Feature:** gentle-ai v4 upgrade / queue Q33 (guard + plugins).
**Task ID:** q33-guard-plugins (stable).
**Class:** global-tooling-change.
**Route:** `workflow-odd-secure` (delegated).
**Unit status:** T0 IN PROGRESS (tracker created; implementation T1 pending).
**Model:** cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07).

## Objective

Remove the retired SDD route surface from the routing guard and its plugins so gentle-ai v4 has
no SDD route left to unlock. Record honestly that several of these edits are hygiene — the live
runtime is already clean — rather than functional gating changes.

## Problem

`docs/TODO.md:875-888` (Q33). The line numbers in that item have drifted; the current map is:

- `global-config/plugins/systematic-routing-guard.ts:280-284` still admits `workflow-sdd-secure`
  into `ADAPTER_WORKFLOW_SKILLS` (`:282`; consumers `:533` and `:1106`).
- `systematic-routing-guard.ts:584` still treats any `host_sdd_` prefix as a routing gate.
- `global-config/plugins/lib/routing-guard-helpers.ts:18` still lists `sdd-apply`/`sdd-apply-local`,
  and `routing-guard-helpers.ts:46` still lists `sdd-explore|sdd-verify|sdd-research`.
- `global-config/plugins/workflow-health-check.ts:8` and `:40` still describe v3.5/SDD scope.

## Scope

### In scope

- The four edits in T1 plus their test updates.

### Out of scope (other queue items; preserved)

- Q65 (`pm-sdd` retirement — the `opencode.json` block, the orchestrator `permission.task`,
  `routing-guard-helpers.ts:32-36`, the verifier PM lists).
- Q30 (deleting `global-config/skills/workflow-sdd-secure/`).
- Removing `"host_sdd_archive_compose"` from `ROUTING_GATE_TOOLS`
  (`systematic-routing-guard.ts:224`).
- Q66; Q34-Q39.
- Q15 is closed separately as obsolete-by-absence.

## Constraints

- Q33 does NOT edit `verify-workflow.sh`, so `VERIFY_SCRIPT_SHA256`
  (`workflow-health-check.ts:93`) is NOT re-pinned.
- `host_sdd_archive_compose` stays in `ROUTING_GATE_TOOLS` (`systematic-routing-guard.ts:224`)
  so `isRoutingGateTool` still gates it.
- `routing-guard-helpers.ts:32-36` is untouched.
- Branch `feat/gentle-ai-v4`; the writer runs on the sandbox work branch; never switch branches;
  never commit.
- Tests: `HOME="$(mktemp -d)" bun test tests/routing-guard`.
- `bash -n` is syntax-only and is NOT evidence.
- The verifier is not run against the host tree.

## Acceptance criteria

- The four SDD tokens are absent from the guard/helper source.
- The guard suite passes.
- The `ADAPTER_WORKFLOW_SKILLS` removal is proven by a NON-vacuous positive control.
- No plugin export is renamed or removed.

## Authorized scope

Source edits: `global-config/plugins/systematic-routing-guard.ts`,
`global-config/plugins/lib/routing-guard-helpers.ts`,
`global-config/plugins/workflow-health-check.ts` (comments only),
`tests/routing-guard/routing-guard.test.ts`, plus this tracker and the advice record.
No deployment.

## Checks

- `HOME="$(mktemp -d)" bun test tests/routing-guard` green.
- A fresh `host_sdd_` sweep over `global-config/` showing no other live `host_sdd_*` tool.
- Plugin loads.

## Tasks

- [ ] T1 — guard `:282` remove "workflow-sdd-secure" from ADAPTER_WORKFLOW_SKILLS; guard `:584` remove `|| tool.startsWith("host_sdd_")` keeping `:224`; helpers `:18` drop "sdd-apply"/"sdd-apply-local"; helpers `:46` drop the sdd-* read-only entries; health-check `:8`/`:40` comment updates (no re-pin); tests `:273` and `:292` literal updates plus a new positive control for the ADAPTER_WORKFLOW_SKILLS removal.

## Progress

- 2026-10-11: T0 — tracker and advice record created. Route: delegated. No source edit yet.

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` writer (direct; PM layer unusable — see the PM-layer
note). Trigger: secure no-inline-mutation policy (any file change delegated); multiple
non-trivial files → bounded sandbox writer.

## Next step

T1 implementation per the Tasks line, then Q65 (pm-sdd retirement) and Q30 (skill deletion),
in that order.
