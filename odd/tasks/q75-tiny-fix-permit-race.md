# Q75 — Tiny-fix permit race: bind the permit to the intended child

**Feature:** PM-layer completion
**Task ID:** `q75-tiny-fix-permit-race`
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T1 implementation and checks complete; no commit or native review (per instruction)
**Model:** cloud

## Objective

A tiny-fix permit must be granted only to the child the tiny-fix dispatch actually produced, never to an unrelated concurrent child.

## Problem

**Observed (Q72 T1a review, R3-tiny-fix-permit-race, WARNING):** `registerTinyFixChild` consumes the pending parent permit on the first `session.created` for that parent, binding only by `parentID` (`global-config/plugins/systematic-routing-guard.ts:832-840`). The event handler reads only the child `id` and `parentID` (`global-config/plugins/systematic-routing-guard.ts:856-861`), not agent or task identity. An unrelated child created first can therefore steal the permit; the intended writer is left without exemption while the unrelated child receives the sandbox-write exemption. Both independent pre-code advisors graded this a BLOCKER and independently identified insufficient identity information at the consumption point (per the T0 task brief; advisor names/reports were not supplied here).

The exploitable window is a tiny-fix dispatch concurrent with another task, a routine grouped-wave pattern. The PM dispatch path uses the same writer-dispatch handling: the flag is detected and the pending permit is set using `input.sessionID`, with no orchestrator/PM special case (`global-config/plugins/systematic-routing-guard.ts:1023-1034`).

## Owner decision (2026-10-15)

Bind by a **candidate set plus an observed-agent match**:

1. At `task` with `tiny_fix: true`, arm the pending permit with the expected writer agent, already identified as `isWriterDispatch` from `subagent_type` (`global-config/plugins/systematic-routing-guard.ts:990-993,1023-1034`).
2. At `session.created`, add the child to a candidate set keyed by parent; do not consume the permit.
3. When the child emits an agent-bearing `chat.message`, compare its observed agent to the expected writer. On match, consume the parent permit and grant the child permit. On mismatch, remove that candidate.
4. Clean up candidates on `session.deleted`, TTL expiry, and dispatches that never produce a child.
5. `tool.execute.after` may finalize or clean stale candidates, but must not bind: the child can write before this hook runs (`odd/tasks/q72-tiny-fix-route.md:131,137`; `global-config/plugins/systematic-routing-guard.ts:1112-1118`).

## Scope

**In scope:** T1 binding change; writer-agent normalization for expected-versus-observed comparison, including `-local` and `-astra`; candidate/permit cleanup; race tests, including the PM-dispatched path.

**Out of scope:** changing the 30-minute TTL shared with workflow-key TTL; orchestrator-side gate behavior; `verify-workflow.sh`.

## Constraints and unresolved evidence

- Runtime evidence supplied for this unit establishes child event delivery on the observed path; whether all plugin instances share in-memory state remains **UNVERIFIED**. Do not generalize beyond the observed route.
- `input.agent` is observed, not authenticated (`global-config/plugins/systematic-routing-guard.ts:325-331,875-880`). Matching reduces accidental misbinding but does not eliminate spoofing risk.
- In-repo tests directly invoke the hook and remain synthetic; runtime evidence is the separate 2026-10-15 log observation recorded below.
- Agent normalization for writers does not currently exist. The helper normalizes `-astra` for PM adapter identity only (`global-config/plugins/lib/routing-guard-helpers.ts:37-49`); do not mistake that for writer normalization.
- `task_id`, `background`, and retry timing are not established as child identity signals; investigate before relying on them.
- Do not claim T1a mutation proofs M1/M2/M3 are durable evidence: they were ad hoc and are not in-repo, so their validity after this binding change is unconfirmed.

## Acceptance criteria

- A non-writer child of the same parent cannot steal the permit; the intended writer still gets it.
- The prior `1d` child-permit test is updated to require a candidate with a matching observed writer message; the other existing permit cases remain green.
- A race test creates a non-matching child FIRST and intended writer SECOND; the mismatch receives the normal bootstrap warning and the matching writer receives the one-shot permit.
- A tiny-fix executable-file tripwire warns on script/executable extensions and shebang content; its warning-only and pre-apply limits are recorded.
- Expected/observed writer normalization covers `-local` and `-astra` variants.
- Runtime evidence establishes the child-session delivery path described below; observed agent identity remains unauthenticated and plugin-instance topology remains an explicit limitation.
- One-shot consumption, TTL, own-session-only semantics, existing negative controls, and non-vacuity controls are preserved.

## Authorized scope

