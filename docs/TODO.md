# TODO

Ordered open work, one row per work unit. Maintained by the orchestrator alongside the in-agent
todo list and the per-feature tracker (`odd/tasks/<feature>.md`). The feature tracker holds the
detail for one body of work; this file holds the cross-cutting queue and the order.

**Contract:** updating this file gates STARTING a new work unit. A unit paused awaiting user
input is a valid recorded state and does not block. Unfinished work must be finished or
explicitly parked before another unit starts.

**Completeness rule (user requirement, 2026-10-01):** every planned work unit is listed here,
once, with its prerequisites. Work that exists only in a plan, tracker or handoff is a defect in
this file. Dated reasoning and the old item bodies live in `docs/TODO-HISTORY.md`.

**Former BLOCKER (sandbox worker lifecycle): RESOLVED / narrowed.** Evidence in
`docs/TODO-HISTORY.md`: worker creation and mutation work (item 1 landed through
`sandbox_apply_patch` and was verified by execution, commit `71a2eb3`); `sandbox_edit` landed a
change on a small file. Residual faults, tracked below: the `sandbox_read` timeouts were re-probed
on 2026-10-01 and are fixed (`docs/TODO-HISTORY.md` "2026-10-01 — sandbox_read confirmed fixed");
the rule revision is Q12; the install-vs-commit gap is a cross-project item (Q13).

Status vocabulary: DONE (with commit) / IN PROGRESS / READY (prerequisites met) / BLOCKED
(a prerequisite is unmet) / PLANNED (not started, not yet scheduled) / PARKED. "status
unverified" means the evidence is ambiguous; the line says what would confirm it.

## Queue (in order)

**Phases (2026-10-02).** Q-numbers are stable IDs; the phases give the execution order, and
`docs/PLAN.md` Sequence follows them.
- **Phase 1, guard and handoff fixes:** Q01 close-out, then Q03 (absorbs the overlapping Q20 and
  Q21 findings), then Q25. Q35 can run at any time.
- **Phase 2, verifier and gating foundations:** Q26, then Q28, then Q04, plus Q48 (rule now; lint
  after Q26).
- **Phase 3, recipe and policy:** Q05, Q09, the Q10 items, Q12, Q14, Q24, Q50, then the remaining
  READY and PLANNED items in listed order (Q11, Q13, Q15-Q23).
- **Phase 4, gentle-ai v4 upgrade (owner-triggered):** Q29, then Q30-Q33 and Q35-Q39 delivered as
  the Q36 change set, then Q34, plus Q65 and Q66. Q49 runs throughout.
- **Phase 5, OpenCode V2 upgrade (owner-triggered, after Phase 4):** Q40-Q47.
- **Project-manager layer (owner, 2026-10-04; runs alongside Phases 2 and 3):** Q53 and Q54 are
  complete as reports. Removal check (c) PASSED by a failed `pm-probe` Task dispatch. Checks (a)
  and (b) are PARTIALLY PASSED: permitted-operation broker authorization and the installed
  sandbox-refusal list were observed, while the broker deny path and broker-side identity list
  remain unobservable/unverifiable from this workspace. Q55's post-code advisory review is done;
  its other acceptance work remains open. Q56/Q58 must carry these evidence limits forward rather
  than describe all three removal checks as outstanding or passed. See Q54, Q56 and Q58 below.
  Then Q57-Q60 and Q61. Q62 (retired-model list and seat-assignment reconciliation) is independently
  planned.
- **Advisor capacity (owner, 2026-10-17; independent of the phases):** Q76.
- **Multi-agent v2 (owner-authorized, 2026-10-23):** Q89 phase 1 only — permissions first, inert.
  Phases 2-4 (tool implementation with dormant protection, the workflow/tracker change, and
  verification) belong to agent-sandbox-integration and are explicitly excluded here until
  separately authorized.

Every source change needs the deploy step: verifier mirror, then restart. Q27 waits on an owner
decision.

**Previous working order (owner, 2026-10-01; superseded by the phases above):** Q35 (Claude Code side, once scope is confirmed) can run any time; Q03 (R2-001 + cross-route stage resolution) → Q25
(handoff corrections) → Q26 (verifier prose coupling) → Q28 (deployment gating matrix) → the rest
in listed order; then, when the owner decides to upgrade: Q29 → Q30–Q33 delivered as the Q36 change set, built late on stacked branches (Q48, Q49) (one feature branch,
gated) → Q34. OpenCode V2 (Q40-Q47) follows the v4 upgrade. Every source change then needs the deploy step: verifier mirror, then restart. Q27
waits on an owner decision.

### Q01. Advisor layer close-out
- **Status:** IN PROGRESS. Registration fixes landed (`c01a73f`, `c5a326b`, `8570dc6`). Verifier
  ran on 2026-10-01: exit 0, "All checks passed (self-repairs applied)". It recovered the gentle-ai
  sync drift in the live `opencode.json` and `AGENTS.md` (Q24), with a backup in
  `backups/workflow-recovery/20261001T211934Z.384302/`. The live config now matches
  `global-config/`, and `gentle-orchestrator` again allows all five `advisor-*`.
- **Prerequisites:** none. Next host action: restart OpenCode (user). Until then the running
  servers (started 17:26 and 18:07) use the config they loaded at start.
- **Source:** `docs/TODO-HISTORY.md` "Advisor registration — verifier findings" and "PRIORITY
  CHANGE"; `docs/advisor/handoff-workflow-optimisation.md` "Where this slots in" 1.
- **Advisor dispatch verification PASSED (2026-10-01):** all five registered and dispatched on
  bounded tasks. Each read real files and cited line numbers. The tool surface was confirmed: the
  four workspace tools are present and every host-returning tool is absent. Findings → Q03, Q25,
  Q26, Q27 (`docs/TODO-HISTORY.md` "2026-10-01 — Advisor dispatch verification PASSED").
- **Restart observed 2026-10-02:** both OpenCode servers started at 05:46:18 and 05:46:42. The
  five-advisor dispatch verification already PASSED on 2026-10-01 (above).
- **Remaining:** run `verify-workflow.sh --behavioral` and a plain re-run (the
  cache-prune check was skipped because config was repaired). Then dispatch each of the five
  `advisor-*` agents once on a bounded task and confirm registration, successful reads, denied host
  mutations, and the assigned model observed.

### Q02. B0 coherence fixes, B1 mandatory advice policy, B2 advisory-evidence protocol
- **Status:** DONE (2026-10-01, review `review-bd57149caec073dc` approved). Tracker `odd/tasks/advice-mandate-and-queue.md` (T1 queue, T2
  `WORKFLOW.md`, T3 `docs/PLAN.md`, T4 ledgers).
- **Prerequisites:** none. The interim lane it defines relies on Q01 verification; until Q01 is
  done an unverified advisor is a missing opinion, not an approval.
- **Source:** `docs/advisor/handoff-workflow-optimisation.md` B0, B1, B2.
- **Description:** advice mandatory for every non-trivial change (interim pre-code lane:
  registered `advisor-*-pre` agents); external lane written as PLANNED; tracker protocol for
  advisory evidence.

### Q03. Guard review findings — fix unit (old item 12)
- **Status:** DONE (2026-10-03; guard fix unit landed). Follow-on review and runtime findings remain
  recorded in the tracker; this queue item covers the completed fix unit.
- **Prerequisites:** Q02 (advice record before coding).
- **Source:** `docs/TODO-HISTORY.md` "12. Guard review findings"; `odd/tasks/routing-guard-keys.md`
  review `review-84383b2e59dc8844`; `odd/tasks/guard-q03.md`.
- **Findings, in fix order.** R2-001 and the cross-route defect are both in the stage-resolution
  path; fix them together.
  - R2-001 (real defect, live): `allowsSpecialists` is inverted; fix first.
  - Cross-route stage satisfaction (advisor-design, 2026-10-01; latent): the stage-resolution path
    carries no route, so a stage is satisfied by a marker from any route.
    - Markers are written as `artifact-${stage.id}` (`systematic-routing-guard.ts:742`).
    - `hasRouteStageArtifactInAncestorChain` (`:281-301`) receives only `stageID`; `ROUTE_STAGES`'
      route key is never threaded in.
    - The legacy `artifact-odd-${stageID}` fallback applies to every route.
    - Verified latent, not live: the only legacy markers on disk are `artifact-odd-tracker` (23),
      and no `workflow-systematic` stage has id `tracker`. It becomes live once two routes share a
      stage id (risk for Q15 and Q18).
    - Fix: namespace markers by route, pass the route into the ancestor walk, and scope the legacy
      fallback to `workflow-odd-secure`.
  - R3-patch-stage-marker-gap: patch path extraction recognises only `odd/tasks/*.md`.
  - R3-child-marker-merge-excl: `COPYFILE_EXCL` stops a re-dispatched child updating a parent marker.
  - R3-marker-write-race and R4-001 (resilience): unawaited marker writes cause false warnings.
  - R3-specialist-warning-dedup: specialist warnings bypass `warningKey` deduplication.
  - R3-stage-logic-untested: add automated assertions for the stage table and its gates (the
    recurring finding across two reviews).
- **Absorbed from Q20 and Q21 (2026-10-02; same file and code path, so edit and review once):**
  - R3-console-warning-dedup (Q20): `host_review_start` `:778-783` and skill-load `:971-976` pass
    `warnConsole=true` unconditionally. Fix with R3-specialist-warning-dedup `:860`.
  - R3-copy-path-gap (Q20), now CONFIRMED OPEN.
    - `sandbox_copy_out` takes `{workerPath, hostTarget}` (agent-sandbox-integration
      `sandbox-tools.ts:478`).
    - The guard's `targetPath` (`:720-727`) prefers `workerPath`, so it checks the sandbox SOURCE
      rather than the host destination.
    - Fix: resolve `hostTarget` first for `sandbox_copy_out`. `sandbox_copy_in`
      (`{hostSource, workerPath}`) is already correct, because there `workerPath` is the
      destination.
    - Impact is low: copy-out targets are allowlisted external paths.
  - R3-unawaited-key-io (Q21): `void refreshWorkflowKeyActivity` `:718` and `void mintWorkflowKey`
    `:1003`. Fix with the marker-write race.
  - R4-001 nested inheritance (Q21).
    - `getWorkflowKeyStatus` `:430-499` and `refreshWorkflowKeyActivity` `:362-390` walk one
      parent level only.
    - It is live in practice: `subagent_depth` is 3 and `frontend-dev` may dispatch
      `frontend-apply`.
    - Walk the same 3-level ancestor chain as `hasRouteStageArtifactInAncestorChain`.
  - R3-missing-key-tests (Q21): key expiry, inheritance, parent refresh and bootstrap-ordering
    assertions, in the same test suite as the stage assertions.
- **Size:** expected above the ~400-line planning heuristic (advisory only), because it is one
  coherent fix unit for one file.

### Q04. Split `verify-workflow.sh` (old item 11)
- **Status:** READY. Ordered before B3 because B3 adds verifier checks.
- **Prerequisites:** none. Preserve check ordering, `fail` aggregation, TTY/`NO_COLOR` colour
  behaviour, the digest pinning contract and the `WORKFLOW_VERIFY_*` switches.
- **Source:** `docs/PLAN.md` "11. Split `verify-workflow.sh`"; `docs/TODO-HISTORY.md` item 11.
- **Description:** thin runner plus per-area check scripts (recommended) so each check is
  independently runnable and testable. Motivation is readability and testability, no longer
  tooling: targeted `sandbox_edit` works on the ~4,800-line file (`docs/TODO-HISTORY.md` "2026-10-01 — CORRECTION: sandbox_edit is targeted").

### Q05. Workflow policy (old item 5)
- **Status:** PLANNED.
- **Prerequisites:** Q02.
- **Source:** `docs/TODO-HISTORY.md` item 5; `docs/PLAN.md` Sequence 4; B0 fix 4 and the B1
  selection table in `docs/advisor/handoff-workflow-optimisation.md`.
- **Description:** policy across task classes and the ODD/SDD/advisor layers; the
  complexity-and-impact axis, where impact decides how much advice (B0 fix 4); the per-project
  impact-surface declaration delivered by the host; the heavier route always governs; the B1
  selection table.

### Q06. B3 — activate the external advisor lane
- **Status:** BLOCKED.
- **Prerequisites:** agent-sandbox-integration plan A slices A3, A5, A6 and A7/A8 installed
  (external); Q04.
- **Source:** `docs/advisor/handoff-workflow-optimisation.md` B3; `docs/advisor/interface-contract.md`.
- **Description:** grant the orchestrator `host_advisor_ask`, `host_advisor_get`,
  `host_advisor_list` in `global-config/opencode.json`, deny them to workers, `advisor-*` and
  relay lanes; add verifier checks (grants, no non-user launcher references `advisor-open`, and no
  agent or skill starts a review with `externalLenses: true`); flip the external lane from PLANNED to mandatory.
  Initial state on activation is `pair-default`: both hosts per non-trivial unit (owner,
  2026-10-01). Also activate `post-code-pair`: both hosts review the committed unit before
  `ce:review` and the native review. Prerequisite with the sandbox side: an advisory request
  kind for post-code review (proposed `advisory-review`; interim fallback `pre-code-advice` with
  `binding.step: "post-code"` and a commit snapshot). Verify that the broker's `group` gives first-pass independence for the pair. Pass condition:
  after host A submits, `host_advisor_get` on B's request (and B's advisor view) shows no
  `response` from A until B has submitted. Then both responses are visible, and each carries the
  same `group` and its own `resolvedHost`.

### Q07. B4 — routing guard integration (warn-only)
- **Status:** BLOCKED.
- **Prerequisites:** Q06; Q03 (R2-001 fixed before another stage relies on `allowsSpecialists`).
- **Source:** `docs/advisor/handoff-workflow-optimisation.md` B4.
- **Description:** optional `advice` stage satisfied only by an observed `host_advisor_get`
  result (`status: submitted`, matching `binding.task`) and, in the interim, an observed
  `advisor-*-pre` or `advisor-*-post` dispatch result. Owner decides whether the stage exists.
  (The external-lens capture warning was dropped: reviews stay on the in-OpenCode agents.)

### Q08. B5 — advisor handoff document
- **Status:** BLOCKED.
- **Prerequisites:** Q06.
- **Source:** `docs/advisor/handoff-workflow-optimisation.md` B5; `docs/ADVISOR-HANDOFF.md` "Requested".
- **Description:** answer the two "Requested" items with plan A's verified contracts
  (cross-project read-only inspection; workspace isolation) and describe the external lane next
  to the ten registered split advisors.

### Q09. Tracking contract in the recipe (old item 6)
- **Status:** PLANNED.
- **Prerequisites:** Q05 (same `WORKFLOW.md` policy area; avoids conflicting edits).
- **Source:** `docs/TODO-HISTORY.md` item 6; `docs/PLAN.md` "Tracking contract".
- **Description:** state in `WORKFLOW.md` that the orchestrator maintains this file, the plan and
  an in-agent list; updating them gates starting a NEW unit; a unit paused awaiting user input
  does not block.

### Q10. Recipe drift and gaps (old item 7), one unit per bullet
- **Source:** `docs/TODO-HISTORY.md` item 7.
- **Q10.1 Systematic version drift.** Status: DONE (2026-10-01). Both `global-config/opencode.json`
  and `~/.config/opencode/opencode.json` pin `@fro.bot/systematic@3.21.0`; the 3.21.0 package still
  ships the `screen`/`prepare`/`merge`/`finalize` pipeline (`skills/ce-review/references/
  pipeline-invocation.md`) and the four guard reason codes. `WORKFLOW.md` wording updated to
  "3.18.4+ (verified in the installed 3.21.0)".
- **Q10.2 Documentation class review option.** Status: PLANNED. Prerequisites: Q05. The
  documentation class has no mandated review option; `document-review` is the candidate.
- **Q10.3 Global tooling adapter and stage coverage.** Status: PLANNED. Prerequisites: Q03.
  Global tooling has no adapter skill and no stage coverage, so the guard cannot see it.
- **Q10.4 `ce:review` helper pipeline needs a sandbox worker.** Status: PLANNED. Prerequisites:
  Q12. The read path re-probe passed on 2026-10-01; re-assess whether the helper pipeline now
  runs once Q12 records the revised worker rules.

### Q11. Emergency fix route (old item 9)
- **Status:** PLANNED.
- **Prerequisites:** Q05 (the open question, a seventh task class versus an orthogonal session
  mode, is settled when the policy is defined).
- **Source:** `docs/PLAN.md` "Emergency fix route (design — to implement)"; `docs/TODO-HISTORY.md` item 9.
- **Description:** user-declared priority lane that parks the current unit, minimum ceremony,
  bounded diff, review debts recorded as named follow-ups.

### Q12. Worker contract — sandbox tool rules (old item 10, amended per B0 fix 1)
- **Status:** READY. The re-probe passed on 2026-10-01: `sandbox_read` succeeds at all sizes,
  and a very large file only hits the harness's limit on one tool response
  (`docs/TODO-HISTORY.md` "2026-10-01 — sandbox_read confirmed fixed").
- **Prerequisites:** none (the re-probe was met on 2026-10-01).
- **Source:** `docs/TODO-HISTORY.md` item 10 and "sandbox tooling fault fully characterised";
  `docs/PLAN.md` "Coding standard: prefer small files".
- **Description:** record the revised worker rules (`docs/TODO-HISTORY.md` "2026-10-01 — CORRECTION: sandbox_edit is targeted"):
  `sandbox_read` is fine to use (very large files may hit the harness's per-response limit; use
  a targeted read); `sandbox_edit` for targeted `oldString`/`newString` changes at any size up to
  the 512 KB cap; `sandbox_write` only for files the caller can produce whole; patches when a
  change spans many separate places. Verify with `sandbox_bash git diff` and treat a success
  return as unverified until readback. The file-mode defect is fixed (`docs/TODO-HISTORY.md` "2026-10-01 — mode-preservation defect fixed and verified"). The earlier "whole-body" rule is retracted. The original silent
  no-op is still UNEXPLAINED (open question). File-size discipline stays a coding standard.

### Q13. Cross-project items (old item 8) — agent-sandbox-integration
- **Status:** BLOCKED (external project).
- **Prerequisites:** delivery of these entries in agent-sandbox-integration's TODO, by name:
  Tier 2 items 7–8 (ledger appends); the allowlisted append operation; the ledger move out of
  git; the project-scoped signal channel; the install-vs-commit gap. Confirm each is delivered
  and installed here.
- **Source:** B0 fix 5 in `docs/advisor/handoff-workflow-optimisation.md`; `docs/TODO-HISTORY.md`
  item 8 and "Review state" (ledgers are shared git-tracked files).
- **File-mode defect: FIXED and verified (2026-10-01).** `sandbox_edit` now preserves the
  executable bit; `git diff` shows no mode change (`docs/TODO-HISTORY.md` "2026-10-01 — mode-preservation defect fixed and verified"). Drop it from the handoff's request list.
- **Note:** the host commit tool also rejects multi-line messages (`routing-guard-keys.md` Debt);
  the `ROUTED:` trailer sits on the subject line until that is fixed in the host tooling.

### Q14. Engram as the inter-agent communication channel (Magic Context stays main memory)
Owner direction (2026-10-01): Engram is a candidate channel for information that agents pass to
each other. Magic Context stays the main memory, including the ODD tracker mirror. Recorded in
`docs/PLAN.md` "Memory and inter-agent communication".

- **Q14a. Evaluation (B6, report only).** Status: PLANNED. Prerequisites: none.
  - Assess scoped, per-request access to handoff summaries and evidence references:
    - project labels are not access control;
    - unrelated memories must not be exposed;
    - independent first-pass reviewers and advisors must not see each other's conclusions
      before they submit.
  - Also define the channel semantics: what a message is (sender, recipient or topic, task
    binding, evidence refs), its lifetime, and how it is read.
  - Source: `docs/advisor/handoff-workflow-optimisation.md` B6.
- **Q14b. Adoption.** Status: PLANNED. Prerequisites: Q14a; the owner's adoption decision on
  Q14a's report; Q04 preferred (it adds verifier checks).
  - Add the `engram` MCP to the canonical `global-config/opencode.json`. Today the verifier strips
    it, because gentle-ai sync adds `engram mcp --tools=agent` and the canonical config lacks it
    (observed 2026-10-01).
  - Teach the verifier the entry.
  - Grant the `engram` tools per agent, with first-pass isolation kept.
  - Write the `WORKFLOW.md` policy with clear direction:
    - Engram carries only inter-agent communication (handoffs, evidence references, requests and
      answers between agents);
    - Magic Context stays the main memory and the ODD mirror;
    - nothing is duplicated between them;
    - an Engram message is evidence, never approval.
  - Replace the current "do not invoke `mem_*`" rule with this scoped rule.

### Q15. Routing guard T7 — `workflow-sdd-secure` phase-agent gating
- **Status:** CLOSED — obsolete on v4. It was obsolete-by-absence: the guard's `ROUTE_STAGES` only ever held `workflow-odd-secure` and `workflow-systematic` (`global-config/plugins/lib/routing-guard-helpers.ts:67-103`), so the SDD phase-agent gating was never implemented (see Q33/Q65).
- **Prerequisites:** Q03.
- **Source:** `odd/tasks/routing-guard-keys.md` T7c "Implementation order" 3.

### Q16. Routing guard T7 — review-due marker from the assessment output
- **Status:** PLANNED.
- **Prerequisites:** Q03.
- **Source:** `odd/tasks/routing-guard-keys.md` T7c "Implementation order" 4 and "Review stage semantics".

### Q17. Routing guard T7 — durable project-scoped signal and project-aware markers
- **Status:** BLOCKED.
- **Prerequisites:** Q13 (project-scoped signal channel and ledger move, agent-sandbox-integration).
- **Source:** `odd/tasks/routing-guard-keys.md` T7c "Implementation order" 5 and Debt
  (project-blindness: no trustworthy session-project source).

### Q18. Routing guard T8 — bug-fix route with its own stages and no ODD tracker
- **Status:** PLANNED.
- **Prerequisites:** Q03, Q05.
- **Source:** `odd/tasks/routing-guard-keys.md` T8 and T7c stage tables (reproduce-bug, `ce:work`, `ce:review`).

### Q19. Routing guard — learnings stage
- **Status:** PARKED.
- **Prerequisites:** the post-archive condition must become observable (external condition).
- **Source:** `odd/tasks/routing-guard-keys.md` T7c "Implementation order" 2.

