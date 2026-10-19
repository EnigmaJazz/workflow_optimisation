# Q59 — PM layer: verifier

**Status:** READY FOR IMPLEMENTATION HANDOFF — planning unit `q59-pm-verifier-plan-u1`; implementation tasks A–E remain PENDING.
**Tracker task:** `q59-pm-verifier`.
**Parent:** `odd/tasks/pm-layer.md` T7 (Q59).

## Objective

Make the verifier assert the project-manager layer as a set of route coordinators rather than a
single hard-coded `gentle-orchestrator` name: a coordinator-generic inventory, the PM identity
surface, permissions/depth/family independence, prompt budgets, behavioural probes, and the
digest re-pin.

## Problem

The existing verifier already contains substantial orchestration and PM checks, but they grew as
single-name assumptions and as partial per-tool grants. There is no line-numbered classification
that separates genuinely coordinator-generic assertions from orchestrator-only ones, and the
historical "23 single-name checks" figure has not been verified. Q54 also records that broker
identity on permitted calls is inferred, not echoed, so the identity surface must be asserted
explicitly rather than assumed.

## Authorized scope

### This planning unit (current)

- Authorized writes are exactly: `odd/tasks/q59-pm-verifier.md` (created first),
  `odd/tasks/pm-layer.md`, `docs/TODO.md`, and `ROUTER-LOG.md`.
- Documentation and tracker text only. No implementation source, test, config, prompt, plugin, or
  verifier edits; no deploy; no branch switch, push, PR, or worker commit/native-review
  operation/evidence.
- The PM owns the fixed-host work-unit commit and every post-commit risk assessment. The PM does
  not run native review; native review remains externally driven. This worker returns a staged
  reviewability receipt only.
- Preserve unrelated existing files. Stop on a conflicting tracked modification.

### Future implementation units (A–E) — authorized later, not this unit

- **Scope guard for A–E as well as this unit:** no agent-prompt or `global-config/opencode.json`
  edits, and no `WORKFLOW.md` edits. Audit only. An exact missing clause or grant returns PM
  `NEEDS_INPUT` for a separate unit; it is not edited here. Q04 is not a prerequisite or blocker.
- [ ] **A — coordinator inventory.** Produce a line-numbered inventory that classifies each existing
  check as coordinator-generic or orchestrator-only. Do not repeat the unverified "23" as an exact
  count. The coordinator set is `gentle-orchestrator`, `pm-odd`, `pm-systematic`, plus
  `gentle-orchestrator-legacy` ONLY while it is actually selectable. Never restore a retired agent.
- [ ] **B — PM identity surface (exactly one unit).** Assert the one-unit identity boundary: one PM
  session executes exactly one work unit, never a whole feature or a multi-unit session. Assert
  the assigned route skill is loaded first, route validation against `WORKFLOW.md`, the
  `pm-unit-brief/v1` schema pointer, stop/resume, and report-not-proof. Keep canonical/deployed
  consistency without duplicating the prompt parity suite. Audit permissions and depth; do not
  edit prompts or `global-config/opencode.json`: the orchestrator admits PMs; the only
  general-dispatch exception is the explicit tiny-fix rule; PMs admit only their named
  writers/verifiers; no deeper or coordinator self-dispatch. Reuse the family helper; an unknown
  family fails closed, and the tiny-fix exception is preserved: DeepSeek `gentle-orchestrator`,
  OpenAI `general`, Sol PMs, and DeepSeek `odd-apply` / `gentle-ai-worker`. Preserve the
  orchestrator-only tiny-fix, fixed-host, and project-registration rules and the existing
  independent pairs. No blanket PM fixed-host grants. If a required grant is missing, return
  `NEEDS_INPUT` for a separate unit.
- [ ] **C — prompt budgets and behavioural probes.** Keep the existing PM `<6000` cap, measure and
  report every prompt size, and find the authoritative orchestrator budget. The existing
  prompt-source test prints bytes/lines but does NOT establish a numeric cap; if the authority stays
  unresolved, return `NEEDS_INPUT` and do not invent a threshold. Extend existing behavioural probes
  ONLY through the orchestrator (Q51 at `docs/TODO.md:463-475`; verifier `:5354-5462`), falling back
  to static/fixture checks when unusable. Live probes are HOST-ONLY and are NOT RUN in the sandbox.
