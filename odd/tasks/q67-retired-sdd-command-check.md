# Q67 — Retired SDD command detector

**Feature:** post-v4-upgrade residue cleanup
**Task ID:** q67-retired-sdd-command-check (stable)
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0–T1 DONE-AT-SOURCE (committed and reviewed).
**Model:** cloud `opencode-go/deepseek-v4.1-flash`

## Objective

Close the CLASS behind a real post-upgrade incident: a retired SDD slash-command survived a
gentle-ai v4 sync and stayed live, undetected by the verifier.

## Problem

After the v4 upgrade (gentle-ai 4.1.1, 2026-10-13), the sync deleted every managed `sdd-*.md`
under the deployed `~/.config/opencode/commands/`, but `sdd-code.md` SURVIVED because it is not
gentle-managed. It still referenced the retired `sdd-apply`/`sdd-apply-local` agents and the
removed Engram path, and remained a live `/sdd-code` command until the owner deleted it manually.
The verifier did not catch it: its existing retirement check asserts retired SKILL DIRECTORIES
(`RETIRED_WORKFLOW_SKILL_PRESENT`, `verify-workflow.sh:3920-3934`), not commands. No detector
exists for this class.

## Scope

- **In scope:** T1 adds `RETIRED_SDD_COMMAND_PRESENT` to `verify-workflow.sh`, a
  `COMMANDS_DIR`/`WORKFLOW_VERIFY_COMMANDS_DIR` seam, and a committed test with four fixtures.
- **Out of scope (deliberately deferred; reasons recorded):**
  - content-based detection of retired-agent references inside a renamed command file — a broader,
    higher-false-positive invariant; the observed incident was a NAME match;
  - the windsurf and antigravity command directories — their paths are not recorded in this repo;
  - any auto-deletion — detect-only by design, matching the skill precedent.

## Constraints

- The change edits `verify-workflow.sh`, which is DIGEST-PINNED: `VERIFY_SCRIPT_SHA256` in
  `global-config/plugins/workflow-health-check.ts:93` must be re-pinned LAST in the same commit.
- The verifier must NEVER be run against the host tree (fixtures with `WORKFLOW_VERIFY_*`
  overrides only, and NOT `--recover-config-only`, which exits before section 1).
- `bash -n` is smoke-only and is NOT evidence.
- The new check HARD-FAILS (detect-only), which masks sections 10/10a/11 because they gate on
  `FAIL -ne 0` (`verify-workflow.sh:5010`, `:5059`, `:5117`) — the same accepted trade-off the
  skill check makes.
- Branch `main`; never commit; never switch branches.

## Acceptance criteria

- A retired SDD command in the deployed commands directory is caught with an exact-path +
  exact-removal message.
- The detector uses an EXPLICIT DENYLIST, never a glob (`commands/` is user space).
- A committed test proves non-vacuity.
- No existing check is weakened.
- The pin matches `sha256sum verify-workflow.sh`.

## Authorized scope

T1: `verify-workflow.sh`, `tests/test_retired_commands.py` (new),
`global-config/plugins/workflow-health-check.ts` (the pin ONLY). Plus this tracker, the advice
record, `ROUTER-LOG.md`.

## Checks

- `python3 -m unittest tests.test_retired_commands -v`
- `python3 -m unittest discover -s tests`
- `HOME="$(mktemp -d)" bun test tests/routing-guard`
- `bash -n verify-workflow.sh` (smoke only)
- The four fixture controls.
- `sha256sum verify-workflow.sh` == the pin.

## Tasks

- [x] T1 — add COMMANDS_DIR + WORKFLOW_VERIFY_COMMANDS_DIR (mirroring SKILLS_DIR at
  `verify-workflow.sh:116`); add the RETIRED_SDD_COMMAND_PRESENT block in section 3 immediately
  after the retired-skill block (`:3920-3934`) and before section 4 (`:3936`), using an explicit
  denylist of the retired command basenames and a per-name `[ -f ]` test, with the message shape:
  `RETIRED_SDD_COMMAND_PRESENT: <path> exists; remove it once with: rm <path>`; add
  `tests/test_retired_commands.py` mirroring `tests/test_anchor_manifest.py`; re-pin
  VERIFY_SCRIPT_SHA256 LAST.

## Progress

