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

## Second live smoke test findings and corrections (2026-10-18)

The second live `pm-odd` smoke test passed 4/8 checks and preserved the expected feature branch, branch-ref HEAD SHA, tracker last line, and class/route. It failed three checks:

1. **Higher-priority PM prompts still required tracker hashes.** Both `pm-odd` and `pm-systematic` in `global-config/opencode.json` required comparing `tracker_sha256`, contradicting the spec. Replaced that obligation in both prompts with the read-based anchor and explicit hash-duty suspension. Updated the orchestrator overlay and regenerated embedded prompt so the orchestrator carries the same anchor contract.
2. **Byte count was not observable.** `read` exposes numbered lines, not file-size metadata, and truncates long lines. Replaced byte/character count with exact line count and kept exact last-line text plus feature-branch HEAD SHA. The revised anchor can flag stale/truncated working-tree text only when line count or last line differs, and a wrong branch-ref SHA. It cannot detect whitespace/semantic changes preserving those observations or long-line truncation that leaves them unchanged; it is not a cryptographic witness.
3. **Committed-versus-working-tree state was unproven.** The PM read the working-tree tracker path and could not establish content equality with the commit. The contract now states this limitation directly: the anchor checks readable working-tree text and the feature-branch ref, but does not prove the tracker contents are committed or equal the committed blob.

**Runtime boundary:** PM runtime behavior remains HOST-ONLY. The falsifier is a live `pm-odd` dispatch whose result envelope records the anchor comparison (and the specified working-tree limitation).

## Checks
- `python3 -m json.tool global-config/opencode.json`: PASS (exit 0).
- `python3 -m unittest tests.test_pm_handoff_spec -v`: PASS, 8/8.
- `python3 -m unittest tests.test_pm_layer_prompts -v`: PASS, 10/10.
- `python3 -m unittest tests.test_orchestrator_prompt_source -v`: PASS, 27/27. Three-way prompt equality passed: assembler output equals the embedded `gentle-orchestrator` prompt; SHA-256 equals the test constant and normative-ledger digest. Prompt SHA-256 `74838e16cf689f8c3f862dc56d3d9dc22f925dab8b8dcabc4d849bf96a2dd2ac`; 55,246 bytes / 414 lines; generated embedded delta +699 bytes / +0 lines.
- `python3 -m unittest discover -s tests`: 210 tests; 199 passed, 10 errored because sandbox denied `node` execution in `test_gemini_advisor_route`, 1 skipped. No failures.
- `bash -n verify-workflow.sh`: PASS (exit 0).
- Verifier `read_verify_script_pin` regex: PASS; plugin pin literal and `verify-workflow.sh` SHA-256 both `e48ea733ae1097677ad76729f3d1e8cc1d7b56da78533ae9f35f0d47528bfb9d`. `verify-workflow.sh` was unchanged, so no pin value change was needed.
- Positive controls: the modified spec-anchor assertion failed when the byte-count mechanism was absent; the PM prompt tests failed against both old hash-mandating prompts; and the orchestrator-anchor source test failed before the overlay/embed regeneration. The final targeted tests pass.

## Progress
- [x] Read the complete current `docs/specs/pm-handoff.md` before editing.
- [x] Replace the hash obligation in both PM prompts and regenerate the orchestrator prompt source/embed/ledger chain.
- [x] Replace the byte-count anchor with exact line count and narrow the committed-state claim.
- [ ] Apply the sandbox result only after `sandbox_finish` and report whether apply succeeded.
