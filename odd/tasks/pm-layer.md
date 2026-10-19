# Project-manager layer

## Objective
Restore workflow compliance by moving route execution out of the long orchestrator session into
short, route-specific project-manager (PM) subagent sessions, one per work unit.

## Problem
The orchestrator's prompt is 70,817 characters and the global `AGENTS.md` 23,513; the routing
rules are lost in long sessions. Stage markers and keys also accumulate across changes in one
orchestrator session.

## Scope
Design and work items: `docs/handoffs/2026-10-04-pm-layer-workflow-optimisation.md` (Handover B).
Cross-project request: `docs/handoffs/2026-10-04-pm-layer-agent-sandbox-integration.md`
(Handover A; the owner passes it across).

## Decisions (owner, 2026-10-04)
- One PM session per work unit, not per feature. State between units lives in the tracker.
- The orchestrator dispatches only `explore` and `pm-*`, and keeps `host_register_project`.
- `subagent_depth` 3 → 4.
- Separate handovers for the agent-sandbox-integration agent and for this repository's agents.

## Constraints
- Forward-compatible by default; `pm-sdd` is the only V1-only part.
- Non-destructive rollout: `gentle-orchestrator-legacy` stays selectable until Q61.
- Warning-only guard, as today.
- Every source change needs the deploy step: verifier mirror, owner restart, verifier pass.

## TDD
Mode: on for guard and verifier changes (owner strategy: spec and tests first). Runners:
`HOME="$(mktemp -d)" bun test tests/routing-guard`; `python3 -m unittest discover -s tests`;
`bash verify-workflow.sh`.

## Delivery
Strategy: `ask-on-risk`. Forecast: above 400 authored lines in total, so one work-unit commit per
task, each assessed against the last reviewed boundary.

