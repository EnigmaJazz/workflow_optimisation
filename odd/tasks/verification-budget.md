# Q87 — Finite verification budget by task type

Feature: replace open-ended pre/post advice and verifier loops with a finite budget mapped to the
six existing route classes. Task ID `q87-verification-budget`. Class: global-tooling-change. Route:
delegated (`workflow-odd-secure`). Unit: `q87-verification-budget-plan-u1` (planning only). Delivery
strategy: `ask-on-risk`.

## Objective

Define a finite ceiling of pre-code advice, post-code checks and independent verification by task
type, and stop treating "repeat as needed" as an unlimited refinement budget. This unit records the
plan only; it makes no policy or source edit.

## Problem and evidence

- Observed (owner directive, 2026-10-21): work, verification and advice are finite by task type,
  never unlimited. Simple documentation gets ZERO advisor and `gentle-ai-verify` Tasks; the PM
  checks and an orchestrator independently reads back.
- Observed (`odd/tasks/q59-pm-verifier.md:288-295,415-459`): several correction/test cycles preceded
  the five committed source commits; two were real source defects (a JS `ReferenceError`, a stale PM
  prompt), recorded as replay evidence.
- Observed (`WORKFLOW.md:65`; `docs/specs/pm-handoff.md:30`): the current "Repeat as needed"
  refinement wording carries no ceiling.
- Inferred: the loops caught real defects, so the fix is a bounded budget, not zero checks. This
  unit does NOT assert that every cycle was needless (not proven).

## Final plan (authoritative for the future source unit; no edits here)

1. **Docs boundary by the actual unit diff, not the feature class.** Allowlist for the simple-docs
   exception: `odd/tasks/**` and `odd/advice/**` (state/planning/evidence only), `ROUTER-LOG.md`,
   `CLAIM-RETRACTIONS.md`, `docs/TODO.md`, `docs/TODO-HISTORY.md`, and the non-Constraints/
   non-decisions portions of `docs/PLAN.md`. A planning tracker may state FUTURE acceptance criteria
   without changing an existing executable acceptance contract; changing existing normative
   specs/constraints/acceptance is NOT docs. Any test/verifier reader disqualifies; uncertainty
   fails closed. `WORKFLOW.md`, `AGENTS.md`, `docs/specs/**`, `global-config/**`, ANCHOR_MANIFEST
   files and command-changing docs are never simple docs. No automatic source-comment exemption. A
   native medium/high raise moves a unit up, never down.
2. **Finite matrix over the six existing route classes** (no new classes): docs/planning/closure
   metadata and genuinely passive tiny = 0 pre-advice, 0 post-advice, 0 `gentle-ai-verify` (PM
   factual/structural checks plus an orchestrator independent readback). Medium ordinary behaviour/
   test-only/command docs = one pre-advice phase and one post-code check (`ce:review` substitutes the
   advisor); the verifier runs only on an explicit exception (security boundary, uncertainty, live
   fallback/independence, or an explicitly reduced small-model profile). High normative contract/
   config/security/enforcement tests/dependency or plugin pins = one pre phase, one post phase, one
   independent verifier. Generated inherits source. A conservative high reading of dependency/pin
   work resolves the reports' medium-vs-high conflict. The named `ce:review` baseline reviewers stay
   intact; counts are check phases, not numbers of baseline reviewers.
3. **Explicit PROPOSED policy decision:** the configured `opencode-go/deepseek-v4.1-flash` default
   writer is NOT treated as a small/reduced profile merely because of the "flash" name; no
   authoritative small-model label was found in research. The medium verifier exception must name a
   reduced profile/reason, not fire on all DeepSeek work. This is a policy decision to adopt, not a
   discovered upstream fact. The PM Sol self-check is independent of a DeepSeek docs writer;
   independent orchestrator readback remains required and no extra verifier is added.
4. **Per unit maximum: one initial writer plus ONE fresh correction writer across all pre-commit
   post-code gates** (including `ce:review` and external advice). Batch all applicable checks on the
   SAME candidate before correction; use finding IDs; issue one consolidated fix brief; install
   first, then refine on the installed base; run one targeted recheck of the IDs plus affected
   regression controls. The same unresolved blocker, or a new blocker during recheck, cannot buy
   another round: advisory/follow-up for non-blockers, `NEEDS_INPUT` for explicit human
   authorization, `BLOCKED` for missing authority/environment/evidence. A human may explicitly
   authorize a bounded exception with reason, scope and a new limit recorded; metadata or a new task
   ID never silently resets the counter. Record `correction_rounds_used` `0|1` in
   `pm-unit-result/v1`; record any override separately.
5. **`ce:review` is a post-code check, not an extra cycle;** its findings join the batch and it is
   not fully rerun after a fix. When the external post-code-pair lane is active it is one
   consolidated check whose internal and external same-candidate findings merge; both pair rules
   exclude docs. Manual advisor reports are not that lane. Native review stays a separate
   one-scoped-fix/targeted-validator step that closes it; no PM advisor/verifier loops run on a
   native correction. A tiny fix escalated after commit gets the applicable post-code check on the
   committed candidate; any one correction is a new commit, never rewritten history.
