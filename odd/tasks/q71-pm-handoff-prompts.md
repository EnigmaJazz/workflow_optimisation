# Q71 — PM-handoff prompt gaps (orchestrator brief schema + PM complete-memory read)

**Feature:** PM-layer completion (Q56 pilot prerequisites)
**Task ID:** q71-pm-handoff-prompts (stable)
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0 IN PROGRESS (tracker + advice created; T1 pending).
**Model:** cloud `opencode-go/deepseek-v4.1-flash`

## Objective

Close the two prompt-teaching gaps that a live `pm-odd` smoke test exposed: an orchestrator cannot
build a valid `pm-unit-brief/v1`, and a PM cannot complete the mirror readback the contract
requires.

## Problem

OBSERVED 2026-10-15 via two live `pm-odd` dispatches:

(a) The orchestrator prompt (`global-config/opencode.json:590`, assembled from
`global-config/prompts/gentle-orchestrator/base.md` + `overlay.md`) contains ZERO `pm-handoff` and
ZERO `pm-unit-brief` text. The schema tag `pm-unit-brief/v1` exists in exactly ONE file repo-wide —
`docs/specs/pm-handoff.md:7,40,47`. Consequence: an orchestrator has no way to know the required
brief fields. A first smoke-test brief omitted `unit_id`, `task_id`, `tracker_path`, `task_class`,
`initial_plan`, `rdd_mode`/`rdd_mode_source` and `constraints`; `pm-odd` correctly returned `BLOCKED`
with `BRIEF_SCHEMA_INCOMPLETE`.

