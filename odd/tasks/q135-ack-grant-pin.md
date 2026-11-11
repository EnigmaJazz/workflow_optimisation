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
| T1 | New pinning test `tests/test_acknowledge_grant_pin.py`: source and derived-V2 holder sets, every other agent resolves deny/absent, positive controls for a fourth agent (allow, ask, wildcard) and for a coordinator losing its exact allow | done | 4 tests; RED-1 marker-missing, RED-2 exact+wildcard ask, GREEN (see Evidence) |
| T2 | Tighten the `verify/checkers/check-runtime-agents.cjs` non-coordinator sweep from "not allow" to "deny or absent", behind an `acknowledge-grant-policy` marker block the test executes | done | one marker pair, one definition per function, sweep `resolved !== undefined && resolved !== "deny"`, synthetic-ask + omitted controls; Bun whole-file parse gate passed |
| T3 | Re-pin: `python3 scripts/verifier_manifest.py update`, then `check` | done | `ok: manifest and pin are current` |
| T4 | State the holder set, the owner decision and the rationale in `WORKFLOW.md` (review-relay section) | done | one paragraph inside the `workflow.review-relay` anchor |

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
route: workflow-odd-secure | specialist: `pm-odd` then, after its structural block, one direct `general`
sandbox writer | basis: WORKFLOW.md.

Tier 2 correction 2026-11-11 routed the work through `pm-odd` (substantial ODD unit; a linked worktree is not
a blocker under the current `docs/specs/pm-handoff.md`). `pm-odd` validated the class/route, passed the
unit-start anchor, dispatched the Planner, and its Planner issued Gate 1 PASS with security and specification
pre-code advice read. `pm-odd` then returned `BLOCKED / REQUIRED_WRITER_SURFACE_UNAVAILABLE`: in this runtime
its subagent surface exposes only `advisor-*`, `explore`, `gentle-ai-verify`, `gentle-ai-verify-routine` and
`planner`, so neither `odd-apply` nor `gentle-ai-worker` can be dispatched by the PM. Tier 2 accepted a direct
`general` writer as a sanctioned exception (same form as Q102 P1a); `general` is `openai/gpt-6-luna`,
independent of the DeepSeek orchestrator.

Advice budget: enforcement-test/security unit → one pre-advice phase, one post-code check, one independent
verifier. Pre-code: Planner-run security + specification advisors (Gate 1 PASS). Post-code: `advisor-security-post`
plus the independent `gentle-ai-verify` high-risk seat.

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

### Writer sequencing and advisor finding dispositions

1. **T1 first; missing-marker RED.** The first failure must identify `acknowledge-grant-policy marker block is missing`, not an import/runtime/config error. Mutation controls check rejection by non-empty failures. Runtime skipping is allowed when neither runtime exists, but skipped execution is NOT GREEN evidence.
2. **Mechanical extraction; ask-only RED.** Expose the NEW sweep name `acknowledgeGrantOutsideFailures` while retaining the OLD `resolved === "allow"` behavior and old failure strings; migrate the five call-site names so the intermediate file stays coherent. Do not add the synthetic-ask self-control until the tightening step. The ask-family controls must fail; the others must pass.
3. **Final T2; GREEN.** Apply the exact sweep, update the five expected strings, add `synthetic-ask` detection with a named `...POSITIVE_CONTROL_FAILED` failure. Ordered-deny, explicit deny and omitted controls must yield no failures.
4. **T2 isolation.** One contiguous block after the sandbox-mutation defaults loop; only the five functions in contract order; `globPatternMatches`/`resolvedPermissionValue` unchanged; only `acknowledgeGrantShow` inside; no `fail`/`show`/`cfgPerm`/`cfgTool`; delete the originals; move the probe after the block; preserve the EXACT explicit-own-key allow requirement. Verify one marker pair, one definition per function, zero old sweep-name references, five call sites updated.
5. **T1 acceptance.** Cover exact AND wildcard ask in one ask-family test with isolated deep copies. Retain every listed positive/negative control. Every coordinator must both have an exact allow and resolve allow; every other agent must resolve deny/absent. Assert identical holder sets in source and derived configs; call BOTH `derive_config` and `add_v2_astra_aliases`; no `-astra` alias silently whitelisted; the live-config docstring is mandatory.
6. **T4 then T3.** One paragraph inside the review-relay anchor; after final checker bytes run manifest `update` then `check`; never hand-edit manifest or pin.
7. **Required final executions.** `node --check`, focused unittest, full suite; retain verbatim outputs. Where node is unavailable, a whole-file Bun build with `--target=node --no-bundle` is recorded as a parse gate, never as node verification.

