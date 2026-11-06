# PM-only writer dispatch

## Objective

Plan PM-only dispatch enforcement for `odd-apply` and `gentle-ai-worker`, while preserving sanctioned `gentle-ai-worker-local` dispatch. T1 records FUTURE implementation acceptance criteria; it changes no executable acceptance contract and authorizes no deployment.

## Unit and allowed surface

- Current unit: `pm-only-writer-dispatch-u1-planning`; task `T1`.
- Class: Documentation / simple-docs planning, under WORKFLOW.md:534-557.
- T1 may change ONLY `odd/tasks/pm-only-writer-dispatch.md`.
- No configuration, code, tests, skills, manifest, WORKFLOW.md, queue or router-log edits in T1. Required separate bookkeeping must not silently widen this unit.
- Future enforcement is a separate Global tooling change with its own gates, specification advice, surface advice and independent verifier. This document's exemption does not transfer to it.

## Request trace

Orchestrator draft received: “enforce PM-only dispatch for odd-apply and gentle-ai-worker via global-config/opencode.json denies, tests, skills, systematic.jsonc, ROUTE_STAGES assertions, NONPROMPT re-pin.”

PM suggestions received as messages: “keep tracker simple-docs (odd/tasks/pm-only-writer-dispatch.md only), zero pre/post advice per allowlist but still issue Gate 1, preserve exact-phrase tests, keep gentle-ai-worker-local allowed, record linked-worktree anchor hazard.”

## Observed evidence

- WORKFLOW.md:166-198 defines Planner finalization and technical gates, and prohibits Planner writer/lens dispatch and task marking.
- WORKFLOW.md:536 explicitly allows FUTURE acceptance criteria in planning trackers without making them normative executable contracts; simple docs require PM factual/structural checks plus independent orchestrator Git/tracker readback, not advisor/verifier Tasks. An executable reader or uncertainty disqualifies the exemption.
- This exact tracker path returned file-not-found. The complete sibling task listing showed existing task documents but not this filename, establishing it as a new document in the inspected checkout.
- Read-only explore result `ses_e4ceec05effeQgsKbBuaQmutLD` reports `global-config/opencode.json:778-857` has orchestrator task wildcard ask, explicit local-worker allow, and no specific entries for the two targeted writers. PM task maps carry explicit worker allowances. These are in-repo source observations, not proof of live enforcement.
- Same result identifies existing permission checks/tests in `verify/checkers/check-runtime-agents.cjs`, `tests/test_pm_task_allowlists.py`, `tests/test_review_pipeline_permissions.py`, `tests/test_orchestrator_prompt_source.py`, `tests/test_anchor_manifest.py`, and `tests/routing-guard/routing-guard.test.ts`.
- A read of `.codegraph` returned file-not-found. Read-only/AFT inspection was used; no initialization or execution occurred.

## Tasks

### T1 — Finalize planning tracker

Status: pending; not completed or ticked by the Planner.

Acceptance criteria:
1. Actual diff changes only this document and contains state/planning/evidence text; no executable reader is introduced.
2. The future requirements below retain the draft's scope, exact-phrase regression protections and local-worker exception.
3. Linked-worktree hazards are recorded without fabricating branch, HEAD, unit anchor, execution or fixed-tool success.
4. PM factual/structural check and independent orchestrator Git/tracker readback are supplied against the actual installed candidate. Include applicable Markdown diagnostics or an explicit not-applicable result in the first post-write check, not first after correction.
5. Gate 2 occurs on that candidate with the required pre-commit evidence/assessment BEFORE commit and PM completion/tick. Post-commit native review is not Gate 2 input.

Test expectation: no runtime behavior change; structural checks do not prove dispatch enforcement. No runtime test result is claimed for T1.

### T2 — Future enforcement implementation

Status: not started; separate implementation handoff and Gate 1 required.

