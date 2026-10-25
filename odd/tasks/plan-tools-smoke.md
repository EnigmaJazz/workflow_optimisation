# Plan-tools smoke test

## Objective
Prove the plan lifecycle end to end on a real, small unit: orchestrator draft, PM suggestions, Planner finalisation and Gate 1, one writer, Gate 2, PM tick.

## Route and budget
ROUTE: Documentation | intent: authorized change (plan finalisation only in this Planner session) | route: workflow-odd-secure / Planner Gate 1 | specialist: planner | basis: WORKFLOW.md.

This is a DOCS-ONLY normative unit, not a Tiny fix and not simple docs. Observed: `WORKFLOW.md:526` excludes `WORKFLOW.md` from the simple-docs allowlist. The normal non-simple-docs normative-impact budget is one pre-advice phase, one post-code check and one independent verifier (`WORKFLOW.md:536,539`). The selected budget is the following explicit, unit-scoped owner cost override, not a silently reduced classification.

OWNER OVERRIDE (verbatim): no pre-code advisors, no post-code advisors, no independent verifier. Checks are: the host runner `workflow-tests` plus the focused Python suite (`python3 -m unittest discover -s tests`). One writer (cloud odd-apply), one correction maximum. No deploy, no tracker migration.

Reason: "plan-lifecycle smoke test, owner directive 2026-10-25".

Advisor selection: no pre-code or post-code advisors are selected under this docs-only owner override. Design, integration, testing, security and maintainability advisor Tasks are all skipped for that reason; the unit does not change code or configuration. Gemini advisors are additionally unavailable for dispatch because the external lane is PLANNED, not active. No planner-evidence Task is needed: the draft and both exact anchor regions were established through the Planner's own reads. No independent verifier is selected under the same override. The PM factual/structural self-check and independent orchestrator readback remain required; they are not independent-verifier Tasks. This override does not waive Gate 2 or any applicable native review requirements.

## Work item
Add exactly this normative sentence: "A Tiny fix is never automatically native-reviewed; any review is the outcome of its own risk assessment."

Pinned location: the Tiny fix budget row under `WORKFLOW.md` -> `Verification and advice budget by task type` -> `Budget matrix over the six existing route classes`, currently line 532. Append the sentence inside the final table cell, immediately after `zero `gentle-ai-verify``. The exact final row is:

```markdown
| Tiny fix | zero pre-advice (passive tiny) | zero post-advice | zero `gentle-ai-verify`. A Tiny fix is never automatically native-reviewed; any review is the outcome of its own risk assessment. |
```

Do not edit the route-decision paragraph at `WORKFLOW.md:85`.

Mirror decision (ii): the normative sentence lives only in `WORKFLOW.md`. The Tiny fix row at `docs/specs/pm-handoff.md:47` keeps the budget vector, not this prose, and remains unchanged. This is one normative-file change, not a two-file normative mirror update.

## Acceptance criteria
- AC1: The exact sentence "A Tiny fix is never automatically native-reviewed; any review is the outcome of its own risk assessment." appears only in the Tiny fix budget row in the normative `WORKFLOW.md` change, inside the final table cell immediately after `zero `gentle-ai-verify`` at the pinned `WORKFLOW.md:532` anchor, yielding the exact final row shown above. The route-decision paragraph at `WORKFLOW.md:85` remains unchanged. Quoting the target sentence in this planning tracker is permitted.
- AC2: No other row, section, file, config, agent, verifier, skill or prompt changes. This restriction applies to the normative implementation diff; the explicitly sanctioned lifecycle updates to this tracker's `## Log` and `## Revisions`, Gate records, T2 evidence/completion metadata and their separate metadata commit are permitted and are not prohibited by AC2.
- AC3: The host runner `workflow-tests` and companion command `python3 -m unittest discover -s tests` pass for the resulting implementation candidate/commit. Record each observed result and the exact candidate/commit identity; do not claim a check passed from an unexecuted command or a syntax-only check.
- AC4: Preserve T1/T2 identifiers. Record the evidence commit and the Planner's Gate 2 technical verdict before the PM ticks T1. Commit the sanctioned tracker evidence/closure updates separately as metadata. The Planner does not tick tasks or create commits.

## Checks
Required runners, adopting PM suggestion (d)'s canonical-host-runner alternative:
1. Host runner: `workflow-tests`.
2. Focused Python companion command: `python3 -m unittest discover -s tests`.

`workflow-tests` is the owner-designated canonical host runner for this unit; do not replace it with a vague "workflow tests" description or add a separate manual routing-guard command as a third required check. Execution must use the authorized runner/executor surfaces, never Planner host shell execution. These checks are planned, not yet reported as executed. If a required runner or authority is unavailable, report BLOCKED rather than substituting a check.

