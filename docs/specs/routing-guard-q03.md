# Routing guard Q03 — fix design

Target: `global-config/plugins/systematic-routing-guard.ts`. Tests:
`tests/routing-guard/routing-guard.test.ts` (bun). Queue Q03 (absorbing the overlapping Q20 and
Q21 findings). Where this document and the tests disagree, the tests win, and this document is
corrected in the same change.

Behaviour stays warning-only (the guard never newly throws), apart from the existing generic-task
block.

## 0. Testability seam

`SYSTEMATIC_ROUTING_GUARD_STATE_ROOT`, when set, replaces `homedir()` for every guard path. It is
read at each use, not at import.

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

- **Read-only specialists** are exempt. The exemption is exported as
  `READ_ONLY_SPECIALIST_PATTERNS`, matched against the whole name:
  - `explore`, `gentle-ai-explore`, `gentle-ai-verify`;
  - names ending in `reviewer` or `-refuter`, or starting with `review-`, `asi-review-` or
    `advisor-`;
  - `jd-judge-a`, `jd-judge-b`;
  - names containing `research` or `analyst`.
- Every other name, including an unknown one, is a writing specialist.
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
  2. the legacy markers, ONLY for `workflow-odd-secure`: `artifact-<stage.id>` and
     `artifact-odd-<stage.id>`. Real ODD markers of both forms exist on disk, and they keep
     working;
  3. `skill-<marker>` for each of the stage's `skillMarkers`. Skill loads are facts about a
     session, not a route.
- No other route honours an unnamespaced marker, so a marker from one route can never satisfy
  another route's stage of the same id.
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
path-known, using the extracted paths. A patch that touches the tracker counts as writing it.
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

## 5. Key inheritance across up to three ancestors

- **Status:** `getWorkflowKeyStatus` walks `inherited.key` → `inherited_from` up to 3 hops, with a
  visited set (a cycle means stop). At each session it applies the same skill and TTL rules to
  that session's own `workflow-*.key` files. The first valid key gives `valid`. Otherwise the
  result is `expired` if any expired key was seen, else `missing`.
- **Refresh:** `refreshWorkflowKeyActivity` refreshes `last_active` on the valid key found by the
  same walk, wherever it lives, including the root ancestor. The 60 s throttle per session is
  unchanged.

## 6. Warning de-duplication

Every console warning goes through one de-dup set keyed by `sessionID`, tool and failure text,
including the `host_review_start`, specialist and skill-load warnings. The log file still gets
every occurrence. Different failures for the same tool are not suppressed by each other.

## 7. Exports for tests

`ROUTE_STAGES` and `READ_ONLY_SPECIALIST_PATTERNS` are exported (read-only data). The plugin
default export is unchanged.

## Not changed

- `COPYFILE_EXCL` in the marker merge (R3-child-marker-merge-excl). Markers are existence-only, so
  an existing parent marker already represents the stage. Skipping the copy loses nothing. Not a
  defect.
- Q20's remaining items: R2-003, R3-child-regex-format, R3-systematic-apply-marker-gap, and R4-001
  verifier factory.
