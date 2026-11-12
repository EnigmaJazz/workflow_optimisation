# Q135 — pin the `host_review_acknowledge_approved` grant

**Objective:** make the owner's 2026-11-10 decision (item 8, verbatim: "Yes allow, does not need to ask")
executable: `host_review_acknowledge_approved` is `allow` for exactly `gentle-orchestrator`, `pm-odd` and
`pm-systematic`, and `deny` by global default for every other agent. Rationale: acknowledgement only burns
the authority the provider already issued for the exact lineage, and consent was given earlier, so an `ask`
gate stalls an approved review for no benefit.

**Branch:** `feat/q135-ack-grant-pin` (worktree `~/ai-workspace/worktrees/workflow_optimisation/q135-ack-grant-pin`),
off `main` `f1cbf3c`. The grant itself is already in `global-config/opencode.json`; this unit adds the evidence and pins it.

**Delivery:** committed by the owner as `c85c75c`; Codex Tier 4 PASS. `scripts/**` and the verifier manifest
(`VERIFY_MODULES` in `verify-workflow.sh` plus the `VERIFY_SCRIPT_SHA256` pin in
`global-config/plugins/workflow-health-check.ts`) were S17-protected, so they were staged as one diff and the
owner committed all five paths together (no partial commit).

**Test runner:** `python3 -m unittest discover -s tests -p 'test_acknowledge_grant_pin.py' -v`, then
`python3 -m unittest discover -s tests`. Bun suites, if run, use a temporary `HOME`.

**Risk:** item 2 (permissions) → Tier 4 Codex review with a SECURITY section before merge. Codex PASS recorded
(msg `msg_5d22e2050e77`).

## Tasks

| ID | Task | Status | Evidence |
|---|---|---|---|
| T1 | New pinning test `tests/test_acknowledge_grant_pin.py` | done | 4 tests; RED-1 marker-missing, RED-2 exact+wildcard ask, GREEN |
| T2 | Tighten the `check-runtime-agents.cjs` non-coordinator sweep to "deny or absent" behind the `acknowledge-grant-policy` marker block | done | one marker pair, one definition per function, `resolved !== undefined && resolved !== "deny"`, synthetic-ask + omitted controls; Bun whole-file parse gate |
| T3 | Re-pin the verifier manifest | done | `ok: manifest and pin are current` |
| T4 | State the holder set and the owner decision in `WORKFLOW.md` | done | one paragraph inside the `workflow.review-relay` anchor |
| T5 | Native review of the widened candidate | done, approved | lineage `review-f0b965c39bb70244`, consumed `sha256:d1995d99…`, authority burned |

## Acceptance criteria

- The source config and the derived V2 config expose exactly the three holders; every other agent resolves
  `deny` or has no rule (inherits the global `deny`).
- The test fails when a fourth agent receives `allow` or `ask` (exact or wildcard), when one of the three loses
  its exact `allow` (removed, `ask`, or wildcard-only), and when the global default leaves `deny`.
- `python3 scripts/verifier_manifest.py check` reports the manifest and pin current.
- The three coordinators keep an exact explicit key: a wildcard alone never satisfies the coordinator check.

## Authorized scope

`tests/test_acknowledge_grant_pin.py`, `verify/checkers/check-runtime-agents.cjs`, `verify-workflow.sh`,
`global-config/plugins/workflow-health-check.ts`, `WORKFLOW.md`. `global-config/opencode.json` and the grant
itself were not changed.

## Route and trigger evidence

ROUTE: Global tooling change | intent: authorized change | route: workflow-odd-secure | specialist: `pm-odd`,
then one direct `general` sandbox writer after its structural block | basis: WORKFLOW.md.

`pm-odd` validated the class/route, passed the unit-start anchor, dispatched the Planner, and its Planner issued
Gate 1 PASS with security and specification pre-code advice read. `pm-odd` then returned `BLOCKED /
REQUIRED_WRITER_SURFACE_UNAVAILABLE`: in this runtime its subagent surface exposes only `advisor-*`, `explore`,
`gentle-ai-verify`, `gentle-ai-verify-routine` and `planner`, so neither `odd-apply` nor `gentle-ai-worker` can
be dispatched by the PM. Tier 2 accepted a direct `general` writer as a sanctioned exception (Q102 P1a form);
`general` is `openai/gpt-6-luna`, independent of the DeepSeek orchestrator.

Advice: pre-code Planner-run security + specification advisors (Gate 1 PASS); post-code `advisor-security-post`
(two CRITICALs refuted, see Evidence) plus the independent `gentle-ai-verify` high-risk seat (PASS).

## Implementation contract

Authoritative record of what was implemented.

### T1 — `tests/test_acknowledge_grant_pin.py`

