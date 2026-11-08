# Q115 — V2-mode verifier reads V2 paths and this checkout

## Objective

With OpenCode V2 first on `PATH`, `verify-workflow.sh` must derive its config
surface and workspace from V2 and from the checkout that contains the script,
must not fail on V1-only shapes in section 9, must classify the `github_ro`
probe correctly, and must reach section 10 with no failures from these items.
Acceptance remains Tier 2's live host run with the V2 server.

## Commits on `chore/q115-v2-verifier`

- `90ccb14` — V2-aware env derivation, section 9 projection, `github_ro` fix,
  docs, tests.
- `96a2d50` — regenerated verifier manifest without the bytecode row.
- `63d2b0d` — Tier 4 findings F1 and F2 (V2 agent constructs, V1 override
  surface).

## F1 (HIGH) — section 9 vs the real derived config

Resolved. `derive-v2-config.py:291-309` materialises `-astra` aliases and
`:197-213` inserts Systematic access mirrors; `check-runtime-agents.cjs:376-380`
rejects both, so section 9 failed on any real derived config.

- `v2-runtime-config.py` validates the alias invariant (base exists, hidden,
  model present, `permission`/`tools` identical to base) and the mirror
  invariant (only `sandbox_`/`host_` rules, only mirror fields, at least one
  rule), then removes only validated entries from the projection and reports
  each removal with its real reason.
- Mirror detection is purely structural: a mixed entry such as the real
  `gentle-ai-worker` (`opencode.json:414`, `sandbox_write` plus
  `bash`/`read`/`grep`) is NOT a mirror, so it keeps full checker coverage; a
  Systematic agent pinned with real rules still reaches the checker and trips
  `SYSTEMATIC_AGENT_SHADOWED`.
- The literal `<reason>` template at `59:174` is gone; adapter notes are
  printed as `info:`.
- `verify/checkers/check-runtime-agents.cjs` was not modified.

`-astra` removal is safe because the equivalent checks now run in the adapter,
not because the entries were dropped.

## F2 (MEDIUM) — unconditional overrides widened the executable surface

Resolved. `derive_workspace_paths` now assigns every source as a plain
`$WORKSPACE`-anchored value, keeping only the two overrides that predate this
unit (`SECURE_RUNTIME_WITNESS`, `CACHE_PRUNE_APPROVAL`). This removes
`WORKFLOW_VERIFY_PLUGIN_CACHE_INTEGRITY_HELPER`, whose target is executed by
`30-recover-config.sh:156-157` and `54-section-2c-package-integrity.sh:31-35`
outside the module manifest, and `WORKFLOW_VERIFY_AGENTS_FILE`, which
redirected the V1 recovery target in `31-recover-skills-agents.sh:76`.
`AGENTS_FILE` and `RUNTIME_CONFIG_FILE` are plain again in `10-env.sh`; their
overrides apply only in the V2 branch of `21-opencode-major.sh`.

## Checks observed

- `python3 -m pytest tests/test_verifier_v2_sections.py -q -rs` →
  `9 passed, 1 skipped`; skip reason `node could not be spawned: [Errno 13]
  Permission denied: 'node'`.
- Combined requested suite → `51 passed, 15 skipped`, no failures. Skip causes
  are the sandbox's inability to spawn `node`; `/usr/bin/node` exists on the
  host.
- `python3 scripts/verifier_manifest.py check` → `ok: manifest and pin are
  current`; no `__pycache__`/`.pyc` row in `VERIFY_MODULES`.
- `bash -n` on the entry and changed modules → exit 0.
- Adapter over a real-derived fixture → exit 0, dropping
  `gentle-ai-worker-astra` plus the four access mirrors and keeping
  `gentle-ai-worker` with unchanged rules.
- Not run: live `verify-workflow.sh --behavioral` (needs the live V2 server),
  native review, and reviewers — all excluded by the dispatch.

## Open items

- **Native review due, not started** — earlier assessment: `high`, lineage
  `review-e460198a780543cd`, target for `5beff94..90ccb14`. Not re-assessed
  for `63d2b0d`, per the "do not run native review" constraint.
- **Protected-path follow-up (owner).** `scripts/verifier_manifest.py` is S17.
  `render()` and `drift()` filter only by `is_file()`, so `__pycache__` under
  `verify/checkers` becomes a required module even though `.gitignore` excludes
  bytecode. Patch both comprehensions with `"__pycache__" not in
  p.relative_to(base).parts and p.suffix != ".pyc"`.
- **Residual:** mirror detection is structural, so a real agent declaring only
  `sandbox_`/`host_` rules would be classified as a mirror and dropped from the
  projection. No such agent exists in the current config.
- PM dispatch remains impossible in this worktree (`.git` is a file, so
  `docs/specs/pm-handoff.md` mandates BLOCKED); work ran as direct `general`
  writer dispatches.

## Next step

Tier 2: live V2 acceptance run. Owner: `verifier_manifest.py` bytecode filter.


## Revisions
- r1 2026-11-08T07:04:51Z gentle-orchestrator: Open Q115 unit: V2-mode verifier derivation, section 9 adapter, github_ro classification
- r2 2026-11-08T08:34:43Z gentle-orchestrator: Record Q115 commits 90ccb14 + 96a2d50, observed checks, review-due state and the protected-path follow-up
- r3 2026-11-08T10:38:50Z gentle-orchestrator: Record 63d2b0d and the F1/F2 resolution, checks, and residual risks
