# Q67 — Retired SDD command detector

**Feature:** post-v4-upgrade residue cleanup
**Task ID:** q67-retired-sdd-command-check (stable)
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0 IN PROGRESS (tracker + advice created; T1 pending)
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

- [ ] T1 — add COMMANDS_DIR + WORKFLOW_VERIFY_COMMANDS_DIR (mirroring SKILLS_DIR at
  `verify-workflow.sh:116`); add the RETIRED_SDD_COMMAND_PRESENT block in section 3 immediately
  after the retired-skill block (`:3920-3934`) and before section 4 (`:3936`), using an explicit
  denylist of the retired command basenames and a per-name `[ -f ]` test, with the message shape:
  `RETIRED_SDD_COMMAND_PRESENT: <path> exists; remove it once with: rm <path>`; add
  `tests/test_retired_commands.py` mirroring `tests/test_anchor_manifest.py`; re-pin
  VERIFY_SCRIPT_SHA256 LAST.

## Progress

- 2026-10-14: T0 — tracker and advice record created; no source edit yet. Route: delegated.

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply`.
- Trigger: secure no-inline-mutation policy; multiple non-trivial files → bounded sandbox writer.
- RDD: on (decided by global).

## Next step

T1 implementation, then its native review (high risk: shell_source), then the metadata record.
