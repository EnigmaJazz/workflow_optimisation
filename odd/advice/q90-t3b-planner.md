# Q90 T3b Planner unit — advice and route record

## Identity and authorization

- Unit `q90-t3b-planner-u1`; task `q90-multi-agent-v2-queue`; class `global-tooling-change`.
- Owner authorization 2026-10-24 is a fresh writer authorization, separate from the one remaining
  correction (used: 0). Prior frozen results `30f00ac7bd85824e32b730a485cb2a80f7bc1132` and
  `ac28216d7daae167f8ca4817ff3d810f837b4b3a` were REJECTED and are NOT installed, restored,
  cherry-picked, or reused. The prior writer's TDD ordering deviation (tests executed AFTER source,
  not pre-source RED) is recorded; this unit ran RED before source/docs.

## Route and evidence

- Route `workflow-odd-secure`, delegated `odd-apply`, multi-file plus secure preparation. This record
  was created before the first source/docs edit. One writer, one later independent
  `gentle-ai-verify`, NO pre/post advisors and ONE correction; no advisor or reviewer result is
  claimed.
- Baseline attestation: sandbox root `/work`, branch `work`, synthetic HEAD
  `63aa25ec24ae42684da330c5049407213702a3b1`, parent
  `416f289ea0d0bee83669c9fa881e0b55dc653c40`; `git diff --stat 416f289 HEAD` is empty. The untracked
  `ses_e8f9d06abffet3DxrvrqOqnaLB.bundle` is not authored.

## Owner scope and decisions

- Add `planner` (`openai/gpt-6.1-sol` `high`; read-only except ask-gated `host_plan_write` and
  `host_gate_verdict`, with `host_task_mark` denied) and `planner-evidence`
  (`openai/gpt-6-luna` `medium`; facts-only, no task). Add `planner` ONLY to the orchestrator,
  `pm-odd` and `pm-systematic` task maps. Preserve every other task grant, PM GLM model, fallback
  profile, and global host deny. No guard, `ROUTE_STAGES`, overlay, embedded prompt, ledger,
  assembler/base/upstream, prompt-SHA or systematic-config change.
- Docs add the planned Planner handoff and Gate 1/Gate 2 ownership. The pipeline is SOURCE-ONLY and
  NOT installed, deployed or live; current PM runtime ownership remains until deferred integration.
  Gate 1 follows pre advice; Gate 2 follows post advice and the orchestrator's raw lens evidence and
  occurs BEFORE PM completion/tick. Both verdicts are technical only, never delivery.
- Owner decision 2026-10-24 closes `455a769..416f289` metadata by OWNER DECISION, NOT native review;
  reviewed boundary `416f289`. Luna/Tiny (`general`, `jd-fix-agent`) sharing is an owner-accepted
  exception. Q90-D1 prompt reduction/externalization is deferred until the PM layer becomes active;
  it is not an immediate prerequisite and was not performed.
- THIS-CANDIDATE size exception: 700 authored changed lines, 102,400 raw patch bytes, 46,080 bytes
  per file; no compression or coverage deletion. Tracker backfill is delegated to the orchestrator
  later because `odd/tasks/**` is protected; the owner-supplied 1,015-line whole-file
  `host_plan_write` replacement (revision 0) was NOT invoked or written. Mirror write/readback is
  UNIMPLEMENTED and was not read.
## Observed checks

- RED: `tests.test_q90_planner` failed with `KeyError: 'planner'` / `KeyError: 'planner-evidence'`
  and `planner-handoff block not found in verify-workflow.sh`.
- GREEN: focused `tests.test_q90_planner` 7 tests OK; required regression 204 tests OK, no skips;
  `bash -n`, JSON parse, `py_compile` and `git diff --check` exited 0; verifier digest
  `7245cd6da2445e5cdd044bf31ff562712f9d2a360f40ec47be7f88d0608a2bed` matches the plugin pin.
- AFT was denied after activation; no AFT static-clean claim. `sandbox_read` caps at 201,008 bytes,
  so bounded `sed -n` range reads were used for large-file inspection (no shell search or mutation).
  Markdown and the TypeScript pin have no available LSP producer. Full verifier, deploy, restart,
  live consumer, commit, independent verifier, correction decision and assessment remain PENDING.
