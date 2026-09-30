# Routing Guard Keys

## Objective
Make the orchestrator's routing compliance mechanically enforced with session-scoped keys, keyed on the adapter actually loaded, inherited by spawned workers, and suspicious of self-granted authority. Keep the gate warn-only until the log shows no spurious hits.

## Problem
The route gate could be satisfied by any skill load, including a hollow one. A fixed 30-minute lifetime conflated orphaned sessions with long-running work; keys were deleted on every user message, creating a per-turn reset; a valid key did not authorise gated tools on its own; workers could self-mint keys; and registered worker mutation tools were not gated.

## Scope
- `global-config/plugins/systematic-routing-guard.ts`
- `odd/tasks/routing-guard-keys.md`
- Magic Context mirror at `ODD_TASKS key=odd/workflow_optimisation/routing-guard-keys/tasks`

## Constraints
- Keep the routing gate warn-only; do not block tool calls.
- Preserve the kill switch at `~/.config/opencode/routing-guard-off` and `SYSTEMATIC_ROUTING_GUARD_MODE` semantics.
- Keep routing keys outside the project because a plugin may not derive the project path from the server cwd.
- The health plugin's digest pin covers `verify-workflow.sh` only; do not change the health plugin or verifier for this task.
- Do not change `opencode.json` or any ledger.

## Tasks
- **T1 — Warn-only gate** — **done**. Commit `2c0134f`.
- **T2 — Session-scoped key store minted for `workflow-*` skills** — **done**. Commit `3ae9c94`.
- **T3 — Inactivity expiry and removal of per-message deletion** — **done**. Commits `f652ddb` and `1993a8e`.
- **T4 — ISO-timestamped per-occurrence logging** — **done**. Commit `83311d0`.
- **T5 — Parentage, inherited authority and purge of a child's self-minted key** — **done**. Commit `21e59c0`.
- **T6 — Require an adapter key; bare router key is insufficient** — **done**. Commit `d27d2d1`.
- **T6a — Refresh the parent key from child activity (native review finding R3-inherited-expiry, CRITICAL)** — **done**.
- **T7 — Per-route stage table and worker mutation gating on required artifacts** — **in progress**. T7a (the ODD bootstrap write gate) is implemented. T7b (guard side) is implemented in this change: the declarative per-route stage table and ancestor-chain artifact resolution. The host-side append operation and ledger move remain separate units in the agent-sandbox-integration project.
- **T7a-fix — Correct the review's three T7a advisory findings (R3-sandbox-catchall, R3-odd-marker-gap, R3-child-session-regex)** — **done**.
- **T8 — Bug-fix route with its own stages and no ODD tracker** — **planned**.
- **T9 — Native review outcome recorded (lineage review-16c862492747259a)** — **done**.

## Acceptance criteria
- A session with only a `workflow-route` key warns on gated tools.
- A session with an unexpired adapter key does not warn.
- A child's authority follows its parent's adapter-key validity.
- Every gated occurrence is logged with a timestamp.
- Nothing blocks while warn-only is in force.

## Authorized scope
The authorized implementation scope is the routing-guard plugin change and this task tracker. No commits, deployment, verifier/health-plugin edits, configuration edits, or ledger edits are authorized by this task.

## Checks
- Run `bun build global-config/plugins/systematic-routing-guard.ts --target=bun --external @opencode-ai/plugin --outdir /tmp/guard-odd-stage-check` for T7a.
- The verifier load-checks every deployed plugin by executing it with Bun from a scratch cwd and timeout; syntax/parse and unresolved named-export errors fail, while other import-time errors are informational.
- `bun build` does not resolve named exports, so every plugin change must also be validated by EXECUTING the module (`bun global-config/plugins/systematic-routing-guard.ts` must exit without a SyntaxError).
- Confirm `context.directory` is absent from the plugin; verify `ODD_TRACKER_PATTERN` references and warning behavior remain warn-only.
- The module-execution verification rule is stated in `WORKFLOW.md` and in the recovered `global-config/AGENTS.md` block.
- After each commit, assess RDD with an explicit base ref; assessments to date returned `review_due: false` with reason `under_budget`.
- Correction for native review finding `R3-inherited-expiry` was produced under the review's correction budget: 200 lines, 30 declared.
- Review live warning evidence in `~/.local/share/opencode/logs/routing-guard.log`; ROUTER-LOG.md records live log evidence for the initial key-backed gate at row 98.