(b) Both PM prompts (`opencode.json:1921` `pm-odd`, `:2041` `pm-systematic`) already name
`docs/specs/pm-handoff.md` and already instruct "require … complete Magic Context mirror readback
before `DONE`" — but neither teaches the MECHANISM. The literal `"action": "get"` appears 0 times in
the file. A second smoke test therefore returned `BLOCKED` with
`MIRROR_COMPLETE_READBACK_UNAVAILABLE`, claiming "no complete memory-item read operation is exposed".
That claim is FALSE: `ctx_memory` supports `action: "get"` with `ids: [1-20]` and returns the
COMPLETE memory-item body (verified live by the orchestrator on memory id 1160), and BOTH PMs
already hold `ctx_memory: true` in their tool grants (`opencode.json:1939`, `:2059`) — corroborated
by `odd/tasks/pm-layer.md:198` ("Item 8 PASS — `ctx_memory` write (id 1087), read-back, and
`ctx_search` hit all succeeded"). So the tool exists and is granted; the prompts never teach it.

## Scope

### In scope

T1 adds (a) a PM-brief pointer plus the required-field list to the orchestrator prompt overlay;
(b) the `ctx_memory` `action: "get"` complete-read mechanism to BOTH PM prompts; and (c) a committed
test asserting both, with non-vacuous positive controls.

### Out of scope (deliberately deferred, with reasons)

Any change to `docs/specs/pm-handoff.md` (the contract is correct; the prompts are behind it); any
tool-grant change (the grants are already correct); any change to the verifier's assertions;
`pm-probe` (retired); `pm-sdd` (retired, Q65 `5aadb9f`).

## Constraints

- The orchestrator prompt is assembled: editing `overlay.md` REQUIRES regenerating the assembled
  prompt into `global-config/opencode.json:590` and updating `CURRENT_PROMPT_SHA256`
  (`tests/test_orchestrator_prompt_source.py:28`, current
  `c90727b3fc99ed1de2ff073685b435d58e6379668d92b3cad6644ea125d7b360`) and
  `global-config/prompts/gentle-orchestrator/normative-ledger.md`, or
  `verify-workflow.sh:2957-2968` fails `ORCHESTRATOR_PROMPT_ASSEMBLER_DRIFT`.
- The assembled sha changes for ANY overlay edit (an advisor claimed otherwise — that claim is WRONG
  and must not be relied on).
- `overlay.md` is a section-replacement overlay where `replace`/`remove` blocks carry a `supersedes`
  sha computed over the exact base section (adding to an existing `add`-type block needs no new sha,
  but the assembled bytes still change).
- The PM prompts are inline JSON strings and must be edited byte-preservingly (no re-serialization,
  keep `\n` escapes and 2-space indent) and stay valid JSON.
- Each PM prompt must stay under the ~6,000-character cap (`docs/specs/pm-handoff.md:11`; currently
  `pm-odd` 1,817 and `pm-systematic` 1,831 chars — ample headroom).
- `VERIFY_SCRIPT_SHA256` needs NO re-pin unless `verify-workflow.sh` itself is edited.
- `global-config/AGENTS.md` is the WRONG surface because `recover_agents_file` byte-compares only
  four bounded blocks (codegraph, subagent-cancellation, grep-enforcement, workflow-routing) so any
  other AGENTS edit is INERT on deployment.
- Branch `chore/pm-layer-completion`; never commit; never switch branches.

## Acceptance criteria

- The orchestrator prompt names `docs/specs/pm-handoff.md` and `pm-unit-brief/v1` plus the required
  field list.
- BOTH PM prompts teach the `ctx_memory` `action: "get"` complete-read mechanism.
- A committed test asserts each in its OWN agent's prompt (never against a joined string) with
  positive controls that prove each assertion can fail and that a substring present in a DIFFERENT
  agent's prompt does not silence the check.
- The assembled prompt, `CURRENT_PROMPT_SHA256` and the ledger agree.
- `opencode.json` parses.
- No unrelated line changes.
- The existing suites stay green.

## Authorized scope

T1: `global-config/prompts/gentle-orchestrator/overlay.md`, `global-config/opencode.json` (the
assembled orchestrator prompt at `:590` and the two PM prompts at `:1921`/`:2041`),
`global-config/prompts/gentle-orchestrator/normative-ledger.md`, `tests/test_pm_layer_prompts.py`
(new). Plus this tracker, the advice record, `ROUTER-LOG.md`.

## Checks

- `python3 -c 'import json; json.load(open("global-config/opencode.json"))'` rc 0.
- A per-agent presence probe printing the result for `gentle-orchestrator`, `pm-odd`,
  `pm-systematic`.
- The assembler run compared to `CURRENT_PROMPT_SHA256` and to the embedded prompt (three-way match).
- `python3 -m unittest tests.test_pm_layer_prompts -v`.
- `python3 -m unittest discover -s tests`.
- A fake-HOME `bun test tests/routing-guard`.
- `git diff` scoped to the intended regions only.

## Tasks

- [ ] T1 — add the brief pointer + required-field list to overlay.md; regenerate the assembled prompt
  into opencode.json:590; update CURRENT_PROMPT_SHA256 and normative-ledger.md; add the ctx_memory
  action:get complete-read instruction to BOTH PM prompts (:1921, :2041); add
  tests/test_pm_layer_prompts.py with per-agent assertions and positive controls including a
  cross-agent contamination control.

## Delivery strategy

**Chosen strategy:** `stacked-to-main` (owner decision 2026-10-14).

**Forecast (authored additions + deletions, generated files excluded):** T0 ≈ 200; T1 ≈ 120 (overlay
insertion + two prompt insertions + the new test), plus the regenerated assembled prompt counted as
generated. **Forecast total ≈ 320**, under the about-400 accumulated threshold.

**Selected AT tracker creation** per `odd-and-review.md:36`.

## Progress

- 2026-10-15: T0 — tracker, advice record and queue entry created; delivery strategy selected at
  creation. No source edit yet. Route: delegated.

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply`.
- Trigger: secure no-inline-mutation policy; multiple non-trivial files → bounded sandbox writer.
- RDD: on (decided by global).

## Next step

T1 implementation, then native review (assess the tier), then the metadata record.
