# Q67 — Retired SDD command detector — Advice record

## advisor-integration-pre (2026-10-14)

Pre-code advice (integration lens); load-bearing points only:

- **Denylist, not glob (the central decision).** `commands/` is USER SPACE: a glob, or an
  "anything not in the manifest" rule, would flag the owner's own commands. Deriving the set from a
  manifest or a pattern is forbidden by the recorded Q30 advice
  (`odd/advice/gentle-ai-v4.md:100-101`: use a FIXED retired list, never "anything absent from the
  reviewed manifest"). The skill precedent uses a fixed list too (`verify-workflow.sh:3924`,
  `retiredWorkflowSkills=("workflow-sdd-secure")`). So use an EXPLICIT denylist of the retired
  command basenames and test each `<COMMANDS_DIR>/<name>.md` with a per-name `[ -f ]`.
- **Placement.** Section 3, immediately after the retired-skill block (`verify-workflow.sh:3920-3934`)
  and before section 4 (`:3936`): same region, same `$OPENCODE_CONFIG_DIR`, and it must run before
  the later sections. The comment above the skill block (`:3920-3923`) explains why the list must
  not be derived from the manifest; carry the same reasoning onto the command check.
- **`COMMANDS_DIR` seam.** Add
  `COMMANDS_DIR="${WORKFLOW_VERIFY_COMMANDS_DIR:-$OPENCODE_CONFIG_DIR/commands}"`, mirroring
  `SKILLS_DIR` at `verify-workflow.sh:116` (no such override exists today). Without it the check
  cannot be exercised against a planted directory; the skill check needed the same addition
  (`WORKFLOW_VERIFY_SKILLS_DIR`, `:116`).
- **Message shape.** Match `verify-workflow.sh:3928` exactly: a code prefix, the exact path, and an
  exact one-time removal — `RETIRED_SDD_COMMAND_PRESENT: $COMMANDS_DIR/<name>.md exists; remove it
  once with: rm $COMMANDS_DIR/<name>.md`. Use `rm`, NOT `rm -rf`, because the target is a SINGLE
  FILE; this directly addresses the recorded `R3-rmrf-guidance` advisory (the skill message uses
  `rm -rf` because a skill is a directory). Document the one-time removal as a deploy step.
- **Hard-fail, detect-only.** A hard `fail()` is correct, matching the skill precedent (`:3928`):
  the check is detect-only and cannot self-heal, and a warning would be swallowed. The accepted
  consequence: sections 10/10a/11 gate on `FAIL -ne 0` (`verify-workflow.sh:5010`, `:5059`,
  `:5117`), so a hard-failing retirement check MASKS them — the same trade-off the skill check
  already makes for `RETIRED_WORKFLOW_SKILL_PRESENT`.

## advisor-testing-pre (2026-10-14)

Pre-code advice (testing lens); load-bearing points only:

- **Committed test, not an ad-hoc extracted predicate.** Q30, Q32 and Q65 all proved their
  retirement checks by extracting and executing the predicate out of band, and all three carry
  recorded advisory debt (`R3-retired-skill-coverage` and its siblings). That approach leaves no
  durable control. `tests/test_anchor_manifest.py` is the ONLY durable precedent and is the bar: a
  committed `tests/test_retired_commands.py` that runs under `python3 -m unittest discover -s tests`
  and proves non-vacuity with its own positive control.
- **FOUR-fixture control** (each rules out a distinct vacuous-pass mechanism):
  - (a) a planted file under the `WORKFLOW_VERIFY_COMMANDS_DIR` override → the check FIRES;
  - (b) a clean override directory → the check is SILENT;
  - (c) a planted file under the override with a DECOY `OPENCODE_CONFIG_DIR` → the check still FIRES
    (proves the override is honoured, not a hard-coded path);
  - (d) a planted file under the real `$OPENCODE_CONFIG_DIR/commands/` with an EMPTY override → the
    check does NOT fire (proves there is no parent/real-path fallback).
- **Test-convention constraints.** NEVER run the verifier against the host tree; fixtures with
  `WORKFLOW_VERIFY_*` overrides only. Do NOT use `--recover-config-only` (it exits before section 1,
  so it proves nothing about section 3). Re-pin `VERIFY_SCRIPT_SHA256` LAST. `bash -n` is smoke-only
  and is NOT evidence; the coherence proof is `sha256sum verify-workflow.sh` == the pin extracted
  with the verifier's own regex (`verify-workflow.sh:1251-1276`, `:1268`).
- **No weakening.** No existing check is weakened; the new check is additive beside the skill block.
- **Deferred items (recorded, not done):**
  - content-based scanning for retired-agent references inside a renamed command file — a broader,
    higher-false-positive invariant; the observed incident (`sdd-code.md`) was a NAME match, so the
    name-denylist closes the observed class; content scanning is a separate, riskier invariant.
  - the windsurf and antigravity command directories — their paths are not recorded in this repo, so
    they cannot be detected from here without inventing a path.
