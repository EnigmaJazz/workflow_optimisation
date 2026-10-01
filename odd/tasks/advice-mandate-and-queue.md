# Advice Mandate and Complete Work Queue

## Objective
Apply plan B slices B0 (coherence fixes), B1 (mandatory advice policy, interim lane) and B2
(tracker protocol for advisory evidence) from `docs/advisor/handoff-workflow-optimisation.md`,
and rebuild `docs/TODO.md` so every planned work unit is listed in order with its prerequisites.

## Problem
- `docs/TODO.md` has become a dated append-log: item headers contradict later entries (item 1
  "IN PROGRESS" though closed in `71a2eb3`; item 3 "nothing is live" though the guard is live;
  item 4 open though advisors are registered), and the "BLOCKER (active)" header is stale.
- Planned work is spread across `docs/PLAN.md`, `docs/TODO.md`, `odd/tasks/routing-guard-keys.md`
  and `docs/advisor/handoff-workflow-optimisation.md`, with no single list of prerequisites.
- `WORKFLOW.md` carries `## Pre-code advice (advisors)` twice.
- The impact axis "shares one trigger set" with advice; once advice is mandatory for every
  non-trivial change, impact must decide how much advice, not whether.
- `ROUTER-LOG.md` has an earlier row rewritten in place, a duplicate appended row, and three rows
  not in the table format.

## Why
The user requires that all planned work is in the TODO list with prerequisites specified, and
the advice mandate is the cheapest earlier gate against the defect class reviews keep finding.

## Scope
- `docs/TODO.md` (rebuild as an ordered queue) and `docs/TODO-HISTORY.md` (verbatim preservation
  of the dated entries being removed from the queue).
- `WORKFLOW.md` advice section (merge, mandate, interim and external lanes, external-lens review,
  subscription rule, throughput note, advisory-evidence tracker protocol).
- `docs/PLAN.md` (sequence, layers, impact redefinition, recorded decisions).
- `ROUTER-LOG.md` and `CLAIM-RETRACTIONS.md` (ledger hygiene, this unit's route row).

## Constraints
- Documentation only. No change to `global-config/`, plugins, skills or `verify-workflow.sh`.
- `WORKFLOW.md` must keep every keyword `verify-workflow.sh:4073` checks: `ce:brainstorm`,
  `ce:plan`, `ce:work`, `ce:review`, `ce:compound`, `RDD`, `ROUTED:`, `Required Thinking Layers`,
  `## Substantial ODD work units and review — Gentle AI 3.5.0`, `## Route decision checkpoint`,
  `basis: WORKFLOW.md`.
- Ledgers are append-only: never rewrite an earlier row to read better.
- Preserve the work under way: the five `advisor-*` subagents, `docs/ADVISOR-HANDOFF.md`,
  `odd/tasks/routing-guard-keys.md`.
- B3–B6 are not implemented here; they are queued with prerequisites.
- Commits: Conventional Commits with the repo's `— ROUTED: <class>@<gate> (<date>)` suffix; no
  AI attribution trailer (user rule).

## TDD
Mode: off (source: no project TDD configuration; documentation-only unit). Runner: none.
Ordinary checks apply (see Checks).

## Tasks
- [x] T1 — Rebuild `docs/TODO.md` as one ordered queue covering every planned unit, each with
  status, prerequisites and source; move the dated entries verbatim to `docs/TODO-HISTORY.md`;
  apply B0 fixes 1, 2 and 5. Route: delegated (writer trigger: 2+ non-trivial files).
- [x] T2 — `WORKFLOW.md`: merge the duplicate advice sections (B0 fix 3), apply B1 and B2.
  Route: delegated (same writer).
- [x] T3 — `docs/PLAN.md`: sequence update, impact = how much advice (B0 fix 4), recorded
  decisions. Route: delegated (same writer).
- [x] T4 — Ledgers: restore the rewritten tesla #26 row, convert the three plain-text rows to the
  table format, append this unit's route row. Route: delegated (same writer).

## Acceptance criteria
1. Every planned unit found in `docs/PLAN.md`, `docs/TODO.md`, `odd/tasks/routing-guard-keys.md`,
   `docs/advisor/handoff-workflow-optimisation.md` and `docs/ADVISOR-HANDOFF.md` ("Requested")
   appears exactly once in `docs/TODO.md`, with status, prerequisites (or "none") and a source.
2. No dated history entry is lost: each removed entry appears verbatim in `docs/TODO-HISTORY.md`.
3. `WORKFLOW.md` has exactly one `## Pre-code advice` section stating the mandate; all verifier
   keywords are present.
4. `docs/PLAN.md` sequence matches the TODO queue order.
5. `ROUTER-LOG.md`: no earlier row altered relative to `HEAD`; all new rows are table rows.

## Authorized scope
User authorization 2026-10-01: "Yes" to starting B0 + B1 + B2 as one ODD unit, with the
requirement that all planned work is in the TODO list with any prerequisite specified.

## Checks
- `rg -c '^## Pre-code advice' WORKFLOW.md` → 1.
- Each verifier keyword found by `rg -F` in `WORKFLOW.md`.
- `git diff HEAD -- ROUTER-LOG.md CLAIM-RETRACTIONS.md` shows additions only.
- History preservation: every removed dated heading from `docs/TODO.md` present in
  `docs/TODO-HISTORY.md`.
- Parent structural readback of each file.

## Delivery strategy
`ask-on-risk`. Forecast ~300 authored changed lines; one work-unit commit per task on
`feat/advice-mandate-and-queue`. Push and PR remain the user's decision.

## Progress
- 2026-10-01: tracker created; branch `feat/advice-mandate-and-queue` created from `main`
  (`2a757ab`).
- 2026-10-01: T1 done. `docs/TODO.md` rebuilt as ordered queue Q01-Q23 with status, prerequisites and source; old item bodies and dated entries moved verbatim to `docs/TODO-HISTORY.md` (all 18 removed `## ` headings from main confirmed present). Commit `21c1aa2`.
- 2026-10-01: T2 done. `WORKFLOW.md`: two advice sections merged into one (`rg -c '^## Pre-code advice'` = 1); mandate, interim lane, PLANNED external lane with selection table, external-lens definition and relay-rule cross-reference, `### Advisory evidence in the ODD tracker`; all 11 verifier keywords present. Commit `1bdbd70`.
- 2026-10-01: T3 done. `docs/PLAN.md` sequence matches the TODO queue; layers and impact axis updated; dated 2026-10-01 superseding decision appended (original line kept). Commit `1f748ee`.
- 2026-10-01: T4 done. `ROUTER-LOG.md`: rewritten tesla #26 row restored to its HEAD text; both appended tesla #26 rows kept; three plain-text rows converted to table columns; this unit's row appended; `git diff main` shows additions only for `ROUTER-LOG.md` and `CLAIM-RETRACTIONS.md`. RDD assessment pending (orchestrator). T4 commit recorded in the closing commit.

## Next step
Orchestrator: run the RDD assessment on the work-unit commits and fill the ROUTER-LOG row's gate outcome; push and PR are the user's decision.
