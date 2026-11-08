# Q115 — V2-mode verifier reads V2 paths and this checkout

## Objective

With OpenCode V2 first on `PATH`, `verify-workflow.sh` must derive its config
surface and workspace from V2 and from the checkout that contains the script,
must not fail on V1-only shapes in section 9, must classify the `github_ro`
probe correctly, and must reach section 10 with no failures from these items.
Acceptance remains Tier 2's live host run against the V2 server.

## Commits on `chore/q115-v2-verifier`

- `90ccb14` — V2-aware env derivation, section 9 projection, `github_ro` fix.
- `96a2d50` — regenerated manifest without the bytecode row.
- `63d2b0d` — Tier 4 F1/F2: V2 agent constructs and V1 override surface.
- `a5e3ada` — Tier 4 F1 recheck: derivation-exact projection removal.

## F1 (final) — projection must not hide grants

The earlier fix erased any entry whose rules were all `sandbox_`/`host_`
prefixed. An overlay could add a prefix-only entry granting
`host_review_acknowledge_approved`, have it erased, and never reach
`check-runtime-agents.cjs:1147` →
`HOST_REVIEW_ACKNOWLEDGE_ALLOW_OUTSIDE_COORDINATORS` (:1048-1057).

Now an entry is removed only when it is exactly what
`scripts/derive-v2-config.py` generates for that name:

- mirror: equals the prefixed rule subset of its declared `ACCESS_MIRRORS`
  reference;
- alias: equals the deep copy `add_v2_astra_aliases` builds for a base that
  `astra_alias_wanted` accepts.

The derivation is imported by path (no duplicated constants), and comparison is
order-sensitive JSON equality. Everything else stays in the projected
inventory, so extra grants, changed values, reordered rules and ineligible
bases all remain visible to every sweep. The module docstring records the
equivalence argument: a removed entry holds no grant absent from a still
projected reference or base, in the same rule order.

## Advisor on the security surface (recorded before the writer)

`security-reviewer` returned **DESIGN GAPS** on the first exact-match design,
and both gaps changed the implementation:

1. Name-based exemptions. An exact alias can inherit a grant that is legal for
   its base name but not for the alias name — e.g. `planner-astra` inheriting
   `host_plan_write: ask` although only the exact `planner` name joins the
   allowed plan writers, and a coordinator switched to Sol with `mode` omitted.
   Resolved by requiring derivation-exact equality plus the base/reference
   remaining projected and swept.
2. Rule ordering. `check-runtime-agents.cjs:1037-1046` resolves last-match-wins,
   so dict `==` treats `host_review_*: allow` then `…acknowledge…: deny` as
   equal to the reverse order, which has opposite authority. Resolved by
   order-sensitive `json.dumps(..., sort_keys=False)` comparison.

The advisor also enumerated 17 further `deployedAgents` sweeps that erasure
would bypass (`:358-367`, `:376-380`, `:1000-1004`, `:1080-1088`, `:1089-1098`,
`:1165-1180`, `:1328-1331`, `:1336-1346`, `:1378-1441`, `:1548-1557`,
`:180-191`, `:1579-1620`, `:1726-1727`, `:1815-1832`, `:1927-1930`,
`:1964-1980`, `:2426-2431`), which is why the fix restricts removal rather than
adding one targeted check.

## Planner handoff — structurally blocked

`docs/specs/pm-handoff.md:74` mandates `BLOCKED` when a worktree's HEAD lives
under `.git/worktrees/`; this checkout's `.git` is a file pointing at
`.../worktrees/q109-q106`, so the Planner handoff cannot emit a plan here. Work
ran as direct bounded `general` writer dispatches with the advisor advice as
the pre-code input.

## F2 (closed by Tier 4)

`derive_workspace_paths` assigns plain `$WORKSPACE`-anchored values again,
keeping only the two pre-existing overrides; the `AGENTS_FILE` and
`RUNTIME_CONFIG_FILE` overrides apply only in the V2 branch.

## Checks observed

- `python3 -m pytest tests/test_verifier_v2_sections.py
  tests/test_verifier_v2_mode.py tests/test_verifier_v2_github_mcp.py -q` →
  `55 passed, 15 skipped`, no failures.
- Sections suite alone → `13 passed, 1 skipped`; skip reason `node could not
  be spawned: [Errno 13] Permission denied: 'node'`.
- Targeted bypass fixture → passes; the `correctness-reviewer` entry with
  `host_review_acknowledge_approved` remains in the projection.
- `python3 scripts/verifier_manifest.py check` → `ok: manifest and pin are
  current`; no `__pycache__`/`.pyc` row.
- `bash -n verify-workflow.sh` → exit 0.
- Not run: live `--behavioral` verifier, native review, reviewers — excluded by
  the dispatch.

## Open items

- **Native review due, not started** — assessment for `5beff94..90ccb14` was
  `high` (lineage `review-e460198a780543cd`); not re-assessed for later
  commits, per the "do not run native review" constraint.
- **Protected-path follow-up (owner).** `scripts/verifier_manifest.py` (S17)
  `render()`/`drift()` filter only by `is_file()`, so `__pycache__` under
  `verify/checkers` becomes a required module despite `.gitignore`. Patch both
  comprehensions with `"__pycache__" not in p.relative_to(base).parts and
  p.suffix != ".pyc"`.
- **Residual:** a mirror-named entry that differs from the derivation in any
  respect is intentionally left visible to the checker, so a legitimate but
  non-derived overlay on a Systematic agent name will surface as
  `SYSTEMATIC_AGENT_SHADOWED` rather than being silently projected away.

## Next step

Tier 2: live V2 acceptance run. Owner: `verifier_manifest.py` bytecode filter.


## Revisions
- r1 2026-11-08T07:04:51Z gentle-orchestrator: Open Q115 unit: V2-mode verifier derivation, section 9 adapter, github_ro classification
- r2 2026-11-08T08:34:43Z gentle-orchestrator: Record Q115 commits 90ccb14 + 96a2d50, observed checks, review-due state and the protected-path follow-up
- r3 2026-11-08T10:38:50Z gentle-orchestrator: Record 63d2b0d and the F1/F2 resolution, checks, and residual risks
- r4 2026-11-08T11:16:26Z gentle-orchestrator: Record a5e3ada, the advisor's DESIGN GAPS advice, the blocked Planner handoff, and observed checks