The first post-code pass also performs the required factual/structural checks and applicable static diagnostics on the same initial candidate: exact final row, valid table structure, unchanged route-decision paragraph and pm-handoff vector, and permitted-path diff. Consolidate any findings before using the sole correction allowance; targeted rechecks do not create a new correction budget.

## Tasks
- T1 — add the pinned sentence to the `WORKFLOW.md` Tiny fix budget row. Pending. Gate 1 follows successful Planner plan finalisation. The PM may subsequently dispatch one cloud `odd-apply` writer; one fresh correction writer maximum is permitted if needed. The Planner dispatches neither writer nor review lens.
- T2 — record the evidence commit and tick T1 after Gate 2. Pending. Tracker `## Log`/`## Revisions` evidence and closure updates and their separate metadata commit are permitted. Gate 2 follows the required post-code evidence (zero post-code advisors by the owner override) and the orchestrator's raw post-commit lens evidence. The Planner reads the raw evidence and issues the technical verdict before PM completion/ticking. Both gates are technical only, never delivery, deployment, merge, release or user-acceptance approval.

## PM suggestions resolved
- (a) Adopt: Documentation class with normative impact; not simple docs. State the normal one-pre/one-post/one-verifier budget and the owner-decided override and reason explicitly above.
- (b) Choose (ii): normative prose in `WORKFLOW.md` only; `docs/specs/pm-handoff.md:47` retains the vector, not the prose, and is unchanged.
- (c) Adopt: pin the exact sentence and final-cell placement in the budget row at `WORKFLOW.md:532`; AC1 uses this anchor, not the route-decision paragraph at line 85.
- (d) Adopt the canonical-host-runner alternative: required checks are `workflow-tests` plus `python3 -m unittest discover -s tests`.

## Non-goals
No model, permission, fallback, verifier, skill, prompt or tracker-format migration work.

## Log
- 2026-10-25 planning: Draft and normative anchor regions read; PM suggestions resolved for this finalisation. Implementation checks and post-commit evidence remain pending. No writer, advisor or review lens dispatched by the Planner; no task ticked and no commit created by the Planner.




## Revisions
- r1 2026-10-25T13:36:57Z gentle-orchestrator: Orchestrator draft for the plan-tools smoke unit
- r2 2026-10-25T13:49:14Z planner: Planner finalisation r1 -> r2 (plan-tools smoke)
- r3 2026-10-25T16:43:28Z planner: r3: broker task-ID shape (T1/T2) replacing ST1/ST2; content unchanged

- r4 2026-10-25T16:43:45Z pm-odd: task mark T1 passed

- r5 2026-10-25T16:44:47Z pm-odd: task mark T2 passed

## Ticks
T1 passed evidence=04077e6673f4546bb8e035ba41d1468c4edd10b7 tier=high 2026-10-25T16:43:45Z pm-odd: smoke unit; swept into 04077e6; Gate 2 post-facto; owner override
T2 passed evidence=04077e6673f4546bb8e035ba41d1468c4edd10b7 tier=high 2026-10-25T16:44:47Z pm-odd: evidence commit recorded; T1 ticked after Gate 2

## Gates
- ST1 PASS 2026-10-25T13:50:06Z planner ref=odd/tasks/plan-tools-smoke.md r2; WORKFLOW.md:526-549; docs/specs/pm-handoff.md:39-58; owner override 2026-10-25: zero advisors; PM suggestions (a)-(d) resolved. Gate 1 technical only.
- ST1 PASS 2026-10-25T16:40:09Z planner ref=d=0a26402d478be918cbbae40c4610497d212d27c39f62c0ffaf773551ba22212d;w=93e28776f73b6858369c642b75da9a5740a5579f54f43142c5737f9d31ed4ee4;exit0,342/OK,105ctl;post-facto;2units@04077e6;ST1-tech;W176-196
- T1 PASS 2026-10-25T16:43:32Z planner ref=d=0a26402d478be918cbbae40c4610497d212d27c39f62c0ffaf773551ba22212d;w=93e28776f73b6858369c642b75da9a5740a5579f54f43142c5737f9d31ed4ee4;exit0,342/OK,105ctl;post-facto;2units@04077e6;ST1-tech;W176-196
- T2 PASS 2026-10-25T16:44:39Z planner ref=d=0a26402d478be918cbbae40c4610497d212d27c39f62c0ffaf773551ba22212d;w=93e28776f73b6858369c642b75da9a5740a5579f54f43142c5737f9d31ed4ee4;exit0,342/OK,105ctl;post-facto;2units@04077e6;ST1-tech;W176-196
