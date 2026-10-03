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

## Next step
Q27: owner decision on the advisor sandbox lifecycle gap, tracked in `docs/ADVISOR-HANDOFF.md`.