## Tasks
- [x] T0 — Plan and the two handovers. Route: inline (Claude Code, advisory; the content is the
  planner's own analysis). Trigger: owner request.
- [x] T1 (Q53) — Probe with `pm-probe` and depth 4; record the eight observations. Probe work is complete; item 4 remains unobserved and its placement is deferred to Q55.
- [x] T2 (Q54) — Complete from the owner-relayed Handover A report; identity policy, sandbox refusals and five probe answers recorded below. The later live correction records that `pm-probe` removal is unverified; see Correction C.
- [ ] T3 (Q55) — implementation landed in commit `8980254`: `docs/specs/pm-handoff.md`, four agent registrations, guard coordinator admission, and regression tests. The post-code advisory review is complete (recorded at `:304-317`). The contract-completeness and unit-start branch-verification text landed in `docs/specs/pm-handoff.md` in commit `551b7d3`; this closes that documentation acceptance, not the PM pilot. The earlier claim that `pm-probe` was removed is superseded by Correction C. Route-specific classification is verified, but hard rejection is not (the guard is warning-only). Q55 remains open for the later pilot steps recorded under T4/T6: Q58's unguarded `pm-odd` bootstrap execution and independent relay-delivery evidence, then Q56's ten consecutive units after enforcement is live. Route: delegated to `odd-apply` on branch `chore/pm-layer-completion`.
- [ ] T4 (Q56) — Pilot `pm-odd` on global-tooling units; ten units without route escape.
  - Sequence: (1) run the verifier mirror, then restart `sandbox-broker.service` and
    `secure-opencode.service`; (2) run the `pm-odd` smoke test, recording that
    `host_register_project` is absent from the registered tool set (tool-registration-layer
    control, not a broker refusal) and one permitted `host_git_commit` or `host_review_start`;
    (3) verify `pm-probe` removal through effective broker policy, installed plugin bytes, and a
    dispatch that fails (a restart alone does not apply the canonical config); (4) execute Q58
    through `pm-odd` as a bootstrap unit, with its review independently driven; (5) start Q56's
    ten-unit count only once Q58's enforcement is live.
  - Q58 is the bootstrap exception only and does not count toward the ten consecutive units without
    route escape: its own route-key enforcement is not live during its execution. The unit that
    establishes review independence must not itself be reviewed without it; therefore Q58's review
    is driven by the orchestrator or another coordinator, not its implementing `pm-odd` session.
- [ ] T5 (Q57) — Slim orchestrator prompt and permissions; `AGENTS.md` split; `WORKFLOW.md` and
  skills.
- [ ] T6 (Q58) — The guard-ordering slices are complete and shipped, but the `pm-odd` bootstrap
  run has NOT been executed. Relay-delivery proof must come from a dispatch outside the coordinating
  PM session, with a genuine provider-issued binding; Q54 reported reachability only, so context
  delivery remains UNVERIFIED. It may run through `pm-odd` as Q56's
  bootstrap unit only (see T4); its own enforcement does not exist during execution, so it runs
  unguarded by design. Its review must not be self-driven.
  Before Q58 starts, Q56's other gates must pass: both service restarts and the live-policy smoke
  test. Removal-check evidence is reconciled below: (c) PASSED; (a) and (b) PARTIALLY PASSED, with
  the broker deny path unobservable and its separate identity list unverifiable from this workspace.
  Do not characterize those partial findings as full passes.
  - Requirement — IMPLEMENTED, warning-only as designed (recorded in commit `e9bffc0`): a PM must hold its own
    route's adapter key before `host_review_start` (`pm-odd`→`workflow-odd-secure`; `pm-systematic`→`workflow-systematic`), as for
    `host_git_commit` or a writer dispatch. The guard binds the persisted latest-message agent, resolves the required
    skill with `pmRequiredRouteSkill`, and checks the PM's own-directory key for `HOST_MUTATION_GATE_TOOLS`/`host_review_*` (`global-config/plugins/systematic-routing-guard.ts:877-895`, own-dir `:562-576`, `isRoutingGateTool` `:578-583`).
  - A relay grant without the matching route key must not admit a review; permission alone is
    not readiness.
  - **Owner decision: enforced independence.** The coordinating PM cannot dispatch relay lenses;
    review is driven from outside the PM session. Q58's route-key rule is necessary but not
    sufficient: it verifies that the PM loaded its route skill, not that the reviewer differs from
    the author. Independence requires lane separation, not the key rule alone.
  - **Q58/Q61 evidence consequence:** relay-delivery proof must come from a dispatch outside the
    coordinating PM session, not from the PM itself. No PM is required to prove its own relay
    delivery.
  - **Open question — undecided:** each PM still holds `host_review_start` and review lifecycle
    tools, so a PM can start a review it cannot complete without relay lanes. Options:
    (a) the PM keeps `host_review_start` and another actor drives the lens; or
    (b) review start also leaves the PM session. Do not resolve this here.
  - The verifier rule `RELAY_TASK_GRANTED_OUTSIDE_ORCHESTRATOR` allows PM relay grants, but does not
    require them; removing the lanes from `pm-odd` and `pm-systematic` satisfies its assertion.
    `pm-sdd` remains without relay targets because it does not launch native RDD.
- [ ] T7 (Q59) — Verifier coordinator-set checks must assert the PM identity surface as well as
  prompt budgets, behavioural probes and digest pin; Q54's bound identity is inferred because
  the broker does not echo identity on permitted calls.
- [ ] T8 (Q60) — Model assignment, after the external advice.
- [ ] T9 (Q61) — Remaining routes; remove the legacy agent; `ce:compound`.

## Acceptance criteria
1. A change request dispatches exactly one PM and no writer from the orchestrator.
2. A PM completes a unit in route order and returns a well-formed envelope; the orchestrator's
   read-only check matches it.
3. Human input returns to the same PM session.
4. Orchestrator and PM prompts stay within their budgets, enforced by the verifier.
5. Ten consecutive pilot units complete with no route escape.

## Advice record
- T0, pre-code, Claude Code (external, advisory, 2026-10-04). Findings, all carried into
  Handover B:
  1. Not code-free: host mutations are bound to `gentle-orchestrator` in the sandbox broker and
     plugin. Resolved by Handover A (Q54).
  2. A PM per feature would decay like the orchestrator. Resolved: one PM per work unit.
  3. A Sol PM shares a family with `general` and two pre-code advisors. Carried to Q60.
  4. Unverified runtime behaviour (subagent `question`, review relay and `ce:*` skills from a
     subagent, key state on resume). Resolved by the Q53 and Q54 probes before any build.
- The registered `advisor-*` pre-code advice is still owed for T3 onwards and is recorded per
  task.
- T3/Q55 follow-up on commit `8d40f97`, post-code advisors (advisory evidence only; not approval):
  - `advisor-integration-post` (verified): `pm-probe` removal is complete and safe in the committed
    source: no surviving reference in `global-config/opencode.json` or `verify-workflow.sh`; the
    orchestrator Task allow-list and verifier `required_agents`/`pmAgents` lists contain only the
    three production PMs, and the renamed verifier list has no stale referent. Positive control:
    any survivor would occur as a JSON agent block, a `permission.task` allow entry, or a verifier
    list member. Sequencing gap: restart both services and run the live smoke test, then perform the
    three removal checks, then Q55's review, all before the pilot. Highest-risk assumption: that
    identity policy is live and `pm-odd` is bound as intended. Retire-test: restart
    `sandbox-broker.service` and `secure-opencode.service`; from one `pm-odd` session confirm one
    denied `host_register_project` and one permitted `host_git_commit` or `host_review_start`.
  - `advisor-security-post` (advisory evidence): **HIGH — self-review loop:** one PM session can
    dispatch the writer, commit, start native review, dispatch the relay lens, capture its result,
    and acknowledge approval. Q58's route-key-before-review rule is unimplemented; the guard is
    warning-only; and the broker identity table grants every PM every mutation without route
    distinction. `WORKFLOW.md` states review independence is intended, but nothing enforces it.
    **Reachability:** `frontend-apply`, `frontend-apply-local` and `frontend-dev` have a
    `permission.task` wildcard ask rule, enabling dispatch to any named subagent including a PM;
    mitigation is to remove only those wildcards and preserve explicit targets. **Live/committed
    drift:** until both services restart, the running broker still defines `pm-probe` with
    `reviewStart` and `gitCommit`, and running OpenCode still accepts it as a dispatch target;
    committed removal is not live. Ranked mitigations: (1) drop the three frontend wildcards;
    (2) perform both restarts; (3) implement Q58's route-key rule before the pilot.

## Progress
- 2026-10-05: Q55 (T3) implementation landed in commit `8980254`. Files: `docs/specs/pm-handoff.md`,
  `global-config/opencode.json`, `global-config/plugins/lib/routing-guard-helpers.ts`,
  `global-config/plugins/systematic-routing-guard.ts`,
  `global-config/skills/workflow-odd-secure/SKILL.md`, `odd/tasks/pm-layer.md`,
  `tests/routing-guard/routing-guard.test.ts`, and `verify-workflow.sh`. The test run finished
  with 53 passed / 0 failed; the red-first run had 4 failures. The implementation delivers the
  handoff contract, PM agents, ODD writer, coordinator guard admission and five regression cases.
  At that time `pm-probe` was retained pending Q54. Q54 has now closed the probe and licensed
  removal in this unit. T3 remains IN PROGRESS: the post-code advisory review is still owed;
  acceptance also remains open because the guard is warning-only and pilot evidence is deferred.
  The Q58 requirement that PMs hold their own route key before `host_review_start` is recorded
  above. The later owner decision requires enforced independence: PM relay lanes are removed, and
  relay-delivery evidence must be dispatched outside the coordinating PM session. The verifier's
  admission rule permits PM relay grants but does not require them. Acceptance evidence and the
  required metadata/mirror close-out remain pending.
- 2026-10-05: Q55 advisory review ran in design scope (seven findings) and integration scope;
  testing scope was not run because guard tests had a red-first run. This did not discharge the
  required post-code advisory review, which remains owed. The contract folds in commit ownership,
  review assessment as a `DONE` conjunct, the reviewability receipt, brief schema identity,
  route-specific post-code advice, RDD mode/source brief inputs, log-backed routing-gate
  observations, and explicit metadata worker/commit/failure handling. The verifier asserts PM
  non-execution permissions, the `odd-apply` writer shape, and its PM-only task allowlist.
  Deferred: `COORDINATOR_PATTERNS` still treats any `pm-*` name as a coordinator without registry
  cross-check; `workflow-sdd-secure` has no `ROUTE_STAGES` entry; the warning-only guard leaves
  the three-way invariants unenforced; and the behavioral probe does not exercise PM agents
  (Q59/T7 territory). T3 remains open.
- 2026-10-04: T0 done. Facts verified against `global-config/opencode.json`, the guard helpers,
  `verify-workflow.sh`, the OpenCode 1.18.34 binary (Task `task_id`, depth check, child
  permission derivation) and agent-sandbox-integration (`sandbox-tools.ts:64`,
  `broker/src/config.ts:243`, `broker/src/service.ts`). Branch `docs/pm-layer-handovers`.
- 2026-10-04: T0 committed as `bd7835c`. Assessment from `main`: medium, `slice_budget_reached`.
  Native review `review-314b7602882be12e` (one lens, reliability): approved and acknowledged;
  authority burned. One advisory suggestion (Q54 and Q55 can run in parallel) applied to the
  Phases line in `docs/TODO.md`. Reviewed boundary: `bd7835c`.
- **Observed — abandoned native-review lineage (2026-10-06):** Gentle AI 3.7.0 (stable, protocol
  1.5) review `review-df3efa401830a824` reached `correction_required`, then required
  `intended_untracked_selection_required`. The required exact
  `gentle-ai.review-intended-untracked-selection/v1` JSON schema was unavailable through the CLI,
  so the lineage could not be advanced. The supplied recovery command failed after caller-authored
  `--actor` and `--reason` flags were appended; the `--reason` value was silently captured as an
  untracked path, poisoning the successor lineage's inventory. Successor
  `review-df3efa401830a824-s1` is abandoned. Run provider-returned lifecycle commands verbatim
  with no added flags, as already asserted in `docs/TODO.md` around line 590 and
  `docs/TODO-HISTORY.md` around line 104. The CLI also reported pre-existing store-integrity damage
  and unsupported automatic repair; details and affected lineage IDs are tracked in `docs/TODO.md`
  Q63. No `.git` store files were inspected or edited.

### Q53 probe results
- **Item 1 PASS** — Four-level chain executed end to end: orchestrator → `pm-probe` (`ses_ef76d56c2ffeiKOhXlYSHVZ3KP`) → `frontend-dev` (`ses_ef76d1349ffeMfRV4Yyur0n4Uq`) → `frontend-apply` (`ses_ef76ceca5ffeil6DlZlHAyGf60`) → `vision` (`ses_ef76cd241ffepugoicm9Up9w7S`). No permission or depth gate fired.
- **Item 2 PASS** — Loading `workflow-odd-secure` minted `workflow-odd-secure.key` in the PM session (`{"skill":"workflow-odd-secure","specialists":[]}`) and added a `skill-workflow-odd-secure` marker. Every child carried `.parent` and `inherited.key`; `frontend-dev` inherited directly, and the rest transitively.
- **Item 3 PASS** — A subagent `question` call reached the user and returned their answer. A failed relay was not needed.
- **Item 4 UNOBSERVED** — No ask-gated prompt could be produced from `pm-probe` because its tool grants deny every ask-gated tool by design. This must be tested with the real Q55 PM agents, which hold those grants.
- **Item 5 PASS** — Resuming the same PM session with `task_id` retained its earlier context: it recalled a recorded token, a memory-write count, the loaded skill, and the user's answer without re-deriving them.
- **Item 6 PASS (with caveat)** — The expired-key path was exercised. Guard log `~/.local/share/opencode/logs/routing-guard.log` line ~8940 (2026-10-04T21:16:29Z) records `routing gate: task is not authorized … (workflow key status: expired (workflow key expired) …)` for the orchestrating session, i.e. a dispatch made after the 30-minute inactivity TTL had lapsed. Recovery verified in prospect: probe session `ses_ef7397de9ffeudGDGF7zIMF8Wn` started with **no key** (`status=missing`, log line ~8943), loaded `workflow-odd-secure`, which minted its own key (`minted_at` 2026-10-04T21:20:44.548Z), after which its next dispatch logged `status=valid` (line ~8945) with no warning.
  - **Caveat:** the probe did **not** itself inherit and then lose an inherited key — it had no `.parent` and no `inherited.key` at all, so the specific "inherited orchestrator key expires" scenario was not reproduced in that session. The expired condition is nonetheless directly evidenced by the `status: expired` log lines for the dispatching session.
- **Finding (warnings are log-only)** — A gated call that trips the gate still succeeds; no warning text is returned in the tool result. The violation is written to the server console and `routing-guard.log` only. Q58 enforcement must read the log rather than the call outcome.
- **Finding (inheritance is not guaranteed at session start)** — Probe `ses_ef7397de9ffeudGDGF7zIMF8Wn` was a root: no `.parent`, no `inherited.key`, no session directory until it acted. Item 1's probe, by contrast, had `.parent` and `inherited.key`. The parent marker is written when a child dispatches, so a PM must never assume inherited authority on entry and must load its route skill first. This reinforces the design; it does not contradict it.
- **Finding (key refresh cadence)** — After a dispatch, `last_active` advanced ~15 s after the logged `status=valid` check, consistent with `ROUTING_KEY_REFRESH_INTERVAL_MS = 60_000`. Recorded as an observation; the writing call was not instrumented.
- **Finding (adapter key is the live one)** — `workflow-route.key` can be stale while `workflow-odd-secure.key` is fresh: the guard refreshes the active adapter key from child activity. Compare adapter keys, not the route key, when assessing TTL. **Note:** file mtimes are local time; the guard log is UTC (a one-hour offset at this time of year).
- **Item 7 PASS** — `workflow-systematic` and `ce:plan` both loaded in a PM session under the workflow guard with no failure code. The Systematic workflow guard reported `state=waiting, reasonCode=missing-evidence, enforcement=observe`. A repeat skill load neither re-minted a key nor bumped `last_active`; this is recorded as a finding.
- **Item 8 PASS** — `ctx_memory` write (id 1087), read-back, and `ctx_search` hit all succeeded with no denial or gate.
- **Finding (item 1/2)** — A Task-dispatched session carries no `.parent` and no `inherited.key` until it dispatches a child of its own; the parent marker is written on the child's dispatch. Q58 must not assume a PM has a parent link on entry.
- **Finding (item 2)** — `inherited.key` `minted_at` values were not monotonic with chain creation order. This is recorded as an observation only, with no mechanism asserted; investigate before Q58 gates on key state.
- **Routing-guard log path** for future probe evidence: `~/.local/share/opencode/logs/routing-guard.log`. A plain workflow-key mint writes no line there.
- **Item 4 remains UNOBSERVED** — deferred to Q55's PM agents, which hold ask-gated tools.
- **Next step:** T1 probe work is complete; item 4's placement is deferred to Q55.

- **Retraction (third claim)** — Retracted the assertion that "the parent's adapter key is not being refreshed from child activity." It was falsified by `workflow-odd-secure.key` showing `last_active` matching its own file mtime while `workflow-route.key` was simply stale; see `CLAIM-RETRACTIONS.md`.

### Additional probe findings — 2026-10-05 (superseded by Q54 report below)

- At that time host binding/resume could not be observed because `pm-probe` lacked the required
  host tools, relay dispatch was blocked by its task allowlist, and sandbox reads returned
  `unknown session` rather than a refusal. Q54's owner-relayed report later supplied probe answers
  and the intended fail-closed sandbox policy; it does not change the provenance of those earlier
  observations.
- The 2026-10-05 depth assessment remains historical. Q54's owner-relayed report states no
  depth-sensitive behavior was found in broker/plugin code and that raising depth 3→4 should not
  affect binding, worker initialization or relay session-root resolution.

### Q54 handover — owner-relayed external report (2026-10-07; not independently observed here)

- **Broker identity table:** `HOST_MUTATION_IDENTITY_OPERATIONS` enforces identity restrictions
  beyond host permission grants: `gentle-orchestrator` receives every `HOST_MUTATION_OPERATIONS`
  entry; `pm-odd`, `pm-systematic` and `pm-sdd` receive every entry except `registerProject`;
  `pm-probe` receives exactly `reviewStart` and `gitCommit`. `registerProject` remains
  orchestrator-only. All five identities are refused by `sandbox_read`, `sandbox_list`,
  `sandbox_grep`, `sandbox_diff`, and sandbox mutation tools: no PM enters the sandbox.
- **Five reported answers:** (1) Subagent binding YES: `host_git_commit` returned “cannot commit:
  no applied B→C result for this session” and `host_review_start` returned the SDD runtime's
  “untracked files require an explicit declaration”; these business errors imply authorization
  passed and no `HOST_MUTATION_*` denial appeared. The bound identity is inferred to be `pm-probe`:
  the broker echoes no identity on a permitted call. (2) Resume YES: binding survived `task_id`
  resume; whether via per-turn re-send or idempotent rebinding was not observed. (3) A depth-1
  review relay was reachable but delivery untested: dispatch refused at the frame layer because
  the relay prompt lacked provider-issued review binding, not because of session-root/parent
  resolution; full `GENTLE_AI_REVIEW_CONTEXT` delivery remains unobserved. (4) PM read surface:
  `read`, `glob`, AFT, CodeGraph, AST-grep, context tools, and host read operations (open to all
  agents); no host bash or sandbox tools. (5) No depth-sensitive behavior was reported in
  `broker/src/**` or `opencode/plugins/**`; `subagent_depth` appears only in documentation, and
  raising depth 3→4 should not change binding, `ensureWorker`, or relay session-root resolution.
- **Operations and warning:** Required restarts are `sandbox-broker.service` and
  `secure-opencode.service`. Check installed plugin bytes before classifying an unbound-looking
  result as a hook defect: the first probe returned `HOST_MUTATION_UNKNOWN_AGENT` because the
  installed plugin still listed only `gentle-orchestrator`; the hook was fine.
- **Removal condition and closure:** Effective broker policy, installed plugin bytes, and refusal
  of mutations from a previously bound probe session must be verifiable. The probe is recorded
  closed as of this unit, licensing removal; those external/runtime checks were not independently
  performed in this workspace. Q54 is complete from the owner-relayed report, with review-relay
  delivery explicitly unverified.

### Corrections to the Q54 report — observed 2026-10-07

- **Correction A — broker grant versus reachable tools:** The broker grant is every
  `HOST_MUTATION_OPERATIONS` entry except `registerProject`; the reachable surface is the
  intersection of that grant with tools registered to the session. In the observed live
  `pm-odd` session, the host-mutation tools actually registered were `host_git_commit`,
  `host_review_start`, `host_review_acknowledge_approved`, `host_review_capture_result`,
  `host_review_capture_refuter`, `host_review_capture_validation`,
  `host_review_capture_correction_plan`, `host_review_capture_unachievable`,
  `host_review_recover`, and `host_review_validate`. It did not hold
  `host_git_push`, `host_gh_issue_create`, `host_plan_append`, or
  `host_sandbox_result_install`. This change adds `host_git_push` and
  `host_sandbox_result_install`; `host_gh_issue_create` and `host_plan_append` remain absent by
  design. The broad broker grant does not itself mean every operation is reachable from a PM.
- **Correction B — live `pm-odd` smoke test:** After the owner restarted services,
  `host_git_commit({"message":"test: identity probe"})` returned the business error
  `cannot commit: no applied B→C result for this session`. `host_review_start({})` returned
  the runtime business error `the candidate has no pending changes; already-committed work can
  be reviewed by rerunning review start with --base-ref <commit>`. No `HOST_MUTATION_*` token
  appeared in any response. `host_register_project` is absent from the session's registered
  tool set, so its deny path is unobservable for `pm-odd`: the call never reaches the broker.
  This is a tool-registration-layer control, not a broker refusal. Verdict: identity binding is
  **confirmed live for permitted operations**; the deny path is **unobservable**, not refuted.
  The security advisor's author→commit→review→approve loop is **confirmed reachable**: commit,
  review start, capture, and acknowledge are all in the observed tool set.
- **Correction C — check (c) FAILED:** A Task dispatch to `pm-probe` still succeeded and the
  session still carried its Q53 probe brief. The canonical→live mirror had not run since commit
  `8d40f97`, so `~/.config/opencode/opencode.json` still defined `pm-probe`; restart alone applies
  nothing. Correct deployment sequence: verifier mirror → restart. Removal remains unverified
  until a dispatch to `pm-probe` fails. Positive observation: the still-live `pm-probe` session
  correctly refused an instruction shaped like a liveness beacon rather than complying.
- **Correction D — deployment verification (observed after commit `ae24a7f`):** Check (c) PASSES:
  a Task dispatch to `pm-probe` returned `Unknown agent type: pm-probe is not a valid agent type`;
  the removal is live. The canonical→live deployment chain is confirmed end to end: commit →
  verifier mirror → restart → live. A restart alone applies nothing; this was the observation that
  proved the order matters. The live `pm-odd` tool set was verified at 12 host-mutation tools:
  `host_git_commit`, `host_git_push`, `host_review_acknowledge_approved`,
  `host_review_capture_correction_plan`, `host_review_capture_refuter`,
  `host_review_capture_result`, `host_review_capture_unachievable`,
  `host_review_capture_validation`, `host_review_recover`, `host_review_start`,
  `host_review_validate`, and `host_sandbox_result_install`. `host_gh_issue_create` and
  `host_plan_append` are absent by design. Resume was re-confirmed: resuming the earlier
  `pm-odd` session retained its prior conversation, a second independent observation of the
  `task_id` resume behaviour (the first was the synthetic probe). In this unit, `pm-sdd` was
  extended to the same 12 host-mutation tools, with `host_sdd_archive_compose` retained as its
  route-specific extra.

- 2026-10-14: Q55 contract-closure work started. At that point `docs/specs/pm-handoff.md` stated the unit-start branch obligation at `:15` and `:19` without naming a mechanism, so the live `pm-odd` run could not perform it and blocked. The candidate was a bounded `read` of `.git/HEAD`; the completed procedure is recorded below and the contract text landed in commit `551b7d3`. The post-code advisory also identified missing deterministic procedures for an absent or unrecoverable tracker mirror, an unverifiable `last_reviewed_boundary`, and outstanding prerequisite checks; those procedures also landed in `docs/specs/pm-handoff.md` in `551b7d3`. The live PM execution/pilot evidence remains open. Branch `chore/pm-layer-completion` (owner decision: the branch is for the PM-layer completion).

- 2026-10-14: T1 (Q55) — contract text landed in commit `551b7d3` on branch `chore/pm-layer-completion`, in `docs/specs/pm-handoff.md`. The brief-in field list adds `feature_branch` (`docs/specs/pm-handoff.md:5-8`). The route-validation section names the criterion (the exact branch named by the brief), mechanism (read `.git/HEAD` and compare it with `ref: refs/heads/<feature_branch>`), PASS condition, and BLOCKED hazards (`docs/specs/pm-handoff.md:13-20`); absent/unrecoverable tracker or Magic Context mirror, unverifiable `last_reviewed_boundary`, and outstanding prerequisite checks each have deterministic BLOCKED procedures (`:28`). Detached HEAD, a different branch, unborn branch, worktree HEAD under `.git/worktrees/`, rebase/merge in progress, and unavailable read return BLOCKED; absence of a read surface is itself blocking. `odd/advice/q32-verifier-v4.md:26` was updated to CLOSED in the same commit. This verifies that the contract text landed, not that a PM has executed it: live `pm-odd` pilot evidence remains open; falsifier for execution is a live dispatch envelope recording the branch check and observed result.
- 2026-10-14: Read-only map reconciled the Q56 prerequisites against the code. The PM own-route-key-before-`host_review_start` requirement is IMPLEMENTED, not open (`systematic-routing-guard.ts:877-895`). The `asi-review-*` relay lanes are absent from both PM task allows while the orchestrator's block lists all six (a positive control on the same audit). Q58's behaviours are present: the orchestrator direct-writer-dispatch warning (`:968-980`), the advice-before-writer stage (`:982-994`), and the PM own-route-key gate (`:877-895`). The three-way writer-policy drift remains OPEN. Separately, `rate-limit-fallback.json:829-853` `excludeAgents` now lists all `review-*`/`asi-review-*`/advisor agents, which the tracker's DeepSeek fallback-chain concern never mentions.

## Next step
Q55's contract-completeness and unit-start branch-verification text is complete in `docs/specs/pm-handoff.md` (commit `551b7d3`; see the T1 entry above). Q55/T3 remains open for the pilot's later steps: execute Q58 through `pm-odd` as the bootstrap unit, independently verify genuine relay-context delivery, complete the remaining Q56 smoke/deployment prerequisites, then begin and complete the ten-unit no-route-escape pilot. The bootstrap run and relay-delivery proof are not evidenced as completed here. Delivery strategy for this branch: `stacked-to-main` (owner decision 2026-10-14).

## Post-code advisory review — findings and open decisions

- **Q55 post-code advisory review (completed; advisory evidence, not approval):** `advisor-integration-post`, Task `ses_ee7ce6bb0ffe1l2JkLinwru2FK`.
  - **Contract completeness gap:** `docs/specs/pm-handoff.md` specifies `ROUTE_DISPUTED` (line 15) and `BLOCKED` (lines 108–110) at a high level, but gives no deterministic procedure for an absent or unrecoverable tracker mirror, an unverifiable `last_reviewed_boundary`, or outstanding prerequisite checks. The live `pm-odd` run applied the general `BLOCKED` rule correctly; the contract remains silent on those states.
  - **`odd-apply` contradiction found and fixed:** its prompt instructed the worker to include the work-unit commit, tracker update, and `ROUTER-LOG` entry in one worker lifecycle, contrary to `docs/specs/pm-handoff.md` lines 27 and 108. The prompt now assigns implementation, checks, and the staged reviewability receipt to the worker; commit ownership stays with the PM, and tracker/`ROUTER-LOG` updates belong to the separate metadata work unit.
  - **`pm-sdd` latent hazard — MOOT / resolved by removal (`pm-sdd` retired by Q65, commit `5aadb9f`; no agent block, no orchestrator allow, no adapter-map row):** it has `host_review_start`, `host_review_capture_*`, and `host_review_acknowledge_approved` at `ask`, although the SDD contract forbids starting native review and `pm-sdd` has no `asi-review-*` relay lanes. These tools are unreachable in practice because the loop fails at lens dispatch, but the grants contradict the contract's intent. No permission change is made here.
  - **Three-way drift:** see the existing **Open (deferred)** note below; the guard, ODD route skill, and `pm-odd` task allowlist remain inconsistent. The narrower config does not create a security hole, but the discrepancy remains tracked rather than duplicated here.
  - **Owner decision — enforced independence (resolved):** remove the `asi-review-*` relay lanes
    from `pm-odd` and `pm-systematic`, leaving review dispatch outside the coordinating PM session.
    Q58's route-key rule is necessary but not sufficient: it verifies that the PM loaded its route
    skill, not that reviewer and author differ. The config change is recorded in this unit.
- **Open (owner decision):** Review fallback chains carry DeepSeek targets. A fallback hit on any 4R lens can put a reviewer on the author's model family, contradicting the recorded constraint that a reviewer never shares a model family with the author. This is a constraint-versus-reality conflict; it is recorded for owner resolution, not fixed here.
- **Open (deferred):** Three-way policy drift remains: `ODD_SPECIALIST_WRITERS` in the guard helpers authorises writers that the ODD route skill and `pm-odd` task permissions do not use, so those three surfaces are not equivalent. `ROUTE_STAGES` also has no `workflow-sdd-secure` entry although `pm-sdd` loads it. Not fixed in this change.

## Native review and advisory follow-ups — 2026-10-07

- **Observed — native review `review-eafee5bf38502dad`: APPROVED, acknowledged, authority burned.** Candidate base tree `0d7c77c405ad8d3304869f18ecf697cb69036c89` (last reviewed boundary, commit `2a72ba2`); candidate HEAD tree `b1f3c8c46b1c0fe60d678be7763ab729668922b8`; 10 paths / 716 changed lines; tier high. Correction budget 200, unused; no finding opened a correction. `review-risk`, `review-resilience`, `review-readability`, and `review-reliability` all completed (4/4); readability returned zero findings. Reliability failed twice before completion: one attempt was refused by the relay concurrency cap of 4, and a later attempt was cancelled; it completed on retry after the provider re-offered the same task. These were transport/provider refusals, not findings. At the time, the reviewed boundary advanced to candidate HEAD tree `b1f3c8c46b1c0fe60d678be7763ab729668922b8`.
- **Observed — earlier native review `review-87d0cd86677f9627`: APPROVED.** The review store no longer has a retrievable record: `host_review_status` returned `applicability: "unrelated"` and zero lineages (status readback supplied for this task). Its reviewed boundary is confirmed as commit `2a72ba2` by equality between that commit's tree and the review's recorded `initial_review_tree`.
- **Advisory findings — all non-blocking and informational; none reopens either review or warrants rerunning it.**
  - **R1-001 (risk, WARNING):** `global-config/opencode.json` newly registers `host_git_push` and `host_sandbox_result_install` for `pm-odd`, `pm-systematic`, and `pm-sdd` at `ask`. Push extends a PM session's blast radius to remote push, gated only by `ask`, which is susceptible to approval fatigue.
  - **R1-002 (risk, SUGGESTION) — MOOT / resolved by removal (`pm-sdd` retired by Q65 `5aadb9f`; the cited block is deleted, `opencode.json` is now 2406 lines, so this `:2595-2603` ref is stale):** `global-config/opencode.json:2595-2603` grants `pm-sdd` the full `host_review_*` lifecycle although the SDD contract forbids starting native review and `pm-sdd` has no `asi-review-*` relay lanes. The grants contradict contract intent and weaken defense-in-depth.
  - **R3-PM-SDD-REVIEW-HAZARD (reliability, WARNING) — MOOT / resolved by removal (`pm-sdd` retired by Q65 `5aadb9f`; this `:2592-2603` ref is stale, the cited block was deleted):** the same `global-config/opencode.json:2592-2603` grants create a latent stuck-lineage hazard if `pm-sdd` starts review without relay lanes.
  - **R4-001 (resilience, WARNING):** `verify-workflow.sh:2702-2716` had a vacuous-pass path: the `Object.keys` walk over `agent.tools` and `Object.entries` walk over `agent.permission` iterated only present keys, using empty-object fallbacks. A deployed review relay with either object omitted therefore produced no lockdown failures while OpenCode defaults applied unaudited. The existing synthetic positive control proved only that explicit enabled tool/allowed permission values were flagged; it did not exercise omitted objects. **Fixed in this unit:** missing or non-object `tools` and `permission` are failures, and the positive control includes an agent object with both omitted.
  - **R4-002 (resilience, WARNING) — MOOT / resolved by removal (`pm-sdd` retired by Q65 `5aadb9f`; this `:2670-2681` ref is stale, the cited block was deleted):** at `global-config/opencode.json:2670-2681`, a `pm-sdd` session with approved ask prompts can start a review it cannot drive; lens dispatch fails without relay permissions, leaving a stuck lineage recoverable only through manual abandon, after automated repair reported unsupported.
  - **R4-003 (resilience, SUGGESTION):** `verify-workflow.sh:2747` removes `pm-probe` from the PM non-execution audit list and ordinary memory-agent set without asserting its absence from deployed config. A future reintroduction would escape this audit; add an explicit absence assertion.
- **Positive security observations (risk lens):** the `asi-review-*` relay lanes were removed from `pm-odd` and `pm-systematic`; the task wildcard was removed from `advisor-testing-pre`, `advisor-maintainability`, and `advisor-testing-post`; the new 12-agent review lockdown audit was added; `pm-probe` was fully removed; and `odd-apply` commit ownership was separated.
- **Open follow-ups (owner decision / separate units; no changes made here):** R1-001 asks the owner to resolve whether PM ask-gated remote push is acceptable; R1-002 / R3-PM-SDD-REVIEW-HAZARD / R4-002 require an owner decision on `pm-sdd` review lifecycle grants and the stuck-lineage/manual-abandon risk; R4-003 needs a separate explicit-absence assertion. R4-001 is addressed by this unit's fail-closed check. These remain advisory evidence, not approval conditions.

## Q58 bootstrap prerequisites — observed evidence (2026-10-08)

- **Observed — reviewed boundary:** Git tree for commit `6ac15ea0a8206cda8e915c3e33ea5e76dd043a24` is `b1f3c8c46b1c0fe60d678be7763ab729668922b8`, equal to the approved candidate tree recorded for `review-eafee5bf38502dad`. This confirms `6ac15ea0a8206cda8e915c3e33ea5e76dd043a24` as the last reviewed boundary. Descendant commits seen in the inspected history are `a926f9e8f1e2eb7df33d8474d5966f6be786510c`, `dbdcfe109bc8453ad704dbbcce711e5d8296b36f`, `1b6ba2ba7259b1baa023ae94644b8c68e369f918`, and `c76f9e630234b09295de5cc8129e74653353f615`; no later reviewed candidate is recorded in this tracker or the located `ROUTER-LOG.md` entry. Boundary remains commit `6ac15ea0a8206cda8e915c3e33ea5e76dd043a24`.
- **Observed — `pm-probe` removal check (c), PASSED:** a Task dispatch returned `Unknown agent type: pm-probe is not a valid agent type`.
- **Observed — removal check (b), PARTIALLY PASSED:** the installed sandbox-refusal list in `/home/james/.config/opencode/plugins/sandbox-tools.ts`, `READ_ONLY_AGENTS` lines 64–69, contains `gentle-orchestrator`, `pm-odd`, `pm-systematic`, and `pm-sdd`, and contains no `pm-probe`. The broker's separate identity list is in the `agent-sandbox-integration` project and is not reachable from this workspace; the `~/ai-workspace` directory listing was permission-denied. That half remains unverifiable here and is not treated as passed.
- **Observed — removal check (a), PARTIALLY PASSED:** live `pm-odd` calls returned `host_git_commit`: `cannot commit: no applied B→C result for this session`; and `host_review_start`: `the candidate has no pending changes…`. These business errors are reachable only after authorization passed; no `HOST_MUTATION_*` token appeared. The deny path is unobservable: `host_register_project` is absent from `pm-odd`'s registered tool set, so the call cannot reach the broker. This is a tool-registration-layer control, not an observed broker refusal. Do not characterize all of (a) as passed.
- **Owner decision (2026-10-07) — session writing-model decision: decided: cloud.** This project uses `gentle-ai-worker` (`deepseek-v4.1-flash`); a PM unit may rely on this explicit decision without inferring it. The local option, `gentle-ai-worker-local` (`kinver/professional`), exists but was not selected.
- **Advisory evidence — Q58 pre-code advice (`advisor-integration-pre`):** consequential open question: recording PM identity only when the parent receives a completed Task result cannot establish identity during that child’s initial execution. Cross-reference `odd/tasks/guard-q03.md`, “Confirmed loader defect closure” / runtime investigation note: child/parent state is only observed when the Task returns, not at dispatch. This tracker records the implication without duplicating the Q03 timing analysis.

### Removal-check status summary

- (a) Effective broker policy: **PARTIALLY PASSED (observed)** for permitted calls; broker refusal/deny path unobservable because `host_register_project` is not registered in the live PM tool set.
- (b) Installed plugin bytes: **PARTIALLY PASSED (observed)** for `READ_ONLY_AGENTS`; separate broker identity list **UNVERIFIABLE** from this workspace.
- (c) Previously bound probe-session refusal: **PASSED (observed)** by failed `pm-probe` Task dispatch.

## T6 (Q58) slice readiness — 2026-10-09

- **Unit:** `Q58-bootstrap-slice1` (T6), workspace `workflow_optimisation`, tracker `odd/tasks/pm-layer.md`.
- **Route: delegated.** Specialist: `odd-apply` sandbox writer; the orchestrator stays read-only. Trigger evidence: the writer trigger (two or more non-trivial files) plus the secure delegation/preparation policy — every project mutation and execution is delegated. Recorded before the first implementation source edit per `WORKFLOW.md` lines 58 and 64.
- **Authorized scope (forecast):** `global-config/plugins/systematic-routing-guard.ts`, `global-config/plugins/lib/routing-guard-helpers.ts`, and `tests/routing-guard/` regression tests. No verifier, config, or permission edits; `docs/specs` stays untouched (advisor suggestion out of scope).
- **Model:** cloud owner decision (2026-10-07): `opencode-go/deepseek-v4.1-flash`, observed in the canonical config; models are not changed.
- **TDD:** on (owner strategy); TDD source is this tracker and the Task brief; runner `HOME="$(mktemp -d)" bun test tests/routing-guard`, executed only in the isolated sandbox. RED first, then GREEN, then REFACTOR.
- **Bootstrap/review exception:** Q58 runs as Q56's bootstrap unit, unguarded by design, and does not count toward the ten-unit pilot. Its review must not be self-driven: the orchestrator independently drives review, metadata closure, and deployment after handoff; no post-code advice or native review runs in this unit, which stops at sandbox handoff.
- **Forecast:** below 400 authored changed lines and 100 KiB of authored textual patch for this slice (revise here if implementation evidence says otherwise).
- **Pre-code advice (advisory evidence only, not approval):** `advisor-integration-pre`, Task `ses_ee2053b3fffe6TKHQSp3cZZXSC`, configured `opencode-go/kimi-k2.7-code`. Required shape: PM key validation only from the PM's own route-directory key (no inherited key, no wrong-route acceptance); identity from the persisted recent message agent via `chat.message`; an exact declarative map in the helpers (`pm-odd`→`workflow-odd-secure`, `pm-systematic`→`workflow-systematic`); keep the broad `isCoordinator` admission and the generic/non-PM stage semantics; every gated host mutation and review-lifecycle warning names the PM and the missing key.
- **Latest-message-agent limitation:** PM identity is not observable while the child first executes — parent/child state is written only when the Task returns; helpers must rely on the persisted latest-message agent through `chat.message`. See the Q58 prerequisites note above; the Q03 timing analysis is not duplicated here.
- **Inputs:** reviewed boundary `6ac15ea0a8206cda8e915c3e33ea5e76dd043a24`; RDD enabled (global). Readback of this body and its Magic Context mirror is the readiness gate before the first source edit.

## Workflow optimisations (owner, 2026-10-09)

1. **Feature branch before work.** Problem observed: Q58 reached the commit step while the host was on `main`; `WORKFLOW.md:76` required a feature branch but did not check it before work started. Binding rule: confirm the appropriate feature branch at unit start, before any work; do not discover its absence at commit time.
2. **Refinement loop — DECIDED: install-then-refine (option a).** Problem observed: the PM let a writer run `sandbox_finish`, did not install that result, then dispatched a new writer to rebuild the change on the original base for refinements. Binding rule: install the result, then dispatch a fresh writer to make further changes on the installed base; never rebuild from the original base. Repeat as needed. Only the reviewed result is committed; intermediate installed states are not committed. Rationale: a sandbox worker is single-lifecycle and terminal after apply, so refinement always uses a fresh worker regardless; installing each iteration makes the work durable immediately, which matters because worker sessions stall and are cancelled routinely. Cost: the host tree carries uncommitted intermediate states, so tree hygiene and deliberate branch reconciliation are required. This selects (a), not the prior review-diff-then-refine alternative.
3. **Post-code advisory review runs pre-commit.** Problem observed: the post-code advice ran after the commit, followed by native review, so its findings were absent from the committed candidate. Binding rule: the PM runs the independent post-code advisory review before the work-unit commit so the committed version is already advisor-reviewed; native review remains separately driven and is not run by the PM. This deliberately reverses the earlier `docs/specs/pm-handoff.md` instruction to stop after the work-unit commit and not run post-code advice. That earlier ordering preserved review independence by having the orchestrator drive the advice; the owner now requires the PM to arrange the independent advisory review before commit, preserving reviewer/author independence while ensuring its findings are present in the committed candidate.
4. **PMs delegate bounded read-only investigation to explore agents.** Problem observed: the PM did investigation reading itself instead of delegating bounded read-only investigation. Binding rule: the PM uses `explore` agents for such investigation to reduce its own work.

## Q58 slice 1 — COMPLETE (2026-10-09)

- The warning-only control requires a `pm-odd` or `pm-systematic` coordinator to hold its **own route's** adapter key before gated host mutations and any `host_review_*` call. Validation checks only the PM's own key directory; inherited or wrong-route keys do not satisfy the check.
- Commit `7a427d7` (`feat(routing-guard): require a PM's own route key before gated mutations and review start`) on `feat/q58-pm-route-key`; 3 files, 362 insertions. TDD: 80 passed / 0 failed.
- Native review `review-31cac7f1ea8f5a23`: **approved**, acknowledged, authority burned. Risk and readability found nothing; resilience returned 3 advisories; reliability returned 2 advisories and 1 warning. Correction budget 200, unused.
- **Identity premise verified live:** a temporary `chat.message` probe logged `keys: ["sessionID","agent","model","messageID","variant"]` with `agent` a populated string (`"gentle-orchestrator"`). The runtime therefore delivers `input.agent` on `chat.message`; the binding is not inert. The probe has since been removed.
- **Known limitation:** the binding is the latest observed message agent, not authenticated identity, and a task-dispatched child PM may never receive `chat.message`; the gate can therefore silently not apply to that child. This was independently identified by the security advisor and review finding `R3-PM-IDENTITY-CHAT-MESSAGE-BLIND-SPOT`.
- **Open, non-blocking advisory follow-ups:**
  - `R4-001`: `.agent` persistence swallows write errors without a breadcrumb, making an unwritable binding store indistinguishable from an unbound session; this has the same silent-failure shape as the earlier plugin-loader defect.
  - `R3-PM-HOST-MUTATION-DUPLICATE-SET`: `HOST_MUTATION_GATE_TOOLS` duplicates the host-mutation subset of `ROUTING_GATE_TOOLS`, so the sets can drift.
  - `R3-FALLBACK-SUPPORTED-FIELDS-REGEX`: the verifier derives the fallback supported-field set by regex; `peakPolicy` is force-added, demonstrating that the parse is not authoritative.
  - Integration advice, P2: `host_sandbox_result_install` and `host_sdd_archive_compose` are held by PMs but not covered by the PM own-key gate. Correction (2026-10-14, verified against the guard code): `host_sandbox_result_install` IS in `ROUTING_GATE_TOOLS` (`global-config/plugins/systematic-routing-guard.ts:223`), so it is in `HOST_MUTATION_GATE_TOOLS` and is covered by the PM own-key gate; the earlier statement that it is outside `ROUTING_GATE_TOOLS` is stale. `host_sdd_archive_compose` was removed from the set when `pm-sdd` was retired (Q65 `5aadb9f`). The recorded `verify-workflow.sh` `gatedHostMutations` disagreement is superseded for these two names.
  - **Open external/upstream item — review relay deadline:** two review lenses expired with `reviewer_relay_deadline_expired: review relay deadline of 600000 ms expired` although the lenses took 16–19 minutes. The deadline is `RELAY_DEADLINE_MS = 600_000` in `~/.config/opencode/plugins/lib/reviewer-relay-core.ts:112`, overridable through `config.deadlineMs` at `:778` and `:1294`. That plugin file is not tracked in this repository; this repository tracks only `global-config/plugins/lib/routing-guard-helpers.ts`, and nothing here sets the deadline. The fix belongs to the external plugin owner, not this repository's local work.
- **Q58 remaining slices — COMPLETE:** the orchestrator direct-writer-dispatch warning and the advice-before-writer stage were delivered in commits `d25228b` and `4b63481`, respectively. The final shipped routing-guard changes are recorded below. The commit-before-review half is superseded by the pre-commit advisory rule recorded in the workflow formalisation.

### Q58 shipped follow-up — 2026-10-09

- Commits `9c215b1`, `d25228b`, and `4b63481` shipped the follow-up guard behavior. `9c215b1` derives `HOST_MUTATION_GATE_TOOLS` by filtering `ROUTING_GATE_TOOLS` for `host_` names, adds routing/PM gating for `host_sandbox_result_install` and `host_sdd_archive_compose`, emits one deduplicated console breadcrumb when the message-agent binding write fails (`R4-001`), and adds the every-turn user-facing-message rule to the recovered AGENTS block. `d25228b` warns when `gentle-orchestrator` dispatches a writing specialist directly instead of through the route coordinator. `4b63481` adds an advice stage before writer dispatch for `workflow-odd-secure` and `workflow-systematic`; dispatching a writer before the advice record exists warns.
- **Observed test result:** routing-guard tests: 94 passed / 0 failed (previously 80 passed).
- **Status boundary:** these slices are complete and shipped; the `pm-odd` bootstrap run has NOT been executed, and independent relay-delivery proof remains UNVERIFIED. T6 stays unchecked until those runtime acceptance steps have evidence.
- **Advice-record convention:** substantial routes owe pre-code advisory review before the first writer dispatch, evidenced by `odd/advice/<change>.md`. A delegated sandbox worker writes the file because the orchestrator and PM agents are read-only and cannot write project files. The guard detects its written path, as it detects tracker and plan writes; the path satisfies the advice stage, while an early writer dispatch warns only and is not blocked. The artifact is advisor-agnostic and remains visible/reviewable when advice comes from a CLI, another runtime, or a human, unlike a `task` dispatch event that proves only that a task call occurred and ceases to be observable for external advisors. The gate proves advice was recorded, not that it was acted on.

### Q56 pilot — first completed pm-odd unit (2026-10-19)

- Observed: `pm-odd` completed one standalone tiny-fix unit end to end and returned `pm-unit-result/v1` status `DONE`.
- Unit `q78-advice-correction-u1` (task `q78-advice-correction`), standalone tiny fix, branch `chore/q72-t1b-tiny-fix-contract`.
- Implementation commit `47781da` (append-only correction to `odd/advice/q78-host-review-materialize.md`, 7 authored lines); metadata commit `a104abc` (one `ROUTER-LOG.md` row, 1 authored line). Both commits were made by the PM through `host_git_commit`.
- Both committed candidates assessed `passive` (`review_due=false`); no native review lifecycle was required.
- Orchestrator readback matched the envelope: branch HEAD `a104abc`, `ROUTER-LOG.md:258` intact, and both commits confined to the authorized paths.
- A pre-existing uncommitted delta in `tests/test_tiny_fix_route.py` (mtime `2026-10-18 23:03:03 +0100`, +2 lines) predates the unit, was excluded from both commits, and was left untouched; authorship unresolved, timing resolved.
- This smoke test does NOT count toward Q56's ten consecutive units. The count starts only after Q58's enforcement is live (T4).

## Q58 bootstrap — native-review advisory clearance (2026-10-19)

- **Unit:** `q58-bootstrap-advisory-clearance-u1` (task `q58-bootstrap`). Route: delegated. Writer trigger: the change touches two or more non-trivial files (tests plus the normative spec), and the secure mutation policy delegates every project mutation/execution to one bounded sandbox writer; recorded before the first source/test edit.
- **Scope (authorized paths only):** `odd/tasks/pm-layer.md`, `docs/TODO.md`, `docs/specs/pm-handoff.md`, `ROUTER-LOG.md`, `tests/test_tiny_fix_route.py`, `tests/test_pm_handoff_spec.py`. No `global-config` edits, verifier edits, prompt/permission edits, push/PR/deploy, writer commits, or native-review operations. The "no commits" scope applies to this writer only: the PM owns and authorizes the unit commit after the result is installed and independently reviewed.
- **PM-observed start checks (not rerun here):** `.git/HEAD` contained `ref: refs/heads/chore/q72-t1b-tiny-fix-contract`; the tracker was 398 lines with last line `- This smoke test does NOT count toward Q56's ten consecutive units. The count starts only after Q58's enforcement is live (T4).`; branch SHA `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422` matched the input boundary; RDD effective mode was `enabled` with source `global` via `host_review_mode_status`. The tracker read is a working-tree observation, NOT proof that the tracker equals the committed blob.
- **Mirror:** the deterministic Magic Context tool is unimplemented; no mirror was read or written.
- **Review ordering:** the historical Q58 note that this unit owes no post-code advice and no native review is SUPERSEDED by the current `WORKFLOW.md`: independent post-code advice before the commit, committed-candidate assessment after the commit, and external orchestrator-driven native review. This writer produces no review evidence.
- **Pre-code advice (completed, advisory only):** `advisor-testing-pre` Task `ses_eaa552d98ffedYn7FuReRE4vSH`, model `opencode-go/minimax-m3` (advisor reported identity/config aligned), pre-code for `q58-bootstrap`. Summary: iterate the mutation control over all five sources; align the spec and the deep phrase assertion; preserve headings and existing assertions; replace ALL occurrences only in the in-memory mutated text. The advisor recommended no ROUTER-LOG repair despite observing blank L38 before the Q72 row at L39; that recommendation is rejected because it conflicts with the advisor's own evidence and the acceptance requirement.
- **Five native advisory findings (explicit mapping; all resolved in this unit):**
  1. `R3-001` per-source controls/adopted+2 — RESOLVED in `tests/test_tiny_fix_route.py`. Per-source in-memory replacement of `absence MUST NOT block a unit` with `removed diagnostic wording` now asserts `AssertionError` containing `PM trace contract` for all five sources via `subTest`; the existing `sources[0]` assertion and the two adopted tuple lines are preserved.
  2. `R3-002` deep positive control — RESOLVED in `tests/test_pm_handoff_spec.py`. The deep non-planning branch-SHA phrase control was added and the helper aligned to the corrected spec; explicit planning all-`none`/skip and non-planning block assertions were added. The independent post-code advisor later found the marker-collision blocker recorded below; this refinement resolves it. RED before the original spec fix: 25 tests run, 2 failures, 23 passed; GREEN after: 25 tests, OK.
  3. `R3-003` planning-vs-execution SHA wording — RESOLVED in `docs/specs/pm-handoff.md`. Removed `remains required in every case` and `In both shapes`; planning anchors now include the branch SHA in the all-`none`/skipped clause, and every non-planning unit including a standalone tiny fix requires and compares the branch `HEAD` commit SHA and blocks on mismatch.
  4. `R4-1` row adjacency — RESOLVED in `ROUTER-LOG.md`. Removed the blank between the Q86 reviewer-delivery row and the Q72 dual-shape row; exactly one blank remains before `## Usage Notes`. Scoped programmatic check: `36 37 True` (zero-based Q86 row index 36, Q72 row index 37, adjacent True) and `True False` (the line before the heading is empty; the line before that is not). The earlier whole-region observation was `region_rows=29`, `blank_positions=[15,16,28]`, `non_table_rows=[]`, `trailing_blank_lines_before_usage=1`; positions 15–16 are pre-existing blanks before the earlier Q79 corrections row and are outside this repair.
  5. `R4-2` accurate control naming — RESOLVED in `tests/test_pm_handoff_spec.py`. Renamed the inaccurate `test_standalone_tiny_fix_positive_control_rejects_removed_none_authorization` to `test_standalone_tiny_fix_positive_control_rejects_removed_standalone_authorization`, preserving its existing `standalone tiny fix` control. The new deep control keeps its accurate name `test_positive_control_detects_removed_nonplanning_branch_sha_authorization`.
- **PM-found, not one of the five native advisory IDs:** stale `docs/TODO.md` Q58 **Status** still said the bootstrap had NOT executed. Corrected to the historical shipped-slices plus the executed 2026-10-19 bootstrap, five advisories addressed, any native review external, relay proof UNVERIFIED, and no ten-unit or approval claim; the post-commit assessment later recorded no native review due (`under_budget`).
- **Post-code advice (independent; completed, advisory only; not approval):** `advisor-testing-post`, Task `ses_eaa48d2e6ffeXfsGxfQXo4HFLk`, model `opencode-go/kimi-k2.7-code` (observed at `global-config/opencode.json:1801`). It found one blocker: at `tests/test_pm_handoff_spec.py:155` the deep positive-control marker ``branch `HEAD` commit SHA is required for every non-planning unit`` also occurred in the brief, so the mutation failed the earlier brief assertion instead of the intended deep comparison.
- **Refinement — blocker resolved (writer-observed):** the deep control now uses the unique full marker ``branch `HEAD` commit SHA is required for every non-planning unit and its comparison still runs``. The test asserts `spec.count(marker) == 1`, asserts the full marker is absent from the brief while the short brief clause is preserved, then replaces only that full marker with ``branch `HEAD` commit SHA is optional for non-planning units and its comparison is skipped`` and asserts the failure message matches the full marker via `assertRaisesRegex(re.escape(marker))`. Because the brief is unchanged and the full marker is unique to the deep comparison, the observed failure is the intended deep comparison, not the earlier brief assertion. **Independent confirmation (PM-observed, before the implementation commit):** the resumed `advisor-testing-post` Task `ses_eaa48d2e6ffeXfsGxfQXo4HFLk`, model `opencode-go/kimi-k2.7-code` and independent of the DeepSeek authors, inspected the installed unique full-marker/count-1/unchanged-brief fix, the renamed standalone control, the tracker, and `docs/TODO.md`, and returned: 'No remaining blockers. The current applied candidate is independently post-code advised and has no blockers.' This is a PM-supplied readback; this writer did not execute it.
- **Writer provenance:** first writer Task `ses_eaa5195eeffe7nGCFHsgaUKLn1` and refinement Task `ses_eaa42e0fcffeyg21jSNKlgI07b`; both are observed Task IDs supplied by the PM. The first writer's applied result and the refinement result are installed on the host. Metadata continuation was explicitly authorized by the user for the same under-budget medium boundary and then assessed by the PM against the original boundary.
- **Observed checks (2026-10-19, sandbox, refinement rerun):** focused `python3 -m unittest tests.test_tiny_fix_route tests.test_pm_handoff_spec` → `Ran 25 tests in 0.163s` / `OK`. Single deep control → `test_positive_control_detects_removed_nonplanning_branch_sha_authorization ... ok`; `Ran 1 test in 0.000s` / `OK`. Single renamed standalone control → `test_standalone_tiny_fix_positive_control_rejects_removed_standalone_authorization ... ok`; `Ran 1 test in 0.000s` / `OK`. Full `python3 -m unittest discover -s tests` → `Ran 220 tests in 3.751s` / `FAILED (errors=10, skipped=1)` (209 passed). All 10 errors are `test_gemini_advisor_route` `PermissionError: [Errno 13] Permission denied: 'node'`: `PositiveControl.test_advisor_with_a_read_tool_fails`, `PositiveControl.test_advisor_with_a_wider_task_scope_fails`, `PositiveControl.test_dispatcher_losing_an_advisor_fails`, `PositiveControl.test_evidence_agent_with_a_host_route_fails`, `PositiveControl.test_fallback_allowed_fails`, `PositiveControl.test_missing_agents_are_reported_by_the_verifier_block`, `PositiveControl.test_non_dispatcher_granting_an_advisor_fails`, `PositiveControl.test_non_dispatcher_wildcard_granting_advisors_fails`, `PositiveControl.test_pm_dispatching_the_evidence_agent_fails`, and `RealConfig.test_verifier_block_passes_real_sources`. `git diff --check` → no output (clean). Programmatic ROUTER-LOG check → `36 37 True` and `True False`. AFT scoped inspect was not rerun in this refinement; the earlier observation remains PARTIAL: complexity incomplete, Python dead-code analysis unsupported, and one host-tree pre-existing Pyright error `tests/test_tiny_fix_route.py:184:74 "group" is not a known attribute of "None"`. The host tree does not contain the sandbox edits and the tests execute, so this remains a diagnostic gap, not a blocker.
- **Reviewability receipt (staged candidate relative host feature HEAD `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422`):** aggregate `authored_changed_lines: 0074` (additions + deletions across all six changed files, including the two adopted tuple lines), `authored_patch_bytes: 032288`, `generated_or_binary_paths: []`. Refinement-only (this writer, relative the installed base `a9be128`): `authored_changed_lines: 0048`, `authored_patch_bytes: 19719`, `generated_or_binary_paths: []`. Measurement boundary: measured with these fixed-width slots in place; replacing each slot with an equal-width value does not change the line count or patch byte count, so the numbers describe the final staged candidate including this receipt. Both caps are satisfied. This is the implementation candidate receipt, not the metadata-continuation receipt; the metadata receipt is returned to the PM separately after final content to avoid self-reference.
- **Forecast:** under 400 authored changed lines and 100 KiB authored textual patch for this unit (excluding generated files; none expected).
- **Tests-first runner:** `python3 -m unittest tests.test_tiny_fix_route tests.test_pm_handoff_spec`, then `python3 -m unittest discover -s tests` in the sandbox.
- **Bootstrap/review boundary:** this unit does NOT count toward Q56's ten-consecutive-unit pilot. The implementation was committed by the PM as `b3fba8dd6666af98cf6ba00d61eac425747b9f20` (six allowed paths; 66 insertions / 8 deletions). The PM's host assessment after that commit returned status 0 with empty stderr: `{"schema":"gentle-ai.review-assessment/v1","risk":"medium","reasons":[{"code":"executable_change","path":"tests/test_pm_handoff_spec.py"}],"changed_paths":6,"changed_lines":74,"candidate":{"kind":"base-diff","base_ref":"deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422","consumed":false},"review_due":false,"review_due_reason":"under_budget"}`. No native review is DUE; the reviewed boundary remains `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422`, and the medium slice remains accumulated/pending. It is NOT passive, approved, or consumed. The external orchestrator drives any future native review. Independent relay-delivery proof remains UNVERIFIED and no Q56 ten-unit credit is claimed. The metadata continuation is prepared in this working tree; the PM commit, independent post-code metadata advice, and committed-candidate assessment remain pending. No approval is claimed.
- **Baseline provenance (observed):** the first writer's sandbox baseline commit `1211a8fd2458527fe83d28c91b8fdcfaa22687ce` on branch `work` sat on `deab3b5` and contained exactly 2 insertions in `tests/test_tiny_fix_route.py` (`index 9d4ecb8..82037cf`), adding `global-config/skills/workflow-odd-secure/SKILL.md` and `odd/advice/q72-tiny-fix-route.md` to the five-source tuple. This refinement's sandbox baseline is `a9be128` (observed in `git log`), which contains the already-installed full implementation; the aggregate receipt is measured from `deab3b5` so those installed changes and the two adopted tuple lines are included. The first-writer record matches the user-supplied index and the earlier tracker record at line 397. User-supplied provenance: mtime `2026-10-18 23:03:03 +0100`. The first writer's sandbox checkout mtime was `2026-10-19 19:41:12.914641168 +0000` (checkout time), so the original host mtime was not independently observed here.

### Q58 bootstrap metadata closure — 2026-10-19

- **Metadata continuation (authorized):** user-authorized metadata-only closure of `q58-bootstrap-advisory-clearance-u1`; allowed paths exactly `odd/tasks/pm-layer.md`, `docs/TODO.md`, and `ROUTER-LOG.md`. No tiny-fix route was used and no `general` writer was dispatched.
- **Implementation readback (owner-supplied, not this writer's execution):** commit `b3fba8dd6666af98cf6ba00d61eac425747b9f20` on `chore/q72-t1b-tiny-fix-contract`; 66 insertions / 8 deletions across the six allowed paths. The orchestrator independently inspected the commit sources, controls, table, tracker, and TODO as reported by the owner; this writer did not rerun that inspection.
- **Post-code confirmation (PM-observed, before the implementation commit):** resumed `advisor-testing-post` Task `ses_eaa48d2e6ffeXfsGxfQXo4HFLk`, model `opencode-go/kimi-k2.7-code`, independent of the DeepSeek authors, inspected the installed unique full-marker/count-1/unchanged-brief fix and the renamed standalone control plus the tracker/TODO, and returned: 'No remaining blockers. The current applied candidate is independently post-code advised and has no blockers.'
- **Writer provenance:** first writer Task `ses_eaa5195eeffe7nGCFHsgaUKLn1`; refinement Task `ses_eaa42e0fcffeyg21jSNKlgI07b`. Both are observed Task IDs supplied by the PM.
- **Assessment and review state:** the exact PM assessment after commit is recorded in the preceding boundary bullet. `review_due=false` for `under_budget`; reviewed boundary retained at `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422`; medium slice accumulated/pending, NOT passive/approved/consumed. External orchestrator drives any future native review. Independent relay proof UNVERIFIED; no Q56 ten-unit credit.
- **Metadata scope and pending steps:** this unit changes only the three metadata paths; the implementation texts in `tests/test_tiny_fix_route.py`, `tests/test_pm_handoff_spec.py`, and `docs/specs/pm-handoff.md` are unchanged by it. The prior refinement's ROUTER-LOG `36 37 True` observation predates this metadata unit's formatting-only removal of two internal blank separators. The metadata reviewability receipt is returned to the PM separately after final content to avoid self-reference. PM commit, independent post-code metadata advice, and committed-candidate assessment remain pending. Magic Context mirror is unimplemented and was not read or written.
