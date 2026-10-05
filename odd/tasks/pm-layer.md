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
- [ ] T2 (Q54) — Wait for the owner to pass Handover A to agent-sandbox-integration; then install the sandbox allowlist and probe host mutations from a subagent.
- [ ] T3 (Q55) — implementation landed in commit `8980254`: `docs/specs/pm-handoff.md`, four agent registrations, guard coordinator admission, and regression tests. `pm-probe` is deliberately retained pending Q54's probe-target change from `pm-probe` to the real PM agents; Q54's existing probe dependency must retain its subject. The post-code advisory review is complete; acceptance remains open for enforcement and pilot evidence. Route-specific classification is verified, but hard rejection is not (the guard is warning-only).
- [ ] T4 (Q56) — Pilot `pm-odd` on global-tooling units; ten units without route escape.
- [ ] T5 (Q57) — Slim orchestrator prompt and permissions; `AGENTS.md` split; `WORKFLOW.md` and
  skills.
- [ ] T6 (Q58) — Guard ordering rules, tests first.
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
  - The broker currently binds `host_review_start` to `gentle-orchestrator`, so PMs cannot start
    a review until Q54 lands; the grant is deliberately in place ahead of Q54 for `pm-odd` and
    `pm-systematic`, because those routes owe native review. SDD does not launch native RDD, so
    `pm-sdd` receives no relay grant.
- [ ] T7 (Q59) — Verifier coordinator-set checks, prompt budgets, behavioural probes, digest pin.
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

## Progress
- 2026-10-05: Q55 (T3) implementation landed in commit `8980254`. Files: `docs/specs/pm-handoff.md`,
  `global-config/opencode.json`, `global-config/plugins/lib/routing-guard-helpers.ts`,
  `global-config/plugins/systematic-routing-guard.ts`,
  `global-config/skills/workflow-odd-secure/SKILL.md`, `odd/tasks/pm-layer.md`,
  `tests/routing-guard/routing-guard.test.ts`, and `verify-workflow.sh`. The test run finished
  with 53 passed / 0 failed; the red-first run had 4 failures. The implementation delivers the
  handoff contract, PM agents, ODD writer, coordinator guard admission and five regression cases.
  `pm-probe` is deliberately retained until Q54 changes its probe target to the real PM agents.
  T3 is IN PROGRESS, not complete: post-code advisory review has now run, but acceptance remains
  unmet because the guard is warning-only and the PM behavioral probe/pilot evidence is deferred.
  The Q58 requirement that PMs hold their own route key before `host_review_start` is recorded
  above; relay grants and verifier admission for PMs remain coupled to the future guard rule.
  Acceptance evidence and the required metadata/mirror close-out remain pending.
- 2026-10-05: Q55 post-code advisory review ran in design scope (seven findings) and integration
  scope. Testing scope was not run because the guard tests were empirically verified with a
  red-first run. The contract folds in commit ownership, review assessment as a `DONE` conjunct,
  the reviewability receipt, brief schema identity, route-specific post-code advice, RDD mode/source
  brief inputs, log-backed routing-gate observations, and explicit metadata worker/commit/failure
  handling. The verifier now asserts PM non-execution permissions, the `odd-apply` writer shape,
  and its PM-only task allowlist. Deferred: `COORDINATOR_PATTERNS` still treats any `pm-*` name
  as a coordinator without registry cross-check; `workflow-sdd-secure` has no `ROUTE_STAGES`
  entry; the warning-only guard leaves the three-way invariants unenforced; and the behavioral
  probe does not exercise PM agents (Q59/T7 territory). T3 remains open because acceptance criteria
  remain unmet.
- 2026-10-04: T0 done. Facts verified against `global-config/opencode.json`, the guard helpers,
  `verify-workflow.sh`, the OpenCode 1.18.34 binary (Task `task_id`, depth check, child
  permission derivation) and agent-sandbox-integration (`sandbox-tools.ts:64`,
  `broker/src/config.ts:243`, `broker/src/service.ts`). Branch `docs/pm-layer-handovers`.
- 2026-10-04: T0 committed as `bd7835c`. Assessment from `main`: medium, `slice_budget_reached`.
  Native review `review-314b7602882be12e` (one lens, reliability): approved and acknowledged;
  authority burned. One advisory suggestion (Q54 and Q55 can run in parallel) applied to the
  Phases line in `docs/TODO.md`. Reviewed boundary: `bd7835c`.

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

### Additional probe findings — 2026-10-05

- **Observed — host binding/resume:** The probe could not observe host binding or resume because `pm-probe` lacked the required host tools. This unit corrects the probe tool surface; the finding records the probe limitation, not proof that those behaviors have since been exercised.
- **Observed — relay dispatch:** The depth-1 review relay dispatch was blocked by `pm-probe`'s task allowlist.
- **Observed — PM sandbox reads:** Sandbox read calls from a PM returned `unknown session`, rather than a refusal. The owner decision is that PMs must not use the sandbox; the sandbox read tools are removed from their surfaces.
- **Observed — review integration depth:** The review integration showed no depth or parent sensitivity in the probe. `trustedParent` exists in the interface but `decide()` does not read it; the only `parentID` read is the relay's. This records the observed code shape without claiming a mechanism or causal effect.

## Next step
T1 (Q53) is complete; Q55 is the next actionable item, and item 4 remains deferred to its PM agents. T2 (Q54) still waits on the owner passing Handover A across to agent-sandbox-integration.

## Post-code advisory review — open, deferred findings

- **Open (owner decision):** Review fallback chains carry DeepSeek targets. A fallback hit on any 4R lens can put a reviewer on the author's model family, contradicting the recorded constraint that a reviewer never shares a model family with the author. This is a constraint-versus-reality conflict; it is recorded for owner resolution, not fixed here.
- **Open (deferred):** Three-way policy drift remains: `ODD_SPECIALIST_WRITERS` in the guard helpers authorises writers that the ODD route skill and `pm-odd` task permissions do not use, so those three surfaces are not equivalent. `ROUTE_STAGES` also has no `workflow-sdd-secure` entry although `pm-sdd` loads it. Not fixed in this change.
