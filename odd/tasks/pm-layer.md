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
- [ ] T3 (Q55) — `docs/specs/pm-handoff.md`; PM and `odd-apply` agents; prompts; guard data and
  tests. `pm-probe` removal is deferred until Q54's probe target is changed from `pm-probe` to
  the real PM agents; Q54's existing probe dependency must retain its subject.
- [ ] T4 (Q56) — Pilot `pm-odd` on global-tooling units; ten units without route escape.
- [ ] T5 (Q57) — Slim orchestrator prompt and permissions; `AGENTS.md` split; `WORKFLOW.md` and
  skills.
- [ ] T6 (Q58) — Guard ordering rules, tests first.
  - Requirement: a PM must hold its own route's key before it may dispatch a relay or call
    `host_review_start`: `pm-odd` requires `workflow-odd-secure`, `pm-systematic` requires
    `workflow-systematic`, and `pm-sdd` requires `workflow-sdd-secure`.
  - A relay grant without the matching route key must not admit a review; permission alone is
    not readiness.
  - The verifier rule admitting PMs to relay grants and the guard rule requiring the route key
    must move together, or the verifier will reject what the design needs (or admit what it should
    not).
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
- 2026-10-05: Q55 implementation evidence: `docs/specs/pm-handoff.md`, four agent registrations,
  route-specific guard admission, and five regression cases are present. T3 remains pending: the
  staged reviewability receipt is above the 400-line per-commit limit; no commit or native review
  was started. Required pre-code advisor
  dispatch was unavailable in this bounded worker, so no advice result is claimed. The route is
  delegated global-tooling work; the named sandbox writer ran the ordered implementation and test
  stages in this session. Final tracker/mirror metadata and review must be completed in a separate
  metadata work unit before T3 can be marked done.
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

## Next step
T1 (Q53) is complete; Q55 is the next actionable item, and item 4 remains deferred to its PM agents. T2 (Q54) still waits on the owner passing Handover A across to agent-sandbox-integration.
