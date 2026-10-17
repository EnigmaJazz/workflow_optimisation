# Q78 — host_review_materialize permission for the ce:review pipeline

Feature: enable the ce:review advisory pipeline. Task ID `q78-host-review-materialize`. Class: global-tooling-change. Route: `workflow-odd-secure` (delegated). Unit status: T1 delivered (commit `2800586`); metadata follow-up IN PROGRESS. Model: cloud `opencode-go/deepseek-v4.1-flash`.

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

- [x] T1 — add explicit `allow` permissions to gentle-orchestrator, pm-odd and pm-systematic; add PM tool exposure entries and global `deny`; add verifier exception, explicit-own-key assertions, negative sweep and positive controls; document the temporary `general` writer deviation/revert trigger; add the anchor token; re-pin last after verifier edits. The orchestrator tools map needed no entry: it has no explicit host-review tool allow/deny list and relies on implicit custom-tool exposure, while PM tools maps explicitly enumerate host_review_* and now include the entry.

## T1 Record (2026-10-17)

- `global-config/opencode.json`: added global `host_review_materialize: deny`; explicit `allow` under the three named agents; added `true` to both PM tool maps only (orchestrator tools map remains implicit).
- `verify-workflow.sh`: added gated mutation registration and orchestrator allow exception; explicit own-property/exact-value assertions for each grant, per-agent omitted-key and wrong-value controls, global default assertion, and an extra-agent negative sweep with a synthetic fourth-agent control.
- `global-config/skills/workflow-odd-secure/SKILL.md`: recorded the temporary `general` (`openai/gpt-6-luna`) writer deviation for direct orchestrator dispatch, PM-layer `odd-apply` behavior, and Q56 PM-layer pilot revert trigger; added the owning-file anchor token row.
- `global-config/plugins/workflow-health-check.ts`: re-pinned `VERIFY_SCRIPT_SHA256` last among verifier/source edits.
- Cross-repo precondition: broker-side registration is being built in `agent-sandbox-integration`; it is unverified here and the permission is inert until that registration is installed.
- Verification: JSON parse passed; `bash -n` passed; anchor-manifest suite 10/10 passed (39 structural rows, 99 token rows); routing-guard suite 103/103 passed; full Python suite ran 199 tests, with 189 passing and 10 errors because `node` execution is denied in the sandbox. The pin regex test passed and matched both literals. The extracted JavaScript permission-fixture block could not be executed because the required `node` runtime is denied; its source controls are present but fixture sweep execution remains unverified. The full verifier is an owner deploy step (host paths and `node` are unavailable in this sandbox).

## Metadata follow-up verification (2026-10-17)

- `bash -n verify-workflow.sh`: passed.
- `python3 -m unittest tests.test_anchor_manifest -v`: 10/10 passed.
- `python3 -m unittest discover -s tests`: 199 tests; 189 passed, 10 errored because sandbox execution of `node` is denied; 0 assertion failures after the pin update.
- `env HOME=/tmp/q78-meta-home bun test tests/routing-guard`: 103 passed, 0 failed.
- Pin regex test `tests.test_orchestrator_prompt_source.OrchestratorPromptSourceTests.test_verifier_script_pin_matches_its_own_regex`: passed; both literals were `e962494eb4e4f597da163fdf26c9bf36a8debe43a311be16d235c56d23d26bf4`.
- Extracted assertion fixture execution was not completed: Node is unavailable (spawn denied), and the sandbox command interface rejected the inline Bun fixture harness. Thus the present/removed/false fixture outcomes remain unverified here; this is not a claim that the fixture suite passed.
- Full verifier/deploy and any Node-dependent check remain the owner's deploy step.

## Delivery strategy

**Chosen strategy:** stacked-to-main (owner decision 2026-10-14). **Forecast:** T0 ~200; T1 ~140. Total ~340. **Selected AT tracker creation** per odd-and-review.md:36.

## Progress

- 2026-10-17: T0 — tracker, advice record and queue entry created; delivery strategy selected at creation.
- 2026-10-17: T1 — implementation delivered in commit `2800586`; native review approved and acknowledged; R4-002 and R4-004 addressed in this metadata follow-up.

## Route / trigger evidence

Route: delegated. Specialist: `odd-apply` for ODD units (the route skill's named writer). Trigger: secure no-inline-mutation policy; a security/contract change (`WORKFLOW.md:249`) is NOT a tiny fix (`WORKFLOW.md:128`) even though it is only a few keys. RDD: on (decided by global).

## Native review record (2026-10-17)

- Lineage `review-9acb2006667ef984`; tier **high**; four lenses; outcome **approved + acknowledged**; authority **burned**; consumed revision `sha256:fa09328a…`.
- Reliability BLOCKER `R3-host-review-materialize-positive-control-name-mismatch`: **REFUTED** by the refuter.
- Advisory findings (non-blocking informational):
  - `R4-001` — recorded as informational; location: `odd/tasks/q78-host-review-materialize.md:46-55` (T1 implementation and verification record).
  - `R4-002` — recorded as informational; location: `verify-workflow.sh` PM materialize checks and `global-config/opencode.json:2097,2226` (PM `tools` maps). Follow-up: verifier assertion and positive controls added in this metadata unit.
  - `R4-003` — recorded as informational; location: `odd/tasks/q78-host-review-materialize.md:48-55` (T1 record and its verification limitations).
  - `R4-004` — recorded as informational; location: `docs/TODO.md` Q78 entry. Follow-up: status corrected to delivered T1 and acknowledged review.

## Next step

The metadata follow-up records the review and closes R4-002/R4-004. The tool's broker-side registration is a cross-repo precondition for the permission to have any runtime effect.
