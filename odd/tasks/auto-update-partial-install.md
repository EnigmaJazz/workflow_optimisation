# Auto-update partial install

## Objective
Stop plugin auto-updates from leaving a partially installed package that the config then points
at, which disables the plugin (here: Magic Context, the main memory pathway) on the next OpenCode
start.

## Problem (incident 2026-10-02)
- 07:46:52 BST: the local auto-update plugin (`~/.local/share/opencode-plugin-auto-update-local`,
  loaded via `file://`) ran inside a short-lived verifier probe (`opencode run` in
  `run.*/neutral-cwd`, `WORKFLOW_HEALTH_CHECK_PROBE=1`). It ran `bun add <pkg>@latest` in the config
  dir (`src/update.ts:390-395`) and rewrote the pins in `opencode.json`/`tui.json`: magic-context
  0.44.2 → 0.44.4, aft 0.58.0 → 0.58.2.
- 07:47: OpenCode began installing the new pins into `~/.cache/opencode/packages/`. The probe
  process was disposed mid-install; magic-context 0.44.4 was left without its `package.json`.
- The verifier then preserved the newer pins into `global-config/opencode.json` (`:468-540`) with
  no completeness check.
- 08:00: the sandboxed server restarted; Magic Context failed to load (`ctx_*` tools missing).
- The broken cache dir was removed 2026-10-02 (owner-approved).

## Root causes
1. The plugin runs in verifier probe processes; it ignores `WORKFLOW_HEALTH_CHECK_PROBE`.
2. The plugin has no throttle by default (`OPENCODE_AUTO_UPDATE_INTERVAL_HOURS` default 0), so
   every OpenCode start runs `bun add @latest` for every plugin.
3. The verifier preserves an auto-bumped pin without checking the package is completely installed.
4. Nothing detects or quarantines an incomplete package directory.

## Scope
- Plugin fork (out of repo, local git): probe/disable guard; tests; build.
- `verify-workflow.sh`: completeness check before preserving a pin; detect and quarantine
  incomplete configured-plugin package directories (move, never delete); digest re-pin in
  `global-config/plugins/workflow-health-check.ts`.

## Constraints
- Non-destructive: quarantine by moving into `backups/plugin-quarantine/<timestamp>/`.
- The fork's uncommitted edits (`src/lock.ts`, `src/update.ts`) are already built into `dist/`
  (dist 2026-09-15 23:27 is newer than src 23:26); commit them first as a baseline, then change.
- Forward-compatible (PLAN constraint): no new V1-only coupling beyond the existing plugin shape.
- No AI attribution in commits.

## TDD
Mode: off (no configured project TDD). Runner: fork — `bun test` (new), `bun run typecheck`,
`bun run build`; verifier — `bash -n`, targeted fixture checks, full run.

## Tasks
- [x] T0 — Advice record (mandate). Route: OpenCode `advisor-*` dispatch (owner, TUI).
- [x] T1 — Plugin fork: baseline commit of existing edits; no-op when
  `WORKFLOW_HEALTH_CHECK_PROBE=1` or `OPENCODE_AUTO_UPDATE_DISABLED=true`; test; build.
  Route: delegated writer.
- [x] T2 — Verifier: completeness guard on pin preservation; incomplete-dir detection and
  quarantine; re-pin digest. Route: delegated writer (same).
- [x] T3 — Verify end to end: verifier run, OpenCode restart, Magic Context loads, verifier clean;
  then commit the preserved pin change. Route: parent, owner restarts OpenCode.

## Acceptance criteria
1. A verifier probe never runs the auto-update.
2. The verifier never writes a pin into `global-config/` whose package is incomplete.
3. An incomplete configured-plugin package dir is reported and moved to quarantine, so the next
   OpenCode start reinstalls it.
4. Magic Context loads at 0.44.4 and the verifier passes without `MAGIC_CONTEXT_*` or `ctx_*`
   tool failures.

## Progress
- 2026-10-02: diagnosis complete; broken cache dir removed; branch
  `fix/auto-update-partial-install` created from `feat/advice-mandate-and-queue` (`d314d7a`).

- 2026-10-02: T0 attempt 1 — `opencode run --agent advisor-integration` (auto-update throttled
  via `OPENCODE_AUTO_UPDATE_INTERVAL_HOURS=24`) timed out after 600 s with no answer (exit 124;
  stdout held only plugin load lines). Missing opinion, not approval: the mandatory advice gate is
  BLOCKED. Side effect observed: that long-lived run completed OpenCode's reinstall of
  magic-context 0.44.4 (`package.json` now present, version 0.44.4).

