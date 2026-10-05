# Project-manager unit handoff contract

**Status:** normative contract for the project-manager layer (Q55 / tracker T3).

## Brief-in fields

Every PM Task brief is exactly one work unit, never a whole feature. It carries `unit_id`, `task_id` (stable tracker task identifier), `tracker_path` (repository-relative; absent only for planning that creates the tracker), `task_class`, selected `route`, the orchestrator's `initial_plan` (scope, approach, acceptance criteria, non-goals, resolved decisions), `last_reviewed_boundary` (exact commit/revision or explicit `none`), and `constraints` (TDD mode/source/runner, allowed paths, review/delivery policy, required evidence).

## PM prompt boundary

Keep each PM prompt to approximately 6,000 characters or less. It contains only the one-unit identity/authority contract, route-skill load-first requirement and route validation against `WORKFLOW.md`, stop/resume rules, the rule that a report is not proof, and a pointer to this versioned envelope contract. The route procedure, specialist precedence, review protocol, and route-specific checks remain in the loaded `workflow-*` skill and its references. Do not copy the route procedure into a third prompt-level source.

## Route validation and ordered execution

The PM loads its assigned secure route skill first, reads the current `WORKFLOW.md`, and confirms task class and route before any writer dispatch or mutation. Disagreement returns `ROUTE_DISPUTED` with the supplied and expected class/route plus concrete reasons. It dispatches no writer and performs no mutation; only route-skill loading and read-only inspection are permitted.

After route agreement, follow that route skill's current requirements in order:

1. pre-code advice;
2. named writer/specialist for this unit only;
3. required checks, each captured with its observed result;
4. authorized work-unit commit and staged reviewability receipt;
5. post-code advice or Systematic `ce:review`, as the route owes;
6. native review only when the selected non-SDD route and user-owned RDD state require it; then
7. tracker, `docs/TODO.md`, and `docs/PLAN.md` updates as applicable.

Review is route-dependent. **An SDD route never starts native RDD review, never issues native-review consent, and never treats review as an SDD phase gate.** Advisory review remains distinct from native review. Native review Tasks use `asi-review-*` relays, never plain `review-*` names.

Planning is a work unit: `ce:brainstorm`, `ce:plan`, and tracker creation run in a PM session and receive their own work-unit commit before implementation units begin.

## Versioned result envelope

Return one JSON object conforming to `pm-unit-result/v1`:

```json
{
  "schema": "pm-unit-result/v1",
  "status": "DONE | NEEDS_INPUT | BLOCKED | ROUTE_DISPUTED",
  "identity": {
    "project": "registered project identity",
    "unit_id": "stable unit identifier",
    "task_id": "stable tracker task identifier",
    "route": "selected workflow route",
    "pm_session_id": "PM session identifier"
  },
  "candidate": {
    "input_boundary": "exact input/last-reviewed boundary or explicit none",
    "candidate_commits": ["commit identifiers, in order"],
    "final_head": "observed final HEAD",
    "changed_artifacts": ["repository-relative path or durable evidence reference"]
  },
  "progress": {
    "completed_steps": ["ordered step identifiers and outcomes"],
    "pending_step": "next step or null",
    "blocker": "concrete blocker or null"
  },
  "checks": [
    {"name": "check/command", "observed_result": "verbatim or faithfully bounded result", "passed": true}
  ],
  "advice_record": {"reference": "durable advice record or null", "status": "observed state"},
  "review": {
    "mode": "enabled | disabled | not-applicable",
    "mode_source": "default | global | clone-local | not-applicable",
    "assessment_result": "observed result or not-applicable",
    "candidate_selectors": {"base_ref": "exact boundary", "committed_only": true, "other": "exact returned selector values"},
    "due_reason": "provider result or not-applicable",
    "lineage_evidence": "provider lineage, subject and revision evidence or not-applicable",
    "acknowledgement_evidence": "exact acknowledgement evidence or not-applicable",
    "boundary_disposition": "advanced | retained | abandoned | not-applicable with reason",
    "new_reviewed_boundary": "exact new boundary or unchanged boundary"
  },
  "continuation": null,
  "readback": {
    "tracker_reference": "path/revision and observed readback result",
    "magic_context_reference": "exact ODD_TASKS key/item and complete-body readback result"
  }
}
```

The actual status is exactly one of `DONE`, `NEEDS_INPUT`, `BLOCKED`, or `ROUTE_DISPUTED`. Keep every field present even when null or `not-applicable`. Candidate selectors and boundary disposition are explicit: record whether the reviewed boundary advanced, stayed unchanged, or was explicitly abandoned, with reason and evidence.

For `NEEDS_INPUT`, `continuation` is required and contains the **verbatim** user-facing prompt or provider consent envelope (lossless) and exact continuation context: PM Task `task_id`, PM session ID, pending step, prior decisions/results, and provider-returned continuation arguments. Other statuses set it to `null`. A `ROUTE_DISPUTED` envelope records the disagreement/reasons and has no writer dispatch, commit, or mutation in completed steps.

## Human input and resume

Permission prompts surface directly from the PM session. For other questions or required consent, return `NEEDS_INPUT` without paraphrasing or omitting envelope fields. The orchestrator relays it verbatim and resumes the same PM session using Task's `task_id` and exact continuation context. When direct PM `question` is supported and appropriate, it may ask directly; otherwise use the lossless relay. Never start a replacement PM session for an interrupted unit.

## Closure and metadata work unit

The implementation sandbox worker is single-lifecycle and cannot re-enter after termination to update tracker metadata. Therefore, after the implementation candidate is committed, a **separate metadata work unit and worker lifecycle** updates and commits the tracker, `docs/TODO.md`, and `docs/PLAN.md` as applicable, including implementation commit/check evidence and review outcome. That metadata worker mirrors the complete canonical tracker body to Magic Context under the exact registered-project ODD task key and reads back both stores.

A PM returns `DONE` only after observing committed implementation and metadata work-unit state, reading back the final committed tracker and its complete Magic Context mirror, and verifying agreement. Writer completion, a passing test, or a PM report is not closure. The orchestrator independently reads tracker and Git state and compares them with the envelope before the next unit; a report is a claim, not proof. The planning unit commits its plan/tracker artifacts and records the durable tracker reference before `DONE`.