Future requirements, not T1 executable contract changes:
- Enforce PM-only dispatch of exactly `odd-apply` and `gentle-ai-worker` through `global-config/opencode.json` denies and intended PM grants. Test default/wildcard resolution and explicit caller overrides; preserve worker self-denials and least privilege.
- Keep `gentle-ai-worker-local` allowed on currently sanctioned routes, including the orchestrator route. Avoid name wildcards that accidentally capture it.
- Add positive and mutation controls for PM success, non-PM refusal, wildcard fallback, explicit override precedence and local-worker non-regression. Reconcile `tests/test_pm_task_allowlists.py`, `tests/test_review_pipeline_permissions.py` and `verify/checkers/check-runtime-agents.cjs` together.
- Reconcile in-repo route skills and `global-config/systematic.jsonc` with the supported permission mechanism. The inspected systematic configuration has no task keys; establish schema support rather than inventing keys.
- Reconcile `ROUTE_STAGES` assertions in `tests/routing-guard/routing-guard.test.ts` with `global-config/plugins/lib/routing-guard-helpers.ts` where the coordinator handoff requires it. Distinguish warning-only stage guidance from actual permission refusal.
- Preserve existing exact-phrase and anchor tests: retain the PM writer clause, `Tiny-fix route:`, direct-orchestrator tiny-fix behavior and `Temporary writer deviation (owner decision, 2026-10-17)` historical marker. Reconcile canonical/mirrored wording together; do not weaken tests to mask contradictions.
- Recompute `NONPROMPT_CONFIG_SHA256` in `tests/test_orchestrator_prompt_source.py` from the resulting non-prompt configuration using its existing canonical serialization; retain the mutation control. Do not copy another branch's digest.
- If verifier modules change, use the repository manifest generator and check to complete the health-check re-pin lifecycle; no handwritten hashes.
- Carry a test-first execution posture. Exact runners and allowed paths must be established in T2, not guessed here. Run required tests, static diagnostics, specification/surface advice and independent verification on the same initial candidate; combine findings into at most one fresh correction.
- Keep behavior and regression tests together within the work-unit reviewability cap. Source review and owner-controlled deployment remain distinct; no technical verdict is delivery authority.

Candidate paths above are references, not T1 edit authority. T2 must establish its exact allowlist, risk/advisor selection, baseline and feature-branch HEAD anchor before implementation.

## Advisor selection for T1

Selected pre-code advisors: none. Selected post-code advisors: none. Independent verifier Tasks: none. Reason: the sole authorized surface is a planning tracker inside the simple-docs allowlist (WORKFLOW.md:536).

Specification pre/post carriers are exempt for this documentation-only unit, not unavailable. Design, security, integration, testing and maintainability advisors are skipped because T1 changes no executable surfaces. Reassess all applicable requirements for T2. Subscription external advisors are not dispatched while that lane is PLANNED; API-credit specification carriers are unnecessary for this exempt unit.

`planner-evidence` is skipped: no facts require that specialized carrier. One bounded read-only `explore` Task supplied in-project references after the direct read budget; its raw result was read and is evidence only, not advice or approval.

## Linked-worktree anchor hazard

Observed: `.git` is a pointer file into the primary repository's worktree metadata; that external target was not followed. `verify/10-env.sh:33` defaults to the primary checkout. Current branch, HEAD and unit-start anchor remain unverified in this planning session.

Inferred risk: a tool assuming a `.git` directory or resolving the default primary checkout could refuse or bind the wrong checkout. This is not an observed fixed-tool failure. Verify returned project/anchor evidence for every host plan/gate operation and later handoff. Stop BLOCKED on mismatch or unavailable authority; never follow external metadata, switch checkouts, widen access or synthesize an anchor to bypass it.

## Gates and closure

Gate 1 is a technical verdict after plan finalization. Zero advisor Tasks are intentional for T1. Gate 2 remains pending the actual installed-document evidence, PM check, independent orchestrator readback and required pre-commit assessment; exempt advisor/verifier positions do not create extra Tasks.

One initial writer plus at most one fresh correction covers all pre-commit checks. Gate 2 runs again after revision; a second failure returns the unit to the human only for a true blocker. Missing authority/evidence is BLOCKED, never assumed success.

No PM completion/tick before Gate 2. No Planner task marking, writer or review-lens dispatch. Commit and subsequent native assessment/review remain with authorized owners. No gate approves deployment, merge, release or user acceptance.

Mirror: no mirror write is claimed. Closure must record actual deterministic mirror availability and result; no improvised memory write.

## Log

- Planner loaded workflow-route and workflow-odd-secure, consulted WORKFLOW.md, and reconciled the orchestrator draft with PM message suggestions.
- Facts gathered by read-only explore session `ses_e4ceec05effeQgsKbBuaQmutLD`; completed raw result read by Planner.
- No writer/advisor/verifier, tests, commit, task mark or deployment performed by Planner. Initial host plan content was refused for a broker-owned section heading; no successful write was claimed from that refusal.


## Revisions
- r1 2026-11-06T22:58:35Z planner: Finalize T1 planning-only scope and future requirements; omit broker-owned log sections.
