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

### Q01. Advisor layer close-out
- **Status:** READY. Registration fixes appear landed: `c01a73f` (MiMo fallback policy, advisors
  classified as isolated-memory agents), `c5a326b` (search-contract block in advisor prompts),
  `8570dc6` (workspace-local sandbox tools). `github_ro_*` is absent from the five advisor blocks
  in `global-config/opencode.json`. Verifier pass on the final state is **status unverified**:
  confirm by running `verify-workflow.sh` after the mirror.
- **Prerequisites:** none. Host actions in order: verifier mirror, then service restart
  (`SECURE_OPENCODE_RESTART_REQUIRED` is expected until then).
- **Source:** `docs/TODO-HISTORY.md` "Advisor registration — verifier findings" and "PRIORITY
  CHANGE"; `docs/advisor/handoff-workflow-optimisation.md` "Where this slots in" 1.
- **Remaining:** dispatch each of the five `advisor-*` agents once on a bounded task and confirm
  registration, successful reads, denied host mutations, and the assigned model observed.

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
- **Findings, in fix order:**
  - R2-001 (real defect): `allowsSpecialists` is inverted; fix first.
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
  independently runnable and testable; the file is 4,770 lines and cannot be whole-body edited.

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
- **Q10.1 Systematic version drift.** Status: READY. Prerequisites: none. `WORKFLOW.md` names
  Systematic v3.18.4; v3.21.0 is installed. Status of the installed version is **unverified**:
  confirm with the installed Systematic inventory before editing.
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
- **Description:** keep the patch route as the interim worker rule (host reads before
  activation; context-bearing hunks via `sandbox_apply_patch`; verify with `sandbox_bash git
  diff`; treat a success return as unverified until readback). The conclusion "`sandbox_read`
  broken at any size; never use" is superseded: `sandbox_read` is the normal read for small
  and moderate files; very large files use a host read before activation, the saved-output
  artifact, or a targeted read. First rule is file-size discipline; the patch route is the escape hatch.

### Q13. Cross-project items (old item 8) — agent-sandbox-integration
- **Status:** BLOCKED (external project).
- **Prerequisites:** delivery of these entries in agent-sandbox-integration's TODO, by name:
  Tier 2 items 7–8 (ledger appends); the allowlisted append operation; the ledger move out of
  git; the project-scoped signal channel; the install-vs-commit gap. Confirm each is delivered
  and installed here.
- **Source:** B0 fix 5 in `docs/advisor/handoff-workflow-optimisation.md`; `docs/TODO-HISTORY.md`
  item 8 and "Review state" (ledgers are shared git-tracked files).
- **Note:** the host commit tool also rejects multi-line messages (`routing-guard-keys.md` Debt);
  the `ROUTED:` trailer sits on the subject line until that is fixed in the host tooling.

### Q14. B6 — Engram evaluation (report only)
- **Status:** PLANNED.
- **Prerequisites:** none. Output is a report; adoption is the owner's decision because
  `WORKFLOW.md` currently forbids `mem_*` in ODD.
- **Source:** `docs/advisor/handoff-workflow-optimisation.md` B6.
- **Description:** assess scoped, per-request access to handoff summaries and evidence
  references: project labels are not access control, unrelated memories must not be exposed,
  independent first-pass reviewers must not see each other's conclusions.

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
- **Status:** PLANNED; whether later guard commits already fixed any of them is **status
  unverified**: confirm by reading the cited locations in `systematic-routing-guard.ts`.
- **Prerequisites:** Q03.
- **Source:** `odd/tasks/routing-guard-keys.md` review `review-10d26170c9d40efc`.
- **Findings:** R2-003 (tracker wording, `routing-guard-keys.md:133`); R3-child-regex-format;
  R3-console-warning-dedup; R3-copy-path-gap; R3-systematic-apply-marker-gap; R4-001
  (verifier, partially fixed: factory required but not invoked).

### Q21. Routing guard — advisory follow-ups of `review-16c862492747259a` not covered by Q03
- **Status:** PLANNED; R3-missing-key-tests, R3-unawaited-key-io and R4-001 (nested inheritance)
  are **status unverified** (not recorded as fixed): confirm against the guard source.
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
