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
- [ ] T5 — Native review; verifier mirror; owner restart; verifier pass.

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

## Next step
T5: native review; verifier mirror; owner restart; verifier pass.
