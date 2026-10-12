# Q66 — Assembler hardening

**Feature:** gentle-ai v4 upgrade / queue Q66 (harden the orchestrator prompt assembler).
**Task ID:** `q66-assembler-hardening` (stable).
**Class:** global-tooling-change.
**Route:** `workflow-odd-secure` (delegated).
**Unit status:** T0–T2 DONE-AT-SOURCE (Q66 source complete; T2 committed and reviewed).
**Model:** cloud `opencode-go/deepseek-v4.1-flash` (owner decision 2026-10-07).
**Target:** `global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py`.

## Objective

Close the six review findings against the prompt assembler and pin its error/exit contract with non-vacuous tests, WITHOUT changing the assembled prompt bytes except where a finding structurally requires it.

## Problem

`docs/TODO.md:1130-1135`; findings recorded at `odd/tasks/q31-agent-allocation.md:441-446`. All six are still present on HEAD:

1. `R3-ASSEMBLER-FAILURE-PATHS-UNTESTED` WARNING (`:253-260`) — the five loud-failure paths (nested markers, unknown kind, empty body, duplicate ids, malformed markers) are exercised only by code, never asserted.
2. `R3-ASSEMBLER-ATTR-PARSER-FRAGILE` SUGGESTION (`:54-63`) — `parse_attrs` slices raw text to the next recognised `key=` with no per-key uniqueness/validation.
3. `R3-ASSEMBLER-ORDERING-HAZARD-UNGUARDED` SUGGESTION (`:191-207`) — `splice`'s cursor-shift handles splice displacement but overlapping-region ordering is unguarded.
4. `R4-ATTRPARSE-001` SUGGESTION (`:54-63`) — THE SAME defect as (2), counted twice by a second lens.
5. `R4-EXITCODE-001` SUGGESTION (`:258-264`) — `main()` catches only `AssemblyError`, so a missing `--base`/`--overlay` raises `FileNotFoundError` → traceback and exit 1, contradicting the docstring "Every block fails loudly (exit 2)" (`:11-12`), and the tests' `assertNotEqual(rc, 0)` (`:347,:359,:371`) cannot distinguish 1 from 2.
6. `R4-MARKER-COUPLING-001` WARNING (`:142-154`) — the `<!-- gentle-ai:opencode-desktop-delegation-progress -->` pair is split across a GUARDED and an UNGUARDED base section (opening marker is the tail of `#### Cost and Context Balance`, `base.md:162`; closing marker sits inside `#### Delegation Visibility`, `base.md:175`), so a replace/remove of either section splits the pair; only `tests/test_orchestrator_prompt_source.py:326-333` guards BALANCE, not pairing.

## Scope

In scope: T1 the assembler-only hardening; T2 the marker-coupling fix and its regeneration chain. Out of scope: the assembler's CLI surface beyond the exit-code contract; `base.md`/`overlay.md` prose other than the marker move; Q34/Q36.

## Constraints

- The branch is `feat/gentle-ai-v4` (the host confirms; a sandbox advisor seeing `work` was reporting its own synthetic baseline).
- T1 MUST NOT change the assembled prompt bytes — the assembled sha256 is `cece24ff93db6155f8800dca56bc8f517d9b5a0accbdf1801e21c7d4324c2155`, pinned at `tests/test_orchestrator_prompt_source.py:28` and carried in `global-config/opencode.json:590`.
- T2 DOES change bytes and therefore must update, in the same commit, `global-config/opencode.json` (the embedded prompt), `CURRENT_PROMPT_SHA256`, `global-config/prompts/gentle-orchestrator/normative-ledger.md` (the sha + any line citations), any overlay `supersedes` sha256 affected by a `base.md` section edit, and `verify-workflow.sh`'s hard-coded prompt-content assertions — and therefore re-pin `VERIFY_SCRIPT_SHA256` LAST.
- The existing sha pin, the residue scan (`:195-206`) and its positive control (`:317-323`) must NOT be weakened.
- New tests MUST use `--base`/`--overlay` overrides into `tempfile.TemporaryDirectory()` so they cannot perturb the real assembled bytes.
- `bash -n` is NOT evidence; never commit; never switch branches.

