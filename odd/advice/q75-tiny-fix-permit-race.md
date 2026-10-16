# Q75 — Tiny-fix permit race — Advice record

## Finding and severity

**BLOCKER — bind a tiny-fix permit to the intended child, not the first child created by its parent.** The two independent pre-code advisors both graded the finding BLOCKER and independently identified insufficient identity information at the permit-consumption point (per the owner-provided T0 brief; advisor names and original reports were not provided for this record).

Observed implementation: `registerTinyFixChild` looks up a pending permit using only the parent session ID, immediately deletes that pending entry, and grants it to the first child session (`global-config/plugins/systematic-routing-guard.ts:832-840`). The `session.created` handler passes only `info.id` and `info.parentID` (`global-config/plugins/systematic-routing-guard.ts:856-861`). Consequently, a sibling or unrelated child created first can take the sandbox-write exemption, while the intended tiny-fix writer receives no permit. This is a race in child attribution, not a failure of the tiny-fix task flag itself.

## Identity available at each hook

| Hook | Evidence available | Consequence |
|---|---|---|
| `tool.execute.before` for `task` | Parent `input.sessionID`; task arguments at `output.args` (`global-config/plugins/systematic-routing-guard.ts:883-887`). The hook reads and strips `tiny_fix` (`:990-993`), normalizes a qualified agent name, derives `dispatchedType` and `isWriterDispatch` (`:1008-1027`), then arms the permit on the parent (`:1029-1034`). | This is where the expected writer must be captured. The code already has the writer agent identity, but current pending state records only expiry. |
| `session.created` | `properties.info.id` and `properties.info.parentID` only (`global-config/plugins/systematic-routing-guard.ts:856-861`; the test helper models exactly those fields at `tests/routing-guard/routing-guard.test.ts:71-72`). | Enough to collect parent-linked candidates, not enough to identify which task or agent created one. Current first-child consumption is unsafe. |
| `chat.message` | The guard's hook receives `input.sessionID` and observed `input.agent`, then persists that agent (`global-config/plugins/systematic-routing-guard.ts:875-880`). Its documented limitation says the latest observed agent can vary and is not authenticated (`:325-331`). | Candidate plus observed-agent comparison is the selected discriminator, subject to the child-hook delivery open question and spoofing limitation. |
| `tool.execute.after` for `task` | Parent session and output string; the child ID is parsed from `id="(ses_[A-Za-z0-9]+)"` (`global-config/plugins/systematic-routing-guard.ts:1112-1118`). | This arrives after the child may have run. It cannot safely be the permit-binding surface. |

The in-memory candidate/permit maps additionally assume parent and child events reach the same plugin instance; that assumption is UNVERIFIED and must remain an explicit limitation.

## Why the result hook is too late

The child can call a mutating tool before `tool.execute.after` handles the task result: `.parent` and `inherited.key` are written from the task result hook only after the task returns (`odd/tasks/q72-tiny-fix-route.md:131,137`; implementation `global-config/plugins/systematic-routing-guard.ts:1112-1158`). The in-memory permit map exists precisely to cover the child's earlier writes. The result hook may help finalize or clean stale state, but must not decide which child receives the permit.

## Recommended two-phase binding

1. On an explicit tiny-fix writer task, store parent → expected writer plus expiry. The target is already computed by the task hook (`global-config/plugins/systematic-routing-guard.ts:990-993,1023-1034`).
2. On `session.created`, add child → parent candidate membership; do not consume the parent permit.
3. On an agent-bearing child `chat.message`, compare the observed agent to the expected writer after canonicalizing writer variants. On a match, atomically consume the parent permit and grant the child permit. On mismatch, remove that candidate without consuming the parent permit.
4. Remove candidates on session deletion and TTL expiry; ensure a pending dispatch that never creates a child expires without leaving reusable state. Do not extend the existing 30-minute TTL.
5. Keep one-shot semantics and own-session-only permit lookup: a child permit applies only to the matching child session, not its siblings or the parent.

The synchronous map update that consumes a match must happen before any awaited work, so two candidate callbacks cannot both grant from one pending permit within the same JS event loop. This does not prove multiple plugin instances share state.

## Alternatives considered

| Alternative | Tradeoff / disposition |
|---|---|
| Keep first `session.created` wins, matching only parent ID | Rejected: it is the defect; unrelated or earlier children can steal the permit (`systematic-routing-guard.ts:832-840,856-861`). |
| Bind using task-result child ID | Rejected as the authorization point: child ID is only recoverable after the child can run (`systematic-routing-guard.ts:1112-1118`; Q72 tracker `odd/tasks/q72-tiny-fix-route.md:131,137`). Useful only for cleanup/consistency checks. |
| Match the observed agent on `chat.message` with a candidate set | Selected owner design: uses a signal from the child after creation while remaining early enough to precede child writes if the hook is delivered in time. It is fail-closed if child hook behavior cannot be established. Tradeoff: observed agent is not authenticated (`systematic-routing-guard.ts:325-331,875-880`), and same-instance event delivery is unverified. |
| Treat any writer-looking child or any child of the parent as a match | Rejected: a different writer can still inherit the permit, so the target identity is not preserved. |
| Use `task_id`, `background`, retry ordering, or another task argument as correlation | Not selected: no evidence establishes that these fields are exposed on child events or uniquely bind the created session to this dispatch. Investigate, but do not rely on them absent evidence. |
| Persist a permit or key for later inheritance | Rejected: expands duration/scope and conflicts with the existing ephemeral, session-specific one-shot model (`systematic-routing-guard.ts:813-820`). |

