# Q85 — deterministic PM unit-start anchor

## Objective
Replace the PM's unusable unit-start tracker/mirror hash duties with a deterministic read-only anchor while explicitly suspending those hash duties until the deterministic host tool lands.

## Evidence
A live `pm-odd` smoke test on 2026-10-17 returned `BLOCKED` with `MISSING_REQUIRED_UNIT_START_SNAPSHOT` and `HASHING_SURFACE_UNAVAILABLE`. The PM observed that `docs/specs/pm-handoff.md:123` suspends the mirror write and verification, but the brief field list, the readback clause and the envelope clause STILL require the supplied hashes and the PM's own tracker hash comparison — so the suspension does not cover this case. The PM has NEITHER a shell NOR a deterministic hashing tool, so `tracker_sha256` is unachievable regardless of any suspension.

## Scope
- `docs/specs/pm-handoff.md`
- `tests/test_pm_handoff_spec.py`
- `odd/tasks/q85-unit-start-anchor.md`
- `docs/TODO.md`
- `ROUTER-LOG.md`

## Acceptance criteria
- Define the anchor as tracker byte (or character) count, exact literal last-line text, and unit feature-branch `HEAD` commit SHA, compared by the PM using only `read`.
- Explain its coverage and limitation: catches stale/truncated/wrong-commit tracker; does not catch whitespace-only or semantically divergent changes; not a cryptographic witness.
- Replace hash duties in brief/readback/envelope; explicitly suspend them until deterministic host tool lands, which is the return trigger.
- Keep deterministic host tool as mirror write/verification owner and metadata worker as repository-file owner.
- Test anchor, suspension/trigger, envelope observations and named mismatch reason; retain prior controls and add a PositiveControl that fails when the anchor definition is mutated.
- Run focused and full Python suites and demonstrate PositiveControl non-vacuity.

## Checks
- `python3 -m unittest tests.test_pm_handoff_spec -v`: PASS, 8 tests.
- Anchor PositiveControl non-vacuity: temporarily changed its mutation to a nonexistent phrase; the test failed with `AssertionError: AssertionError not raised`; restored the mutation and the test passed.
- `python3 -m unittest discover -s tests`: 209 tests ran; 198 passed, 10 errored, 1 skipped. All 10 errors are existing `test_gemini_advisor_route` subprocess attempts to launch `node`, denied with `PermissionError: [Errno 13] Permission denied: 'node'`.
- `git diff --check`: PASS.

## Runtime boundary
The PM's RUNTIME behaviour is HOST-ONLY. The falsifier is a live `pm-odd` dispatch whose envelope records the anchor comparison.

## Progress
- [x] Read the complete current `docs/specs/pm-handoff.md` before editing.
- [x] Implement and verify the contract and durable tracking updates.
- [ ] Apply the sandbox result only after `sandbox_finish` and report whether apply succeeded.
