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

## Finalised unit plan — T1-T4

**Unit:** `q135-ack-grant-pin-u1`. **Plan status:** finalised for Gate 1; implementation and checks remain unexecuted by the Planner. This section supplements, never replaces, the verbatim Implementation contract above. The PM writer brief MUST include that entire section through its Evidence sequence verbatim, plus these clarifications. T1-T4 stay one atomic, OWNER-COMMIT unit: no commit operation, partial commit, push, PR, merge, deployment, or native RDD review. The owner separately arranges Tier 4 Codex review with a SECURITY section before merge. Allowed implementation paths remain exactly the five listed under Authorized scope; the tracker is the sole sanctioned planning/evidence update. Do not modify `global-config/opencode.json`, the existing grant, scripts, derivation logic, or other workflow artifacts.

### Evidence basis and selected advice

- Observed: `workflow-route`, `workflow-odd-secure`, `orchestrating-subagents` and `ce:plan` loaded; the existing authoritative tracker is retained rather than creating a second plan. The fixed ODD scope, finite advice budget and owner-commit override govern over generic planning defaults.
- Observed: read-only mapping Task `explore`, session `ses_e334c281bffeIgyV7bL7VGYRt0`, returned checker/config/derivation/test evidence. CodeGraph had no loaded project on initial call; explorer reported explicit-project retry failed with a readonly database error and used AFT/read fallback. No index lifecycle operation is authorised.
- Selected `advisor-security-pre` (assigned OpenCode Go GLM family), session `ses_e334850baffefUeVPspv0Fj0qg`: permission-boundary enforcement is the sole affected advisory surface. Its RAW initial answer and same-phase evidence clarification were read. The initial B1 sequencing blocker is resolved below; initial B2 writer-runtime impossibility claim was expressly withdrawn by the advisor as unproven for the future writer.
- Selected mandatory `advisor-spec-pre` (assigned OpenCode Go Qwen family), session `ses_e33485072ffeExdgeZwn001b13`: every code unit requires independent exact-specification coverage in addition to the surface advisor. Its RAW answer was read. B1-B6 are dispositioned below; advice is evidence, never approval.
- Skipped design/UX: no interface change. Skipped integration: no new integration or derivation implementation change. Skipped testing as a separate surface seat: mutation controls serve the same permissions boundary, already assessed by security and mandatory specification advice. Skipped maintainability: extraction is bounded to the specified marker block, not an independent refactor. No additional pass or extra surface advisor is selected. `planner-evidence` skipped: own tracker/workflow reads plus one bounded explorer established the planning facts needed.

### Writer sequencing and advisor finding dispositions

1. **T1 first; missing-marker RED.** Follow the exact test runner above. Capture the complete command, stdout/stderr and exit status verbatim. The first failure must identify `acknowledge-grant-policy marker block is missing`, not an import/runtime/config error. Mutation controls check rejection by non-empty failures rather than prematurely requiring the final renamed diagnostic string. Runtime skipping is allowed by the test contract when neither runtime exists, but skipped execution is NOT GREEN evidence for this unit.
2. **Mechanical extraction; ask-only RED.** Security B1: expose the harness-required NEW sweep name `acknowledgeGrantOutsideFailures` while retaining the OLD `resolved === "allow"` behavior and old failure strings. Mechanically migrate the five existing call-site names at the same time so the intermediate file stays coherent; do not leave undefined old names. Do not add the checker's synthetic-ask rejection self-control until the tightening step. Run T1 and capture the exact ask-family failure; other controls must pass. This distinguishes the behavioral defect from the first structural RED.
3. **Final T2; GREEN.** Apply the exact sweep implementation in the contract, not an approximation. Update expected strings at all five original sites (observed baseline locations: deployed sweep 1194, exact allow 1195, wildcard allow 1197, ordered deny 1199, deny 1201; navigate by symbols when lines shift). Add `synthetic-ask` detection and a `HOST_REVIEW_ACKNOWLEDGE_NON_DENY_OUTSIDE_COORDINATORS` diagnostic assertion with a named `...POSITIVE_CONTROL_FAILED` failure if detection is absent. Ordered-deny, explicit deny and omitted controls must yield no failures. Capture focused GREEN verbatim.
4. **T2 isolation constraints, explicit for specification B2-B6.** The single contiguous block is immediately after the sandbox-mutation defaults loop and before `registeredHostReads` (observed baseline 1052-1055). Keep only the five functions in the exact contract order. Preserve `globPatternMatches` and `resolvedPermissionValue` unchanged, including last-match ordering. Use only `acknowledgeGrantShow` inside the block, with no `fail`, `show`, `cfgPerm`, `cfgTool` or other file-level helper. Delete the original definitions. Move the existing `acknowledgeAskProbe` lines unchanged to immediately after the block. Preserve later coordinator helper calls and the EXACT explicit-own-key allow requirement. Verify one marker pair, one definition per moved function, zero remaining old sweep-name references, all five original call sites updated, and no out-of-block dependency in the extracted policy.
5. **T1 acceptance clarification, specification B1 / D1 and security O1.** Exact AND wildcard ask are required by the existing Acceptance criteria, even though T1's example list only spells out exact ask. Cover both in one ask-family test using isolated deep copies and parameterized subtests; step-two failures may be the exact/wildcard ask subcases of that control, never unrelated failures. This is coverage of the existing acceptance criterion, not a new policy or grant. Also retain every listed positive/negative control, including removed/ask/wildcard-only coordinator and global-allow mutations. Every coordinator must both have an exact allow and resolve allow; every other agent must resolve deny/absent. Assert identical exact holder sets in source and derived configs. Use the specified temporary fork `package.json` fixture and call BOTH `derive_config` and `add_v2_astra_aliases`; do not copy the precedent's HOME-dependent derived-config skip. No granting `-astra` alias may be silently whitelisted. The live-config docstring is mandatory.
6. **T4 then T3.** Add exactly one paragraph inside the review-relay anchor with the holder names, global deny, verbatim owner decision/date/item and rationale. After final checker bytes, execute manifest `update`, then `check`; require `ok: manifest and pin are current`. Never hand-edit manifest or pin; re-run update/check after any later checker correction.
7. **Required final executions.** Execute `node --check verify/checkers/check-runtime-agents.cjs`, focused unittest and full `python3 -m unittest discover -s tests`; retain verbatim outputs and statuses. Any Bun execution uses a temporary HOME. The Planner has no Bash/sandbox execution surface and makes no execution claim. Security's same-phase clarification reported node EACCES only in an advisor-evidence sandbox, without a root/status attestation; availability for the future writer is unproven, not observed impossible. The writer must attempt the contracted node check on its own authorised execution surface. If denied/unavailable, record the exact failure and return BLOCKED for that required check; do not silently substitute Bun parsing or label syntax as runtime verification. A missing Node does not authorise changing the contract.