## Progress
The assessed slice accumulates from boundary `65b1f35`. Completed commit sequence recorded for this task: `2c0134f`, `3ae9c94`, `f652ddb`, `1993a8e`, `83311d0`, `21e59c0`, and `d27d2d1`; T6 is done, T6a corrects native review finding `R3-inherited-expiry` (T7 is in progress, T7a implemented in the accumulated slice), and T8 is planned. This unit implements T7b's guard side: route stages are declarative and artifact markers resolve through up to three ancestor levels. This change implements the ODD bootstrap write warning: before the session's `odd/tasks/<feature>.md` tracker is observed, valid ODD-key sessions warn only on mutations with a known non-tracker target path. Native review `review-17a7dab1e332596a` ran on the accumulated slice (401 lines, 5 paths, medium tier), selected the reliability lens, admitted a refuter, and returned one CRITICAL candidate-caused finding, `R3-inherited-expiry`, which this change corrects. No commit has been created. The slice continues to accumulate from `65b1f35`; take native review when assessment returns `review_due` (`slice_budget_reached`), then advance the boundary. T7a-fix corrected `R3-odd-marker-gap` and `R3-child-session-regex`. `R3-sandbox-catchall` was not reproducible in the candidate — the gate already matched only the explicit tool set and the host prefixes, with no blanket `sandbox_` rule — so no code change was made for it; the advisory finding was a false positive. This follow-up preserves compatibility with legacy `artifact-odd-<stage>` markers so they remain recognized after the stage table's naming change.

The high-risk candidate (12 paths, 489 lines) was reviewed end to end under lineage `review-16c862492747259a`: all four lenses (risk, resilience, readability, reliability) were admitted; risk and readability were clean; and the review was APPROVED and then acknowledged (`authority: burned`). The earlier CRITICAL finding `R3-inherited-expiry` was corrected and is contained in this approved candidate.

## Advisory follow-ups (non-blocking, from review-16c862492747259a)
The provider recorded these as non-blocking and never as a reason to re-run review on this candidate.
- `R3-sandbox-catchall` — WARNING — `global-config/plugins/systematic-routing-guard.ts:447` — `isRoutingGateTool` matches every `sandbox_` tool, gating read-only worker tools the documented scope excludes. **Not reproducible in the candidate: `isRoutingGateTool` matched only the explicit tool set, with no `sandbox_` prefix rule. No code change required.**
- `R3-odd-marker-gap` — WARNING — `system-routing-guard.ts:656-672` — The tracker marker is set only for `sandbox_write`/`sandbox_edit`, so satisfying the bootstrap via apply/copy leaves persistent false warnings. **Addressed by T7a-fix.**
- `R3-child-session-regex` — WARNING — `system-routing-guard.ts:775` — Parentage uses an unanchored `/ses_[A-Za-z0-9]+/` and can corrupt the wrong session's key directory. **Addressed by T7a-fix.**
- `R3-missing-key-tests` — WARNING — `system-routing-guard.ts:238-431` — No automated assertions cover key expiry, inheritance, parent refresh or bootstrap ordering.
- `R3-unawaited-key-io` — SUGGESTION — `system-routing-guard.ts:655` — Void-launched refreshes can race status reads and cause transient warnings.
- `R4-001` — WARNING — `system-routing-guard.ts:410` — Nested sessions do not inherit through an already-inherited parent, so their gated calls log as unauthorized.

## Route and trigger evidence
Route: delegated. Specialist: `general` sandbox writer. Triggers fired: mapping (4+ files), writer (2+ non-trivial files), preparation, and long-session backstop. The task is a global tooling change. The historical tracker is being created after the first implementation source edit, contrary to protocol; see Debt.

## Delivery strategy
`accumulate`, per the owner's decision. This candidate was reviewed and its boundary advanced on acknowledgement, so the accumulated slice restarts from the approved candidate. Keep the per-commit reviewability caps and checks.

## Next step
Continue T7 with the remaining route-stage coverage; T7a was committed as `af1a841` and reviewed inside lineage `review-16c862492747259a`. T7a-fix's three advisory corrections are recorded under the T7 work unit.

## Warn-log audit (2026-09-30)

The log `~/.local/share/opencode/logs/routing-guard.log` held 131 lines across four message generations.

Genuine warnings:
- This orchestrator session (`ses_f270b9eafffeFfcM9pOx6jrScb`) generated warnings across dozens of lines because it never loaded a route or adapter skill.
- A second orchestrator session (`ses_f63454890ffej5Y5gIUDN4HFKf`) generated warnings covering `task`, `host_review_status`, `host_review_assess`, `host_review_start`, `host_review_recover`, `host_review_acknowledge_approved`, and `host_git_push`; it never held an adapter key.

False positives had three causes:
- (a) Per-message key deletion, lines 4-47, fixed in `f652ddb`/`1993a8e`.
- (b) The in-memory AND-condition, lines 8, 11, 24, 28, and 43, fixed in `1993a8e`.
- (c) The per-session and project-blind artifact marker: lines 85-100 and 127-130 write to config and to the guard itself while `odd/tasks/routing-guard-keys.md` existed; lines 79-83 write into the agent-sandbox-integration project, where a marker can never be satisfied.

Lines 99-100 are the `R3-odd-marker-gap` case in the wild, removed by T7a-fix.

## T7c — full route and stage design (2026-09-30)

A route declares an ordered list of stages. Each stage carries (a) the evidence that clears it — a project-relative artifact pattern or a skill-use marker — (b) the actions it gates, and (c) the specialists it allows. Gates remain warning-only until the warn log is clean.

