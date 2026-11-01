# Q99 — Unblock Gate 1: name the API-credit Gemini carrier for the spec advisor

## Identity and authority

Work unit and task ID: `q99-spec-advisor-route-u1`.
Project: `/home/james/ai-workspace/workflow_optimisation`.
Branch: `chore/coordinator-selection`.
Class: global tooling change — normative planner prompt text plus its pinned tests.
Route: `workflow-odd-secure`.
Owner authorization: 2026-11-01 — "Name the api route for now", answering the block reported from
the Q98 PM dispatch.

## Problem

Observed 2026-11-01 in the Q98 PM dispatch (`pm-odd` session returned `BLOCKED`, no writer, no
diff): the Planner refused Gate 1 twice, because its own binding is unsatisfiable.

- `global-config/opencode.json:518` stated both: "Gemini advisors run only when the external lane is
  active; it is currently PLANNED, so do not dispatch them." and "`advisor-spec-pre` is compulsory
  for every code unit".
- `advisor-spec-pre` is itself a Gemini agent: `global-config/opencode.json:688-692` sets
  `"model": "google/gemini-4-argon"` (and `advisor-spec-post` mirrors it).
- The same prompt forbids substitution: "never substitute an unrelated advisor".
- Consequence: for every code unit the Planner had to dispatch a Gemini spec advisor it was told not
  to dispatch, or return `BLOCKED`. No code unit could reach Gate 1 in that configuration. The Q98
  unit stopped exactly there with `correction_rounds_used: 0`.

This also explains why the PM layer has never completed a unit since it went live.

## Spec

- **S1.** The compulsory specification advice keeps a carrier in every configuration: when the
  Antigravity lane is inactive, the registered API-credit agents `advisor-gemini-pre` and
  `advisor-gemini-post` (`global-config/opencode.json:2230`) carry the pre and post positions.
- **S2.** Exactly one carrier per position; the two are never dispatched together for the same phase.
- **S3.** The phrase "`advisor-spec-pre` is compulsory" survives, because
  `tests/test_spec_advisor_seats.py:91` and the seat contract depend on it; the carrier rule is
  appended rather than replacing it.
- **S4.** Non-goals: no model change, no permission change, no Antigravity activation, no change to
  the PM or handoff contracts.

## Tasks

- [x] T1 (S1-S3): amend the planner prompt's Gemini-lane sentence and append the carrier rule to the
  compulsory bullet; update the tests that read those sentences. Implemented 2026-11-01.
- [ ] T2: record the row in `ROUTER-LOG.md`; reopen Q98 afterwards so the PM can run Gate 1.

## Acceptance criteria

- The planner prompt contains exactly one statement of the carrier rule and one amended
  Gemini-lane statement. Observed via the new executable read-back assertions.
- No model, permission or seat-count change in the diff. `git diff` shows exactly two files:
  `global-config/opencode.json` (the prompt string) and `tests/test_spec_advisor_seats.py`.
- `python3 -m unittest tests.test_spec_advisor_seats tests.test_q90_planner tests.test_gemini_advisor_route`
  passes, with a control proving the carrier sentence is absent before the edit.
- Full suite: no failure attributable to this change against the recorded baseline.

## Allowed edit surfaces

1. `global-config/opencode.json`
2. `tests/test_spec_advisor_seats.py`
3. `tests/test_q90_planner.py`
4. `tests/test_gemini_advisor_route.py`
5. `ROUTER-LOG.md`
6. `odd/tasks/q99-spec-advisor-route.md`

## Constraints

- The planner prompt exists only as an inline JSON string in `global-config/opencode.json`; there is
  no markdown source. Edit the string precisely and keep the JSON valid (`python3 -m json.tool`).
- Test-first: add the carrier assertion and observe it RED before editing the prompt text.
- Delegation exception, recorded: this unit is dispatched delegated-direct because the PM route is
  blocked by the defect this unit fixes. Owner instruction 2026-11-01 authorized the route change.
  The next code unit must go back through `pm-odd`.
- Normative text: post-code check and the native review gate after the commit.
- No deployment; `derive --apply` and restarts remain the owner's action.

## Progress

- 2026-11-01: tracker created; implementation dispatched delegated-direct under the recorded
  exception.
- 2026-11-01: T1 implemented. Clause A is now "Subscription Gemini advisors …" with the API-credit
  carriers exempted; the single-carrier-per-position rule is appended to the compulsory bullet. TDD:
  the carrier assertion was observed RED (`'When the Antigravity lane is inactive' not found`) before
  the prompt edit. `tests.test_spec_advisor_seats tests.test_q90_planner
  tests.test_gemini_advisor_route` = 49 tests OK; `json.tool` valid. Full-suite failures are the
  pre-existing sandbox environment set (missing `sqlite3`, denied `node`), none touching this change.
  Side effect recorded: the editor added a trailing newline to `global-config/opencode.json`.

## Next step

Commit the installed candidate, then re-dispatch Q98 through `pm-odd` and confirm Gate 1 issues.


## Revisions
- r1 2026-11-01T17:57:56Z gentle-orchestrator: Create Q99 tracker: unblock Gate 1 by naming the API-credit Gemini carrier for the compulsory spec advisor
- r2 2026-11-01T18:51:19Z gentle-orchestrator: Tick T1 and record the implementation evidence and RED observation
