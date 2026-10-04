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
  the Q36 change set, then Q34. Q49 runs throughout.
- **Phase 5, OpenCode V2 upgrade (owner-triggered, after Phase 4):** Q40-Q47.

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
- **Status:** READY. Subject to the advice mandate (Q02). The guard is live and warn-only, so
  any fix needs the verifier mirror and a restart to take effect.
- **Prerequisites:** Q02 (advice record before coding).
- **Source:** `docs/TODO-HISTORY.md` "12. Guard review findings"; `odd/tasks/routing-guard-keys.md`
  review `review-84383b2e59dc8844`.
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
- **Status:** PLANNED; obsolete on v4 (see Q33).
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
- **Status:** READY.
- **Prerequisites:** none. Do it with or before Q04; the split must preserve whatever contract
  replaces the literals.
- **Source:** advisor-maintainability (`docs/TODO-HISTORY.md` "2026-10-01 — Advisor dispatch verification PASSED").
- **Description:**
  - About 15 hardcoded prose literals must appear in `WORKFLOW.md`/`AGENTS.md` or the verifier
    fails, so routine doc edits break it.
  - Replace prose matching with stable machine markers (e.g. `<!-- workflow:anchor ... -->`) or a
    single declared anchor list, so wording can change freely.
  - Inputs for Q04: 4,772 lines and only 13 functions, all ending by line 1231; the rest is one
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
- **Status:** PLANNED, gated by "owner decides to upgrade".
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
- **Status:** PLANNED, gated by "owner decides to upgrade".
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
- **Status:** PLANNED, gated by "owner decides to upgrade".
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

### Q33. Guard and plugins
- **Status:** PLANNED, gated by "owner decides to upgrade".
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
- **Status:** PLANNED, gated by "owner decides to upgrade".
- **Prerequisites:** Q29-Q33 on one gated branch.
- **Source:** v4.0.0 release notes; Q24 (sync overwrites the live config).
- **Description:**
  1. Confirm the install method (`command -v gentle-ai`; Homebrew formula present, so
     `brew upgrade gentle-ai`).
  2. `gentle-ai sync --dry-run` first.
  3. Upgrade the binary.
  4. `gentle-ai sync`; expect it to overwrite managed agents and prompts, and handle a non-zero
     exit when it cannot detect the OpenCode version.
  5. Apply Q30-Q33 with the Q36 change-set tool (`apply --dry-run`, then `apply`). Do not
     hand-copy.
  6. Run the verifier (recovery plus checks).
  7. Restart OpenCode.
  8. `verify-workflow.sh --behavioral`.
  9. Dispatch checks: `advisor-*`, the v4 generic agents, `asi-review-*`.
  10. Rollback: keep the v3.7.0 binary and the verifier backup in `backups/workflow-recovery/`.

### Q35. Remove mandatory Engram instructions everywhere (Magic Context is the default memory)
- **Status:** IN PROGRESS.
  - Done 2026-10-01: Claude Code text stripped. The `gentle-ai:engram-protocol` block was removed
    from `~/.claude/CLAUDE.md`, and the ODD lines now make the task file the durable record, with
    a Magic Context mirror where the runtime has it and Engram "never required". Backup:
    `backups/claude-md/CLAUDE.md.20261001T222932Z.before`.
  - Owner choice: the Engram plugin stays installed until Q14b brings Engram back as an
    inter-agent MCP.
  - Remaining: the plugin's SessionStart hook still injects its own "MANDATORY" protocol text.
    The ODD lines sit inside the gentle-ai-managed `agent-routing` block, and the protocol block
    is gentle-ai-managed too, so the next `gentle-ai sync` will restore both. The enforcement
    check below is what makes the removal stick.
- **Prerequisites:** none for the OpenCode side (already done). Claude Code side: owner confirms
  the scope of edits to `~/.claude` (outside this repo).
- **Source:** owner decision; read-only survey 2026-10-01.
- **Description:**
  - **OpenCode: already enforced.** `WORKFLOW.md:129` makes Magic Context mandatory. The
    verifier fails on `LEGACY_ENGRAM_PROTOCOL_REAPPEARED` (`verify-workflow.sh:4388`) and on
    `ENGRAM_UNEXPECTEDLY_ENABLED` (`:3086`). Keep both checks through Q32 and the v4 upgrade. Q14b
    must not reintroduce a mandatory protocol, only a scoped opt-in channel.
  - **Claude Code: still mandatory.** Remove:
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
  - **Enforcement (per the deployment-gating constraint, Q28):** gentle-ai sync rewrites the
    CLAUDE.md block. Add a check (in the verifier, or a Claude Code-side health check) that fails
    when `<!-- gentle-ai:engram-protocol -->` or a mandatory Engram hook reappears, and relates to
    Q24 (sync drift).
  - **v4:** apply the same rule to v4's managed orchestrator prompts (Q29b, Q30).

### Q36. Non-destructive change set for the v4 upgrade: apply and revert without clobbering drift
- **Status:** TOOL DONE 2026-10-02: `scripts/changeset.py`, spec `docs/specs/changeset-tool.md`
  v1.3, 72 tests, three native reviews approved (tracker `odd/tasks/changeset-tool.md`; follow-up
  T5). The v4 change-set CONTENT is authored at upgrade time (Q30-Q33), per the build-late rule.
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
- **Status:** PLANNED, gated by "owner decides to upgrade"; delivered in the Q36 change set.
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
  - **Gate:** a verifier check fails if `strict_tdd`, `--strict-tdd` or "STRICT TDD MODE"
    reappears in the canonical config, the workflow docs or the skills.

### Q39. SDD changes in flight at upgrade time
- **Status:** PLANNED, gated by "owner decides to upgrade". It is a preflight of the Q36 apply.
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
- Work queue and plan created: `b0e000e`.
