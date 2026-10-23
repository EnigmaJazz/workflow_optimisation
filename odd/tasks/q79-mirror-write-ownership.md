# Q79 — Deterministic mirror-write ownership

## Objective

Replace Q77's metadata-worker mirror-write ownership with deterministic host-tool ownership for the tracker mirror write and verification, while keeping the contract accurate even if that host tool has not landed.

## Problem

The current ownership contract is internally inconsistent. `docs/specs/pm-handoff.md:7` denies the PM the tracker/mirror body in its brief and `:28` describes hash-based readback, while `:123` requires the metadata worker to mirror the body and read back both stores. Q77 explicitly preserved the metadata worker's mirror-write ownership, and `tests/test_pm_handoff_spec.py:60-63` pins that ownership as a live assertion. Magic Context 0.46 removed `ctx_memory` from all subagents by design, so the current contracts assign tracker-mirror WRITE and READBACK to actors that cannot perform them.

Stale surfaces requiring correction:
- `WORKFLOW.md:75,91`.
- `global-config/prompts/gentle-orchestrator/overlay.md:111,155,156,164,189`, including the `## Key Learnings` chain at `:155,156,164,189`.
- `global-config/skills/workflow-odd-secure/references/odd-and-review.md:20`.
- Stale grants in `global-config/systematic.jsonc:53,115`, with verifier policy checks at `verify-workflow.sh:1733-1752` and `:2176-2187`.
- `global-config/opencode.json:51` (`explore` agent).

Owner decision: a DETERMINISTIC host tool owns the tracker-mirror write and verify. This unit must explicitly retract Q77's metadata-worker write ownership in a `CLAIM-RETRACTIONS.md` entry; never silently reverse it. The contract must remain correct WHETHER OR NOT the deterministic tool has landed: until it exists, the write simply is not performed, and that is a known recorded state, not a silent gap.

## Scope

- **A — Ownership decision and spec:** retract Q77's ownership decision with a `CLAIM-RETRACTIONS.md` entry; name the deterministic host tool as write+verify owner; fix `docs/specs/pm-handoff.md:123`; settle what happens to the `metadata_work_unit` envelope field; update `tests/test_pm_handoff_spec.py:60-63`.
- **B — Workflow and prompt surfaces:** update `global-config/prompts/gentle-orchestrator/overlay.md`, including the `## Key Learnings` chain at `:155,156,164,189`; update `WORKFLOW.md:75,91` and `global-config/skills/workflow-odd-secure/references/odd-and-review.md:20`; execute and verify the entire 7-step prompt regeneration chain atomically.
- **C — Derived guards:** add `ctx_note` to `FORBIDDEN_RESIDUE` (`tests/test_orchestrator_prompt_source.py:62`); add a verifier check that the embedded prompt equals assembler output (currently only the test constant gates it — F13); fix `global-config/systematic.jsonc` and the verifier's `systematicMemoryPolicy`; resolve the `explore` grant (`global-config/opencode.json:51`, F12).

## Constraints

- Never commit; never switch branches. The host branch is `chore/q72-t1b-tiny-fix-contract`; a sandbox-internal branch named `work` is expected and is not a discrepancy.
- Authorized implementation scope for the future unit is the sources and tests named above, the required retraction entry, and associated prompt-regeneration artifacts. This tracker-creation unit itself changes only the tracker, advice record, and one queue entry.
- Do not grant `ctx_memory` or `ctx_note` to subagents to paper over the missing deterministic host tool.
- Until that tool exists, explicitly record that mirror writing is not performed; do not imply successful write/readback.
- Preserve all invariants named in the advice record, all existing positive controls, and the HOST-ONLY falsifier boundary.
- Keep the 7-step prompt regeneration chain atomic: a partial commit makes the contract red.

## Acceptance criteria

- Q77's decision is explicitly and traceably retracted in `CLAIM-RETRACTIONS.md`; the deterministic host tool is named as owner of mirror write and verify.
- The specification, `metadata_work_unit` envelope semantics, prompts, workflow documents, configuration, tests, and verifier agree, whether or not the tool has landed; absence is an explicit recorded state.
- Tests positively detect the relevant stale instructions, grants, verifier drift, and prompt-regeneration mismatch without weakening existing controls.
- The 7-step regeneration chain is delivered atomically and the prompt-source checks pass.
- A live runtime falsifier is identified as HOST-ONLY; no repository test is represented as proof of runtime behavior.

