# Q66 — Assembler hardening — pre-code advice record

Two pre-code advisories were taken before any edit. Both are recorded below in English with every `path:line` reference and every recommendation preserved.

## advisor-integration-pre (2026-10-11)

### Per-finding fix table

| Finding | Fix | Regenerates the prompt? |
|---|---|---|
| 1 `R3-ASSEMBLER-FAILURE-PATHS-UNTESTED` (`assemble-orchestrator-prompt.py:253-260`) | Add the five failure-path tests | NO |
| 2 `R3-ASSEMBLER-ATTR-PARSER-FRAGILE` (`:54-63`) | Harden `parse_attrs`: per-key uniqueness, reject unknown/duplicate keys | NO |
| 3 `R3-ASSEMBLER-ORDERING-HAZARD-UNGUARDED` (`:191-207`) | Guard overlapping-region ordering in `splice` | NO |
| 4 `R4-ATTRPARSE-001` (`:54-63`) | Same defect as finding 2 — fixed once | NO |
| 5 `R4-EXITCODE-001` (`:258-264`) | Catch `OSError` at `:258`, return 2 | NO |
| 6 `R4-MARKER-COUPLING-001` (`:142-154`) | Move the marker pair into ONE base section | YES |

Findings 2 and 4 are ONE defect located at `parse_attrs:54-63`; the second lens counted the same code twice. Fix it once and both findings are closed.

Findings 1 and 6 do NOT overlap: finding 1 is missing coverage of the assembler's error branches; finding 6 is a structural split inside `base.md` (a prompt-content problem, not an assembler-code problem).

### Exit-code decision

Catch `OSError` alongside `AssemblyError` at `:258` and return 2. DO NOT rewrite the docstring to say 1. Callers today do not distinguish: `tests/test_orchestrator_prompt_source.py:347,:359` use `assertNotEqual(rc, 0)`, and `verify-workflow.sh:2956-2959` fails on any thrown error without inspecting the code. But the CLI contract is an interface, and a missing input file IS a loud failure — the docstring at `:11-12` ("Every block fails loudly (exit 2)") is the contract to honour, not to amend.

### Finding 6 route: reject assembler-side validation

REJECT the assembler-side HTML-comment-pair validation route for finding 6. It couples the assembler to prompt content and is a brittle special case that would need updating every time the prompt's prose changes. The correct fix is structural: move the `<!-- gentle-ai:opencode-desktop-delegation-progress -->` pairing so both markers live entirely inside one base section.

### T2 regeneration chain

When T2 changes the assembled bytes, all of the following must be updated together:

- `global-config/opencode.json:590` (the embedded prompt).
- `tests/test_orchestrator_prompt_source.py:28` (`CURRENT_PROMPT_SHA256`).
- `global-config/prompts/gentle-orchestrator/normative-ledger.md:5` (the sha + any line citations).
- Any overlay `supersedes` sha256 affected by a `base.md` section edit — e.g. `overlay.md:62`.
- `verify-workflow.sh:2982-2998` hard-coded prompt-content assertions.

`VERIFY_SCRIPT_SHA256` changes only when `verify-workflow.sh` itself is edited; it is not part of the prompt sha chain, but the content assertions in the verifier are.

### Byte-change discipline

Fixes 1/2/3/5 leave the assembled sha256 identical — compare the assembler output before and after T1 against the pin to prove it. Do not mix the two commits without regenerating: shipping the T2 prompt change without updating the pin fails the verifier's `ORCHESTRATOR_PROMPT_ASSEMBLER_DRIFT` check at `verify-workflow.sh:2964-2965`.

### Branch note

The branch is `feat/gentle-ai-v4`. A sandbox advisor observed `work` as the branch — that was its own synthetic baseline, not the host checkout.

## advisor-testing-pre (2026-10-11)

### Five failure-path tests with fixtures, stable substrings, and positive controls

Each failure path is exercised through `--base`/`--overlay` overrides into a `tempfile.TemporaryDirectory()`, with a fixture that differs from a passing control by exactly the property under test and reaches the same `parse_overlay` path:

1. Nested markers — fixture with a nested `SECURE:BEGIN`; stable stderr substring `nested SECURE:BEGIN`.
2. Unknown kind — fixture with an unrecognised kind; stable stderr substring `kind must be one of`.
3. Empty body — fixture with an empty body; stable stderr substring `empty body`.
4. Duplicate ids — fixture with two blocks sharing an id; stable stderr substring `ids must be unique`.
5. Malformed marker — fixture with a malformed `SECURE` marker; stable stderr substring `malformed SECURE marker`.

### Anti-vacuity rule

Every negative test must have a positive control that differs by exactly the property under test and reaches the same code path (`parse_overlay` for the five failure paths). A test that would pass with the failure path deleted is vacuous and does not count as coverage.

### Assertion shape

Use `assertEqual(result.returncode, 2, ...)` plus a stderr substring assertion. Do NOT assert the full formatted message, the exception class, or a literal line number — those freeze cosmetics and break on legitimate message edits.

### Exit-code tightening and the missing-file test

Replace the three `assertNotEqual(rc, 0)` sites at `tests/test_orchestrator_prompt_source.py:347,:359,:371` with `assertEqual(rc, 2)`. Add a missing-file test asserting `rc == 2` plus the `FAILED` prefix (`assemble-orchestrator-prompt.py:259`) as the control that the `AssemblyError` path was taken rather than Python's default traceback (which would exit 1).

### R3 ordering RED test

Add `test_overlapping_regions_preserve_file_order`: base with `### A` / `### B` / `### C`; overlay performing `add after="### A"` → `remove supersedes="### B"` → `add after="### A"`; assert `index(Added1) < index(Added2)`. The bug is that a cursor strictly before the spliced region never rebases. The positive control is the existing `test_shared_anchor_adds_insert_in_file_order` at `:285-308`. Frame the assertion as the PROPERTY (file order preserved), not as cursor internals. The test must be RED before the fix and GREEN after.

### R4 partial-drop test

The existing count-based balance check at `:326-333` is vacuous for this case: a body carrying only the BEGIN marker and body but not the END leaves counts that are 0 == 0, or a re-added pair still balances. Add a partial-drop test: a `replace` body containing the BEGIN marker and body but not the END → assert the END is absent while the BEGIN is present. Positive control: a body that carries both, with the base's pair staying intact.

### What must NOT be weakened

- The `CURRENT_PROMPT_SHA256` pin.
- The residue scan at `assemble-orchestrator-prompt.py:195-206` with its positive control at `:317-323`.
- `test_replace_remove_declarations_carry_verifiable_hashes`.
- The `upstream/` render test.
- `REQUIRED_IDS` / `SIGNATURES`.

### Blast-radius rule and subtle trap

All new tests use temp dirs and `--base`/`--overlay` overrides, so the real assembled bytes cannot move. Subtle trap: keep new temp bases free of `<!-- SECURE:` substrings in body content, or the malformed-marker check trips before the intended failure does.
