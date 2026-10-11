# Q32 — verify-workflow.sh v4 overhaul

**Feature:** gentle-ai v4 upgrade / queue Q32 (verifier). **Task ID:** q32-verifier-v4 (stable).
**Class:** global-tooling-change. **Route:** `workflow-odd-secure` (delegated).
**Unit status:** T0 + T1 DONE (committed; T1 native review approved+acknowledged). T2–T4 pending.
**Unit state (2026-10-11):** T0 created this tracker and `odd/advice/q32-verifier-v4.md`; T1 landed the four S5b verifier fixes on `verify-workflow.sh` + the digest pin. No T2–T4 edits, no `global-config/AGENTS.md` edit, no deployment.
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
- [x] T1 (Slice 1) — S5b findings: guard/sanitize `workspaceRoot` (:2895-2910, :4800, :4813); widen the Magic Context scrubber lookahead to `(?=\n#{1,6} )` and fail on a no-op (:3041). + digest re-pin.
- [ ] T2 (Slice 2) — v4 version + SDD assets: :10, :58-59; floor 3.5.0→4.0.0 (:3462); `GENTLE_AI_V3_5_*`→`GENTLE_AI_V4_*` (:3472/:3480/:3486); `sdd-archive-compose` (:3494-3498); `sdd-research|sdd-verify|sdd-archive SKILL.md` + `commands/sdd-research.md` (:3513-3538). + digest re-pin.
- [ ] T3 (Slice 3) — recipe/contract alignment: recovery manifest (:813/:842 "four"→"three"), WORKFLOW.md greps (:4277/:4312/:4322/:4325/:4328/:4330/:4335/:4336), routing-contract `cat` (:4481-4482) + strings (:4520-4561). + digest re-pin.
- [ ] T4 (Slice 4) — AGENTS.md coupling (ONE commit): delete `global-config/AGENTS.md:49-59` + the verifier recovery logic; update `global-config/AGENTS.md:247` routing wording; ADD negative checks (no `sdd-*` agent; every `host_sdd_*` deny, moving `host_sdd_status`/`host_sdd_continue`/`host_sdd_task_result` out of `registeredHostReads` :2702; v4 generic agents with expected tools, fixture-verified). + digest re-pin.

## Progress
- 2026-10-11: starting state HEAD `b2ed95e` (feat/gentle-ai-v4); RDD on (deciding source: global). Pre-code advice recorded (`odd/advice/q32-verifier-v4.md`). Verifier confirmed RED read-only. No source edit yet.
- 2026-10-11: two `pm-odd` dispatches returned BLOCKED (no Git-state read surface for unit-start branch verification); unit proceeds via direct `odd-apply` (Q31 path).
- 2026-10-11: T0 committed `a46a5f2` (2 files, +86): `odd/tasks/q32-verifier-v4.md` + `odd/advice/q32-verifier-v4.md`. Magic Context mirror id 1132 (read back). Post-T0 RDD assessment: review not due (`under_budget`, medium).
- 2026-10-11: T1 committed `3d0eb45` (2 files, +46/−19). Edits: `verify-workflow.sh` adds a `WORKSPACE_ROOT_UNAVAILABLE` guard before any `path.join` (:1836-1839) and gates the assembler block on `workspaceRootAvailable`; sanitizes `ORCHESTRATOR_PROMPT_ASSEMBLER_MISSING`/`FAILED`/`DRIFT` to the repo-relative path and the first error line; widens the Magic Context scrub lookahead to `(?=\n#{1,6} )` and adds `MAGIC_CONTEXT_SECTION_MISSING`/`MAGIC_CONTEXT_SECTION_SCRUB_NOOP`; `VERIFY_SCRIPT_SHA256` re-pinned `e6823599…` → `723924c3…`. Checks: `bash -n` rc 0; routing-guard 94 pass / 0 fail; positive+negative controls reproduced the pre-fix `TypeError` and silent-relative fallback and proofed the new guards; pin == `sha256sum`.
- 2026-10-11: T1 native review: lineage `review-079176e1e68deb02`; tier **high** (`shell_source` on `verify-workflow.sh`, `process_boundary` on `workflow-health-check.ts`); candidate 8 files / 226 lines; all four lenses (risk, resilience, readability, reliability) admitted; outcome **approved** and **acknowledged**; `authority: burned`; consumed revision `sha256:ed0832ef…`; reviewed boundary advanced to candidate tree `a04464ae` (HEAD `3d0eb45`).
- 2026-10-11: T1 advisory findings (non-blocking, informational; separate later work, never re-review triggers): `R3-001` (reliability; `verify-workflow.sh:3052-3053` — the scrub lookahead still needs a following heading, so a Magic Context section at end-of-prompt would trip `MAGIC_CONTEXT_SECTION_SCRUB_NOOP`); `R3-002` (reliability; `:1837-1838` — new failure paths not covered by an automated test); `R4-001` (resilience; `:2918-2919` — the assembler-failure message now discards stderr/traceback, trading a real diagnostic for a duplicate command echo); `R4-002` (resilience; `:4827` — hedged claim that the S5b-recorded `:4800` call site was not modified); `R4-003` (resilience — tracker state contradicted the shipped diff; addressed by this metadata update).

## Route / trigger evidence
- Route: delegated. Specialist: `odd-apply` writer (direct; see PM-layer note). Trigger: secure no-inline-mutation policy (any file change delegated); two-or-more non-trivial files (`verify-workflow.sh` + `workflow-health-check.ts`) → bounded sandbox writer.

## Next step
- T2 (Slice 2) — v4 version + SDD assets; then T3, T4. Consider folding the T1 advisories (`R3-001` end-of-prompt lookahead case, `R4-001` diagnostic trim) into T2/T3 while the same file is open. Deployment/restart remains the owner's action.
