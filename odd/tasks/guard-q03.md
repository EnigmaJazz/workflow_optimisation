# Routing guard Q03

## Objective
Fix the routing guard's stage and key logic and give it its first automated test suite (queue Q03,
absorbing the overlapping Q20 and Q21 findings).

## Scope
- `global-config/plugins/systematic-routing-guard.ts`: implementation, by a delegated cheaper
  writer.
- `docs/specs/routing-guard-q03.md`: the design (strong model).
- `tests/routing-guard/routing-guard.test.ts`: the acceptance suite (strong model).
- Deploy: verifier mirror, digest re-pin if needed, OpenCode restart (owner).

## Decisions
- 2026-10-02 (owner): specialist rule is **deny by default**. Every writing specialist is gated
  by a stage's `allowsSpecialists`; read-only agents are exempt.
- Correction recorded: R2-001 was not an inverted predicate. The real gap is the allow-list
  semantics.

## TDD
Mode: on (owner strategy, spec and tests first). Runner: `HOME="$(mktemp -d)" bun test
tests/routing-guard`. The suite refuses to run against a real HOME.

## Tasks
- [x] T1 — Design `docs/specs/routing-guard-q03.md`. Route: inline (strong model).
- [x] T2 — Acceptance suite; RED observed. Route: inline (strong model).
- [x] T3 — Advice record on the design (owner TUI dispatch; Q51 open).
- [x] T4 — Implement to GREEN. Route: delegated writer.
- [x] T5 — Native review; verifier mirror; owner restart; verifier pass.

## Progress
- 2026-10-02: the map of the guard (read-only explorer) established the testability constraints:
  hooks are fire-and-forget, `homedir()` is fixed at import, and bun's `homedir()` ignores
  `HOME` changes at runtime. Hence the state-root seam.
- 2026-10-02: RED. The first run had 9 vacuous passes (absence assertions against the wrong
  root); fixed with a positive-control probe in every absence test. Final: 37 tests, 0 pass,
  37 fail.

- 2026-10-02: T3 advice (`advisor-integration`, owner TUI). 10 findings; all settled in design
  rev. 2 and the tests:
  1. Bounded the awaited chains with a 2 s time box.
  2-3. The seam covers all four `homedir()` uses, via accessors read at each use.
  4. The read-only exemption is an exact declared set from real agents plus structural patterns;
     loose matching is dropped.
  5. Stage writer lists cover every legitimate writer; only undeclared writers get "not
     allowed". Three-place policy consistency goes to Q28.
  6. Legacy unnamespaced markers count only while the stage id is unique (pure
     `stageMarkerNames`, tested with a synthetic collision table).
  7. Migration premise verified on disk: 25 `artifact-tracker`, 23 `artifact-odd-tracker`, no
     Systematic artifact markers.
  8. Refresh touches valid keys only.
  9. One bootstrap warning per multi-path patch.
  10. The V2 hook-skipping scope is noted for Q42.
  Added from my own on-disk check: qualified skill names are canonicalised (`systematic:ce:plan`
  gives `skill-ce-plan`). Suite: 43 tests, 0 pass, 43 fail.
- 2026-10-02: T4 done. RED 0 pass/43 fail, GREEN 43 pass (3 runs), build and load check OK, python unittests OK.

- 2026-10-02: Native review lineage `review-5a92897d9da43815` (medium, 1,168 lines, 4 paths) resumed after capture stopped at the 30-minute limit and completed **APPROVED, acknowledged, authority burned**.
  - R3-001 (reliability WARNING, test-suite concurrency): FIXED by installing the `console.warn` spy once per file via `beforeAll`/`afterAll`.
  - R3-002 (suggestion, misleading test name): FIXED by dispatching `mystery-writer`.
  - R3-003 (suggestion, unexercised 2 s write timeout): initially OPEN GAP; subsequently addressed by the post-code timeout seam and task-result hook test recorded below.