- [ ] **D — tests and digest pin.** Every new condition needs a mutation-positive control: a
  reverted, removed, or wrong clause must fail the assertion. Assertions and their positive
  controls travel with the behavior in the same commit; do not create standalone test commits.
  Extend the existing `tests/test_review_pipeline_permissions.py`, `tests/test_pm_layer_prompts.py`,
  `tests/test_orchestrator_prompt_source.py`, and `tests/test_anchor_manifest.py`; do not create a
  parallel suite. Pin `VERIFY_SCRIPT_SHA256` in `workflow-health-check.ts` LAST, after all verifier
  edits, in the same verifier-edit commit that carries the behavior and tests; do not create a
  standalone pin commit. Verify with `sha256sum` equality and the `read_verify_script_pin` regex.
- [ ] **E — metadata and records.** After implementation, update the tracker, `docs/TODO.md`, and
  `ROUTER-LOG.md` with observed results. Update `docs/PLAN.md` only as a separately authorized
  unit.

## Current-state evidence

Evidence below is from the read-only explore session recorded by the PM
(`ses_eaa066b63ffeI5HcVR3jdxT8jL`); this planning unit did not redo the audit.

- **Observed — PM host reads/grants and positive controls:** `verify-workflow.sh:2771-2919`.
- **Observed — PM execution/tool denies:** `verify-workflow.sh:3016-3031` (`pmAgents`).
- **Observed — SDD retirement:** `verify-workflow.sh:3033-3053`.
- **Observed — PM task and `odd-apply` rules:** `verify-workflow.sh:3063-3076`.
- **Observed — existing reuse surfaces:** relay lockdown and writer model-family checks already
  exist (family helper `:2395-2410`). Audit and reuse them; do not duplicate.
- **Observed — legacy key:** a bounded full agent-object read of `global-config/opencode.json`
  found no `gentle-orchestrator-legacy` key. The conditional deployed inventory remains unresolved
  because no deployed/external inspection is available here.
- **Observed — PM cap:** `tests/test_pm_layer_prompts.py:141-147` asserts `<6000` characters.
- **Observed — prompt-size reporting:** `tests/test_orchestrator_prompt_source.py:625-647` prints
  bytes/lines; it does not define a numeric orchestrator cap.
- **Observed — Q26 boundary:** stable-anchor machinery is present at `verify-workflow.sh:4637-4917`,
  but broader review/deployment closure is still pending per its tracker. Do not claim all of Q26.
- **Observed — prerequisites:** Q59 names Q55 as its prerequisite. Q26 and Q04 are "easier after",
  not hard prerequisites; the user explicitly stated Q04 is NOT a blocker. Verify Q55 handoff
  acceptance at implementation start instead of inferring its state from aggregate TODO status.
- **Observed — model config:** PMs use `openai/gpt-6.1-sol` (`global-config/opencode.json:2067,:2204`),
  `odd-apply` uses `opencode-go/deepseek-v4.1-flash` (`:2350`), `gentle-ai-worker` uses the same
  (`:369`), the orchestrator uses `opencode-go/deepseek-v4.1-flash` (`:466`), and `general` uses
  `openai/gpt-6-luna` (`:243`). Configured identity is observed; live runtime/fallback is not attested.
- **Constraint — no route rewrites here:** any future verifier split must preserve existing checks.
  The later authorized implementation scope has no `WORKFLOW.md` edits.
- **Constraint — fail closed on gaps:** no agent-prompt or `global-config/opencode.json` edits in
  this planning unit or in future A–E; no `WORKFLOW.md` edits. An exact missing clause or grant
  returns PM `NEEDS_INPUT` for a separate unit rather than being edited here. Q04 stays
  non-blocking.

## Constraints

- Planning-only ODD work unit; mutation is limited to the four authorized metadata paths.
- Planning is NOT one of Q56's ten implementation pilot units. It earns no pilot credit.
- There is no requirement to implement A–E in the next session. A fresh PM takes exactly one
  bounded, anchored unit.
- No implementation source/test/config/prompt edits, deploy, branch switch, push, PR, worker
  commit, or worker native-review operation/evidence in this unit. The PM performs the fixed-host
  work-unit commit and post-commit assessment; native review is not run by the PM and remains
  externally driven.
- All execution and mutation use only the authorized sandbox surfaces.
- A report is a claim, not proof. Every completed task needs an observed result.

## Acceptance criteria

- The tracker exists, is the first edit, and contains objective, problem, scope, constraints,
  tasks A–E, acceptance, checks, route/advice evidence, and status.
