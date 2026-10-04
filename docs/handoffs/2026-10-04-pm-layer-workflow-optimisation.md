# Handover B — project-manager layer (workflow_optimisation)

**For:** the OpenCode agents working in this repository.
**From:** owner decision and Claude Code advisory plan, 2026-10-04.
**Tracker:** `odd/tasks/pm-layer.md`. **Queue:** `docs/TODO.md` Q53–Q61.
**Self-contained:** you do not need the other handover (Handover A, for agent-sandbox-integration)
beyond the dependency stated under Q54.

## Problem

The orchestrator loses its routing rules in long sessions, even with Magic Context. Its prompt is
70,817 characters and the global `AGENTS.md` adds 23,513. Subagents comply because their context
is short and fresh: they load the right skill at the start and finish before it fades.

A second defect follows from the same cause. Stage markers and workflow keys accumulate in one
long orchestrator session, so evidence from an earlier change can satisfy a stage for a later
one. `WORKFLOW.md` "Each change is a new routed task" forbids that, but only in prose.

## Design (owner decisions, 2026-10-04)

**Two levels.**
- `gentle-orchestrator` (primary) is the strategic front end: the user interface, the walk
  through `docs/PLAN.md` and `docs/TODO.md`, an initial plan per change, the route choice, and a
  read-only check of each result. It dispatches only `explore` and `pm-*`.
- A **project manager (PM)** subagent runs **one work unit** to completion. One PM session per
  unit, never per feature: a PM that runs a whole feature would grow the same long context. State
  between units lives in the tracker, not in a session.

**Agents.**

| Agent | Route skill it loads first | Covers |
|---|---|---|
| `pm-odd` | `workflow-odd-secure` | tiny fix, documentation, global tooling change, ODD task units |
| `pm-systematic` | `workflow-systematic` | small feature, bug investigation, substantial feature (planning unit, then one unit per task) |
| `pm-sdd` | `workflow-sdd-secure` | selected SDD only. V1-only; retired by the gentle-ai v4 change set (Q36) |
| `odd-apply` | (writer) | implements one ODD unit and updates the tracker and router log in the same worker lifecycle |

- A PM has today's orchestrator permissions minus what its route does not use. It never has
  sandbox mutation tools, `bash`, `edit` or `write`. It cannot enter the sandbox, so the
  single-lifecycle worker limit never applies to it.
- PM prompts are short (budget about 6,000 characters): identity, the unit contract, "load skill
  X first", and the result envelope. Route detail stays in the `workflow-*` skills, which remain
  the single source.
- Frontend work: the PM dispatches `frontend-dev` or `frontend-dev-premium` as the route says.
- `subagent_depth` rises from 3 to 4 (orchestrator → PM → `frontend-dev` → `frontend-apply` →
  `vision`).

**Unit handoff contract** (to be written as `docs/specs/pm-handoff.md`, Q55).
- **Brief in:** unit ID, tracker path, task class, route, the orchestrator's initial plan, the
  last reviewed boundary, constraints.
- **Route check first.** The PM confirms the class and route against `WORKFLOW.md`. If it
  disagrees it returns `ROUTE_DISPUTED` with reasons and does nothing else.
- **Then the route, in order:** pre-code advice → writer → checks → work-unit commit → post-code
  advice or `ce:review` (as the route owes) → native review → tracker, `docs/TODO.md` and
  `docs/PLAN.md` update.
- **Result envelope:** `DONE`, `NEEDS_INPUT`, `BLOCKED` or `ROUTE_DISPUTED`; the commit; each
  check with its observed result; the advice record; the review outcome; the new reviewed
  boundary.
- **Human input.** Permission prompts surface from the PM session directly. For anything else
  the PM returns `NEEDS_INPUT` carrying the prompt verbatim (lossless relay, including the
  gentle-ai consent envelope). The orchestrator asks the user and resumes the **same** PM session
  with the Task tool's `task_id`. If the Q53 probe shows `question` works from a subagent, the PM
  asks directly and the relay is the fallback.
- **Planning is a unit.** `ce:brainstorm`, `ce:plan` and tracker creation are run by a PM as
  their own unit, with their own commit.
- **The orchestrator verifies.** Before dispatching the next unit it reads the tracker and git
  and compares them with the `DONE` envelope. A PM report is a claim, not evidence.

## Verified facts (2026-10-04)

