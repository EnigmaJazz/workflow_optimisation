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
- [ ] **B — Surfaces and atomic regeneration:** correct the overlay and its `## Key Learnings` chain (`:155,156,164,189`), `WORKFLOW.md:75,91`, and `odd-and-review.md:20`; complete and verify all 7 prompt-regeneration steps as one atomic unit.
- [ ] **C — Derived guards:** add `ctx_note` to `FORBIDDEN_RESIDUE` at `tests/test_orchestrator_prompt_source.py:62`; add the F13 verifier check for embedded prompt/assembler equality; fix `systematic.jsonc` and verifier `systematicMemoryPolicy`; resolve the F12 `explore` grant.

## Delivery strategy

**Chosen strategy:** ask-on-risk. **Forecast at creation:** approximately 600 authored changed lines across the retraction, contract/spec/test, workflow and prompt surfaces, derived guards, and regeneration work; this crosses the approximately 400-line planning threshold, so resolve stacked-to-main versus feature-branch-chain before delivery if the forecast remains above threshold. Recompute from actual work-unit commits; preserve atomicity of the 7-step regeneration chain.

## Progress

- 2026-10-18: T0 — created tracker, pre-code advice record, and Q79 queue entry. Owner decision recorded: deterministic host tool owns mirror write+verify. Magic Context subagent memory tools are unavailable by design; no mirror write/readback was performed as part of this authorized three-path creation. No implementation changes, commit, or branch switch.
- 2026-10-18: Unit A — explicitly retracted Q77's metadata-worker mirror-write decision; clarified that the metadata worker updates/commits repository files only and that `metadata_work_unit` covers those repository-file updates/commit; assigned Magic Context write+verify to the deterministic host tool invoked by the orchestrator; strengthened the ownership assertion and its positive control. Focused handoff-spec suite passed 8/8. Full Python suite ran 200 tests: 190 passed and 10 errored because the sandbox denies execution of `node`; errors are in `test_gemini_advisor_route` subprocess probes. Temporarily restoring Q77's old metadata-worker mirror wording made the new ownership assertion fail as expected. Honest limit: the deterministic host tool has not landed, so mirror write and verification remain unimplemented and were not performed; no Magic Context mirror/readback was possible from this subagent. No commit or branch switch.

## Route / trigger evidence

Route: delegated ODD tracker creation. Specialist: sandbox worker fallback. Trigger: secure ODD policy delegates every file mutation; substantial work spans three meaningful units and must be tracked before implementation. User explicitly authorized only the tracker, advice record, and queue entry for this unit. Host branch specified by user: `chore/q72-t1b-tiny-fix-contract`; sandbox internal branch `work` is expected. RDD status was not queried because this is an uncommitted tracker-creation unit and user explicitly prohibited committing.

## Next step

Dispatch the authorized implementation work for units A/B/C on the specified host branch; before implementation, resolve the outstanding `metadata_work_unit` envelope consequence and confirm how the deterministic host tool is represented. If the tool has not landed, preserve the explicit known-not-performed state and do not claim mirror write/readback.
