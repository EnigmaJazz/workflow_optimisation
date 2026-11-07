# PM-only writer dispatch

## Objective

Plan PM-only dispatch enforcement for `odd-apply` and `gentle-ai-worker`, while preserving sanctioned `gentle-ai-worker-local` dispatch. T1 records FUTURE implementation acceptance criteria; it changes no executable acceptance contract and authorizes no deployment.

## Unit and allowed surface

- Current unit: `pm-only-writer-dispatch-u1-planning` (`T1`, closed) and `pm-only-writer-dispatch-u2-enforcement` (`T2`, done).
- T1 class: Documentation / simple-docs planning, under WORKFLOW.md:534-557.
- T1 changed ONLY `odd/tasks/pm-only-writer-dispatch.md`.
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

Status: DONE 2026-11-06 (Gate 2 reconciled by the orchestrator plan read-back; planning-only, no executable surface).

Acceptance criteria:
1. Actual diff changes only this document and contains state/planning/evidence text; no executable reader is introduced.
2. The future requirements below retain the draft's scope, exact-phrase regression protections and local-worker exception.
3. Linked-worktree hazards are recorded without fabricating branch, HEAD, unit anchor, execution or fixed-tool success.
4. PM factual/structural check and independent orchestrator Git/tracker readback are supplied against the actual installed candidate. Include applicable Markdown diagnostics or an explicit not-applicable result in the first post-write check, not first after correction.
5. Gate 2 occurs on that candidate with the required pre-commit evidence/assessment BEFORE commit and PM completion/tick. Post-commit native review is not Gate 2 input.

Test expectation: no runtime behavior change; structural checks do not prove dispatch enforcement. No runtime test result is claimed for T1.

### T2 — Future enforcement implementation

Status: DONE 2026-11-07 under an owner-authorized Gate 2 substitution; the unit commit is recorded in `ROUTER-LOG.md`.

Delivered (all paths inside the authorized surfaces):
- `global-config/opencode.json`: explicit `odd-apply`/`gentle-ai-worker` denies in the orchestrator map (its wildcard is `ask`) and in `frontend-dev-premium` (same leak); `general` and `gentle-ai-worker-local` grants unchanged; PM maps unchanged; no embedded prompt text touched.
- `verify/checkers/check-runtime-agents.cjs`: `PM_ONLY_WRITERS` and `pmOnlyWriterDispatchFailures`, wired into the deployed failure sweep beside `coordinatorTaskGraphFailures`, with in-file positive controls. Fail-closed on malformed agent/task shapes (only the bare string `deny` passes), partial-glob evaluation (`odd-*`, `gentle-ai-*`) after exact-key and `*` resolution, and a `gentle-ai-worker-local` non-match control.
- `tests/test_pm_task_allowlists.py`, `tests/test_review_pipeline_permissions.py`, `tests/test_model_independence.py`, `tests/routing-guard/routing-guard.test.ts`: config-level assertions plus mutation controls for the deny, the wildcard leak, the PM required grants, the globs and the local-worker non-regression; the model-independence absence assertion was strengthened to an explicit `deny`.
- `global-config/plugins/lib/routing-guard-helpers.ts` and `global-config/plugins/systematic-routing-guard.ts`: exported PM-only membership/predicate and a warning-only PM-only notice for non-PM dispatchers; the guard never refuses, and PM sessions do not warn.
- `global-config/skills/workflow-route/SKILL.md` and `global-config/skills/workflow-odd-secure/SKILL.md`: one sentence per skill stating that the permission layer is the refusal, only the PMs dispatch the two writers, `gentle-ai-worker-local` stays allowed, and the stage table is warning-only guidance. Anchor markers and contractual literals unchanged.
- `global-config/systematic.jsonc`: header comment only; no `task` key invented.
- `verify-workflow.sh` and `global-config/plugins/workflow-health-check.ts`: regenerated by `python3 scripts/verifier_manifest.py update` as the last implementation edit; `check` is current. Final pin `d0150ecf...`.

Resolved decisions:
- The planner map stays `{"*": "deny"}` with no literal entries: effective deny already holds and `tests/test_q90_planner.py:99-106` pins that exact key set.
- `tests/test_model_independence.py:118` now asserts an explicit `deny`; absence was no longer sufficient once the orchestrator wildcard is `ask`, so the change strengthens the assertion.
- The routing guard remains warning-only guidance; the OpenCode task-permission layer is the enforcement point.

Reviewability and budget: ~557 authored changed lines (+544/−13 across 14 implementation files) against the ~400-line heuristic. Not split: the deny rules, their skill and stage-table agreement, the verifier predicate with its controls, and the pins that bind them are ONE cohesive behaviour; splitting would separate the deny from the controls that prove it.

Follow-ups recorded, not blockers: the PM-only warning sits inside the `!tinyFix` branch, so a `[tiny-fix]`-marked non-PM dispatch emits none and no test pins that interaction; and no negative control proves stage gating still fires from a PM-bound session.

### Future requirements (retained from T1, all satisfied by T2)

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

## Advisor selection for T1

Selected pre-code advisors: none. Selected post-code advisors: none. Independent verifier Tasks: none. Reason: the sole authorized surface is a planning tracker inside the simple-docs allowlist (WORKFLOW.md:536).

Specification pre/post carriers are exempt for this documentation-only unit, not unavailable. Design, security, integration, testing and maintainability advisors are skipped because T1 changes no executable surfaces. Reassess all applicable requirements for T2. Subscription external advisors are not dispatched while that lane is PLANNED; API-credit specification carriers are unnecessary for this exempt unit.

