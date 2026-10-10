# gentle-ai v4 upgrade — agent allocation (Q31)

**Feature:** gentle-ai v4 upgrade / queue Q31 (agent allocation). **Task ID:** T1 (stable).
**Class:** global-tooling-change. **Route:** `workflow-odd-secure` (delegated).
**Branch:** `feat/gentle-ai-v4`. **Prerequisite:** Q29 (done).

## Objective

Remove SDD agent allocation from `global-config/opencode.json` and `global-config/tui.json`, deny every
`host_sdd_*` permission, add the four Q29d generic agents, and retitle `gentle-orchestrator` while
preserving its exact agent key.

## Problem

gentle-ai v4 retires SDD. The current OpenCode agent configuration still registers twelve `sdd-*`
agents, grants SDD tasks, and retains host-SDD capabilities. The verifier checks registered host
reads and agent requirements, and its health-check plugin pins `verify-workflow.sh` by SHA-256.
These changes must remain valid JSON and ship with their paired verifier updates and digest re-pin;
otherwise configuration validation or the health-check plugin can fail.

## Scope

### In scope (Q31)
- Remove the twelve `sdd-*` agent definitions from `global-config/opencode.json`:
  `sdd-apply` through `sdd-init` (`874-1161`) and `sdd-onboard` through `sdd-verify`
  (`1162-1401`), plus `sdd-research` (`1506-1565`). The file is currently 2935 lines;
  TODO line references are stale and must be rechecked at implementation time.
- Remove SDD `permission.task` grants: `gentle-orchestrator` (`283-292`, `331`) and `pm-sdd`
  (`2654-2665`).
- Set every `host_sdd_*` permission to `deny`: global (`2838`, `2864`, `2866`),
  `gentle-orchestrator` (`378`, `380`), and `pm-odd`, `pm-systematic`, and `pm-sdd`.
- Rebuild `gentle-orchestrator` from the v4 source `internal/assets/opencode/orchestrator.md`,
  retitling its description (`:264`) and prompt (`:398`) per Q29c while keeping the agent key
  exactly `gentle-orchestrator`.
- Add the Q29d generic agents: `gentle-ai-explore`, `gentle-ai-worker`,
  `gentle-ai-worker-local`, and `gentle-ai-verify`.
- Drop `opencode-sdd-engram-manage` from `global-config/tui.json` (`:6`).
- Pair each of the five configuration slices with its verifier edit and update
  `VERIFY_SCRIPT_SHA256` in `global-config/plugins/workflow-health-check.ts` after each
  `verify-workflow.sh` change.

### Out of scope
- Cleaning the live `~/.config/opencode/prompts/sdd/` directory; that is a separate live-config
  operation outside this repository.
- Engram MCP work (Q14b).
- The full Q32 verifier overhaul.
- Q33 plugins other than the Q31 digest-pin update in
  `global-config/plugins/workflow-health-check.ts`.

## Constraints
- **Verifier work is paired per slice.** Owner-approved 2026-10-10, per `docs/PLAN.md:178`:
  each Q31 slice includes its own verifier edit, including the `VERIFY_SCRIPT_SHA256` re-pin.
- **Five independently valid slices.** Each slice leaves `global-config/opencode.json` valid JSON
  and carries the corresponding `verify-workflow.sh` change and digest update.
