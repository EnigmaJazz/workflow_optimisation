# Project-manager unit handoff contract

**Status:** normative contract for the project-manager layer (Q55 / tracker T3).

## Brief-in fields

Every PM Task brief is exactly one work unit, never a whole feature. It carries the schema tag `pm-unit-brief/v1`, `unit_id`, `task_id` (stable tracker task identifier), `tracker_path` (repository-relative; explicit `none` for planning that creates the tracker or a standalone tiny fix), `unit_start_anchor` (exact line count of the tracker file read by the PM, exact literal text of its last line, and the feature-branch `HEAD` commit SHA; for planning that creates the tracker, all components are explicitly `none`; for a standalone tiny fix, only the tracker-derived line-count and last-line components are `none`, while the branch `HEAD` commit SHA is required for every non-planning unit), `task_class`, selected `route`, the orchestrator's `initial_plan` (scope, approach, acceptance criteria, non-goals, resolved decisions), `last_reviewed_boundary` (exact commit/revision or explicit `none`), `feature_branch` (the exact branch the unit must be on, or explicit `none` only for planning that creates the tracker), `rdd_mode` (`enabled | disabled`) and `rdd_mode_source` (`default | global | clone-local`), and `constraints` (TDD mode/source/runner, allowed paths, review/delivery policy, required evidence). The PM reads the tracker path and counts its displayed lines, records its exact literal last-line text, and reads the feature branch ref SHA, using only its `read` tool. This read-based anchor catches stale or truncated working-tree tracker text and a wrong feature-branch HEAD SHA. It does not establish that the tracker contents are committed or equal the blob in that commit; it does not catch whitespace-only changes that preserve line count and last-line text, semantically divergent changes, or long-line truncation that leaves those observations unchanged. It is not a cryptographic witness. Hash-based `tracker_sha256` and `mirror_sha256` duties are SUSPENDED until the deterministic host tool lands; that tool landing is the named trigger that returns the hash duty. The PM does not receive `ctx_memory` and must not be given or asked to fetch the mirror body. The PM verifies these inputs against `WORKFLOW.md`; brief schema mismatches are invalid and stop dispatch before any writer.

## PM prompt boundary

Keep each PM prompt to approximately 6,000 characters or less. It contains only the one-unit identity/authority contract, route-skill load-first requirement and route validation against `WORKFLOW.md`, stop/resume rules, the rule that a report is not proof, and a pointer to this versioned envelope contract. The route procedure, specialist precedence, review protocol, and route-specific checks remain in the loaded `workflow-*` skill and its references. Do not copy the route procedure into a third prompt-level source.

## Planner handoff (installed and live)

`planner`, `planner-evidence` and the three plan tools are installed and deployed as of 2026-10-25.

Sequence:

1. The orchestrator drafts the plan.
2. The PM reads the draft and hands it to the Planner with its own suggestions. Suggestions are
   messages, never plan writes.
3. The Planner finalises the plan and selects only the pre-code advisors the task class and impact require:
   none for documentation, metadata, comment-only, tiny or passive; one surface advisor for
   medium code; at most three for high-risk, normative, config, security or cross-cutting. It reads
   each selected advisor's RAW output and never accepts a PM or orchestrator summary as the advice.
   `planner-evidence` runs only when facts cannot be established by the Planner's own reads.
4. **Gate 1** follows the pre-code advice. The Planner issues `PASS`, `REFINE`, or `ESCALATE` through
   the ask-gated `host_gate_verdict` fixed act.
5. A writer implements; the Planner runs the required post-code advisory check.
6. The orchestrator dispatches the four post-commit lenses and supplies their raw evidence.
7. **Gate 2** follows both the post-code advice and the raw lens evidence. Gate 2 occurs BEFORE the PM completes or ticks the unit. The PM does not close the unit before Gate 2.
8. The PM ticks the unit after Gate 2; the orchestrator then assesses and acknowledges; the owner
   approves delivery.

