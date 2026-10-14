# Q68 — Sandbox lifecycle ordering in the worker prompts

**Feature:** worker-safety prompt hardening
**Task ID:** q68-sandbox-lifecycle-prompts (stable)
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0–T1 DONE (committed and reviewed; deployment pending the owner).
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

- [x] T1 — insert the ordering rule into the three prompts; add
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
- 2026-10-14: T1 committed `a80ef09` (2 files, +118/−4; authored 117 lines). The rule was inserted into all three prompts as a byte-preserving inline string segment: `general` (:218, after its sandbox sentence), `gentle-ai-worker` (:367), `odd-apply` (:2170). `tests/test_sandbox_lifecycle_prompts.py` added (114 lines, 5 tests): module-level `NEEDLE` + `AGENT_NAMES`, a repo-relative config path resolved from `__file__`, and a `PositiveControl` class proving the validator reports a removed needle, an absent agent key and a non-string prompt — so a green run is not vacuous. Checks: presence probe [True, True, True]; `python3 -m json.tool global-config/opencode.json` exit 0 (the brief's one-liner was blocked by the sandbox argv guard because `;` is a rejected metacharacter — the equivalent `json.tool` check was used instead); new suite `Ran 5 tests OK`; `python3 -m unittest discover -s tests` 127 → 132 OK; routing-guard 96 pass / 0 fail; the scoped diff is exactly 3 hunks at :218/:367/:2170 with no whitespace drift and `git diff --check` clean.
- 2026-10-14: T1 native review: lineage `review-a87bf254a54ea61b`; tier **medium** (configuration change in `global-config/opencode.json`); candidate 9 paths / 499 lines (the accumulated slice from base `4a2eef60`); ONE lens selected (`review-reliability`, a medium-risk consolidated review, not the 4-lens high-risk plan); outcome **approved** and **acknowledged**; `authority: burned`; consumed revision `sha256:908f47ec…`. Captured on the FIRST dispatch — the raised relay deadline removed the transport failures seen earlier the same day.
- 2026-10-14: T1 advisory finding (non-blocking, informational; never a re-review trigger): `R3-001` (reliability SUGGESTION, `global-config/opencode.json:2366`) — the reviewer flagged that `@fro.bot/systematic` is bumped 3.21.5 → 3.21.8 without explicit justification in the Q68 scope. ANSWERED, not a defect: that bump is the VERIFIER's own canonical pin sync (a plain `bash verify-workflow.sh` run writes a newer deployed plugin pin back into the tracked source), recorded as intended behaviour. It rides in this accumulated candidate only because it was uncommitted at the time; it is unrelated to Q68's own change.
- 2026-10-14: FOLLOW-UP identified by the T1 worker and NOT actioned here (out of the authorized scope): `gentle-ai-worker-local` carries the SAME sandbox-tools sentence at `global-config/opencode.json:416` but did NOT receive the lifecycle rule. If the ordering trap applies to it too, it needs the same one-line insertion; recorded as a candidate follow-up rather than silently widening this unit.

## Route / trigger evidence

- Route: delegated.
- Specialist: `odd-apply`.
- Trigger: secure no-inline-mutation policy; multiple non-trivial files → bounded sandbox writer.
- RDD: on (decided by global).

## Next step

Q68 source work is COMPLETE (T0–T1; T1 reviewed and acknowledged). OWNER ACTION: run `bash verify-workflow.sh` to mirror the edited config into `~/.config/opencode/opencode.json`, then restart OpenCode — the RUNNING process keeps the old prompts until then, which no check in this repo can observe. Carry-forward: `R3-001` (answered above) and the `gentle-ai-worker-local` follow-up.
