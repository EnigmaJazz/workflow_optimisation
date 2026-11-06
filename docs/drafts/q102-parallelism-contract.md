# DRAFT: Q102 parallel implementation contract edits (D31, D32, OPEN-20)

Status: DRAFT. Nothing here is applied to `global-config/` or `docs/specs/`. It waits for the owner to take it
through the `advisor-*` subagents in the OpenCode TUI (WORKFLOW.md makes advice mandatory), then it is applied as
a normal routed work unit with the verifier and tests below. Edits change contracts the live OpenCode setup
consumes (high-risk item 3).

## 1. Replace the single-writer rule (three places, one rule)

Current text: `overlay.md:66` and `base.md:161`: "Use a single writer thread for implementation; do not run
parallel writers unless isolated worktrees are explicitly approved." `odd-and-review.md:83`: "Keep mutating writers
serialized unless the workflow explicitly isolates them in independent worktrees or otherwise proves non-overlapping state."

Replacement for all three (the skill reference points to the orchestrator contract instead of restating it):

> Implementation units that are independent run in parallel: launch every independent writer together as
> background Tasks in one message. Two units are independent when their edit surfaces are disjoint and neither
> consumes the other's output. Each writer prompt names its `## Allowed edit surfaces`, the existing helpers it must
> reuse for shared state, and the invariants those keep. The parent owns git: writers run no commits, repository-wide
> formatters, generators or installs; a shared file has one owner or the parent edits it last; the parent checks each
> writer's diff against its declared surface before accepting it, and one seam check (the full suite, once) runs when
> all return. Units that need the same file run one after another or in isolated worktrees. Within a staging chain, a
> stage is the unit of review: parallelism comes from separate chains (feature and fix lanes) and from disjoint
> writers inside one stage.

Why: the single-writer sentence is the cause named in D31; the Writer-trigger rule already in the gentle-ai block
(`Parallel writers`) is the model for the wording.

## 2. Re-base the PM `unit_start_anchor` (OPEN-20, resolved by the owner)

Dependents (checked): `docs/specs/pm-handoff.md:7, 87, 170-171, 200`; `overlay.md:119`; the `pm-odd` and
`pm-systematic` prompts in `global-config/opencode.json`. The verifier (`verify-workflow.sh:3130-3132`) and the two
test files check only the tags `pm-unit-brief/v1` and `pm-unit-result/v1`: keep both tags unchanged.

Change to the field definition (same name, same `/v1` tag, so no consumer breaks):

- `unit_start_anchor` components become: the exact line count and last-line text of the unit's own tracker
  component (a per-unit file or section, not the shared tracker file), and the **stage's pinned baseline commit**
  SHA (read from `refs/opencode-sandbox/chain/<id>/stage/<n>` or the stage record), replacing the feature-branch
  `HEAD` SHA.
- Mismatch reasons keep their names (`UNIT_START_ANCHOR_MISMATCH`, `MISSING_REQUIRED_UNIT_START_ANCHOR`) so the
  verifier and tests are unaffected; only what the SHA is compared against changes.
- Planning and standalone-tiny-fix rules are unchanged (components `none` as today; a non-planning unit still
  requires the commit component).
- The per-unit tracker component means two PMs working in parallel never compare against a file the other is editing.
- Host commits happen at the owner's apply and review, so the PM no longer reads a moving feature-branch `HEAD`.

Open point for the advisors: the PM has only a `read` tool; confirm the stage ref is readable that way (the
current wording reads the branch ref the same way), or the brief should carry the SHA only and the PM verifies it
against the brief.

## 3. Orchestrator contract: background dispatch (D32)

Add to the orchestrator contract (not the skill): independent Tasks are launched as background subagents and the
parent ends its turn when no independent work remains, resuming on each completion event; it never polls.

## 4. Verification plan (test first)

1. `tests/test_pm_layer_prompts.py`: add a needle test that the single-writer sentence is gone from the three
   files and the disjoint-surface rule is present, with a positive control that the old sentence is detected.
2. Anchor wording: a test that the brief schema still carries `pm-unit-brief/v1` and now names the stage's pinned
   baseline commit; the verifier needle check stays green.
3. Dispatch two disjoint writers in the OpenCode TUI and one overlapping pair; show the first runs in parallel and
   the second is serialized (executed evidence, not a build pass).
4. `HOME="$(mktemp -d)" bun test tests/routing-guard`, `python3 -m unittest discover -s tests`, then
   `bash verify-workflow.sh`; the digest pin is only touched if `verify-workflow.sh` itself changes.
5. Native review: one work-unit commit, escalated item 3, owner consent per candidate.

## 5. Not in this draft

D33 (branch-creation host tool) is a sandbox change that needs coordination with the uncommitted main-checkout
broker work, so it is a separate unit.
