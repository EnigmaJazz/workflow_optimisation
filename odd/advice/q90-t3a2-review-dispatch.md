# Q90 T3a2 — review-dispatch enforcement pre-code advice
Unit `q90-t3a2-review-dispatch-u1`; class global-tooling-change; route
`workflow-odd-secure`, delegated cloud `odd-apply`. Baseline host
`chore/multi-agent-v2-phase1` `21737382bcd50e019eb15a9d1c05ec0c104ea848`.
This is pre-code advice evidence, never approval.
## Verified premise
The PM's direct readback establishes that actor migration is already present:
`gentle-orchestrator` allows all six `asi-review-*` task lanes, the six plain
`review-*` lanes are denied, and both PMs carry a `"*": "deny"` task map with no
review keys. The verifier already asserts the six orchestrator allows and six
plain denies at `verify-workflow.sh:3405-3408`; its neighbouring sweep at
`:3409-3414` skips scalar task maps, catches only `"*": "allow"` and named
`allow`, and exempts `agentName.startsWith("pm-")`. The unit therefore
strengthens enforcement of the existing raw-map shape; it does not migrate
actors, and no config/guard/skill/`WORKFLOW.md` edit is justified by the
observed files.
## Pre-code advice (observed; no approval implied)
- `advisor-security-pre` session `ses_e95081d4effewfWfYgXxHrel7t`: observed
  the existing six-lane checks and PM exemption. Recommended isolated
  diagnostics, fail-closed wildcard/`ask`/scalar handling, and controls proving
  vacuity and production call-site propagation.
- `advisor-integration-pre` session `ses_e95081d5bffeSP0HOmhAcEmIfr`: agreed
  config and skills remain unchanged, and an extracted runnable predicate plus
  the matching digest pin is the right integration surface. Its claim that no
  existing six-lane check existed was disproved by the PM's direct read of
  `verify-workflow.sh:3405-3408`; it is not repeated, and the existing checks
  are preserved rather than duplicated.
- Research mapper session `ses_e95081d54ffePonYA5kwCtYSwq`: agreed the config
  task-map shape is correct for the six lanes but likewise missed the later
  verifier checks. Its mapping is background only.
## Enforced shape and limits
The canonical predicate is `reviewDispatchFailures(agents, relayNames,
plainNames)` in `verify-workflow.sh`. It is a conservative raw-map check, not a
complete OpenCode permission resolver. `cfgPerm` reads only
`agent.permission[tool]`; the predicate does not model inherited defaults,
tool-map booleans, or runtime resolution beyond the maps it is given.
1. `gentle-orchestrator.permission.task` must be an object with the six
   `asi-review-{risk,resilience,readability,reliability,refuter,validator}`
   entries exactly `"allow"` and the six plain
   `review-{risk,resilience,readability,reliability,refuter,validator}`
   entries exactly `"deny"`.
2. Every other agent's `permission.task`, when present, must not grant a named
   `asi-review-*` or `review-*` target except with `"deny"`. A wildcard or
   scalar `"ask"` is a grant except for the canonical `frontend-dev-premium`
   wildcard ask; an `"allow"` wildcard/scalar is always a grant. A missing map
   means no dispatch authority in this raw-map model.
3. A scalar `"deny"` is a valid deny-all shape. Arrays, `null` and other
   malformed shapes fail closed. The production call site must route every
   returned failure through the existing `fail(...)` sink.
Required controls: real source config accepted; omission of every orchestrator
lane detected; PM relay and plain injections detected for both PMs with a
specific diagnostic; advisor and writer relay injections detected; wildcard,
`ask`, scalar and malformed shapes exercised; an always-pass predicate
mutation rejected; and the extracted production call statement executed with a
collecting `fail` sink.
## Limitations
- Full `verify-workflow.sh` and `VERIFY_WORKFLOW_PLUGIN_LOADS_ONLY` are
  HOST-ONLY and are not invoked by this sandbox writer because they can deploy.
- The digest pin must equal the edited verifier's SHA-256; the health plugin is
  import/probe-checked only in an inert sandbox mode. No host runtime claim.
- The deterministic Magic Context mirror host tool is UNIMPLEMENTED; this unit
  does not read or write the mirror body.