- 2026-10-02: Deploy complete: verifier mirrored, `secure-opencode` and `ai-proxy` restarted, and all checks passed.
- Advisory record (task T4, step `post-code`): advisor `advisor-testing`, model `opencode-go/kimi-k2.7-code`. Findings and resolutions:
  1. R3-001: the spy fix is correct only under Bun's default sequential intra-file execution. `describe.sequential` is undefined here while `describe.concurrent` exists, so the original hazard was largely theoretical; the `consoleCount` assertions in `describe("6. warning de-duplication")` are vulnerable only under `--concurrent`. Removed the failed outer `describe("routing guard", ...)` wrapper and left the inner suites/assertions intact.
  2. The file-log fix was partial: once-per-process reporting hides ongoing failures. Changed reporting to de-duplicate by resolved log path plus error code, so signature changes report again while identical repeats stay quiet; added an ENOTDIR failure-path test.
  3. R3-003: two workable timeout test options were identified. Used a configurable `SYSTEMATIC_ROUTING_GUARD_WRITE_TIMEOUT_MS` seam (default 2000 ms, clamped to at least 10 ms) and a test that verifies a never-resolving write chain is bounded by the configured timeout, with no marker created.
  4. Removed the leftover outer wrapper and the unreachable `catch` in `boxed`; the Promise race's work branch catches rejection and the timer branch resolves.
  This is advisory evidence only, never approval. The pre-code advice step was missed for this unit.
- Route/trigger evidence: `route: delegated`; specialist `general` (sandbox writer); trigger: secure ODD policy (every project mutation is delegated).
- The review lens confirmed the intended fixes are present: route-namespaced stage markers with legacy fallback, unique stage ids, three-ancestor inheritance with a visited set, and cycle/four-hop coverage.
- 2026-10-03: Silent-gate investigation outcome: hook registration was PROVEN by hand-run import (`default` is callable and `tool.execute.before` is present); `opencode --version 1.18.34` rules out a V1/V2 mismatch; `ACTIVE_TTL_MS` is 30 minutes, matching the docs. The contradiction remains unresolved: a warning was owed, but the file-log mtime proves `warn()` never ran. This unit adds load/registration/key-status observability and real loader assertions, including the deployed mirror and routing-guard suite.
- Route/trigger evidence: `route: delegated`; specialist `general`; trigger: secure ODD policy.

- 2026-10-03: Native review lineage `review-3c273e09d7f4107a` (high, 11 files / 191 lines; risk, resilience, readability, reliability) was **APPROVED**, then **acknowledged** with authority **burned**. The review produced evidence, not delivery authority. Advisory-only; no correction opened. All six findings are non-blocking:
  - `R3-pyc-tracked` — WARNING, `.gitignore:6`: generated `.pyc` files were staged while `*.pyc` is ignored; contradictory. Follow-up: unstage them (done in this unit).
  - `R3-timeout-flaky` — WARNING, `tests/routing-guard/routing-guard.test.ts:369-389`: wall-clock bounds in the hung-write timeout test can flake under load. Follow-up owed.
  - `R3-boxed-defensive` — SUGGESTION, guard plugin `290-300`: `boxed()` no longer wraps `Promise.race` in `try/finally`.
  - `R3-clamp-coverage` — SUGGESTION, guard plugin `227-231`: clamp inputs (negative/zero/NaN/non-numeric) are untested.
  - `R3-seam-exported` — SUGGESTION, guard plugin `224-226`: `setTaskWriteFileForTests` is exported from the production surface.
  - `R3-filelog-no-timeout` — SUGGESTION, guard plugin `552-572`: file-log append is not wrapped by `boxed()`; pre-existing.

- Advisory record (2026-10-03 unit, step `post-code`): advisor `advisor-integration`, model `opencode-go/deepseek-v4.1-flash`. Findings: (1) the verifier load check must invoke only the default factory or at most one named `*Plugin` export, not every function export; (2) the child Bun probe must set `WORKFLOW_HEALTH_CHECK_PROBE=1` to prevent verifier recursion/side effects; (3) factory exceptions from invalid `{}` input are non-fatal, while import failure or absence of any function export remains fatal; (4) the OpenCode 1.18.34 hook allowlist was incomplete and must include the documented hooks, with explicit version-drift notice; (5) split early import-only and post-mirror factory checks, skipping the early probe in `--recover-config-only`; (6) remove the hung-write test's brittle elapsed-time bounds and use a generous rejecting watchdog; (7) move key-status deduplication into factory scope, include session IDs, and persist module-import, registration and key-status diagnostics to the file log. Also confirmed the Astra plugin source should not carry a stray trailing blank line. This advice is evidence, never approval. **No pre-code advice entry exists for the 2026-10-03 unit; that step was skipped.**

