# Q105 — Unhide the Planner and the advisors (hidden agents cannot be dispatched by name)

## Identity and authority

- Unit: `q105-unhide-planner-u1`, task `T1` (tracker creation and implementation in one unit).
- Project: `worktrees` (repository `workflow_optimisation`, worktree `q105-unhide-planner`).
- Branch: `fix/q105-unhide-planner`, from `origin/main` `54115d5`.
- Class: global tooling change. Route: `workflow-odd-secure`.
- Owner authorization: 2026-11-10 dispatch — unhide the Planner and the advisors, run the probe first and record whether hiding is the proven cause, with the D33 permission rules if they edit the same file.
- Spec: `docs/TODO.md` Q105 (`:2384-2405`).

## Problem

`global-config/opencode.json` declares `hidden: true` for `planner`, `planner-evidence` and the
`advisor-*` seats. A hidden agent is absent from the listing a dispatcher sees, so the Planner cannot
dispatch the advisors its `permission.task` allowlist names, and Gate 1/Gate 2 cannot be issued. Q105
blocks every routed unit's Gate 2.

## Observed evidence (probe, 2026-11-10)

- **observed** — a `pm-odd` unit was dispatched for this work and its Planner dispatch listed only
  `explore`, `gentle-ai-verify` and `gentle-ai-verify-routine` as exposed subagents. `planner`,
  `planner-evidence` and all 13 `advisor-*` agents were absent, while the config declares them
  `hidden: true`.
- **observed** — the Planner returned `BLOCKED: compulsory advisor-spec-pre is unavailable`, issued no
  substitution and no Gate 1 verdict, so the PM returned `BLOCKED` with no writer and no diff.
- **observed** — the Planner prompt at `global-config/opencode.json:518` already names the advisors, so
  Q105's cheaper test ("keep them hidden and name each advisor in the prompt") was already in place and
  is **not sufficient by itself**. Hiding remains the remaining difference between the allowlist and
  the listing.
- **not run** — the post-restart A/B probe (the Planner dispatching `advisor-spec-pre` and
  `advisor-testing-post` by name against the deployed config) is deferred to the owner's restart and is
  **not** claimed as a result.
- **observed** — count correction: `docs/TODO.md` says 15 `advisor-*` agents, but the config has 13
  (Q131 removed `advisor-gemini-pre`/`-post`). This unit unhides 13 advisors + `planner` +
  `planner-evidence` = 15 agents.

## Route exception (recorded)

The PM route is deadlocked by the defect this unit fixes: `pm-odd` must dispatch the Planner, and the
Planner cannot dispatch its advisors while they are hidden. This unit therefore ran **delegated-direct**
from the orchestrator to a `general` writer, under the same recorded exception as
`odd/tasks/q99-spec-advisor-route.md:72-74`, with the owner's explicit 2026-11-10 authorization.

## Spec

- S1. `planner`, `planner-evidence` and all 13 `advisor-*` agents get `hidden: false`; no other agent's
  visibility, model, variant, prompt, tools or permissions change.
- S2. A verifier check fails whenever a target the Planner is allowed to call is neither visible nor
  named as a backticked token in the Planner prompt.
- S3. The pinned tests that assert `hidden: true` are updated to the new intended state, and a new test
  module pins the rule with positive controls.
- S4. Non-goals: no deploy, no `derive --apply`, no restart, no push, no permission widening, no change
  to any caller's `task` allowlist.

## Tasks

- T1 — probe and record the per-lane result (done: see Observed evidence).
- T2 — flip `hidden` on the 15 agents (done, `ff1af3e`).
- T3 — add the visibility rule to `verify/checkers/check-runtime-agents.cjs` and wire it (done).
- T4 — tests and the stale predicates (done).
- T5 — verifier manifest and digest re-pin (done).
- T6 — tracker, `ROUTER-LOG.md` row, `docs/TODO.md` status (done, `c0815f9`).
- T7 — Codex review correction: unconditional visibility (done, `5cb31e1`).

## Acceptance criteria

- `python3 -m json.tool global-config/opencode.json` parses; the diff touches only the `hidden` field of
  the 15 named agents.
- Every one of the 15 required-visible agents is reported `PLANNER_ADVISOR_HIDDEN: <name>` when its
  `hidden` is set true, independent of prompt naming, including `advisor-evidence`, which is not in the
  Planner's `task` map.
