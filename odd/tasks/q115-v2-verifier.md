# Q115 — V2-mode verifier: named section 9 skip

## Outcome (current)

V2 mode no longer projects the derived config into the V1 section-9 checker.
Section 9 reports a named skip, and the run reports `VERIFICATION_INCOMPLETE`
rather than all-passed. V1 mode output is unchanged.

## Owner narrowing (2026-11-08)

After the correction bound was reached, the owner chose the SKIP branch:
"make section 9 V2-aware or skip it with an explicit reason; keep positive
controls so a V1-only pass cannot hide a V2 gap." Projection was dropped
because removing entries before identity-keyed sweeps loses identity, and
because the by-path import of `scripts/derive-v2-config.py` executed a file
outside the digest manifest.

## Commits on `chore/q115-v2-verifier`

- `90ccb14` — V2-aware env derivation, `github_ro` stdout fix, docs.
- `96a2d50` — manifest regenerated without the bytecode row.
- `63d2b0d` — Tier 4 F1/F2 (V2 agent constructs, V1 override surface).
- `a5e3ada` — Tier 4 F1 recheck (derivation-exact projection).
- `88b296a` — **narrowed scope**: projection removed, named skip,
  `VERIFICATION_INCOMPLETE` state.
- `a9d1805` — `SKIPPED_MESSAGES` initialization for `set -u`.

## What section 9 does now

- V2: runs `checkers/v2-runtime-config.py` as a standalone validator, then
  prints exactly one line
  `SKIPPED (V2: SECTION_9_RUNTIME_AGENT_CHECKER_NOT_RUN; ...)` and never
  invokes `check-runtime-agents.cjs` and never prints the pass line.
- V1: unchanged — same `RUNTIME_CHECK_CONFIG`, same checker argv, same
  `ok:`/`fail` messages.
- Section 9a probes and the V2 registration probes stay fatal; section 9b
  `github_ro` stays active and fatal.

## Retained V2 invariants (no V1 checker input)

Exactly one `@cortexkit/opencode-magic-context@~x.y.z` pin (unscoped rejected);
exactly one fallback fork ref naming its vendor directory or `/index.ts`;
global `permission.grep=deny` plus `gentle-orchestrator` `allow`;
`mcp.github_ro` present and `tools["github_ro_*"] === false`. The adapter emits
**no stdout**, so nothing can be piped into an identity-sensitive checker, and
it reads nothing under `scripts/`.

## Skip cannot read as a pass

`skip()` records into `SKIPPED_MESSAGES` and prints the named line. The summary
refuses the all-passed banner, prints `VERIFICATION_INCOMPLETE` with every
skipped check, and withholds the cache-prune approval. The health plugin gained
an `incomplete` state (`workflow-health-check.ts:94,146-157,237`) instead of
reporting clean. Failures win over skips: they are listed and `exit 1` even
when a skip is present.

## Advisor on the verifier-contract surface (recorded before the writer)

`adversarial-reviewer` returned **GAPS**: an echo-only skip would still print
"All checks passed" and exit 0, because `62-section-11-summary.sh:13-28` reads
`FAIL`/`AUTO_REPAIRED` only; the health plugin (`:134-160`) classifies a
successful subprocess as clean from banner text. Both shaped the design above.
It also required that section 9b stay fatal, that the pin regex reject unscoped
refs, and that removed coverage be named rather than implied.

## Advisor-identified coverage now explicitly absent (deferred to Q130)

Model/tool/GGA fallback validation; custom-agent grants such as
`host_plan_write: allow` or `host_review_acknowledge_approved: allow`;
PM model drift; live fallback policy. These are reported as incomplete, never
as verified.

## Planner handoff — structurally blocked

`docs/specs/pm-handoff.md:74` mandates `BLOCKED` when a worktree's HEAD lives
under `.git/worktrees/`, which is this checkout. Work ran as direct bounded
`general` writer dispatches with the advisor advice as pre-code input.

## Checks observed

- `python3 -m pytest tests/test_verifier_v2_sections.py -q` → `12 passed`.
- Broader suite during implementation → `51 passed, 14 skipped`; skips are the
  sandbox's `node` spawn `EACCES` (host has `/usr/bin/node`).
- `python3 scripts/verifier_manifest.py check` → `ok: manifest and pin are
  current`; no `__pycache__`/`.pyc` row.
- `bash -n` on every changed module → exit 0.
- Executed V2 fragment → one `SKIPPED (V2: SECTION_9_RUNTIME_AGENT_CHECKER_NOT_RUN ...)`,
  no checker invocation, no pass line.
- Executed V1 fragment → `checker invoked=True skip printed=False`.
- Summary controls → failures+skips exit 1 with the failed check listed;
  skips only exit 0 incomplete; empty run keeps
  `== All checks passed — workflow setup intact ==`.
- Not run: live `--behavioral` verifier, native review, reviewers (excluded).

## Open items

- **Native review due, not started** — assessment for `5beff94..90ccb14` was
  `high` (lineage `review-e460198a780543cd`); later commits not re-assessed per
  the constraint.
- **Protected-path follow-up (owner).** `scripts/verifier_manifest.py` (S17)
  filters only `is_file()`, so `__pycache__` under `verify/checkers` becomes a
  required module despite `.gitignore`. Patch both comprehensions with
  `"__pycache__" not in p.relative_to(base).parts and p.suffix != ".pyc"`.
- **Q130** owns the V2 runtime-agent sweep; do not start it here.

## Next step

Tier 2: live V2 run, expecting section 10 reached, the named skip, and
`VERIFICATION_INCOMPLETE`. Owner: `verifier_manifest.py` bytecode filter.


## Revisions
- r1 2026-11-08T07:04:51Z gentle-orchestrator: Open Q115 unit: V2-mode verifier derivation, section 9 adapter, github_ro classification
- r2 2026-11-08T08:34:43Z gentle-orchestrator: Record Q115 commits 90ccb14 + 96a2d50, observed checks, review-due state and the protected-path follow-up
- r3 2026-11-08T10:38:50Z gentle-orchestrator: Record 63d2b0d and the F1/F2 resolution, checks, and residual risks
- r4 2026-11-08T11:16:26Z gentle-orchestrator: Record a5e3ada, the advisor's DESIGN GAPS advice, the blocked Planner handoff, and observed checks
- r5 2026-11-08T14:38:31Z gentle-orchestrator: Record narrowed skip scope, 88b296a + a9d1805, advisor GAPS advice, planner block and observed checks