## Post-code advisory (2026-10-03; after native review)

- Advisor: `advisor-integration`; model: `opencode-go/deepseek-v4.1-flash`; step: `post-code`.
- Findings: B2 — keep the factory-mode probe after all three plugin mirrors, including Astra; B3 — only the three canonical plugins make an unrecognized factory shape fatal, while third-party shapes are report-only and import failures remain fatal; B4, B5, C4, D4, F2, and F3 — advisory finding IDs retained, but their detailed descriptions were not present in the supplied evidence; B7 — isolate `HOME` and `SYSTEMATIC_ROUTING_GUARD_STATE_ROOT` for child probes; C2 — centralize duplicate routing-log append failure handling; D1 — restore the test's original `root` and clean temporary roots in `finally`.
- A1/process issue: the advisory ran **after** native review, contrary to `WORKFLOW.md:424`; this ordering violation is recorded, not normalized as acceptable.
- Resolved here: B2, B3, B7, C2, and D1. Remaining advice detail for B4, B5, C4, D4, F2, and F3 requires recovery from the original advisory record before those items can be considered settled.
- Confirmed incident evidence (owner report): the routing-guard log's final entry was `2026-10-02T15:26:46.613Z`, a `host_git_commit` refusal for session `ses_f63454890ffej5Y5gIUDN4HFKf`; there was no later entry for any session. The adapter key expired at approximately 15:55 that day, leaving approximately 17+ hours of owed warnings un-emitted. The guard is not running in the current service. The reported first-catch instrument is checking the key's `last_active` against its TTL before explaining silence.

## Status — second native review lineage (2026-10-03)

- Second lineage `review-6f4b75d709b92711` was high tier (9 files, 223 lines; correction budget 112) and started after first lineage `review-3c273e09d7f4107a` closed approved/acknowledged.
- Two eligibility problems were fixed before start:
  - `tests/__pycache__/*.pyc` were tracked despite `.gitignore` entries for `__pycache__/` and `*.pyc`. The earlier claim that these files were never tracked was wrong: the `git ls-files` used to support it ran inside the sandbox, a different checkout. Native finding `R3-pyc-tracked` correctly identified the issue; the files were removed in commit `0166043`.
  - `CLAUDE.md` was untracked and rewritten by another agent, so the untracked inventory could not be pinned between STATUS reporting it and the selection consuming it. Commit `0db4238` tracked the file, emptied the eligible set, and removed the selection step.
- All four lenses completed. Risk, resilience, and readability captured clean. Reliability returned `correction_required` with two findings. Direct reads—not the lens's diff-scoped evidence—verified both as false positives:
  - `R3-undeclared-log-failure-set` (BLOCKER) claimed `reportedFileLogFailures` was undeclared. It is declared at `global-config/plugins/systematic-routing-guard.ts:217` as `const reportedFileLogFailures = new Set<string>()`; the declaration predates the diff and was outside the lens's changed lines.
  - `R3-verifier-factory-check-removed` (CRITICAL) claimed the factory-mode check was gone. `check_plugin_loads` has two call sites: `verify-workflow.sh:260` with a `$plugin_mode` argument, and `verify-workflow.sh:3904` after the mirror.