Both gate verdicts are TECHNICAL only. They never approve delivery, deployment, merge, release, or
user acceptance. The Planner is read-only except for the ask-gated `host_plan_write` and
`host_gate_verdict` fixed acts; `host_task_mark` is denied. It dispatches no writer and no review lens. Deferred Q90-D1 prompt reduction/externalization happens only AFTER the PM layer becomes active; it is not an immediate prerequisite to making the PM layer active and is not performed here.

## Verification and advice budget by task type

The unit's **actual diff** selects a finite budget, not its feature class, file count or risk estimate alone; a native medium/high raise moves a unit up, never down.

**Simple-docs allowlist (fail closed).** A unit is simple docs only when every changed path is in this allowlist: `odd/tasks/**` and `odd/advice/**` (state, planning and evidence only), `ROUTER-LOG.md`, `CLAIM-RETRACTIONS.md`, `docs/TODO.md`, `docs/TODO-HISTORY.md`, or the non-Constraints/non-decisions portions of `docs/PLAN.md`. A planning tracker may state FUTURE acceptance criteria without changing an existing executable acceptance contract. Any test/verifier reader disqualifies the unit; uncertainty fails closed. `WORKFLOW.md`, `AGENTS.md`, `docs/specs/**`, `global-config/**`, `ANCHOR_MANIFEST` files and command-changing docs are never simple docs. **No automatic source-comment exemption** applies. Simple docs get zero pre-advice, zero post-advice and zero `gentle-ai-verify` Tasks: the PM performs factual and structural checks and an orchestrator independently reads back Git and tracker state. A metadata unit follows this rule only when its actual diff is in the allowlist.

| Route class | Pre-code advice | Post-code check | Independent verifier |
|---|---|---|---|
| Tiny fix | zero pre-advice (passive tiny) | zero post-advice | zero `gentle-ai-verify` |
| Small feature | one pre-advice phase | one post-code check | none unless an explicit exception applies |
| Substantial feature | one pre-advice phase | one post-code check; `ce:review` substitutes for the post advisor | none unless an explicit exception applies |
| Bug investigation | one pre-advice phase | one post-code check | none unless an explicit exception applies |
| Documentation | zero pre-advice for simple docs; otherwise one pre-advice phase | zero post-advice for simple docs; otherwise one post-code check | zero `gentle-ai-verify` for simple docs; otherwise an explicit exception only |
| Global tooling change | one pre-advice phase | one post-code check | one independent verifier |

A medium ordinary behaviour, test-only or command-changing-docs unit takes one pre-advice phase and one post-code check; `ce:review` substitutes for the post advisor when it runs, and the verifier is the explicit exception only for a security boundary, uncertainty, live fallback/independence, or an explicitly reduced small-model profile. A high normative contract/config/security/enforcement-test/dependency or plugin-pin change takes one pre-advice phase, one post-code check and one independent verifier. Generated inherits source. Counts are check phases, not numbers of baseline reviewers; the named `ce:review` baseline reviewers stay intact. The configured `opencode-go/deepseek-v4.1-flash` writer is NOT treated as a small/reduced profile merely because of the "flash" name (owner decision, 2026-10-21); the medium verifier exception must name the reduced profile and reason.

**One-correction ceiling.** A unit gets one initial writer plus ONE fresh correction writer across all pre-commit post-code gates, including `ce:review` and external advice. Batch all applicable checks on the SAME candidate before correction, name findings with finding IDs, issue one consolidated fix brief, install first, then refine on the installed base; a targeted recheck of those IDs and affected regression controls is not a full new advice cycle. The same unresolved blocker, or a new blocker during recheck, does not buy another round: record advisory/follow-up for non-blockers, return `NEEDS_INPUT` for explicit human authorization, or `BLOCKED` for missing authority/environment/evidence. A human may authorize a bounded exception with reason, scope and a new limit; record any override separately; metadata or a new task ID never silently resets the counter. Record `correction_rounds_used` as `0|1` in `pm-unit-result/v1`. Native review is a separate authority: a native correction gets one scoped fix plus a targeted native validator and is then closed; no PM advisor or verifier cycle runs on it, and native review state stays untouched. A tiny fix escalated after commit owes the applicable post-code check on the committed candidate; any correction is a new commit, never rewriting history.