## Acceptance criteria

- All six findings closed or explicitly accounted.
- The five failure paths are asserted with `rc == 2` and a stable stderr substring (not the full message).
- The missing-file path exits 2 with the `FAILED` prefix.
- the ordering property test passes and the guard is in place — the "RED before the fix" requirement was CORRECTED during T1 because the hazard is LATENT: it does not reproduce (see T1 Progress and the T1 advisories).
- The marker pair lives entirely inside one section.
- The assembled prompt is regenerated and its sha pin, ledger and the verifier's content assertions agree.
- No test is vacuous.
- The routing-guard and python suites stay green.

## Authorized scope

- T1: `global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py`, `tests/test_orchestrator_prompt_source.py`.
- T2: those plus `global-config/prompts/gentle-orchestrator/base.md`, `global-config/prompts/gentle-orchestrator/overlay.md` (only if an affected `supersedes` must be recomputed), `global-config/opencode.json` (the embedded prompt only), `global-config/prompts/gentle-orchestrator/normative-ledger.md`, `verify-workflow.sh` + the `VERIFY_SCRIPT_SHA256` pin in `global-config/plugins/workflow-health-check.ts`. Plus this tracker, the advice record, `ROUTER-LOG.md`. No deployment.

## Checks

- `python3 -m unittest tests.test_orchestrator_prompt_source -v`
- The assembler run before/after T1 compared by sha256 against the pin (must be identical).
- In T2 the regenerated sha must equal the updated pin.
- `HOME="$(mktemp -d)" bun test tests/routing-guard`
- `python3 -m unittest discover -s tests`
- For T2 the digest pin equals `sha256sum verify-workflow.sh`.

## Tasks

- [x] T1 — assembler-only hardening: fix the exit-code contract (catch `OSError` → 2), harden `parse_attrs` (per-key uniqueness, reject unknown/duplicate keys), guard overlapping-region ordering, and ADD the five failure-path tests plus the missing-file exit-2 test; tighten the three `assertNotEqual(rc, 0)` sites to `assertEqual(rc, 2)`. MUST leave the assembled bytes unchanged.
- [x] T2 — marker coupling: move the `opencode-desktop-delegation-progress` pair into ONE base section, then run the regeneration chain (opencode.json, `CURRENT_PROMPT_SHA256`, normative-ledger.md, affected overlay `supersedes`, verify-workflow.sh content assertions) and re-pin `VERIFY_SCRIPT_SHA256` LAST.

## Progress