### Initial post-code batch, Gate 2 and owner handoff

- PM owns writer dispatch; Planner dispatches neither writer nor native review lens. Require the writer's changed-path inventory, both REDs, focused GREEN, full test output, syntax check, manifest output and reviewability receipt. No claimed execution is accepted from skipped tests, parse-only output or a different candidate.
- On the SAME INITIAL candidate: one security post-code check, the single independent high-risk `gentle-ai-verify`, and static diagnostics covering every changed path, as one post-code check phase.
- Mandatory `advisor-spec-post` runs only after actual writer output and verifier evidence are available, before Gate 2.
- Batch all initial post-code findings before correction. At most ONE fresh correction writer. Regenerate affected pins and re-run targeted checks after correction.
- `sandbox_finish` then approval-gated `sandbox_apply`. If S17 refuses apply, preserve the frozen finished result and return its exact identity; do not retry, bypass, or commit. Leave the accepted applied diff UNCOMMITTED. No commit tool or native RDD operation is permitted in this unit.

### Deferred, non-blocking findings

Malformed/null/array/object-valued permissions beyond the specified controls (specification E1-E3, security O3) are out of scope: preserve the existing helper semantics; object-valued entries are ignored by resolution. No resolver redesign, tool-enablement pin, new holder, or derivation change. No planning-time test result is assumed.

## Evidence

- Writers: initial `general` writer applied five paths; one `general` correction writer repaired the checker
  (duplicate `const acknowledgeAskProbe`, corrupted `globPatternMatches` regex, missing `=` on
  `acknowledgeGlobThenDenyProbe`, and added the omitted-key negative control). Correction diff: 3 files,
  6 insertions, 11 deletions.
- RED-1 (test only): `AssertionError: acknowledge-grant-policy marker block is missing: substring not found`
  — `Ran 0 tests`, `FAILED (errors=1)`.
- RED-2 (behavior-preserving extraction): only `exact ask` and `wildcard ask` fourth-agent controls failed —
  `AssertionError: [] is not true : positive control failed to detect exact ask` / `... wildcard ask`;
  `Ran 4 tests`, `FAILED (failures=2)`.
- GREEN (tightened sweep): `Ran 4 tests in 0.906s`, `OK`. Independently re-run by the verifier:
  `Ran 4 tests in 0.987s`, `OK`; by the regression worker: `Ran 4 tests`, `OK`.
- Manifest: `manifest regenerated`, `plugin pin updated`, then `ok: manifest and pin are current`.
- Syntax: `node --check` is unavailable in the sandbox (`PermissionError`/EACCES on `node`); a whole-file
  `bun build verify/checkers/check-runtime-agents.cjs --target=node --no-bundle` transpiled successfully
  (166.36 KB), recorded as a parse gate, not node verification. `tests/test_verifier_split.py`'s
  `test_checkers_are_valid_scripts` errors only because it shells out to `node`.
- Independent verifier (`gentle-ai-verify`, high-risk seat): PASS. Observed exactly the five authorized paths
  (198 insertions, 31 deletions) against parent `b91b728`; one marker pair; one definition per function; one
  `const acknowledgeAskProbe`; sweep condition exact; exact-key coordinator enforcement intact; probe strings
  match emitted diagnostics; no agent outside the three resolves `allow`; `global-config/opencode.json` untouched.
- Post-code security advisor raised two CRITICALs claiming the coordinator check accepted a wildcard-only
  allow. REFUTED: `hostReviewAcknowledgeAllowFailures` uses `Object.prototype.hasOwnProperty.call(permission,
  "host_review_acknowledge_approved")` and does not call `resolvedPermissionValue`; the GREEN run includes the
  `pm-odd` wildcard-only control and passes. Recorded as a refuted advisory, not acted on.
