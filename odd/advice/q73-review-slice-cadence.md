# Q73 — Native-review slice cadence — Advice record

## advisor-integration-pre (2026-10-16)

Pre-code advice (integration lens); load-bearing points only:

- **The cap is ALREADY contractual — do not duplicate it.** The per-commit cap and the serialized
  budget are pinned literals today: `verify-workflow.sh:4499` (`400 authored changed lines and
  100 KiB`), `:4500` (`200 KiB serialized per-runtime review-input budget`), `:4501`
  (`review-size-exception`), `:4543` (the odd-and-review mirror), and `:4574` (the AGENTS entrypoint,
  `final 200 KiB serialized-input authority`). The cadence rule must ADD a rule, never re-state these
  numbers, or the same literal is contractual in two places and can drift.
- **Three prose surfaces must mirror, each under an existing anchor.** (1) `WORKFLOW.md`, inside
  `workflow.work-unit-review` (`WORKFLOW.md:88-99`). (2) `odd-and-review.md`, inside
  `workflow.odd-and-review.work-unit-review` (`:27-38`). (3) `session-decisions.md`, inside
  `workflow.session-decisions.reviewability-budget` (`:54-59`), whose keystone literal is
  `authored_patch_bytes` and whose manifest row is `verify-workflow.sh:4471`. A new contractual
  literal is legal ONLY as a new `ANCHOR_TOKENS` row (`:4494-4577`); no existing row may be deleted
  to make room, and each new row's anchor id must already exist in `ANCHOR_MANIFEST` (`:4444-4478`).
- **`CLAIM-RETRACTIONS.md` carries the three directly relevant historical failures, and they dictate
  the rule's wording.**
  - `:38-39` (2026-09-27): a `baseRef=<previous commit>` window is always `under_budget`, so
    `review_due` never fired; the documented form is the last REVIEWED BOUNDARY, not the previous
    commit.
  - `:40` (2026-09-27): the accumulated `changed_lines` shortfall matched a net base-to-HEAD diff
    collapsing lines re-edited across commits (`a base-to-HEAD candidate counts each line once`).
  - `:58` (2026-09-29): a scoped base-ref IS executable — a 36-line candidate reviewed and closed
    approved, advancing the boundary to the tip.
  The rule must therefore **FORBID** `baseRef=<previous commit>` explicitly and **ENDORSE**
  `baseRef=<last reviewed boundary>` scoped to the accumulated slice.
- **No outcome-record schema exists today.** Native review records tier/reason/consumed/outcome in
  prose in the tracker; there is no machine schema for a closure record. The closest existing
  contractual token is `verify-workflow.sh:4502` (`Do not leave the evidence update uncommitted`).
  The rule should name who records the closure (the orchestrator, in the tracker and Magic Context
  mirror) rather than invent a schema.
- **The integration advisor's proposed wording.** A short paragraph — "close the accumulated
  medium-risk slice BEFORE the next high-risk commit" — with (a) the trigger (a high-risk commit is
  next), (b) the mechanism (`gentle-ai review assess --base-ref <last reviewed boundary>
  --committed-only` scoped to the accumulated slice), (c) a **path-count guard of about 12** as the
  observable that predicts refusal, and (d) the explicit rejection of the upstream inline path
  because `gentle-orchestrator` has NO write capability, so an inline fix is impossible here.
- **Advisor uncertainty (recorded, not resolved).** The measured path counts were 12 paths PASSED and
  18-22 REFUSED; the advisor could not pin the true ceiling and states it could be 13-15. The rule
  should say "about 12" and point at the measurement, not assert a hard ceiling.

## advisor-testing-pre (2026-10-16)

Pre-code advice (testing lens); load-bearing points only:

- **The anchor and token machinery asserts STRUCTURAL presence only, never behaviour.**
  `anchor_check_row` (`verify-workflow.sh:4386-4442`) proves a marker pair exists, is ordered, has a
  non-empty interior after comments/headings/whitespace, and contains the keystone literal; the
  `ANCHOR_TOKENS` loop (`:4579-4588`) proves a literal string is present in an anchor's interior. It
  never proves the orchestrator ACTS on the rule. `tests/test_anchor_manifest.py:46-73` likewise
  validates table structure (non-empty fields, known anchors, unique manifest ids) and says nothing
  about meaning. So a green verifier + green anchor test is necessary, not sufficient.
- **The falsifier for the rule is a `ROUTER-LOG.md` row.** The rule is violated when a high-risk
  commit lands while medium commits still sit between the boundary and HEAD, and the boundary then
  advances past them with no acknowledged review. Record this as the falsifier; there is no
  mechanical observer, so it must be stated as an explicit falsifier in the rule text.
- **The 200 KiB ceiling is PROVIDER-OWNED and not repo-testable.** It lives in the native
  gentle-ai START guard, not in this repository; record it as a measured observation only. The repo
  may not claim to enforce it.
- **What must NOT be weakened.** `WORKFLOW.md:93` (the cap + `review-size-exception` path);
  `:125`/`:128` (the routing-decision rules — changed-line count never selects a route);
  `:97` (`never rewritten retroactively` belongs in tracker and router log, not the commit);
  the Q26 `ANCHOR_MANIFEST`/`ANCHOR_TOKENS` tables (no row may be deleted to add one);
  `tests/test_anchor_manifest.py`'s `PositiveControl`; and the routing-guard suite. The new test must
  carry its own planted-wrong-prose positive control so a green run is not vacuous.
- **Recommended verification set.** Repo-testable: `bash -n verify-workflow.sh`, the new
  `tests/test_review_cadence.py`, `tests.test_anchor_manifest`, `python3 -m unittest discover -s
  tests`, a fake-HOME `bun test tests/routing-guard`, and `sha256sum verify-workflow.sh` equal to the
  `VERIFY_SCRIPT_SHA256` pin. NOT repo-testable: the orchestrator actually closing the slice first
  (the falsifier above), and the provider-owned 200 KiB ceiling.