### Q20. Routing guard — advisory findings of `review-10d26170c9d40efc` not covered by Q03
- **Status:** PLANNED. Verified 2026-10-01 against `systematic-routing-guard.ts` at `069cc4b` (no
  later guard commit fixes any of them):
  - R2-003: undetermined. Only its id and line are recorded; the review text is needed to act.
  - R3-child-regex-format: OPEN (`:904`, strict `id="(ses_...)"` match).
  - R3-console-warning-dedup: MOVED to Q03 (2026-10-02).
  - R3-copy-path-gap: MOVED to Q03, and confirmed OPEN (2026-10-02): copy-out checks
    `workerPath` (the source), not `hostTarget`.
  - R3-systematic-apply-marker-gap: OPEN. `sandbox_apply` is excluded from `pathKnown`, and
    `patchTrackerPath` at `:805` is dead code.
  - R4-001 (verifier factory): treated as OPEN per the tracker; the verifier code was not read.
- **Prerequisites:** Q03.
- **Source:** `odd/tasks/routing-guard-keys.md` review `review-10d26170c9d40efc`.
- **Findings remaining here:** R2-003 (tracker wording, `routing-guard-keys.md:133`);
  R3-child-regex-format; R3-systematic-apply-marker-gap; R4-001
  (verifier, partially fixed: factory required but not invoked).

### Q21. Routing guard — advisory follow-ups of `review-16c862492747259a` not covered by Q03
- **Status:** MOVED to Q03 (2026-10-02). All three were verified OPEN on 2026-10-01 at `069cc4b`
  and are now fixed as part of Q03. Kept here for traceability:
  - R3-missing-key-tests: no guard test file exists. Handle it in the same test unit as Q03's
    stage assertions.
  - R3-unawaited-key-io: `void refreshWorkflowKeyActivity` `:718` and `void mintWorkflowKey`
    `:1003`. The marker writes `:740/908/985` are Q03's race.
  - R4-001: `getWorkflowKeyStatus` `:430-499` and `refreshWorkflowKeyActivity` `:362-390` go
    only one parent level, while marker lookup walks 3 levels (`:281-318`).
- **Prerequisites:** Q03 (R3-unawaited-key-io overlaps the Q03 marker-write race; handle together).
- **Source:** `odd/tasks/routing-guard-keys.md` "Advisory follow-ups".
- **Findings:** R3-missing-key-tests (assertions for key expiry, inheritance, parent refresh,
  bootstrap ordering); R3-unawaited-key-io; R4-001 (nested sessions do not inherit through an
  already-inherited parent). R3-sandbox-catchall was a false positive; R3-odd-marker-gap and
  R3-child-session-regex were fixed by T7a-fix.

### Q22. Disposition of open review lineage `review-17a7dab1e332596a`
- **Status:** READY. Lineage is in `correction_required`, superseded by the approved lineage
  `review-16c862492747259a`; its disposition is unresolved.
- **Prerequisites:** none. The owner decides the disposition through the gentle-ai lifecycle.
- **Source:** `odd/tasks/routing-guard-keys.md` Debt.

### Q23. Magic Context mirror flattens tracker newlines
- **Status:** PLANNED.
- **Prerequisites:** none.
- **Source:** `odd/tasks/routing-guard-keys.md` Debt.
- **Description:** the mirror stores the tracker body newline-flattened, so a verbatim write-back
  collapses markdown structure; restore from git and re-apply sections as real multi-line text.

### Q24. gentle-ai sync overwrites the live OpenCode config
- **Status:** READY.
- **Prerequisites:** none. Coordinate with Q14b (part of the sync diff is the `engram` MCP).
- **Source:** observation 2026-10-01, Q01.
- **Description:** a `gentle-ai sync` at 20:28 on 2026-10-01 rewrote `~/.config/opencode/opencode.json`
  and `AGENTS.md`. It:
  - reset `gentle-orchestrator`'s `permission.task` to `{"*": "deny"}`, dropping the `advisor-*`,
    `asi-review-*` and Systematic specialists;
  - reverted 12 agent models (e.g. `review-validator` back to `glm-5.2`);
  - dropped search-contract prompts and `github_ro`;
  - added the `sdd-*-local` agents and the `engram` MCP.

  The verifier recovers all of this, but only when it is run; a restart before it would have
  loaded the drift. Make it detectable or self-correcting: run the verifier after every
  gentle-ai sync (`WORKFLOW.md` "After Updates"), and/or have the health plugin flag drift at
  OpenCode start.

### Q25. `docs/ADVISOR-HANDOFF.md` corrections
- **Status:** READY.
- **Prerequisites:** none. Small and factual. It matters because the sandbox project builds against
  this document.
- **Source:** advisor-integration (`docs/TODO-HISTORY.md` "2026-10-01 — Advisor dispatch verification PASSED").
- **Description:**
  - `sandbox_finish` and `sandbox_apply` are not registered on the advisor surface; they are not
    permission-denied. Say so.
  - State that the read tools require an active worker.
  - Replace "cannot return results": `sandbox_bash` output and `sandbox_diff` return in-tool; only
    the persisted export needs `finish`.
  - Keep the isolation caveat (advisor-security): the boundary is designed in, not proven, until
    the isolation guarantees are verified.
  - Drop the file-mode defect if listed (fixed).

### Q26. Verifier prose coupling
- **Status:** IN PROGRESS — T1 (docs anchors) DONE-AT-SOURCE (commit `65beb19`, 31 anchor blocks); T2 (verifier checker + re-pin) pending.
- **Deferred (T2):** the `AGENTS.md` `## Secure workflow router (MANDATORY)` block is not anchored in T1 — its bytes must equal the verifier heredoc (`verify-workflow.sh:1305-1319`, byte-compared at `:4453-4472`), so anchoring it requires a verifier edit + re-pin.
- **Prerequisites:** none. Do it with or before Q04; the split must preserve whatever contract
  replaces the literals.
- **Source:** advisor-maintainability (`docs/TODO-HISTORY.md` "2026-10-01 — Advisor dispatch verification PASSED").
- **Description:**
  - The section-7 region carries on the order of ~170 hardcoded grep predicates over prose in
    `WORKFLOW.md`/`AGENTS.md`/skill references; if a literal drifts the verifier fails, so routine
    doc edits break it.
  - Replace prose matching with stable machine markers (e.g. `<!-- workflow:anchor ... -->`) or a
    single declared anchor list, so wording can change freely.
  - Inputs for Q04: 5,008 lines and only 14 functions, all ending by line 1,276; the rest is one
    top-level body. The 16 numbered section markers are the natural seams, and section numbers are
    cited externally, so numbering and order are preserved. Any split re-pins the digest in the
    same change.

### Q27. Advisor worker lifecycle — owner decision
- **Status:** BLOCKED on an owner decision.
- **Prerequisites:** owner decides who owns export and teardown of an advisor's workspace.
- **Source:** advisor-integration (`docs/TODO-HISTORY.md` "2026-10-01 — Advisor dispatch verification PASSED"); design gap introduced by the workspace-tool split
  (`8570dc6`).
- **Description:** the granted mutation tools activate a single-lifecycle worker that an advisor
  can never finish or tear down: it is mutable but cannot be exported. Options to decide between:
  - the orchestrator tears down (discards) every advisor worker after the advice is recorded;
  - a narrow advisor-side `sandbox_discard` grant;
  - withdraw the mutation tools and route all execution through structured test requests.
  Record the choice in `WORKFLOW.md` and `docs/ADVISOR-HANDOFF.md`.

### Q28. Deployment gating matrix
- **Status:** READY.
- **Prerequisites:** none for the matrix itself. Implementing the gates depends on Q03, Q07, Q26.
- **Source:** owner requirement, 2026-10-01: "All changes to workflow will ultimately have to be
  correctly gated when deployed." `docs/PLAN.md` Constraints.
- **Description:** a table mapping every workflow rule to its enforcement point (routing-guard
  stage or check, verifier check, native gentle-ai gate) and a status: enforced, planned, or
  advisory-only (with the reason). At minimum these rules:
  - pre-code advice record (interim `advisor-*-pre` and `pair-default`);
  - post-code advisory review (interim `advisor-*-post` when no `ce:review`; `post-code-pair`).
    Concrete check for the interim branch: after a non-trivial unit's work-unit commit, before
    the native review starts, warn if neither a `ce-review` skill marker nor an observed
    `advisor-*-post` dispatch with step `post-code` exists for the session. When a `ce-review`
    marker exists, no advisor dispatch is required. Implementation is a guard stage (with Q03
    namespacing and Q07). Until then the rule is advisory-only, recorded here as such;
  - `ce:review` before the native review where owed;
  - native review lanes only `asi-review-*`, and no `externalLenses: true`;
  - ODD tracker before the first source write;
  - external sessions only user-opened;
  - Engram channel scope (once adopted).

  Each gap becomes a named follow-up item in this file.

### Q50. Propose the interface-contract amendment to agent-sandbox-integration
- **Status:** READY.
- **Prerequisites:** none. The contract changes only by agreement of both sides
  (`docs/advisor/interface-contract.md` intro).
- **Source:** external review, 2026-10-02 (finding 4); owner decisions recorded in the handoff
  amendments.
- **Description:** send agent-sandbox-integration a proposed contract revision that:
  - withdraws the `review-lens` request kind, §4 external-lens lineages,
    `host_review_start externalLenses` and `host_review_capture_result inputFromAdvisorResponse`
    from this side's needs;
  - adds an `advisory-review` request kind for the post-code advisory review (same mechanics as
    `pre-code-advice`, with a commit or `resultRef` snapshot);
  - records `pair-default`/`post-code-pair` group use.
  Until it is agreed, this repo's copy stays as published, and the handoff amendments state the
  divergence.
- **Incident 2026-10-02 11:28:** an external sync overwrote both `docs/advisor/` files here. It
  deleted the three owner amendments, and added the external-lens capture path as "implemented in
  `broker/src/advisor-relay.ts`, verified live". Owner resolution:
  - the amendments are restored;
  - the contract keeps the sandbox side's implementation text, annotated "not used by
    workflow_optimisation".
  Raise it in the Q50 proposal, and ask agent-sandbox-integration not to sync over this repo's
  copies. These files diverge by design until the contract is agreed.

