# Q80 — ce:review pipeline host permissions

Class: global tooling change. Route: `workflow-odd-secure`; authorized change. Branch switching and commits are prohibited for this task.

## Objective

Grant the ce:review pipeline's two newly registered host tools to the orchestrator and both PMs, with verifier enforcement and a global deny default.

## Scope

- `host_review_pipeline_run`: `allow` for `gentle-orchestrator`, `pm-odd`, and `pm-systematic`.
- `host_review_persist`: `ask` for those same agents.
- Global defaults remain `deny`; no other agent may receive either explicit key.
- Add PM tool-map entries, verifier checks/positive controls, and preserve the verifier digest pin.

## Acceptance and checks

- [ ] JSON parses and the three requested agent values are correct.
- [ ] Other agents do not hold either explicit permission key.
- [ ] Verifier validates per-agent values, global defaults, exception membership, PM tool maps, and negative sweep with effective positive controls.
- [ ] `bash -n verify-workflow.sh` passes.
- [ ] `python3 -m unittest discover -s tests` results recorded.
- [ ] The verifier's `read_verify_script_pin` regex matches both digest literals.
- [ ] No branch switch and no commit.

## Progress

- Current task began on sandbox branch `work`; it was not switched. Q78's requested standalone test file was not present in `tests/`; verifier-embedded positive controls are extended instead.
