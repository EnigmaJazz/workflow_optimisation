# Q33 — pre-code advice

## advisor-integration-pre (2026-10-11)

Scope: integration impact of the four T1 edits on the live routing guard and its consumers.

- Keeping `ROUTING_GATE_TOOLS:224` keeps `host_sdd_archive_compose` gated. The `:584` prefix rule
  currently gates no other live tool because every other `host_sdd_*` is denied/false in
  `opencode.json` (`:563-588`, `:2191-2192`, `:2240-2241`, `:2431-2472`). Removing `:584` is
  therefore hygiene, not a functional change. Defer removing `:224` to Q65 — it would break the
  test enumerations at `:873`/`:892`.
- Removing `sdd-apply`/`sdd-apply-local` from `SPECIALIST_WRITERS` (consumed at helpers `:95` →
  guard `:1006`) changes no live gating: neither is a registered agent post-Q31. Only tests are
  affected (`routing-guard.test.ts:267-279`, `:273`, `:283`).
- Removing the `sdd-*` `READ_ONLY_SPECIALIST_PATTERNS` entries (consumed by
  `isReadOnlySpecialist` at guard `:971`) changes no live gating; the generic-dispatch blocker
  (`:1020-1038`) does not use that list. Only tests are affected (`:289-301`).
- `ADAPTER_WORKFLOW_SKILLS` has a SECOND consumer beyond `:533`: `:1106` (skill-load stage-gate
  exemption). Removing the member has no live effect because no `ROUTE_STAGES` entry gates
  `workflow-sdd-secure`.
- Ordering Q33 → Q65 → Q30 confirmed. Hazard: after Q33 and before Q65, a `pm-sdd` session emits
  an extra generic "workflow key missing" warning on gated tools (because `helpers:32-36` still
  maps `pm-sdd` → the now-unlisted skill); noisy but safe, resolved by Q65.
- `astra-sol-upgrade.ts` needs NO Q33 change: it names only `jd-fix-agent` and
  `gentle-orchestrator`, both present in `opencode.json`. Its runtime resolution is not statically
  provable.
- `VERIFY_SCRIPT_SHA256` does NOT change for Q33 (the verifier is untouched).

## advisor-testing-pre (2026-10-11)

Scope: test-suite impact of the T1 edits and the required non-vacuous positive control.

- `SPECIALIST_WRITERS` drop breaks exactly one test (`routing-guard.test.ts:267-279`): the
  `expect(logCount("specialist")).toBe(0)` at `:277` becomes 2. Minimal fix: delete the two
  entries from the literal at `:273`.
- `READ_ONLY_SPECIALIST_PATTERNS` drop breaks exactly one test (`:289-301`): the count at `:299`
  goes 0→3. Minimal fix: delete the three entries at `:292`.
- `ADAPTER_WORKFLOW_SKILLS` drop: no test seeds a `workflow-sdd-secure` key (all `seedKey` sites
  enumerated), so no fixture change is needed — and NO positive control for that set exists today.
  Add one in describe "7. exported stage table" (~`:189-191`): assert the member is absent AND
  drive an observable consequence (e.g. seed a `workflow-sdd-secure.key` under a temp session and
  assert the key is not treated as valid / the expected warning still fires) so the absence
  assertion cannot pass vacuously.
- `host_sdd_` prefix drop: zero test impact while `:224` stays.
- No coordinator/generic-dispatch/advice-stage test depends on the removed names.
- Plugin-load risk: none — no export is renamed or removed; the `check_plugin_loads` probe is
  unaffected.
- `workflow-health-check.ts` `:8`/`:40` edits are inside the header block comment and cannot fail
  verification; the digest pin is bound to `verify-workflow.sh`.
- Flag for the owner: after Q33, a `pm-sdd` session still requires `workflow-sdd-secure` as its
  own key (helpers `:32-36`) but no key can satisfy it, so its warning text is permanently
  expected until Q65 removes the map. No test contradicts this today.
