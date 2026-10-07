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
- [ ] T3 (Q55) — implementation landed in commit `8980254`: `docs/specs/pm-handoff.md`, four agent registrations, guard coordinator admission, and regression tests. The post-code advisory review remains owed. The earlier claim that `pm-probe` was removed is superseded by Correction C. Route-specific classification is verified, but hard rejection is not (the guard is warning-only).
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
- [ ] T6 (Q58) — Guard ordering rules, tests first; include proof of a real review relay from a PM
  with a genuine provider-issued binding. Q54 reported reachability only; context delivery remains
  unverified. It may run through `pm-odd` as Q56's bootstrap unit only (see T4); its own enforcement
  does not exist during execution, so it runs unguarded by design. Its review must not be self-driven.
  Do not start Q58 until Q56's other gates pass: both service restarts, the live-policy smoke test,
  and all three `pm-probe` removal checks.
  - Requirement (not yet implemented; recorded in commit `e9bffc0`): a PM must hold its own
    route's adapter key before `host_review_start`: `pm-odd` requires `workflow-odd-secure`, and
    `pm-systematic` requires `workflow-systematic`. This matches the existing rule that a PM must
    hold its route key before `host_git_commit` or a writer dispatch. `pm-sdd` does not launch
    native RDD.
  - A relay grant without the matching route key must not admit a review; permission alone is
    not readiness.
  - The relay grants and verifier rule admitting them on `pm-*` are deliberately coupled
    with the future guard rule requiring the PM's own route key before review. The verifier
    admits relays only on `gentle-orchestrator` and `pm-*`; the guard will later require the key.
  - These grants restore the `pm-odd` and `pm-systematic` relay permissions previously removed
    by the `RELAY_TASK_GRANTED_OUTSIDE_ORCHESTRATOR` fix; that verifier rule now admits PMs.
  - Before Q54, the broker bound `host_review_start` to `gentle-orchestrator`; Q54's owner-relayed
    identity table now permits it for the PM identities that owe native review. A genuine,
    provider-bound PM relay still must be exercised under Q58/Q61; SDD does not launch native RDD,
    so `pm-sdd` receives no relay grant.
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
  above; relay grants and verifier admission for PMs remain coupled to the future guard rule.
  Acceptance evidence and the required metadata/mirror close-out remain pending.
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

## Next step
Q54's `pm-probe` removal check (c) now PASSES after verifier mirror → restart; the failed dispatch
is observed and the removal is live. Q55's post-code advisory review is complete; Q55 remains in
progress for its other open acceptance items. Q56 remains gated on Q55 and its other pilot
prerequisites.

## Post-code advisory review — findings and open decisions

- **Q55 post-code advisory review (completed; advisory evidence, not approval):** `advisor-integration-post`, Task `ses_ee7ce6bb0ffe1l2JkLinwru2FK`.
  - **Contract completeness gap:** `docs/specs/pm-handoff.md` specifies `ROUTE_DISPUTED` (line 15) and `BLOCKED` (lines 108–110) at a high level, but gives no deterministic procedure for an absent or unrecoverable tracker mirror, an unverifiable `last_reviewed_boundary`, or outstanding prerequisite checks. The live `pm-odd` run applied the general `BLOCKED` rule correctly; the contract remains silent on those states.
  - **`odd-apply` contradiction found and fixed:** its prompt instructed the worker to include the work-unit commit, tracker update, and `ROUTER-LOG` entry in one worker lifecycle, contrary to `docs/specs/pm-handoff.md` lines 27 and 108. The prompt now assigns implementation, checks, and the staged reviewability receipt to the worker; commit ownership stays with the PM, and tracker/`ROUTER-LOG` updates belong to the separate metadata work unit.
  - **`pm-sdd` latent hazard:** it has `host_review_start`, `host_review_capture_*`, and `host_review_acknowledge_approved` at `ask`, although the SDD contract forbids starting native review and `pm-sdd` has no `asi-review-*` relay lanes. These tools are unreachable in practice because the loop fails at lens dispatch, but the grants contradict the contract's intent. No permission change is made here.
  - **Three-way drift:** see the existing **Open (deferred)** note below; the guard, ODD route skill, and `pm-odd` task allowlist remain inconsistent. The narrower config does not create a security hole, but the discrepancy remains tracked rather than duplicated here.
  - **Open owner decision — PM-owned review versus enforced independence:** the advisor recommends removing the `asi-review-*` relay lanes from `pm-odd` and `pm-systematic`, leaving a coordinating PM able to start native review but unable to conduct it itself. Q58's route-key rule is necessary but not sufficient: it verifies that the PM loaded its route skill, not that reviewer and author differ. No permission is changed in this unit.
- **Open (owner decision):** Review fallback chains carry DeepSeek targets. A fallback hit on any 4R lens can put a reviewer on the author's model family, contradicting the recorded constraint that a reviewer never shares a model family with the author. This is a constraint-versus-reality conflict; it is recorded for owner resolution, not fixed here.
- **Open (deferred):** Three-way policy drift remains: `ODD_SPECIALIST_WRITERS` in the guard helpers authorises writers that the ODD route skill and `pm-odd` task permissions do not use, so those three surfaces are not equivalent. `ROUTE_STAGES` also has no `workflow-sdd-secure` entry although `pm-sdd` loads it. Not fixed in this change.
