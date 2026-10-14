# Q68 — Sandbox lifecycle ordering in the worker prompts

**Feature:** worker-safety prompt hardening
**Task ID:** q68-sandbox-lifecycle-prompts (stable)
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0 IN PROGRESS (tracker + advice created; T1 pending)
**Model:** cloud `opencode-go/deepseek-v4.1-flash`

## Objective

Make the sandbox lifecycle order (call `sandbox_finish` BEFORE `sandbox_apply`) explicit in the
three worker agent prompts, so a worker cannot lose its edits by applying first.

## Problem

OBSERVED 2026-10-14 in this repo: a worker called `sandbox_apply` before `sandbox_finish`; it failed
with `session <id> has no worker recorded — fail closed`, REVERTED the worker to a fresh baseline,
and DISCARDED all edits. Re-applying the edits and calling `sandbox_finish` then `sandbox_apply`
succeeded. The lifecycle is documented as `sandbox_finish` exports the result and `sandbox_apply`
consumes it (`global-config/AGENTS.md:264-266`), and a worker is terminal after apply
(`AGENTS.md:269-271`, `WORKFLOW.md:436-438`) — but the three worker prompts never state the ORDER,
so the rule is discoverable only by losing work.

## Scope

### In scope

T1 adds the ordering rule to the three agent prompts in `global-config/opencode.json`: `general`
(prompt `:218`), `gentle-ai-worker` (`:367`), `odd-apply` (`:2170`); and adds a committed test
asserting the rule is present in all three, with a non-vacuous positive control.

### Out of scope (deliberately deferred, with reasons)

- (a) a clarifying sentence in `global-config/AGENTS.md`'s sandbox-tool-contract block:
  `recover_agents_file` does NOT recover that block (it recovers only codegraph,
  subagent-cancellation, grep-enforcement and workflow-routing — `verify-workflow.sh:906-914`,
  `:970-983`), so such an edit is INERT on deployment; making it live would require extending the
  recovery and re-pinning `VERIFY_SCRIPT_SHA256`.
- (b) `WORKFLOW.md:436` documentation: would not reach agents.
- (c) Any broker-side change: the refusal is a broker guarantee, not repo behaviour.

## Constraints

- The change edits `global-config/opencode.json`, a ~2406-line tracked JSON file that the verifier
  regenerates into the live config; the edit MUST be byte-preserving TEXT insertion inside the
  existing prompt strings (no `jq`, no `json.dumps` re-serialization, no re-flowing, keep 2-space
  indentation, keep the existing `\n` escape style, keep the surrounding `<!-- … -->` markers
  intact).
- The file must re-parse
  (`python3 -c 'import json; json.load(open("global-config/opencode.json"))'` exit 0); the verifier
  compares PARSED JSON, not bytes (`verify-workflow.sh:539`).
- NO `VERIFY_SCRIPT_SHA256` re-pin is needed because nothing in `verify-workflow.sh` asserts these
  prompts' text (`assertCfgWriter:2764-2777` checks tool SHAPE only; `required_agents:369-380` is
  membership only).
- The deployed runtime only sees new prompts after an OpenCode restart (owner action).
- Branch `chore/sandbox-lifecycle-in-prompts`; never commit; never switch branches.

## Acceptance criteria

- All three prompts carry the rule.
- The rule states the ORDER and the consequence (apply-first fails and discards edits).
- A committed test asserts presence in all three with a positive control proving the assertion can
  fail.
- `global-config/opencode.json` still parses.
- No unrelated line changes.
- The routing-guard and python suites stay green.

## Authorized scope

T1: `global-config/opencode.json`, `tests/test_sandbox_lifecycle_prompts.py` (new). Plus this
tracker, the advice record, `ROUTER-LOG.md`.

## Checks

- `python3 -c 'import json; json.load(open("global-config/opencode.json"))'` rc 0.
- A per-agent presence probe printing True/True/True for the three names.
- `python3 -m unittest tests.test_sandbox_lifecycle_prompts -v`.
- `python3 -m unittest discover -s tests`.
- `HOME="$(mktemp -d)" bun test tests/routing-guard`.
- `git diff` scoped to insertions inside the three prompt strings only.

## Tasks

- [ ] T1 — insert the ordering rule into the three prompts; add
  tests/test_sandbox_lifecycle_prompts.py with three assertIn cases plus a PositiveControl class
  that plants a tampered prompt and asserts rejection; verify JSON parse and the scoped diff.

## Delivery strategy

**Chosen strategy:** `stacked-to-main` (owner decision 2026-10-14; consistent with the repo's
current delivery rule).

**Forecast (authored additions + deletions, generated files excluded):** T0 tracker+advice+queue
≈ 170; T1 three prompt insertions + the new test ≈ 90. **Forecast total ≈ 260**, under the
about-400 accumulated delivery threshold.

**Selected AT tracker creation**, per `odd-and-review.md:36` — unlike Q67, whose strategy was
recorded only after its commits landed (a recorded process gap).

## Progress

- 2026-10-14: T0 — tracker, advice record and queue entry created; delivery strategy selected at
  creation. No source edit yet. Route: delegated.

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply`.
- Trigger: secure no-inline-mutation policy; multiple non-trivial files → bounded sandbox writer.
- RDD: on (decided by global).

## Next step

T1 implementation, then its native review (risk tier to be assessed; the change touches a large
tracked config plus a test), then the metadata record.