## Authorized scope

Creation scope: `odd/tasks/q79-mirror-write-ownership.md`, `odd/advice/q79-mirror-write-ownership.md`, and one appended entry in `docs/TODO.md` only. No implementation-source edits are authorized by this tracker-creation request.

Planned implementation scope: the files and surfaces listed in units A/B/C, including the required `CLAIM-RETRACTIONS.md` entry and prompt regeneration chain.

## Checks

- Confirm the spec test now asserts deterministic host-tool ownership and settled `metadata_work_unit` behavior, with a positive control proving it detects the old Q77 ownership.
- Run the focused handoff-spec and orchestrator-prompt-source tests, including their positive controls.
- Run the verifier's relevant fixture/tests, proving embedded prompt equals assembler output and stale `systematicMemoryPolicy`/grant policy is detected.
- Execute the full 7-step prompt regeneration chain and verify its final output; do not accept a partial chain.
- Run the relevant full Python test suite and shell syntax check for verifier changes.
- HOST-ONLY falsifier: when the deterministic host tool exists, perform a live synthetic divergent tracker/mirror case and verify the tool reports divergence and does not claim a successful write/verify. Until it exists, report the write as intentionally not performed and the runtime check as pending.

## Tasks

- [x] **A — Ownership decision and spec:** record the explicit Q77 ownership retraction in `CLAIM-RETRACTIONS.md`; designate the deterministic host tool as mirror write+verify owner; update `pm-handoff.md:123`; decide and document the `metadata_work_unit` envelope field consequence; update `tests/test_pm_handoff_spec.py:60-63` with a positive control.
- [x] **B — Surfaces and atomic regeneration:** correct the overlay and its `## Key Learnings` chain (`:155,156,164,189`), `WORKFLOW.md:75,91`, and `odd-and-review.md:20`; complete and verify all 7 prompt-regeneration steps as one atomic unit. Mirror writing remains explicitly unimplemented because the deterministic host tool has not landed.
- [x] **C — Derived guards:** add `ctx_note` to `FORBIDDEN_RESIDUE` at `tests/test_orchestrator_prompt_source.py:62`; add the F13 verifier check for embedded prompt/assembler equality; fix `systematic.jsonc` and verifier `systematicMemoryPolicy`; resolve the F12 `explore` grant.
- [x] **D — Correct stale verifier expectations:** enforce `explore.ctx_memory=deny`, require the orchestrator-persists wording introduced in unit B, and keep `ctx_memory` out of research/design read-tool expectations while explicitly rejecting it for the explorer. Predicate-level pass/reversion execution was observed on 2026-10-23 with extracted/stubbed predicates; this is source/predicate-complete, not full-verifier or live-runtime proof.
- [x] **E — Q79 review corrections:** suspend the PM mirror-read duty until the deterministic tool exists; gate the verifier check away from probe-free modes; make its positive/negative controls exercise exact equality; report failures distinctly with a subprocess timeout; regenerate and pin all prompt artifacts atomically. The requested suites and sandbox-permitted extracted predicate positive/negative controls were executed on 2026-10-23; source/predicate-complete only, with full-host-verifier/live-runtime proof pending.

- 2026-10-18: Unit C — added `ctx_note` to the forbidden residue tuple and the planted control; the residue suite passed 24/24, detecting all six planted terms. The verifier now compares the embedded orchestrator prompt byte-for-byte with the live assembler output and runs a mutated-prompt control that must fail the same equality predicate. Denied stale `ctx_memory` grants for `research`, `design`, and `explore`; `workflow` remains allowed, with static and runtime verifier expectations aligned. `bash -n`, anchor manifest 10/10, PM-layer 10/10, PM-handoff 8/8, routing-guard 103/103, JSON parsing, and verifier-pin regex coherence pass. Full Python suite: 200 tests, 190 passed and 10 errored because sandbox execution of `node` is denied; no test failures. Full verifier/deploy remains the owner's step because it depends on host paths and unavailable `node`. `verify-workflow.sh` sha256 and plugin pin both equal `fd1d1d8c992cd0cb770bba52dd3b013a22ec3a022543bc0de6c0bfde692203aa`. The deterministic host tool has not landed, so no mirror write/readback was performed. No commit or branch switch.

