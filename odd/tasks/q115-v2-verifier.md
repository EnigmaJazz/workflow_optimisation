# Q115 — V2-mode verifier reads V2 paths and this checkout

## Objective

With OpenCode V2 first on `PATH`, `verify-workflow.sh` must derive its config
surface and workspace from V2 and from the checkout that contains the script,
must not fail on V1-only shapes in section 9, must classify the `github_ro`
probe correctly, and must therefore reach section 10 with no failures from
these items (acceptance is Tier 2's host run with the live V2 server).

## Problem (owner-supplied evidence, 2026-11-08)

1. `WORKSPACE` is fixed to `~/ai-workspace/workflow_optimisation`
   (`verify/10-env.sh:33`); the main checkout may be on any branch.
   `WORKFLOW_VERIFY_WORKSPACE` is the only override.
2. `AGENTS_FILE` derives from `OPENCODE_CONFIG_DIR`
   (`verify/10-env.sh:34,44`), so `AGENTS_BOUNDED_BLOCK_DRIFT`
   (`verify/58-section-7-recipe.sh:403`) compares the stale V1 copy even in V2
   mode. The V2 root copy is byte-identical to source.
3. Section 9 runtime-agent checks assume V1 config shapes. Pointing the V1
   config-dir variable at the derived V2 root produced ~20 V2-correct failures
   (global `grep` deny, `plugins` not `plugin`, materialised Astra aliases, no
   V1 magic-context or GGA fallback plugin entry). One runtime-agents failure
   under the supported invocation remains undiagnosed.
4. `GITHUB_RO_RUNTIME_INACTIVE_OR_UNSCOPED` is recorded although the checker
   prints `clean<TAB>github_ro is connected on the V2 server ...` after two
   retries. Root cause (observed by reading the code):
   `verify/60-section-9a-9b-secure-service.sh:34` captures `2>&1`, so the
   checker's stderr retry lines precede `clean` and the anchored `case` pattern
   `clean$'\t'*` cannot match.
5. `GENTLE_AI_V4_ODD_SKILL_MISSING` (`verify/51-section-1-gentle-ai.sh:45-47`)
   looks for `work-unit-commits` / `chained-pr` under `$SKILLS_DIR`, which is the
   V2 root when the config dir is overridden. That is Q116 and is NOT fixed
   here; V2 mode must not regress it.
6. Behavioural probes (§10, §10a) are gated on `FAIL -ne 0`.

## Authorized scope

V2-mode behaviour of the verifier plus documentation. No change to V1-mode
behaviour, no change to `global-config/` content, no deployment, no push/PR.

## Decisions

- D1 (workspace): in V2 mode, when `WORKFLOW_VERIFY_WORKSPACE` is unset,
  `WORKSPACE` is derived from the verifier entry path (`VERIFY_ENTRY_PATH`), and
  every `WORKSPACE`-derived path variable is recomputed from it, so the run
  reads this checkout. An explicit override still wins in both modes.
- D2 (AGENTS): in V2 mode `AGENTS_FILE` defaults to `$V2_CONFIG_ROOT/AGENTS.md`
  (`WORKFLOW_VERIFY_AGENTS_FILE` overrides in both modes). `OPENCODE_CONFIG_DIR`
  and therefore `SKILLS_DIR` stay unchanged so Q116 is neither fixed nor
  regressed.
- D3 (section 9): keep `checkers/check-runtime-agents.cjs` (2482 lines,
  V1-shaped, consumed elsewhere) untouched. Add a small, independently testable
  V2 projection adapter that validates V2-only invariants and emits a
  V1-shaped config for the unchanged checker. Every item the adapter does not
  project is printed as `skipped (V2): <reason>`; no blanket skip.
- D4 (github_ro): capture stdout only; surface the checker's stderr retry
  lines as indented `info:` output; keep the anchored classification so a real
  `error<TAB>...` still fails.
- D5 (tests first): behaviour changes land with failing-then-passing tests.
  Every absence/skip assertion carries a positive control proving the same
  check still fires where it applies (V1 path, or a mutated V2 fixture).

## Task IDs

- T1 — TDD + fixture scaffolding for V2 mode derivation (tests red first).
- T2 — V2 workspace/AGENTS/runtime-config derivation (D1, D2) + `info:` lines.
- T3 — Section 9 V2 adapter and its wiring (D3), explicit skip reasons.
- T4 — `github_ro` stderr/stdout classification fix (D4).
- T5 — Docs: `docs/upgrades/opencode-v2-cutover.md` step 6 exact invocation.
- T6 — Manifest regeneration and full offline verification.

## Acceptance criteria

- AC1 V1 mode byte-identical behaviour: unchanged default `WORKSPACE`,
  `AGENTS_FILE`, and checker argv; tests prove the V1 values and the existing
  suites stay green.
- AC2 A V2 run derives `WORKSPACE` to the script's checkout, `AGENTS_FILE` and
  the section-9 runtime config from `V2_CONFIG_ROOT`, and prints the effective
  values.
- AC3 Section 9 in V2 mode runs the adapter, fails on any V2-only invariant
  violation, and names each non-projected item with `skipped (V2): <reason>`.
- AC4 A `clean` result survives stderr retry chatter; a real error still fails.
- AC5 Q116 untouched: `SKILLS_DIR` still derives from `OPENCODE_CONFIG_DIR`.
- AC6 `python3 scripts/verifier_manifest.py check` passes after `update`.
- AC7 Cutover step 6 documents the exact V2 invocation and overrides.
- AC8 No reviewer dispatch and no deployment from this unit.

## Checks

`python3 -m pytest tests/ -q` (at minimum the verifier suites),
`python3 scripts/verifier_manifest.py check`, `bash -n` on every changed
module. The live V2 acceptance run (`PATH=<v2>:$PATH bash verify-workflow.sh
--behavioral < /dev/null`) is Tier 2's, not this unit's.

## Progress

- 2026-11-08: unit opened. Route: ODD, substantial change, global-tooling-class
  verifier contract. PM dispatch unavailable in this linked worktree (`.git` is
  a file; the PM contract mandates BLOCKED when the worktree HEAD lives under
  `.git/worktrees/`), so this is a direct delegated writer unit with the
  deviation recorded here.
- Next: T1.

## Route / trigger evidence

- Class: substantial ODD change (verifier contract consumed by others).
- Trigger: mutation rule (verifier modules) + execution rule (pytest).
- Writer: `general` (direct orchestrator dispatch; PM path structurally blocked
  by the worktree branch-anchor contract).

## Next step

T1: write the failing tests, then T2-T4 implementation.


## Revisions
- r1 2026-11-08T07:04:51Z gentle-orchestrator: Open Q115 unit: V2-mode verifier derivation, section 9 adapter, github_ro classification