### Q51. Scripted advisor dispatch is unreliable
- **Status:** READY.
- **Prerequisites:** none.
- **Source:** `odd/tasks/auto-update-partial-install.md` T0 (2026-10-02).
- **Description:**
  - `opencode run --agent advisor-*` silently falls back to the default primary agent ("is a
    subagent, not a primary agent"). The advisor never receives the brief.
  - A run that asks `gentle-orchestrator` to dispatch the advisor by Task stalled at instance
    `init` for 900 s, with no session created. A 4 s run just before it had completed. The cause
    is unknown.
  - Needed for any automated advice record, including the verifier's.
  - Investigate with `--print-logs --log-level DEBUG`, and with concurrent and sequential runs.
  - Until fixed, the advice step is dispatched from the TUI.

### Q52. Auto-update partial-install follow-ups
- **Status:** PLANNED.
- **Prerequisites:** Q04 for T4.
- **Source:** `odd/tasks/auto-update-partial-install.md` (DONE except T4); reviews
  `review-f0d7d1d1572a4195` and the follow-up review.
- **Description:**
  - T4: shell-level integration test for the verifier's §2c mapping and the pin-preservation
    fallback.
  - Comment at `verify-workflow.sh` §2c noting that the quiet period comes from the helper's
    `QUIET_PERIOD_SECONDS`.
  - Plugin fork: the lock is not atomic (`lock.ts` read-then-write), and the history log's
    "Updated X" regex never matches. Both are owned by the local fork.

## Project-manager layer (owner decision 2026-10-04)

Source for the whole group: `docs/handoffs/2026-10-04-pm-layer-workflow-optimisation.md`
(Handover B: design, verified facts, acceptance per item). Tracker: `odd/tasks/pm-layer.md`.
One PM subagent session per work unit; the orchestrator dispatches only `explore` and `pm-*`.

### Q53. PM layer: probe (go/no-go)
- **Status:** DONE. The eight-item probe ran: items 1, 2, 3, 5, 6, 7 and 8 were observed and
  passing; item 4 was unobserved and deferred to Q55. Evidence: `odd/tasks/pm-layer.md` and
  `ROUTER-LOG.md`.
- **Prerequisites:** none.
- **Description:** temporary `pm-probe` subagent and `subagent_depth` 4; record the eight
  observations listed in Handover B (nesting, key mint and inheritance, subagent `question`,
  permission prompts, `task_id` resume, key state after expiry, `ce:plan` load, `ctx_memory`).

### Q54. PM layer: sandbox allowlist (cross-project)
- **Status:** DONE as a report (owner-relayed findings plus live smoke corrections, 2026-10-07);
  check (c), `pm-probe` removal, now PASSES in the deployment verification after commit `ae24a7f`.
- **Prerequisites:** Handover A passed to agent-sandbox-integration and reported installed.
- **Description:** The broker-side grant is every `HOST_MUTATION_OPERATIONS` entry except
  `registerProject`, but the reachable PM surface is the intersection of that grant with tools
  registered to the session. A live `pm-odd` session held `host_git_commit`, `host_review_start`,
  `host_review_acknowledge_approved`, `host_review_capture_result`, `host_review_capture_refuter`,
  `host_review_capture_validation`, `host_review_capture_correction_plan`,
  `host_review_capture_unachievable`, `host_review_recover`, and `host_review_validate`. It did not
  hold `host_git_push`, `host_gh_issue_create`, `host_plan_append`, or
  `host_sandbox_result_install`; this change adds `host_git_push` and
  `host_sandbox_result_install`, while `host_gh_issue_create` and `host_plan_append` remain absent
  by design. All five identities are refused by sandbox read/list/grep/diff and mutation tools, so
  PMs do not enter the sandbox. Other owner-relayed answers remain: (1) `task_id` resume YES,
  mechanism unobserved; (2) depth-1 relay REACHABLE, but full context delivery is unverified; (3) PM
  surface includes host reads, AFT, CodeGraph, AST-grep, context and read/glob, with no host bash or
  sandbox tools; (4) no depth-sensitive behavior was reported, and raising depth 3→4 should not
  affect binding, worker initialization or session-root relay resolution.
- **Live smoke correction (observed after owner restart):**
  `host_git_commit({"message":"test: identity probe"})` returned `cannot commit: no applied B→C
  result for this session`; `host_review_start({})` returned `the candidate has no pending changes;
  already-committed work can be reviewed by rerunning review start with --base-ref <commit>`. No
  `HOST_MUTATION_*` token appeared. `host_register_project` is absent from the registered tool set,
  so its deny path is unobservable for `pm-odd` (tool-registration-layer control, not broker
  refusal). Identity binding is confirmed live for permitted operations; the deny path is
  unobservable, not refuted. The security advisor's author→commit→review→approve loop is confirmed
  reachable: commit, review start, capture and acknowledge are all in the observed tool set.
- **Removal correction — check (c) FAILED:** A Task dispatch to `pm-probe` still succeeded, with
  its Q53 probe brief. The canonical→live mirror had not run since commit `8d40f97`, so
  `~/.config/opencode/opencode.json` still defined the agent; restart alone applies nothing. The
  correct deployment sequence is verifier mirror → restart. Positively, the still-live `pm-probe`
  refused an instruction shaped like a liveness beacon. Required services are
  `sandbox-broker.service` and `secure-opencode.service`. Related: Q50 (interface contract).
- **Deployment verification (observed after commit `ae24a7f`):** Check (c) PASSES. A Task dispatch
  to `pm-probe` returned `Unknown agent type: pm-probe is not a valid agent type`; the removal is
  live. The canonical→live deployment chain is confirmed end to end: commit → verifier mirror →
  restart → live. A restart alone applies nothing; this is the observation that proved the order.
  `pm-odd`'s live tool set was verified at 12 host-mutation tools: `host_git_commit`,
  `host_git_push`, `host_review_acknowledge_approved`, `host_review_capture_correction_plan`,
  `host_review_capture_refuter`, `host_review_capture_result`,
  `host_review_capture_unachievable`, `host_review_capture_validation`, `host_review_recover`,
  `host_review_start`, `host_review_validate`, and `host_sandbox_result_install`.
  `host_gh_issue_create` and `host_plan_append` are absent by design. Resuming the earlier
  `pm-odd` session retained its prior conversation, a second independent observation of `task_id`
  resume behaviour (the first was the synthetic probe). In this unit, `pm-sdd` was extended to the
  same host-mutation set, retaining `host_sdd_archive_compose` as its route-specific extra. This
  extension is superseded by Q65's retirement of `pm-sdd`.
- **Observed removal-check reconciliation (2026-10-08):** check (c) PASSED by the failed dispatch
  recorded above. Check (b) is PARTIALLY PASSED: installed `/home/james/.config/opencode/plugins/
  sandbox-tools.ts`, `READ_ONLY_AGENTS` lines 64–69, lists `gentle-orchestrator`, `pm-odd`,
  `pm-systematic`, and `pm-sdd`, with no `pm-probe`; the separate broker identity list in
  `agent-sandbox-integration` is unreachable from this workspace (the `~/ai-workspace` listing
  was permission-denied), so that half is UNVERIFIABLE here. Check (a) is PARTIALLY PASSED: live
  `pm-odd` returned business errors for `host_git_commit` (`cannot commit: no applied B→C result
  for this session`) and `host_review_start` (`the candidate has no pending changes…`), with no
  `HOST_MUTATION_*` token; authorization passed for those permitted calls. The deny path is
  unobservable because `host_register_project` is not registered, which is a tool-registration
  control, not a broker refusal. Full detail and the confirmed review boundary are in
  `odd/tasks/pm-layer.md`.

### Q55. PM layer: handoff contract, agents and writer
- **Status:** IN PROGRESS. Implementation landed in commit `8980254`. The contract-completeness and
  unit-start branch-verification text landed in `docs/specs/pm-handoff.md` in commit `551b7d3`
  (brief-in `feature_branch` field at `docs/specs/pm-handoff.md:7`; branch criterion/mechanism/PASS/
  BLOCKED hazards at `:15`, ordered unit-start step at `:19`, and deterministic missing-artifact /
  boundary / prerequisite BLOCKED procedures at `:28`). Q55's post-code advisory review is DONE;
  findings and open decisions are recorded in `odd/tasks/pm-layer.md`. This closes the contract-text
  gap, not the pilot: the later `pm-odd` bootstrap run, independent relay-delivery proof, remaining
  smoke/deployment steps, and ten-unit pilot remain open under Q56.
- **Prerequisites:** Q53.
- **Description:** `docs/specs/pm-handoff.md`; `pm-odd`, `pm-systematic`, `pm-sdd` and
  `odd-apply` in `global-config/opencode.json`; PM prompts within budget; guard data
  (`SPECIALIST_WRITERS`, `pm-` as coordinator) with tests first. Q54's live `pm-probe` removal
  verification now passes check (c); see Q54. The post-code advisory review is DONE; see
  `odd/tasks/pm-layer.md`. Route-specific classification is verified, but hard rejection is not (the
  guard is warning-only).

### Q56. PM layer: pilot `pm-odd`
- **Status:** BLOCKED on Q55's remaining acceptance work, deployment, and owner disposition of the
  explicitly limited removal evidence.
- **Prerequisites:** Q55 post-code advisory review is done; its other acceptance items remain open.
  The verifier mirror and restarts of `sandbox-broker.service` and `secure-opencode.service` are
  recorded as completed for the existing smoke/removal observations. In one `pm-odd` session,
  retain `host_register_project` as absent from the registered tool set (registration-layer
  control, not broker refusal) and the permitted-operation smoke evidence. Removal check (c)
  PASSED: dispatch to `pm-probe` failed with `Unknown agent type: pm-probe is not a valid agent
  type`. Checks (a) and (b) are PARTIALLY PASSED, not outstanding wholesale: permitted calls
  demonstrate authorization passed and the installed `READ_ONLY_AGENTS` list omits `pm-probe`;
  the broker deny path is unobservable because `host_register_project` is not registered, and the
  broker's separate identity list is unverifiable from this workspace. Preserve those caveats and
  do not label the three-check set fully passed. Evidence: `odd/tasks/pm-layer.md`, “Q58 bootstrap
  prerequisites — observed evidence”.
- **Description:** run global-tooling units here through `pm-odd`, with
  `gentle-orchestrator-legacy` kept selectable. Ten consecutive units without route escape. Q58
  may run through `pm-odd` as the pilot's bootstrap unit only; it does not count toward the ten-unit
  criterion because its route-key enforcement is not yet live during its own execution. Start the
  count only after Q58's enforcement is live. Q58's review must be driven independently by the
  orchestrator or another coordinator, not by the implementing `pm-odd` session: the unit that
  establishes review independence must not itself be reviewed without it.
- **Pilot smoke (2026-10-19):** one standalone tiny-fix unit completed end to end through `pm-odd` and returned `DONE`; implementation `47781da`, metadata `a104abc`; both assessments passive; orchestrator readback matched. This does not start the ten-unit count, which begins only after Q58's enforcement is live. Q59's implementation is not a Q56 pilot unit and earns no pilot credit; no new pilot validation is inferred.
- **Counted unit 1/10 (2026-10-22):** Q85 ce:review pipeline host permissions — verified through pm-odd; route workflow-odd-secure; no route escape; source already complete; metadata commit 916a4f5e3291f42507bfb47b429bcea5c6d65e4c; assessment passive (3 paths / 33 lines, review_due=false). Owner count authorization on 2026-10-22 supersedes the earlier blocked-count timing for this unit; it does not assert that Q58 enforcement or broker runtime registration is live.
- **Counted unit 2/10 (2026-10-22):** Q85a PM unit-start deterministic anchor — verified through pm-odd; route workflow-odd-secure; no route escape; source already complete; metadata commit 1ab7647be851e2930c23023c87daa42564086066; assessment passive (4 paths / 29 lines, review_due=false).
- Counted unit 3/10 (2026-10-22): Q79 D/E mirror-write ownership — verified through pm-odd; route workflow-odd-secure; no route escape; source verified; metadata commit PENDING-COMMIT.
- Counted unit 4/10 (2026-10-23): Q86 ce:review 16-parameter contract revision — SOURCE COMPLETE; route workflow-odd-secure; PM-dispatched `odd-apply`; source commit `83bdeeab3d9f3bf430c54d4ffbb00e097e1856cd`; PM accepted PM01–PM05; correction_rounds_used 1; source assessment medium / `under_budget` / `review_due=false` with boundary `77b4df8` retained; metadata closure PENDING-PM-COMMIT/assessment. Reviewer delivery and helper byte custody BOTH UNRESOLVED; ASTRA caller aliases OPEN. Process exceptions: orchestrator-run pre-advice `ses_e98032642ffeiI5jf9yzRYlKki` and post-code `ses_e97ed133effeHLcEpI7U9gAhhl` are not PM checks; no PM pre-advice compliance or clean/no-process-defect claim. No route escape claimed.
- **Counted unit 5/10 (2026-10-23):** Q89 multi-agent v2 phase 1 planning — route
  workflow-odd-secure; PM-dispatched `odd-apply`; planning artifact committed as
  `28d4a43` and assessed medium/`under_budget`; count
  explicitly authorized by the dispatch brief even though earlier planning units were not counted;
  no implementation, deployment, or native review claimed.

### Q57. PM layer: slim the orchestrator
- **Status:** PLANNED.
- **Prerequisites:** Q56. Coordinate with Q29c (user-owned orchestrator prompt).
- **Cap status (owner 2026-10-19):** the numeric orchestrator cap is DEFERRED to this item; the
  "about 8,000 characters" below is a planning target, not an enforced threshold. No threshold is
  invented here and `docs/PLAN.md` is unchanged.
- **Description:** forward contract (Q90 decision, 2026-10-23): `permission.task` routes to PM
  and Tiny only; the six `asi-review-*` lanes and `advisor-*` run on the PM; the orchestrator does
  assessment/consent/acknowledgement only and is not a lens. Host mutations are removed except
  `host_register_project`. Split `global-config/AGENTS.md`; update `WORKFLOW.md`,
  `workflow-route` and the adapters. The earlier "deny by default with `explore` and `pm-*`
  allowed" draft is SUPERSEDED by Q90; the numeric cap remains DEFERRED per Status above.

### Q58. PM layer: guard ordering
- **Status:** SLICES COMPLETE AND SHIPPED; the `pm-odd` bootstrap run executed 2026-10-19 as `q58-bootstrap-advisory-clearance-u1` (task `q58-bootstrap`) and addressed the five advisory findings. Slice 1: `7a427d7`; direct-writer-dispatch warning: `d25228b`; advice-before-writer stage: `4b63481`; supporting routing-gate and breadcrumb fixes: `9c215b1`. Implementation commit `b3fba8dd6666af98cf6ba00d61eac425747b9f20` on `chore/q72-t1b-tiny-fix-contract` (six allowed paths, 66 insertions / 8 deletions; owner-supplied readback, not this writer's execution). The exact PM host assessment after that commit returned status 0 with empty stderr: `{"schema":"gentle-ai.review-assessment/v1","risk":"medium","reasons":[{"code":"executable_change","path":"tests/test_pm_handoff_spec.py"}],"changed_paths":6,"changed_lines":74,"candidate":{"kind":"base-diff","base_ref":"deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422","consumed":false},"review_due":false,"review_due_reason":"under_budget"}`. No native review is DUE; the reviewed boundary remains `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422`, and the medium slice remains accumulated/pending — NOT passive, approved, or consumed; the external orchestrator drives any future native review. Independent relay-delivery proof remains UNVERIFIED and the bootstrap unit does not count toward the ten-unit pilot. Observed historical closure, scoped to metadata commit `905e347bd2dc25d814e576737bd9a53e1b948c1a` only and not a final result for any later correction commit: the final committed-candidate assessment was `medium` / `under_budget` / `review_due=false` with `changed_paths=6`, `changed_lines=94`, and `consumed=false`; the reviewed boundary was retained at `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422`; the medium slice remains accumulated/pending with no native review due; independent advisor Task `ses_eaa48d2e6ffeXfsGxfQXo4HFLk` inspected the METADATA candidate and returned no blockers before that metadata commit; the metadata receipt was 34 authored changed lines / 28470 bytes with no generated or binary paths; no approval claimed.
- **Bootstrap run executed 2026-10-19:** `q58-bootstrap-advisory-clearance-u1` (task `q58-bootstrap`) cleared the five advisory contract/ledger findings in `docs/specs/pm-handoff.md`, `tests/test_tiny_fix_route.py`, `tests/test_pm_handoff_spec.py`, `ROUTER-LOG.md`, and this item; the dispositions and observed check outputs are in `odd/tasks/pm-layer.md`. No native review is due (`under_budget`); any future native review is external to the implementing writer, independent relay-delivery proof remains UNVERIFIED, and this bootstrap unit does not count toward the ten-unit pilot.
- **Prerequisites:** Q55 and Q56 pilot evidence/caveats remain recorded above. The Q58 implementation, reviewability, and slice evidence are in `odd/tasks/pm-layer.md`. Q58 feeds Q28 (gating matrix).
- **Description:** Slice 1 adds a warning-only check that PM coordinators hold their own route's
  adapter key before gated host mutations and any `host_review_*` call; inherited and wrong-route
  keys do not satisfy it. The binding premise was verified live with a temporary `chat.message`
  probe, which has since been removed. The completed remaining slices warn when `gentle-orchestrator` dispatches a writing specialist directly instead of through its route coordinator, and when a writer is dispatched before the advice record exists. The prior commit-before-review half is superseded by the pre-commit advisory rule recorded in the workflow formalisation. Commits `9c215b1`, `d25228b`, and `4b63481` are recorded in `odd/tasks/pm-layer.md`; the routing-guard suite reports 94 passed / 0 failed (previously 80 passed). The advice-record convention is documented in `WORKFLOW.md` and the tracker.
  **Owner decision: enforced independence.** The coordinating PM cannot dispatch relay lenses;
  review is driven from outside the PM session. Q58's route-key rule is necessary but not
  sufficient: it verifies that the PM loaded its route skill, not that the reviewer differs from
  the author. Require relay-delivery proof from a dispatch outside the coordinating PM session,
  with a genuine provider-issued binding; Q54 showed reachability only, not delivery. The PM itself
  must not dispatch or prove its own relay delivery. The `pm-odd` bootstrap run executed 2026-10-19
  (see Status above), and the independent relay-delivery proof remains UNVERIFIED. Q58 ran through
  `pm-odd` as Q56's bootstrap unit only (see Q56); its review must be driven independently, not by
  the implementing `pm-odd` session.
- **Open question — undecided:** each PM still holds `host_review_start` and review lifecycle
  tools, so a PM can start a review it cannot complete without relay lanes. Options:
  (a) the PM keeps `host_review_start` and another actor drives the lens; or
  (b) review start also leaves the PM session. Do not resolve this in Q58.
- **Supersession (2026-10-23, Q90 decision 1):** the enforced-independence requirement and the
  open `host_review_start` question are RESOLVED for the forward contract: the PM runs the six
  native `asi-review-*` lanes and keeps the review lifecycle, while the lenses are independently
  driven outside the implementing writer, not outside the PM. The historical text above is
  retained unchanged as the record at its date.
- **Open external/upstream item — review relay deadline:** two review lenses expired with `reviewer_relay_deadline_expired: review relay deadline of 600000 ms expired` despite taking 16–19 minutes. The deadline is `RELAY_DEADLINE_MS = 600_000` at `~/.config/opencode/plugins/lib/reviewer-relay-core.ts:112`, overridable through `config.deadlineMs` at `:778` and `:1294`. That file is not tracked here (this repository tracks only `global-config/plugins/lib/routing-guard-helpers.ts`), and nothing in this repository sets the deadline. The fix belongs to the external plugin owner, not local Q58 work; details are in `odd/tasks/pm-layer.md`. New data point (2026-10-14): a resilience review lens needed 26m18s against the 600000 ms deadline; the owner permanently increased the relay timeout, and because that file is not tracked here the fix lives with the external plugin owner.

### Q59. PM layer: verifier
- **Status:** **DONE (source + metadata); activation/deploy UNVERIFIED.** Implementation
  `q59-pm-verifier-impl-u1` is COMPLETE and SOURCE-COMMITTED in five commits on `chore/q72-t1b-tiny-fix-contract` at
  `41fbe77a7ba3214c340e610df935ff7fb73b62c0`: `58b1c8c` (S1), `44f22bd` (S2a), `4677915` (S2b),
  `db85a6b` (S2c), `41fbe77` (S2d/e). Each source commit has an owner-relayed native review
  APPROVED + ACKNOWLEDGED with authority burned: `review-87858bd36a02d266` (S1 + S2a),
  `review-028c45784dd7c5b9` (S2b), `review-5bea3eacbe067a77` (S2c), `review-8bf653955b7f58f5`
  (S2d/e). These are owner-supplied acknowledgements, not worker-produced evidence; no
  acknowledgement token was independently read and no acknowledged source candidate is
  re-reviewed. Observed before this M1 metadata edit: focused 7 Python modules 102 PASS; full
  Python 228 PASS with no skips; routing-guard 104 pass / 0 fail / 254 expectations; direct JS
  harness PASS; `bash -n`, `git diff --check` and pin regex PASS; 103 same-predicate controls
  (91 rejections + 12 accepted); all 43 prompt metrics asserted (orchestrator 57167, PMs 2968 and
  2982; PM cap <6000; numeric orchestrator cap DEFERRED to Q57). Current pin
  `28ff39379aee7460bce784386e62c83bf5f51aea2b93074e2f35230fa299e7ad`; historical `57fdc56c...`,
  `22aa96f9...` and `bdce2e68...` are HISTORICAL, not current. Activation/deploy is UNVERIFIED:
  verifier mirror, service restart, full verifier, deploy and live probes are HOST-ONLY and NOT
  RUN. Unit metadata closure is COMPLETE in the M2/final record; Q59 earns no Q56 pilot credit
  and no deployment claim is made.
  Tracker: `odd/tasks/q59-pm-verifier.md`.
- **Prerequisites:** Q55; easier after Q26 and Q04. Q26 and Q04 are not hard blockers (owner:
  Q04 is NOT a blocker); re-verify Q55 handoff acceptance at implementation start rather than
  inferring it from aggregate status.
- **Description:** replace the single-name `gentle-orchestrator` checks with a coordinator
  set that also asserts the PM identity surface; permission, depth and family-independence checks;
  prompt-size budgets; behavioural probes through the orchestrator (Q51); digest re-pin. The
  historical "23" count is UNVERIFIED and is replaced by the tracker's line-numbered
  inventory/classification. Owner decision (2026-10-19): all prompt sizes are measured
  (`gentle-orchestrator=57167`, `pm-odd=2968`, `pm-systematic=2982`); the PM `<6000`-character cap
  is enforced; the numeric orchestrator cap is deferred to Q57 ("about 8,000" is the planned
  target, not an invented threshold). Corrected PM contract: the orchestrator alone keeps
  `general`; both PMs dispatch a mid-unit tiny fix only to `odd-apply` or `gentle-ai-worker`
  (DeepSeek), never `general`, and otherwise use their PM-authorized writer/verifier lanes (local
  writer `kinver/professional`; verifier OpenAI Sol); strict declared maximum task keys reject an
  unknown key whether `allow` or `deny`. Owner authorization for `global-config/opencode.json` is
  limited to removing `general` from the two PM task maps; source commit1 also changed only the
  two PM Tiny-fix sentences. Seven test modules were extended (six Python, one JS),
  `test_anchor_manifest.py` ran unchanged, and the current pin is
  `28ff39379aee7460bce784386e62c83bf5f51aea2b93074e2f35230fa299e7ad` (historical `57fdc56c...`,
  `22aa96f9...` and `bdce2e68...` are superseded). Split source receipts: S1 253/32,732;
  S2a 189/22,277; S2b 162/13,680; S2c 185/13,674; S2d/e 213/19,607. These five are the committed
  source history, not a pending metadata SHA. Each commit was assessed immediately against its
  prior boundary with `committedOnly=true`, and the now owner-supplied reviews closed the due
  high-risk candidates. Config/prompt runtime is still not attested; full verifier, deploy and
  live probes are HOST-ONLY and were NOT RUN. Q54's identity on a permitted broker call is inferred
  because the broker echoes no identity.
- **Forward check (Q90 decision 1, 2026-10-23):** verify the PM runs the six `asi-review-*` lanes
  and the review lifecycle; do not require a "lack of relays" check. Verify the PM model/prompt
  is `glm-5.3-flash`; keep the `<6000`-character prompt cap, the digest re-pin and the historical
  evidence/status above.

### Q60. PM layer: model assignment
- **Status:** PLANNED — seats selected by Q90 (2026-10-23); remaining implementation OPEN. Model-ID existence and seat/independence readiness remain open.
- **Prerequisites:** Q56.
- **Description:** PMs on `openai/gpt-6.1-sol`; writers on DeepSeek; move `advisor-design-pre`
  and `advisor-security-pre` off Sol; fallback chains keep a PM off its writer's family; exclude
  PMs from the Astra aliases. Owner decision: a cheaper PM for tiny-fix and documentation units.
- **Supersession (2026-10-23, Q90 decision 3):** the old PM-on-Sol assignment is SUPERSEDED:
  PM `glm-5.3-flash` high with `qwen3.8-flash` high fallback, Planner `openai/gpt-6.1-sol` high
  (xhigh for gate 1 on multi-step/high-risk). Writers remain DeepSeek; `advisor-design-pre` and
  `advisor-security-pre` move off Sol; PM/writer fallback family independence and the Astra
  exclusion remain requirements. That implementation is still OPEN; the cheaper PM for
  docs/tiny-fix is satisfied by the selected GLM seat, but deployment is UNVERIFIED.

### Q61. PM layer: remaining routes and close
- **Status:** PLANNED.
- **Prerequisites:** Q57, Q58, Q59, Q60.
- **Description:** move the Systematic route to `pm-systematic` (SDD is retired by v4; `pm-sdd` was
  RETIRED by Q65 on 2026-10-11, so Q61 no longer lists it); remove
  `gentle-orchestrator-legacy`; `ce:compound`. Require relay-delivery proof from a dispatch
  outside the coordinating PM session, carrying a genuine provider-issued binding; Q54 showed
  reachability only, not delivery. Do not require the PM itself to dispatch or prove its own relay
  delivery. For V2,
  the four-level nesting must be probed in Q41, because V2 has no `subagent_depth` (Q43).

### Q62. Keep retired models aligned with seat assignments
- **Status:** PLANNED.
- **Prerequisites:** none.
- **Description:** resolve the maintenance gap between the retired-model list and seat
  assignments. Three seats in a row were blocked by the retired-model list; the list and
  assignments are maintained in different places, with no mechanism keeping them in sync.
  Define one authoritative relationship or a check that detects drift, then reconcile both
  records without blocking valid assignments accidentally.

### Q63. Native review CLI lifecycle and store-integrity blockers
- **Status:** BLOCKED (upstream CLI/schema gap; store repair unsupported); malformed compact-state
  lineages deferred pending the Gentle AI 4.x upgrade.
- **Prerequisites:** Gentle AI must publish a usable intended-untracked-selection schema and
  provide a supported repair path for malformed compact state. Installed build is 3.7.0 (stable);
  the owner is preparing for 4.x.
- **Source:** Native-review investigation of `review-df3efa401830a824` on Gentle AI 3.7.0,
  stable, protocol 1.5; findings recorded in `odd/tasks/pm-layer.md`.
- **Description:**
  - The lineage reached `correction_required` with
    `next_transition: intended_untracked_selection_required`, but the required exact
    `gentle-ai.review-intended-untracked-selection/v1` JSON schema is not exposed by the CLI.
    `gentle-ai review capabilities` lists 18 schemas, while `gentle-ai review schema` accepts
    only `capture-result-dry-run`, `refuter`, `reviewer`, and `validator`. The tested inputs
    `[]`, `{"intended":[]}`, and `--untracked-scope=exclude` were rejected with
    `invalid_request`. A lineage at this transition cannot be advanced through the CLI: this is
    a blocking CLI/schema gap.
  - `gentle-ai review inspect-authority` reported `complete: false`, `valid: false`, 10 compact
    entries, six `malformed_compact_state` entry diagnostics, and one valid recovery edge.
    `gentle-ai review repair --preflight` reported `status: unsupported`, six unsupported
    lineages, and zero eligible candidates; automatic repair is unavailable. Affected lineage
    IDs: `review-2a1bfe11a622fa3c`, `review-43365ff5c2bb5a93`,
    `review-59015664a1ffc9ea`, `review-64494052f59ee6b9`,
    `review-ca0b00d6638492b9`, `review-fb8e1806d1fc1169`. These pre-existing shared-store
    findings were reported by the CLI; no store files were inspected. The existing log entries
    locate the store at `.git/gentle-ai`.
  - Defer these six malformed compact-state lineages pending the Gentle AI 4.x upgrade. Do not
    file or comment on an upstream report while a published fix may exist in the pending release:
    the residue protocol forbids reporting when a fix is not verifiably absent. If 4.x ships
    without fixing this, an upstream report becomes appropriate then.
  - After upgrading, run `gentle-ai review inspect-authority` and confirm the six entries either
    read cleanly or are repairable, with `gentle-ai review repair --preflight` reporting eligible
    candidates. Record the outcome here. Also re-check the unpublished
    `gentle-ai.review-intended-untracked-selection/v1` schema after upgrading; this schema gap is
    separate from the malformed-state question and may or may not be affected by 4.x.
  - Run provider-returned lifecycle/recovery commands verbatim; do not append caller-authored
    flags. The recovery-command rule is already established in the gentle-ai v4 notes above
    (around line 590) and `docs/TODO-HISTORY.md` (2026-09-30 item 1, around line 104); this item
    reinforces rather than duplicates that rule.

### Q64. PM workflow execution optimisations
- **Status:** DONE (2026-10-09); the owner selected install-then-refine and all four rules are
  formalised in `WORKFLOW.md`, `docs/specs/pm-handoff.md`, and `odd/tasks/pm-layer.md`.
- **Prerequisites:** none; the refinement-loop decision is made (install-then-refine, option a).
- **Source:** owner, 2026-10-09; observations and decision recorded in
  `odd/tasks/pm-layer.md`, “Workflow optimisations (owner, 2026-10-09)”.
- **Description:** confirm the appropriate feature branch before unit work; install each writer
  result before dispatching a fresh writer to refine on the installed base, with only the reviewed
  result committed; run required independent post-code advisory review from the PM before the
  work-unit commit (native review remains separate); and delegate bounded read-only investigation
  to `explore` agents.

## gentle-ai v4 upgrade (PLANNED — implement when the owner decides to upgrade)

Source for the whole group: `gh release view v4.0.0 -R Gentleman-Programming/gentle-ai` (released
2026-10-01; repo docs at tag v4.0.0). Installed: 3.7.0 via Homebrew (`/home/linuxbrew/.linuxbrew/bin/gentle-ai`);
OpenCode 1.18.33 (V1). Route proposal: `docs/PLAN.md` "Route for former-SDD work".

Release facts that drive the group:
- SDD and OpenSpec are removed: no `/sdd-*`, profiles or phases. Removed subcommands:
  `sdd-status`, `sdd-continue`, `sdd-attempt`, `sdd-archive-compose`, `sdd-task-result`,
  `sdd-preflight-hook`. Removed flags: `install --sdd-mode`, `sync --sdd-mode`,
  `sync --sdd-profile-strategy`. `sync --strict-tdd` is rejected and a saved `strict_tdd` is
  ignored (test-first guidance is installed by default).
- One managed orchestrator prompt per runtime. OpenCode generic agents: `gentle-ai-explore`
  (read-only mapper), `gentle-ai-worker` (implementation writer), `gentle-ai-verify` (read-only
  verifier). `review-risk|resilience|readability|reliability`, `jd-fix-agent`, `jd-judge-a`,
  `jd-judge-b` are re-provisioned. The legacy `__managed_by` marker is removed by a JSONC-aware
  cleanup.
- Delegation uses an evidence budget instead of file counts: inline only within one parallel batch
  (at most 3 calls, about 10k tokens); more than about 5 sequential lookups or long-session mapping
  goes to one read-only explorer returning at most about 2k tokens with `path:line`. The writer
  rule for 2+ non-trivial files is unchanged.
- v4 ODD mirrors the feature document to Engram under `odd/<feature>/tasks`; our recipe mirrors to
  Magic Context.
- `sync` exits non-zero when it cannot detect the OpenCode version. The OpenCode review plugin
  refuses on PATH `gentle-ai` binary skew. V2-only managed plugins (`@opencode/plugin`) do not
  apply on V1; note them for a later OpenCode V2 move.
- `review assess` judges added lines; STATUS returns a runnable `review recover` command;
  Engram, Context7 and Persona writers target the effective settings file. Go module path is `/v4`:
  a v3 self-upgrade cannot cross to v4 on Go installs; `brew upgrade gentle-ai` is fine.

### Q29. Decisions before upgrading (owner) — ALL DECIDED 2026-10-02
- **Status:** PLANNED, gated by "owner decides to upgrade".
- **Prerequisites:** none.
- **Source:** v4.0.0 release notes; `docs/PLAN.md` "Route for former-SDD work (proposed, v4)",
  "Memory and inter-agent communication".
- **Description:** decisions only; record each in `docs/PLAN.md` Recorded design decisions.
  - (a) DECIDED (owner, 2026-10-02): the full former-SDD route in `docs/PLAN.md` (ODD doc → `ce:brainstorm` → `ce:plan` → advice → `ce:work` → post-code advice → `ce:review` → native review → `ce:compound`).
  - (b) DECIDED (owner, 2026-10-01): Magic Context remains the default memory pathway
    throughout, and mandatory Engram instructions are removed.
    - On upgrade, override or disable v4's Engram `odd/<feature>/tasks` mirror; the ODD tracker
      mirror stays Magic Context.
    - Engram is at most the opt-in inter-agent channel (Q14).
    - See Q35 for removal and enforcement.
  - (c) DECIDED (owner, 2026-10-02): keep a user-owned `gentle-orchestrator` prompt, rebuilt from
    v4's managed OpenCode prompt (`internal/assets/opencode/orchestrator.md` at v4.0.0) as the base,
    with our secure rules in marked blocks so upstream changes show as diffs. The verifier keeps
    restoring it after every sync.
  - (d) DECIDED (owner, 2026-10-02): agent mapping, keeping the proven cross-family
    writer/verifier pair:

    | role | agent | model (from) |
    |---|---|---|
    | explore | `gentle-ai-explore` | deepseek-v4.1-flash (our `explore`) |
    | write, cloud | `gentle-ai-worker` | deepseek-v4.1-flash (`sdd-apply`) |
    | write, local | `gentle-ai-worker-local` (ours) | kinver/professional (`sdd-apply-local`) |
    | verify | `gentle-ai-verify` | gpt-6.1-sol (`sdd-verify`) |
    | execution fallback | `general` | gpt-6-luna (unchanged) |
    | retired | `sdd-*` | — |

    The definitions are user-owned, with sandbox tools, the search contract and the Magic Context
    adapter carried over. The per-session write-path choice (`session-decisions.md:11-17`) maps
    to `gentle-ai-worker` vs `gentle-ai-worker-local`. The verifier's writer/verifier diversity
    check (`verify-workflow.sh:2273`) moves to the `gentle-ai-worker`/`gentle-ai-verify` pair.
    Keep `asi-review-*`, `advisor-*`, `jd-*` and Astra aliases, re-checking family diversity.

### Q30. Workflow documents
- **Status:** DONE-AT-SOURCE (T1 committed `522683b`: both skill files deleted; a detect-only `RETIRED_WORKFLOW_SKILL_PRESENT` check added; pin `12ebaf72…`).
- **Deploy (OWNER, pending):** after the verifier mirror and OpenCode restart, run `rm -rf ~/.config/opencode/skills/workflow-sdd-secure`; the verifier will fail with `RETIRED_WORKFLOW_SKILL_PRESENT` until it is done (intended).
- **Prerequisites:** Q29.
- **Source:** v4.0.0 release notes. `WORKFLOW.md` :7, :11, :35, :39, :86, :100 (Substantial feature
  row), :105-111 (Classification and SDD Selection Rules), :123, :125 (`sdd-verify` verifies
  `sdd-apply`), :127-134 (Context and SDD Artifact Backend; `gentle-ai.sdd-status/v2`), :140
  `host_sdd_*`, :144, :146, :150-155 (Optional SDD Research), :157, :162, :186-187
  (`sdd-archive-compose`), :196-201 (precondition rows), :212, :223-226 (UI lane in SDD), :241,
  :271-273 (Astra rows sdd-design/spec/verify), :297, :302, :321, :418; file-count rules :52-58
  (esp. :55); TDD-mode forwarding :66. `global-config/AGENTS.md` :49-59 and :236. Skills and
  `docs/PLAN.md`: every SDD mention (regenerate the list with `rg -n SDD docs/PLAN.md` when the
  work starts; line numbers drift).
- **Description:**
  - Delete the SDD sections, rows and the `workflow-sdd-secure/` skill (`SKILL.md`,
    `references/sdd-magic-adapter.md`).
  - Rewrite Task Classes and the selection rules to the Q29a route.
  - Replace file-count delegation with the evidence budget.
  - Retitle the "Gentle AI 3.5.0" headings to version-neutral or 4.x.
  - Remove TDD-mode-selection assumptions (test-first is the default; still forward the runner).
  - Remove the `user:host-sdd-runtime-boundaries` block (`host_sdd_status`, `host_sdd_continue`)
    and the `workflow-sdd-secure` routing line in `AGENTS.md`.
  - Update the Astra table.
  - Skills: `workflow-route/SKILL.md` :3, :13, :14, :18, :20, :22;
    `workflow-route/references/session-decisions.md` :9, :11-12, :17 (`sdd-apply-local`/`sdd-apply`
    write path), :34, :38, :50-52, :58, :80, :85, :88; `workflow-odd-secure/SKILL.md` :8, :11
    (file-count triggers), :12, :14; `workflow-odd-secure/references/odd-and-review.md` :3-8, :19,
    :33, :40, :56-57; `workflow-systematic/SKILL.md` :13;
    `workflow-systematic/references/specialists.md` :20.
  - Update the session-decisions write path to the Q29d agents.
  - Update `docs/PLAN.md` at the cited lines.

### Q31. Agent allocation (`global-config/opencode.json`, `tui.json`, `systematic.jsonc` if needed)
- **Status:** IN PROGRESS — source complete, committed and reviewed; deploy (verifier mirror +
  restart) is the owner's pending step.
- **Prerequisites:** Q29.
- **Source:** v4.0.0 release notes. `global-config/opencode.json`: `gentle-orchestrator` :522
  ("Gentle AI SDD Orchestrator"), :647 (local prompt "# Gentle AI — SDD Orchestrator
  Instructions"); `permission.task` sdd-* :546-555, :594; `host_sdd_*` permissions :622-629,
  :643-644, :2133, :2158-2173; agents `sdd-apply` :1117, `sdd-apply-local` :1165, `sdd-archive`
  :1213, `sdd-design` :1261, `sdd-explore` :1309, `sdd-init` :1357, `sdd-onboard` :1405,
  `sdd-propose` :1453, `sdd-spec` :1501, `sdd-tasks` :1549, `sdd-verify` :1597, `sdd-research`
  :1749 (prompts `{file:./prompts/sdd/sdd-*.md}` plus the "USER-OWNED MAGIC CONTEXT SDD ADAPTER");
  `asi-review-*` :595-600, :1809-2013; `jd-*` :537-539, :672, :720, :770.
  `global-config/tui.json` :6 `opencode-sdd-engram-manage`.
- **Description:**
  - Remove the `sdd-*` agents and their `permission.task` entries.
  - Set every `host_sdd_*` permission to `deny` (owner, 2026-10-01). Deny rather than delete, so a
    host tool that still registers is refused explicitly. Today the global grants
    `host_sdd_status`, `host_sdd_continue` and `host_sdd_task_result` are `allow`, and the
    orchestrator's `host_sdd_attempt_grant` and `host_sdd_archive_compose` are `ask`. All become
    `deny`. This can land before the upgrade (Q37).
  - Add and allow the v4 generic agents per Q29d, with explicit models.
  - Reconcile the re-provisioned `review-*` and `jd-*` agents with our definitions.
  - Retitle the `gentle-orchestrator` description and prompt per Q29c.
  - Drop `opencode-sdd-engram-manage` from `tui.json`.
  - Engram MCP per Q14b.
  - Remove the `./prompts/sdd/` prompt files no agent references.

### Q32. Verifier (`verify-workflow.sh`)
- **Status:** DONE-AT-SOURCE (T0–T5 are committed and reviewed — `odd/tasks/q32-verifier-v4.md`; final pin `14d37ce9…` after Q65; deployment is pending the owner).
- **Prerequisites:** Q29, Q31. Q26 strongly preferred, Q04 preferred.
- **Source:** v4.0.0 release notes; `verify-workflow.sh` line refs below (read-only mapping,
  2026-10-01).
- **Description:** the verifier will FAIL on v4. Remove or replace:
  - §1: `:3380-3383` `gentle-ai sdd-archive-compose --help`; `:3399-3423` required
    `$SKILLS_DIR/sdd-research|sdd-verify|sdd-archive/SKILL.md` and `commands/sdd-research.md`.
  - §6: `:4277-4278` and `:765` require `workflow-sdd-secure` files.
  - §7: `:4108`, `:4118`, `:4132` grep `WORKFLOW.md` for "## Context and SDD Artifact Backend",
    "Optional SDD Research and Diagnostics — Gentle AI 3.5.0", "gentle-ai sdd-archive-compose";
    `:4333`, `:4339`, `:4349`, `:4357` routing-contract SDD strings; `:2788-2793`, `:2870`,
    `:2889`, `:2904` embedded SDD strings.
  - §9: `:352-355` required agents `sdd-research`, `sdd-apply-local`; `:2273` writer/reviewer pair
    `sdd-apply`/`sdd-verify`; `:2641-2643` `host_sdd_*` permission asserts. Move `host_sdd_status`, `host_sdd_continue` and
    `host_sdd_task_result` out of `registeredHostReads` and assert every `host_sdd_*` is `deny`
    (global and orchestrator), keeping the `HOST_MUTATION_OR_RETIRED_DEFAULT_NOT_DENY` code; `:2663-2679` `sdd-*`
    writer and `SDD_RESEARCH_*` checks; `:2699`, `:2767`; `:2916-2919`
    `MAGIC_CONTEXT_SDD_OVERRIDE_MISSING`; `:2950-2958` runtime probes; `:3108-3126` GitHub MCP
    reader lists that include sdd agents; `:4448-4456` probe list; `:4617`.
  - Section 0 AGENTS recovery: `:861-862`, `:941-952`, `:1268`, `:4202-4248` (host-sdd block).
  - Version: the floor at `:3343-3349` is 3.5.0 and passes on 4.0.0; move it to 4.0.0 and replace
    the `GENTLE_AI_V3_5_SYNC_*` codes (`:3366-3372`, read `~/.gentle-ai/state.json`) with
    `GENTLE_AI_V4_*`.
  - "Gentle AI 3.5.0" heading pins: `:4073` (`WORKFLOW.md:74`), `:4118` (`WORKFLOW.md:150`),
    `:4121` (`WORKFLOW.md:50`), `:2813-2815`, `:2866`, `:2872`, `:4316`, `:4321`: replace.
  - File-count delegation pins `:2774`, `:2823`, `:4125`, `:4318`: update to evidence-budget
    wording, ideally via Q26 anchors.
  - Add checks: no `sdd-*` agent or `host_sdd_*` grant present; v4 generic agents registered with
    the expected tools; `gentle-ai sync` exit status handled; review plugin binary-skew awareness.
  - Re-pin `VERIFY_SCRIPT_SHA256` (`:76` and the health plugin) after the edits.
  - **S5b verifier findings (Q31 S5b native review `review-8b540c67721bcaa1`, 2026-10-11):**
    - `R3-WORKSPACE-001` (`verify-workflow.sh:2895`): an empty `workspaceRoot` silently falls back to
      a relative path.
    - `R4-001` (`:3041`): the Magic Context scrubber lookahead silently no-ops if the following
      heading level changes.
    - `R4-002` (`:4800`): `workspaceRoot` undefined at another call site would throw before `fail()`.
    - `R4-003` (`:4813`): the assembler-missing/failed codes leak an absolute host path + raw error.

### Q33. Guard and plugins
- **Status:** DONE-AT-SOURCE (T0–T1 committed and reviewed — `odd/tasks/q33-guard-plugins.md`; commit `f10468b`; Q15 is closed as obsolete; the `astra-sol-upgrade.ts` name check was resolved — it names only `jd-fix-agent`/`gentle-orchestrator`, both present — its runtime resolution remains statically unprovable).
- **Prerequisites:** Q29; Q03 (route namespacing).
- **Source:** v4.0.0 release notes. `systematic-routing-guard.ts` :219 (skill list contains
  `workflow-sdd-secure`), :505 (`host_sdd_` prefix); `workflow-health-check.ts` :8, :40 (comments);
  `astra-sol-upgrade.ts` :42, :57-70 (depend on `jd-fix-agent`/`gentle-orchestrator` names).
- **Description:**
  - Remove `workflow-sdd-secure` from the guard skill list (:219) and the `host_sdd_` prefix
    handling (:505).
  - Close Q15 as obsolete.
  - ROUTE_STAGES for the Q29a route: requirements, plan, tracker, review, namespaced by route
    (relates to Q03 cross-route namespacing and Q18).
  - Update the comments in `workflow-health-check.ts`.
  - Confirm `astra-sol-upgrade.ts` still resolves its agent names after Q31.

### Q34. Upgrade procedure (runbook)
- **Status:** DONE-AT-SOURCE (T0–T1 committed — `odd/tasks/q34-upgrade-runbook.md`; commit `3789cc1` authored `docs/upgrades/gentle-ai-v4.md`, 257 lines). The runbook WAS executed on 2026-10-13 (gentle-ai 3.7.0 → 4.1.1, Steps 1–12), recorded in the Q34 tracker's execution record.
- **Prerequisites:** Q29-Q33 on one gated branch.
- **Source:** v4.0.0 release notes; Q24 (sync overwrites the live config).
- **Deliverable:** [`docs/upgrades/gentle-ai-v4.md`](upgrades/gentle-ai-v4.md) is the sole
  authority for Gentle AI v4 upgrade execution, activation, recovery and completion checks. Q34
  tracks document readiness only; publishing the runbook does not authorize the upgrade.

### Q35. Remove mandatory Engram instructions everywhere (Magic Context is the default memory)
- **Status:** CLOSED — OpenCode side DONE-AT-SOURCE; Claude-side remainders OUT OF SCOPE.
  - Closure finding (read-only sweep 2026-10-11): no live OpenCode mandatory-Engram instruction
    and no Engram-requiring enforcement remains in this repository. The only literal
    mandatory-Engram text is vendored upstream prompt source
    (`global-config/prompts/gentle-orchestrator/upstream/orchestrator.template.md:155-160`,
    `:179-183`) and its byte-exact render
    (`global-config/prompts/gentle-orchestrator/base.md:303-306`, `:326-329`); the overlay
    (`overlay.md:152-182`) replaces exactly those sections at assembly, and the deployed prompt
    (`global-config/opencode.json:590`) is the assembled artifact verified to contain zero
    `engram`/`mem_` residue by `tests/test_orchestrator_prompt_source.py:310-324` (with a planted
    positive control). The `ENGRAM_*` verifier checks are presence-guards that must be KEPT
    (`verify-workflow.sh:3267`, `:4625-4629`, `:3099-3110`, plus the `recover_agents_file` strip
    `:883-884`, `:929-939`). Magic Context is the OpenCode memory rule (`WORKFLOW.md:66`,
    `:131`), deployed via the four generic-agent adapters in `global-config/opencode.json`. No
    verifier re-pin: Q35 makes no `verify-workflow.sh` edit.
  - Done 2026-10-01: Claude Code text stripped. The `gentle-ai:engram-protocol` block was removed
    from `~/.claude/CLAUDE.md`, and the ODD lines now make the task file the durable record, with
    a Magic Context mirror where the runtime has it and Engram "never required". Backup:
    `backups/claude-md/CLAUDE.md.20261001T222932Z.before`.
  - Owner choice: the Engram plugin stays installed until Q14b brings Engram back as an
    inter-agent MCP. Q14b (an optional, never-mandatory scoped Engram MCP for OpenCode) is a
    separate queue item and is NOT part of Q35.
  - Claude-side remainders — SKIPPED by owner decision (2026-10-11): the plugin's SessionStart
    hook (which injects its own "MANDATORY" protocol text) and the planned Claude Code enforcement
    check are Claude-side and outside this repository (`~/.claude/CLAUDE.md` + the Claude Code
    Engram plugin). Engram is deliberately RETAINED as the Claude Code <-> external-advisor memory
    channel, so neither remainder is removed or enforced against. The ODD lines sit inside the
    gentle-ai-managed `agent-routing` block and the protocol block is gentle-ai-managed too, so a
    future `gentle-ai sync` may restore both; that is accepted, not a Q35 open item.
- **Prerequisites:** none for the OpenCode side (already done). Claude Code side: owner confirms
  the scope of edits to `~/.claude` (outside this repo).
- **Source:** owner decision; read-only survey 2026-10-01.
- **Description:**
  - **OpenCode: already enforced.** Magic Context is the OpenCode memory rule (`WORKFLOW.md:66`,
    `:131`). The verifier fails on `LEGACY_ENGRAM_PROTOCOL_REAPPEARED` (`verify-workflow.sh:4625-4629`)
    and on `ENGRAM_UNEXPECTEDLY_ENABLED` (`:3267`); these presence-guards fire on Engram
    REAPPEARING and must be kept through the v4 upgrade. Q14b must not reintroduce a mandatory
    protocol, only a scoped opt-in channel.
  - **Claude Code (Claude-side; OUT OF SCOPE per the 2026-10-11 owner decision — kept for
    history).** The original plan was to remove:
    - the gentle-ai-managed `<!-- gentle-ai:engram-protocol -->` block in `~/.claude/CLAUDE.md`
      (lines 536-564 today);
    - the ODD lines that require an Engram mirror of the tracker (`:579`, `:620-622`, and the
      resume steps that call `mem_*`);
    - the Engram plugin's SessionStart "ACTIVE PROTOCOL … MANDATORY" injection. Disable it, or
      keep the plugin's tools available without the mandatory hook.
    Correction (owner, 2026-10-01): Claude Code cannot reach Magic Context, so its memory
    pathway is Engram only, used mainly in its advisory role. What is removed is the blanket
    mandatory-protocol text, not Engram itself. `~/.claude/CLAUDE.md` now states the
    per-runtime pathway.
  - **Enforcement (Claude-side, OUT OF SCOPE per the owner decision 2026-10-11):** the planned
    check — failing when `<!-- gentle-ai:engram-protocol -->` or a mandatory Engram hook reappears
    (per the deployment-gating constraint, Q28; relates to Q24 sync drift) — is Claude-side and is
    NOT implemented here. No OpenCode enforcement against Engram is wanted; the OpenCode
    `ENGRAM_*` checks guard against re-introduction and stay.
  - **v4:** apply the same rule to v4's managed orchestrator prompts (Q29b, Q30).

### Q36. Non-destructive change set for the v4 upgrade: apply and revert without clobbering drift
- **Status:** DONE. Tool completed 2026-10-02: `scripts/changeset.py`, spec
  `docs/specs/changeset-tool.md` v1.3, 72 tests, three native reviews approved (tracker
  `odd/tasks/changeset-tool.md`; follow-up T5). The v4 change-set CONTENT is authored at upgrade
  time (Q30-Q33), per the build-late rule.
- Status note (2026-10-11): the TOOL is DONE; the v4 CONTENT is build-late BY DESIGN — authored at
  upgrade time — so Q36's tool is DONE and its content is deliberately deferred: no change-set
  content is authorable inside the repo now (no re-pin). The build-late rule is at
  `odd/tasks/changeset-tool.md:17`; the earlier note cited `docs/specs/changeset-tool.md:17`, which
  is the v1.2 changelog note — a citation drift corrected here. Q30–Q33, Q35, Q38 are committed to
  feat/gentle-ai-v4 and Q39's gate is deferred, so the repo-tracked half already reaches live
  through the verifier mirror. The live `~/.config/opencode` surfaces Q36 once claimed are
  regenerated by the verifier's six `recover_*` functions in `verify-workflow.sh`
  (`recover_opencode_config`, `recover_tui_config`, `recover_reviewed_router_skills`,
  `recover_agents_file`, `recover_systematic_config`, `recover_fallback_policy`), not by change-set
  operations. Exactly two genuine remnants remain and neither can live in a change set: (a) the
  retired skill DIRECTORY `~/.config/opencode/skills/workflow-sdd-secure` — the `file_remove` op
  moves a single FILE, so it cannot express a directory removal; it belongs to the Q34 runbook's
  one-time manual `rm -rf`. (b) `~/.claude/CLAUDE.md`'s gentle-ai-managed blocks — the verifier
  cannot reach them, the Claude side is OUT OF SCOPE per Q35, and Q38 says to check them AFTER the
  v4 sync, so they belong to the Q38 post-sync check, not change-set ops.
- **Prerequisites:** Q29 (the changes to encode); Q26 (stable anchors make markdown edits
  addressable).
- **Source:** owner, 2026-10-01: build it all non-destructively, with a simple process to insert
  the changes when upgrading and, ideally, a revert that will not overwrite drift elsewhere.
- **Description:**
  - **Change set:** `upgrade/v4/` holds declarative operations, never whole-file copies.
    - JSON (`opencode.json`, `tui.json`): operations keyed by JSON path, each with
      `expect_before` and `set` (or `delete`).
    - Markdown (`WORKFLOW.md`, `AGENTS.md`, skills, `~/.claude/CLAUDE.md`): operations keyed by
      an anchor or marked block, with the expected current block text and the replacement.
    - Whole files: add or remove only with the expected hash, e.g. deleting `workflow-sdd-secure`.
  - **Apply (`python3 scripts/changeset.py apply --set upgrade/v4 [--dry-run]`):**
    - For each operation, apply it only when the current value equals `expect_before`.
    - If it already equals the target, record it as already applied (idempotent).
    - Otherwise report a conflict and skip that operation. Never overwrite.
    - Write a journal under `backups/upgrade-v4/<timestamp>/` with, per operation, the before
      value, the applied value and the outcome.
    - Finish by running the verifier: mirror, checks, digest re-pin as committed.
  - **Revert (`python3 scripts/changeset.py revert --journal <journal> [--dry-run]`):**
    - Restore an operation's before value only when the current value still equals what apply
      wrote.
    - Anything changed since (gentle-ai sync, other sessions, manual edits) is reported as drift
      and left untouched.
  - **Repo-tracked files** additionally ship as one feature branch (Q30-Q33); `git revert` of the
    merge is the repo-level rollback. The live files under `~/.config/opencode` and `~/.claude`
    are what the journal protects.
  - **Gating (Q28):** apply refuses when the verifier fails before it starts, and reports the
    verifier result after it finishes.
  - **Failure paths:**
    - The journal is write-ahead: each operation's before value and intent are recorded and
      flushed BEFORE its write, and the outcome after it. An interrupted apply is resumable,
      because rerunning treats applied operations as idempotent and pending ones as fresh.
    - Revert ignores operations whose apply outcome was conflict-skip or already-applied (it
      wrote nothing).
    - Revert refuses a missing journal, or one that fails its checksum or schema, and changes
      nothing.
    - Both tools take a lock so two runs cannot interleave.
  - **Contents (owner, 2026-10-01):** the set includes
    - the `host_sdd_*` → `deny` operations and the matching verifier change, as one unit (Q37);
    - the strict-TDD removals (Q38);
    - the in-flight SDD preflight (Q39). Apply refuses while any in-flight SDD change lacks a
      recorded disposition.
  - **Tests:** a fixture tree covering clean apply, already-applied, conflict-skip, interrupted
    apply then resume, revert, revert-with-drift-preserved, revert of a conflict-skipped
    operation (no-op), and a missing or corrupt journal (refused).

### Q37. Deny the `host_sdd_*` tools (merged into the Q36 change set)
- **Status:** MERGED into Q36 (owner, 2026-10-01: "this should be part of the script"). Not
  applied early. The details below define the Q36 operations and preflight.
- **Prerequisites:** none. It is a global tooling change, routed as source change, then native
  review, then verifier mirror and restart.
- **Source:** owner, 2026-10-01; current grants listed in Q31.
- **Description:**
  - Set the five open `host_sdd_*` grants to `deny` in `global-config/opencode.json`.
  - Update `verify-workflow.sh` `registeredHostReads` and the deny assertion, then re-pin the
    digest.
  - Mirror, then restart.
  - Effect: SDD host tools stop working on 3.7.0 too. Acceptable only if no SDD work is in
    flight.
  - **Ordering guard:** the `opencode.json` deny and the verifier update land in ONE commit, and
    the verifier must pass on that commit before the mirror. Applying either half alone fails the
    verifier (`HOST_READ_PERMISSION_MISMATCH`, or the new deny assertion).
  - **Precondition check:** confirm no SDD change is in flight before applying. Use
    `gentle-ai sdd-status` on 3.7.0 for each registered project, and look for active
    `openspec/changes/*` or Magic Context `SDD_ARTIFACT` keys. If any are found, stop and ask
    the owner.

### Q38. Remove strict-TDD references (v4 retires `strict_tdd`)
- **Status:** DONE-AT-SOURCE (commit `5ba5226`; the three live wording sites rewritten; the orchestrator prompt regenerated and its digest + ledger citation updated; no re-pin; the proposed verifier Gate DEFERRED — it would fire on `docs/PLAN.md:80`, which retains `strict_tdd` as a forbidden dependency).
- **Prerequisites:** Q29c (the orchestrator prompt decision decides how its block is removed).
- **Source:** v4.0.0 release notes (`sync --strict-tdd` rejected; a saved `strict_tdd` enables
  nothing; test-first guidance installed by default). Read-only survey 2026-10-01.
- **Description.** Remove or rewrite:
  - `global-config/opencode.json:647`, the `gentle-orchestrator` prompt's "Strict TDD Forwarding
    (MANDATORY)" block, which reads `strict_tdd: true` from the SDD init record and injects
    "STRICT TDD MODE IS ACTIVE".
  - `WORKFLOW.md:66` and `global-config/skills/workflow-odd-secure/references/odd-and-review.md:19`:
    "Forward resolved TDD mode, its source, and exact test runner". Rewrite to: test-first by
    default for runnable deterministic behaviour changes, and forward the exact test runner.
  - `global-config/skills/workflow-odd-secure/SKILL.md:14`: "TDD mode and runner" becomes
    "test runner".
  - `~/.claude/CLAUDE.md:550` and the ODD paragraph "Resolve effective TDD on/off …": same
    rewrite. These sit in gentle-ai-managed blocks, so v4 sync may supersede them; check after
    sync.
  - The gentle-ai-managed `sdd-*` skills, prompts and commands that carry strict-TDD files, under
    `~/.config/opencode/{skills,prompts/sdd,commands}` and `~/.claude/skills`
    (`sdd-apply/strict-tdd.md`, `sdd-verify/strict-tdd-verify.md`, …). v4 sync retires the
    managed SDD assets. Verify that it did, and remove only provably managed leftovers. Never
    touch user-owned files.
  - Saved `strict_tdd` keys in SDD init records (Magic Context, Engram): leave them. They are
    inert on v4, and v4 preserves persisted SDD keys.
  - **Gate (DEFERRED):** the proposed verifier check — fails if `strict_tdd`, `--strict-tdd` or
    "STRICT TDD MODE" reappears in the canonical config, the workflow docs or the skills — is
    NOT implemented: it would false-fire on `docs/PLAN.md:80`, which keeps `strict_tdd` as a
    forbidden v4 dependency, and would force a re-pin plus another high-risk review.

### Q39. SDD changes in flight at upgrade time
- **Status:** RECORDED — inventory captured 2026-10-11; owner dispositions recorded 2026-10-12; gate not yet implemented (Q28 PLANNED). Still gated by "owner decides to upgrade" and remains a preflight of the Q36 apply.
- **Prerequisites:** none to inventory. Each disposition needs the owner and runs in that
  project's repository.
- **Source:** v4.0.0 removes SDD commands and phases but preserves user-owned files and persisted
  SDD keys, so in-flight changes survive with no tooling to continue them. Survey 2026-10-01.
- **Inventory today (unarchived `openspec/changes/*`):**
  - agent-sandbox-integration: `role-based-subagents`, `agent-host-tools`,
    `reviewer-relay-transport`
  - opencode-workspace/vision: `mock-ui-test`
  - peak-redir: `peak-hour-routing`
  - sdd-quality/mini-sdd: `local-apply-test`

  Some may be stale. Magic Context `SDD_ARTIFACT key=` records (OpenCode) and Engram `sdd/*`
  topics (Claude Code) were not enumerated here.
- **Preflight (in the Q36 apply):** enumerate in-flight changes on 3.7.0, using
  `gentle-ai sdd-status` per registered project, non-archived `openspec/changes/*`, Magic Context
  `SDD_ARTIFACT` keys and Engram `sdd/*` topics. Write the list to the journal. Refuse to apply
  while any change lacks a recorded disposition.
- **Disposition per change (owner chooses one):**
  1. **Finish on 3.7.0 first** (preferred when near done): complete apply, verify and archive
     before upgrading.
  2. **Convert to ODD** (the former-SDD route in `docs/PLAN.md`):
     - proposal and spec → `docs/brainstorms/<change>.md` (requirements);
     - design → `docs/plans/<change>.md`, plus decisions in the feature document;
     - tasks → `odd/tasks/<change>.md` checklist, keeping checked state and stable IDs;
     - apply-progress and verify results → the feature document's Progress section and
       evidence.
     Keep the original OpenSpec folder read-only and link it from the feature document. Resume
     under ODD after the upgrade.
  3. **Abandon:** move it to the archive marked abandoned, with a one-line reason in the
     project's ledger.
- **Record:** a row per change in the project's tracker or `ROUTER-LOG.md` with its disposition.
  The Q36 journal references them.
- **Gate:** the apply preflight is the enforcement point (Q28).

#### Q39 inventory (read-only, 2026-10-11)
Six unarchived SDD changes exist across four external projects (roots: `/home/james/agent-sandbox-integration`, `/home/james/opencode-workspace/vision`, `/home/james/peak-redir`, `/home/james/sdd-quality/mini-sdd`). The premise that they are stale is only partly true — two are live work. Per the 2026-10-11 decision, no disposition is made from this repository; each change's disposition is OWNED BY ITS PROJECT, and `agent-sandbox-integration` has already begun its own v4 retirement (`docs/upgrades/gentle-ai-4.md`).

| Change | Project | State observed | Disposition owner/status |
|---|---|---|---|
| `agent-host-tools` | agent-sandbox-integration | every task complete except Phase 5.1–5.6, each explicitly marked "Superseded by the gentle-ai 4 retirement" with a pointer to `docs/upgrades/gentle-ai-4.md` | superseded; project-owned archive |
| `reviewer-relay-transport` | agent-sandbox-integration | complete; has `archive-report.md` ("PASS; 13/13 complete; 7/7 requirements, 13/13 scenarios, zero findings; runtime ledger complete") which states the change directory "MUST NOT be deleted or moved" | done; leave in place |
| `role-based-subagents` | agent-sandbox-integration | Phase 0 and Phase A complete; Phases B, C and D unstarted | ACTIVE — project-owned |
| `peak-hour-routing` | peak-redir | 1.1–1.3 complete; task 1.4 BLOCKED on a host write with the finished config preserved as `rate-limit-fallback.json.new`; Phases 2–4 unstarted | ACTIVE/BLOCKED — project-owned |
| `mock-ui-test` | opencode-workspace/vision | header reads "Status: MOCK — planning simulated; apply runs for real in two lanes"; T1–T3 all pending | test fixture — project-owned |
| `local-apply-test` | sdd-quality/mini-sdd | NOT READABLE from this repository (read denied) | unknown — needs another route |

Gate reality: the "apply refuses while unarchived SDD changes exist" behaviour is NOT implemented — `docs/specs/changeset-tool.md:31-32` places that preflight out of scope, `scripts/changeset.py` exposes only a caller-supplied `--verify-cmd`, and the planned enforcement point is Q28 (status PLANNED). Nothing therefore blocks the Q36 apply today. Q39's own disposition rule (finish on 3.7.0; convert to ODD; or abandon-archive with a one-line reason) is exercised by each owning project, not here.

#### Q39 dispositions — OWNER DECISION (2026-10-12)

After reviewing `gentle-ai sdd-status` against the live projects, the owner records that ALL SIX in-flight SDD changes are ABANDONED as SUPERSEDED:

| Change | Project | Disposition | One-line reason |
|---|---|---|---|
| `agent-host-tools` | agent-sandbox-integration | abandon-archive | superseded |
| `reviewer-relay-transport` | agent-sandbox-integration | abandon-archive | superseded |
| `role-based-subagents` | agent-sandbox-integration | abandon-archive | superseded |
| `peak-hour-routing` | peak-redir | abandon-archive | superseded |
| `mock-ui-test` | opencode-workspace/vision | abandon-archive | superseded |
| `local-apply-test` | sdd-quality/mini-sdd | abandon-archive | superseded |

**Recorded 2026-10-12, BEFORE the binary upgrade** — `gentle-ai sdd-status` exists only on 3.7.0, so this had to precede the binary upgrade; it satisfies the runbook's "Q39 in-flight SDD dispositions are RECORDED" precondition (`docs/upgrades/gentle-ai-v4.md`, the checklist item after the Q39 item).

**Differential for the record (do not drop it):** the 2026-10-11 read-only inventory classified `role-based-subagents` (Phases B–D unstarted) and `peak-hour-routing` (task 1.4 blocked on a host write, config preserved as `rate-limit-fallback.json.new`) as ACTIVE, and `agent-host-tools` as self-marked superseded. The owner's review of the live `sdd-status` is the authority; the earlier classification is retained here so the change of judgement is visible.

**Scope of "abandon":** the changes are NOT implemented. NO change directory is deleted, moved or modified by this decision — in particular `reviewer-relay-transport` carries an `archive-report.md` stating its directory MUST NOT be deleted or moved, and that constraint is unaffected.

**Gate:** the change-set gate for Q39 remains unimplemented (`docs/specs/changeset-tool.md:31-32`); the operator is the only enforcement, and this recorded decision IS that enforcement for this upgrade.

### Q65. Retire `pm-sdd`
- **Status:** DONE-AT-SOURCE (T0–T1 committed and reviewed — `odd/tasks/q65-retire-pm-sdd.md`; commit `5aadb9f`; the decision was RETIRE; two follow-ups remain: the external `sandbox-tools.ts` `READ_ONLY_AGENTS` entry and T1's `R4-migration-vacuous-zero`).
- **Prerequisites:** Q30 (the `workflow-sdd-secure` skill disposition) and Q31 (done); coordinate
  with Q61, which currently lists `pm-sdd` as the SDD route PM.
- **Source:** `odd/tasks/q31-agent-allocation.md` S5b post-code advisory (2026-10-11); Q54's
  host-mutation extension of `pm-sdd`; `odd/tasks/pm-layer.md:24,315`.
- **Description:** gentle-ai v4 retires SDD, so `pm-sdd` has no route left to coordinate. Decide
  retire (default) vs repurpose, then: remove the `pm-sdd` agent block from
  `global-config/opencode.json` (prompt loads `workflow-sdd-secure`); drop `pm-sdd` from the
  orchestrator `permission.task` allows, the guard's coordinator map (`pm-sdd`→`workflow-sdd-secure`),
  the verifier PM lists, and `docs/specs/pm-handoff.md` if named; drop `pm-sdd` from the external
  `sandbox-tools.ts` `READ_ONLY_AGENTS` list; pair the verifier edits with the config change and
  re-pin `VERIFY_SCRIPT_SHA256` (Q31 pattern); correct Q61 to drop `pm-sdd`.

### Q66. Q31 S5a assembler-finding follow-ups
- **Status:** DONE-AT-SOURCE (T0–T2 committed and reviewed — `odd/tasks/q66-assembler-hardening.md`; deployment is pending the owner).
- **Note:** implementation commits `61f85e4` (T1 assembler hardening) and `9d85764` (T2 marker coupling); deployment is pending.
- **Prerequisites:** Q31 (done).
- **Source:** Q31 S5a native review (`review-1633e87da601f9dd`), 2026-10-11.
- **Description:** harden `global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py`
  per six non-blocking findings: `R3-ASSEMBLER-FAILURE-PATHS-UNTESTED` (WARNING — loud-failure paths
  untested: nested markers, unknown kind, empty body, duplicate ids, malformed markers),
  `R3-ASSEMBLER-ATTR-PARSER-FRAGILE`, `R3-ASSEMBLER-ORDERING-HAZARD-UNGUARDED` (replace-after-add /
  add-after-remove), `R4-ATTRPARSE-001`, `R4-EXITCODE-001` (environment failures exit 1 vs the
  documented exit 2), `R4-MARKER-COUPLING-001` (WARNING — the delegation-progress comment pair is
  split across a guarded and an unguarded base section).

### Q67. Retired SDD command detector
- **Status:** DONE-AT-SOURCE (T0–T1 committed and reviewed — `odd/tasks/q67-retired-sdd-command-check.md`; T1 commit `365b718`; native review `review-01bc0dd6dde6aeeb`; `VERIFY_SCRIPT_SHA256` re-pinned `d89dc81a`; deployment pending the owner).
- **Prerequisites:** none.
- **Source:** post-v4-upgrade incident 2026-10-13: `sdd-code.md` survived the v4 sync in the
  deployed `~/.config/opencode/commands/` and stayed live; tracker
  `odd/tasks/q67-retired-sdd-command-check.md`.
- **Description:** add a detect-only `RETIRED_SDD_COMMAND_PRESENT` check to `verify-workflow.sh`
  (a `COMMANDS_DIR`/`WORKFLOW_VERIFY_COMMANDS_DIR` seam, an explicit denylist, and a committed
  `tests/test_retired_commands.py` with four fixtures), re-pinning `VERIFY_SCRIPT_SHA256` LAST.
  Full scope, constraints and acceptance criteria are in the tracker.

### Q68. Sandbox lifecycle ordering in the worker prompts
- **Status:** PLANNED (source not yet written).
- **Prerequisites:** none.
- **Source:** observed incident 2026-10-14 in this repo: a worker called `sandbox_apply` before
  `sandbox_finish`, which reverted the worker to a fresh baseline and discarded all edits; tracker
  `odd/tasks/q68-sandbox-lifecycle-prompts.md`.
- **Description:** make the sandbox lifecycle order (`sandbox_finish` before `sandbox_apply`)
  explicit in the three worker agent prompts (`general`, `gentle-ai-worker`, `odd-apply`) in
  `global-config/opencode.json`, with a committed test and a non-vacuous positive control.
  Tracker: `odd/tasks/q68-sandbox-lifecycle-prompts.md`.

### Q69. Sandbox lifecycle rule in the local worker prompt
- **Status:** DONE-AT-SOURCE (committed; reviewed)
- **Prerequisites:** Q68.
- **Source:** the follow-up recorded by Q68 T1 (2026-10-14); tracker `odd/tasks/q68-sandbox-lifecycle-prompts.md`.
- **Description:** extend the sandbox lifecycle ordering rule to the `gentle-ai-worker-local` prompt in `global-config/opencode.json` (identical text to Q68) and cover all four worker agents in `tests/test_sandbox_lifecycle_prompts.py`; deployment (mirror + restart) remains the owner's action.

### Q70. Dangling prompt include for the frontend writers
- **Status:** PLANNED (not yet investigated).
- **Description:** `frontend-apply` (`global-config/opencode.json:56`) and
  `frontend-apply-local` (`:108`) both set their `prompt` to
  `{file:./prompts/frontend/frontend-apply.md}` plus the search contract, and that include target
  does NOT exist anywhere in the repository (`global-config/prompts/` contains only
  `gentle-orchestrator/`, and a repo-wide search for `frontend-apply.md` matches only the two
  prompt fields). Consequence: those two writers resolve with no frontend-specific prompt body.
  This is OBSERVED (found 2026-10-14 by the Q69 worker); the correct fix (restore the include
  target, inline the intended prompt, or remove the include) is undecided and needs
  investigation.

### Q71. PM-handoff prompt gaps (orchestrator brief schema + PM complete-memory read)
- **Status:** PLANNED (source not yet written).
- **Prerequisites:** none. Part of the Q56 pilot prerequisites.
- **Source:** observed live `pm-odd` smoke tests 2026-10-15 (an incomplete `pm-unit-brief/v1`
  rejected with `BRIEF_SCHEMA_INCOMPLETE`; a mirror-readback claim rejected with
  `MIRROR_COMPLETE_READBACK_UNAVAILABLE`); tracker `odd/tasks/q71-pm-handoff-prompts.md`.
- **Description:** teach the orchestrator prompt the `pm-unit-brief/v1` required-field list (via
  `overlay.md`, assembled into `global-config/opencode.json:590`) and teach BOTH PM prompts
  (`pm-odd` `:1921`, `pm-systematic` `:2041`) the `ctx_memory` `action: "get"` complete-read
  mechanism, with a committed per-agent test and non-vacuous positive controls. Tracker:
  `odd/tasks/q71-pm-handoff-prompts.md`.

### Q72. Tiny-fix route (direct delegation, no PM, no tracker)
- **Status:** PLANNED.
- **Prerequisites:** none. Part of the PM-layer completion work on `chore/pm-layer-completion`.
- **Source:** gentle-ai v4.2.0 INLINE boundary (PR #5530 / issue #5529) cannot map onto a read-only
  orchestrator; tracker `odd/tasks/q72-tiny-fix-route.md`.
- **Description:** add a tiny-fix route for genuinely tiny work (a few lines or a config value) as a
  direct delegation with no PM, no ODD tracker, no advice record and no review slices, available to
  the orchestrator and both PMs. T1 gives the routing guard a tiny-fix exemption (with a paired
  non-vacuous test), adds `gentle-ai-worker` and `gentle-ai-verify` to both PM task allowlists, edits
  the `WORKFLOW.md` `Tiny fix` row and its escalation-only backstop, aligns the three route skills,
  adds the tiny-fix option to both PM prompts, and adds `tests/test_pm_task_allowlists.py`. Tracker:
  `odd/tasks/q72-tiny-fix-route.md`.

### Q73. Native-review slice cadence
- **Status:** PLANNED (T0 tracker + advice + queue entry created; T1 pending). Tracker:
  `odd/tasks/q73-review-slice-cadence.md`.
- **Prerequisites:** none. Part of the PM-layer completion work on `chore/pm-layer-completion`.
- **Source:** observed 2026-10-16 in this repo: medium-risk commits assess `under_budget` with
  `review_due: false`, so the slice accumulates; a later high-risk commit makes the accumulation due
  and `review start` refuses it with `lens_context_budget_exceeded` (`mutation_outcome: not_started`).
  Tracker: `odd/tasks/q73-review-slice-cadence.md`.
- **Description:** add a review-cadence rule (NOT a routing rule) to `WORKFLOW.md`,
  `global-config/skills/workflow-odd-secure/references/odd-and-review.md` and
  `global-config/skills/workflow-route/references/session-decisions.md`: close the accumulated
  medium-risk slice BEFORE a high-risk commit lands, using `--base-ref <last reviewed boundary>`
  scoped to the accumulated slice; forbid `baseRef=<previous commit>`; reject the upstream inline
  path because the read-only orchestrator has no write capability. Pin the rule with `ANCHOR_TOKENS`
  rows and a committed `tests/test_review_cadence.py` with a planted-wrong-prose positive control.
  Full scope, constraints and acceptance criteria are in the tracker.

### Q74. Tiny-fix writer model independence
- **Status:** PLANNED.
- **Prerequisites:** none. Part of the PM-layer completion work on `chore/pm-layer-completion`.
- **Source:** owner decision 2026-10-15 narrows writer-model independence to the tiny-fix route, where
  the orchestrator directly dispatches the writer; tracker `odd/tasks/q74-writer-model-independence.md`.
- **Description:** re-point the tiny-fix writer from `gentle-ai-worker` (DeepSeek) to `general`
  (`openai/gpt-6-luna`) across every route surface; add and pin the orchestrator↔tiny-fix-writer
  independence clause; add `tests/test_model_independence.py` with a same-family positive control.
  PM-dispatched writer work is already independent because PMs run `openai/gpt-6.1-sol` and dispatch
  `odd-apply` (DeepSeek), so do not re-point those models. Record PM↔`gentle-ai-verify` Sol sharing
  and Astra-alias collapse as waivers. Full scope, constraints and acceptance criteria are in the
  tracker.

### Q75. Tiny-fix permit race: bind the permit to the intended child
- **Status:** PLANNED (T0 tracker + advice + queue entry created; T1 pending). Tracker:
  `odd/tasks/q75-tiny-fix-permit-race.md`.
- **Prerequisites:** none. Part of the PM-layer completion work on `chore/pm-layer-completion`.
- **Source:** Q72 T1a review finding `R3-tiny-fix-permit-race`: the first `session.created` from a parent consumes its pending tiny-fix permit using only `parentID`; two independent pre-code advisors graded this a BLOCKER. See `odd/advice/q75-tiny-fix-permit-race.md`.
- **Description:** bind the one-shot permit to the intended writer using a parent-keyed candidate set plus an observed child-agent match; normalize `-local` and `-astra` writer variants; cover non-writer-first sibling races and the PM-dispatched path. Resolve whether child `chat.message` events arrive with the agent, or fail closed. Preserve one-shot, TTL, own-session-only behavior and all five existing `1d` cases. Correct or cover Q72's erroneous claim that an Astra permit case exists at `tests/routing-guard/routing-guard.test.ts:1056-1061` (that range is the PM adapter alias test).

### Q76. Gemini API advisor route (Antigravity substitute) and the Antigravity Argon/Flash split
- **Status:** IMPLEMENTED on `feat/gemini-api-advisor-route` (Claude Code, at the owner's request,
  2026-10-17). Tracker: `odd/tasks/q76-gemini-api-advisor-route.md`. Pending items:
  - pre-code advice from the `advisor-*` lanes (owner dispatch from the OpenCode TUI);
  - native review of the T1 commit on the `asi-review-*` lanes (`review assess`: high, review due);
  - verifier mirror and restart.
- **Prerequisites:** none. Stacked on `chore/pm-layer-completion` for Q72's allowlist test and the
  advisor `noFallbackAgents` entries.
- **Source:** owner request, 2026-10-17. Google API credits are a pool separate from the
  Antigravity subscription, and Argon is now on that subscription too.
- **Description:**
  - In-OpenCode `advisor-gemini-pre`/`-post` (Argon, delegate-only) and `advisor-gemini-evidence`
    (Flash, sandbox-only) supply Antigravity's half of the pair under the `gemini-api-substitute`
    rule (`WORKFLOW.md`).
  - The verifier checks this with `geminiAdvisorRouteFailures`; `tests/test_gemini_advisor_route.py`
    runs that check against fixtures.
  - Antigravity gets `argon_advisor` and `evidence_collector` custom agents through the
    `changesets/q76-antigravity-agents` change set. See `docs/gemini-api-route.md`.

### Q77. PM mirror readback under Magic Context 0.46
- **Status:** PLANNED.
- **Prerequisites:** none. Part of the PM-layer completion work on `chore/pm-layer-completion`.
- **Source:** owner-confirmed Magic Context 0.46 subagent tool surface and two live `pm-odd` BLOCKED results (2026-10-17); tracker `odd/tasks/q77-pm-mirror-readback.md`.
- **Description:** make `docs/specs/pm-handoff.md`'s mandatory tracker/mirror readback achievable without registering `ctx_memory` for subagents (removed by design). U1 adds `tracker_sha256` and `mirror_sha256` to the brief, has the PM hash the committed tracker file independently and compare it with the supplied tracker hash, specifies BLOCKED outcomes, records the comparison/method in the result envelope, preserves metadata-worker mirror-write ownership, and adds a schema test. U2 updates the orchestrator overlay, both PM prompts and regeneration chain. The live runtime falsifier is HOST-ONLY. Full scope and acceptance criteria: `odd/tasks/q77-pm-mirror-readback.md`.

### Q78. host_review_materialize permission for the ce:review pipeline
- **Status:** IN PROGRESS. T1 DONE-AT-SOURCE (commit `2800586`); native review `review-9acb2006667ef984` approved and acknowledged, authority burned. Metadata record and R4-002/R4-004 follow-ups are in progress.
- **Prerequisites:** broker-side `host_review_materialize` registration and the `ce:review` helper unit in `agent-sandbox-integration`; until installed, the permission is inert.
- **Source:** owner decision 2026-10-17; pre-code advice in `odd/advice/q78-host-review-materialize.md`.
- **Description:** grant explicit `allow` under `permission` to `gentle-orchestrator`, `pm-odd`, and `pm-systematic`, with a global `deny` default; add the PM `tools` map entries where applicable; enforce the exception, exact per-agent grants, positive controls, and negative agent sweep in `verify-workflow.sh`; re-pin `VERIFY_SCRIPT_SHA256` last. This is the advisory `ce:review` helper path, not native `asi-review-*`. Full scope, constraints and checks: `odd/tasks/q78-host-review-materialize.md`.

### Q79. Deterministic mirror-write ownership
- **Status:** SOURCE/PREDICATE COMPLETE for D/E (2026-10-23); units A/B/C are source-complete but NOT natively reviewed. D/E source was present; execution checks: prompt-source 29 OK including the real extracted PY heredoc equality control, PM handoff 26 OK, PM layer 13 OK, anchor 11 OK (39 anchors/99 tokens), full Python 244 OK (zero failures/errors), `bash -n` rc 0, JSON parse rc 0; extracted D predicates produced the expected mismatch codes, and the actual E heredoc returned rc 0/5/2/1/4 for real/mutation/invalid-config/assembler-failure/timeout. Explicit limitation: extracted/stubbed predicate proof only; the full host verifier was NOT run, the live synthetic mirror falsifier is pending, the deterministic mirror tool is unimplemented, and mirror write/verification was NOT performed. The A/B/C native review gap remains OPEN. Q56 counted unit 3/10 (2026-10-22); metadata commit PENDING-COMMIT.
- **Prerequisites:** none. Part of the PM-layer completion work on `chore/q72-t1b-tiny-fix-contract`.
- **Source:** owner decision 2026-10-18: a DETERMINISTIC host tool owns tracker-mirror write and verify; explicitly retract Q77's metadata-worker ownership decision. Magic Context 0.46 removed `ctx_memory` from subagents by design.
- **Description:** correct the contradictory `pm-handoff.md` ownership contract and `metadata_work_unit` envelope semantics; update the orchestrator overlay and its `## Key Learnings` chain, `WORKFLOW.md`, and `odd-and-review.md`; complete the seven-step prompt regeneration atomically; add the `ctx_note` residue guard, F13 embedded-prompt/assembler verifier check, correct `systematicMemoryPolicy`, and resolve the `explore` grant. If the deterministic host tool has not landed, record that mirror write is not performed rather than implying a successful write/readback. Explicitly retract Q77 in `CLAIM-RETRACTIONS.md`. Full scope and checks: `odd/tasks/q79-mirror-write-ownership.md`; pre-code advice: `odd/advice/q79-mirror-write-ownership.md`.

### Q80. Guard: advisory-strategy unit C
- **Status:** BLOCKED (resume after PM-layer completion).
- **Prerequisites:** PM-layer completion (Q56-Q61).
- **Source:** `odd/tasks/q72-tiny-fix-route.md:38` (currently listed only as out of scope); pre-code advisory findings recorded in the audit that identified this gap.
- **Description:** GUARD work, to be resumed after the PM layer. Resolve the 12 advisory findings before implementation: (1) `ROUTE_STAGES` has no post-code stage; (2) `ce:review` replacing post-code advisors is not representable; (3) “end of ODD” does not survive the review-cadence slice rule; (4) warning-only enforcement implies a documentation-only obligation; (5) the verifier checks prose presence, not behaviour; (6) the external-lane skip clause cannot be recorded; (7) the on-demand clause has no decision criteria; (8) before-commit conflicts with end-of-ODD sequencing; (9) vacuous-pass traps require positive controls; (10) identify the tests and anchor rows to change; (11) reconcile ownership disagreement among `WORKFLOW.md`, `overlay.md`, and `pm-handoff.md`; (12) distinguish post-code advice from the staged reviewability receipt.

### Q81. Guard: record skipped external-advisor use
- **Status:** BLOCKED (resume after PM-layer completion; design required).
- **Prerequisites:** PM-layer completion (Q56-Q61).
- **Source:** `WORKFLOW.md:507-523,533`; the audit found no skip field in `odd/advice/**`, the brief schema, or the result envelope.
- **Description:** Design how to record a SKIPPED external-advisor use. `selection.rule` currently names selection rules only, and a missing advice record is a blocked gate, never a silent skip; define and test an explicit skip representation and its required rationale/evidence rather than treating absence as skip.

### Q82. Guard: add ODD post-code and review stages
- **Status:** BLOCKED (resume after PM-layer completion).
- **Prerequisites:** PM-layer completion (Q56-Q61); coordinate with Q28.
- **Source:** `global-config/plugins/lib/routing-guard-helpers.ts:74-110` (`workflow-odd-secure` currently has `advice` and `tracker` stages); `docs/TODO.md` Q28:429-430; `odd/tasks/routing-guard-keys.md:114`.
- **Description:** Add a post-code stage to ODD `ROUTE_STAGES` and make `ce:review` satisfy an ODD review stage where applicable. Q28 mentions a guard stage but no item owns it, and the `ce:review` half is unrecorded; reconcile this with the current description of ODD review as a CONTINUOUS STATE, not an artifact.

### Q83. Guard: reconcile the three writer lists
- **Status:** BLOCKED (resume after PM-layer completion).
- **Prerequisites:** PM-layer completion (Q56-Q61); coordinate with Q28.
- **Source:** `global-config/plugins/lib/routing-guard-helpers.ts:18-19` (`ODD_SPECIALIST_WRITERS`, 13 writers); `global-config/skills/workflow-odd-secure/SKILL.md:15` (names only `odd-apply`); `docs/specs/routing-guard-q03.md:46` (Q28 assignment by name).
- **Description:** Enumerate and reconcile the guard's 13 `ODD_SPECIALIST_WRITERS`, the ODD route skill's `odd-apply` writer naming, and `pm-odd`'s task allowlist. Q28 assigned this drift by name, but no item records the three lists or their comparison.

### Q84. Reconcile post-code advice sequencing drift
- **Status:** BLOCKED (resume after PM-layer completion).
- **Prerequisites:** PM-layer completion (Q56-Q61).
- **Source:** `WORKFLOW.md:471,520`; `docs/specs/pm-handoff.md:23`; `global-config/prompts/gentle-orchestrator/overlay.md:199`.
- **Description:** Reconcile the three normative surfaces: `WORKFLOW.md` and `pm-handoff.md` say post-code advice runs BEFORE the work-unit commit, while the orchestrator overlay says it runs against the COMMITTED implementation snapshot before the native review entry. Record the agreed sequence and keep all three surfaces consistent.

### Q85. ce:review pipeline host permissions

- **Status:** DONE for config, verifier and source verification. Broker-side registration and runtime effect remain unverified.
- **Prerequisites:** broker-side registration of `host_review_pipeline_run` and `host_review_persist` must be confirmed before runtime effect is claimed.
- **Source:** `odd/tasks/q80-review-pipeline-host-permissions.md`.
- **Description:** Grant `host_review_pipeline_run: allow` and `host_review_persist: ask` to `gentle-orchestrator`, `pm-odd`, and `pm-systematic`; retain global `deny`, verifier enforcement, per-agent controls, PM tool-map coverage, and a negative sweep. No branch switch; owner-authorized counted-unit PM metadata commit (worker never commits).
- **Verification (2026-10-22):** `python3 -m json.tool global-config/opencode.json` exit 0 (stderr empty); 43 agents total, three coordinators grant `allow`/`ask` as specified, remaining 40/40 permission maps inspected with zero explicit either key (offenders `[]`); `bun tests/test_review_pipeline_permissions.js` exit 0 with all extracted verifier assertions and reverted-fixture positive controls passing; `bash -n verify-workflow.sh` exit 0 (no output); `python3 -m unittest discover -s tests` exit 0 — 244 tests OK, zero failures/errors, no child `node` denial; verifier pin canonical literal and computed script SHA both `28ff39379aee7460bce784386e62c83bf5f51aea2b93074e2f35230fa299e7ad`; extracted `read_verify_script_pin` regex matches the real source plus single-quoted and double-quoted 64-hex fixtures; focused rerun `python3 -m unittest tests.test_orchestrator_prompt_source -v` exit 0 — `Ran 29 tests`, `OK`, zero failures/errors, including `test_verifier_script_pin_matches_its_own_regex` (no full-suite rerun; correction round 1/1, 2026-10-23); deployed plugin/pin not probed. Q56 counted unit 1/10 (2026-10-22); metadata commit 916a4f5e3291f42507bfb47b429bcea5c6d65e4c; assessment passive (3 paths / 33 lines, review_due=false). Broker registration remains a prerequisite for any runtime claim.

### Q85a. PM unit-start deterministic anchor
- **Status:** DONE (source already complete; no source change in the metadata verification unit `q85a-pm-verify-u1`; metadata commit 1ab7647be851e2930c23023c87daa42564086066; assessment passive (4 paths / 29 lines, review_due=false)). Current focused checks: PM handoff 26 OK; PM layer prompts 13 OK including 7 PositiveControls; orchestrator prompt source 29 OK; full Python suite `Ran 244` OK with zero failures/errors/skips; `bash -n verify-workflow.sh` and `python3 -m json.tool global-config/opencode.json` exit 0. Current prompt SHA-256 `521796dfbfc71a125e49b8bbd8127de7197a491b12a0ea8bd942c29de64a046b` (59,950 bytes); `74838e16cf689f8c3f862dc56d3d9dc22f925dab8b8dcabc4d849bf96a2dd2ac` is HISTORICAL, not current. The owner-authorized current-state lifecycle wording records that the applied source is present and verified, while the original `sandbox_finish`-before-`sandbox_apply` sequence is not independently re-verifiable from current artifacts. Q56 counted unit 2/10 (2026-10-22).
- **Prerequisites:** Q79 deterministic host-tool mirror ownership contract.
- **Description:** replace the PM's unavailable `tracker_sha256` comparison with a read-verified
  tracker byte/character count, literal last-line text, and feature-branch HEAD SHA. Suspend hash
  duties until the deterministic host tool lands; see `odd/tasks/q85-unit-start-anchor.md`.

### Q86. Record the ce:review contract parameters
- **Status:** IN PROGRESS — unit `q86-ce-review-contract-u1` (documentation) SOURCE COMPLETE at `83bdeeab3d9f3bf430c54d4ffbb00e097e1856cd`; PM accepted PM01–PM05; metadata closure PENDING-PM-COMMIT/assessment (assess from retained boundary `77b4df8f1955fb8bc9255c3cde6a7246be5fed87`). Open follow-ups remain; whole Q86 is not solved.
- **Prerequisites:** none.
- **Source:** external agent `agent-sandbox-integration` supplied the contract parameters for the
  `ce:review` helper; tracker `odd/tasks/q86-ce-review-parameters.md`.
- **Description:** current documentation contract revision (unit `q86-ce-review-contract-u1`):
  sixteen NORMATIVE parameters with stable, named `CEV-*` refusal codes now live in `WORKFLOW.md`
  and the tracker; every refusal names its code and the applicable field, cap, observed size, path,
  or policy detail. Reviewer delivery and helper byte custody are BOTH UNRESOLVED; no mechanism is
  selected or claimed solved. The ASTRA caller-alias question remains OPEN and uninvestigated. Q56
  counted unit 4/10 (2026-10-23): source committed at `83bdeea`; PM accepted PM01–PM05;
  correction_rounds_used 1; source assessment medium / `under_budget` / `review_due=false` with
  boundary `77b4df8` retained. Metadata commit and assessment are PM-owned and pending. The
  former reviewer-delivery RESOLVED claim is retracted in `CLAIM-RETRACTIONS.md`.
- **Deferred follow-up (not this unit, not authorized executable work):** drift-guard test for the
  contract codes; prerequisites are this contract revision and an explicit future code
  authorization.

### Q87. Finite verification budget by task type
- **Status:** IN PROGRESS — SOURCE COMPLETE (U2a + U2b); deployment/live activation not performed.
  Planning unit `q87-verification-budget-plan-u1` is complete. U2a
  `q87-verification-budget-src-u1` is source-committed as
  `30f76652d6fcdfe97999ffd87bff643cb8e964df` (7 paths, 389 authored lines, 67564 patch bytes);
  owner decision 2026-10-21 advanced the source reviewed boundary to `30f7665` without native
  review. U2b `q87-verification-budget-src-u2` is source-committed as
  `5a8a8ab191bb5fcfcccdf810f1d46e003fc52ac5` (11 paths, +149/-7 = 156 changed lines; 154 authored
  lines excluding the generated embedded-prompt hunk, 37667 authored patch bytes). Source
  assessment: medium, under_budget, consumed=false, review_due=false at base `415009c...`; this is
  not native review or approval and remains historical. Owner decision 2026-10-21 advanced the
  reviewed boundary from `415009c` to `8437aa3`, the prior metadata/final HEAD at disposition,
  closing the U2b medium slice without native review; `8437aa3` is not this metadata unit's
  commit. Deployment and live activation are separate and were not performed. Tracker
  `odd/tasks/verification-budget.md`; advice `odd/advice/verification-budget.md`.
- **Prerequisites:** U2a source commit and its metadata closure; both are done. U2b records the
  post-code static-diagnostic-order rule and the prompt/overlay scope. Folds Q88
  (overlay/prompt generation) — Q88 is not a separate queue item and no new queue ID is created.
- **Source:** owner directive 2026-10-21 (finite advice/verification by task type; static
  diagnostics in the first post-code pass); Q59 cycle evidence; the Q84 post-code-sequencing drift.
- **Description:** define 0/one/one pre-and-post phases plus an optional verifier by task type over
  the existing six route classes; a per-unit maximum of one initial writer plus one correction
  writer; a docs allowlist by actual diff that fails closed; and a `correction_rounds_used` recorder.
  The local-tier writer takes exactly ONE changed file per writer Task while cloud writers may batch
  a coherent multi-file unit. Subunits: `q87-verification-budget-plan-u1` (complete);
  `q87-verification-budget-src-u1` (U2a, source committed `30f7665`); U2b
  `q87-verification-budget-src-u2` (SOURCE COMPLETE `5a8a8ab`: `overlay.md`, assembled
  `global-config/opencode.json`, prompt regeneration, `CURRENT_PROMPT_SHA256`, normative ledger,
  `advisor-gemini-post` sequencing drift, and the post-code static-diagnostic-order clause in
  `WORKFLOW.md`/`docs/specs/pm-handoff.md` plus overlay wording), folding Q88 and the Q84
  sequencing fold with no new queue ID. Deployment/live activation remain separate.
- **Planning overlay (2026-10-23, Q90 decision 2):** on planned/gated routes the post-code
  advisory actor is the PLANNER, replacing the PM `advisor-*-post` closure; the finite matrix is
  unchanged and the docs exemption stays intact. No advice is added for true docs units. This
  overlay is planning-only: not implemented, deployed or live.

### Q89. Multi-agent v2 phase 1 — inert plan-task permissions
- **Status:** DONE for phase 1 (inert permissions; source and metadata complete). Planning
  `q90-phase1-plan-u1` committed as `28d4a4368e0e3925069208ce7775b73c84c4922a`; T2 source
  `473c9cd85db1c70122ed5ea007241fce10be9f59` (7 additions, 0 removals; config blob
  `854e5c4...`). Owner decision (2026-10-23) closed the T2 medium slice and advanced the reviewed
  boundary from `b154ef3a33ce692bba5218c0547def92755dc371` to
  `22132adc686629cceaa7b32e469c5ec10d009e2a` (metadata). The prior owner-supplied assessment is
  medium/`under_budget`, 5 paths / 287 changed lines. This is owner closure, NOT native review or
  approval. Deployment/restart and consumer loading are the owner's separate host action and
  remain UNVERIFIED; the tools are inert and not live. Tracker
  `odd/tasks/multi-agent-v2-phase1.md`; advice `odd/advice/multi-agent-v2-phase1.md`. One metadata
  factual correction round (round 1 of 1) is historical; source bytes unchanged. Metadata identity
  and assessment are PM-supplied; no independent verification is claimed here.
- **Prerequisites:** committed input `docs/contracts/multi-agent-v2-workflow-prompt.md` (commit
  `92a2a38`, base `41c293de5365c861242ed78999a3fbc1d565e5fb`); RDD enabled (global); current
  `global-config/opencode.json` permission blocks. Phases 2-4 are OUT OF SCOPE: they belong to
  agent-sandbox-integration and require separate authorization.
- **Source:** owner-supplied multi-agent v2 contract and dispatch brief, 2026-10-23.
- **Description:** phase 1 only — add inert permission entries for `host_plan_write`,
  `host_gate_verdict` and `host_task_mark`: global deny after `host_plan_append`; `pm-odd` and
  `pm-systematic` `host_plan_write`/`host_task_mark` ask after `host_sandbox_result_install`.
  No tool implementation, no tools-map key, no orchestrator grant, no `host_gate_verdict` PM
  grant, and no `WORKFLOW.md`/tracker-rule/plan-root-protection change. The prompt is committed
  input, not output. The tracker records the exact line positions, author split, tool contracts
  and T2/T3 acceptance.
- **Count:** Q56 counted unit 5/10, explicitly authorized by the dispatch brief even though
  earlier planning units were not counted.

### Q90. Multi-agent v2 workflow config (handover 2026-10-19)
- **Status:** IN PROGRESS — T1 COMPLETE: source
  `114366b35651316e00c972f71f723b7804fcae4c`; metadata
  `dfbeb296af708f02151d7444d8d76431606abff6`. Final PM assessment completed at retained boundary
  `22132adc686629cceaa7b32e469c5ec10d009e2a`: medium/`under_budget`. T2 COMPLETE for
  decisions/evidence (2026-10-23), metadata closed at `2f196b6`. T3a1 COMPLETE: source
  `b89f5a00d0bc1412f672954aaa7c1810c7a34092`; native review `review-1ca5500bc130a1cf` approved
  and acknowledged, authority burned. T3a2 COMPLETE: four commits from `2173738` to source
  `77ef08af7c376386b24a62e26efc6809b9753bdf`; approved lineage `review-bff8f73a89ebffa5`;
  four deferred WARNINGs. T3.0 model/role PLAN COMPLETE in the tracker (planning only; no source);
  the owner-authorized 2026-10-24 one-commit docs review-size exception is recorded there only
  and changes no source decision; T3.0.3a PM reassignment `q90-pm-reassign-u1` COMPLETE: source
  `455a769219795e57769488210ee89ba8d67ac63f`, 15 paths / 400 authored lines, owner-supplied review
  `review-f6f31e924064dec0` approved/acknowledged, deployment PENDING; the remaining
  T3.0.1-T3.0.9 slices are PLANNED; T3b (`q90-t3b-planner-u1`) is SOURCE STAGED, not committed or
  deployed; owner decision 2026-10-24 closes `455a769..416f289` metadata by OWNER DECISION, NOT
  native review, with reviewed boundary `416f289`; then T3c (permission-only), T3d (residual), T4-T6. Current
  native-reviewed source boundary `77ef08a`; PM-observed host branch HEAD `36d461f` on
  `chore/multi-agent-v2-phase1`. Tracker `odd/tasks/multi-agent-v2-queue.md`; handover
  `docs/handoffs/2026-10-19-multi-agent-v2-workflow-config.md`. No deployment is claimed.
- **Prerequisites:** T1: none (owner authorization 2026-10-23). Q89 phase 1 is a completed, inert
  prerequisite; its tools are not live. Phases 2-4 remain external to this repository. T3.0 has NO
  `agent-sandbox-integration` dependency and precedes T3b; the external host tools, session and
  seat-independence checks remain gates for the slices that need them. The pending medium metadata
  slice from `77ef08a` must be closed by native review or an explicit owner boundary before the
  first high-risk T3.0 source unit; `under_budget` alone does not close it. `minimax-m3.1-flash`
  hang, session and Go-allowance acceptance remain future gates for its promotion to a live seat.
- **Owner decisions (2026-10-23, corrected; planning direction, not live deployment and not a
  change to current policy):**
  1. Review returns to the orchestrator: it dispatches FOUR lenses and the provider-selected
     refuter/validator, and keeps assessment, consent and acknowledgement. The PM dispatches no
     review lanes. The earlier 2026-10-23 "PM runs the lenses" decision is SUPERSEDED the same
     day; Q58's restriction is restored. The same-day Q57/Q58 forward statements that the PM runs
     the lanes are superseded; their historical sections are untouched.
  2. The orchestrator first drafts the plan; the PM reads the draft and hands it to the Planner
     with its own suggestions, passing NO advice; the Planner finalises it, calls ALL pre-code
     advisors itself plus its own read-only Luna evidence agent, runs post-code advisory, and
     issues BOTH gate verdicts. No additional advice for true docs; Q87's forward post-code actor
     is the Planner.
  3. PM `glm-5.3-flash` high, fallback `qwen3.8-flash` high; Planner `openai/gpt-6.1-sol` high,
     xhigh for Gate 1 on multi-step/high-risk. Independence across orchestrator, PM, Planner,
     apply and review models. The new planner-evidence agent uses `openai/gpt-6-luna`; sharing
     Luna with the Tiny writer `general` and `jd-fix-agent` is an explicit agreed exception,
     accepted because Tiny is passive/ungated.
  4. The orchestrator does plan drafting + review dispatch, plus assessment/consent/acknowledgement.
     `host_plan_write` is ask-gated for BOTH the orchestrator and the Planner, with NO no-ask
     exception (T2 decision (b), RESOLVED); PM suggestions are messages, never plan writes. The PM
     loses relay AND advisor dispatch.
  5. Q89 phase 1 is a completed prerequisite; phases 2-4 remain external to this repository,
     unchanged.
  6. Item 8 is RESOLVED: advice is evidence; the gate verdict is the approval act. On gated
     routes the Planner issues PASS/REFINE/ESCALATE after reading the plan revision, the pre-code
     advice it called, the post-code advice it ran, the raw lens findings, and the evidence
     commit assessment tier, phase-appropriate (Gate 1 does not imply post-code evidence exists).
     PASS technically approves the change and authorises the PM tick, NOT delivery, deployment or
     acceptance. Non-gated routes take advice as evidence only, with no verdict.
  7. T3.0 model and role assignment comes FIRST, before T3b, with no `agent-sandbox-integration`
     dependency. Former `minimax-m3` seats move to `opencode-go/minimax-m3.1-flash` (reliability
     `xhigh`; advisors `high`); this supersedes the earlier no-seat/open R3 planning text but is
     NOT a hang/session clearance. Owner ruling on planning basis: "Planning basis: canonical
     `global-config/`; the deployed file is stale because T3a1/T3a2 are not deployed. The
     implementation unit must re-read the deployed file after the mirror and record any source-vs-live
     difference; it must not edit the live file directly." Source-to-mirror remains authority. The
     full source-vs-target table, 12-lens mapping, variant mechanics, fallback fix graph and atomic
     slices live in the tracker; the still-pending owner mappings there are not settled policy.
- **Pipeline (exact):** orchestrator drafts plan -> PM reads/suggests -> Planner finalises, calls
  pre-code advisors and Luna evidence agent -> Gate 1 -> writer implements -> PM closes unit ->
  orchestrator dispatches four post-commit lenses, Planner runs post-code advice -> Gate 2 -> PM
  ticks -> orchestrator assesses/acknowledges -> owner approves delivery.
- **Review terminology:** FOUR lenses — R1 risk `qwen3.8-flash` `high`, R2 readability
  `kimi-k2.7-code` forced thinking, R3 reliability target `minimax-m3.1-flash` `xhigh` with output
  ≥ 32768 (owner direction 2026-10-23; `minimax-m3` remains excluded and M3.1 promotion still
  needs session/hang/Go-allowance acceptance), R4 resilience `glm-5.3-flash` `high` — PLUS the
  provider-selected refuter `mimo-v2.6-flash` default thinking (output ≥ 32768) and validator
  `claude-haiku-5-5` `high`. Targets are planned, not live.
- **Units:**
  - **T1 — queue revision (COMPLETE):** Q90, the Q57-Q60 forward lines, the Q87 planning overlay,
    Q91 and the router row. Source `114366b`; metadata `dfbeb29`; final assessment
    medium/`under_budget` at retained boundary `22132ad`.
  - **T2 — readiness (COMPLETE for decisions/evidence, 2026-10-23):** decisions (b), (d), (e) and
    (f) closed. (b) `host_plan_write` ask-gated for BOTH orchestrator and Planner, no no-ask
    exception; PM suggestions are messages, never plan writes. (d) all named model IDs resolve,
    evidenced by THREE owner-reported host `opencode models` runs: Go pool plus
    `openai/gpt-6.1-sol` (+ -fast, -ultrafast), `openai/gpt-6-luna` (+ -fast), and the Google
    models `google/gemini-flash-latest`, `google/gemini-4-argon`, `google/gemini-3.8-flash`;
    shared-pool variants exist but are not the named providers. (e) `minimax-m3` is excluded
    fail-closed from EVERY native review seat until the hang is proven absent; R3 has no
    confirmed seat, `minimax-m3.1-flash` is not promoted without session/hang checks, and T3d
    chooses from `claude-sonnet-5-5`, `minimax-m3.1-flash`, `muse-spark-1.3-contributor` or
    `step-5-preview`. (f) actor slices T3a-d, each atomic across `opencode.json` task
    permissions, guard `ROUTE_STAGES`/helper lists, route skills and its own `WORKFLOW.md` lines,
    with no owner size exception and no intermediate guard-denies/skill-allows state. Host-tool
    built/tested, session and independence checks remain future implementation gates, NOT
    completed by T2.
  - **T3a — orchestrator slice (T3a1 and T3a2 COMPLETE, high risk):** T3a1 bounded the
    plan/test tools and ask-gated `host_plan_write` across the three policy surfaces plus
    orchestrator `WORKFLOW.md`; source `b89f5a0`, 11 paths, 400 authored changed lines / 48,326
    bytes; 77 focused tests plus Bun controls; native review `review-1ca5500bc130a1cf` (target
    sha256:3bb686d938a115b6330bb81f9da519f06bab7c2562e74642e79ab4c5a6e6f271) approved, four
    lenses acknowledged, authority burned; three informational/non-blocking reviewer claims
    recorded below, no correction opened. T3a2 added review-dispatch ENFORCEMENT, not actor
    migration, at source `77ef08a` with approved lineage `review-bff8f73a89ebffa5`; four
    WARNINGs are deferred (below).
  - **T3a1 reviewer claims (informational/non-blocking; deferred follow-up, not endorsed or
    implemented):** R4-1 resilience WARNING `verify-workflow.sh:2809-2817` (proof `:2836`) —
    `host_test_run` has a grant sweep excluding only orchestrator but `host_plan_write` has no
    equivalent verifier/Python/Bun sweep, so future non-orchestrator not-deny plan grants would
    pass gates; existing PM plan-write asks are intentionally preserved by source scope. R4-2
    resilience SUGGESTION `tests/test_review_pipeline_permissions.py:709-715` — `run_controls`
    skips only `PermissionError`, and missing Bun falls back to `'bun'` and raises unhandled
    `FileNotFoundError` instead of skipping. R2-001 readability SUGGESTION
    `global-config/prompts/gentle-orchestrator/overlay.md:57` — "narrowly defined, pre-registered"
    `host_test_run` qualifier names no registry, authority or allowed-test list, so maintainers
    cannot determine the permitted set from the contract alone. `host_test_run` remains inert
    until the host tool ships. No `minimax-m3.1-flash` promotion is attached to T3a1; that
    substitution belongs to T3.0, not T3d.
  - **T3.0 — model and role assignment (PLAN COMPLETE; source PLANNED, high risk):** the tracker
    holds the complete current-source-vs-target seat table, variant mechanics, fallback fix graph,
    12-lens advisor mapping and per-slice AUTHORED ESTIMATES (not measured). Atomic subunits, each
    carrying config, matching verifier edits, digest pin and exact tests in one commit, in this
    order: T3.0.1 `q90-t30-variants-u1`; T3.0.2 `q90-t30-core-seats-u1`; T3.0.3a
    `q90-t30-pm-u1`; T3.0.3b `q90-t30-judges-u1`; T3.0.4a `q90-t30-fallback-writer-u1`;
    T3.0.4b `q90-t30-fallback-closure-u1`; T3.0.5a `q90-t30-review-risk-resilience-u1`; T3.0.5b
    `q90-t30-review-readability-reliability-u1`; T3.0.5c `q90-t30-review-refuter-validator-u1`;
    T3.0.6a `q90-t30-advisor-design-map-u1`; T3.0.6b `q90-t30-advisor-deps-map-u1`; T3.0.6c
    `q90-t30-advisor-testing-map-u1`; T3.0.6d `q90-t30-advisor-security-map-u1`; T3.0.6e
    `q90-t30-advisor-integration-map-u1`; T3.0.7a `q90-t30-advisor-scope-ux-u1`; T3.0.7b
    `q90-t30-advisor-data-u1`; T3.0.7c `q90-t30-advisor-performance-u1`; T3.0.7d
    `q90-t30-advisor-concurrency-u1`; T3.0.7e `q90-t30-advisor-resilience-u1`; T3.0.7f
    `q90-t30-advisor-bug-hunt-u1`; T3.0.8 `q90-t30-escalations-u1`; T3.0.9
    `q90-t30-integration-audit-u1`. Each ID appears once here; each depends on its predecessor and
    the tracker holds the exact prerequisites. First prerequisite: close the pending `77ef08a`
    metadata slice by review or owner boundary. No `agent-sandbox-integration` dependency; the
    existing current actor owns advice until T3b and NO Planner permission is preinstalled. The
    owner mappings still listed as pending in the tracker must be settled before the affected
    source slice.
  - **T3.0 Kimi removal (`q90-t30-kimi-removal-u1`, owner-directed 2026-10-24):** five Kimi
    primaries and the DeepSeek maintainability-post remapped to MiniMax/Qwen/Ling with the exact
    variants; readability unchanged; inactive Kimi exact policy removed and three dormant
    completeness policies added. Prerequisite: T3.0.1 staged boundary and pre-advice; consumer
    variant support, model availability, M3.1 hang/session/Go allowance and runtime remain
    UNVERIFIED gates. Correction round 1/1: the initial fallback detector did not prove target
    values (source/target control vacuous), so it is corrected and now also scans
    `systematic.jsonc` read-only; the corrected live scan finds zero executable Kimi references.
    Initial RED 7 / GREEN 84 remains HISTORICAL INITIAL, not strengthened-detector evidence.
    SOURCE COMPLETE at implementation commit
    `ee2dab0f2c24f3daaf34bf50ba4633557fbf1b19` (8 paths; independently counted 587 authored
    lines = 555 additions + 32 deletions; host commit confirmed 555/32; verifier session
    `ses_e913c44faffeUx5Yfi8UYWMLav`, verifier-reported latest snapshot
    `6661e88c45c9f8f3be1b07e718a3c2bd66cc6286` (parent `decd167`; not present in this checkout);
    writer raw patch 51,008 bytes,
    NOT independently verified after the exact refusal `argv item contains shell metacharacters`
    was not retried). Exact implementation assessment: status 0,
    `gentle-ai.review-assessment/v1`, risk medium, reason `configuration_change`
    (`global-config/opencode.json`), `under_budget`, 8 paths / 587
    lines, `consumed=false`, `review_due=false`, candidate base
    `decd167b8b01e0d4fcd41653840f817d607c7859` retained as the last reviewed boundary; it
    approves, advances and closes nothing and starts no lineage. V1-V4 are CLEARED. Latest
    independent execution:
    22 tests (14+8), 0 failures/errors/skips; the earlier 88-check result is historical.
    `aft_inspect` is PARTIAL; `tests/test_model_independence.py:72:58` optional
    `specialist.group` is recorded/inferred pre-existing, with no overall clean claim.
    `review-642f4745d7f6d6fe` is owner-designated SUPERSEDED, not approved or closed. Owner
    decision 2026-10-24: native review runs AFTER owner deploy, so reliability uses
    `opencode-go/minimax-m3.1-flash`; deploy/restart were NOT performed, all
    runtime/consumer/model-availability/M3.1 gates remain UNVERIFIED, and `WORKFLOW.md` policy is
    unchanged. Source assignments only: reliability + `asi-review-reliability` MiniMax `xhigh`;
    integration-pre MiniMax `high`; integration-post/testing-post Qwen default with `variant`
    OMITTED; maintainability-post Ling default with `variant` OMITTED; readability Muse `high`
    unchanged; future `advisor-ux-pre` MiniMax `high` only when created at T3.0.7a; inactive
    Kimi exact fallback removed and evaluator exclusions preserved. The five seats the owner
    called `live` are source assignments only because deployment was not performed. RDD is
    enabled/global; correction counter remains 1/1. This metadata closure is class
    `documentation` under the simple-docs allowlist (route `workflow-odd-secure`) and changes
    exactly this tracker, `docs/TODO.md` and `ROUTER-LOG.md`; the PM owns the commit. Q90 remains
    IN PROGRESS.
  - **T3.0 normal-row drift + validator migration (`q90-t30-advisor-drift-u1`, owner-directed
    2026-10-24; CLOSED):** six normal WORKFLOW advisor rows aligned to canonical config; both
    validators `opencode-go/claude-haiku-5-5` `high`; verifier `ling`/`claude` families and Ling
    absent-only target. One writer, targeted tests, no advisor and no independent verifier under
    an explicit THIS-unit owner cost override (not simple docs, not a standing waiver). RED is
    corrected to FIVE q90 + one model-independence + one variants = 7 failures of 75, 0
    skips/errors (the earlier "four q90" was wrong); GREEN 75/75, 103 Bun controls; JSON validity
    and `bash -n` exit 0; full pin
    `41100b1b1896d808ca5b49f0db2edf5470db5f402dfe2d0314724a9a80e07b61`. Implementation commit
    `6ff16915407c39f2ca980339d30ed6907e2ee536`: 11 paths, 229 authored lines (213 additions / 16
    deletions), full range 41,948 bytes; the frozen writer receipt is distinct at 225 lines /
    41,473 bytes, and the committed diff carries the owner-explained Magic Context 0.49.20 / AFT
    0.62.0 pin substitutions that the frozen delta excludes (owner-attributed auto-update
    behaviour, not unit scope; not independently proved). Original assessment: base
    `d14e83f90a4f044e5b42b268fd47eec8c4ee96d8`, `committedOnly=true`, risk `high`, 229 lines / 11
    paths, `consumed=false`, `review_due=true`. Acknowledged lineage `review-ef3ab1c9aad86044`:
    four lenses APPROVED, authority burned, target sha256 `7e9e7564…`; lens evidence is
    owner-supplied 2026-10-24 and the PM observed the stopped `v9` status with
    `target_already_acknowledged` (the PM did not dispatch lanes, consent or acknowledgement).
    Deferred nonblocking findings `R3-UNSCOPED-PLUGIN-UPGRADES` WARNING and `R4-001` SUGGESTION;
    no correction opened. Static PASS PARTIAL (existing optional `specialist.group` diagnostic at
    `tests/test_model_independence.py:75:58`, Bash 0, six paths without LSP, no TS root; inferred
    pre-existing, no all-clean claim). Deploy/restart NOT performed: owner-reported live config
    still uses `minimax-m3` on `review-validator`, `asi-review-validator` and
    `advisor-testing-pre` until deploy (not PM-observed); runtime, full verifier, plugin load and
    M3.1 acceptance remain UNVERIFIED. Unit source+review CLOSED; Q90 remains IN PROGRESS.
  - **T3.0 fallback exact-policy repair (`q90-t30-fallback-repair-u1`, owner-directed
    2026-10-24; implementation committed and assessed):** mechanical verifier repair inside T3.0,
    not a new planned unit. Deleted the inactive exact source keys
    `opencode-go/mimo-v2.6-flash` and `opencode-go/minimax-m3` (their catalog entries, target refs
    and evaluator exclusions remain) and added `opencode-go/claude-haiku-5-5` with the same
    two-target deepseek-max / openrouter-default chain and capabilities as
    `opencode-go/minimax-m3.1-flash`. The two validators are the only agent assignments for
    Haiku; the removed identities had zero agent assignments. One implementation writer, no
    pre/post advisor and no independent verifier under an explicit THIS-unit owner ceremony
    override (a recorded deviation, not simple docs and not a standing waiver). New focused test
    `tests/test_q90_t30_fallback_repair.py`: delegated RED `Ran 8 tests` with `failures=4` on the
    old policy (the three owner diagnostics plus the accepted-control failure); final combined
    exact command `python3 -m unittest tests.test_q90_t30_fallback_repair
    tests.test_q90_t30_kimi_removal tests.test_model_independence tests.test_model_variants`
    reported `Ran 60 tests in 0.583s`, `OK`, 0 skips — focused 8 plus related 52, so the focused
    module is NOT part of that 52 (the earlier wording that read 52 as including it is corrected).
    `python3 -m json.tool` printed full normalized valid JSON without error; `git diff --check`
    and `py_compile` reported success. Numeric exit-0 statuses were NOT exposed and are delegated
    success inferences, not independently observed by the PM; no exit code is invented. The full
    verifier was NOT run; no deploy, restart or runtime claim. Implementation commit
    `5697f72b671c05dc94fac955bb9450a75aa37995` on `chore/multi-agent-v2-phase1`: 6 paths, 334
    additions + 26 deletions = 360 authored changed lines, 26,793 raw patch bytes (immutable
    readback `run54d52f7cb8af387f1cbb44f16c3bfbf7`, base `81c5ef5...`, head `5697f72...`,
    SHA-256 `e9d57ecb7383f050ebdb8d04261a9a889b887207cff35349ace43f691177d297`). Implementation
    assessment: status 0, `gentle-ai.review-assessment/v1`, `baseRef=81c5ef5...`,
    `committedOnly=true`, risk medium, reason `configuration_change`
    (`global-config/rate-limit-fallback.json`), 6 paths / 360 lines, `consumed=false`,
    `review_due=false`, `under_budget`; it approves, advances and closes nothing, and the last
    reviewed boundary is RETAINED at `6ff1691...`. PM first host `aft_inspect` over the 6 paths
    was PARTIAL: Python 0 errors / 0 warnings; JSON and four Markdown paths have no producer — no
    all-static-clean claim. Metadata closure: exactly one owner-authorized metadata-only writer
    for this same unit, class `documentation` under the simple-docs allowlist, confined to the
    tracker, this file and `ROUTER-LOG.md`; it is separate from the implementation's THIS-unit
    cost override and is not a correction (`correction_rounds_used=0`, unchanged). The PM owns the
    metadata commit and the post-commit metadata assessment (owner-requested at
    `baseRef=5697f72...`, `committedOnly=true`; the result is not predicted here). Owner verifier
    must be RE-RUN; deployment and native review remain PENDING/UNVERIFIED. Q90 remains IN
    PROGRESS; no new planned unit is added.
  - **T3.0 PM reassignment (`q90-pm-reassign-u1`, owner-directed 2026-10-24; COMPLETE, source
    `455a769219795e57769488210ee89ba8d67ac63f`):** both PMs `opencode-go/glm-5.3-flash` `high`;
    identical Qwen-high then cross-provider Gemini Flash agent chains (variant absent, no DeepSeek);
    shared GLM policy unchanged; exact verifier seat gate plus focused tests. 15 paths, 382 additions
    + 18 deletions = 400 authored lines, 73,737 raw patch bytes broker-measured. Prior executed
    evidence, not rerun by the metadata unit: independent verifier `ses_e9016b1f1ffeuBzEZnVD4LZq1V`
    ran 149 tests with 0 failures/errors/skips; correction writer `ses_e901223deffeqiZY7yeVugLvri`
    ran 48 targeted tests with 0; both JSON files valid, `bash -n` passed, verifier/pin `89ec3b2b…`.
    Owner-supplied lineage `review-f6f31e924064dec0` four lenses APPROVED, acknowledged, authority
    burned; the PM observed terminal `v9` status action `stop`, `not_replayable`,
    `target_already_acknowledged` and dispatched no lanes/consent/ack. Deferred informational
    findings exactly `R2-001`, `R2-002`, `R3-PM-SEAT-MISSING-TEST`, `R4-1` WARNING, `R4-2` WARNING,
    `R4-3`; no correction reopened. First-pass `aft_inspect` PARTIAL (no all-clean claim).
    Deployment/restart PENDING: owner reports live PMs still Sol; not independently
    runtime-verified. Metadata commit and post-commit assessment belong to the PM envelope.
    Q90 IN PROGRESS; no new planned unit.
  - **T3b — Planner slice (`q90-t3b-planner-u1`, owner-authorized 2026-10-24; SOURCE STAGED, NOT
    COMMITTED):** adds `planner` (`openai/gpt-6.1-sol` `high`) and `planner-evidence`
    (`openai/gpt-6-luna` `medium`), and `planner` only to the orchestrator, `pm-odd` and
    `pm-systematic` task maps. The Planner has the two ask-gated fixed acts `host_plan_write` /
    `host_gate_verdict`, `host_task_mark` denied, no writer/lens dispatch, and a deny-default task
    map limited to the defined pre/post advisors (including Gemini), `planner-evidence` and
    `explore`. `planner-evidence` is facts-only, read-only, task-denied and memory-write-denied.
    Verifier uses narrow `planWriterAgents`/`advisorDispatchAgents` sets, not `coordinatorAgents`;
    no guard, `ROUTE_STAGES`, overlay, embedded prompt, ledger, assembler or prompt-SHA change.
    Docs add the planned Planner handoff and Gate 1/Gate 2 ownership; the pipeline is SOURCE-ONLY
    and NOT installed, deployed or live, and current PM runtime ownership remains until deferred
    integration. Gate 2 is after post-code advice and the orchestrator's raw lens evidence and
    BEFORE the PM completes or ticks the unit. Both verdicts are technical only, never delivery.
    Deferred Q90-D1 prompt reduction/externalization is AFTER the PM layer becomes active, not an
    immediate prerequisite, and was not performed. Owner decision 2026-10-24 closes
    `455a769..416f289` metadata by OWNER DECISION, NOT native review; reviewed boundary `416f289`.
    Luna/Tiny (`general`, `jd-fix-agent`) sharing is an owner-accepted exception. Prior frozen
    results `30f00ac7...` and `ac28216d...` were rejected, uninstalled and not reused; the prior
    writer's TDD ordering deviation (tests executed after source, not pre-source RED) is recorded.
    This unit ran RED before source (missing agents and verifier block), then 7 focused Planner
    tests and the 204-test required regression all passed with no skips. ONE writer, one later
    independent `gentle-ai-verify`, NO pre/post advisors and ONE correction remain the owner's
    ceremony; THIS-CANDIDATE review-size exception is up to 700 authored lines / 102,400 raw
    patch bytes / 46,080 per file. Tracker backfill is delegated to the orchestrator later because
    `odd/tasks/**` is protected; the owner-supplied 1,015-line whole-file `host_plan_write`
    replacement (revision 0) was NOT invoked or written. Mirror write/readback is UNIMPLEMENTED
    and was not read; commit, independent verifier, correction decision and assessment are PENDING.
    Q90 remains IN PROGRESS.
  - **T3c — PM slice (PLANNED, high risk):** permission-only drop of relay/advisor dispatch after
    the T3.0 model migration; no model/fallback work deferred to T3c; same three surfaces plus PM
    `WORKFLOW.md` lines.
  - **T3d — residual audit (PLANNED, high risk):** remaining nonduplicated fallback/routing audit
    only; no model or fallback seat work already delivered in T3.0. M3.1 session/hang/Go-allowance
    acceptance is still required before its promotion goes live. `minimax-m3` stays excluded from
    EVERY native seat. Same three surfaces.
  - **T4 — verifier (PLANNED):** new-agent/model/tool checks and digest re-pin, after ALL T3a-d
    slices.
  - **T5 — mirror and owner restart (PLANNED):** after T4.
  - **T6 — release (PLANNED):** behavioral probes and trial metrics, after T5 and the owner
    restart.
- **T1 evidence (2026-10-23):** source `114366b35651316e00c972f71f723b7804fcae4c`; metadata
  `dfbeb296af708f02151d7444d8d76431606abff6`; source receipt 206 authored lines / 25,263 bytes /
  generated-binary [], PM factual readback accepted, correction 1/1. The SOURCE assessment at
  boundary `22132adc686629cceaa7b32e469c5ec10d009e2a` was medium/`under_budget`,
  `consumed=false`, `review_due=false`, 6 cumulative paths / 563 lines — cumulative source slice,
  NOT this unit's 206 lines and NOT the final metadata statistics. Final PM assessment completed
  medium/`under_budget`; boundary `22132ad` retained. This is not native review or approval.
- **T3a1 evidence (2026-10-23):** source writer `ses_e9572b051ffexBxZRVrDekeEtA`; pre advisors
  security `ses_e957e891bffeVQZBnoMD7HKtyq` (Sol) and integration
  `ses_e957e890effeymwKzrfR3yBr7m` (Kimi); independent verifier
  `ses_e9562bcafffeOQNeIGCxxCnel4` (Sol) executed 77 tests plus Bun controls and prompt/digest
  checks; post advisors `ses_e9562bccdffeexMrjlOz20JrPa` (security) and
  `ses_e9562bcc4ffeZ3GFFnyZBf71BD` (integration) before source commit; correction rounds 0.
  Assembled orchestrator prompt 419 lines / 61,050 bytes SHA-256
  `0cf8da259010ca402320756ef19aaa148b9706d8c93f31a535cd97684b767838`; verifier SHA-256
  `9b10a8bee1873fd7adc2e23ecd68fb9f0bd2edf5a41eb2cffdbe6dd9cc865c29`. First-pass static
  `aft_inspect` PARTIAL: seven diagnostics at unchanged Python sites (pre-existing, inferred), no
  static-clean claim. Full verifier, runtime load, live consumer and tool enforcement are
  host-only NOT run; no deploy. Readability attempt 1 was an incomplete-JSON transport refusal,
  attempt 2 admitted; the rejected artifact
  `.git/gentle-ai/rejected-results/review-1ca5500bc130a1cf/review-readability-1-42837fe6b897.json`
  is transport evidence, not a finding.
- **T3a2 evidence (2026-10-24):** four commits from `2173738`: `3b96708` enforcement source,
  `3069e33` owner advice, `cdf9056` two omitted-control expected-string corrections plus digest,
  and `77ef08a`
  post-escalation R4-1/R4-2 fix plus digest; final range four paths / 484 lines. Approved
  lineage `review-bff8f73a89ebffa5`, target
  `36776914a529bd3645a44d7532f8518cb3a9c7ec50fff49f8570d0cd10b259c2`, approved and
  acknowledged, authority burned; prior lineage `review-83d13326ee0004a8` escalated and is
  superseded, NOT approved. This was ENFORCEMENT only: `opencode.json` already granted the six
  `asi-review-*` lanes to the orchestrator and none to the PMs; no config/guard/skill/
  `WORKFLOW.md` change, and Q89 coordinator `host_plan_write` asks are preserved. Deferred
  WARNINGs (informational/non-blocking; no correction opened; owner-confirmed admitted results):
  `R3-MISSING_BUN_SKIP` reliability `tests/test_review_pipeline_permissions.py:908` — `run_script`
  lacks the Bun-absence skip present in `run_controls`; `R4-1` resilience same file `:920-930` —
  same Bun-absence class; `R4-2` resilience `verify-workflow.sh:2819-2828` — boolean false
  inconsistency (`hostPlanWriteGrantSweepFailures` reads false as grant, `reviewDispatchFailures`
  as deny); `R4-3` resilience `verify-workflow.sh:3460` — control/producer alignment for
  `<inherit/none>` is inferential. Source normal `correction_rounds_used=1` plus owner-authorized
  sentinel+pin fix (2026-10-23) and post-escalation R4-1/R4-2 fix (2026-10-23), neither opening
  a new advisor/verifier round. Final verifier digest `e76baed…`; full verifier, live plugin
  hooks and deployment remain UNVERIFIED.
- **Resolved decisions and standing gates (2026-10-23):**
  (a) RESOLVED: handover item 8 — advice is evidence, the gate verdict is the approval act
      (decision 6);
  (b) RESOLVED: `host_plan_write` is ask-gated for BOTH the orchestrator and the Planner, with NO
      no-ask exception; PM suggestions are messages, never plan writes. The companion design ask
      for no `ctx.ask` is rejected; the repository safety model stands;
  (c) RESOLVED: the PM dispatches no review lanes, so the `review-resilience` GLM and
      `review-risk` `qwen3.8-flash` seat collision is gone;
  (d) RESOLVED: all named model IDs resolve, per THREE owner-reported host `opencode models` runs
      on 2026-10-23. Go pool, OpenAI `openai/gpt-6.1-sol` and `openai/gpt-6-luna`, and Google
      `google/gemini-flash-latest`, `google/gemini-4-argon`, `google/gemini-3.8-flash`; the
      shared-pool `opencode-go/*` variants are not the named providers. Model-ID resolution does
      NOT prove seat independence;
  (e) FAIL CLOSED: `minimax-m3` is excluded from EVERY native review seat until the hang is
      proven absent. The owner states the repo holds no hang record (owner-attributed absence,
      no independent search claimed). R3 has NO confirmed seat; `minimax-m3.1-flash` is not
      promoted without session and hang checks. T3d chooses the replacement from
      `claude-sonnet-5-5`, `minimax-m3.1-flash` (after checks), `muse-spark-1.3-contributor` or
      `step-5-preview`. No seat is chosen here; SUPERSEDED 2026-10-23 by the owner model
      direction (item 7): `minimax-m3.1-flash` is the planned reliability/advisor target, subject
      to session/hang/allowance acceptance. The no-seat text is retained as history;
  (f) RESOLVED: actor slices T3a orchestrator, T3.0 model/role, T3b Planner, T3c PM, T3d
      residual. EACH actor commit changes the same three policy surfaces consistently —
      `global-config/opencode.json` task permissions; guard `ROUTE_STAGES`/helper lists; route
      skills — PLUS that actor's `WORKFLOW.md` lines. T3.0 atomic subunits also carry their
      verifier edits and digest pin. No owner size exception; no intermediate
      guard-denies/skill-allows state; any slice unable to remain consistent STOPS AND ASKS.
- **Genuine open choices:** the owner mappings still marked pending in the tracker (design pair,
  maintainability scope, optional v4-pro profile, qwen-max escalation shape, local Kinver opt-in)
  and M3.1 session/hang/Go-allowance acceptance. SETTLED RECOMMENDATIONS (a contrary policy needs
  separate owner authorization): judges stay fixed/no-fallback with verifier controls; PM keeps
  qwen for same-provider model-scope failure and fails closed on provider outage.
  `frontend-dev-premium` stays the unchanged read-only Sol design coordinator. The R3 replacement
  itself is no longer open: the owner names `minimax-m3.1-flash` for planning, with no clearance
  claim. Host-tool, session and seat-independence checks remain prerequisites, not owner decisions.
- **Order:** T3.0 model/role work FIRST (no `agent-sandbox-integration` dependency), then T3b
  Planner, T3c PM (permission-only), T3d residual audit, T4 verifier/digest, T5 mirror/owner
  restart, T6 behavioral probes/trial metrics. Host tools built/tested remain gates for slices
  that need them; T3a1/T3a2 already landed. The queue revision was the owner-authorized planning
  exception and enabled no tool.
- **Scope boundary (historical):** T2 was planning/evidence only; T3a1 and T3a2 have since
  landed; T3.0 planning is complete with no source. Phases 2-4 are external; the unmerged planner
  tier is only the Q91 placeholder. T3.0.1 is next, high risk; T3b follows T3.0 and owes
  pre-advice, post-advice, one independent verifier, ONE correction round and native review
  after commit.
- **Slice closure and boundary:** prior medium slice `22132ad`..`2f196b6` is CLOSED by explicit
  owner decision 2026-10-23; the boundary advanced to `2f196b6` BEFORE T3a1 source. That closure
  is not native review of the prior slice. The current native-reviewed source boundary is
  `77ef08af7c376386b24a62e26efc6809b9753bdf` (T3a2 lineage `review-bff8f73a89ebffa5`
  approved); T3.0.1 is next, then T3b; both remain untouched.

### Q91. Planner tier (renumbered from the unmerged Q67 plan on docs/pm-planner-delegation, 9938cd1)
- **Status:** PLANNED.
- **Prerequisites:** Q90.
- **Description:** Placeholder for the unmerged planner tier; Q90 owns the forward decisions.

## OpenCode V2 upgrade (PLANNED — implement when the owner decides to upgrade)
Trigger: OpenChamber 2.x requires OpenCode 2.0.15 or newer (OpenChamber v2.0.0 release notes).
Installed: OpenCode 1.18.33 (V1). Latest V2: `@opencode/cli` 2.0.21 (npm, 2026-10-01).

Verified facts (sources: https://opencode.ai/v2/docs/migrate-v1/,
https://opencode.ai/v2/docs/build/plugins/migrate-v1, npm):
- **V1 plugins do not run on V2.** Entry becomes `export default Plugin.define({id, setup(ctx)})`
  from `@opencode/plugin`, and hooks move to domains (`ctx.tool.hook("execute.before")`,
  `ctx.session.hook("prompt"|"context")`, `ctx.agent.transform`, `ctx.event.subscribe`). Dual-mode
  entries (`{...Plugin.define(...), server(){V1 hooks}}`) run on both V1 (1.18.29+) and V2.
- **Config:** V2 reads V1 config and normalises it in memory without rewriting files (`agent` →
  `agents`, `plugin` → `plugins`, `prompt` → `system`, permission arrays, `task` → `subagent`).
  `subagent_depth` and `compaction.prune` are dropped. `CLAUDE.md` is no longer read, only
  `AGENTS.md`.
- **TUI:** `tui.json` is auto-migrated to `~/.config/opencode/cli.json` on first V2 start. V1 TUI
  plugins need `@opencode/plugin/tui` entrypoints.
- **Native review on V2 needs gentle-ai v4.** v3.7.0 refuses it. v4 admits it only with the
  `gentle-ai.opencode-relay/v2-staged` relay, proven only on OpenCode 2.0.19 on macOS. When a
  review plugin refuses a call, later plugins' hooks are skipped for it.
- **Third-party readiness** (detail in `~/ai-workspace/OPENCODE-V2-PLUGIN-TASKS.md`):
  - **Systematic 3.21.0 is V1-only** (peer `@opencode-ai/plugin ^1.1.30`). This is a hard blocker,
    because the `ce:*` skills and agents depend on it.
  - `opencode-subagent-statusline` (issue #97), `opencode-sdd-engram-manage` (#52) and
    `opencode-plugin-auto-update` (#7) are not ready.
  - `opencode-usage-total`: not yet, inferred.
  - `@cortexkit/opencode-magic-context` needs upgrading to 0.44.4 and `@cortexkit/aft-opencode`
    to 0.58.2; both have V2 support.

### Q40. V2 prerequisites and blockers
- **Status:** BLOCKED.
- **Prerequisites:**
  - gentle-ai v4 upgrade complete (Q29-Q39), because native review on V2 needs v4.
  - A V2-compatible Systematic release (external).
  - Each third-party plugin either has a V2 release or is retired (`~/ai-workspace/OPENCODE-V2-PLUGIN-TASKS.md`).
  - The agent-sandbox-integration V2 port (Q47).
- **Description:** track each blocker with its evidence link, and re-check upstream before
  scheduling. Owner decides the target V2 version: at least 2.0.15 (OpenChamber); gentle-ai's
  review proof is on 2.0.19; latest is 2.0.21.

### Q41. Side-by-side V2 probe (non-destructive; answers the unverified behaviour)
- **Status:** READY once V2 can be installed beside V1 (it ships an `opencode2` binary; confirm the
  install channel).
- **Prerequisites:** none. Run against a scratch COPY of the config (separate `XDG_CONFIG_HOME`),
  never the live one.
- **Description.** Probe and record:
  - whether `plugin` (V1 key) and global `~/.config/opencode/plugins/*.ts` auto-load still work;
  - `{file:...}` prompt includes;
  - `mode`, `hidden`, `variant` and the `tools` maps;
  - the `permission.task` → `subagent` mapping and `host_*`/`sandbox_*` tool-id permissions;
  - whether `opencode agent list`, `opencode debug agent <name>` and `opencode run --format json`
    exist, and their output shape (the verifier depends on all three);
  - tool-call refusal by throwing from `execute.before`;
  - `tui.json` + `tui.jsonc` → `cli.json` migration (including the herdr entry);
  - the V2 event fields the guard reads (`input`, task output with `ses_` ids, command parts).
  Results feed Q42-Q45.

### Q42. Port this repo's plugins to dual-mode (V1 + V2)
- **Status:** PLANNED.
- **Prerequisites:** Q41.
- **Description.** Each file exports `Plugin.define({id, setup})` plus `server()` with the
  current V1 hooks, so one file works before and after the switch:
  - `astra-sol-upgrade.ts` (`config` hook mutating `config.agent` and `permission.task`): becomes
    `ctx.agent.transform`, or define the `-astra` aliases statically in config.
  - `systematic-routing-guard.ts`: `chat.message` → `session.hook("prompt")`,
    `tool.execute.before/after` → `tool.hook(...)` (`event.input` replaces `output.args`;
    re-verify `output.output` parsing of child `ses_` ids), `command.execute.before` → command
    transform. Account for hooks being skipped after another plugin refuses a call (plugin
    order).
  - `workflow-health-check.ts`: `experimental.chat.system.transform` → `session.hook("context")`.
    Keep the `WORKFLOW_HEALTH_CHECK_PROBE` recursion guard.
  - Tests: stage-table assertions (Q03) run against both entrypoints.

### Q43. Config for V2 (`global-config/opencode.json`, `tui.json` → `cli.json`)
- **Status:** PLANNED.
- **Prerequisites:** Q41, Q40 (plugin list).
- **Description:**
  - Keep V1-compatible keys while dual-running (V2 normalises them in memory). Move to native
    V2 keys only after V1 is retired.
  - Decide on the dropped `subagent_depth: 3` (V2 has no equivalent) and `compaction.prune`.
  - Update the plugin list per `~/ai-workspace/OPENCODE-V2-PLUGIN-TASKS.md`: upgrade magic-context and aft; remove sdd-engram-manage,
    gentle-logo, the auto-update local build (it rewrites `plugins` → `plugin`) and statusline
    until #97 is fixed.
  - Add a canonical `global-config/cli.json` and retire `tui.json` handling once V2 is the
    runtime.

### Q44. Verifier V2 mode (`verify-workflow.sh`)
- **Status:** PLANNED.
- **Prerequisites:** Q41, Q42, Q43; Q04 and Q26 strongly preferred.
- **Description.** Select the mode by the `opencode --version` major.
  - Runtime probes `:4437` (`agent list`), `:4518` (`debug agent`) and `:4650`/`:4657`/`:4696`
    (`run`) are adapted per Q41.
  - JS helpers `:1872-1955` parse the V2 permission arrays (renamed actions).
  - `check_plugin_loads` (`:200-262`) also asserts a V2 `id` + `setup`.
  - `tui.json` recovery (`:114-125`, `:577-724`) gains `cli.json`.
  - `:2847` "OpenCode V2 native review remains unavailable and fails closed" and the `:2841` v8
    relay text are replaced by the v4 V2 relay declaration check.
  - The auto-update pins (`:150`, `:3213-3236`) and rate-limit-fallback checks (`:131-146`,
    `:2399`, `:2427-2430`) follow Q43.
  - Re-pin the digest.

### Q45. Workflow documents for V2
- **Status:** PLANNED.
- **Prerequisites:** Q41, gentle-ai v4 (Q29-Q39).
- **Description:**
  - `WORKFLOW.md:142`, `:165` ("OpenCode V1 v8 review work"; "V2 native review remains
    unavailable") and the `asi-review-*` relay lane text (`:173-177`): rewrite for gentle-ai v4's
    V2 relay. Owner decision: the reviews stay on in-OpenCode agents (decided), but the relay
    mechanism changes to gentle-ai's managed V2 review transport.
  - Note that V2 reads `AGENTS.md` only, never `CLAUDE.md`.
  - Update the routing-guard and plugin-order notes for the refusal-skips-later-hooks limitation.

### Q46. OpenCode V2 change set and runbook (non-destructive, reversible)
- **Status:** PLANNED.
- **Prerequisites:** Q36 tool (reuse it with an `upgrade/opencode-v2/` profile); Q40-Q45.
- **Description.** The same declarative operations, `expect_before`, write-ahead journal and
  drift-preserving revert as Q36.
- **Runbook:**
  1. Preflight: Q40 blockers cleared, `~/ai-workspace/OPENCODE-V2-PLUGIN-TASKS.md` items done or retired, verifier passing on V1.
  2. Back up the live config.
  3. Install V2 beside V1.
  4. Apply the change set (dual-mode plugins, config ops).
  5. First V2 start (journal the `cli.json` migration).
  6. Verifier in V2 mode.
  7. OpenChamber check (plugin loaded status), then `--behavioral` and dispatch checks.
- **Rollback:**
  - V2 never rewrites `opencode.json`, and the plugins are dual-mode, so V1 stays runnable.
  - Revert the journal (drift preserved).
  - Switch back to the V1 binary.
  - `cli.json` is left in place (V1 ignores it).

### Q47. Cross-project and out-of-repo plugin work for V2
- **Status:** PLANNED, external.
- **Prerequisites:** none to file.
- **Description:**
  - **agent-sandbox-integration owns** `sandbox-tools.ts` (about 40 `tool({...})` definitions →
    `ctx.tool.transform` with JSON Schema; `chat.params`), `reviewer-relay-transport.ts` and
    `lib/reviewer-relay-core.ts` (`event`, system/messages transforms, `tool.execute.*`) and
    `routing-guard.ts`. Add these to its TODO by name.
  - **Other local plugins** (nono, codecast, herdr, `use-grep-tool`, rate-limit-fallback fork,
    auto-update local build, gentle-logo, `sdd-task-result-artifacts`) are tracked in `~/ai-workspace/OPENCODE-V2-PLUGIN-TASKS.md`, with
    per-plugin tasks, verification and rollback.

### Q48. Forward-compatibility rule and lint
- **Status:** READY.
- **Prerequisites:** none for the rule; the lint is easiest after Q26 (anchors).
- **Source:** owner, 2026-10-02 (`docs/PLAN.md` Constraints).
- **Description:**
  - Add the forward-compatible-by-default rule to `WORKFLOW.md` (global tooling section) and to
    the delegation brief for writers.
  - Add a verifier check (advisory-only until Q28 lists it as enforced) that flags NEW
    occurrences on a branch relative to `main`:
    - SDD agents, skills or `host_sdd_*` grants;
    - `strict_tdd`;
    - V1-only plugin entrypoints without a V2 `Plugin.define` in this repo's plugins;
    - new "Gentle AI 3.x" or "OpenCode V1" literal headings.
  - Existing occurrences stay until their upgrade item removes them.

### Q49. Upgrade readiness dry-run (detect drift between main and the upgrade branches early)
- **Status:** PLANNED.
- **Prerequisites:** Q36 apply tool (`--dry-run`), and the upgrade branches once they exist.
- **Source:** owner, 2026-10-02.
- **Description:**
  - A read-only mode (verifier flag or a standalone script) that:
    - test-rebases the v4 and V2 branches onto current `main` in a throwaway worktree under the
      home directory, never `/tmp` (CodeGraph worktree rule);
    - runs the change-set `apply --dry-run` against the current live files.
  - Reports rebase conflicts and conflict-skipped operations, and changes nothing.
  - Run it after each merged work unit that touches `global-config/`, `WORKFLOW.md`, skills or
    the verifier.

## Done

- Review follow-up on the plugin load check (old items 1–2): `71a2eb3` (`d85ca4a` introduced the
  check); native review `review-10d26170c9d40efc` approved and acknowledged.
- Guard deploy (old item 3): the guard is live and warn-only (history "Deploy note"); the
  verifier mirror and restart for the advisor registration remain in Q01.
- Advisor registration: `5c41a4f`, `844d759`, `c01a73f`, `c5a326b`, `8570dc6`; verification in Q01.
- Pre-code advice policy and structured test requests in `WORKFLOW.md`: `a08e447`, `812741b`;
  advisor interface contract and plan B: `2a757ab`.
- Guard stages and keys, T1–T7b, T7a-fix, T9: see `odd/tasks/routing-guard-keys.md`; native review
  `review-84383b2e59dc8844` approved and acknowledged (its findings are Q03).
- Review/advisor model assignments and follow-on fallback fixes: complete work unit, recorded in
  `odd/tasks/model-assignments.md`. Added here in Done rather than assigning a new Q-number because
  the tracked unit and its follow-ons are complete; the GPT fallback target question remains open.
- Work queue and plan created: `b0e000e`.