- 2026-10-18: Unit D — corrected the three stale verifier expectations: `explore` memory permission is denied; the orchestrator contract requires the unit-B persistence wording; and the read-only `explore` runtime tool list no longer requires `ctx_memory`, with an explicit deny check instead. Static Systematic expectations already deny memory for both `research` and `design`. Shell syntax, prompt-source 24/24, anchor manifest 10/10, PM handoff 8/8, and routing-guard 103/103 pass; verifier and pin both equal `151d5cfc840e5f469900714abbbc36d4c8e318ca7733c598d98d0cdda55426ae`. The full Python suite ran 200 tests: 190 passed and 10 errored because sandbox execution of `node` is denied. The required exact-predicate pass/reversion proof remains pending because this sandbox exposes argv-only execution and the full verifier is unavailable; leave this unit incomplete pending that proof. Focused and full suite results are recorded in the ROUTER-LOG row. No commit; no branch switch.

## Delivery strategy

**Chosen strategy:** ask-on-risk. **Forecast at creation:** approximately 600 authored changed lines across the retraction, contract/spec/test, workflow and prompt surfaces, derived guards, and regeneration work; this crosses the approximately 400-line planning threshold, so resolve stacked-to-main versus feature-branch-chain before delivery if the forecast remains above threshold. Recompute from actual work-unit commits; preserve atomicity of the 7-step regeneration chain.

## Progress

- 2026-10-18: T0 — created tracker, pre-code advice record, and Q79 queue entry. Owner decision recorded: deterministic host tool owns mirror write+verify. Magic Context subagent memory tools are unavailable by design; no mirror write/readback was performed as part of this authorized three-path creation. No implementation changes, commit, or branch switch.
- 2026-10-18: Unit A — explicitly retracted Q77's metadata-worker mirror-write decision; clarified that the metadata worker updates/commits repository files only and that `metadata_work_unit` covers those repository-file updates/commit; assigned Magic Context write+verify to the deterministic host tool invoked by the orchestrator; strengthened the ownership assertion and its positive control. Focused handoff-spec suite passed 8/8. Full Python suite ran 200 tests: 190 passed and 10 errored because the sandbox denies execution of `node`; errors are in `test_gemini_advisor_route` subprocess probes. Temporarily restoring Q77's old metadata-worker mirror wording made the new ownership assertion fail as expected. Honest limit: the deterministic host tool has not landed, so mirror write and verification remain unimplemented and were not performed; no Magic Context mirror/readback was possible from this subagent. No commit or branch switch.
- 2026-10-18: Unit B — corrected tracker ownership and readback instructions in the orchestrator overlay, canonical workflow, and ODD reference; updated Key Learnings so subagents return text and the orchestrator persists evidence-backed durable facts. Completed the seven-step prompt regeneration: assembled prompt `7ac00866aef67b734224843453f66681fdd979cde98b4f4f053ab19f5bedc995`, 54,292 bytes / 414 lines; test constant and embedded prompt match assembler output; ledger cites the new digest and classifies the changed `Never mark a task complete without observed checks` rule as kept. No anchor/token rows needed edits; all 39 anchor and 99 token checks pass. Prompt-source 24/24, anchor-manifest 10/10, PM-layer 10/10, PM-handoff 8/8, routing-guard 103/103; full Python suite 190 passed / 10 errored because sandbox execution of `node` is denied. JSON parse and `bash -n` pass; all three agent prompts are present. Temporarily replacing the prompt SHA constant with zeros caused the embedded-prompt/SHA test to fail at its expected digest assertion. The deterministic host tool has not landed, so no mirror write/readback was performed; full verifier/deploy remains an owner step because it depends on host paths and unavailable `node`. No commit or branch switch.

