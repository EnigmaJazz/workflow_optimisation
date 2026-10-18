# Project-manager unit handoff contract

**Status:** normative contract for the project-manager layer (Q55 / tracker T3).

## Brief-in fields

Every PM Task brief is exactly one work unit, never a whole feature. It carries the schema tag `pm-unit-brief/v1`, `unit_id`, `task_id` (stable tracker task identifier), `tracker_path` (repository-relative; explicit `none` only for planning that creates the tracker), `unit_start_anchor` (exact byte (or character) count of the committed tracker file, exact literal text of its last line, and the `HEAD` commit SHA for the unit's feature branch; explicit `none` only for planning that creates the tracker), `task_class`, selected `route`, the orchestrator's `initial_plan` (scope, approach, acceptance criteria, non-goals, resolved decisions), `last_reviewed_boundary` (exact commit/revision or explicit `none`), `feature_branch` (the exact branch the unit must be on, or explicit `none` only for planning that creates the tracker), `rdd_mode` (`enabled | disabled`) and `rdd_mode_source` (`default | global | clone-local`), and `constraints` (TDD mode/source/runner, allowed paths, review/delivery policy, required evidence). The PM reads and compares all three anchor values using only its `read` tool. This catches a stale tracker, a truncated tracker, or a wrong commit; it does not catch a whitespace-only or semantically divergent change and is not a cryptographic witness. Hash-based `tracker_sha256` and `mirror_sha256` duties are SUSPENDED until the deterministic host tool lands; that tool landing is the named trigger that returns the hash duty. The PM does not receive `ctx_memory` and must not be given or asked to fetch the mirror body. The PM verifies these inputs against `WORKFLOW.md`; brief schema mismatches are invalid and stop dispatch before any writer.

## PM prompt boundary

Keep each PM prompt to approximately 6,000 characters or less. It contains only the one-unit identity/authority contract, route-skill load-first requirement and route validation against `WORKFLOW.md`, stop/resume rules, the rule that a report is not proof, and a pointer to this versioned envelope contract. The route procedure, specialist precedence, review protocol, and route-specific checks remain in the loaded `workflow-*` skill and its references. Do not copy the route procedure into a third prompt-level source.

## Route validation and ordered execution

The PM loads its assigned secure route skill first, reads the current `WORKFLOW.md`, and confirms task class and route before any writer dispatch or mutation. Disagreement returns `ROUTE_DISPUTED` with the supplied and expected class/route plus concrete reasons. It dispatches no writer and performs no mutation; only route-skill loading and read-only inspection are permitted. At unit start, it verifies the feature branch the brief names: it compares the checked-out branch against the brief's `feature_branch` by reading `.git/HEAD` with its existing `read` grant. The check PASSES only when `.git/HEAD` contains `ref: refs/heads/<feature_branch>` exactly. It returns `BLOCKED`, naming the observed state and never passing silently, for a raw SHA (detached HEAD), a different branch name, an unborn branch with no `refs/heads/<feature_branch>`, a worktree whose HEAD lives under `.git/worktrees/`, an in-progress rebase or merge, or an unavailable read; the absence of a read surface is itself a blocking condition, not a pass. For bounded read-only investigation, the PM delegates to `explore` agents instead of doing the reading itself, reducing PM workload while retaining ownership of the resulting understanding and implementation contract.

After route agreement, follow that route skill's current requirements in order:

1. verify at unit start, via the `read`-based `.git/HEAD` check above, that the checked-out branch equals the brief's `feature_branch`; do not defer this check until commit time;
2. pre-code advice;
3. named writer/specialist for this unit only;
4. required checks, each captured with its observed result;
5. post-code advisory review from the PM before the work-unit commit: routes that do not run Systematic `ce:review` owe the registered post-code advisor review; routes that run `ce:review` do not owe that additional advisor review. The advisory reviewer must be independent of the author, and its findings must inform the candidate that is committed;
6. staged reviewability receipt and authorized PM-owned work-unit commit;
7. native review only when the selected non-SDD route and user-owned RDD state require it; it remains separately driven and is never run by the PM; then
8. tracker, `docs/TODO.md`, and `docs/PLAN.md` updates as applicable.

At unit start, the PM reads the committed tracker file and compares its exact byte (or character) count, exact literal last-line text, and feature-branch `HEAD` commit SHA with the supplied `unit_start_anchor`, using only its `read` tool. Any mismatch returns `BLOCKED` with reason `UNIT_START_ANCHOR_MISMATCH` before work begins. A missing or invalid anchor when the unit is not the planning unit returns `BLOCKED` with reason `MISSING_REQUIRED_UNIT_START_ANCHOR`. For a planning unit that creates the tracker, `tracker_path` and `unit_start_anchor` are explicitly `none`, and the dispatch-time comparison is skipped rather than blocked. The PM does not fetch or read back the Magic Context body. The byte/character count, last line, and commit SHA catch a stale tracker, a truncated tracker, or a wrong commit, but do not catch whitespace-only or semantically divergent changes and are not a cryptographic witness. Hash-based `tracker_sha256` and `mirror_sha256` duties are SUSPENDED until the deterministic host tool lands; that event is the trigger for restoring the hash duty. An unverifiable `last_reviewed_boundary` also returns `BLOCKED`, naming the value and resolution failure (an explicit `none` is valid); an outstanding prerequisite check that cannot be run or whose result is unknown returns `BLOCKED`, naming the check (an unrun check is never treated as passed).

When a writer's result needs refinement, install the result first, then dispatch a fresh writer to refine the installed base; never reconstruct the changes from the original base. Repeat as needed. Sandbox workers are single-lifecycle and terminal after apply, so every iteration uses a fresh worker regardless. Installing each iteration makes progress durable immediately, which matters because worker sessions routinely stall or are cancelled. Only the reviewed result is committed; intermediate installed states are not committed. The host tree therefore carries uncommitted intermediate states: maintain tree hygiene and deliberately reconcile the intended feature branch before continuing.

The implementation sandbox worker does not commit. The PM commits the worker's applied result through the reviewed fixed host commit operation; that grant sits on the PM, not the worker. The worker supplies the staged reviewability receipt before the PM commits.

Review is route-dependent. **An SDD route never starts native RDD review, never issues native-review consent, and never treats review as an SDD phase gate.** Advisory review remains distinct from native review. Native review Tasks use `asi-review-*` relays, never plain `review-*` names.

Planning is a work unit: `ce:brainstorm`, `ce:plan`, and tracker creation run in a PM session and receive their own work-unit commit before implementation units begin.

## Versioned result envelope

Return one JSON object conforming to `pm-unit-result/v1`. The brief version is carried in `identity.brief_schema`; it must equal the input brief's `pm-unit-brief/v1` tag, otherwise reject the envelope as a version mismatch.

```json
{
  "schema": "pm-unit-result/v1",
  "status": "DONE | NEEDS_INPUT | BLOCKED | ROUTE_DISPUTED",
  "identity": {
    "brief_schema": "pm-unit-brief/v1",
    "project": "registered project identity",
    "unit_id": "stable unit identifier",
    "task_id": "stable tracker task identifier",
    "route": "selected workflow route",
    "pm_session_id": "PM session identifier"
  },
  "candidate": {
    "input_boundary": "exact input/last-reviewed boundary or explicit none",
    "candidate_commits": ["implementation and metadata commit identifiers, in order"],
    "final_head": "observed final HEAD",
    "changed_artifacts": ["repository-relative path or durable evidence reference"],
    "reviewability_receipt": {
      "authored_changed_lines": 0,
      "authored_patch_bytes": 0,
      "generated_or_binary_paths": ["repository-relative path"]
    }
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
  "routing_gate_observations": [
    {"observed_at": "timestamp", "event": "gated call and intended action", "log_reference": "guard log path and matching evidence"}
  ],
  "review": {
    "mode": "enabled | disabled | not-applicable",
    "mode_source": "default | global | clone-local | not-applicable",
    "assessment_result": "observed result or not-applicable",
    "assessment_terminal_outcome": "observed terminal outcome or not-applicable",
    "candidate_selectors": {"base_ref": "exact boundary", "committed_only": true, "other": "exact returned selector values"},
    "due_reason": "provider result or not-applicable",
    "lineage_evidence": "provider lineage, subject and revision evidence or not-applicable",
    "acknowledgement_evidence": "exact acknowledgement evidence or not-applicable",
    "boundary_disposition": "advanced | retained | abandoned | not-applicable with reason",
    "new_reviewed_boundary": "exact new boundary or unchanged boundary"
  },
  "metadata_work_unit": {
    "status": "complete | failed | not-applicable",
    "worker": "metadata worker identity and session or not-applicable",
    "commit": "metadata commit identifier or null",
    "failure": "observed failure or null"
  },
  "continuation": null,
  "readback": {
    "tracker_reference": "path/revision and observed readback result",
    "magic_context_reference": "orchestrator-supplied mirror reference; PM does not read the body",
    "unit_start_anchor_comparison": {
      "method": "compare observed committed-tracker byte_or_character_count, exact last_line_text, and feature_branch head_commit_sha with brief unit_start_anchor using read only; skip for planning creation",
      "observed": {
        "byte_or_character_count": "exact observed count or none",
        "last_line_text": "exact literal last line or none",
        "head_commit_sha": "observed feature-branch HEAD SHA or none"
      },
      "outcome": "MATCH | BLOCKED: UNIT_START_ANCHOR_MISMATCH | BLOCKED: MISSING_REQUIRED_UNIT_START_ANCHOR | skipped: planning creation",
      "mismatch_blocked_reason": "UNIT_START_ANCHOR_MISMATCH | MISSING_REQUIRED_UNIT_START_ANCHOR | null"
    }
  }
}
```

The actual status is exactly one of `DONE`, `NEEDS_INPUT`, `BLOCKED`, or `ROUTE_DISPUTED`. Keep every field present even when null or `not-applicable`. `candidate_commits` includes both the implementation work-unit commit and the metadata work-unit commit, in order; each applicable commit receives its own receipt and review assessment. Candidate selectors and boundary disposition are explicit: record whether the reviewed boundary advanced, stayed unchanged, or was explicitly abandoned, with reason and evidence. `routing_gate_observations` records log-only guard warnings, since a gated call may succeed without returning warning text. `metadata_work_unit` covers only the metadata worker's repository-file updates and commit (the tracker, `docs/TODO.md`, and `docs/PLAN.md` as applicable); it does not represent Magic Context mirror writing or verification.

For `NEEDS_INPUT`, `continuation` is required and contains the **verbatim** user-facing prompt or provider consent envelope (lossless) and exact continuation context: PM Task `task_id`, PM session ID, pending step, prior decisions/results, and provider-returned continuation arguments. Other statuses set it to `null`. A `ROUTE_DISPUTED` envelope records the disagreement/reasons and has no writer dispatch, commit, or mutation in completed steps.

## Human input and resume

Permission prompts surface directly from the PM session. For other questions or required consent, return `NEEDS_INPUT` without paraphrasing or omitting envelope fields. The orchestrator relays it verbatim and resumes the same PM session using Task's `task_id` and exact continuation context. When direct PM `question` is supported and appropriate, it may ask directly; otherwise use the lossless relay. Never start a replacement PM session for an interrupted unit.

## Closure and metadata work unit

The implementation sandbox worker is single-lifecycle and cannot re-enter after termination to update tracker metadata. Therefore, after the implementation candidate is committed, a **separate metadata work unit and worker lifecycle** ensures the metadata worker updates and commits the repository files only: the tracker, `docs/TODO.md`, and `docs/PLAN.md` as applicable, including implementation commit/check evidence and review outcome. The metadata worker identity/session and repository-file outcome are recorded in `metadata_work_unit`; its commit is included in `candidate_commits` and receives its own reviewability receipt and any required post-commit RDD assessment. The deterministic host tool owns the Magic Context mirror write and verification and is invoked by the orchestrator; the PM still never reads or touches the mirror body. The host tool has not landed, so its mirror write and verification are currently unimplemented and are not performed.

A metadata-worker failure after successful implementation leaves the unit `BLOCKED`, with the implementation commit retained in candidate evidence, `metadata_work_unit.status` set to `failed`, the concrete failure recorded, and `metadata` as the pending step. The PM must not return `DONE`.

A PM returns `DONE` only after observing committed implementation and metadata work-unit state, checking the tracker against the unit-start anchor (or explicitly skipping that comparison for a planning unit that creates it), and reading the final committed tracker file itself. The PM does not read the Magic Context mirror body. It records the three observed anchor values and comparison outcome in the result envelope; mismatch is `BLOCKED` with the named reason `UNIT_START_ANCHOR_MISMATCH`, while an absent required anchor is `BLOCKED` with `MISSING_REQUIRED_UNIT_START_ANCHOR`. Hash-based `tracker_sha256` and `mirror_sha256` duties remain SUSPENDED until the deterministic host tool lands; its landing is the trigger for restoring those duties. When the route's RDD state requires assessment, the post-commit assessment for every applicable candidate commit must have been executed and its terminal outcome recorded; committing and mirroring without completing that assessment cannot satisfy `DONE`. Writer completion, a passing test, or a PM report is not closure. The orchestrator independently reads tracker and Git state and compares them with the envelope before the next unit; a report is a claim, not proof. The planning unit commits its plan/tracker artifacts and records the durable tracker reference before `DONE`.
