# Q77 — PM mirror readback under Magic Context 0.46

Metadata: Feature: PM-layer completion. Task ID `q77-pm-mirror-readback`. Class: global-tooling-change. Route: `workflow-odd-secure` (delegated). Unit status: T0 IN PROGRESS. Model: cloud `opencode-go/deepseek-v4.1-flash`.

## Objective

Make `docs/specs/pm-handoff.md`'s mandatory tracker/mirror readback achievable by a PM, given that Magic Context 0.46 removed `ctx_memory` from subagents.

## Problem

OWNER-CONFIRMED 2026-10-17: as of Magic Context 0.46, `ctx_memory` is deliberately unavailable to subagents — this is by DESIGN, not a broker or runtime gap. Subagents keep the read-side tools (`ctx_search`, `ctx_expand`, `ctx_reduce`) but not `ctx_memory`/`ctx_note`. Consequence: `docs/specs/pm-handoff.md:28` requires "complete Magic Context mirror readback before DONE" and `:117` requires the PM to read back "the final committed tracker and its complete Magic Context mirror", and a PM CANNOT do either. OBSERVED evidence: two live `pm-odd` dispatches returned BLOCKED naming `ctx_memory` unregistered and explicitly refusing to accept a `ctx_search` preview as the complete body; a `gentle-ai-explore` tool-registration probe found `ctx_search`/`ctx_expand`/`ctx_reduce` PRESENT and `ctx_memory`/`ctx_note` ABSENT. The orchestrator DOES have `ctx_memory` and can read a complete body via `action: "get"`.

## Scope

In scope: the SPEC change (U1) — the brief field, the PM readback clause, the result-envelope field, and a schema test. Out of scope: the prompt changes (U2: the orchestrator overlay, both PM prompts, the regeneration chain); registering `ctx_memory` for subagents (that would fight the plugin's deliberate design — DO NOT propose it); any broker change.

## Design (owner-agreed) — HASHES, NOT BODIES

The orchestrator reads the mirror (it can) and supplies `tracker_sha256` and `mirror_sha256` in the brief. The PM reads the TRACKER FILE itself (it can), hashes it, and requires agreement with the supplied `tracker_sha256`; it reports the comparison outcome. Rationale: the PM never needs the memory body; two 64-char fields are far smaller than a multi-KB body (a tracker can be 20-30 KB and the brief has no documented cap); hashing is byte-deterministic where text comparison is not; and requiring the PM to hash the FILE itself preserves the independent check — if the orchestrator supplied both sides, one failure could make them agree while both diverge from the canonical tracker.

## Constraints

The spec is prose, asserted by no repo test today; the change must keep the document internally consistent (`:7` the brief fields, `:28` the readback requirement, `:96-99` the result envelope, `:113` the metadata worker's mirror-write ownership, `:117` the pre-DONE obligation); the metadata worker still OWNS the mirror write (`:113`) — only the READ is being re-routed; never commit; never switch branches.

## Acceptance criteria

- The brief field list carries the new hash field(s).
- The PM's obligation is stated as "compare the supplied `tracker_sha256` against a hash you compute over the committed tracker file; BLOCKED on mismatch", with an explicit outcome for absent/empty/mismatched values.
- The result envelope records the comparison and its method.
- The metadata worker's mirror-write ownership is unchanged and stated.
- The document is internally consistent.

## Authorized scope

U1: `docs/specs/pm-handoff.md`, `tests/test_pm_handoff_spec.py` (create). Plus this tracker, the advice record, `docs/TODO.md`, `ROUTER-LOG.md`.

## Checks

- `python3 -m unittest tests.test_pm_handoff_spec -v`
- `python3 -m unittest discover -s tests`

The PM's RUNTIME behaviour is NOT repo-testable; the falsifier is a live `pm-odd` dispatch whose result envelope records the hash comparison — HOST-ONLY.

## Tasks

- [x] T1 — add the hash field(s) to the brief field list; reword the readback clause at :28/:117 to the compare-supplied-hash obligation with its BLOCKED outcomes; record the comparison in the result envelope; keep the metadata worker's write ownership; add tests/test_pm_handoff_spec.py asserting the schema with a positive control.

## Delivery strategy

**Chosen strategy:** stacked-to-main (owner decision 2026-10-14). **Forecast:** T0 ~190; T1 ~90. Total ~280, under the about-400 accumulated threshold. **Selected AT tracker creation** per odd-and-review.md:36.

## Progress

- 2026-10-17: T0 — tracker, advice record and queue entry created. Route: delegated.
- 2026-10-17: T1 — updated `docs/specs/pm-handoff.md` with orchestrator-supplied `tracker_sha256`/`mirror_sha256`, PM-computed committed-tracker SHA-256 comparison and named BLOCKED outcomes, comparison evidence in the result envelope, and preserved metadata-worker mirror-write ownership. Added `tests/test_pm_handoff_spec.py`; targeted suite: 5 passed. Positive control mutates away `mirror_sha256` and confirms the schema assertion raises `AssertionError`. Full suite: 192 tests, 182 passed, 10 errors because sandbox execution denied `node` in pre-existing `test_gemini_advisor_route.py` subprocess checks. PM runtime behavior remains NOT repo-testable; falsifier is a live `pm-odd` dispatch whose result envelope records the hash comparison — HOST-ONLY.

## Route / trigger evidence

Route: delegated. Specialist: `general` (non-DeepSeek; the orchestrator is DeepSeek). Trigger: secure no-inline-mutation policy. RDD: on (decided by global).

## Next step

U2 (the prompts + regeneration), then a live smoke test.
