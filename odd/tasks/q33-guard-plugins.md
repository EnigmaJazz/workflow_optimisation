# Q33 — Guard and plugins (de-SDD)

**Feature:** gentle-ai v4 upgrade / queue Q33 (guard + plugins).
**Task ID:** q33-guard-plugins (stable).
**Class:** global-tooling-change.
**Route:** `workflow-odd-secure` (delegated).
**Unit status:** T0–T1 DONE — Q33 source complete (committed; T1 native review approved+acknowledged). Q65 and Q30 remain.
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

- [x] T1 — guard `:282` remove "workflow-sdd-secure" from ADAPTER_WORKFLOW_SKILLS; guard `:584` remove `|| tool.startsWith("host_sdd_")` keeping `:224`; helpers `:18` drop "sdd-apply"/"sdd-apply-local"; helpers `:46` drop the sdd-* read-only entries; health-check `:8`/`:40` comment updates (no re-pin); tests `:273` and `:292` literal updates plus a new positive control for the ADAPTER_WORKFLOW_SKILLS removal.

## Progress

- 2026-10-11: T0 — tracker and advice record created. Route: delegated. No source edit yet.
- 2026-10-11: T1 committed `f10468b` (4 files, +25/−10). Edits: `systematic-routing-guard.ts` drops `"workflow-sdd-secure"` from `ADAPTER_WORKFLOW_SKILLS` (consumers `:533` and `:1106` both unaffected — no ROUTE_STAGES entry ever gated it) and drops `|| tool.startsWith("host_sdd_")` from `isRoutingGateTool` while KEEPING `"host_sdd_archive_compose"` in `ROUTING_GATE_TOOLS` (`:224`); `lib/routing-guard-helpers.ts` drops `sdd-apply`/`sdd-apply-local` from `SPECIALIST_WRITERS` and the `sdd-explore|sdd-verify|sdd-research` alternatives from `READ_ONLY_SPECIALIST_PATTERNS` (`:32-36` and `ROUTE_STAGES` untouched — Q65); `workflow-health-check.ts` header comments (`:8`, `:40`) updated to the v4 reality, comment-only, NO re-pin (the pin binds `verify-workflow.sh`, untouched by Q33); `tests/routing-guard/routing-guard.test.ts` membership literals updated and a NEW non-vacuous positive control added in describe section 7. Checks: baseline `HOME="$(mktemp -d)" bun test tests/routing-guard` 94 pass / 0 fail → final 95 pass / 0 fail; RED proof — temporarily re-adding `"workflow-sdd-secure"` produced 94 pass / 1 fail at the new control, then reverted; a `host_sdd_` sweep over `global-config/` found the only live hit is the intentional `ROUTING_GATE_TOOLS` membership at `:224` (every `opencode.json` entry is `false`/`deny`); no export renamed or removed.
- 2026-10-11: T1 native review: lineage `review-d237798876244875`; tier **high** (`process_boundary`); candidate 4 files / 35 lines; all four lenses admitted; outcome **approved** and **acknowledged**; `authority: burned`; consumed revision `sha256:97b5321c…`.
- 2026-10-11: T1 advisory findings (non-blocking, informational; separate later work, never re-review triggers): `R4-1` (resilience WARNING, deterministic — the `host_sdd_` gate removal is fail-open: if any `host_sdd_*` tool were ever re-registered (stale plugin load across the mirror/restart window, or a cross-project reference) it would no longer require a routing key or log, leaving only the verifier-time assertion as a control); `R4-2` (resilience SUGGESTION — the health-check header asserts v4 checks while `verify-workflow.sh` is outside this candidate's manifest; NOTE: the v4 verifier section already landed in Q32 T2, so the header is accurate; the finding could not see it); `R3-host-sdd-gate-untested`, `R3-sdd-readonly-untested`, `R3-sdd-writers-untested` (reliability SUGGESTIONs — the three removals have no explicit negative-assertion tests; only the `ADAPTER_WORKFLOW_SKILLS` removal got a positive control).

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` writer (direct; PM layer unusable — see the PM-layer
note). Trigger: secure no-inline-mutation policy (any file change delegated); multiple
non-trivial files → bounded sandbox writer.

## Next step

Q65 (retire `pm-sdd`) next, then Q30 (delete `global-config/skills/workflow-sdd-secure/`). Carry-forward advisories (non-blocking): T1's `R4-1`, `R4-2`, `R3-host-sdd-gate-untested`, `R3-sdd-readonly-untested`, `R3-sdd-writers-untested`. Revisit for removal in Q65: `"host_sdd_archive_compose"` in `ROUTING_GATE_TOOLS` (`systematic-routing-guard.ts:224`) and the `helpers:18`-derived test enumerations at `tests/routing-guard/routing-guard.test.ts:873`/`:892`. The verifier mirror and OpenCode restart remain the owner's deployment action.