**Static diagnostics in the first post-code pass.** The FIRST post-code verification pass runs on the SAME INITIAL candidate and includes the required tests, the post-code advisor or `ce:review`, the verifier where the budget owes one, and `aft_inspect` or applicable static diagnostics for every changed path. All findings join the ONE correction batch. Running diagnostics for the first time only after correction is a process defect.

**Writer tier.** `gentle-ai-worker-local` takes exactly ONE changed file per writer Task; cloud writers may batch a coherent multi-file unit.

## Route validation and ordered execution

The PM loads its assigned secure route skill first, reads the current `WORKFLOW.md`, and confirms task class and route before any writer dispatch or mutation. Disagreement returns `ROUTE_DISPUTED` with the supplied and expected class/route plus concrete reasons. It dispatches no writer and performs no mutation; only route-skill loading and read-only inspection are permitted. At unit start, it verifies the feature branch the brief names: it compares the checked-out branch against the brief's `feature_branch` by reading `.git/HEAD` with its existing `read` grant. The check PASSES only when `.git/HEAD` contains `ref: refs/heads/<feature_branch>` exactly. It returns `BLOCKED`, naming the observed state and never passing silently, for a raw SHA (detached HEAD), a different branch name, an unborn branch with no `refs/heads/<feature_branch>`, a worktree whose HEAD lives under `.git/worktrees/`, an in-progress rebase or merge, or an unavailable read; the absence of a read surface is itself a blocking condition, not a pass. For bounded read-only investigation, the PM delegates to `explore` agents instead of doing the reading itself, reducing PM workload while retaining ownership of the resulting understanding and implementation contract.

After route agreement, follow that route skill's current requirements in order:

1. verify at unit start, via the `read`-based `.git/HEAD` check above, that the checked-out branch equals the brief's `feature_branch`; do not defer this check until commit time;
2. pre-code advice when the finite actual-diff budget requires it; a true simple-docs unit inside the allowlist takes none;
3. named writer/specialist for this unit only;
4. required checks, each captured with its observed result;
5. post-code advisory review from the PM before the work-unit commit, only when the unit's actual-diff budget requires it: every normative change, including a normative or command-doc change, owes the budget's post-code check exactly as code does; routes that do not run Systematic `ce:review` owe the registered post-code advisor review; routes that run `ce:review` do not owe that additional advisor review, and `ce:review` plus the external pair are one consolidated phase whose same-candidate findings merge, never a full rerun. Only a true docs/metadata unit inside the allowlist or a genuinely passive tiny fix owes neither; its factual/structural check and the independent orchestrator readback stand in. The advisory reviewer must be independent of the author, and all advisory blockers must be resolved before the work-unit commit;
6. staged reviewability receipt and authorized PM-owned work-unit commit;
7. after that commit, obtain the native review risk assessment against the committed candidate; continue native review only when the selected non-SDD route and user-owned RDD state require it. The pre-apply assessment requirement is removed. The PM does not run native review;
8. tracker, `docs/TODO.md`, and `docs/PLAN.md` updates as applicable.

