# Change-set tool (Q36)

## Objective
Build the non-destructive apply/revert tool that delivers the gentle-ai v4 (and later OpenCode V2)
upgrade changes to files git cannot reach: the live `~/.config/opencode`, `~/.claude`, and
gentle-ai-managed blocks. It must never overwrite drift.

## Why
Queue Q36, owner decisions 2026-10-01/02 (`docs/PLAN.md` "Upgrade change set" and "One source of
truth, stacked upgrade branches"). Repo-tracked changes ride git branches; this tool covers the
rest.

## Scope
- `docs/specs/changeset-tool.md`: the contract (written by the strong model).
- `tests/test_changeset.py`: the acceptance suite (written by the strong model, RED until built).
- `scripts/changeset.py`: the implementation (delegated to a cheaper writer against the tests).
- No real change set content yet: v4 operations are authored at upgrade time (build late).

## Constraints
- Python 3 stdlib only; one file; no network.
- Never delete: removals move into the journal directory.
- Bytes outside an edited value or block stay identical.
- Forward-compatible: nothing OpenCode-version specific.
- No AI attribution in commits.

## TDD
Mode: on for this unit, by owner strategy (spec and tests first, implementation after).
Runner: `python3 -m unittest tests/test_changeset.py -v`.

## Tasks
- [x] T1 — Spec `docs/specs/changeset-tool.md`. Route: inline (strong model, by owner strategy).
- [x] T2 — Acceptance tests `tests/test_changeset.py`; observe RED (script absent). Route: inline
  (strong model).
- [ ] T3 — Advice record on the spec (mandate), then implement `scripts/changeset.py` to GREEN.
  Route: delegated writer (cheaper model).
- [ ] T4 — Native review; record outcome.

## Acceptance criteria
1. Every behaviour in the spec has at least one test.
2. All tests pass against the implementation, with no test edits except for documented spec
   errors.
3. Native review approved.

## Progress
- 2026-10-02: branch `feat/changeset-tool` from `fix/auto-update-partial-install` (`ef0d75c`).

- 2026-10-02: T1 done. `docs/specs/changeset-tool.md` (v1) covers ops, evaluation, byte
  preservation, atomic writes, lock, write-ahead journal and seal, resume, revert with drift
  preservation, report, exit codes, dry run, verify gate, path safety and status.
- 2026-10-02: T2 done. `tests/test_changeset.py` has 50 tests. RED observed: 50 failures with the
  script absent. The first RED run showed 6 vacuous passes (Python's own exit 2 for a missing
  script matched the expected conflict exit); fixed by requiring a JSON report on every CLI call
  (spec section 7). Second run: 0 passes.

- 2026-10-02: native review (4 lenses, high risk, range `9424d69..0e65178`) APPROVED and
  acknowledged, authority burned. 8 advisory findings; folded in before implementation:
  - R4-001: the lock becomes `fcntl.flock`, removing the stale-lock race; tests now hold a real
    flock from a separate process.
  - R4-002: reverting after a resume is specified.
  - R2-002: the outcome vocabulary, including `unknown`, is listed.
  - R3: stronger dry-run assertion; new tests for pointer escapes, a missing parent and multi-line
    indentation; a conflict-only revert test.
  - R2-001: missing blank line before Q30 restored.
  Not acted on: R2-003, tracker wording (the tracker is updated as status changes). Suite: 54
  tests, all RED, 0 vacuous passes.

## Next step
T3: advice record on the spec (owner TUI dispatch, Q51 open), then a delegated implementation to
GREEN.