- 2026-10-18: Unit E — corrected the suspended PM mirror-read contract and embedded-prompt verifier controls. Reverted each changed guard in turn: the PM contract test failed on the old mandatory/readback-blocker wording; the verifier regression test failed when the mode gate was removed, when the mutated control was based on the already-divergent embedded prompt, when the 30-second timeout was removed, and when distinct config-error labeling was removed. The identical-prompt and mutated-prompt branches execute successfully against live assembler/config inputs. Final checks: PM handoff 8/8; prompt-source 26/26; anchor manifest 10/10 (39 anchors/99 tokens); routing-guard 103/103; `bash -n verify-workflow.sh` pass; plugin-loads-only probe-free mode exits without invoking the prompt check; assembled prompt, embedded prompt, and test SHA match at `e51b3285759e494d54f737015c461ab3a4225f5bcdc84679f63ab5fa656424ce` (54,547 bytes/414 lines); script/plugin pin match at `77788b42106939bcb6f590a897e09bf8c6d8856596cdff0cc8d8fcd0308914e5`. Full Python suite: 202 tests, 192 pass and 10 error because sandbox denies `node` execution. No commit or branch switch.

- 2026-10-22: Q56 counted unit 3/10 — verified through pm-odd; no route escape; source already complete or verified; metadata commit PENDING-COMMIT

Current execution date for the verification appended below is 2026-10-23; the pilot entry above keeps the owner-requested date.

## Source/predicate verification (2026-10-23)

- **Source presence (read-only):** explore Task `ses_e985e1ceeffePtaNzn6NQVQZER` found the unit D/E source present in `verify-workflow.sh`; no source edit was needed by this metadata unit. This is a source-presence observation, not a full verifier run.
- **Execution-only checks:** `gentle-ai-worker` Task `ses_e985e1cdeffedEnTDI72tVsU5R` (zero tracked changes) ran `python3 -m unittest tests.test_orchestrator_prompt_source -v` with 29 OK including `test_embedded_prompt_verifier_has_real_bidirectional_equality_control`, which executes the real extracted PY heredoc; `tests.test_pm_handoff_spec` 26 OK; `tests.test_pm_layer_prompts` 13 OK; `tests.test_anchor_manifest` 11 OK (39 anchors/99 tokens); `python3 -m unittest discover -s tests` 244 OK with zero failures/errors; `bash -n verify-workflow.sh` rc 0; `python3 -m json.tool global-config/opencode.json` rc 0.
- **Extracted D predicates under Bun:** real memory/read inventories pass. `explore.ctx_memory` allow -> `MAGIC_CONTEXT_MEMORY_POLICY_MISMATCH`; research memory allow -> `Systematic category research.permission.ctx_memory must be deny`; `ctx_memory` exposed -> `RESEARCHER_MEMORY_TOOL_EXPOSED`; missing `ctx_expand` -> `RESEARCHER_READ_OR_MEMORY_TOOL_MISSING`; removed orchestrator-persists wording -> `MAGIC_CONTEXT_ORCHESTRATOR_CONTRACT_MISSING`.
- **Actual E Python heredoc:** real run rc 0; embedded mutation rc 5 DRIFT; invalid config rc 2 CONFIG_INVALID; assembler failure rc 1 ASSEMBLER_FAILED; real 30-second timeout rc 4 ASSEMBLER_TIMEOUT. The exact shell gate runs normally and skips recovery-only/plugin-loads-only modes. Predicate in-memory false mutation rc 3 EQUALITY_CONTROL_FAILED; true mutation rc 3 INEQUALITY_CONTROL_FAILED. PM suspended-wording/anchor positive controls detect reversions.
- **Digests:** current assembled/embedded/test digest `521796dfbfc71a125e49b8bbd8127de7197a491b12a0ea8bd942c29de64a046b` (59,950 bytes / 417 lines); script/pin `28ff39379aee7460bce784386e62c83bf5f51aea2b93074e2f35230fa299e7ad`.
- **Explicit limitations:** these are extracted/stubbed predicate proofs, not full-verifier or live-runtime proof. The full verifier was NOT run because it is host-only/deployment work and is forbidden here. The live synthetic mirror falsifier remains pending; the deterministic host mirror tool is unimplemented, so mirror write/verification was NOT performed. The PM never reads the mirror body.
- **Advisories:** `R4-resilience-02` independence/tautology remains OPEN; false/true mutations establish self-test behavior, not independent validation of equality. `R3-001` committed tests' failure-branch coverage remains OPEN despite this one-off execution. Other advisory history is unchanged. The A/B/C native review gap remains OPEN.
- **PM readback:** the PM metadata factual check and independent orchestrator readback remain PENDING for this unit.

