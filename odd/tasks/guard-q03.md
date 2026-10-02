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
- [ ] T3 — Advice record on the design (owner TUI dispatch; Q51 open).
- [ ] T4 — Implement to GREEN. Route: delegated writer.
- [ ] T5 — Native review; verifier mirror; owner restart; verifier pass.

## Progress
- 2026-10-02: the map of the guard (read-only explorer) established the testability constraints:
  hooks are fire-and-forget, `homedir()` is fixed at import, and bun's `homedir()` ignores
  `HOME` changes at runtime. Hence the state-root seam.
- 2026-10-02: RED. The first run had 9 vacuous passes (absence assertions against the wrong
  root); fixed with a positive-control probe in every absence test. Final: 37 tests, 0 pass,
  37 fail.

## Next step
T3.
