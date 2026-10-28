# OpenCode V2 Phase A: V1-safe plugin pin preparation

Objective: make the pinned plugin set in `global-config/` correct and consistent on V1 1.19.5
while being the set that also loads on V2 (2.2.0 probe target). Branch `chore/opencode-v2-phase-a`
off `main`. Test runner: `python3 -m unittest`. Plan: `~/ai-workspace/OPENCODE-V2-UPGRADE-PLAN.md`
(Phase A, A1-A6). Implemented by Claude Code on the owner's explicit override of the advisory
role (2026-10-28).

## Specs
- S1: `opencode-subagent-statusline` is pinned to `@1.3.1` in `global-config/tui.json` (A1).
  Evidence: 2.x is V2-only and refuses V1; the entry was unversioned (`@latest`).
- S2: `@fro.bot/systematic` is `3.27.0` and `@cortexkit/opencode-magic-context` is `0.49.28` in
  `global-config/opencode.json` and `tui.json` (A2). `@cortexkit/aft-opencode` stays `0.62.0`.
- S3: `global-config/tui.json` has the same pins as `opencode.json` for shared packages, and no
  `@fro.bot/systematic` entry (Systematic has no `./tui` export) (A3, A6).
- S4: no `workflow_guard` key in `global-config/systematic.jsonc` (A4). Already true at source;
  only the live copy is stale until the verifier mirrors.
- Out of scope here: A5 (retire auto-update; needs verifier changes and a digest re-pin), A7
  (backups), live `tui.jsonc` drift (not in `global-config/`).

## Tasks
- [x] T1 (S1-S3): `tests/test_plugin_pins.py` RED (5 failures) then pins edited GREEN; full suite 388 OK. Route: inline. Uncommitted.

## Log
- L1 (2026-10-28, owner): "I have spare claude code usage and I want to overrule advisory role
  for this work and do as much as possible with claude code".
- L2: advice record: the OpenCode `advisor-*` dispatch is not reachable from Claude Code; the
  Claude Code `advisor` tool was consulted for the plan (2026-10-28). Mandate gap recorded, not
  closed.
- L3 (2026-10-28): T1 committed as `eb4a633`. Native review assessment: risk medium
  (`configuration_change`), `review_due: false`, reason `under_budget` (108 changed lines, base
  `11d7aeb`). Outcome: under budget; stays pending in the slice until a later commit reaches the
  review budget. Review lanes stay the in-OpenCode `asi-review-*` lanes.
