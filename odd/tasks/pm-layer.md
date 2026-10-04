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
- [ ] T1 (Q53) — Probe with `pm-probe` and depth 4; record the eight observations.
- [ ] T2 (Q54) — Sandbox allowlist installed (Handover A); probe host mutations from a subagent.
- [ ] T3 (Q55) — `docs/specs/pm-handoff.md`; PM and `odd-apply` agents; prompts; guard data and
  tests.
- [ ] T4 (Q56) — Pilot `pm-odd` on global-tooling units; ten units without route escape.
- [ ] T5 (Q57) — Slim orchestrator prompt and permissions; `AGENTS.md` split; `WORKFLOW.md` and
  skills.
- [ ] T6 (Q58) — Guard ordering rules, tests first.
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
- 2026-10-04: T0 done. Facts verified against `global-config/opencode.json`, the guard helpers,
  `verify-workflow.sh`, the OpenCode 1.18.34 binary (Task `task_id`, depth check, child
  permission derivation) and agent-sandbox-integration (`sandbox-tools.ts:64`,
  `broker/src/config.ts:243`, `broker/src/service.ts`). Branch `docs/pm-layer-handovers`.

## Next step
T1 (Q53). T2 waits on the owner passing Handover A across.