6. **Docs evidence:** exact changed-path list and allowlist rationale, stats, `git diff --check`,
   branch/SHA and any asserted references/ancestry, the PM check, the orchestrator independent
   readback, and `advice_record` status `not-applicable` with a reason; no runtime tests for true
   docs. Any test reader makes the unit normative with its applicable deterministic execution checks.
7. **Same future delivery must align:** `WORKFLOW.md:65,158,461/475,524` and the external-pair
   clauses; `docs/specs/pm-handoff.md:20,23,30,36,123` and its envelope; both route SKILLs;
   `overlay.md:196-200`; and the `advisor-gemini-post` committed-vs-precommit drift at
   `global-config/opencode.json:2008` (fold the relevant Q84 sequencing fix into Q87, keeping
   unrelated Q84 scope intact); plus the relevant Q59 ACTIVE metadata instruction, without rewriting
   historical failure reports. Add a dated owner decision. No policy edits in this unit.
8. **Overlay is included; Q88 folds into Q87, not deferred.** Exact future sequence: update the
   policy/tests and the overlay; run
   `python3 global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py --base global-config/prompts/gentle-orchestrator/base.md --overlay global-config/prompts/gentle-orchestrator/overlay.md`;
   capture stdout through authorized worker process/file APIs (no shell redirection/heredoc) and
   update the embedded `gentle-orchestrator` prompt in `global-config/opencode.json`; hash the
   assembled prompt into `CURRENT_PROMPT_SHA256` in `tests/test_orchestrator_prompt_source.py` and
   `global-config/prompts/gentle-orchestrator/normative-ledger.md`; run the assembler
   equality/mutation controls and `python3 -m unittest discover -s tests -p test_pm_handoff_spec.py`,
   then the same runner for `test_orchestrator_prompt_source.py`, `test_anchor_manifest.py`,
   `test_review_cadence.py`, `test_tiny_fix_route.py`. Verify the actual assembler location before
   documenting if it differs. No new `verify-workflow.sh` check or digest change. Future source/
   config consumer verification and deploy are HOST-ONLY through the orchestrator; the owner restart
   is separate to this unit.
9. **Forecast and delivery:** source is forecast at 250-450 authored lines (estimate; recompute the
   staged receipt). The embedded prompt is one very long line and may exceed authored bytes if not
   objectively generated: give it a separate generated receipt and never hide authored advisor-prompt
   changes as generated. Split into coherent units or record an approved size exception before
   commit, preserving source-plus-generated integrity. Default strategy `ask-on-risk`; no push/PR
   authority. Keep this tracker compact with stable finding IDs and no append-only superseded prose.
10. **Writer-tier dispatch rule.** Owner rule 2026-10-21: when the writer is
    `gentle-ai-worker-local`, dispatch exactly ONE file change per writer Task; do not batch
    multiple files. Cloud writers may batch a coherent multi-file unit. The future source unit
    records this rule in `WORKFLOW.md` and `docs/specs/pm-handoff.md`.

## Scope

- **In:** the plan above, recorded in this tracker; the advice record
  `odd/advice/verification-budget.md`; the `docs/TODO.md` queue entry; one `ROUTER-LOG.md` row.
- **Out (future source unit):** all `WORKFLOW.md`, `docs/specs/**`, `global-config/**`, test,
  verifier and prompt edits; the owner restart and deploy.
- **Future delivery (U2 policy, not enacted here):** record the owner's writer-tier rule — local
  writers take exactly ONE file change per Task; cloud writers may batch a coherent multi-file
  unit — in `WORKFLOW.md` and `docs/specs/pm-handoff.md`.

## Constraints and non-goals

- Planning-only: no source, test, verifier, config, prompt or pin edit; no commit, deploy, branch
  switch, push or PR.
- Artifacts are English, compact and factual. Observations, inferences and proposed decisions are
  labelled.
- Never claim a check, deploy or live behaviour not observed.

## Acceptance criteria (future source implementation)

- **Scope note:** these are full-feature acceptance criteria; U2a is PARTIAL and U2b (overlay/regeneration) remains pending.
- `WORKFLOW.md`, `docs/specs/pm-handoff.md`, both route SKILLs and `overlay.md` state the finite
  matrix and the one-correction ceiling consistently; the six route classes are unchanged.
- The docs allowlist is explicit and fails closed; a test/verifier reader reclassifies a unit as
  normative with its execution checks.
- The regeneration chain (items 7-8) is atomic and its tests pass; `correction_rounds_used` is
  recorded with no silent reset.
- No new `verify-workflow.sh` check or digest change.
- Future U2 records the local-writer one-file dispatch rule (cloud writers may batch a coherent
  multi-file unit) in `WORKFLOW.md` and `docs/specs/pm-handoff.md`; this planning unit does not
  enact it.

## Tasks

- `T0` (this unit, `q87-verification-budget-plan-u1`): create the tracker and advice record; add the
  TODO and ROUTER-LOG entries. Planning only.
- `T1` (future, `q87-verification-budget-src-u1`): implement the finite matrix and docs boundary
  across `WORKFLOW.md`, `docs/specs/pm-handoff.md`, both route SKILLs, and the tests.
