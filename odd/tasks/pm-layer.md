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
- [ ] T1 (Q53) — Probe with `pm-probe` and depth 4; record the eight observations. Partial results are recorded below: items 1, 2, 3, 5, 7 and 8 observed; item 4 unobserved and item 6 pending.
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
- **Item 6 PENDING** — Requires the orchestrator key to pass its TTL.
- **Item 7 PASS** — `workflow-systematic` and `ce:plan` both loaded in a PM session under the workflow guard with no failure code. The Systematic workflow guard reported `state=waiting, reasonCode=missing-evidence, enforcement=observe`. A repeat skill load neither re-minted a key nor bumped `last_active`; this is recorded as a finding.
- **Item 8 PASS** — `ctx_memory` write (id 1087), read-back, and `ctx_search` hit all succeeded with no denial or gate.
- **Finding (item 1/2)** — A Task-dispatched session carries no `.parent` and no `inherited.key` until it dispatches a child of its own; the parent marker is written on the child's dispatch. Q58 must not assume a PM has a parent link on entry.
- **Finding (item 2)** — `inherited.key` `minted_at` values were not monotonic with chain creation order. This is recorded as an observation only, with no mechanism asserted; investigate before Q58 gates on key state.
- **Routing-guard log path** for future probe evidence: `~/.local/share/opencode/logs/routing-guard.log`. A plain workflow-key mint writes no line there.
- **Next step:** Item 6 (TTL/expiry), then decide item 4's placement in Q55.

## Next step
T1 (Q53): item 6 (TTL/expiry), then decide item 4's placement in Q55. T2 waits on the owner passing Handover A across.
