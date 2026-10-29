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
- [ ] T3 verifier consumes `pending-updates.json` (apply approved bumps through `global-config/`)
  and A5 retires the old build from the config. Not started; touches `verify-workflow.sh` and the
  digest pin.
- [ ] T4 load check on a real V1 host and, after the V2 probe, on V2. NOT DONE.

## Log
- L1 (2026-10-28, owner): "Propose only rewrite".
- L2: the live `dist/` was rebuilt during T2 by mistake and restored from `main` immediately;
  the deployed plugin is still the OLD apply-mode build. The new build is not deployed.
- Known gap: an unpinned entry is reported `hold/unpinned` and its peer compatibility is not
  shown (the statusline 2.1.0 V2-only case). Follow-up inside T3.
