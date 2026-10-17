# Q78 — host_review_materialize permission for the ce:review pipeline

Feature: enable the ce:review advisory pipeline. Task ID `q78-host-review-materialize`. Class: global-tooling-change. Route: `workflow-odd-secure` (delegated). Unit status: T0 IN PROGRESS. Model: cloud `opencode-go/deepseek-v4.1-flash`.

## Objective

Grant the new host tool `host_review_materialize` to the orchestrator and both project-managers, with a global `deny` default and VERIFIER ENFORCEMENT, so the `ce:review` advisory pipeline can run as intended.

## Problem

OWNER-STATED 2026-10-17: `host_review_materialize` is a NEW host tool currently being built by the `agent-sandbox-integration` project. It is required by the `ce:review` advisory pipeline together with a helper unit also being built there; without both, `ce:review` cannot be used at all. This is NOT the native review lens path (`asi-review-*`) — it is a separate advisory pipeline. Two pre-code advisors established: (a) the tool name appears NOWHERE in this repo (0 matches) and the known `host_review_*` surface is 13 enumerated operations; (b) `"disallow"` is NOT a valid permission value here — the vocabulary is `allow`/`deny`/`ask`; (c) `verify-workflow.sh:2717` declares `gatedHostMutations` and `:3002-3003` requires every entry to be `"ask"` for `gentle-orchestrator` EXCEPT `host_review_start` which is `"allow"` — so a new `allow` entry trips `ORCHESTRATOR_HOST_TOOL_NOT_ASK` unless added to that exception; (d) NO verifier assertion covers this permission, so a grant to three agents would be silently driftable.

## Scope

In scope: the permission entries, the `tools` block entries, the verifier enforcement (exception membership + per-agent assertions + a negative sweep + positive controls), the digest re-pin, and the record. Out of scope: the tool's own implementation and the `ce:review` helper unit (both `agent-sandbox-integration`, cross-repo); any change to the native `asi-review-*` lens path; the orchestrator prompt (no prompt text is added in this unit — if one becomes necessary it is a separate unit with its own regeneration chain).

## Constraints

The permission value is `"allow"` (owner decision: an exception, like `host_review_start`); the GLOBAL default is `"deny"` (NOT `"disallow"` — that value does not exist); the entry goes under each agent's `permission` block, NOT under `permission.task`; the PMs enumerate their `host_review_*` tools in a `tools` block, so they need `"host_review_materialize": true` there too — check whether the orchestrator needs the same (its `tools` block omits `host_review_*` and relies on implicit exposure); the change edits `verify-workflow.sh`, so `VERIFY_SCRIPT_SHA256` must be re-pinned LAST in the same commit; the tool does not exist yet, so the permission is INERT until the broker-side registration lands — state that plainly; never commit; never switch branches.

## Acceptance criteria

- The three agents carry the explicit `allow`.
- The global default is `deny`.
- The verifier treats the entry as an `allow` exception for the orchestrator and asserts the three grants explicitly (not via a wildcard).
- A NEGATIVE sweep proves no other agent gained it.
- Each new assertion has a positive control.
- The digest is re-pinned.
- The cross-repo precondition is recorded as an explicit blocker-for-effect, not silently assumed.

## Authorized scope

T1: `global-config/opencode.json`, `verify-workflow.sh`, `global-config/plugins/workflow-health-check.ts` (the pin ONLY, LAST). Plus this tracker, the advice record, `ROUTER-LOG.md`.

## Checks

- `python3 -m json.tool global-config/opencode.json`
- `bash -n verify-workflow.sh`
- The extracted verifier permission block executed against fixtures (the three grants present, the global default `deny`, a fourth agent with the grant FAILS the sweep, and each positive control fires)
- `python3 -m unittest discover -s tests`
- `env HOME=/tmp/q78-home bun test tests/routing-guard`
- The pin coherence via the verifier's own `read_verify_script_pin` regex

## Tasks

- [ ] T1 — add the explicit allow to gentle-orchestrator, pm-odd and pm-systematic (and the tools-block entry where the agent enumerates host_review_* tools); add the global deny default; add the verifier's allow-exception membership, the three per-agent assertions and the negative sweep, each with a positive control; re-pin LAST.

## Delivery strategy

**Chosen strategy:** stacked-to-main (owner decision 2026-10-14). **Forecast:** T0 ~200; T1 ~140. Total ~340. **Selected AT tracker creation** per odd-and-review.md:36.

## Progress

- 2026-10-17: T0 — tracker, advice record and queue entry created; delivery strategy selected at creation. No source edit yet.

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` for ODD units (the route skill's named writer). Trigger: secure no-inline-mutation policy; a security/contract change (`WORKFLOW.md:249`) is NOT a tiny fix (`WORKFLOW.md:128`) even though it is only a few keys. RDD: on (decided by global).

## Next step

T1 implementation, then its own native review candidate, then the metadata record. The tool's broker-side registration is a cross-repo precondition for the permission to have any runtime effect.
