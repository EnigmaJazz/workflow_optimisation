# Q98 — Coordinator selection: the orchestrator must use the PM layer

## Identity and authority

Work unit and task ID: `q98-coordinator-selection-u1`.
Project: `/home/james/ai-workspace/workflow_optimisation`.
Branch: `chore/coordinator-selection`.
Class: global tooling change — normative prompt/policy text plus its pinned test readers.
Route: `workflow-odd-secure`.
Owner authorization: 2026-11-01 ("Automatically"), recorded as the answer to the default question
for substantial units.

This document is the orchestrator's `initial_plan` draft. The PM finalises it, calls the pre-code
advice its task class requires, and issues Gate 1. Nothing here is implementation authorization and
no task is ticked.

## Problem

Observed 2026-11-01: the PM layer is installed and live, and nothing selects it.

- `global-config/prompts/gentle-orchestrator/overlay.md:119` defines `pm-unit-brief/v1` only for the
  conditional "When a unit is delegated to a project-manager (`pm-odd` or `pm-systematic`)". It
  never states the choice.
- `docs/specs/pm-handoff.md` specifies the PM's twelve-step procedure and the planning unit, but
  contains no selection rule.
- `WORKFLOW.md` names the PM layer in three places only: as a writer-family constraint (`:160`), as
  the pre-commit post-code advisor dispatcher (`:573`), and as a Gemini advisor dispatcher (`:626`).
- Consequence observed in the same session: an entire V2 documentation programme ran
  delegated-direct through generic writers, with no PM, no Gate 1 and no Gate 2, and nothing in the
  prompt was violated. The layer is dormant by prompt, not by configuration.

## Specs

- **S1 (policy).** `WORKFLOW.md` gains a coordinator-selection rule: a substantial ODD unit is
  dispatched to `pm-odd`; a substantial Systematic unit to `pm-systematic`; a tiny fix stays a
  direct writer dispatch with no PM; a read-only request starts no coordinator. Selection is by task
  class and the existing substantial-work test, never by the owner asking for a PM.
- **S2 (orchestrator prompt).** The orchestrator overlay carries the same rule, so the orchestrator
  applies it without rereading `WORKFLOW.md` mid-unit.
- **S3 (pins).** The rule is pinned by the existing readers: the orchestrator prompt-source test's
  embedded-prompt SHA and, where the change introduces a stable sentence, an anchor token row.
- **S4 (non-goals).** No change to the PM or Planner contracts, to `pm-unit-brief/v1`, to any
  permission map, to the verifier's semantics, or to the tiny-fix writer selection.

## Tasks

- [ ] T1 (S1-S3): add the selection rule to `WORKFLOW.md` and to the orchestrator overlay; rebuild
  the embedded orchestrator prompt from the assembler; update the pinned prompt SHA.
- [ ] T2 (S3): extend the pinning tests so the rule is asserted once in each surface, with a
  missing-rule control; keep the existing prompt delta reviewable.
- [ ] T3: record the unit row in `ROUTER-LOG.md` and the closure evidence here.

## Acceptance criteria

- The orchestrator prompt states the selection rule exactly once; `grep` for the sentence returns one
  hit in each surface.
- The assembler output changes only by the added rule: the prompt delta is bounded and reported.
- `python3 -m unittest discover -s tests` shows no new failure against the recorded baseline.
- The pinned SHA values match the rebuilt artifacts.
- No permission, PM contract or verifier semantic changes appear in the diff.

## Allowed edit surfaces

1. `WORKFLOW.md`
2. `global-config/prompts/gentle-orchestrator/overlay.md`
3. `global-config/opencode.json`
4. `tests/test_orchestrator_prompt_source.py`
5. `tests/test_anchor_manifest.py`
6. `ROUTER-LOG.md`
7. `odd/tasks/q98-coordinator-selection.md`

## Constraints

- Normative change: pre-code advice, post-code check, independent verifier, native review after the
  commit.
- Prompt assembly is deterministic: the overlay is spliced by
  `global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py` into the embedded
  `gentle-orchestrator` prompt, so the embedded bytes and the pinned SHA must be regenerated, never
  hand-edited.
- Test-first: the missing-rule assertion must be observed RED before the text lands.
- No deployment. `derive --apply` and the restart remain the owner's action; the deployed V2 config
  is currently older than the repo, which is why this unit's own orchestrator prompt lacks the rule.

## Progress

- 2026-11-01: tracker created by the orchestrator (plan-only); PM dispatch pending.

## Next step

Dispatch `pm-odd` with the `pm-unit-brief/v1` envelope so the PM finalises this plan, runs the
required pre-code advice, and issues Gate 1.


## Revisions
- r1 2026-11-01T17:37:19Z gentle-orchestrator: Create the Q98 tracker: coordinator selection rule for substantial units, with the observed evidence and acceptance criteria