- 2026-10-02: owner chose "retry the advisor". Attempt 2 (`--format json`, 900 s) also timed
  out with zero events. Diagnosis (debug run): `opencode run --agent advisor-integration` falls
  back to the default primary agent ("agent advisor-integration is a subagent, not a primary
  agent"), so the advisor never received the brief. The orchestrator likely waited on an
  interactive permission prompt that a non-interactive run cannot answer. Attempt 3: the
  orchestrator is prompted to dispatch `advisor-integration` itself via Task, with INFO logs.

- 2026-10-02: attempt 3 (orchestrator dispatches via Task) timed out at 900 s. Logs stop at
  instance `init` (07:40:12Z) before any session is created, apart from a `cleanup` line at
  07:41:13Z. No session, no permission ask, no tool call. A 4 s debug run at 07:39:40Z had
  completed normally, so the stall is intermittent and occurs at bootstrap, not in the advisor.
  Cause not established. No `opencode run` processes linger, and there is no auto-update lock.
  Scripted advisor dispatch is therefore unreliable here: a separate defect, to be queued.

- 2026-10-02: T0 DONE. Owner dispatched `advisor-integration` from the OpenCode TUI (via
  `gentle-orchestrator` Task). The advisor could not read the plugin source (permission denied)
  and reasoned from tracker citations.

- 2026-10-02: T1 done in the fork (commits 9f7b120 baseline, eab2992 guard). `src/guard.ts` exports
  `isAutoUpdateDisabled` and `resolveIntervalHours` (default 24). `bun test` 7 pass; typecheck and
  build clean; built `dist/index.js` imported with the probe env returned in 6 ms and left
  `.auto-update.json` untouched.
- 2026-10-02: T2 done: `scripts/plugin-cache-integrity.py` (check-pin, scan), 12 unittest
  cases pass; verifier pin preservation now requires a complete package (otherwise
  `AUTO_UPDATED_PIN_INCOMPLETE_NOT_PRESERVED` warning and the canonical pin is restored by the
  existing overlay rewrite); new check 2c quarantines idle incomplete packages; digest re-pinned.

## Advice record (T0, advisor-integration, model opencode-go/deepseek-v4.1-flash)
Summary of findings and resolution:
1. Quarantine needs mutual exclusion with a live install. **Accepted, adjusted.** The
   `.auto-update.lock` covers only the plugin's config-dir `bun add`; OpenCode's cache install
   has no lock. Rule: quarantine a dir only when its package `package.json` is missing AND its
   newest mtime is ≥ 10 min old AND no `.auto-update.lock` exists. Otherwise report only.
2. Quarantine must be transactional with the pin. **Accepted; covered by design.** A pin whose
   package is incomplete is never preserved into `global-config/`, so the same verifier run
   restores the canonical complete pin to the live config. Reinstall on next start is observed
   (2026-10-02: 0.44.4 reinstalled completely after the dir was removed).
3. Add a second detection point, because the health plugin may not load when its dependency is
   broken. **Partly rejected.** `workflow-health-check.ts` has no Magic Context dependency, and
   it reported "all checks passed" on every start while Magic Context was broken. Accepted
   residual: detection happens on verifier runs. Mitigated by removing the trigger (plugin
   guard).
4. Re-pin the verifier digest after the script edit. **Accepted;** last step of T2.
5. Change the default interval from 0, and add the probe guard. **Accepted:** default 24 h,
   env-overridable.
6. Behavioural test simulating a killed-mid-install dir. **Accepted:** the integrity logic lives
   in a standalone helper, `scripts/plugin-cache-integrity.py`, with fixture tests; the
   verifier calls it.
7. Verify the probe guard against the built `dist/`, not only `src/`. **Accepted.**

## Next step
T3: verifier run, OpenCode restart, confirm Magic Context loads.

## Native review review-f0d7d1d1572a4195 (high risk, four lenses; approved, authority burned)
Range `d314d7a..c6a938f` (488 lines). 8 advisory findings. Resolution:
- R2/R3 pycache committed: fixed. Removed `tests/__pycache__/*.pyc`; `__pycache__/` gitignored.
- R2/R3 pin-detail overwrite: fixed. `pin_detail =` became `+=`, so the not-preserved detail
  survives when preserved pins also exist.
- R2 magic number: fixed. `QUIET_PERIOD_SECONDS = 600` is a named constant in the helper, and the
  verifier relies on the helper default instead of repeating 600.
- R2/R3 deferred-reason key: not a defect. Both keys exist, and the R3 finding itself concludes
  "this is fine".
- R3 no shell integration test: accepted gap, queued as T4.
- Verifier digest re-pinned after the follow-up edit.

- [ ] T4 — Shell-level integration test for the verifier's §2c mapping (quarantined, deferred
  and error helper outputs to `fail` codes) and the pin-preservation fallback. Best done with the
  Q04 verifier split, where check sections become runnable in isolation.

## T3 progress
- 2026-10-02: verifier run after the fix. The probe guard held (`.auto-update.json` mtime unchanged
  across all probe runs). §2c reported `ok: 4 configured plugin package(s) complete or not yet
  installed`. `MAGIC_CONTEXT_CONFIGURED_VERSION_NOT_INSTALLED` is gone. The only failure was the
  expected `SECURE_OPENCODE_RESTART_REQUIRED`.
- Pin change committed as `83e0e58`, after `check-pin` confirmed magic-context 0.44.4 and aft
  0.58.2 complete. It is the same 4-line change approved under `review-dc42e8f206b3d4e6`; RDD
  assess from `9424d69`: medium, under budget. Revert `83e0e58` if the post-restart check fails.
- Remaining: owner restarts OpenCode (both servers), re-runs the verifier, and confirms the
  `ctx_*` tools and memory checks pass.
- 2026-10-02: T3 DONE. Owner restarted `ai-proxy.service` (port 18900 server, now started 09:26:14)
  and `secure-opencode.service` (port 4096, 09:44:33), then re-ran the verifier: all checks passed
  (owner report). Confirmed independently: both server start times, `.auto-update.json`
  unchanged since 07:46:54, and no quarantine entries. Acceptance 1, 2 and 4 met; 3 is covered by
  the helper's fixture tests (12 pass). Open: T4 (shell-level integration test, with Q04).

## Status
DONE except T4, which is queued with Q04.
