# Q79 — Pre-code advice record

## advisor-integration-pre (2026-10-17)

- **BLOCKER — Q77 invariant reversal and live assertion.** Q77 explicitly preserved metadata-worker mirror-write ownership (`docs/specs/pm-handoff.md:123`), and `tests/test_pm_handoff_spec.py:60-63` pins it as a live assertion. The owner now decides a DETERMINISTIC host tool owns mirror write and verify. Explicitly retract the Q77 decision in `CLAIM-RETRACTIONS.md`; update the test to pin the new owner. Do not silently reverse the invariant.
- **BLOCKER — self-contradicting spec.** `docs/specs/pm-handoff.md:7` and `:28` deny the PM the mirror body / prescribe hash readback, while `:123` requires the metadata worker to mirror the body and read back both stores. Correct the ownership and clarify what a successful handoff can claim.
- **BLOCKER — `## Key Learnings` chain.** The orchestrator overlay at `global-config/prompts/gentle-orchestrator/overlay.md:155,156,164,189` contains the stale ownership/readback chain. Correct the chain end-to-end; changing only one sentence leaves contradictory instructions.
- **BLOCKER — stale memory policy.** `global-config/systematic.jsonc:53,115` and verifier checks `verify-workflow.sh:1733-1752` and `:2176-2187` encode stale `systematicMemoryPolicy` / grants. Align the source policy and verifier checks without weakening enforcement.
- **BLOCKER — atomic 7-step prompt regeneration.** The prompt regeneration chain has seven dependent steps and a partial commit goes red. Treat all seven as one atomic delivery; do not leave assembled, embedded, hashed, or test-expected prompt representations out of sync.
- **F6 — residue guard gap.** `tests/test_orchestrator_prompt_source.py:62` `FORBIDDEN_RESIDUE` lacks `ctx_note`. Add it with a positive control proving the guard catches that residue.
- **F13 — missing verifier parity gate.** `verify-workflow.sh` never checks the embedded prompt against assembler output; currently only the test constant gates it. Add a verifier check for embedded-prompt/assembler equality and test the failure path.
- **F12 — `explore` grant.** Resolve the stale grant at `global-config/opencode.json:51` consistently with the new deterministic ownership and memory policy.
- **F19 — Q77 U2 incomplete.** U2 updated the PM prompts, but did not update the orchestrator overlay, `WORKFLOW.md`, or `global-config/skills/workflow-odd-secure/references/odd-and-review.md`. Complete all three surfaces and verify the full chain.
- **F2 — `metadata_work_unit` consequence.** Explicitly decide what happens to the `metadata_work_unit` envelope field when the metadata worker no longer owns the mirror write. Update its schema/meaning and tests; do not leave a field that implies work the actor cannot perform.

**What must NOT be weakened:** preserve the independent hash check; BLOCKED-on-divergence semantics; per-prompt needles and the cross-agent contamination control; the three-way match; the 6,000-character PM cap; and every existing positive control. The host tool's deterministic write/verify responsibility does not justify weakening PM-side integrity checks, prompt-source parity, or failure detection.

**HOST-ONLY falsifier:** repository tests cannot prove that the live deterministic host tool performs and verifies a mirror write or correctly detects a live divergent store. Once the tool exists, run a live synthetic divergent tracker/mirror case and confirm it reports divergence without claiming successful write/verify. Until then, state that the write is not performed and that live verification is pending; never present static tests as runtime evidence.

## advisor-testing-pre (2026-10-17)

- **BLOCKER — Q77 ownership invariant must be reversed explicitly.** `docs/specs/pm-handoff.md:123` and `tests/test_pm_handoff_spec.py:60-63` presently assign and pin mirror-write ownership to the metadata worker. The owner decision is that a DETERMINISTIC host tool owns write+verify. Add the `CLAIM-RETRACTIONS.md` record and change the test to assert the new contract with a positive control for the former ownership.
- **BLOCKER — contradictory specification.** `docs/specs/pm-handoff.md:7,28,123` assigns mutually incompatible actors/capabilities. The spec test should detect a regression to that contradiction, not merely check for expected new words.
- **BLOCKER — stale `## Key Learnings` chain.** `global-config/prompts/gentle-orchestrator/overlay.md:155,156,164,189` has multiple coupled instructions. Add precise per-surface assertions so a stale clause cannot survive after another clause is corrected.
- **BLOCKER — derived memory-policy drift.** Test both `global-config/systematic.jsonc:53,115` and verifier policy at `verify-workflow.sh:1733-1752` and `:2176-2187`; ensure `systematicMemoryPolicy` and its verifier expectations agree and include positive controls for stale/incorrect policy.
- **BLOCKER — the seven-step regeneration chain is atomic.** Exercise all seven steps and the resulting assembler, embedded prompt, digest, and expected test value together. A partial commit goes red; do not split dependent generated representations into separately accepted commits.
- **F6:** add `ctx_note` to `FORBIDDEN_RESIDUE` at `tests/test_orchestrator_prompt_source.py:62` and prove the residue is detected by a positive control.
- **F13:** add verifier coverage for embedded prompt equality with assembler output. A test-only constant is currently the only gate; prove the verifier fails when the embedded content diverges.
- **F12:** resolve `global-config/opencode.json:51` (`explore` grant), with a positive control detecting reintroduction of the stale grant.
- **F19:** test and correct Q77 U2 omissions: the PM prompts changed, but the orchestrator overlay, `WORKFLOW.md`, and `global-config/skills/workflow-odd-secure/references/odd-and-review.md` did not.
- **F2:** settle and test the consequence for the `metadata_work_unit` envelope field; its semantics must not claim the metadata worker performed deterministic write+verify.

**What must NOT be weakened:** the independent hash check; BLOCKED-on-divergence semantics; per-prompt needles and cross-agent contamination control; the three-way match; the 6,000-character PM cap; every existing positive control. Keep tests individual-prompt scoped so another agent's needle cannot satisfy a missing needle, and retain explicit mutation/failure controls rather than vacuous string-presence checks.

**HOST-ONLY falsifier:** only a live synthetic divergent tracker/mirror operation against the deterministic host tool can establish runtime divergence detection and write/verify behavior. Static repository tests cannot prove that runtime path. Before tool availability, the accurate state is that the mirror write is not performed and live falsification remains pending; do not imply a successful readback.
