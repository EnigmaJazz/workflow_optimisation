# Q115 — V2-mode verifier: named section 9 skip

## Current outcome

V2 mode skips section 9's V1 checker with a named line, and the run reports an
explicit incomplete status rather than success. V1 behaviour is unchanged.

## Commits on `chore/q115-v2-verifier`

- `90ccb14` — V2-aware env derivation, `github_ro` stdout fix, docs.
- `96a2d50` — manifest regenerated without the bytecode row.
- `63d2b0d` — Tier 4 F1/F2 (V2 agent constructs, V1 override surface).
- `a5e3ada` — Tier 4 F1 recheck (derivation-exact projection).
- `88b296a` — narrowed scope: projection removed, named skip,
  `VERIFICATION_INCOMPLETE`.
- `a9d1805` — `SKIPPED_MESSAGES` initialization for `set -u`.
- `108c519` — distinct exit status 3 for an incomplete run.

## Exit-code contract

| Run state | Status | Banner |
| --- | --- | --- |
| clean | 0 | `== All checks passed — workflow setup intact ==` (or the self-repairs variant) |
| incomplete (section 9 skipped) | **3** | `VERIFICATION_INCOMPLETE` |
| any failure (with or without skips) | 1 | `Some checks failed` + failed list |

`verify-workflow.sh` is a 157-line loader that sources `verify/NN-*.sh` in
manifest order and `62-section-11-summary.sh` runs last, so the summary's exit
status is the script's. A skip-only run previously fell off the end with 0, so
`verify-workflow.sh && next_step` accepted an incomplete verification; the
summary now exits 3 and the cutover step warns callers not to read 3 as
success.

`workflow-health-check.ts` catches `e.code === 3` (execFileAsync rejects on any
non-zero status) and sets the `incomplete` state with the existing
`VERIFICATION_INCOMPLETE` warning instead of `failed`.

An incomplete run still withholds the cache-prune approval, so
`prune-opencode-plugin-cache.py` refuses on the missing approval, not on the
exit status — no change needed there.

## Section 9 behaviour

- V2: runs the standalone invariant validator, prints one
  `SKIPPED (V2: SECTION_9_RUNTIME_AGENT_CHECKER_NOT_RUN; ...)` line, never
  invokes `check-runtime-agents.cjs`, never prints the pass line.
- V1: unchanged — same checker argv and messages.
- Section 9a probes and 9b `github_ro` stay active and fatal.

## Retained V2 invariants

One scoped `@cortexkit/opencode-magic-context@~x.y.z` pin (unscoped rejected);
one fallback fork ref naming its directory or `/index.ts`; global
`permission.grep=deny` plus orchestrator `allow`; `mcp.github_ro` present and
`tools["github_ro_*"] === false`. The adapter emits no stdout and reads nothing
under `scripts/`.

## Recorded advice

`adversarial-reviewer` (verifier-contract surface) returned GAPS and required
the incomplete state, the fails-over-skips rule, section 9b staying fatal, and
rejecting unscoped pins. Its list of coverage now explicitly absent (model/tool/
GGA fallback, custom-agent grants, PM model drift, live fallback policy) is
deferred to Q130 and reported as incomplete, never as verified.

`security-reviewer` (earlier round) returned DESIGN GAPS on projection:
name-based exemptions and rule ordering, which is part of why projection was
abandoned for the skip branch.

## Planner handoff — structurally blocked

`docs/specs/pm-handoff.md:74` mandates `BLOCKED` when a worktree's HEAD lives
under `.git/worktrees/`, which is this checkout. Work ran as direct bounded
`general` writer dispatches with advisor input.

## Checks observed

- `tests/test_verifier_v2_sections.py` → 13 passed; controls assert skip-only
  exit 3, failures+skips exit 1, clean exit 0 with the unchanged banner, the
  plugin's exit-3 catch, and no cache-prune approval on incomplete.
- `python3 scripts/verifier_manifest.py check` → `ok: manifest and pin are
  current`; no `__pycache__`/`.pyc` row.
- `bash -n` on `verify-workflow.sh` and `verify/62-section-11-summary.sh` →
  exit 0.
- Not run: live `--behavioral` verifier, native review, reviewers (excluded).

## Open items

- **Native review due, not started** — `5beff94..90ccb14` assessed `high`
  (lineage `review-e460198a780543cd`); later commits not re-assessed.
- **Protected-path follow-up (owner).** `scripts/verifier_manifest.py` (S17)
  filters only `is_file()`, so `__pycache__` under `verify/checkers` becomes a
  required module despite `.gitignore`. Patch both comprehensions with
  `"__pycache__" not in p.relative_to(base).parts and p.suffix != ".pyc"`.
- **Q130** owns the V2 runtime-agent sweep.

## Next step

Tier 2: live V2 run, expecting exit 3, the named skip, and section 10 reached.
Owner: `verifier_manifest.py` bytecode filter.


## Revisions
- r1 2026-11-08T07:04:51Z gentle-orchestrator: Open Q115 unit: V2-mode verifier derivation, section 9 adapter, github_ro classification
- r2 2026-11-08T08:34:43Z gentle-orchestrator: Record Q115 commits 90ccb14 + 96a2d50, observed checks, review-due state and the protected-path follow-up
- r3 2026-11-08T10:38:50Z gentle-orchestrator: Record 63d2b0d and the F1/F2 resolution, checks, and residual risks
- r4 2026-11-08T11:16:26Z gentle-orchestrator: Record a5e3ada, the advisor's DESIGN GAPS advice, the blocked Planner handoff, and observed checks
- r5 2026-11-08T14:38:31Z gentle-orchestrator: Record narrowed skip scope, 88b296a + a9d1805, advisor GAPS advice, planner block and observed checks
- r6 2026-11-08T14:59:02Z gentle-orchestrator: Record 108c519, the exit-code contract, plugin exit-3 handling and observed controls