`planner-evidence` is skipped: no facts require that specialized carrier. One bounded read-only `explore` Task supplied in-project references after the direct read budget; its raw result was read and is evidence only, not advice or approval.

## Advisor and Gate 2 record for T2

- Pre-code: Gate 1 PASS 2026-11-07T00:02:36Z by the Planner after three raw pre-code advisors.
- Post-code: the registered `advisor-*-post` / `advisor-gemini-post` lanes are hidden agents not materialized for subagent dispatch (queue Q105), so the Planner could not obtain its compulsory advice and refused Gate 2. That refusal is a tooling fault with zero content defects in the unit.
- Owner authorization, recorded verbatim 2026-11-07: "The owner authorizes a Gate 2 substitution for the installed T2 candidate: Gate 2 is satisfied by the independent gentle-ai-verify PASS plus the ce:review baselines (correctness PASS, testing PASS, security BLOCK fixed and rechecked, project-standards covered by the orchestrator read-back). The block was a tooling fault (the Planner's advisor lanes are hidden agents, queue Q105), not a defect in the unit. Do not run more reviewers."
- Gate 2 therefore stands as an owner-authorized substitution, not a Planner verdict; it remains technical only and grants no delivery, merge, release or deployment authority.

## Linked-worktree anchor hazard

Observed: `.git` is a pointer file into the primary repository's worktree metadata; that external target was not followed. `verify/10-env.sh:33` defaults to the primary checkout. Current branch, HEAD and unit-start anchor remain unverified in this planning session.

Inferred risk: a tool assuming a `.git` directory or resolving the default primary checkout could refuse or bind the wrong checkout. This is not an observed fixed-tool failure. Verify returned project/anchor evidence for every host plan/gate operation and later handoff. Stop BLOCKED on mismatch or unavailable authority; never follow external metadata, switch checkouts, widen access or synthesize an anchor to bypass it.

## Gates and closure

Gate 1 for T1 and T2 is recorded. T2 Gate 2 is the owner-authorized substitution above. One initial writer plus at most one fresh correction covered every pre-commit check, with the SEC-1 rework treated as the same batch. Missing authority/evidence is BLOCKED, never assumed success.

No gate approves deployment, merge, release or user acceptance. The source-only change is not deployed: the live mirror still needs the owner's reviewed deployment step.

Mirror: no mirror write is claimed. Closure must record actual deterministic mirror availability and result; no improvised memory write.

## Log

- Planner loaded workflow-route and workflow-odd-secure, consulted WORKFLOW.md, and reconciled the orchestrator draft with PM message suggestions.
- Facts gathered by read-only explore session `ses_e4ceec05effeQgsKbBuaQmutLD`; completed raw result read by Planner.
- No writer/advisor/verifier, tests, commit, task mark or deployment performed by Planner. Initial host plan content was refused for a broker-owned section heading; no successful write was claimed from that refusal.
- T2 unit start: anchor MATCH (99 lines, exact last line, branch HEAD `84e4956`); route `workflow-odd-secure`; class global tooling change.
- T2 writers: initial `odd-apply` produced sandbox result `1de900be` (13 files); the surface-authorized `tests/test_model_independence.py` strengthening was applied on top; one consolidated correction (`ses_e4b1a5ac`) then the SEC-1 rework (`ses_e4b06d7c`) were installed in order. No git remote was re-added at any point.
- T2 post-code evidence, all on the installed candidate: routing guard 123 pass / 0 fail / 297 expects; focused Python 186 OK with 9 environment skips; full `discover -s tests` 842 run = 756 passed / 20 failures / 28 errors / 38 skipped, every one environment-limited (sandbox `node` denial, absent `sqlite3`/db-swap); `verifier_manifest.py check` current; orchestrator prompt digest `6fd686e4` unchanged; `aft_inspect` 0 errors; independent `gentle-ai-verify` PASS on the final candidate.
- T2 reviews: correctness PASS; testing PASS with the two follow-ups recorded above; security BLOCK on two predicate defects (fail-open malformed shapes, unchecked partial globs) plus one vacuous control, all fixed in the same batch and rechecked RESOLVED; project-standards did not finish within its step budget and its open items were covered by orchestrator read-back (`systematic.jsonc` comment-only with no `task` key, anchor-manifest suite green, manifest/pin current).
- T2 Gate 2: owner-authorized substitution (verbatim above) after the Planner's advisor-lane refusal; `correction_rounds_used: 1`.
- T2 metadata landing: the tracker is protected for sandbox workers and `host_plan_write` refused the PM agent, so the orchestrator lands this tracker text; the `ROUTER-LOG.md` row was written by the metadata writer in the same unit commit.


## Revisions
- r1 2026-11-06T22:58:35Z planner: Finalize T1 planning-only scope and future requirements; omit broker-owned log sections.
- r2 2026-11-07T08:35:40Z gentle-orchestrator: T2 closure: owner-authorized Gate 2 substitution, review and check evidence, budget/no-split decision, follow-ups

## Gates
- T1 PASS 2026-11-06T22:58:52Z planner ref=Gate 1 only: tracker r1 read back; doc-only exemption, local-worker and exact-phrase safeguards retained. Plan tool auto-committed 4adc76a8 before Gate 2; closure needs PM reconciliation.
- T2 PASS 2026-11-07T00:02:36Z planner ref=Gate 1 T2: three raw advisors read; finalized scoped plan in Planner continuation. Ordered exact orchestrator denies; RED/GREEN, PM/local controls, V2 parity; source-only, no schema/live changes.
