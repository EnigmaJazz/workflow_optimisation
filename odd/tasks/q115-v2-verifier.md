# Q115 — V2-mode verifier: named section 9 skip

## Current outcome

V2 mode skips section 9's V1 checker with a named line, reports an explicit
incomplete status (exit 3), and V1 behaviour is unchanged. Native review
approved the candidate and the receipt was acknowledged.

## Commits on `chore/q115-v2-verifier`

- `90ccb14` — V2-aware env derivation, `github_ro` stdout fix, docs.
- `96a2d50` — manifest regenerated without the bytecode row.
- `63d2b0d` — Tier 4 F1/F2 (V2 agent constructs, V1 override surface).
- `a5e3ada` — Tier 4 F1 recheck (derivation-exact projection).
- `88b296a` — narrowed scope: projection removed, named skip,
  `VERIFICATION_INCOMPLETE`.
- `a9d1805` — `SKIPPED_MESSAGES` initialization for `set -u`.
- `108c519` — distinct exit status 3 for an incomplete run.
- `f0906e1` — native review R3-001: restore the V1 cache-prune message.

## Native review (2026-11-08)

- Assessment: `high` risk (`process_boundary`, `shell_source` on
  `verify-workflow.sh`), base `5beff94`, 14 paths / 574 lines.
- Lineage `review-63500602d1322b81`, initial target
  `sha256:f5d7f77d`, base tree `8f823f41`.
- Lenses: `review-risk`, `review-resilience`, `review-reliability`
  (risk and resilience for the shell/security boundary, reliability for the
  incomplete-versus-failed status contract).
- Refuter: `correction_required` with one CRITICAL, `R3-001`.

### R3-001 (CRITICAL, corrected)

Splitting the cache-prune gate on skips had reworded the shared message, so a
V1 failure-only run claimed "or required checks were skipped" — a false cause
and an unrequested change to V1 output. Fixed in `f0906e1`: failures print the
original V1 text byte-for-byte, skip-only prints its own line, and a run with
both reports the failure. Three cases pinned by tests.

### Advisory findings (non-blocking, informational)

- `R3-002` — `WORKFLOW_VERIFY_AGENTS_FILE` / `..._RUNTIME_CONFIG_FILE` are
  silently ignored in V1; documented V2 scope, but an operator gets no notice.
- `R3-003` — V2 derivation tests inject `VERIFY_ENTRY_PATH`; the `$0` fallback
  the entry actually uses is untested.
- `R3-004` — the section-9 V2 control builds its script with `str.replace`, which
  would silently no-op if the production fragments drift.
- `R3-005` — node `EACCES` converts to a skip, so an environment without node
  reports skipped rather than failed coverage.
- `R3-006` — `detect()` returns only the last stdout line, hiding extra output.
- `R4-001` — bare-name invocation via `PATH` makes `dirname` yield `.` and can
  point the workspace at the caller's directory.
- `R4-002` — the derivation failure exits 2, outside the documented 0/1/3
  contract.
- `R4-003` — the plugin's success-path `VERIFICATION_INCOMPLETE` branch is
  unreachable under the new contract.

### Outcome

`state: approved`; acknowledgement accepted with
`consumed_revision sha256:54010f00…`, target `sha256:2aac4014…`, authority
burned. No follow-up correction was opened.

## Exit-code contract

| Run state | Status | Banner |
| --- | --- | --- |
| clean | 0 | `== All checks passed — workflow setup intact ==` |
| incomplete (section 9 skipped) | 3 | `VERIFICATION_INCOMPLETE` |
| any failure | 1 | `Some checks failed` + list |

`verify-workflow.sh` is a 157-line loader; `62-section-11-summary.sh` runs last,
so its exit status is the script's.

## Section 9 behaviour

V2 runs the standalone invariant validator, prints one
`SKIPPED (V2: SECTION_9_RUNTIME_AGENT_CHECKER_NOT_RUN; ...)` line, and never
invokes `check-runtime-agents.cjs`; V1 is unchanged; 9a probes and 9b
`github_ro` stay fatal.

## Checks observed

- `tests/test_verifier_v2_sections.py` → 14 passed after `f0906e1`.
- `python3 scripts/verifier_manifest.py check` → `ok: manifest and pin are
  current`; no `__pycache__`/`.pyc` row.
- `bash -n` clean on the entry and every changed module.
- Not run: live `--behavioral` run (Tier 2).

## Open items

- **Protected-path follow-up (owner).** `scripts/verifier_manifest.py` (S17)
  filters only `is_file()`, so `__pycache__` under `verify/checkers` becomes a
  required module despite `.gitignore`. Patch both comprehensions with
  `"__pycache__" not in p.relative_to(base).parts and p.suffix != ".pyc"`.
- **Q130** owns the V2 runtime-agent sweep.
- Advisory findings above are separate later work, not reasons to re-run review
  on this candidate.

## Next step

Tier 2: live V2 run expecting exit 3 with the named skip. Owner: the
`verifier_manifest.py` bytecode filter.


## Revisions
- r1 2026-11-08T07:04:51Z gentle-orchestrator: Open Q115 unit: V2-mode verifier derivation, section 9 adapter, github_ro classification
- r2 2026-11-08T08:34:43Z gentle-orchestrator: Record Q115 commits 90ccb14 + 96a2d50, observed checks, review-due state and the protected-path follow-up
- r3 2026-11-08T10:38:50Z gentle-orchestrator: Record 63d2b0d and the F1/F2 resolution, checks, and residual risks
- r4 2026-11-08T11:16:26Z gentle-orchestrator: Record a5e3ada, the advisor's DESIGN GAPS advice, the blocked Planner handoff, and observed checks
- r5 2026-11-08T14:38:31Z gentle-orchestrator: Record narrowed skip scope, 88b296a + a9d1805, advisor GAPS advice, planner block and observed checks
- r6 2026-11-08T14:59:02Z gentle-orchestrator: Record 108c519, the exit-code contract, plugin exit-3 handling and observed controls
- r7 2026-11-08T15:22:33Z gentle-orchestrator: Record native review lineage, R3-001 correction f0906e1, advisory findings and acknowledgement