- Lesson: **a lens shown only changed lines will manufacture absence claims about pre-existing declarations.** Absence claims need a stated search plus a positive control.
- A 45-line defensive correction was nevertheless applied and committed as `409b543` (stronger dedup test, local rejection handler, stricter factory mode). It hardened behavior; it did not fix real defects. The correction plan captured 45 of 112 lines.
- **BLOCKER:** the targeted validator repeatedly refused with `opencode_provider_role_result_refused (cause: validator_result_not_admissible)`; transport produced no capturable result. STATUS re-offers the identical provider task, but the contract requires a valid payload before resubmission and the prompt must be forwarded verbatim, so retrying unchanged is forbidden. The same lane also refused on 2026-09-29 (transport-binding mismatch, then connection resets).
- Upstream relation was investigated, not resolved. `v4.0.0` (published 2026-10-01; stable; provider contract still frozen at `1.2.0`) includes relevant-looking review changes: the OpenCode review plugin checks the PATH `gentle-ai` version before relaying and refuses on binary skew; refusals return one bounded reason code; negotiated STATUS returns a runnable native recovery command without caller-authored actor/reason/authorization. No notes name `validator_result_not_admissible`, so a published fix is **not verifiably established**. Installed build is **3.7**, predating v4.0.0. Per the residue protocol, an unverified fix plus deferred upgrade means **do not create or comment on an upstream issue** for this occurrence; state is preserved.
- Current state: correction committed; lineage remains stuck at `correction_required` with authority unconsumed; deploy is held because a due review blocks. `gentle-ai review abandon` may provide a clean exit, but is untested for this cause.

## Runtime investigation follow-up (2026-10-03)

- Captured service journal evidence: at 14:06:06 the routing-guard module printed `module imported`, with no subsequent `plugin registered` line; other plugin factories reported their normal loaded/registered output. At 14:08:09 `workflow-health-check` logged a failed verifier invocation, `bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh`, followed by `Cannot read directory "/home/james/": AccessDenied` and `47 pass / 0 fail`.
- This distinguishes module import from factory entry: the guard's factory begins with an awaited `logObservedLine`, while module import uses a fire-and-forget call with a catch. Add the bare first-statement discriminator `console.warn("[systematic-routing-guard] factory entered")`. If it prints after restart, the factory was entered and later work is suspect; if absent, OpenCode did not call the factory. Do not infer which outcome before observing the next service start.
- Standalone evidence is service-specific, not proof of service behavior: the deployed factory invoked through standalone `bun -e` returned all four expected hook keys. The service shows no registration line while other factories run.
- Health-check regression/fix: the plugin-load probe had overridden both `HOME` and `SYSTEMATIC_ROUTING_GUARD_STATE_ROOT` to the scratch directory. Keep only the state-root override so the child probe inherits the real `HOME`.
- Reproduction from a scratch HOME: `env HOME=/tmp/tmp.7DgTZ45KUD SYSTEMATIC_ROUTING_GUARD_STATE_ROOT=/tmp/tmp.7DgTZ45KUD WORKFLOW_VERIFY_PLUGIN_LOADS_ONLY=1 WORKFLOW_VERIFY_PLUGIN_LOAD_MODE=factory WORKFLOW_VERIFY_PLUGIN_LOAD_DIR=global-config/plugins bash verify-workflow.sh` completed with all three plugin factories recognized and no `Cannot read directory` error. `env HOME=/tmp/tmp.7DgTZ45KUD bun test tests/routing-guard` completed with 47 pass / 0 fail. The reported outer invocation is the health-check's `bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh`; these isolated reproductions do not identify an inner command that emits the access error. Its service-specific emitter remains unresolved rather than guessed.

## Runtime investigation — second restart (2026-10-03)

