# Q32 — verify-workflow.sh v4 overhaul

**Feature:** gentle-ai v4 upgrade / queue Q32 (verifier). **Task ID:** q32-verifier-v4 (stable).
**Class:** global-tooling-change. **Route:** `workflow-odd-secure` (delegated).
**Unit status:** TRACKER CREATED — no source edits yet.
**This unit (T0):** pre-code advice + tracker only. No `verify-workflow.sh` edit, no digest re-pin, no `global-config/AGENTS.md` edit, no deployment, no native review.
**Model:** cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07).

## Objective
Bring `verify-workflow.sh` — and the single coupled `global-config/AGENTS.md` block — to the gentle-ai v4 no-SDD contract, so the verifier stops asserting retired v3.5/SDD strings and passes on v4, while preserving the reviewed source→mirror deploy path and the digest-pin invariant.

## Problem
Q30/Q31 de-SDD'd WORKFLOW.md, the route skills, AGENTS.md, and the agent set, but `verify-workflow.sh` still asserts the old v3.5/SDD strings and therefore FAILS now (WORKFLOW.md greps :4277, :4312, :4322, :4325, :4328, :4330, :4335, :4336; recovery manifest :813/:842; routing-contract cat :4481-4482). Confirmed read-only 2026-10-11.

## Scope
### In scope
- The four slices (T1-T4) below; each edits `verify-workflow.sh` AND re-pins `VERIFY_SCRIPT_SHA256` in `global-config/plugins/workflow-health-check.ts` in the SAME commit.
- Recover the S5b verifier findings: `R3-WORKSPACE-001` (:2895), `R4-001` (:3041), `R4-002` (:4800), `R4-003` (:4813).
- Add the v4 negative checks with positive controls.
### Out of scope (other queue items; preserved)
- Q33 guard/plugins (`global-config/plugins/**` except the digest pin); Q30 skill deletion (`global-config/skills/workflow-sdd-secure/`); Q65 `pm-sdd` retirement; Q66 assembler; Q34-Q39. Slice 3's wording depends on Q30's decisions.

## Constraints
- **Digest pin invariant:** every `verify-workflow.sh` edit and the `VERIFY_SCRIPT_SHA256` update land in one commit.
- **Atomic AGENTS.md↔verifier coupling:** removing `global-config/AGENTS.md:49-59` (`user:host-sdd-runtime-boundaries`) must be paired, in the same commit, with deleting the verifier recovery constants/heredoc (:909-918, :988-1002, routing heredoc :1316, compare tuple :4434-4439, message :4450-4453); otherwise `recover_agents_file` fails closed.
- **Anchors that MUST stay:** :4329 "two or more non-trivial files", :4481-4489 `SEARCH_TOOL_ROUTING_DRIFT`, :3417 "400 authored changed lines and 100 KiB", and the preserved `sdd-explore` literal at `WORKFLOW.md:94`.
- **Line numbers drift:** the TODO inventory is dated 2026-10-01; the worker re-reads the current file before each slice.
- **Branch:** `feat/gentle-ai-v4`; the writer runs on the sandbox work branch; never switch branches; never commit (the orchestrator commits the applied result).
- **Review boundary:** last reviewed boundary `444244b7db9721dc9dbc4e30e272be3e781cefdc` (S5b's reviewed HEAD); `068f0fc` + `b2ed95e` are post-review docs commits not yet assessed and fall into the next candidate window.
- **Tests:** test-first with positive controls, no vacuous passes. Runners: `HOME="$(mktemp -d)" bun test tests/routing-guard`; `python3 -m unittest discover -s tests`. `bash -n` is syntax-only, not evidence. Fixtures under `$(mktemp -d)`, never host `~/.config/opencode`.
- **Verifier not run against the host tree** (it mutates host config).
- **Delivery:** `feature-branch-chain` (owner-approved). No push/PR/merge/release.

## Acceptance criteria
- No stale SDD/v3.5 string assertion remains in `verify-workflow.sh`.
- Each changed/new check has a positive control proving it can fail.
- `sha256sum verify-workflow.sh` equals the `VERIFY_SCRIPT_SHA256` pin after each slice's commit.

## Authorized scope
Source edits in this repo: `verify-workflow.sh`, `global-config/plugins/workflow-health-check.ts` (digest pin only), `global-config/AGENTS.md` (slice 4), plus this tracker and the advice record. No deployment.

## Checks
- Per slice: RED (fixture with a deliberate violation → the specific `fail()` code) → GREEN (clean fixture → PASS) → negative control.
- Guard suite green (`HOME="$(mktemp -d)" bun test tests/routing-guard`).

## Tasks
- [ ] T1 (Slice 1) — S5b findings: guard/sanitize `workspaceRoot` (:2895-2910, :4800, :4813); widen the Magic Context scrubber lookahead to `(?=\n#{1,6} )` and fail on a no-op (:3041). + digest re-pin.
- [ ] T2 (Slice 2) — v4 version + SDD assets: :10, :58-59; floor 3.5.0→4.0.0 (:3462); `GENTLE_AI_V3_5_*`→`GENTLE_AI_V4_*` (:3472/:3480/:3486); `sdd-archive-compose` (:3494-3498); `sdd-research|sdd-verify|sdd-archive SKILL.md` + `commands/sdd-research.md` (:3513-3538). + digest re-pin.
- [ ] T3 (Slice 3) — recipe/contract alignment: recovery manifest (:813/:842 "four"→"three"), WORKFLOW.md greps (:4277/:4312/:4322/:4325/:4328/:4330/:4335/:4336), routing-contract `cat` (:4481-4482) + strings (:4520-4561). + digest re-pin.
- [ ] T4 (Slice 4) — AGENTS.md coupling (ONE commit): delete `global-config/AGENTS.md:49-59` + the verifier recovery logic; update `global-config/AGENTS.md:247` routing wording; ADD negative checks (no `sdd-*` agent; every `host_sdd_*` deny, moving `host_sdd_status`/`host_sdd_continue`/`host_sdd_task_result` out of `registeredHostReads` :2702; v4 generic agents with expected tools, fixture-verified). + digest re-pin.

## Progress
- 2026-10-11: starting state HEAD `b2ed95e` (feat/gentle-ai-v4); RDD on (deciding source: global). Pre-code advice recorded (`odd/advice/q32-verifier-v4.md`). Verifier confirmed RED read-only. No source edit yet.
- 2026-10-11: two `pm-odd` dispatches returned BLOCKED (no Git-state read surface for unit-start branch verification); unit proceeds via direct `odd-apply` (Q31 path).

## Route / trigger evidence
- Route: delegated. Specialist: `odd-apply` writer (direct; see PM-layer note). Trigger: secure no-inline-mutation policy (any file change delegated); two-or-more non-trivial files (`verify-workflow.sh` + `workflow-health-check.ts`) → bounded sandbox writer.

## Next step
- Land this tracker + advice, read both back + the Magic Context mirror, then start T1 (Slice 1).