T1: `global-config/plugins/systematic-routing-guard.ts`, `global-config/plugins/lib/routing-guard-helpers.ts` (writer normalization only), and `tests/routing-guard/routing-guard.test.ts`. T0 artifacts: this tracker, `odd/advice/q75-tiny-fix-permit-race.md`, and one `docs/TODO.md` queue entry. Do not edit other paths. No commit; never switch branches.

## Checks

- Fake-HOME `bun test tests/routing-guard`.
- Record a genuine RED-then-GREEN proof for the new race test.
- Confirm the existing five `1d` cases stayed unmodified and green.
- `python3 -m unittest discover -s tests`.

## Tasks

- [x] T1 — replace first-child-wins consumption with candidate-set plus observed-agent binding; normalize writer variants; add a non-writer-first race test with a positive control; record runtime evidence and tripwire limits honestly. PM path uses the same `isWriterDispatch` hook and is covered by the executable-file test's PM parent.

## Delivery strategy

**Chosen strategy:** stacked-to-main (owner decision 2026-10-14). **Forecast:** T0 ~200 authored lines; T1 ~150. Total ~350, under the about-400 accumulated threshold. Selected at tracker creation per `global-config/skills/workflow-odd-secure/references/odd-and-review.md:36`.

**Risk note:** a medium-risk slice is pending from Q74's record fix (21 lines). If T1 assesses high-risk, the Q73 cadence rule requires closing that slice first via review assessment with `--base-ref <last reviewed boundary>`.

## Progress

- 2026-10-16: T0 — tracker, advice record, and queue entry created; owner decision on binding recorded. No source edit. Route: delegated.
- 2026-10-16: T1 — expected-writer candidate binding and executable-file tripwire warning implemented. Fake-HOME routing-guard suite 102 baseline → 103 pass / 0 fail; match-check removal reproduced the race-test failure (Expected 1 / Received 0); Python suite 155 pass; anchor-manifest suite 7 pass; `bash -n verify-workflow.sh` and `git diff --check` pass. Verifier SHA-256 pin: `09d57f7c29d2e88efd6b3699a8f207d918c86e3dffde097d25484172dd150d50` (matched by the verifier's `read_verify_script_pin` regex). No commit or branch switch.

## Route / trigger evidence

- Route: delegated.
- Specialist: `general` (cloud; selected as non-DeepSeek so this unit is not written by a same-family writer).
- Trigger: secure no-inline-mutation policy; real defect with an owner-selected design decision.
- RDD: on (decided by global; no review lifecycle action in T0).

## T1 implementation and evidence

**Runtime evidence supplied for this unit (observed 2026-10-15):** the tiny-fix route completed end-to-end. `routing-guard.log` lines 58635-58636 show the guard reading and stripping the flag, arming the one-shot permit, and extending it to the exact child created by the dispatch; lines 58640-58641 show zero `routing gate:` warnings and the child's `sandbox_edit` exempt at the bootstrap gate. This establishes runtime delivery for the tested child route and resolves the prior child-session delivery blocker. It does not establish that every plugin-instance topology shares in-memory state or authenticate `input.agent`.

**Previously observed gap (observed 2026-10-15):** a tiny-fix dispatch whose target was an executable script assessed `risk: high`, `review_due: true`, with `process_boundary` / `shell_process`; nothing stopped it. The one-way tripwire denylist had no executable-file class. Q72 requires passive-only escalation for medium/high risk. The prior tripwire's pre-apply enforcement was not committed in T1a, so documentation alone did not close this gap.

**Fix implemented:** pending parent permits now retain the expected writer; `session.created` adds a candidate without consuming the permit; an observed `chat.message` grants only when its agent matches the expected writer after `-local` / `-astra` normalization. A mismatch candidate is dropped; if no candidate matches, the permit remains unused until its original TTL expires. Candidate/permit state is cleaned on session deletion and lazily swept on guard activity. The existing `tiny-fix permit consumed` dispatch log and child-extension log are preserved. A nonmatching-first race test has a normal bootstrap-warning positive control and a matching-writer success assertion.

The executable-file class now covers script/executable extensions and content opening with a shebang. The guard warns when a matched tiny-fix child writes such a file. **Residual, not covered:** the guard remains warning-only; it cannot inspect a completed candidate's final authored line/file counts or native risk assessment, and it cannot block `sandbox_apply`. Therefore pre-apply candidate/risk assessment remains the required escalation boundary; the guard warning is an early signal, not proof that escalation occurred. `input.agent` remains observed, not authenticated, and in-memory cross-instance sharing remains unverified beyond the supplied runtime observation.

## Next step

Run the required test, verifier syntax, anchor-manifest, Python, diff, and pin-coherence checks; then record exact results. No commit or branch switch is authorized.