### Initial post-code batch, Gate 2 and owner handoff

- PM owns writer dispatch; Planner dispatches neither writer nor native review lens. Require writer attestation of the expected worktree/branch, changed-path inventory, both REDs, focused GREEN, full test output, syntax check, manifest output and reviewability receipt. No claimed execution is accepted from skipped tests, parse-only output or a different candidate.
- On the SAME INITIAL candidate, PM obtains one security post-code check and the single independent high-risk `gentle-ai-verify`, plus `aft_inspect` or applicable static diagnostics covering every changed path. Static diagnostics belong in the first batch, not first after correction. These are one post-code check phase; the mandatory specification advisor is additional, not a replacement for security or verifier.
- Mandatory `advisor-spec-post` (assigned OpenCode Go GLM family) is dispatched only after actual writer output and verifier evidence are available, before Gate 2. Its brief carries the user's exact specification strings, unchanged allowed surfaces, actual diff/relevant code, the verbatim contract, both REDs and GREEN evidence. Read every selected advisor's RAW answer; never substitute a summary as evidence.
- Install the candidate and obtain the pre-commit technical assessment of that installed candidate (not native RDD) before Planner Gate 2. Do not complete/tick T1-T4 or hand off as technically complete before Gate 2. Gate 2 is technical only, never commit/merge/release/user acceptance authority. This unit still makes NO commit.
- Batch all initial post-code findings before correction. At most ONE fresh correction writer is permitted. After correction, regenerate affected pins and run targeted checks for finding IDs and affected regressions, then Gate 2 again. Second Gate 2 passes unless a true blocker remains; a second REFINE/ESCALATE returns to the human. Record non-blocking follow-ups separately, never expand scope or add another advice cycle.
- Follow `sandbox_finish` then approval-gated `sandbox_apply`. If S17 refuses apply, preserve the frozen finished result and return its exact identity for authorised parent preview/install; do not retry, bypass, or commit. If S16 reports divergence, parent must inspect actual status before any new writer. Leave the accepted applied diff UNCOMMITTED on `feat/q135-ack-grant-pin` and report status, diff stat, changed paths, reviewability receipt and unresolved checks. No commit tool or native RDD operation is permitted in this unit.

### Deferred, non-blocking findings

Specification E1-E3 and security O3 concern malformed/null/array/object-valued permissions beyond the specified controls. Preserve the existing helper semantics; object-valued entries are currently ignored by resolution. No resolver redesign, tool-enablement pin, new holder, or derivation change is authorised. Future schema-policy hardening is separate work. Specification E4 uses per-test temporary fixtures/deep copies; no parallel mutation is planned. E5 is covered by unchanged hoisted function declarations and regression tests; E6 by literal marker extraction rather than brace parsing. Specification O3 is addressed by temporary HOME for Bun. No planning-time test result is assumed.

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
- 2026-11-11 Planner finalised the orchestrator's existing T1-T4 scope using the PM's suggestions as messages.
  Formal pre-code security and mandatory specification Tasks returned; RAW outputs read. Their actionable
  planning findings are dispositioned in Finalised unit plan; no source implementation, task completion,
  execution result, native review or delivery approval is claimed by this planning update.


## Revisions
- r1 2026-11-11T22:15:23Z gentle-orchestrator: Create Q135 tracker: pin the acknowledge-approved grant (owner decision 2026-11-10 item 8).
- r2 2026-11-11T22:19:55Z gentle-orchestrator: Record Tier 2 routing correction (pm-odd, worktree supported) and the authoritative implementation contract.
- r3 2026-11-11T22:38:06Z planner: Finalise T1-T4 plan and formal advice dispositions; preserve verbatim contract. Broker retains managed revision log.
