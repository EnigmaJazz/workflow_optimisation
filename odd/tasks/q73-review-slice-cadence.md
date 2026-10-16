# Q73 — Native-review slice cadence

**Feature:** align the review cadence with gentle-ai v4.2.0's slice rule
**Task ID:** q73-review-slice-cadence (stable)
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0 IN PROGRESS (tracker + advice; T1 pending).
**Model:** cloud `opencode-go/deepseek-v4.1-flash`

## Objective

Make the accumulated medium-risk slice close BEFORE a high-risk commit lands, so the native review
never receives an oversized candidate.

## Problem

OBSERVED this session: medium-risk commits assess as `under_budget` with `review_due: false`, so the
pending slice accumulates (`WORKFLOW.md:95`). A later high-risk commit makes the whole accumulation
due at once, and `review start` refuses it with `lens_context_budget_exceeded`
(`mutation_outcome: not_started`; retrying that candidate cannot succeed). Measured: 418 lines /
12 paths PASSED; 692 / 11 PASSED; 845 / 19, 1041 / 22 and 1089 / 18 REFUSED. Path count appears to
dominate. The only remedy is a later `--base-ref`, which advances the boundary and SKIPS intervening
commits — that happened once already (`e39d252a..a4e81b5` skipped).

## Scope

### In scope

T1 adds the cadence rule to THREE prose surfaces and pins it.

### Out of scope (deliberately deferred, with reasons)

- the 400-line / 100 KiB per-commit cap and the 200 KiB serialized budget (ALREADY contractual
  tokens at `verify-workflow.sh:4499-4501`, `:4543`, `:4574` — do not re-state them);
- any routing-decision rule change (`WORKFLOW.md:125`/`:128`).

## Constraints

- the cadence rule must NOT contradict `WORKFLOW.md:125`/`:128` (a changed-line count never SELECTS a
  route); it is a review-cadence rule, not a routing rule;
- the terminology must distinguish the PER-COMMIT cap from the SLICE-WINDOW budget;
- `WORKFLOW.md:93`'s `review-size-exception` path stays legal (the cadence rule applies after it);
- the Q26 anchor/token tables are the only legal way to add a contractual literal, and a row must
  never be deleted to add one;
- `VERIFY_SCRIPT_SHA256` re-pins LAST if `verify-workflow.sh` is edited;
- never commit; never switch branches.

## Acceptance criteria

- the cadence rule appears in `WORKFLOW.md`,
  `global-config/skills/workflow-odd-secure/references/odd-and-review.md` and
  `global-config/skills/workflow-route/references/session-decisions.md`;
- it states the trigger (a high-risk commit is next), the mechanism
  (`--base-ref <last reviewed boundary>` scoped to the accumulated slice), the FORBIDDEN anti-pattern
  (`baseRef=<previous commit>`), who records the closure, and the falsifier;
- the upstream inline path is explicitly rejected with the no-write-capability reason;
- a committed structural test with a positive control;
- the routing-decision rules are unchanged.

## Authorized scope

T1: `WORKFLOW.md`, `global-config/skills/workflow-odd-secure/references/odd-and-review.md`,
`global-config/skills/workflow-route/references/session-decisions.md`, `verify-workflow.sh`
(ANCHOR_TOKENS rows only) + the `VERIFY_SCRIPT_SHA256` pin, `tests/test_review_cadence.py` (new).
Plus this tracker, the advice record, `ROUTER-LOG.md`.

## Checks

- `bash -n verify-workflow.sh`;
- `python3 -m unittest tests.test_review_cadence -v`;
- `python3 -m unittest tests.test_anchor_manifest -v`;
- `python3 -m unittest discover -s tests`;
- a fake-HOME `bun test tests/routing-guard`;
- the sha256 == the pin.

## Tasks

- [ ] T1 — add the cadence rule to the three surfaces with matching ANCHOR_TOKENS rows, reject the
  upstream inline path explicitly, add tests/test_review_cadence.py with a planted-wrong-prose
  positive control, re-pin LAST.

## Delivery strategy

**Chosen strategy:** stacked-to-main (owner decision 2026-10-14).

**Forecast (authored additions + deletions, generated files excluded):** T0 ≈ 200; T1 ≈ 140.
**Forecast total ≈ 340**, under the about-400 accumulated threshold.

**Selected AT tracker creation** per `odd-and-review.md:36`.

## Progress

- 2026-10-16: T0 — tracker, advice record and queue entry created; delivery strategy selected at
  creation. No source edit yet. Route: delegated.

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply`.
- Trigger: secure no-inline-mutation policy; multiple non-trivial files.
- RDD: on (decided by global).

## Next step

T1 implementation, then native review, then the metadata record.
