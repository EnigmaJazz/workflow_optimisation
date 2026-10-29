# Auto-update propose-only rewrite (local fork)

Objective: replace the in-session apply path of the local `opencode-plugin-auto-update` fork with a
propose-only, host-aware, dual-mode (V1 `server`, V2 `setup`) plugin. Decided by the owner
2026-10-28 (plan: `~/ai-workspace/OPENCODE-V2-UPGRADE-PLAN.md` section 9). Repo (out of this repo):
`~/.local/share/opencode-plugin-auto-update-local`, branch `feat/propose-only`. Runner: `bun test`,
`bunx tsc --noEmit`, `bun run build`. Implemented by Claude Code on the owner's explicit override of
the advisory role.

## Specs
- S1: never writes `opencode.json`, `tui.json`, `cli.json` or installs packages.
- S2: reads `plugin` and `plugins`, string and `{package, options}` entries, JSONC.
- S3: gate rejects V2-only plugins on a V1 host and V1-only on a V2 host (peer ranges), holds
  major bumps, prereleases rejected, unknown host holds.
- S4: writes `pending-updates.json` atomically under `$XDG_STATE_HOME`.
- S5: no-op under `WORKFLOW_HEALTH_CHECK_PROBE=1` / `OPENCODE_AUTO_UPDATE_DISABLED`.
- S6: one default export `{id, setup, server}`.

## Tasks
- [x] T1 core + tests (S1-S4): fork commit `ff03f85`.
- [x] T2 runner, dual-mode entry, old apply path removed (S1, S5, S6): fork commit `1ffc20e`.
  35 tests pass, typecheck and build clean; real-data run on a scratch copy of the live config
  proposed Systematic 3.26.0 -> 3.27.0 and Magic Context 0.49.20 -> 0.49.28.
- [x] T3a consumer: `scripts/plugin_pins.py` (report/apply, edits only `global-config/`), `tests/test_plugin_pins_apply.py` 12 tests; verifier untouched so no digest re-pin. Queue entry Q93.
- [ ] T3b (deferred, needs a digest re-pin): verifier advisory line for pending proposals.
- [ ] A5 (revised): deploy the propose-only build at the reviewed path; owner restarts OpenCode.
  Blocked on T4.
- [ ] T4 load check on a real V1 host and, after the V2 probe, on V2. NOT DONE.

## Log
- L1 (2026-10-28, owner): "Propose only rewrite".
- L2: the live `dist/` was rebuilt during T2 by mistake and restored from `main` immediately;
  the deployed plugin is still the OLD apply-mode build. The new build is not deployed.
- Known gap: an unpinned entry is reported `hold/unpinned` and its peer compatibility is not
  shown (the statusline 2.1.0 V2-only case). Follow-up inside T3.
- L3 (2026-10-29): review outcome. Assessment on `11d7aeb..8ed94f2` was high (executable_mode,
  process_boundary on `scripts/plugin_pins.py`). OpenCode relay refused the five-commit candidate
  (`opencode_review_transport_binding_invalid`; local relay defect, not filed upstream). OpenCode
  read-only inspection (not a review verdict) found F1 false positive (shebang), F2-F6 hardening;
  fixed in `d8a0024`. Re-assessment at `d8a0024`: medium, 470 lines, `review_due: false`,
  under budget. Owner decision: no native receipt for this slice.