At unit start, the PM reads the tracker path and compares the exact line count and literal last-line text it can observe, plus the feature-branch `HEAD` commit SHA read from that branch's ref, with the supplied `unit_start_anchor`; it uses only its `read` tool. It does not claim that the working-tree tracker text is committed or that it matches the tracker blob in the referenced commit. Any mismatch returns `BLOCKED` with reason `UNIT_START_ANCHOR_MISMATCH` before work begins. A missing or invalid anchor when the unit is not the planning unit returns `BLOCKED` with reason `MISSING_REQUIRED_UNIT_START_ANCHOR`. For a planning unit that creates the tracker, `tracker_path` and every `unit_start_anchor` component, including the branch `HEAD` commit SHA, are explicitly `none`, and the dispatch-time comparison is skipped rather than blocked. For a standalone tiny fix, `tracker_path` and the tracker-derived anchor components (line count and last-line text) are explicitly `none`; the tracker comparison is skipped rather than blocked, while the branch `HEAD` commit SHA is required for every non-planning unit and its comparison still runs. For every non-planning unit, including a standalone tiny fix, a missing or mismatched branch `HEAD` commit SHA blocks the unit. The PM does not fetch or read back the Magic Context body. The line count and last-line text catch stale or truncated working-tree tracker text only when those observations differ; the branch ref SHA catches a wrong feature-branch HEAD. This anchor does not detect whitespace-only or semantic changes that preserve those observations, does not detect long-line truncation that leaves the line count and last line unchanged, and is not a cryptographic witness. Hash-based `tracker_sha256` and `mirror_sha256` duties are SUSPENDED until the deterministic host tool lands; that event is the trigger for restoring the hash duty. An unverifiable `last_reviewed_boundary` also returns `BLOCKED`, naming the value and resolution failure (an explicit `none` is valid); an outstanding prerequisite check that cannot be run or whose result is unknown returns `BLOCKED`, naming the check (an unrun check is never treated as passed).

When a writer's result needs refinement, install the result first, then dispatch a fresh writer to refine the installed base; never reconstruct the changes from the original base. The unit gets one initial writer plus ONE fresh correction writer across all pre-commit post-code gates, including `ce:review` and external advice; batch same-candidate findings with finding IDs, issue one consolidated fix brief, then targeted recheck. The same unresolved blocker, or a new blocker during recheck, does not buy another round: `NEEDS_INPUT` for explicit human authorization, or `BLOCKED` for missing authority/environment/evidence; metadata or a new task ID never silently resets the counter. Sandbox workers are single-lifecycle and terminal after apply, so every iteration uses a fresh worker regardless. Installing each iteration makes progress durable immediately, which matters because worker sessions routinely stall or are cancelled. Only the reviewed result is committed; intermediate installed states are not committed. The host tree therefore carries uncommitted intermediate states: maintain tree hygiene and deliberately reconcile the intended feature branch before continuing.

The implementation sandbox worker does not commit. The PM commits the worker's applied result through the reviewed fixed host commit operation; that grant sits on the PM, not the worker. The worker supplies the staged reviewability receipt before the PM commits. The writer brief must not require native review evidence; if the worker cannot produce it, that does not block the unit. The PM obtains review-mode evidence through its own host review tools, including `host_review_mode_status`. After the installed implementation is committed, the PM obtains candidate risk-assessment evidence through `host_review_assess` against that committed candidate, then obtains any further evidence through the applicable `host_review_*` grants; the sandbox writer never enters the review path. A pre-apply assessment is not required: `host_review_assess` does not accept an uninstalled sandbox result.

Review is route-dependent. **An SDD route never starts native RDD review, never issues native-review consent, and never treats review as an SDD phase gate.** Advisory review remains distinct from native review. Native review Tasks use `asi-review-*` relays, never plain `review-*` names.

