# Q66 — Assembler hardening

**Feature:** gentle-ai v4 upgrade / queue Q66 (harden the orchestrator prompt assembler).
**Task ID:** `q66-assembler-hardening` (stable).
**Class:** global-tooling-change.
**Route:** `workflow-odd-secure` (delegated).
**Unit status:** T0 IN PROGRESS (tracker + advice created; T1 and T2 pending).
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
- The ordering test is RED before the fix and GREEN after.
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

- [ ] T1 — assembler-only hardening: fix the exit-code contract (catch `OSError` → 2), harden `parse_attrs` (per-key uniqueness, reject unknown/duplicate keys), guard overlapping-region ordering, and ADD the five failure-path tests plus the missing-file exit-2 test; tighten the three `assertNotEqual(rc, 0)` sites to `assertEqual(rc, 2)`. MUST leave the assembled bytes unchanged.
- [ ] T2 — marker coupling: move the `opencode-desktop-delegation-progress` pair into ONE base section, then run the regeneration chain (opencode.json, `CURRENT_PROMPT_SHA256`, normative-ledger.md, affected overlay `supersedes`, verify-workflow.sh content assertions) and re-pin `VERIFY_SCRIPT_SHA256` LAST.

## Progress

- 2026-10-11: T0 — tracker and advice record created from two pre-code advisories; no source edit yet. Route: delegated.

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` writer (direct; the PM layer is unusable). Trigger: secure no-inline-mutation policy; multiple files → bounded sandbox writer.

## Next step

T1 (assembler-only), then T2 (the marker move + regeneration chain), then the owner's deploy.
