# Q80 — ce:review pipeline host permissions

Class: global tooling change. Route: `workflow-odd-secure`; authorized change. No branch switching. Owner-authorized counted-unit PM metadata commit; the worker never commits.

## Objective

Grant the ce:review pipeline's two newly registered host tools to the orchestrator and both PMs, with verifier enforcement and a global deny default.

## Scope

- `host_review_pipeline_run`: `allow` for `gentle-orchestrator`, `pm-odd`, and `pm-systematic`.
- `host_review_persist`: `ask` for those same agents.
- Global defaults remain `deny`; no other agent may receive either explicit key.
- Add PM tool-map entries, verifier checks/positive controls, and preserve the verifier digest pin.

## Acceptance and checks

- [x] JSON parses and the three requested agent values are correct: `python3 -m json.tool global-config/opencode.json` exit 0 (stderr empty); `gentle-orchestrator`, `pm-odd`, and `pm-systematic` grant `host_review_pipeline_run: allow` and `host_review_persist: ask`.
- [x] Other agents do not hold either explicit permission key: 43 agents total; the remaining 40/40 permission maps inspected with zero explicit either key; offenders `[]`.
- [x] Verifier validates per-agent values, global defaults, exception membership, PM tool maps, and negative sweep with effective positive controls: `bun tests/test_review_pipeline_permissions.js` exit 0; extracted real verifier predicates/declarations detect omitted/wrong grants, false/omitted tools, global allow, missing exception, and a synthetic fourth-agent grant, with all reverted-fixture controls passing.
- [x] `bash -n verify-workflow.sh` exit 0 with no output.
- [x] `python3 -m unittest discover -s tests` exit 0: 244 tests OK, zero failures/errors, no child `node` denial.
- [x] `read_verify_script_pin` regex matches the real source plus single-quoted and double-quoted 64-hex fixtures; the verifier pin canonical literal and the computed script SHA are both `28ff39379aee7460bce784386e62c83bf5f51aea2b93074e2f35230fa299e7ad`. The deployed plugin/pin was not probed.
- [x] No branch switch; owner-authorized counted-unit PM metadata commit (worker never commits).

## Progress

- Current task began on sandbox branch `work`; it was not switched. Q78's requested standalone test file was not present in `tests/`; verifier-embedded positive controls are extended instead.
- 2026-10-22: Q56 counted unit 1/10 — verified through pm-odd; source already complete; no source change; metadata commit PENDING-COMMIT

## Log

- Route: delegated; specialist `odd-apply`. Trigger: secure mandatory mutation delegation (`workflow-odd-secure`) — this is a metadata-only unit whose source was already complete, so the writer verifies and records without source edits. RDD: on, decided by global; no post-code or post-commit assessment is claimed here.
- Tasks dispatched: research `explore` `ses_e9a374b11ffej03jwJ76Hed2Ig` inspected the acceptance contract; execution-only `gentle-ai-worker` `ses_e9a3217ddffe9kxhBd5ez5CGgm` ran the checks on an identical base tree with no file changes. Metadata Task: initial writer `odd-apply` `ses_e9a293fe0ffeUl1R14kv3TbbHf`; correction round 1/1 is recorded below. No advisors and no `gentle-ai-verify` Tasks ran.
- Checks observed: `python3 -m json.tool` exit 0 with empty stderr; 43 agents total with the three coordinator grants and the remaining 40/40 maps clean; extracted verifier JS assertions and reverted-fixture controls pass; `bash -n verify-workflow.sh` exit 0 with no output; `python3 -m unittest discover -s tests` exit 0, 244 tests OK with zero failures/errors; pin canonical literal and computed script SHA both `28ff39379aee7460bce784386e62c83bf5f51aea2b93074e2f35230fa299e7ad`; `read_verify_script_pin` matches the real source plus single-quoted and double-quoted 64-hex fixtures. Focused rerun (execution-only `gentle-ai-worker` `ses_e9a3217ddffe9kxhBd5ez5CGgm`): `python3 -m unittest tests.test_orchestrator_prompt_source -v` exit 0 — `Ran 29 tests`, `OK`, zero failures/errors; the pin test `test_verifier_script_pin_matches_its_own_regex` passed. Deployed pin and broker registration were not probed.
- PM factual check: PM observed the retained full diff at 32 authored lines / 12,576 bytes across exactly the three allowlisted paths and read back the applied files; PM confirms the factual/structural check, with the F01 evidence omission addressed in correction round 1/1. Independent orchestrator readback: PENDING. PM-owned commit/post-commit assessment: PENDING, not performed. Mirror: tool unimplemented/not performed; the PM did not fetch mirror body.
- Correction round 1/1 (2026-10-23): this writer's session ID is not exposed in the dispatch. F01 adds the focused `tests.test_orchestrator_prompt_source` command, result and pin-test outcome without displacing the 244-test discovery result; F02 records the initial writer identity and PM readback above. Correction scope remains the same three allowlisted paths; no source, config, test, spec, `PLAN.md` or `WORKFLOW.md` change was made.
- Owner count authorization (2026-10-22, Q56 unit 1/10) supersedes the earlier blocked-count timing for this unit; it does not assert that Q58 enforcement or broker runtime registration is live.
