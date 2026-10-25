# Plan-tools smoke unit — raw evidence

## Host runner (orchestrator, observed)

- Runner: `workflow-tests`
- `exitCode: 0`
- `signal: null`
- `timedOut: false`
- `durationMs: 7564`
- `truncated: false`
- stderr tail: `Ran 342 tests in 7.474s` then `OK`
- stdout tail: `coverage-total: 105 controls passed`
- `gitHead: fc74267c5ab55f2cafbe338b0ee1cd6c37ab6464`
- `dirtyPaths: ["odd/tasks/plan-tools-smoke.md"]`
- `worktreeDigest: sha256:93e28776f73b6858369c642b75da9a5740a5579f54f43142c5737f9d31ed4ee4`
- log artifact: `/home/james/.local/state/opencode-sandbox/test-runs/fb648dbe-1131-4f9a-b57e-b269d16e791b.log`

## Candidate diff

- Commit: `04077e6673f4546bb8e035ba41d1468c4edd10b7`
- Base: `7c1fa2e3fd52a9708bd89c0f16ba5c6095941e6e`
- Materialized diff sha256: `0a26402d478be918cbbae40c4610497d212d27c39f62c0ffaf773551ba22212d`
- Diff bytes: 4733
- Contains the pinned `WORKFLOW.md:532` Tiny-fix row byte-exact, plus the adjacent Gate-2 unit's paragraph rewrite: two units in one commit (recorded provenance deviation).

## Native assessment

- `gentle-ai.review-assessment/v1`: risk `medium`, `review_due=false`, `review_due_reason=under_budget`, `consumed=false`
- Therefore no post-commit lens evidence is owed and none exists.

## Owner authorization

- Gate 2 for ST1 is authorized post-facto under the owner cost override (zero advisors, zero verifier), with no lens evidence because review is not due.