- Owner-reported service evidence from the second restart: at 14:45:13 the routing guard logged `module imported`, but no `factory entered` line; at 14:45:16 the reviewer relay and grep guard loaded; at 14:47:08 the health check failed while running the verifier and reported `Cannot read directory "/home/james/": AccessDenied`.
- The current evidence does **not** prove that module evaluation stopped before the default export: the import diagnostic is issued at module scope before that export, while the factory diagnostic can only run after OpenCode calls the exported factory. The owner-provided diagnosis (an import-time throw between those points) remains a hypothesis pending a module-completion signal.
- Added `module evaluated` immediately after the default export. Together, `module imported` and `module evaluated` bracket module evaluation; the pre-existing `factory entered` line separately distinguishes factory invocation. After restart, imported-without-evaluated supports a module-evaluation failure; both import signals without factory-entered points to loader/factory dispatch rather than an incomplete module. These are diagnostics, not proof of a specific cause.
- Module-scope filesystem/home audit: `global-config/plugins/systematic-routing-guard.ts:261` starts `logObservedLine`, which immediately attempts the console diagnostic and then asynchronously calls `appendRoutingLog` → `mkdir`/`appendFile` under `stateRoot()` (default `homedir()` unless the state-root environment override is set). These import-time log statements are the only top-level statements in the audited range that touch filesystem/home state. The module declarations, literal/regex/Set/Map initializers, and function bodies do not execute filesystem work at import. Line 261 is the pre-existing import-start signal; line 1087 is the new post-export completion signal.
- `/home/james/` denial candidates: `verify-workflow.sh:1475` and `:1832` call `fs.readdirSync(current, ...)` inside the Systematic-agent inventory walkers; their roots are the selected Systematic package's `agents` directory (`ACTIVE_ROOT/agents`), chosen from configured/cache package roots, not the home root itself. They could reach `/home/james/` only if that selected package-agent path were redirected to the home root (for example by abnormal configuration/symlinking); no such redirection is evidenced here. `tests/routing-guard/routing-guard.test.ts:13-14` calls `homedir()` only for the throw-on-real-HOME safety check and contains no directory listing or readdir; with an unset/real HOME it aborts before tests, while with the prescribed temporary HOME it does not target `/home/james/`. The service-specific emitter of the denial therefore remains unresolved; no cause is asserted.
- Digest verification/re-pin: `sha256sum verify-workflow.sh` returned `d2e2187106bf464bf735e045aa0ab354a83dccbc7975349e1b0c5630a9413775`; the existing `VERIFY_SCRIPT_SHA256` is identical, so no constant change was needed.

## Confirmed loader defect and corrective change (2026-10-03)

- The four function-valued exports in `global-config/plugins/systematic-routing-guard.ts` were `setTaskWriteFileForTests`, `stageMarkerNames`, `SystematicRoutingGuardPlugin`, and `default`. OpenCode treats exported functions as plugin factories; calling the helper `stageMarkerNames({})` fails because its required `routeStages` argument is undefined, so the plugin factory was never entered. `stageMarkerNames` was added as an export by commit `da10378` at 2026-10-02 11:55; the guard last worked at 15:26 that day.
- Control: `workflow-health-check.ts` exports only its factory and default, and its factory enters successfully.
- Fix: moved `stageMarkerNames`, `setTaskWriteFileForTests`, `READ_ONLY_SPECIALIST_PATTERNS`, `ROUTE_STAGES`, `RouteStage`, and the mutable test write seam into `global-config/plugins/lib/routing-guard-helpers.ts`. The top-level plugin now imports those helpers and exports only `SystematicRoutingGuardPlugin` and `default`. The verifier's `global-config/plugins/*.ts` / `*.js` scan is non-recursive, so the helper under `lib/` is not a plugin entrypoint.
- Verifier false-green: `check_plugin_loads` previously selected `default` or one named `*Plugin` factory but did not reject additional function-valued exports. It now fails for the three mirrored plugins when function exports exceed `default` plus at most one named `*Plugin`; other plugins remain report-only for this contract.
- Separate fault: the observed nono diagnostic (`validating nono profile… $ cargo install nono-cli … v0.79.0 … nono v0.73.0`, installed 0.74.0, `[nono] Session stopped.` at 2026-10-02 15:48 and 16:34) explains the `/home/james/` AccessDenied separately; it is not the routing-guard loader defect.
- Verification: `bash -n verify-workflow.sh` exited 0; isolated `bun test tests/routing-guard` reported 48 pass / 0 fail. Import and factory modes each reported `OK` for all three mirrored plugins. The routing guard's function-valued export names printed verbatim as:
  ```text
  SystematicRoutingGuardPlugin
  default
  ```
  `sha256sum verify-workflow.sh` and `VERIFY_SCRIPT_SHA256` both read `8ce44ef51d0b53c3d23cd6adbf0fe92a9f19048ff420628b81fd3f4b661181c5`.
- Reviewability receipt: 192 authored changed lines including the new helper (115 additions, 77 deletions); generated/binary path inventory: no changed generated or binary files. The sandbox already contained an unrelated untracked `ses_efd5e0419ffeSmSayI9Pay69az.bundle`; it is not part of this change. Authored patch byte count remains to be read from the complete exported candidate.

## Next step
Q27: owner decision on the advisor sandbox lifecycle gap, tracked in `docs/ADVISOR-HANDOFF.md`. Second-lineage deploy remains held pending a decision on the blocked review.