Mirrors `tests/test_pm_git_head_grants.py` (config pin + derivation + mutation controls) and
`tests/test_grok_seat_policy.py` (extract a delimited block and execute it with node/bun). Constants `TOOL`,
`COORDINATORS=("gentle-orchestrator","pm-odd","pm-systematic")`, markers
`// acknowledge-grant-policy:begin` / `// acknowledge-grant-policy:end`. `build_policy` extracts the block and
appends a stdin-driven harness with modes `coordinator`, `outside`, `resolved`. Derivation loads
`scripts/derive-v2-config.py` and calls `derive_config(...)` then `add_v2_astra_aliases(config)`.
`check(config, allowed=COORDINATORS)` asserts the global `deny`, each coordinator's exact `allow`, and an empty
outside sweep. Positive controls: fourth agent `allow`/`ask`/wildcard; `pm-odd` removed/`ask`/wildcard-only;
global `allow`. Negative controls: explicit `deny`, ordered deny, omitted, string `deny`. The docstring states
the test reads the live config, so a future holder updates the test in the same change.

### T2 — `verify/checkers/check-runtime-agents.cjs`

One contiguous `acknowledge-grant-policy` block after the sandbox-mutation defaults loop containing
`acknowledgeGrantShow`, `globPatternMatches`, `resolvedPermissionValue`, `hostReviewAcknowledgeAllowFailures`,
and `acknowledgeGrantOutsideFailures` with `resolved !== undefined && resolved !== "deny"`. The block calls no
file-level helper. The probe sits immediately after the block; the five call sites use the new sweep; synthetic
allow/glob/ask positive controls and ordered-deny/deny/omitted negative controls are in place. The coordinator
and later orchestrator sections keep the exact own-key check.

### T3 — manifest

`python3 scripts/verifier_manifest.py update` rewrote `verify-workflow.sh` and the pin in
`workflow-health-check.ts`; `check` printed `ok: manifest and pin are current`.

### T4 — `WORKFLOW.md`

One paragraph inside the `workflow.review-relay` anchor: holder set, global deny, owner decision 2026-11-10
item 8 verbatim, rationale, and the verifier pin.

## Evidence

- Writers: initial `general` writer applied five paths; one `general` correction writer repaired the checker
  (duplicate `const acknowledgeAskProbe`, corrupted `globPatternMatches` regex, missing `=` on
  `acknowledgeGlobThenDenyProbe`, and added the omitted-key negative control).
- RED-1: `AssertionError: acknowledge-grant-policy marker block is missing: substring not found` (`Ran 0 tests`,
  `FAILED (errors=1)`).
- RED-2: only `exact ask` and `wildcard ask` fourth-agent controls failed (`Ran 4 tests`, `FAILED (failures=2)`).
- GREEN: `Ran 4 tests in 0.906s`, `OK`; independently re-run by the verifier (`Ran 4`, `OK`).
- Manifest: `ok: manifest and pin are current`.
- Syntax: `node --check` unavailable in the sandbox (EACCES); whole-file
  `bun build verify/checkers/check-runtime-agents.cjs --target=node --no-bundle` parse gate passed.
- Independent `gentle-ai-verify`: PASS — one marker pair, one definition per function, exact-key coordinator
  check intact, no extra `allow` holder, `global-config/opencode.json` untouched.
- `advisor-security-post` raised two CRITICALs claiming the coordinator check accepted a wildcard-only allow.
  REFUTED: `hostReviewAcknowledgeAllowFailures` uses `Object.prototype.hasOwnProperty.call(...)` and the GREEN
  run includes the wildcard-only control; the native `review-risk` lens independently confirmed the refutation.
- Regression modules OK: `test_anchor_manifest` 21, `test_review_cadence` 2, `test_v2_config` 9,
  `test_derive_v2_config` 76, `test_grok_seat_policy` 13, `test_pm_git_head_grants` 5,
  `test_acknowledge_grant_pin` 4. `test_orchestrator_prompt_source` keeps the known main baseline failure.
- Full-suite residue is environmental: missing `sqlite3`, missing `node`, `/nonexistent` temp root, Python 3.13
  dataclass handling.

## Native review outcome

- Scope: `--base-ref df32ad0 --committed-only`, HEAD `970a501`, target
  `sha256:8e3c309ab010524fbec2cc2f3805eab55ee32268cbc071113f88a7b11e424c4a`, base tree
  `f686cf0c6f74938b083104fe220051a47f32ff90`, candidate tree `3656cff25dc96ae50c9b920a270fa64be1fbcb34`,
  six changed paths (the five implementation paths plus this tracker document), 487 changed lines.
- Consent: the owner first consented to `df32ad0..c85c75c`; the tooling could not scope past later commits and
  widened the candidate to `df32ad0..970a501`, which stopped the first attempt. The owner then consented
  verbatim "Yes" (2026-11-12) to the widened review; the provider's `consent_required` envelope was answered
  with its exact `--consent granted` invocation.