## Race and lifecycle scenarios T1 must cover

- Two near-simultaneous child sessions from the same parent: only the candidate with the matching observed writer may consume the one-shot permit; ensure only one matching candidate wins.
- A child created before the tiny-fix task call: it must not become eligible retroactively merely because its parent later arms a permit.
- A child for a different agent, created before the intended writer: it must be removed as a mismatch and must not consume the pending permit.
- A task that never produces a child: pending state expires and is not accidentally granted to a later child.
- TTL expiry mid-flight: expired pending state cannot grant a permit; child candidates and permits are cleaned consistently without extending the TTL.
- Parent session ending: parent pending state and all associated candidates are removed; child deletion removes its candidate/permit.
- PM-dispatched task: the task handler arms on `input.sessionID` with the same `isWriterDispatch` path and no PM special case (`systematic-routing-guard.ts:1023-1034`); test this path explicitly.
- `-local` and `-astra` writer aliases: canonicalize both expected and observed names before comparison without broadening writer eligibility. Existing normalization is PM-specific and Astra-only (`global-config/plugins/lib/routing-guard-helpers.ts:37-49`).

## Required non-vacuous regression test

Add a test in `tests/routing-guard/routing-guard.test.ts` using the existing seeded agent/key pattern (`:381-383`):

1. Bind the parent to `gentle-orchestrator`, seed its valid ODD key, and dispatch a tiny-fix task targeting the expected writer.
2. Create the unrelated/non-writer child FIRST with `session.created`; send its mismatching observed agent through `chat.message`; seed its valid ODD key; attempt a `sandbox_write`.
3. Assert the stealer receives the ordinary bootstrap warning. This positive control proves the mismatch candidate did not get a permit.
4. Create the intended writer SECOND with `session.created`; send its matching observed agent; seed its valid ODD key; attempt a `sandbox_write`.
5. Assert the intended writer has no bootstrap warning and exactly one permit was consumed. Keep an independent unpermitted-session positive control as well.
6. Run the race test against the current implementation first and preserve the RED result, then run it after the fix for GREEN. The current handler grants the first child unconditionally (`systematic-routing-guard.ts:832-840`), so the stealer assertion should fail before the code change.
7. Repeat the sibling ordering through a `pm-odd` parent to prove the PM path, and exercise `-local`/`-astra` canonicalization.

The test helper presently constructs only a `session.created` event with `id` and `parentID` (`tests/routing-guard/routing-guard.test.ts:71-72`); tests that directly call `message(...)` prove guard logic under that synthetic sequence, not runtime delivery of a child `chat.message` hook.

## Existing coverage and record correction

The five existing `1d` permit tests are at `tests/routing-guard/routing-guard.test.ts:387-461`. The “scope” test creates a separate parentless session for its negative assertion (`:413-427`); it does not create a sibling child of the same parent. It therefore does not exercise the reviewer’s “two children of the same parent” scenario. Its seeded binding/key setup is documented at `:381-383`, and the separate child bootstrap test has a positive control at `:446-460`.

**Record defect in Q72:** its T1b note claims a sixth Astra alias permit case at `tests/routing-guard/routing-guard.test.ts:1056-1061` (`odd/tasks/q72-tiny-fix-route.md:165-166`). That range is actually the Astra PM adapter identity test inside “9. PM adapter map own-property lookup” (`routing-guard.test.ts:1046-1061`), not a tiny-fix permit case. Correct the claim in the Q72 record or add a genuinely relevant permit case in this task; do not count the unrelated PM test as permit coverage.

## Preserve these invariants

- One-shot consumption: one parent permit grants at most one matching child.
- Existing 30-minute TTL; do not change it.
- Own-session-only behavior; no parent, sibling, or global exemption.
- All five existing `1d` cases unchanged and green.
- Non-vacuity controls remain: valid keys and observed parent agent for gate tests (`routing-guard.test.ts:381-383`), plus a known unpermitted write that must warn (`:446-460`).
- Never bind on the task-result hook after the child may already have written.

## Open questions and evidence limits

- **Child hook delivery:** Does `chat.message` fire for child sessions and carry the child agent before its first write? OpenCode runtime behavior is not demonstrated by the current in-repo harness. Establish it with reliable runtime evidence before relying on it. If unavailable, fail closed: do not grant a child permit based solely on parent ID or an unverified hook assumption.
- **Plugin-instance topology:** Do parent and child events reach the same plugin instance holding the in-memory maps? UNVERIFIED; report as a limitation unless T1 obtains direct evidence.
- **Agent authenticity:** `input.agent` is observed, not authenticated; matching is risk reduction, not strong identity proof (`systematic-routing-guard.ts:325-331`).
- **Dispatch metadata:** `task_id`, `background`, and retry timing may affect child creation, but their identity semantics are unverified; no permit binding may depend on them without evidence.
- **Prior mutation proofs:** Q72 T1a M1/M2/M3 proofs were run ad hoc and are not in-repo; their validity after this change cannot be confirmed from repository evidence.

## Advisor recommendation and disposition

Proceed with the owner-selected candidate-set plus observed-agent design only after proving the child hook contract; otherwise fail closed. Keep the race test non-vacuous and demonstrate RED against the current implementation, GREEN after the change, and explicit PM-path coverage. Preserve the five existing permit cases and the scope/TTL/one-shot invariants.