### Observation point and limits

The guard observes the `skill` tool and mints a per-session marker for each skill actually loaded (`ce:plan`, `ce:brainstorm`, `ce:review`, `ce:work`, `reproduce-bug`). This makes a worker subagent's adherence to its required Systematic workflow observable and lets a stage refuse a specialist whose preceding stages are unmet. The honest limit: where a stage has no file evidence, the system gates attention (was the skill loaded), not completion (was the work done).

### Stage tables by route

- `workflow-systematic` (small feature, bug, substantial non-SDD), with requirements, plan and review stages implemented in T7c:
  - Requirements: `docs/brainstorms/*-requirements.md` or `ce:brainstorm` marker; gates `ce:plan`.
  - Plan: `docs/plans/*-plan.md` or `ce:plan` marker; gates `ce:work` and writing specialists.
  - Review: `.context/systematic/ce-review/<run-id>/review-summary.json` or `ce:review` marker; gates `host_review_start`.
- Learnings are deferred because the post-archive condition is not observable yet.
- `workflow-sdd-secure`, currently zero stages:
  - Proposal: `openspec/changes/<change>/proposal.md` or phase marker; gates `sdd-spec` and `sdd-design`.
  - Spec and design: gates `sdd-tasks`.
  - Tasks: `tasks.md`; gates `sdd-apply` and `systematic-implementer`.
  - Apply/verify: gates archive.
- `workflow-odd-secure`:
  - Tracker: tracker is built; gates non-tracker mutations.
  - Review: a CONTINUOUS STATE, not an artifact — see Review stage semantics below.
- Bug-fix route (T8), no tracker:
  - Reproduce: `reproduce-bug` marker; followed by `ce:work`, then `ce:review`; gates `host_review_start`.
- `workflow-route` stays stageless; it is the classifier.

### Review stage semantics (owner-corrected)

Do not require a review start per change. The provider's own model is a slice: commits accumulate against a budget until a review is due. The guard observes the assessment verdict: `review_due: false` sets a cleared marker; `review_due: true` clears that marker. Work-unit commits gate on “not due.” `ce:review` keeps its own stage gating `host_review_start`, per native review rather than per commit.

### Order correction (owner-corrected)

For a substantial feature the order is requirements → plan → tracker → implement. Brainstorm and planning precede the tracker, while the tracker still precedes the first source edit.

### Gaps and boundaries

Stages with no file evidence: `ce:work` execution, bug reproduction, the tiny-fix structural readback, the documentation route, `ce:review` in report-only mode, and the ODD route/trigger declaration stored as prose in the tracker. Stages written outside the project: the key store and markers, the gate log, Magic Context, and native review state. A residual: a tracker created via `sandbox_apply` rather than `sandbox_write` does not mint its marker, because apply exposes no path.

### Implementation order

1. `skill` observation plus specialist allow-lists — **implemented** in this unit: skill loads are recorded per session, child artifact/skill markers merge into the parent on task-result arrival, and the ODD tracker stage allows only `general` and `systematic-implementer` after its artifact is observed. The skill-load branch read the wrong argument object, so skill markers and skill-key minting were inert; it now reads `output.args` with a fallback. The plugin failed to load entirely because it imported `COPYFILE_EXCL` as a named export from `node:fs`, which this runtime does not provide; the import now uses `constants`.
2. `workflow-systematic` stages — **implemented** in this unit: requirements, plan and review stages resolve from project-relative artifacts or recorded skill markers; skill-load prerequisites and `host_review_start` warn when their required stage is unsatisfied. The learnings stage is deferred because the post-archive condition is not observable yet.
3. `workflow-sdd-secure` phase-agent gating — remains.
4. The review-due marker from the assessment output — remains.
5. The durable project-scoped signal with the global store in the agent-sandbox-integration project — remains.

This session itself skipped `ce:brainstorm`, `ce:plan`, and `ce:review` while subagents used `ce:work`; that is the asymmetry this design targets. The stage machine would have flagged this session first.

## Debt
- This tracker was created after the first implementation source edit, contrary to protocol.
- Work-unit commits went to `main` rather than a feature branch.
- No delivery strategy was selected at tracker creation.
- The host commit tool rejects multi-line messages, so the `ROUTED:` trailer has to sit on the subject line rather than in the commit body.
- Lineage `review-17a7dab1e332596a` remains open in state `correction_required` (its targeted validator never completed—a relay refusal, then a provider outage), superseded by the approved lineage; its disposition is unresolved.
- Project-blindness persists because no trustworthy session-project source exists, so a marker cannot satisfy a stage artifact for a different project; the host-side append operation and ledger move are tracked as separate units in the agent-sandbox-integration project.
- The Magic Context mirror stores the tracker body newline-flattened, so a verbatim write-back from the mirror collapses this file's markdown structure; restore from git and re-apply sections as real multi-line markdown.
