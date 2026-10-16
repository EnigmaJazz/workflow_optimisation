# Q75 — Tiny-fix permit race: bind the permit to the intended child

**Feature:** PM-layer completion
**Task ID:** `q75-tiny-fix-permit-race`
**Class:** global-tooling-change
**Route:** `workflow-odd-secure` (delegated)
**Unit status:** T0 IN PROGRESS (tracker + advice; T1 pending)
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

- Whether child-session events reach the same plugin instance is **UNVERIFIED**. State this as a limitation; do not silently rely on cross-session in-memory sharing.
- `input.agent` is observed, not authenticated (`global-config/plugins/systematic-routing-guard.ts:325-331,875-880`). Matching reduces accidental misbinding but does not eliminate spoofing risk.
- Whether `chat.message` fires for child sessions and carries their agent is an OPEN QUESTION. Current tests directly invoke the hook and do not establish runtime delivery (`tests/routing-guard/routing-guard.test.ts:70-72`). T1 must establish it with repository/runtime evidence before relying on it; otherwise fail closed and document the limitation.
- Agent normalization for writers does not currently exist. The helper normalizes `-astra` for PM adapter identity only (`global-config/plugins/lib/routing-guard-helpers.ts:37-49`); do not mistake that for writer normalization.
- `task_id`, `background`, and retry timing are not established as child identity signals; investigate before relying on them.
- Do not claim T1a mutation proofs M1/M2/M3 are durable evidence: they were ad hoc and are not in-repo, so their validity after this binding change is unconfirmed.

## Acceptance criteria

- A non-writer child of the same parent cannot steal the permit; the intended writer still gets it.
- The existing five `1d` permit cases remain unchanged and green (`tests/routing-guard/routing-guard.test.ts:383-461`).
- A new race test creates the stealer child FIRST and intended writer SECOND; it fails against the current implementation and passes after the fix, with a positive control proving the mismatch child still receives the normal bootstrap warning.
- The PM-dispatched path has a dedicated test.
- Writer normalization covers `-local` and `-astra` variants.
- The child-hook open question is resolved with evidence or the design fails closed and records why.
- One-shot consumption, TTL, own-session-only semantics, all five existing cases, and non-vacuity controls are preserved.

## Authorized scope

T1: `global-config/plugins/systematic-routing-guard.ts`, `global-config/plugins/lib/routing-guard-helpers.ts` (writer normalization only), and `tests/routing-guard/routing-guard.test.ts`. T0 artifacts: this tracker, `odd/advice/q75-tiny-fix-permit-race.md`, and one `docs/TODO.md` queue entry. Do not edit other paths. No commit; never switch branches.

## Checks

- Fake-HOME `bun test tests/routing-guard`.
- Record a genuine RED-then-GREEN proof for the new race test.
- Confirm the existing five `1d` cases stayed unmodified and green.
- `python3 -m unittest discover -s tests`.

## Tasks

- [ ] T1 — replace first-child-wins consumption with candidate-set plus observed-agent binding; normalize writer variants; add a non-writer-first race test with a positive control and a PM-path case; resolve or fail closed on the child-hook question; record evidence honestly.

## Delivery strategy

**Chosen strategy:** stacked-to-main (owner decision 2026-10-14). **Forecast:** T0 ~200 authored lines; T1 ~150. Total ~350, under the about-400 accumulated threshold. Selected at tracker creation per `global-config/skills/workflow-odd-secure/references/odd-and-review.md:36`.

**Risk note:** a medium-risk slice is pending from Q74's record fix (21 lines). If T1 assesses high-risk, the Q73 cadence rule requires closing that slice first via review assessment with `--base-ref <last reviewed boundary>`.

## Progress

- 2026-10-16: T0 — tracker, advice record, and queue entry created; owner decision on binding recorded. No source edit. Route: delegated.

## Route / trigger evidence

- Route: delegated.
- Specialist: `general` (cloud; selected as non-DeepSeek so this unit is not written by a same-family writer).
- Trigger: secure no-inline-mutation policy; real defect with an owner-selected design decision.
- RDD: on (decided by global; no review lifecycle action in T0).

## T1 observation unit (child-hook delivery evidence)

**Status:** instrumentation implemented; runtime observation pending. This is evidence-only and does not implement candidate-set binding. Binding remains unimplemented until the real-child observation establishes delivery, agent identity, and ordering before the child's first write.

**Instrumented:** `chat.message`, the only agent-bearing hook currently registered by this guard. The returned hook map in `global-config/plugins/systematic-routing-guard.ts` registers no `chat.params` callback, so this unit does not add one. `session.created` records child-session membership when `info.parentID` is a string, and `session.deleted` removes it. When `SYSTEMATIC_ROUTING_GUARD_OBSERVE_AGENT_HOOKS=1`, each `chat.message` invocation appends one temporary observation via `appendRoutingLog`; without the opt-in environment variable, the instrumentation is dormant.

**Exact emitted line format:** `YYYY-MM-DDTHH:mm:ss.sssZ [systematic-routing-guard] TEMP agent-hook hook=chat.message session=<URI-encoded-sessionID> agent=<URI-encoded-agent-or-none> child=<true|false>`. The timestamp is prepended by `appendRoutingLog`; `agent=none` means `input.agent` was not a non-empty string; an unencodable string field is recorded as `invalid` rather than throwing. `child=true` means this plugin instance observed a `session.created` event for that session with a string `parentID`; `child=false` means no such parent was observed by this instance. This instrumentation is explicitly TEMPORARY because it emits one line per message and would otherwise add sustained log volume; remove it after the runtime observation is recorded. It writes through `appendRoutingLog` to `~/.local/share/opencode/logs/routing-guard.log` by default and does not use stdout.

**Gather the observation:** after the canonical plugin is loaded in OpenCode (mirror/deploy the source through the approved verifier path and restart OpenCode), start a fresh session with `env SYSTEMATIC_ROUTING_GUARD_OBSERVE_AGENT_HOOKS=1 opencode`. In a second Fish-compatible terminal run `tail -f ~/.local/share/opencode/logs/routing-guard.log`. From the OpenCode session, dispatch the intended writer agent as a real child and have that child perform a harmless first write in a disposable worktree. Preserve the exact dispatched agent name and identify the child's first write in the task/tool trace. Match its child session ID against the log, then compare ordering: the `agent-hook` line must show `child=true`, its `agent` must equal the dispatched writer (after URI decoding), and that line must appear before the child's first write. A line missing, marked `child=false`, carrying another agent, or appearing after the first write does not establish the required contract. Close OpenCode after the probe so the temporary opt-in does not remain active.

**Check evidence boundaries:** an in-repo test directly invoking the hook remains synthetic and is not runtime-delivery evidence. If the required real-child line is not observed, do not implement binding; record the runtime limitation and fail closed. The candidate-set binding remains unimplemented pending this evidence.

## Next step

Collect and record the real-child observation. Only then decide whether a later unit may implement candidate-set binding; native review and metadata recording follow that implementation unit, not this evidence-only change.
