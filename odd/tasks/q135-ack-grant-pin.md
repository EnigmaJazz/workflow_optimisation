# Q135 — pin the `host_review_acknowledge_approved` grant

**Objective:** make the owner's 2026-11-10 decision (item 8, verbatim: "Yes allow, does not need to ask")
executable: `host_review_acknowledge_approved` is `allow` for exactly `gentle-orchestrator`, `pm-odd` and
`pm-systematic`, and `deny` by global default for every other agent. Rationale: acknowledgement only burns
the authority the provider already issued for the exact lineage, and consent was given earlier, so an `ask`
gate stalls an approved review for no benefit.

**Branch:** `feat/q135-ack-grant-pin` (worktree `~/ai-workspace/worktrees/workflow_optimisation/q135-ack-grant-pin`),
off `main` `f1cbf3c`. The grant itself is already in `global-config/opencode.json`; this unit adds the evidence and pins it.

**Delivery:** the owner commits. `scripts/**` and the verifier manifest (`VERIFY_MODULES` in
`verify-workflow.sh` plus the `VERIFY_SCRIPT_SHA256` pin in `global-config/plugins/workflow-health-check.ts`)
are S17-protected, so the unit leaves its diff applied and uncommitted for the owner, with no partial commit
(HEAD must never reference a checker the manifest has not pinned).

**Test runner:** `python3 -m unittest discover -s tests -p 'test_acknowledge_grant_pin.py' -v`, then
`python3 -m unittest discover -s tests`. Bun suites, if run, use a temporary `HOME`.

**Risk:** item 2 (permissions) → Tier 4 Codex review with a SECURITY section before merge.

## Tasks

| ID | Task | Status | Evidence |
|---|---|---|---|
| T1 | New pinning test `tests/test_acknowledge_grant_pin.py`: source and derived-V2 holder sets, every other agent resolves deny/absent, positive controls for a fourth agent (allow, ask, wildcard) and for a coordinator losing its exact allow | pending | |
| T2 | Tighten the `verify/checkers/check-runtime-agents.cjs` non-coordinator sweep from "not allow" to "deny or absent", behind an `acknowledge-grant-policy` marker block the test executes | pending | |
| T3 | Re-pin: `python3 scripts/verifier_manifest.py update`, then `check` | pending | |
| T4 | State the holder set, the owner decision and the rationale in `WORKFLOW.md` (review-relay section) | pending | |

## Acceptance criteria

- The source config and the derived V2 config expose exactly the three holders; the set of agents resolving
  `allow` equals the three, and every other agent resolves `deny` or has no rule (inherits the global `deny`).
- The test fails when a fourth agent receives `allow` or `ask` (exact or wildcard), when one of the three loses
  its exact `allow` (removed, `ask`, or wildcard-only), and when the global default leaves `deny`.
- `python3 scripts/verifier_manifest.py check` reports the manifest and pin current.
- The three coordinators keep an exact explicit key: a wildcard alone never satisfies the coordinator check.

## Authorized scope

`tests/test_acknowledge_grant_pin.py`, `verify/checkers/check-runtime-agents.cjs`, `verify-workflow.sh` (manifest
regeneration only), `global-config/plugins/workflow-health-check.ts` (pin regeneration only), `WORKFLOW.md`.
No change to `global-config/opencode.json` and no change to the grant itself. No commits in this unit.

## Route and trigger evidence

ROUTE: Global tooling change (permission pin + verifier enforcement test + docs) | intent: authorized change |
route: workflow-odd-secure | specialist: `pm-odd`, which dispatches the ODD writer and owns Planner/advisor
handoff | basis: WORKFLOW.md. Dispatched as a substantial ODD unit per Tier 2 correction (2026-11-11):
substantial ODD units route through `pm-odd`; direct `general` dispatch is not used.

Advice budget: enforcement-test/security unit → one pre-advice phase, one post-code check, one independent
verifier (`gentle-ai-verify`, high-risk seat). The orchestrator's earlier `advisor-security-pre` answer is a
pre-dispatch input only; the PM/Planner own the formal pre-code advice phase.

## Implementation contract

Authoritative for the writer brief; the PM must forward it verbatim.

### T1 — `tests/test_acknowledge_grant_pin.py`

Pattern: mirror `tests/test_pm_git_head_grants.py` (config pin + derivation + mutation controls) and
`tests/test_grok_seat_policy.py` (extract a delimited block from `verify/checkers/check-runtime-agents.cjs`
and execute it with node/bun).

- Constants: `REPO`, `CHECKER`, `CONFIG`, `DERIVE`, `TOOL="host_review_acknowledge_approved"`,
  `COORDINATORS=("gentle-orchestrator","pm-odd","pm-systematic")`, markers
  `// acknowledge-grant-policy:begin` / `// acknowledge-grant-policy:end`.
- `build_policy(checker_source, runtime)` extracts the block and appends a harness reading JSON from stdin:
  `mode=coordinator` → `hostReviewAcknowledgeAllowFailures(agent)`;
  `mode=outside` → `acknowledgeGrantOutsideFailures(agents, allowed)`;
  `mode=resolved` → per-agent `resolvedPermissionValue(agent, "host_review_acknowledge_approved")`.
  Runtime: `shutil.which("node") or shutil.which("bun")`; skip when neither exists.
- Derivation: `importlib` load of `scripts/derive-v2-config.py`; `derive_config(source, fork_dir=<tempdir with
  package.json {"exports":{}}>, fork_ref="/v2/vendor/opencode-rate-limit-fallback-mapped")`, then
  `add_v2_astra_aliases(config)`.