- OpenCode 1.18.34's Task tool takes `task_id` to continue the same subagent session.
- Depth: a session with `n` ancestors may dispatch while `n < subagent_depth`.
- A child session inherits only the parent **session's** deny rules, not the parent agent's
  config. A read-only orchestrator therefore does not restrict a PM's workers. A subagent has
  `task` and `todowrite` denied unless its own config grants them.
- `opencode run` denies `question`. Whether `question` works from a subagent in the TUI is
  **unverified** (Q53).
- Host mutations are bound to the name `gentle-orchestrator` in agent-sandbox-integration
  (`opencode/plugins/sandbox-tools.ts:64`, `broker/src/config.ts:243`). Until Handover A lands,
  a PM cannot commit or start a review.
- `verify-workflow.sh` names `gentle-orchestrator` 23 times.
- The guard's inheritance walk is 3 hops (`MAX_INHERITANCE_HOPS`). A PM holds its own key, so its
  workers stay within 3 hops of it.
- Model families: a PM on `openai/gpt-6.1-sol` shares a family with `general` (Luna) and with
  `advisor-design-pre` and `advisor-security-pre` (Sol).

## Work, in order

Every item is tests-first where a test is possible, carries the advice mandate, ends with a
work-unit commit, and needs the deploy step (verifier mirror, owner restart, verifier pass).
Forward-compatible by default (`docs/PLAN.md` Constraints): nothing new may depend on SDD,
`host_sdd_*` or V1-only plugin hooks, except `pm-sdd` itself.

### Q53 — Probe (go/no-go)

Add a temporary hidden subagent `pm-probe` (read tools, `task`, `question`, `ctx_memory`, host
read tools; no mutation) and set `subagent_depth` to 4. Mirror; owner restarts. From the TUI,
have the orchestrator dispatch `pm-probe` and record each observation in the tracker with the
session ID and the matching `routing-guard.log` lines:

1. A four-level chain dispatches (orchestrator → `pm-probe` → `frontend-dev` → `frontend-apply`
   → `vision`, or an equivalent read-only chain).
2. `pm-probe` loads `workflow-odd-secure`: a key is minted in the PM session, and a worker it
   dispatches inherits it.
3. `question` asked by `pm-probe` reaches the user.
4. An ask-gated permission prompt from `pm-probe` reaches the user.
5. `pm-probe` returns `NEEDS_INPUT`; the orchestrator resumes it with `task_id`; the PM still has
   its earlier context.
6. Key state on resume when the orchestrator's key has expired (wait past the 30-minute TTL, or
   shorten it in a test). Expected: the PM must reload its skill. Record what happens.
7. `ce:plan` loads in the PM session under Systematic's workflow guard without a failure code.
8. `ctx_memory` write and read-back from the PM session.

**Acceptance:** all eight recorded as observed. A failure is a finding, not a blocker by itself:
record it and revise the affected item before starting it. Failures of 1, 2 or 5 stop the work.

### Q54 — Sandbox allowlist (cross-project dependency)

Owner passes `docs/handoffs/2026-10-04-pm-layer-agent-sandbox-integration.md` to that project.
When it is installed, probe from `pm-probe` on a throwaway candidate: `host_git_commit`,
`host_review_start`, one `asi-review-*` relay Task, and `host_review_status`. Record the
contract statement the sandbox side returns.

**Acceptance:** each call succeeds from a subagent session, and a worker session is still
refused. **Prerequisite of Q56.**

### Q55 — Contract, agents and writer

- `docs/specs/pm-handoff.md`: the unit handoff contract above, with the exact envelope fields.
- `global-config/opencode.json`: `pm-odd`, `pm-systematic`, `pm-sdd`, `odd-apply`; the PMs added
  to the orchestrator's `permission.task`. Remove `pm-probe`.
- PM prompts, within the size budget.
- Guard data in `global-config/plugins/lib/routing-guard-helpers.ts`: `SPECIALIST_WRITERS` gains
  `odd-apply`; `pm-` names are coordinators, never writing specialists. Tests first in
  `tests/routing-guard/routing-guard.test.ts`.
- The three places that state the specialist policy stay consistent: `ROUTE_STAGES`, the
  `opencode.json` task permissions, and the route skills.

**Acceptance:** guard suite green with new cases; the verifier's agent-registration checks pass;
each PM dispatches from the TUI and returns a well-formed `ROUTE_DISPUTED` for a deliberately
wrong route.