- 2026-10-11: T0 — tracker and advice record created from two pre-code advisories; no source edit yet. Route: delegated.
- 2026-10-11: T1 committed `61f85e4` (2 files, +221/−7; authored 228 lines). Fixes: (1) the exit-code contract — `main()` now catches `(AssemblyError, OSError)` and still returns 2, so a missing `--base`/`--overlay` no longer escapes as a traceback with exit 1 against the docstring's documented exit 2 (`:11-12`); (2) `parse_attrs` hardened with an explicit `KNOWN_ATTRS` allowlist that rejects unknown and duplicate keys; (3) the `splice`/add ordering guard `position = max(position, section["end"])` plus explanatory cursor comments; (4) tests — the five failure-path tests (nested BEGIN, unknown kind, empty body, duplicate ids, malformed marker) each asserting `assertEqual(rc, 2)` plus a stable stderr SUBSTRING and each carrying a one-edit-away positive control through the same `parse_overlay` path; a missing-input-file test asserting `rc == 2` plus the `FAILED` prefix as the control that the handled path was taken; the property test `test_overlapping_regions_preserve_file_order`; and the R4 partial-drop guardrail test `test_replace_body_carrying_half_a_marker_pair_drops_the_other_half`. The three loose `assertNotEqual(rc, 0)` sites were tightened to `assertEqual(rc, 2, result.stderr)`.
- 2026-10-11: T1 byte invariant OBSERVED: the assembled prompt is IDENTICAL before and after (52,332 bytes, 402 lines, sha256 `cece24ff93db6155f8800dca56bc8f517d9b5a0accbdf1801e21c7d4324c2155`), equal to `CURRENT_PROMPT_SHA256` (`tests/test_orchestrator_prompt_source.py:28`). `python3 -m unittest tests.test_orchestrator_prompt_source -v` 11 → 19 tests, `OK`; `python3 -m unittest discover -s tests` 110 `OK`; routing-guard 96/0.
- 2026-10-11: T1 HONEST DEVIATION — finding 3's "RED before the fix" could NOT be produced and was NOT fabricated. The worker brute-forced the assembler's topology space in three sweeps (per-anchor × target × kind × section-order × headed/headingless; then 0/1/2 intervening ops over {add,rep,rem}×{A,B,C}; then anchor==target with heading-preserving replace) and found ZERO ordering reversals; the exact prescribed scenario printed `ordered=True` on UNMODIFIED HEAD. Root cause: a cursor set after an `add` is always at/after the anchor's recomputed section end, so the branch named in the brief never fires. `R3-ASSEMBLER-ORDERING-HAZARD-UNGUARDED` was therefore a LATENT structural hazard, not a demonstrated bug; the guard is a structural close and a no-op for every constructible case tested, and the property test is a regression guard rather than a RED-to-GREEN fix.
- 2026-10-11: T1 native review: lineage `review-2762b6b8ca261f0c`; tier high; 2 files / 228 lines; four lenses (readability and reliability each needed a re-dispatch after a relay concurrency refusal and a relay deadline expiry); outcome **approved** and **acknowledged**; `authority: burned`; consumed revision `sha256:4e63f4d0…`.
- 2026-10-11: T2 committed `9d85764` (7 files, +126/−30; authored 154 lines excluding the regenerated prompt). Job 1 — the parser regression fixed: `parse_attrs` is now a key-position state machine (`ATTR_NAME_RE` + `HEADING_VALUE_ATTRS` + `KNOWN_ATTR_KEY_RE`), so a heading value containing `=` and ` X=` sequences parses intact (`after=### Foo=Bar` → rc 0, value preserved), while an unknown key still exits 2 (`unknown SECURE:BEGIN attribute`) and a duplicate still exits 2 (`duplicate SECURE:BEGIN attribute`), each now covered by a test with a one-edit-away positive control. Job 2 — the marker pair moved so BOTH halves live inside `#### Delegation Visibility (OpenCode Desktop)`; a `remove` of that section now leaves `0 open / 0 close` (no silent half-drop) while a `remove` of `Cost and Context Balance` leaves the pair intact `1/1`. Job 3 — the regeneration chain ran: assembled sha256 `cece24ff…` (52,332 B / 402 lines) → `c90727b3fc99ed1de2ff073685b435d58e6379668d92b3cad6644ea125d7b360` (52,333 B / 403 lines, +1 byte / +1 line), with a THREE-WAY MATCH (assembler output == `CURRENT_PROMPT_SHA256` == the embedded `opencode.json` prompt); the overlay `user:always-delegate-cost-context` `supersedes` recomputed `ed7c0cab…` → `42802342…` because its body no longer re-emits the opener half; the ledger updated to the new sha and line count. `verify-workflow.sh` was NOT edited, so NO re-pin was required.
- 2026-10-11: T2 SCOPE OVERRIDE (flagged by the worker; recorded here as a carry-forward). `base.md` is a BYTE-EXACT RENDER of `global-config/prompts/gentle-orchestrator/upstream/orchestrator.template.md`, enforced by `test_base_renders_upstream_sources_without_placeholders`, and `base.md`'s own header says it must never be hand-edited. The marker pair lives in the TEMPLATE, so Job 2 could not be done in `base.md` alone without breaking the render test. The worker edited the VENDORED TEMPLATE (outside the unit's authorized path list), preserved the upstream pins, and recorded a `local patch (Q66 T2)` note in `base.md`'s header. CARRY-FORWARD HAZARD: a future upstream re-render would clobber that local patch and re-split the pair; the template edit must be reapplied (or upstreamed) at each `gentle-ai sync`/re-render.
- 2026-10-11: T2 verification (observed): `python3 -m unittest tests.test_orchestrator_prompt_source -v` 19 → 22 tests `OK`; `python3 -m unittest discover -s tests` 110 → 113 `OK`; routing-guard 96/0.
- 2026-10-11: T2 native review: lineage `review-d31a1e3495a484a3`; tier high; 7 files / 156 lines; four lenses (three needed re-dispatch after relay concurrency refusals); outcome **approved** and **acknowledged**; `authority: burned`; consumed revision `sha256:7566e2a8…`. Risk and readability lenses found NOTHING; reliability found nothing.

