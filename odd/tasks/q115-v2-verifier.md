# Q115 — V2-mode verifier reads V2 paths and this checkout

## Objective

With OpenCode V2 first on `PATH`, `verify-workflow.sh` must derive its config
surface and workspace from V2 and from the checkout that contains the script,
must not fail on V1-only shapes in section 9, must classify the `github_ro`
probe correctly, and must therefore reach section 10 with no failures from
these items. Acceptance remains Tier 2's live host run with the V2 server.

## Result

Branch `chore/q115-v2-verifier`:

- `90ccb14` — V2-aware env derivation, section 9 projection, `github_ro` fix,
  docs, tests (9 files).
- `96a2d50` — regenerated verifier manifest without the bytecode row (2 files).

Combined candidate: 12 paths, 443 changed lines, native risk `high`
(`process_boundary` + `shell_source` on `verify-workflow.sh`).

## Problem (owner-supplied evidence, 2026-11-08)

1. `WORKSPACE` was fixed to `~/ai-workspace/workflow_optimisation`
   (`verify/10-env.sh:33`); the main checkout may be on any branch.
2. `AGENTS_FILE` derived from `OPENCODE_CONFIG_DIR`, so
   `AGENTS_BOUNDED_BLOCK_DRIFT` compared the stale V1 copy in V2 mode.
3. Section 9 runtime-agent checks assumed V1 config shapes.
4. `GITHUB_RO_RUNTIME_INACTIVE_OR_UNSCOPED` was recorded although the checker
   printed `clean`. Root cause: `2>&1` merged stderr retry lines ahead of
   `clean`, so the anchored `case` could not match.
5. `GENTLE_AI_V4_ODD_SKILL_MISSING` is Q116 and is out of scope.
6. Behavioural probes are gated on `FAIL -ne 0`.

## What changed

- `verify/10-env.sh`: all `WORKSPACE`-derived paths moved into
  `derive_workspace_paths`, preserving every `WORKFLOW_VERIFY_*` override;
  adds `AGENTS_FILE` and `RUNTIME_CONFIG_FILE` overrides. V1 defaults
  unchanged.
- `verify/21-opencode-major.sh`: in V2 mode, when
  `WORKFLOW_VERIFY_WORKSPACE` is unset, `WORKSPACE` becomes the verifier
  entry's own directory, paths are re-derived, `AGENTS_FILE` and
  `RUNTIME_CONFIG_FILE` default to `V2_CONFIG_ROOT`, and an unresolvable
  entry fails as `V2_WORKSPACE_DERIVATION_FAILED` (no silent `/global-config`
  paths). One `info:` line names the effective values.
- `verify/checkers/v2-runtime-config.py` (new): validates V2-only invariants
  (exactly one scoped Magic Context `@~pin`, exactly one fallback fork ref as
  vendor directory or `/index.ts`, global `permission.grep=deny` plus
  orchestrator `allow`, `mcp.github_ro` present, `tools["github_ro_*"]` false)
  and emits a V1-shaped projection for the unchanged checker. `check-runwar
  -agents.cjs` was deliberately not edited.
- `verify/59-section-8-9-config-runtime.sh`: runs the projection in V2 mode,
  fails with `V2_RUNTIME_CONFIG_PROJECTION_FAILED`, and prints checker notes.
- `verify/60-section-9a-9b-secure-service.sh`: `classify_github_mcp_result`
  plus stdout-only capture with stderr surfaced as `info:`.
- `docs/upgrades/opencode-v2-cutover.md` step 6: exact V2 invocation and
  overrides.
- Tests: `test_verifier_v2_sections.py` (new), `test_verifier_v2_mode.py`,
  `test_verifier_v2_github_mcp.py`.

## Scope held

`OPENCODE_CONFIG_DIR` and therefore `SKILLS_DIR` unchanged, so Q116 is
neither fixed nor regressed. V1 branch untouched. No deployment, no push.

## Checks observed

- `python3 scripts/verifier_manifest.py check` → `ok: manifest and pin are
  current` (after the clean regeneration on the host).
- `bash -n` on the entry and changed modules → exit 0.
- pytest: `30 passed, 2 failed` on the pre-regeneration tree; the two
  failures were `ManifestHasNoBytecode` (caused by the `.pyc` manifest row,
  since removed) and `Manifest.test_checkers_are_valid_scripts`
  (`PermissionError: node`). Sandbox `node` cannot spawn; `/usr/bin/node`
  exists on the host, so the node failures are environmental.
- Not run: the live `verify-workflow.sh --behavioral` V2 acceptance run.
  It needs the live V2 server and is Tier 2's gate.

## Open items

- **Native review due, not started.** `review assess` returned `high`,
  `review_due: true`, lineage `review-e460198a780543cd`, target
  `sha256:7c6c9b33…`. The dispatch instructed not to run reviewers, so the
  review was deliberately not started.
- **Protected-path follow-up (owner).** `scripts/verifier_manifest.py` is S17.
  `render()` and `drift()` both do `rglob("*")` filtered only by `is_file()`,
  so any `__pycache__` under `verify/checkers` becomes a required verifier
  module even though `.gitignore` excludes bytecode. Patch both comprehensions
  with `"__pycache__" not in p.relative_to(base).parts and p.suffix != ".pyc"`.
  This caused two bad manifest regenerations during the unit.
- Multi-tier note: PM dispatch is structurally impossible in this worktree.
  `.git` is a file, so `docs/specs/pm-handoff.md` mandates `BLOCKED` for a
  worktree whose HEAD lives under `.git/worktrees/`. This unit ran as direct
  bounded `general` writer dispatches instead.

## Progress

- 2026-11-08: unit opened; tracker created (revision 1, `d5ad8de`).
- 2026-11-08: writer 1 implemented; parent readback found the adapter rejected
  the real V2 refs and the manifest had absorbed a `.pyc` row.
- 2026-11-08: writer 2 produced an unlandable result (protected path, diverged
  baseline); its functional delta was re-applied by writer 3.
- 2026-11-08: writer 4/5 hit sandbox worker-setup timeouts; writer 5's session
  was resumed and applied the clean manifest.
- 2026-11-08: committed `90ccb14` + `96a2d50`; review assessment `high`.

## Next step

Tier 2: run the live V2 acceptance command, and decide whether to start native
review for target `sha256:7c6c9b33…`. Owner: apply the
`scripts/verifier_manifest.py` bytecode filter.


## Revisions
- r1 2026-11-08T07:04:51Z gentle-orchestrator: Open Q115 unit: V2-mode verifier derivation, section 9 adapter, github_ro classification
- r2 2026-11-08T08:34:43Z gentle-orchestrator: Record Q115 commits 90ccb14 + 96a2d50, observed checks, review-due state and the protected-path follow-up