- `pm-layer.md` T7 remains unchecked and links this tracker without claiming pilot credit.
- `docs/TODO.md` Q59 is `READY` with the tracker link, preserved prerequisite wording, and the
  unverified-count clarification.
- `ROUTER-LOG.md` has one planning row before `## Usage Notes`, with the tracker, pre-code Task,
  and independent post Task evidence and no fabricated commit or review outcome.
- Exactly four repository paths are changed; `git diff --check` is clean.
- No implementation/test source is modified, and no implementation suite is run.

## Delivery

- Strategy: `ask-on-risk`. Forecast: **300–500 implementation authored lines** (forecast, not
  measured), excluding generated files.
- Split into coherent future slices, each under 400 authored lines and 100 KiB, each keeping behavior
  and tests together. Before the running delivery budget crosses about 400 authored lines, resolve
  `stacked-to-main` versus `feature-branch-chain`; there is no pre-authorized exception.

## Checks

### This planning unit (run before finish)

- Documentation consistency assertions for the required sections/tasks/links, Q59 `READY`, T7
  pending, pilot distinction, and no implementation changes.
- `git diff --check`.
- Exactly four changed paths, excluding a pre-existing unrelated untracked bundle.
- Workspace facts: root, branch/HEAD, boundary object type and ancestry.

**Observed results (this refinement, run in the sandbox):**

- Workspace: `git rev-parse --show-toplevel` → `/work` (exit 0); branch `work`; current `HEAD`
  `509e383aa3472e34faff3d9de3b99dfc63f1d30b` (exit 0), whose parent is the briefed input
  `c9c6f02aa50488fae8857d9cace61abbcba3d3d9` (exit 0). The earlier writer's `4951d56` observation
  is superseded for this session. `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422` resolves as a
  `commit` (exit 0) and `git merge-base --is-ancestor deab3b5b... HEAD` exits 0. The host feature
  branch is not a ref in this worker clone; that remains an inferred limitation, not a host-state
  claim.
- Scope: `git diff --name-status c9c6f02aa50488fae8857d9cace61abbcba3d3d9 --` → exactly
  `M ROUTER-LOG.md`, `M docs/TODO.md`, `M odd/tasks/pm-layer.md`, and
  `A odd/tasks/q59-pm-verifier.md` (exit 0). `git diff --name-only -- verify-workflow.sh
  global-config tests scripts WORKFLOW.md` → no output (exit 0), so no implementation source,
  config, test, or workflow file changed. At check time, `git status --short` also showed the
  untracked `.broker-tmp/` check harness and the pre-existing synthetic
  `ses_ea9ed4f02ffe832R6TN3OzuDWs.bundle`; neither was staged and neither is part of the
  candidate. The bundle is not deleted.
- Documentation consistency assertions → `CONSISTENCY_OK`: 15 assertions passed and 20
  mutation-positive controls each failed the same predicate after an actual required clause was
  removed from an in-memory copy (required sections, tasks A–E, one-unit identity, worker/PM
  ownership, future prompt/config/`WORKFLOW.md` guard, `NEEDS_INPUT`, Q04 non-blocking, pre/post
  Task/model evidence, the three cross-links, host-only future checks, pin-last-same-commit, and
  planning-not-pilot).
- `git diff --check` → exit 0, no output (clean).
- The final full-candidate staged receipt (bytes, numstat, and the full new-file patch header) and
  the incremental B→C metrics are measured after this recorded content is final and returned in
  the PM envelope; recording those numbers here would change the measured artifact.

### Future implementation (NOT RUN in this planning unit)

- `bash -n verify-workflow.sh`.
- Focused four existing Python modules listed in task D.
- Full `python3 -m unittest discover -s tests`, comparing observed results with the BRIEF-SUPPLIED
  baseline of 10 node-denied errors and 1 skip. That baseline is supplied, not verified here.
- `bun` routing-guard tests with a genuinely throwaway `HOME`; never the real `HOME`.
- Positive controls must execute assertions; syntax alone is not behavioural proof.
- `sha256sum` pin equality plus the `read_verify_script_pin` regex.
- Full verifier/deploy remains HOST-ONLY and is not run. A source commit is not deployment activation.

## Log

- Initial writer: PM-supplied session `ses_ea9fcd77bffepTGGvpGp0Zk4lC` installed the four
  documentation paths; this refinement did not reconstruct that result.