- 2026-10-14: T0 — tracker and advice record created; no source edit yet. Route: delegated.
- 2026-10-14: T1 committed `365b718` (3 files, +282/−1): the COMMANDS_DIR/WORKFLOW_VERIFY_COMMANDS_DIR seam, the RETIRED_SDD_COMMAND_PRESENT detect-only block in section 3 with a 12-name explicit denylist, and tests/test_retired_commands.py (14 tests). Checks: unittest discover 127 OK; routing-guard 96 pass / 0 fail; the four fixtures plus PositiveControls observed; the planted/clean integration runs observed message-level; `sha256sum verify-workflow.sh` == the re-pinned `d89dc81a…` (MATCH).
- 2026-10-14: T1 native review: lineage `review-01bc0dd6dde6aeeb`; tier high; 11-path accumulated candidate (692 lines); four lenses; outcome approved and acknowledged (`authority: burned`).
- 2026-10-14: T1 advisories (all non-blocking, informational; never re-review triggers): `R3-001` (reliability SUGGESTION, tests/test_retired_commands.py:88-89 — the block-extraction heuristic depends on the outer `fi` sitting at column 0; a future indentation change could silently truncate the extracted snippet and break the clean-state fixtures); `R4-HARDFAIL-MASKING-1` (resilience WARNING, verify-workflow.sh:3947-3949 — the hard fail masks sections 10/10a/11, the pre-accepted trade-off the skill check already makes, documented in this tracker and the advice record); `R4-RM-UNQUOTED-GUIDANCE-1` (resilience SUGGESTION, verify-workflow.sh:3949 — the advisory `rm` text embeds the path unquoted, so a spaced install path would break a verbatim paste; guidance polish only).
- 2026-10-14: two status drifts the review flagged were REAL and are fixed in this metadata commit: the Q67 queue entry still read "source not yet written" while T1 had landed, and the Q34 queue line still read "the runbook has never been executed" while the execution record shows it ran on 2026-10-13.
- 2026-10-14: relay-deadline incident (external, not this repo): the resilience lane failed 4× with `reviewer_relay_deadline_expired` (600000 ms) while the reviewer needed 26m18s, then `reviewer_result_not_admissible` because the reviewer echoed a mismatched subject_hash (`…53c5514a31388266…` vs the binding's `…53c5514a3ab026ac…`). The owner permanently increased the relay timeout; the lane then completed and was captured. Root cause and location are recorded in docs/TODO.md (the external review-relay-deadline item).
- 2026-10-14: delivery strategy recorded as `stacked-to-main` (owner decision); the running total of 468 authored lines crossed the ~400 accumulated threshold, so the strategy applies. The four commits stay stacked on `main`.
- 2026-10-14: OWNER-REPORTED deployment: the owner ran `bash verify-workflow.sh` after the Q67 work and reported "All checks clean". This is recorded AS THE OWNER'S REPORT — not independently verified by this worker, which cannot read the deployed `~/.config/opencode` tree or run the verifier. The re-pinned verifier digest is `d89dc81a…`.

## Delivery strategy

**Chosen strategy:** `stacked-to-main` (owner decision, 2026-10-14).

**Forecast and actual (authored additions + deletions, generated files excluded):** T0 tracker+advice+queue `3501880` = 167; T1 detector+test `365b718` = 283; T1 metadata `d89a404` = 18. **Running total 468**, which crosses the about-400 accumulated delivery threshold, so the strategy applies to this feature.

**Applied:** the work-unit commits `3501880`, `365b718` and `d89a404` stay STACKED ON `main`; no separate feature branch and no branch reconciliation were performed, by owner decision. The next change starts on its own feature branch (owner decision, 2026-10-14).

**Process note (recorded, not hidden):** this strategy was selected AFTER the commits landed rather than at tracker creation as the contract specifies (`odd-and-review.md:36`), and the per-commit reviewability receipts were recorded late (`058ef47`). Both gaps are acknowledged; the commits themselves were assessed normally (medium / `under_budget`).

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply`.
- Trigger: secure no-inline-mutation policy; multiple non-trivial files → bounded sandbox writer.
- RDD: on (decided by global).

## Next step

Q67 is CLOSED at source (T0–T1; T1 reviewed and acknowledged). The owner separately reported the post-Q67 deployment clean: the owner ran `bash verify-workflow.sh`, which re-mirrored the re-pinned verifier and passed. The mirror and the OpenCode restart were the owner's action — not performed or verified by this worker, which cannot read the deployed `~/.config/opencode` tree or run the verifier. Carry-forward advisories: R3-001, R4-HARDFAIL-MASKING-1, R4-RM-UNQUOTED-GUIDANCE-1. The deferred items (content-based detection of retired-agent references in a renamed command file; the windsurf/antigravity command directories) remain out of scope by decision.
