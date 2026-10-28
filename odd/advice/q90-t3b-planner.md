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

## Recovery (2026-10-25, owner-authorized; NOT a correction)
- Verifier `ses_e8f8163b2ffeZzejGDd7pN25jQ`: initial 204 tests OK, zero skips, but V1/V2 FAIL.
  The one correction is used (1/1); this recovery is not another correction; the formatting-only
  rewrap was accepted. Intermediate `85f84ca` is transitional and OWNER-CLOSED, not a review
  candidate. New `VERIFY_SCRIPT_SHA256` `cc88c89e...` re-pinned for the inventory edit. Tracker
  backfill and Q90-D1 remain deferred; deployment was NOT performed and the mirror body was NOT read.

## Advisor-selection revision (q90-t3b-advisor-selection-u1, PM-dispatched 2026-10-25)

- Owner directive 2026-10-25: the live Planner prompt ordered ALL applicable pre-code advisors every
  run, contradicting the verification/advice budget; the prompt must select by task class and impact.
  Documentation-only config text change; class `global tooling change` with OWNER CEREMONY OVERRIDE:
  zero advisors (this unit is the advisor-selection fix), ONE writer, ONE independent verifier,
  correction counter untouched at 0.
- Owner ruling on the RAW-output clause: The selection rule was revised; the raw-output requirement is retained.
- Route `workflow-odd-secure`; unit-start: tracker none (plan-root protected); branch
  `chore/multi-agent-v2-phase1` HEAD at dispatch `707ee925...` expected and observed = MATCH.
- Implementation writer `ses_e8d2ea23dffeh1fJWkufUnXjTR` (`gentle-ai-worker`, DeepSeek); frozen
  result `227d2be...`; receipt 4 lines / 6,560 bytes / generated [].
- Observed checks: baseline focused 8/8 OK; natural RED `FAILED (failures=1)` `'RAW output' not
  found` between edit 1 and edit 2; final focused `Ran 8 tests in 0.423s` OK; `python3 -m json.tool`
  exit 0; `git diff --check` clean; verifier `ses_e8d2b21d6fferrhUqjJ71WCPl7`: diff exactly 2 files /
  2+2-, focused 8/8 OK, JSON valid, absence checks with positive control (new phrase matches the same
  prompt field; removed phrases zero matches), other planner surfaces unchanged vs parent; FULL
  regression not run by the verifier (no-write constraint) — this unit's STEP 0 run: `Ran 341 tests
  in 6.141s` / `OK`. AFT note: `aft_inspect` on the JSON scope was PARTIAL pre-work (no JSON LSP
  producer), no all-clean claim.
- Native assessment at boundary `707ee925...` committedOnly: risk `medium` (`configuration_change`),
  2 paths / 4 lines, `consumed=false`, `review_due=false` (`under_budget`); boundary RETAINED; no
  native review; no approval; this is a technical assessment, not delivery approval.
- Follow-up drift recorded: `WORKFLOW.md:179` and `docs/specs/pm-handoff.md:25-27` still describe the
  every-applicable-advisors + RAW-output planner behavior; both are outside this unit's authorized
  scope and are queued for a later normative follow-up, not preinstalled here.

## Normative doc reconciliation (q90-t3b-planner-reconcile-u1, PM-dispatched 2026-10-25)

- Owner directive 2026-10-25: reconcile the `WORKFLOW.md` and `docs/specs/pm-handoff.md` Planner
  rule/status with the live `planner` prompt (select-by-task-class-and-impact, revised in
  `q90-t3b-advisor-selection-u1`, commit `1a22a939`). The installed/deployed date 2026-10-25 is
  OWNER-asserted; this unit did not independently verify the mirror or the live restart.
- Class `global-tooling-change`, route `workflow-odd-secure`. OWNER CEREMONY OVERRIDE for this unit
  (the advisor-rule reconciliation): zero advisors, zero verifier, one writer, correction budget 1,
  no tracker (plan-root protected), no mirror.
- Unit-start anchor: tracker none (plan-root protected); branch `chore/multi-agent-v2-phase1` HEAD
  `3b341497ccdcab3464c1c9610e81f889e9fc93ee` expected and observed = MATCH.
- Writer session `ses_e8cf338beffeG0Wjx8EprfXYIB` (`odd-apply`, DeepSeek family).
- Staged reviewability receipt: 105 authored changed lines (79 added / 26 deleted); authored patch
  bytes as exported by the sandbox result receipt; generated or binary paths [].
- Edits: `WORKFLOW.md` Planner heading (`installed and live`), intro status paragraph, `planner` Role
  cell (select-by-task-class-and-impact), handoff paragraph; `docs/specs/pm-handoff.md` heading,
  status paragraph, `Sequence:` label, step 3; `tests/test_pm_handoff_spec.py` rename to
  `planner_handoff_gaps` / `test_planner_handoff_is_live_and_gate_owned` with live required terms and
  a removed-phrase absence guard; this record; one `ROUTER-LOG.md` row.
- Q90-D1 deferral retained; Gate-1/Gate-2 ownership prose and the read-only planner grants
  (`host_plan_write`/`host_gate_verdict` ask, `host_task_mark` deny) unchanged.
- Residual drift outside this unit's allowed paths: `global-config/skills/workflow-odd-secure/SKILL.md`
  still describes the handoff as PLANNED/NOT INSTALLED and calls ALL pre-code advisors; queued for a
  later normative follow-up, not edited here.

### Observed checks

- Check 1 — `python3 -m unittest tests.test_pm_handoff_spec tests.test_q90_planner
  tests.test_review_cadence -v`: first run `Ran 37 tests in 0.483s` / `FAILED (failures=1)` because
  step 3 wrapped the required phrase across a line; after the same-unit re-wrap (not a review
  correction) `Ran 37 tests in 0.438s` / `OK`.
- Check 2 — `git diff --check`: no output, exit 0.
- Check 3 — `python3 -m unittest discover -s tests`: `Ran 341 tests in 5.877s` / `OK`; no node-denied
  errors appeared in this run.
- Check 4 — host `.git/HEAD` read before worker activation: `ref: refs/heads/chore/multi-agent-v2-phase1`;
  the branch ref file is `3b341497ccdcab3464c1c9610e81f889e9fc93ee`. The sandbox `.git/HEAD` is the
  synthetic workspace ref `ref: refs/heads/work`, not the feature branch.
- Removal search — no other test file pins the removed phrases; only the new absence guard in
  `tests/test_pm_handoff_spec.py` contains them.

- PENDING: the commit SHA and native risk assessment are recorded in `ROUTER-LOG.md` and the PM
  envelope; the row's commit cell reads `PENDING-COMMIT` because the row ships in the same work-unit
  commit.