## Route / trigger evidence

Route: delegated ODD tracker creation. Specialist: sandbox worker fallback. Trigger: secure ODD policy delegates every file mutation; substantial work spans three meaningful units and must be tracked before implementation. User explicitly authorized only the tracker, advice record, and queue entry for this unit. Host branch specified by user: `chore/q72-t1b-tiny-fix-contract`; sandbox internal branch `work` is expected. RDD status was not queried because this is an uncommitted tracker-creation unit and user explicitly prohibited committing.

- 2026-10-23: delegated `workflow-odd-secure` to cloud `odd-apply` (this metadata writer unit `q79-de-pm-verify-u1`); trigger: secure ODD mandatory mutation delegation. Initial anchor MATCH: 101 lines, exact last-line text empty, ref `1ab7647be851e2930c23023c87daa42564086066`; this is a working-tree/ref observation, not a committed tracker-blob witness. The sandbox root is `/work`, its internal branch is `work` at baseline commit `20962d13123596ae29aa28f4ec37b5a2ad3e9db3` whose parent is `1ab7647`; that internal baseline is expected.

## Next step

The remaining follow-up is host-only and review-related, not reimplementation: when the deterministic host mirror tool lands, run the live synthetic divergent tracker/mirror falsifier and the full host verifier. Units A/B/C remain source-complete but NOT natively reviewed (the recorded option-1 review gap stays open); do not reimplement A/B/C and do not claim deployment or native review. PM metadata factual check and independent orchestrator readback remain pending for this unit.

## Native review outcome and scope gap

- Native review `review-1eeadae16a12d39c`: **high** risk, 8 files / 94 lines, four lenses; **APPROVED and acknowledged**, `authority: burned`.
- The full candidate (16 paths / 319 lines) was **REFUSED** with `lens_context_budget_exceeded`. The review covered only the correction. **Q79 units A, B, and C were NOT reviewed**; this is the explicit option-1 trade accepted by the owner and remains a real review gap. Candidate commits: `18d269e` (A), `c2963a1` (B), `1de04c0` (C), `f452663` (verifier expectation fix), and `ac9f14b` (correction, reviewed).
- Four advisory findings:
  - `R4-resilience-02` — **SUGGESTION, deterministic** (`verify-workflow.sh`, new equality control): the control is tautological. `matches(prompt)` is defined as `prompt == assembled`, so `matches(assembled)` is always true and `ORCHESTRATOR_PROMPT_EQUALITY_CONTROL_FAILED` is unreachable dead code. The inequality control is the only real self-test.
  - `R4-resilience-01` — **WARNING, inferential** (`verify-workflow.sh`, subprocess output capture): `output=$(python3 ...)` under `set -e` could abort the verifier before distinct diagnostics run, defeating the R4-002 goal. This path is unexercised.
  - `R3-001` — **SUGGESTION** (`tests/test_orchestrator_prompt_source.py`, verifier-control tests): tests assert the presence of the timeout, mode gate, and labels but never exercise the failure branches.
  - `R3-002` — **SUGGESTION** (`verify-workflow.sh`, heredoc extraction): extraction is indentation-sensitive.
- **Cadence failure:** four high-risk commits accumulated before review (A, B, C, and the correction), exactly the condition the Q73 rule is intended to prevent. The full-candidate refusal is the consequence. This was not a completed review of the accumulated work.
- **Sizing measurement:** 985 lines / 14 paths **PASSED**, while 319 lines / 16 paths was **REFUSED**. Path count is the binding constraint, compounded by per-path size: `verify-workflow.sh` (~5,000 lines) and `global-config/opencode.json` (~2,400 lines) dominate reviewer evidence.