### Q56 — Pilot on one route

Run global-tooling units in this repository through `pm-odd`. Keep the current orchestrator
available as `gentle-orchestrator-legacy` (a second primary agent with today's prompt and
permissions). Rollback is switching `default_agent` back, then verifier and restart.

**Acceptance:** ten consecutive units complete through `pm-odd` with no route escape, each
logged in `ROUTER-LOG.md`, and no new `CLAIM-RETRACTIONS.md` row caused by routing.

### Q57 — Slim the orchestrator

- New orchestrator prompt, budget about 8,000 characters.
- `permission.task`: `"*": "deny"`, then `explore` and `pm-*` allowed. Host mutations removed,
  except `host_register_project` (`ask`).
- Split `global-config/AGENTS.md` into the contract every agent needs and PM-only material.
- Update `WORKFLOW.md` (the orchestrator sections become the orchestrator and PM contract),
  `workflow-route` and the three adapters.
- Align with Q29c: the user-owned orchestrator prompt rebuilt on gentle-ai v4's managed prompt is
  now this slim prompt.

**Acceptance:** a read-only request dispatches no PM; a change request dispatches exactly one PM
and no writer; the legacy agent is still selectable.

### Q58 — Guard ordering

Warning-only, as today. Tests first.
- A PM agent must hold its own route's key (`pm-odd` ↔ `workflow-odd-secure`) before
  `host_git_commit`, `host_review_start` or a writer dispatch.
- The orchestrator dispatching a writing specialist directly warns.
- New stages: advice record before the writer; commit before the review start.
- Add the rows to the gating matrix (Q28).

**Acceptance:** each rule has a failing-then-passing test with a positive control.

### Q59 — Verifier

Replace the single-name checks with a coordinator set (`gentle-orchestrator` plus `pm-*`):
- only PMs hold ask-gated host mutations; only the orchestrator holds `host_register_project`;
- no coordinator holds a sandbox mutation tool, `bash`, `edit` or `write`;
- `subagent_depth` is 4;
- writer and PM are in different model families, including after the first fallback;
- **prompt-size budgets** for the orchestrator and each PM (this enforces the root cause);
- behavioural probes: a read-only request dispatches no PM; a change request dispatches one PM
  and no writer. Note that `opencode run --agent <subagent>` falls back to the primary agent
  (Q51), so PMs are probed through the orchestrator.
- Re-pin `VERIFY_SCRIPT_SHA256` in `global-config/plugins/workflow-health-check.ts`.

**Acceptance:** verifier clean; each new check shown to fail on a deliberately broken fixture.

### Q60 — Models

Wait for the external model-assignment advice already requested. Proposal to test against it:
- PMs on `openai/gpt-6.1-sol`, so the plan is drafted by one family (DeepSeek orchestrator) and
  finalised by another;
- writers on DeepSeek (`odd-apply`, `sdd-apply`); `general` stays the fallback writer;
- move `advisor-design-pre` and `advisor-security-pre` off Sol, so pre-code advice comes from a
  third family;
- fallback chains keep a PM off its writer's family;
- exclude PMs from the Astra aliases (`astra-sol-upgrade.ts`), because a PM holds commit
  authority.

**Owner decision:** whether tiny-fix and documentation units use a cheaper PM model.

### Q61 — Remaining routes and close

Move the Systematic and SDD routes to `pm-systematic` and `pm-sdd`; remove
`gentle-orchestrator-legacy`; record the learnings with `ce:compound`.

## Risks

- **OpenCode V2 has no `subagent_depth` equivalent** (Q43). This design depends on nesting, so
  the V2 side-by-side probe (Q41) must test a four-level chain.
- The orchestrator is blocked while a PM runs in the foreground.
- A long wait for human input can expire the orchestrator's key; see Q53 item 6.
- A Sol PM on every unit raises cost; Q60 decides the tiering.
- `gentle-ai sync` rewrites the managed orchestrator agent; the verifier overlay must treat the
  PM agents and the slim prompt as user-owned.

## Verification commands

- `HOME="$(mktemp -d)" bun test tests/routing-guard`
- `python3 -m unittest discover -s tests`
- `bash verify-workflow.sh`, and `bash verify-workflow.sh --behavioral` for the dispatch probes