- **Structural hazards:** deleting the final `permission.task` entry can leave a trailing comma and
  invalid JSON (the verifier's `json.loads` fails at `:444-450`); `required_agents` is set-based,
  not ordered; the `vision` and `frontend-dev-premium` blocks lie between the two SDD blocks.
- Recompute line numbers against the current tree before editing; `global-config/opencode.json` is
  currently 2935 lines, so TODO line references are stale.
- Do not commit or apply this preparation tracker to the host. Implementation is pending owner go.

## Implementation notes

- **S5 is blocked** until the owner provides the location of the v4 managed prompt source; keep the
  `gentle-orchestrator` agent key fixed in the meantime.
- `global-config/plugins/astra-sol-upgrade.ts` needs no edit: its regex (`:39-49`) already excludes
  the new names and the plugin auto-aliases `gentle-ai-verify-astra`.
- Stale `sdd-*` names in `global-config/plugins/lib/routing-guard-helpers.ts:18,46` are harmless;
  track cleanup under Q33.
- `global-config/opencode.json` currently parses as valid JSON. Validate it with
  `python3 -m json.tool` after every implementation slice.

## Tasks

- [ ] **T1 (Q31) — Agent allocation and paired verifier updates.** Deliverables:
  - [x] **S1 — Host-SDD lockdown.** Set all global, orchestrator, and `pm-*` `host_sdd_*`
    permissions to `deny`. In `verify-workflow.sh:2699-2703`, remove the three entries from
    `registeredHostReads`; move `host_sdd_attempt_grant` and `host_sdd_archive_compose` from
    `gatedHostMutations` (`:2700`) into `retiredHostOperations` (`:2701`); and retain
    `HOST_MUTATION_OR_RETIRED_DEFAULT_NOT_DENY` (`:2703`) so it asserts every `host_sdd_*`
    permission is `deny`. Re-pin the verifier digest. **Done 2026-10-10 (sandbox result; not
    committed or applied):** 33/33 `host_sdd_*` permission entries are `deny` (global 13;
    `gentle-orchestrator` 13, with `host_sdd_status`/`host_sdd_continue`/`host_sdd_task_result`
    added as `deny`; pm-odd 2; pm-systematic 2; pm-sdd 3) and 7/7 agent tool flags are `false`;
    `retiredHostOperations` lists all 13 retired names so line 2703 (unchanged) asserts every
    `host_sdd_*` permission is `deny`; digest re-pinned to
    `38c5dbfaebc3bc0d1493afac1916022fba9cfb0bdbbbb15aa62b9e3986b46674`.
  - [ ] **S2 — Retire first SDD agent block.** Remove `sdd-apply` through `sdd-init`
    (`874-1161`), remove their task grants, and drop `sdd-apply-local` from `required_agents`.
    Pair with the relevant verifier changes and digest re-pin.
  - [ ] **S3 — Retire remaining SDD agents.** Remove `sdd-onboard` through `sdd-verify`
    (`1162-1401`) and `sdd-research` (`1506-1565`), remove their grants, and drop
    `sdd-research` from `required_agents`. Pair with the relevant verifier changes and digest
    re-pin.
  - [ ] **S4 — Add Q29d generic agents.** Add the four generic agents and the orchestrator's
    `permission.task` allows; add the agents to `required_agents`. Pair with verifier changes and
    digest re-pin.
  - [ ] **S5 — Retitle and remove TUI entry.** BLOCKED: `internal/assets/opencode/orchestrator.md`
    does not exist in this repository, so the orchestrator description (`:264`) and prompt (`:398`)
    cannot yet be authored from the v4 managed prompt source. Keep the agent key exactly
    `gentle-orchestrator`; resume the retitle only after the source location is provided. Remove
    `opencode-sdd-engram-manage` from `global-config/tui.json:6` and update the `required_agents`
    check when unblocked. Pair verifier changes and digest re-pin.

### Paired verifier-edit inventory

Apply the listed verifier edits in the same slice as the related configuration change. Every slice
that edits `verify-workflow.sh` must also re-pin `VERIFY_SCRIPT_SHA256` in
`global-config/plugins/workflow-health-check.ts:93`.

- **S1:** In `verify-workflow.sh:2699-2703`, remove the three `host_sdd_*` reads from
  `registeredHostReads`; move `host_sdd_attempt_grant` and `host_sdd_archive_compose` from
  `gatedHostMutations` (`:2700`) into `retiredHostOperations` (`:2701`); ensure
  `HOST_MUTATION_OR_RETIRED_DEFAULT_NOT_DENY` (`:2703`) asserts every `host_sdd_*` permission is
  `deny`.
- **S4:** At `:2323`, change the writer/verifier pair from
  `["sdd-apply","sdd-verify"]` to `["gentle-ai-worker","gentle-ai-verify"]`.
- **S2/S3/S4:** At `:3089`, remove `sdd-research`, `sdd-apply`, and `sdd-verify` from the
  direct-model list (S2/S3), and add the generic agents (S4).
- **S3:** Delete the `sdd-research` shape/block check at `:2802-2816`.
- **S3:** At `:3264-3265`, remove `sdd-research`, `sdd-explore`, and `sdd-apply` from
  `githubReaderNames`/`githubBlockedNames`. The probe-coverage extractor at `:4726-4730` requires
  every listed name to be probeable.
- **S2/S3:** Drop the hard-coded `sdd-*` entries and `-astra` aliases from `PROBE_NAMES`
  (`:4679-4692`): S2 removes `sdd-apply`/`sdd-explore`; S3 removes `sdd-design`, `sdd-spec`,
  `sdd-verify`, and their aliases.
- **S4:** Extend the writer-shape check at `:2765-2766` to include `gentle-ai-worker` and
  `gentle-ai-worker-local`.

  - [ ] Validate JSON and changed-agent/permission presence and absence with a positive control;
    run the routing-guard tests and `bash -n verify-workflow.sh` per slice.
  - [ ] Record measured per-slice reviewability receipts and route evidence before any later
    work-unit commit; do not commit as part of this tracker preparation.

## Acceptance criteria

1. The twelve `sdd-*` agents and their task grants are removed; all `host_sdd_*` permissions are
   explicitly `deny`.
2. The four Q29d generic agents are present, with the intended orchestrator task grants and
   `required_agents` entries; retired agent requirements are absent.
3. `gentle-orchestrator` is retitled from the v4 source and retains the exact key.
4. `opencode-sdd-engram-manage` is absent from `global-config/tui.json`.
5. All five slices leave `global-config/opencode.json` valid JSON, pair verifier changes with the
   relevant configuration changes, and update the health-check digest to the current verifier
   hash.
6. Per-slice agent/permission probes include positive controls; the routing-guard suite remains
   94 pass / 0 fail; `bash -n verify-workflow.sh` succeeds.
7. The verifier itself is not run because it mutates host configuration; its pass remains a
   deploy-time step.
8. No live `~/.config` cleanup, commit, or host apply is included in this tracker-creation unit.

## Authorized paths

- `global-config/opencode.json`
- `global-config/tui.json`
- `verify-workflow.sh`
- `global-config/plugins/workflow-health-check.ts` (digest pin only)
- `odd/tasks/q31-agent-allocation.md`

Not authorized: `global-config/AGENTS.md`, `global-config/systematic.jsonc`, plugins other than the
digest pin, and all live `~/.config` paths.

## Checks

Run each check for every slice:

- `global-config/opencode.json` parses as valid JSON.
- A changed-agent/permission presence-and-absence probe passes and includes a positive control
  demonstrating it detects the pre-change form.
- `HOME=<mktemp -d> bun test tests/routing-guard` remains **94 pass / 0 fail**.
- `bash -n verify-workflow.sh` succeeds.
- `VERIFY_SCRIPT_SHA256` equals the new `verify-workflow.sh` SHA-256 after the slice's verifier edit.
- Do **not** run `verify-workflow.sh`: it mutates host configuration. Its pass is a deploy-time
  step, not an in-sandbox check.

## Progress

- 2026-10-10: tracker created from the owner-provided read-only mapping of the current tree.
  `global-config/opencode.json` is 2935 lines; the old TODO line references are stale.
  Q29 is done. No Q31 implementation, commit, verifier execution, or host apply has been
  performed in this tracker-creation step.
- 2026-10-10: Pre-code advice from `advisor-integration-pre`, Task
  `ses_eda1f91bbffe3zYguWZEQT76pQ` (model family OpenAI/Sol, independent of the DeepSeek author),
  returned **GO-with-corrections**. This is advisory evidence only; it does not authorize
  implementation or replace required review.
- 2026-10-10: S1 implemented in a sandbox worker (sandbox result exported for PM apply; no commit,
  no host apply, `verify-workflow.sh` not run). Edits: `global-config/opencode.json` host-SDD
  lockdown (33 permission entries `deny`; 7 agent tool flags `false`); `verify-workflow.sh`
  (`registeredHostReads` drops the three `host_sdd_*` reads; `host_sdd_attempt_grant` and
  `host_sdd_archive_compose` move from `gatedHostMutations` into `retiredHostOperations`, now all
  13 retired `host_sdd_*` names); `global-config/plugins/workflow-health-check.ts` digest re-pin
  `68d89eb0…` → `38c5dbfaebc3bc0d1493afac1916022fba9cfb0bdbbbb15aa62b9e3986b46674`. Checks:
  `python3 -m json.tool` clean; probe 33/33 `deny` + 7/7 `false`, 0 non-deny, positive control
  detects injected `"allow"`/`"ask"`; `bash -n` rc 0; routing-guard suite 94 pass / 0 fail;
  `sha256sum verify-workflow.sh` equals the pinned digest.

## Route, triggers, and actual dispatches

- **Route:** delegated (`workflow-odd-secure`). This preparation tracker does not perform
  implementation or execution.
- **Trigger:** substantial change spanning `global-config/opencode.json` and its paired
  `verify-workflow.sh` edits.
- **Actual dispatches:** the tracker-creation writer for the preparation task; 2026-10-10 S1
  implementation dispatched to the `odd-apply` sandbox worker (sandbox result exported; not
  committed or applied).

## Next step

S1 is complete in the sandbox; its result awaits PM apply and review. S2 — retire the first SDD
agent block — begins after the S1 result is applied per the owner's go. S5 remains BLOCKED pending
the location of the v4 managed prompt source; keep the `gentle-orchestrator` key fixed. The other
Q31 slices stay pending.