- Regression modules: `test_anchor_manifest` 21 OK; `test_review_cadence` 2 OK; `test_v2_config` 9 OK;
  `test_derive_v2_config` 76 OK (9 skipped); `test_grok_seat_policy` 13 OK (1 skipped);
  `test_pm_git_head_grants` 5 OK; `test_acknowledge_grant_pin` 4 OK. `test_orchestrator_prompt_source` 44 tests
  with 1 failure (`test_nonprompt_config_tree_matches_the_pinned_digest`), the known baseline failure on main.
- Full suite in this sandbox is environment-limited: `test_opencode_v2_db_swap` reports `sqlite3 is not
  installed`; `test_codegraph_ensure` creates temp dirs under `/nonexistent`; `test_cli_config_mirror` errors in
  Python 3.13 dataclass handling; `test_verifier_split` needs `node`. None touches the changed surfaces.
- Static diagnostics: Pyright reports 5 typing complaints in the new test (`spec_from_file_location` returns
  `ModuleSpec | None`; `cls.runtime` is `str | None`). Non-blocking and identical to the existing
  `test_pm_git_head_grants.py` pattern; runtime is guarded by the skip check.
- Gate 2 is NOT obtained: the PM layer cannot dispatch a writer in this runtime and the unit makes no commit,
  so the pre-commit Gate 2 step has no candidate to gate. The owner's Tier 4 Codex review with a SECURITY
  section is the next gate before merge.

## Owner commit list (one commit, no partial commit)

`tests/test_acknowledge_grant_pin.py`, `verify/checkers/check-runtime-agents.cjs`, `verify-workflow.sh`,
`global-config/plugins/workflow-health-check.ts`, `WORKFLOW.md`.

## Log

- Created before the first implementation edit. Pre-code advice (`advisor-security-pre`) findings applied:
  add a coordinator-with-wildcard-only control; stage test-first as behavior-preserving extraction first, then
  the tightening, so the RED is behavioral rather than "marker missing"; do not let derived `-astra` aliases
  become extra holders silently.
- 2026-11-11 Tier 2 routing correction: substantial ODD units route through `pm-odd`. The earlier claim that
  `pm-handoff` blocks linked worktrees was wrong; the current contract states "A linked worktree is supported
  and is NOT a blocker".
- 2026-11-11 Planner finalised the T1-T4 plan and read the formal security + specification pre-code advice;
  Gate 1 PASS. `pm-odd` then returned `BLOCKED / REQUIRED_WRITER_SURFACE_UNAVAILABLE` because no PM-dispatchable
  writer exists in this runtime. Tier 2 accepted the direct `general` writer fallback as a sanctioned exception
  (Q102 P1a form); recorded here as instructed.
- 2026-11-11 Implementation and one correction round complete; verifier PASS; no commit made. Deliverable is
  the applied, uncommitted diff and the owner commit list above.


## Revisions
- r1 2026-11-11T22:15:23Z gentle-orchestrator: Create Q135 tracker: pin the acknowledge-approved grant (owner decision 2026-11-10 item 8).
- r2 2026-11-11T22:19:55Z gentle-orchestrator: Record Tier 2 routing correction (pm-odd, worktree supported) and the authoritative implementation contract.
- r3 2026-11-11T22:38:06Z planner: Finalise T1-T4 plan and formal advice dispositions; preserve verbatim contract. Broker retains managed revision log.
- r4 2026-11-11T23:58:47Z gentle-orchestrator: Close T1-T4 with RED/GREEN, verifier PASS, refuted advisor finding, owner commit list, and the Tier 2 sanctioned-exception record.

## Gates
- q135-ack-grant-pin-u1 PASS 2026-11-11T22:39:16Z planner ref=odd/tasks/q135-ack-grant-pin.md r3, Finalised unit plan T1-T4; raw security/spec pre-advice read; security B1 and spec B1-B6 resolved; node availability deferred to actual writer execution.