- Lineage: `review-f0b965c39bb70244` (risk `high`; provider-selected lenses `review-risk`,
  `review-resilience`, `review-readability`, `review-reliability`).
- Verdict: **approved**. `review/acknowledge-approved` succeeded with
  `consumed_revision sha256:d1995d99da7cf5f573c57443ccdb13ba8e4d6b0d23cd4b7656e7ce48cc868406` and
  `authority: burned`.
- `review-risk` found nothing and confirmed the grant file is unchanged.
- Non-blocking advisories (all `informational`; none opened a correction, none reopens this candidate):
  - `R2-unused-runtime-param` (readability, WARNING) — `tests/test_acknowledge_grant_pin.py:29`, `build_policy`
    takes a `runtime` argument it never reads.
  - `R2-dunder-setitem` (readability, SUGGESTION) — lines 116-119 use `__setitem__` instead of subscript
    assignment in the mutation controls.
  - `R3-001` (reliability, WARNING) — line 126 fourth-agent controls assert only a non-empty failure list; the
    baseline is not re-asserted inside the subtest and no expected failure code is matched.
  - `R3-002` (reliability, WARNING) — line 140 coordinator controls use the same non-empty-only assertion.
  - `R3-003` (reliability, WARNING) — lines 50-51 whole-class skip when no JS runtime; a skip is not green
    evidence.
  - `R4-1` (resilience, SUGGESTION) — lines 97-103 spawn redundant policy subprocesses in `assert_clean_config`.
  - `R4-2` (resilience, SUGGESTION) — lines 22-26 unguarded `spec_from_file_location`/loader.
  - `R4-3` (resilience, SUGGESTION) — lines 49-51 skip visibility.
- Boundary recorded: the reviewed boundary advances to `970a501` (the consumed candidate). Commits after
  `970a501`, including this metadata update, are not covered by this review.

## Owner commit list

`tests/test_acknowledge_grant_pin.py`, `verify/checkers/check-runtime-agents.cjs`, `verify-workflow.sh`,
`global-config/plugins/workflow-health-check.ts`, `WORKFLOW.md` — committed as `c85c75c`.

## Log

- Created before the first implementation edit.
- 2026-11-11 Tier 2 routing correction: substantial ODD units route through `pm-odd`; the earlier claim that
  `pm-handoff` blocks linked worktrees was wrong ("A linked worktree is supported and is NOT a blocker").
- 2026-11-11 Planner finalised T1-T4 and read the formal security + specification pre-code advice; Gate 1 PASS.
  `pm-odd` returned `BLOCKED / REQUIRED_WRITER_SURFACE_UNAVAILABLE`; Tier 2 accepted the direct `general` writer
  fallback as a sanctioned exception (Q102 P1a form).
- 2026-11-11 Implementation and one correction round complete; verifier PASS. Applied diff handed to the owner.
- 2026-11-12 Owner commit `c85c75c`; Codex Tier 4 PASS. Read-only assess on the five-path candidate returned
  `risk: high`, `candidate.consumed: false`, `review_due: true`, `review_due_reason: high_risk`.
- 2026-11-12 First start attempt stopped: the tooling ranges `df32ad0..HEAD`, so the candidate included this
  tracker commit and could not be scoped to `c85c75c`; nothing was started.
- 2026-11-12 Owner consented to the widened candidate; review started as `review-f0b965c39bb70244`, all four
  lenses admitted, verdict approved, acknowledgement consumed `sha256:d1995d99…` and burned authority.


## Revisions
- r1 2026-11-11T22:15:23Z gentle-orchestrator: Create Q135 tracker: pin the acknowledge-approved grant (owner decision 2026-11-10 item 8).
- r2 2026-11-11T22:19:55Z gentle-orchestrator: Record Tier 2 routing correction (pm-odd, worktree supported) and the authoritative implementation contract.
- r3 2026-11-11T22:38:06Z planner: Finalise T1-T4 plan and formal advice dispositions; preserve verbatim contract. Broker retains managed revision log.
- r4 2026-11-11T23:58:47Z gentle-orchestrator: Close T1-T4 with RED/GREEN, verifier PASS, refuted advisor finding, owner commit list, and the Tier 2 sanctioned-exception record.
- r5 2026-11-12T00:20:25Z gentle-orchestrator: Record the review boundary df32ad0 for candidate c85c75c and the read-only assess result (high, due, not consumed); no transition executed.
- r6 2026-11-12T00:31:05Z gentle-orchestrator: Record native review outcome: lineage review-f0b965c39bb70244 approved, consumed sha256:d1995d99, authority burned, advisories listed; boundary advances to 970a501.

## Gates
- q135-ack-grant-pin-u1 PASS 2026-11-11T22:39:16Z planner ref=odd/tasks/q135-ack-grant-pin.md r3, Finalised unit plan T1-T4; raw security/spec pre-advice read; security B1 and spec B1-B6 resolved; node availability deferred to actual writer execution.