- `PLANNER_ADVISOR_UNREACHABLE: <name>` for a hidden, unnamed allowlisted task target; reachability
  accepts a hidden target that is named in the prompt while visibility still reports it.
- The suite `python3 -m unittest tests.test_q90_planner tests.test_spec_advisor_seats
  tests.test_planner_advisor_visibility tests.test_advisor_checker_policy` passes.
- `python3 scripts/verifier_manifest.py check` reports the manifest and pin are current.

## Checks observed

- `python3 -m unittest tests.test_q90_planner tests.test_spec_advisor_seats
  tests.test_planner_advisor_visibility tests.test_advisor_checker_policy` — 41 tests OK after the
  correction (39 before it).
- Per-agent mutation control: all 15 names emitted `PLANNER_ADVISOR_HIDDEN: <name>`; the literal
  observed list is in the correction batch report.
- `python3 -m json.tool global-config/opencode.json` — parses.
- `python3 scripts/verifier_manifest.py update` — `manifest regenerated`; `plugin pin updated`.
- `python3 scripts/verifier_manifest.py check` — `ok: manifest and pin are current`.
- `git diff --check` — no output.
- Independent verifier (`gentle-ai-verify`, before the correction): its FAIL label was caused solely by
  its own sandbox refusing inline `node -e` argv; it reported no behavioural finding, and the six
  control tests passed under its own execution. Recorded as a method gap, not as its PASS.

## Review outcomes

- Codex review of `ff1af3e` — one MEDIUM: the prompt-naming escape satisfied the visibility rule and
  `advisor-evidence` sat outside the checked task map, so the control proved only hidden-and-unnamed
  detection. Fixed in `5cb31e1` with an explicit 15-name required-visible inventory and a per-agent
  hidden mutation control. SECURITY was clean: 15 flips, no permission or task-allow changes.
- Native RDD assessment of `54115d5..ff1af3e` — `high` risk (`verify-workflow.sh` shell-process
  surface), `review_due: true`, reason `high_risk`. The Codex review is this unit's review gate per the
  owner's dispatch; native review remains available and is not claimed as run.

## Process deviation (recorded, not concealed)

Test-first was instructed and was **not** followed in the intended order: the writer's first suite run
happened after the config edit, and it failed on the stale `PLANNER_NOT_HIDDEN` predicate and an
incomplete prompt-name control. Both were fixed before the passing run. There is therefore no captured
RED output for this unit; the `PLANNER_NOT_VISIBLE` / `PLANNER_EVIDENCE_NOT_VISIBLE` failures observed
on the first run are the closest evidence available and are reported as such.

## Advisories

- `tests.test_orchestrator_prompt_source.CoordinatorSelectionRuleTests.test_nonprompt_config_tree_matches_the_pinned_digest`
  fails: the `NONPROMPT_CONFIG_SHA256` pin is stale on main and pre-existing. Tier 2 ruled it out of
  scope; it is not fixed here. On this branch the digest also moves with the `hidden` flips, so the
  owner should expect the red test until that pin is refreshed in its own unit.
- `tests.test_derive_v2_config.RealConfig.test_everything_except_the_plugin_list_is_carried_over_unchanged`
  (`53 != 55`) and `...test_no_prompt_is_taken_from_the_live_root_any_more` are pre-existing
  environment/drift failures: this diff adds and removes no agent key, the hardcoded `48` is two high
  after Q131 removed the two Gemini advisors, and the derive copies two skills from the live V1 root.
- The V2 verifier will report `PLANNER_NOT_VISIBLE` / `PLANNER_EVIDENCE_NOT_VISIBLE` against the
  currently deployed root until the owner runs `derive --apply` and restarts. That is configuration
  drift, not a defect introduced here.

## Open questions

- Post-restart A/B probe unrun: the owner's restart plus one Planner dispatch of `advisor-spec-pre` by
  name is the confirmation.

## Next step

Owner derives, restarts and runs the deferred probe. No deployment was performed by this unit.


## Revisions
- r1 2026-11-10T15:02:38Z gentle-orchestrator: Create the Q105 tracker: unhide the Planner and its advisors, with probe evidence and checks
- r2 2026-11-10T15:32:53Z gentle-orchestrator: Record the Codex MEDIUM correction, the 15-name control, review outcomes and advisories
