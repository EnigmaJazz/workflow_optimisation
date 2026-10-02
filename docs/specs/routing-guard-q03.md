# Routing guard Q03 — fix design (rev. 2, after advisor-integration)

Target: `global-config/plugins/systematic-routing-guard.ts`. Tests:
`tests/routing-guard/routing-guard.test.ts` (bun). Queue Q03 (absorbing the overlapping Q20 and
Q21 findings). Where this document and the tests disagree, the tests win, and this document is
corrected in the same change.

Behaviour stays warning-only (the guard never newly throws), apart from the existing generic-task
block.

## 0. Testability seam

`SYSTEMATIC_ROUTING_GUARD_STATE_ROOT`, when set, replaces `homedir()` for EVERY guard path use,
including the log directory `mkdir` (formerly a separate `homedir()` call at `:528`). The
module-level path constants become accessor functions that read the variable at each use; nothing
is fixed at import.

| Path | Location |
|---|---|
| key root | `<root>/.local/share/opencode/routing-keys` |
| log file | `<root>/.local/share/opencode/logs/routing-guard.log` (directory created on demand) |
| off switch | `<root>/.config/opencode/routing-guard-off` |

Unset, behaviour is unchanged. Tests always set it; production never does.

## 1. Specialist rule: deny by default (owner decision 2026-10-02)

A stage that declares `allowsSpecialists` gates every **writing** specialist dispatched by `task`
while that stage's route key is valid.

| State | Dispatched specialist | Result |
|---|---|---|
| stage artifact absent | any writing specialist | warn `<route> specialist <name> dispatched before <stage> stage artifact exists` |
| stage artifact present | listed in `allowsSpecialists` | no warning |
| stage artifact present | writing specialist not listed | warn `<route> specialist <name> is not allowed at <stage> stage` |

- **Read-only specialists** are exempt. The exemption uses an EXACT declared set plus structural
  patterns, exported together as `READ_ONLY_SPECIALIST_PATTERNS`, a list of anchored regexes. No
  loose "contains" matching, because under deny-by-default a wrong exemption lets a writer
  through.
  - **Exact names:** `explore`, `gentle-ai-explore`, `gentle-ai-verify`, `sdd-explore`,
    `sdd-verify`, `sdd-research`, `vision`, `architecture-strategist`, `spec-flow-analyzer`,
    `git-history-analyzer`, `issue-intelligence-analyst`, `pattern-recognition-specialist`,
    `deployment-verification-agent`, `repo-research-analyst`, `best-practices-researcher`,
    `framework-docs-researcher`, `learnings-researcher`.
  - **Structural patterns:** the prefixes `review-`, `asi-review-`, `advisor-` and `jd-judge-`,
    and the suffix `reviewer`.
- Every other name, including an unknown one, is a writing specialist.
- **Stage writer lists.** The `workflow-odd-secure` `tracker` stage and the `workflow-systematic`
  `plan` stage list every legitimate writer in this setup: `general`, `systematic-implementer`,
  `frontend-dev`, `frontend-dev-premium`, `frontend-apply`, `frontend-apply-local`,
  `jd-fix-agent`, `pr-comment-resolver`, `bug-reproduction-validator`, `design-iterator`,
  `sdd-apply`, `sdd-apply-local`, `gentle-ai-worker` and `gentle-ai-worker-local`.
  - So "not allowed at stage" flags only writers nobody has declared; that is the purpose of deny
    by default.
  - The specialist policy lives in three places (this table, the `opencode.json` task
    permissions, and the route skills). A Q28 verifier check must keep them consistent.
- Stages without `allowsSpecialists` do not gate specialists.
- This replaces the old allow-list behaviour, under which unlisted writers bypassed the check.
  The earlier "R2-001 inverted predicate" description was inaccurate: the polarity was right, and
  the gap was the allow-list.

## 2. Route-namespaced stage markers

- **Writer:** for every route whose stage pattern matches a written path, write
  `artifact-<route>-<stage>`, for example `artifact-workflow-odd-secure-tracker` or
  `artifact-workflow-systematic-plan`.
