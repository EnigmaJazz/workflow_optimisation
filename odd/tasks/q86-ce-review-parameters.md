# Q86 — ce:review contract parameters

Feature: revise our use of the `ce:review` route against an externally supplied contract. Task ID `q86-ce-review-parameters`. Class: global-tooling-change. Route: `workflow-odd-secure` (delegated). Unit status: T0 record created; planning only. Delivery strategy: stacked-to-main.

## Objective

Record the supplied `ce:review` contract parameters as the authoritative input for revising our use of that route. Our current plan gets the execution environment wrong: it requires the helper pipeline to run in an authorized sandbox worker even though the helper is STDIN-only and sandbox bash is argv-only, making the required pipe or redirection impossible.

## Why our current plan is wrong

`global-config/skills/workflow-odd-secure/references/odd-and-review.md:22` says the helper pipeline “must run in an authorized sandbox worker”, which CANNOT be satisfied: the helper is STDIN-only and the sandbox bash surface is argv-only, so it can neither pipe nor redirect.

## Supplied parameters

The following supplied parameters are the authoritative input for revising the plan. They are recorded as-is; this tracker does not select implementation mechanisms.

### INVOCATION

- Helper identity = absolute path plus sha256, BOTH from config; a separate configured INTERPRETER (absolute path, regular file, executable, never resolved from PATH, never defaulted); verified before EVERY invocation; mismatch/absence/non-regular type is a named refusal; no implicit fallback.
- argv fixed per phase: `screen --reviewer <persona> --harness opencode`; `prepare`, `merge`, `finalize` bare; `artifact <path>`; the harness is server-side and not a caller parameter.
- stdin: payload inline, bounded to 256 KiB measured in REAL bytes, refused (never truncated) naming the cap and observed size; accepts a byte array as well as a string because a JSON string cannot express invalid UTF-8.
- Working directory: the repository root for phases; the staging root for artifact validation.
- Environment: REPLACEMENT not merged — PATH only for diff/git work; PATH plus a real HOME and prompt-suppressed git for ignore checks.
- Budgets: 30 s per helper invocation; client timeout above it (60 s) so the client cannot abort mid-write.
- Exit codes: 0 valid · 1 structural rejection (issues on stderr) · 2 usage or unreadable path · 3 legacy artifact lacking schema_version; an exit 1 whose stderr carries the fixed prefix `ce-review-validator: internal error in` is a HELPER CRASH, not a rejection, and must map differently.

### INPUT

- The range as data — baseRef and headRef resolved to commit object ids via `rev-parse --verify --end-of-options <ref>^{commit}`; diff produced under the replacement environment with external diff, textconv and paging disabled.
- Slicing: 1500 realized diff lines OR 46,080 bytes per slice, whichever binds first, packed on file boundaries; a single file exceeding one slice is REFUSED naming the cap and observed size — never split mid-file, never truncated.
- Chaining: a phase may take stdin from a prior phase's published artifact in the same run (`inputRef`); exactly one of `stdin` and `inputRef` is required, and supplying neither or both is refused.
- Personas: enumerated allowlist `review-risk`, `review-resilience`, `review-readability`, `review-reliability`, required for `screen` and forbidden elsewhere.

### OUTPUT

- Each phase publishes its RAW OUTPUT BYTES into a broker-owned run store as a deterministic per-phase artifact, byte-identical, with byte length and sha256 recorded; phase outputs are named per persona, so four `screen` runs produce four artifacts.
- The operation returns ONLY artifact refs, byte lengths, sha256 values and bounded summaries — never the full output inline.
- The run record carries a broker-generated run id bound to the session, the resolved base and head object ids, the artifact manifest, and after `finalize` the provenance (artifact name, byte length, sha256, phase name, outcome).
- `persist` extracts only the artifact member, inserts `schema_version` when absent, and writes to `<repo>/.context/systematic/ce-review/<runId>/review-summary.json`; it validates BEFORE publishing with four statuses: `passed`, `failed`, `unavailable`, `not_attempted`; nothing is published into the project unless validation passed, and a failed or unavailable result retains the staged copy in the run store and reports its path.
- Ignore provisioning writes an entry covering the run directory only, only when not already ignored, and reports whether it created, changed or left the file unchanged.

### AUTHORITY

- `materialize` and the phases write only into the broker-owned run store and need NO approval.
- `persist` is the SINGLE approval gate, raised BEFORE dispatch; a denial dispatches zero requests.
- `report_only` writes nothing into the project and its prompt must say so.
- Callers: the orchestrator and the PM identities (INCLUDING THE ASTRA VARIANTS); denied for general agents.
- The project path is NEVER a caller parameter.

## Confirmation against our config

The supplied confirmation is that our grants already match: `host_review_materialize` = allow, `host_review_pipeline_run` = allow, `host_review_persist` = ask, which is exactly the authority model above (materialize + phases no approval; persist the single approval gate).

## Gaps to check

- The caller list includes the ASTRA variants; we granted `pm-odd` and `pm-systematic` but the `-astra` aliases were not explicitly granted — determine whether they inherit or need explicit grants.
- The two UNRESOLVED requirements are recorded as REQUIREMENTS, not mechanisms:
  - REVIEWER DELIVERY (how a lens receives a slice is unsolved — lens prompts are provider-materialized and reviewer agents have no read path; until specified the pipeline can obtain and hold a range but cannot complete a multi-persona review).
  - HELPER SOURCE (the pinned bytes currently come from the package cache, which is WRITABLE by the confined agent, so the digest vouches for whatever it was given; the contract should require the pinned bytes to originate from a source the agent cannot write).

## Constraints

Do not redesign the parameters; do not choose mechanisms for the two unresolved requirements; this is a RECORD.

## Acceptance criteria

- Every supplied parameter above is recorded with its exact values.
- The plan-defect is stated.
- The two unresolved items are recorded as requirements, not mechanisms.
- The grant confirmation and the gaps are recorded.

## Tasks

- [ ] Revise our ce:review plan against these parameters, resolve the two requirements, and check the ASTRA caller grants.

## Delivery strategy

**Chosen strategy:** stacked-to-main (owner decision 2026-10-14). **Forecast:** about 100 authored changed lines for this record and queue entry; planning-only follow-up forecast to be revised when its scope is defined.

## Progress

- 2026-10-18: T0 — tracker and queue entry created; supplied parameters recorded as authoritative planning input. No implementation or mechanism selection.
- 2026-10-18: Contract-gap correction — replaced the impossible sandbox-worker execution-location clause in the ODD reference, WORKFLOW.md, and orchestrator prompt with the required contract properties and the two unresolved requirements. The prompt regeneration chain matches at `803f22525a577fbdeeca91febf1fb8666269f50f9fc646644044cbcd83e04104`; focused tests pass, while the full Python suite has 204 passes, 10 errors from sandbox-denied `node`, and 1 skip. The two requirements remain deliberately unresolved; no mechanism selected and no commit made.

## Route / trigger evidence

Route: delegated. Specialist: sandbox worker fallback. Trigger: explicit user authorization for this tracker-and-queue record; the secure ODD policy delegates project mutation, and the user explicitly assigned this worker without a Task/subagent dispatch. Host branch specified by user: `chore/q72-t1b-tiny-fix-contract`; sandbox internal branch `work` is expected. No commit; never switch branches.

## Next step

Revise the existing `ce:review` plan against this recorded contract, determine whether the ASTRA aliases inherit or require explicit grants, and resolve the REVIEWER DELIVERY and HELPER SOURCE requirements without assuming mechanisms in this record.
