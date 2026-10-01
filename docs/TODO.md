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

**Current working order (owner, 2026-10-01):** Q03 (R2-001 + cross-route stage resolution) → Q25
(handoff corrections) → Q26 (verifier prose coupling) → the rest in listed order. Every source
change then needs the deploy step: verifier mirror, then restart. Q27 waits on an owner decision.

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
- **Remaining:** after the restart, run `verify-workflow.sh --behavioral` and a plain re-run (the
  cache-prune check was skipped because config was repaired). Then dispatch each of the five
  `advisor-*` agents once on a bounded task and confirm registration, successful reads, denied host
  mutations, and the assigned model observed.

### Q02. B0 coherence fixes, B1 mandatory advice policy, B2 advisory-evidence protocol
- **Status:** DONE (2026-10-01, review `review-bd57149caec073dc` approved). Tracker `odd/tasks/advice-mandate-and-queue.md` (T1 queue, T2
  `WORKFLOW.md`, T3 `docs/PLAN.md`, T4 ledgers).
- **Prerequisites:** none. The interim lane it defines relies on Q01 verification; until Q01 is
  done an unverified advisor is a missing opinion, not an approval.
- **Source:** `docs/advisor/handoff-workflow-optimisation.md` B0, B1, B2.
- **Description:** advice mandatory for every non-trivial change (interim lane: registered
  advisors); external lane written as PLANNED; tracker protocol for advisory evidence.

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
  relay lanes; add verifier checks (grants, sole holder of `host_review_capture_result`, no
  non-user launcher references `advisor-open`); flip the external lane from PLANNED to mandatory.
  Initial state on activation is `pair-default`: both hosts per non-trivial unit (owner,
  2026-10-01). Verify that the broker's `group` gives first-pass independence for the pair.

### Q07. B4 — routing guard integration (warn-only)
- **Status:** BLOCKED.
- **Prerequisites:** Q06; Q03 (R2-001 fixed before another stage relies on `allowsSpecialists`).
- **Source:** `docs/advisor/handoff-workflow-optimisation.md` B4.
- **Description:** optional `advice` stage satisfied only by an observed `host_advisor_get`
  result (`status: submitted`, matching `binding.task`) and, in the interim, an observed
  `advisor-*` dispatch result; warn on free-form `input` to `host_review_capture_result` for
  external-lens reviews. Owner decides whether the stage exists.

### Q08. B5 — advisor handoff document
- **Status:** BLOCKED.
- **Prerequisites:** Q06.
- **Source:** `docs/advisor/handoff-workflow-optimisation.md` B5; `docs/ADVISOR-HANDOFF.md` "Requested".
- **Description:** answer the two "Requested" items with plan A's verified contracts
  (cross-project read-only inspection; workspace isolation) and describe the external lane next
  to the five registered advisors.

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
- **Status:** PLANNED.
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
  - R3-console-warning-dedup: OPEN. `host_review_start` `:778-783` and skill-load `:971-976`
    bypass dedup. The specialist case `:860` is Q03's R3-specialist-warning-dedup; fix all three
    together.
  - R3-copy-path-gap: probably fixed by `15a5b20` (`:793-797`). Unconfirmed until the copy tools'
    destination field is checked against `targetPath` (`:720-727`).
  - R3-systematic-apply-marker-gap: OPEN. `sandbox_apply` is excluded from `pathKnown`, and
    `patchTrackerPath` at `:805` is dead code.
  - R4-001 (verifier factory): treated as OPEN per the tracker; the verifier code was not read.
- **Prerequisites:** Q03.
- **Source:** `odd/tasks/routing-guard-keys.md` review `review-10d26170c9d40efc`.
- **Findings:** R2-003 (tracker wording, `routing-guard-keys.md:133`); R3-child-regex-format;
  R3-console-warning-dedup; R3-copy-path-gap; R3-systematic-apply-marker-gap; R4-001
  (verifier, partially fixed: factory required but not invoked).

### Q21. Routing guard — advisory follow-ups of `review-16c862492747259a` not covered by Q03
- **Status:** PLANNED. All three verified OPEN on 2026-10-01 at `069cc4b`:
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