- **Resolver:** `hasRouteStageArtifactInAncestorChain(sessionID, route, stage)` checks, per
  session in the chain:
  1. `artifact-<route>-<stage.id>`;
  2. legacy markers:
     - `artifact-<stage.id>` (unnamespaced) counts for a route only while that stage id is
       UNIQUE across all routes in `ROUTE_STAGES`. This keeps in-flight evidence for every
       route today, and closes the cross-route hole automatically the moment two routes share an
       id.
     - `artifact-odd-<stage.id>` counts only for `workflow-odd-secure`.
     - On disk 2026-10-02: 25 `artifact-tracker`, 23 `artifact-odd-tracker`, and no Systematic
       artifact markers.
     - The rule is a pure exported function, `stageMarkerNames(route, stageId, routeStages)`,
       which returns the ordered artifact marker names. It is tested with a synthetic table where
       two routes share an id;
  3. `skill-<marker>` for each of the stage's `skillMarkers`. Skill loads are facts about a
     session, not a route.
- So a marker from one route can never satisfy another route's stage of the same id.
- **Skill names are canonicalised before naming their markers.** A leading `systematic:`
  qualifier is stripped, then the name is sanitised, so `systematic:ce:plan` and `ce:plan` both
  give `skill-ce-plan`. Previously the qualified form gave `skill-systematic-ce-plan`, which never
  matched `ce-plan`.
- Merging child markers into the parent copies `artifact-*` and `skill-*` files, the namespaced
  ones included.

## 3. Written-path extraction

`targetPath` per tool:

| Tool | Path used |
|---|---|
| `sandbox_write`, `sandbox_edit` | `path` |
| `sandbox_copy_in` | `workerPath` (the destination) |
| `sandbox_copy_out` | `hostTarget` (the destination), never `workerPath` (the source) |
| `sandbox_apply_patch` | every path from the patch's `+++ b/<path>` lines (Git unified diff; `+++ /dev/null` ignored; a trailing tab and timestamp stripped) |

Each extracted path is matched against every route's stage patterns. The bootstrap check
(`workflow-odd-secure`, writes before the tracker exists) treats `sandbox_apply_patch` as
path-known, using the extracted paths.
- A patch that touches the tracker counts as writing it, so there is no warning.
- Otherwise there is ONE warning per call: `workflow-odd-secure bootstrap: write to <paths> before
  tracker stage artifact exists`, where `<paths>` is the extracted non-tracker paths, comma-space
  joined, in patch order.
`sandbox_apply` stays unknown-path (residual Q20 item).

## 4. Awaited writes

Every disk write the hooks perform completes before the hook returns:
- the stage marker;
- the skill marker;
- `mintWorkflowKey`;
- `refreshWorkflowKeyActivity`;
- the task parent-linking chain (`.parent`, marker merge, child key removal, `inherited.key`).

Errors stay swallowed, as now, but they are awaited. So a check that immediately follows sees the
state.
- **Time box:** each awaited write chain is raced against a 2,000 ms timeout. On timeout the hook
  continues (the chain is abandoned, errors swallowed), so a hung filesystem can never stall a
  tool call or a `task` return indefinitely.
- **Scope:** these guarantees hold when this hook runs. Under OpenCode V2, a plugin that refuses a
  call can cause later plugins' hooks to be skipped, and `output.args` becomes `event.input`.
  This is tracked for the V2 port (Q42).

## 5. Key inheritance across up to three ancestors

- **Status:** `getWorkflowKeyStatus` walks `inherited.key` → `inherited_from` up to 3 hops, with a
  visited set (a cycle means stop). At each session it applies the same skill and TTL rules to
  that session's own `workflow-*.key` files. The first valid key gives `valid`. Otherwise the
  result is `expired` if any expired key was seen, else `missing`.
- **Refresh:** `refreshWorkflowKeyActivity` refreshes `last_active` on the VALID key found by the
  same walk, wherever it lives, including the root ancestor.
  - It never touches an expired key, so an expired key is never revived by activity.
  - The refresh runs before the status check in the before-hook, so this ordering matters.
  - The 60 s throttle per session is unchanged.

## 6. Warning de-duplication

Every console warning goes through one de-dup set keyed by `sessionID`, tool and failure text,
including the `host_review_start`, specialist and skill-load warnings. The log file still gets
every occurrence. Different failures for the same tool are not suppressed by each other.

## 7. Exports for tests

`ROUTE_STAGES`, `READ_ONLY_SPECIALIST_PATTERNS` and `stageMarkerNames` are exported (read-only
data and a pure function). The plugin default export is unchanged.

## Not changed

- `COPYFILE_EXCL` in the marker merge (R3-child-marker-merge-excl). Markers are existence-only, so
  an existing parent marker already represents the stage. Skipping the copy loses nothing. Not a
  defect.
- Q20's remaining items: R2-003, R3-child-regex-format, R3-systematic-apply-marker-gap, and R4-001
  verifier factory.