## T1 advisory findings (non-blocking, informational; separate later work, never re-review triggers)
- `R3-ATTR-PARSER-REGRESSION` (reliability WARNING, `assemble-orchestrator-prompt.py:48`) — REAL REGRESSION INTRODUCED BY T1's FIX 2, to be fixed in T2. The generalised `ATTR_KEY_RE` (`(?:^|\s)([A-Za-z][A-Za-z0-9_]*)=`) also matches an `identifier=` sequence INSIDE an attribute value, so an overlay such as `after=### Foo=Bar` is misparsed as an unknown attribute `Foo` and rejected, where the previous fixed-key split accepted it. Deterministic; disposition "worsened".
- `R3-ATTR-VALIDATION-UNTESTED` (reliability WARNING, `tests/test_orchestrator_prompt_source.py:388-566`) — the new unknown-attribute and duplicate-attribute raises introduced by fix 2 have NO test coverage. Fix in T2 alongside the regression.
- `R4-half-marker-drop` (resilience WARNING, `assemble-orchestrator-prompt.py:14-18`) — PRE-EXISTING, not introduced: a replace/remove body carrying only one half of a marker pair drops the other half with exit 0 and the count-based balance check is vacuous (0 == 0). T1 documents and pins it; the fail-loudly invariant is T2's structural fix (the marker pair move).

## T2 advisory findings (non-blocking, informational; separate later work, never re-review triggers)
- `R4-001` (resilience SUGGESTION, `assemble-orchestrator-prompt.py:14-19`) — the managed-marker invariant (a paired marker must not straddle a section boundary) is now DOCUMENTED in the assembler docstring and the ledger but NOT enforced by the assembler; a future upstream template edit that re-straddles a pair would again be caught by nothing automated. Disposition base-only. Candidate improvement: make the assembler fail loudly when a managed pair straddles a section boundary.
- `R4-002` (resilience SUGGESTION, `assemble-orchestrator-prompt.py:103-118`) — heading-valued attributes (`after`/`supersedes`) still terminate at the next known-attribute token, so a heading legitimately containing a literal ` kind=`/` id=`/` sha256=` would be silently truncated and surface later as a missing-anchor error against the target rather than the malformed attribute. The old parser had the identical truncation and additionally rejected unknown `identifier=` tokens inside values, so this is PRE-EXISTING and narrowed, not introduced.

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` writer (direct; the PM layer is unusable). Trigger: secure no-inline-mutation policy; multiple files → bounded sandbox writer.

## Next step

Q66 source work is COMPLETE (T0–T2; both reviewed). OWNER ACTION: re-read `global-config/prompts/gentle-orchestrator/base.md`'s header note and the T2 scope-override carry-forward before any future `gentle-ai sync`/re-render, then the deploy described in the Q34 runbook. Carry-forward: `R4-001` (enforce the marker invariant), `R4-002` (heading-value truncation), and the template local-patch hazard.