- Refinement writer: delegated sandbox writer for `q59-pm-verifier-plan-u1`. Its session id is
  exposed only in the PM envelope and is not invented here.
- Refinement changes: tracker ownership/scope/post-advice/receipt wording; `pm-layer.md` T7
  post-advice reference; `docs/TODO.md` Q59 post-advice reference; `ROUTER-LOG.md` row wording and
  post Task evidence. The PM owns the commit and post-commit assessment.

## Route and review evidence

- Dispatch-supplied route evidence: `workflow-odd-secure` was loaded FIRST, then
  `workflow-route`; this worker did not re-observe the skill calls.
- Class: global tooling change. Route: delegated. Triggers: preparation and multi-file secure
  delegation.
- RDD: PM-supplied observed `enabled`, decided `global`. Last reviewed boundary:
  `deab3b5b07c84c9adbd1ffe4f5b7ed02b8dd1422`. Planning input: `c9c6f02`.
- Planning anchor is explicitly `none` and the comparison is skipped; the branch identity was
  previously observed exactly.
- After EVERY PM commit, assess with `host_review_assess` bound to the last boundary and
  `committedOnly=true`. If review is due, stop and return `NEEDS_INPUT`; native review stays with
  the orchestrator only.
- The deterministic Magic Context mirror tool is unimplemented: no mirror write or verification was
  performed, and no mirror body is fetched.

## Advice record (pre-code, advisory only; not approval)

- `advisor-integration-pre` Task `ses_eaa0c1a94ffeaxyFcbfo5hlcON`, configured
  `opencode-go/kimi-k2.7-code` (`global-config/opencode.json:1552`); the same-session report was
  corrected. Model configuration is observed; actual runtime/fallback is not attested.
- Summaries adopted: preserve orchestrator-only exceptions; treat the legacy inventory as
  conditional; require mutation-positive controls and no duplicate checks; prompt-cap authority is
  unresolved; live probes are host-only; split the forecast and pin last.
- Rejected: the advisor's suggested hard Q26/Q04 prerequisites, new `WORKFLOW.md`-anchor scope, and a
  full verifier run inside the sandbox.
- The explorer Task's configured model was unavailable; no result or model is fabricated.
- Writer configured model: `opencode-go/deepseek-v4.1-flash` (`:2350`). Its actual session identity
  and receipt belong to the PM envelope if not exposed here.

## Post-code advice (independent, advisory only; not approval)

- `advisor-integration-post` Task `ses_ea9f1a0ecffe8aPpAJIGyw2L11`, configured
  `opencode-go/kimi-k2.7-code` (`global-config/opencode.json:1752`; PM-read exact). Actual
  runtime/fallback is not attested.
- **PM-supplied initial verdict and blockers (not independently re-derived here): NOT READY.**
  The blockers were: (1) the planning-unit ownership text banned commit and native review for the
  whole unit although the PM owns the fixed-host commit and post-commit assessment; (2) the future
  A–E scope did not explicitly prohibit prompt and `global-config/opencode.json` edits or name the
  `NEEDS_INPUT` route for an exact missing clause or grant; (3) the independent post-advice record
  was still a pending placeholder; (4) the staged reviewability receipt measured only the new
  tracker file, not the full four-path candidate.
- **Resolutions in this refinement:** the ownership text now bans only worker commit/native review
  and assigns the fixed-host commit plus post-commit assessment to the PM, with no PM-run native
  review; this unit and A–E prohibit prompt/config edits, require `NEEDS_INPUT` for an exact
  missing clause or grant, forbid `WORKFLOW.md` edits, and keep Q04 non-blocking; this Task/model
  record replaces the placeholder; and the final staged receipt covers all four paths against the
  host input `c9c6f02aa50488fae8857d9cace61abbcba3d3d9`, including the full new-file patch header.
  The initial 19,904-byte partial new-file measurement and the broker's 20,292-byte / 224-line
  initial patch are superseded by that full receipt; incremental B→C metrics are reported
  separately.
- **Final confirmation:** the PM envelope records the final post-advice confirmation after the
  PM's own verification. This tracker does not claim that final verdict or any native-review
  result.

## Status and next step

The planning content is ready for PM handoff after the PM confirms the post-advice blockers are
resolved and records the fixed-host commit identity and post-commit assessment in the result
envelope; no future SHA or final post verdict is fabricated here. Implementation tasks A–E remain
PENDING. The next session receives exactly one bounded, anchored unit.