- `check(config, allowed=COORDINATORS)`: global `permission.<TOOL> == "deny"`; each coordinator passes
  `hostReviewAcknowledgeAllowFailures`; `acknowledgeGrantOutsideFailures(agents, allowed) == []`.
- Tests: source config clean and holders set equals the three; every non-coordinator resolves `None`/`"deny"`;
  derived V2 config clean with the same holder set (no `-astra` alias may carry the grant); positive controls on
  deep-copied configs — fourth agent `allow`, fourth agent `ask`, fourth agent `{"host_review_*": "allow"}`,
  `pm-odd` key removed, `pm-odd` set to `ask`, `pm-odd` wildcard-allow-only, global set to `allow`; negative
  controls — explicit `deny`, ordered `{"host_review_*": "allow", TOOL: "deny"}`, omitted key, string
  `permission: "deny"`.
- Docstring must state the test reads the live config, so a future legitimate holder updates the test in the
  same change.

### T2 — `verify/checkers/check-runtime-agents.cjs`

Move the acknowledge policy into one contiguous marker block placed immediately after the sandbox-mutation
default loop (after the line `for (const t of ["sandbox_apply",...]) ...` and before
`const registeredHostReads=[...]`). The block contains, in order, and nothing else: a local
`acknowledgeGrantShow(value)` (`value===undefined ? "<inherit/none>" : JSON.stringify(value)`), the existing
`globPatternMatches` and `resolvedPermissionValue` (moved unchanged from their current position), the existing
`hostReviewAcknowledgeAllowFailures` with `show(` replaced by `acknowledgeGrantShow(`, and the renamed sweep:

```js
function acknowledgeGrantOutsideFailures(agents, allowedAgents) {
  const failures = []
  const allowed = new Set(allowedAgents ?? [])
  for (const [name, agent] of Object.entries(agents ?? {})) {
    if (allowed.has(name)) continue
    const resolved = resolvedPermissionValue(agent, "host_review_acknowledge_approved")
    if (resolved !== undefined && resolved !== "deny") {
      failures.push(`HOST_REVIEW_ACKNOWLEDGE_NON_DENY_OUTSIDE_COORDINATORS: ${name}=${acknowledgeGrantShow(resolved)}`)
    }
  }
  return failures
}
```

Nothing inside the block may call `fail`, `show`, `cfgPerm`, `cfgTool` or any other file-level helper. The old
inline `acknowledgeAskProbe` lines move to immediately after the block, unchanged. Delete the old definitions
at their current positions. Update the five call sites of `acknowledgeAllowSweepFailures` to
`acknowledgeGrantOutsideFailures` and their expected strings to the new failure code, and add controls:
`synthetic-ask` must be reported (`...POSITIVE_CONTROL_FAILED`), ordered-deny, deny and omitted must report
nothing. The coordinator check at the later orchestrator section keeps calling
`hostReviewAcknowledgeAllowFailures` unchanged.

### T3 — manifest

After T2's final bytes: `python3 scripts/verifier_manifest.py update` (rewrites `verify-workflow.sh`, then the
pin in `global-config/plugins/workflow-health-check.ts`), then `python3 scripts/verifier_manifest.py check`
must print `ok: manifest and pin are current`. Never hand-edit either value.

### T4 — `WORKFLOW.md`

Add one paragraph to `### Secure fixed host tools and isolated review relay`, inside the
`workflow.review-relay` anchor block: `host_review_acknowledge_approved` is `allow` for exactly
`gentle-orchestrator`, `pm-odd` and `pm-systematic`, and `deny` by global default for every other agent (owner
decision 2026-11-10, item 8: "Yes allow, does not need to ask"); acknowledgement only burns the authority the
provider already issued for the exact lineage and consent was given earlier, so an `ask` gate stalls an
approved review for no benefit; the verifier pins the holder set and the global deny.

### Evidence sequence (test-first, two observable REDs)

1. Write T1 only; run it → RED "acknowledge-grant-policy marker block is missing".
2. Add the marker block as a behavior-preserving extraction (old sweep unchanged in semantics); run T1 →
   RED on the `ask` fourth-agent control only; record the exact failure.
3. Apply the tightened sweep and call sites; run T1 → GREEN.
4. T4, then T3 (`update`, `check`).
5. `node --check verify/checkers/check-runtime-agents.cjs`; full `python3 -m unittest discover -s tests`.
6. `sandbox_finish`, then `sandbox_apply` (human approval); report `git status --short`, `git diff --stat`, and
   the reviewability receipt.

## Log

- Created before the first implementation edit. Pre-code advice (`advisor-security-pre`) findings applied:
  add a coordinator-with-wildcard-only control; stage test-first as behavior-preserving extraction first, then
  the tightening, so the RED is behavioral rather than "marker missing"; do not let derived `-astra` aliases
  become extra holders silently.
- 2026-11-11 Tier 2 routing correction (supersedes the earlier route note): WORKFLOW.md:146 requires substantial
  ODD units to be dispatched to `pm-odd`; the unit is therefore handed to `pm-odd`, which dispatches the ODD
  writer and owns the Planner/advisor handoff. The cited rule that `pm-handoff` blocks worktree HEADs was
  removed: the current `docs/specs/pm-handoff.md` states "A linked worktree is supported and is NOT a blocker".
  This unit is substantial: T1-T4 are four implementation steps. It is an owner-commit unit (S17), so the PM
  must not commit and must record the applied candidate as the owner's to commit.


## Revisions
- r1 2026-11-11T22:15:23Z gentle-orchestrator: Create Q135 tracker: pin the acknowledge-approved grant (owner decision 2026-11-10 item 8).
- r2 2026-11-11T22:19:55Z gentle-orchestrator: Record Tier 2 routing correction (pm-odd, worktree supported) and the authoritative implementation contract.