Planning is a work unit: `ce:brainstorm`, `ce:plan`, and tracker creation run in a PM session and receive their own work-unit commit before implementation units begin. A planning unit is simple docs only when its actual diff is in the allowlist; changing an executable acceptance, normative spec, constraint or test/verifier reader makes it normative with its applicable execution checks.

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
  "correction_rounds_used": 0,
  "docs_exemption": {
    "applicable": false,
    "changed_paths": ["repository-relative path"],
    "rationale": "per-path allowlist clause or explicit not-applicable",
    "stats": "git diff --stat summary or explicit not-applicable",
    "diff_check": "observed git diff --check result or explicit not-applicable",
    "branch_head": "observed feature branch and HEAD SHA or explicit not-applicable",
    "asserted_references": "referenced revisions and ancestry evidence or explicit not-applicable",
    "pm_check": "PM factual and structural check result or explicit not-applicable",
    "orchestrator_readback": "independent Git/tracker readback result or explicit not-applicable"
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
      "method": "compare observed working-tree tracker line_count and exact last_line_text, plus feature_branch head_commit_sha read from the branch ref, with brief unit_start_anchor using read only; does not establish committed tracker contents; skip for planning creation",
      "observed": {
        "line_count": "exact observed line count or none",
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

`correction_rounds_used` is `0|1`. An override is recorded separately, never by resetting the counter. A unit whose status relies on the simple-docs allowlist must populate `docs_exemption`: the exact changed paths and per-path allowlist rationale, the diff stats, the observed `git diff --check` result, the feature branch and HEAD SHA, any asserted references/ancestry evidence, the PM factual/structural check, and the orchestrator's independent Git/tracker readback. Its `advice_record` status `not-applicable` with a reason. True docs run no runtime tests; any test reader makes the unit normative and requires the applicable deterministic execution checks. Keep both fields present for a normative unit, with `docs_exemption.applicable` set to `false`.

For `NEEDS_INPUT`, `continuation` is required and contains the **verbatim** user-facing prompt or provider consent envelope (lossless) and exact continuation context: PM Task `task_id`, PM session ID, pending step, prior decisions/results, and provider-returned continuation arguments. Other statuses set it to `null`. A `ROUTE_DISPUTED` envelope records the disagreement/reasons and has no writer dispatch, commit, or mutation in completed steps.

## Human input and resume

Permission prompts surface directly from the PM session. For other questions or required consent, return `NEEDS_INPUT` without paraphrasing or omitting envelope fields. The orchestrator relays it verbatim and resumes the same PM session using Task's `task_id` and exact continuation context. When direct PM `question` is supported and appropriate, it may ask directly; otherwise use the lossless relay. Never start a replacement PM session for an interrupted unit.

## Closure and metadata work unit

The implementation sandbox worker is single-lifecycle and cannot re-enter after termination to update tracker metadata. Therefore, after the implementation candidate is committed, a **separate metadata work unit and worker lifecycle** ensures the metadata worker updates and commits the repository files only: the tracker, `docs/TODO.md`, and `docs/PLAN.md` as applicable, including implementation commit/check evidence and review outcome. A metadata unit whose actual diff is inside the simple-docs allowlist takes the docs budget; if it changes normative text, or any test/verifier reads it, it is normative and takes the applicable deterministic execution checks. The metadata worker identity/session and repository-file outcome are recorded in `metadata_work_unit`; its commit is included in `candidate_commits` and receives its own reviewability receipt and any required post-commit RDD assessment. The deterministic host tool owns the Magic Context mirror write and verification and is invoked by the orchestrator; the PM still never reads or touches the mirror body. The host tool has not landed, so its mirror write and verification are currently unimplemented and are not performed.

A metadata-worker failure after successful implementation leaves the unit `BLOCKED`, with the implementation commit retained in candidate evidence, `metadata_work_unit.status` set to `failed`, the concrete failure recorded, and `metadata` as the pending step. The PM must not return `DONE`.

A PM returns `DONE` only after observing committed implementation and metadata work-unit state, checking the tracker path's current readable working-tree text against the unit-start anchor (or explicitly skipping that comparison for a planning unit that creates it), and recording that the read does not prove the tracker text is committed or equals the committed blob. The PM does not read the Magic Context mirror body. It records the three observed anchor values and comparison outcome in the result envelope; mismatch is `BLOCKED` with the named reason `UNIT_START_ANCHOR_MISMATCH`, while an absent required anchor is `BLOCKED` with `MISSING_REQUIRED_UNIT_START_ANCHOR`. Hash-based `tracker_sha256` and `mirror_sha256` duties remain SUSPENDED until the deterministic host tool lands; its landing is the trigger for restoring those duties. When the route's RDD state requires assessment, the PM obtains the post-commit assessment for every applicable candidate commit through its own host review tools, including `host_review_assess`, and records the terminal outcome using the applicable `host_review_*` readback; committing and mirroring without completing that assessment cannot satisfy `DONE`. Writer completion, a passing test, or a PM report is not closure. The orchestrator independently reads tracker and Git state and compares them with the envelope before the next unit; a report is a claim, not proof. The planning unit commits its plan/tracker artifacts and records the durable tracker reference before `DONE`.