- `T2` (future, `q87-verification-budget-src-u2`): align `overlay.md`, regenerate the embedded
  prompt, and update the digest/ledger atomically (folds Q88).
- `T3` (future): fold the Q84 sequencing drift into the aligned surfaces.

## U2a source unit evidence (in progress)

- Unit: `q87-verification-budget-src-u1` (U2a), 2026-10-21. Class:
  `global-tooling-change`. Route: delegated. `workflow-odd-secure` was loaded first, then
  `workflow-route`, by the PM; this worker did not re-observe those skill calls. Triggers:
  preparation, multiple non-trivial files, secure delegated mutation.
- Scope split (owner override of the full-feature delivery): U2a changes only the finite policy,
  docs allowlist, one-correction cap, local-writer rule, envelope, route SKILLs and tests. U2b is
  EXCLUDED from this unit and still pending: `overlay.md`, assembled `global-config/opencode.json`,
  prompt regeneration, `CURRENT_PROMPT_SHA256`, normative ledger, and `advisor-gemini-post` prompt.
  U2a therefore does NOT establish full source/prompt equality.
- Pre-code advice: `advisor-integration-pre` Task `ses_e9f8386eaffeAOIdz1LMHjLupw`, configured
  `opencode-go/kimi-k2.7-code`; runtime fallback was not independently attested. Findings treated
  as evidence, not approval: B1 split the tracker feature acceptance from the U2a scope; B2 replace
  the open-ended refinement loop; B3 add the finite matrix; B4 add the correction counter to the
  result envelope; B5 add mutation-positive controls; B6 preserve the existing anchor and tiny-fix
  contracts. The advisor's suggestion of a separate verifier-anchor commit is not adopted because
  it could break anchor/token integrity; anchors, source and tests stay together if a verifier edit
  proves necessary.
- PM readback: `docs/TODO.md:1433-1436` already separates policy/tests from overlay/regeneration;
  the acceptance criteria at this tracker's lines 125-130 are FULL-FEATURE acceptance. U2a is
  PARTIAL against them and U2b remains pending; no claim of full alignment.
- Verification plan: tests first, then policy text, same final candidate. No new anchors or verifier
  checks; verifier/pin edits only if an existing row requires textual change.
- Owner override (2026-10-21, English, factual): a new Pyright diagnostic
  `tests/test_pm_handoff_spec.py:359:84` (`"group" is not a known attribute of "None"`) after the one
  correction round authorized one null-check in one file; new limit: one cloud `odd-apply` writer
  plus targeted module test/scoped diagnostics only, no full advice/verifier cycle, no U2b;
  `correction_rounds_used` stays `1`, recorded separately with no silent reset; used exactly one
  writer `ses_e9f597b78ffe3ckTuejCTsijRt`. Observed (writer/PM-attributed, not re-run here):
  `python3 -m unittest tests.test_pm_handoff_spec -v` → 25 tests OK; result one test path `+3/-1`,
  patch 857 bytes; PM `aft_inspect` after apply FRESH authoritative `1/1`, 0 errors, 0 warnings;
  blockers `F01`/`Q87-V01`/`Q87-V02` closed by that targeted recheck, no new cycle; no host source
  commit yet; assessment, U2b and metadata closure pending.

## Checks (this planning unit)

- `git status`/branch/baseline and changed-path inventory (sandbox).
- `git diff --check`; exact changed paths and stat; boundary resolution equals the expected base.
- Staged reviewability receipt: authored additions plus deletions, raw patch bytes, generated/binary
  paths.
- No runtime tests, advisor Tasks or verifier Tasks are required for planning-only artifacts.

## Advice reference

- `odd/advice/verification-budget.md`: two external manual reports (Claude Code/Anthropic;
  Antigravity/Gemini/Google), 2026-10-21, `selection.rule: external-manual`; the automated external
  lane is PLANNED. Reports are evidence, not approval.

## Route and trigger evidence

- Route: delegated. Specialist for this correction: cloud `odd-apply` (session
  `ses_e9faeabf6ffePAqD0AFjm2mT6k`). Triggers fired: preparation, two-file/four-path planning,
  secure no-inline-mutation.
- The host-retained U1 plan/advice/TODO text is preserved; this correction does not claim that
  `odd-apply` authored the original plan.
- The first cloud dispatch was malformed. The later cloud `odd-apply` session
  `ses_ea056c221ffeWZbhO5QyOZN5J6` failed with `fallback_chain_exhausted` (fallback log 3967–3968).
- The local `gentle-ai-worker-local` session `ses_ea04ab2d1ffeApUt5iTA2xDgqv` completed retained
  211-authored-line/27,772-byte text after stalls (log 3999–4000); it was not installed because the
  host already held the retained text.
- This cloud `odd-apply` Task applies only the authorized correction. Researcher
  `ses_ea061f549ffeaFsPWPWjWp7Pua` completed before dispatch. No plan commit hash is claimed.

## Next step

- PM result readback, host commit of the four paths, and risk assessment. The Magic Context mirror
  tool is unimplemented; no mirror body was accessed.
