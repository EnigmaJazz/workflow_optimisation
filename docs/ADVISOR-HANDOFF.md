# Advisor Handoff

This handoff records the current advisor setup and its verified capability boundaries for the agent-sandbox-integration project.

## Registered advisors

Twelve split advisors are registered; all use `"hidden": true` and `"mode": "subagent"`. Their
`variant` fields follow this table. `WORKFLOW.md` ("Pre-code advisors" and "Post-code advisors") owns
the assignment; this table follows it.

### Pre-code

| Advisor | Model |
|---|---|
| `advisor-design-pre` | `google/gemini-4-argon` |
| `advisor-security-pre` | `google/gemini-4-argon` |
| `advisor-spec-pre` | `openai/gpt-6.1-sol` (`high`) |
| `advisor-integration-pre` | `opencode-go/mimo-v2.6-flash` |
| `advisor-testing-pre` | `opencode-go/glm-5.3-flash` (`high`) |
| `advisor-maintainability-pre` | `opencode-go/glm-5.3-flash` (`high`) |

### Post-code

| Advisor | Model |
|---|---|
| `advisor-design-post` | `opencode-go/qwen3.7-plus` |
| `advisor-integration-post` | `opencode-go/glm-5.3-flash` (`high`) |
| `advisor-testing-post` | `opencode-go/qwen3.8-flash` |
| `advisor-security-post` | `opencode-go/qwen3.7-plus` |
| `advisor-maintainability-post` | `opencode-go/ling-3.1-flash` |
| `advisor-spec-post` | `openai/gpt-6.1-sol` (`high`) |

## Current permissions

**Read tools:** `read`, `sandbox_read`, `sandbox_list`, `sandbox_grep`, `sandbox_diff`, `codegraph_codegraph_explore`.

**Read-tool precondition:** `sandbox_read`, `sandbox_list`, `sandbox_grep`, and `sandbox_diff` require an active worker and fail before activation. A read cannot be the first sandbox call.

**Workspace-local mutation and execution (granted):** `sandbox_write`, `sandbox_edit`, `sandbox_apply_patch`, `sandbox_bash`.

**Not registered on the advisor tool surface:** `sandbox_finish`, `sandbox_apply`, `sandbox_copy_out`, and `sandbox_copy_in`. These are unavailable capabilities, not permission-denied calls. Native `edit`, `write`, and `bash` are denied.

**Also denied:** `grep`, `task` (advisors cannot delegate), and `ctx_memory` (no shared-memory writes).

All twelve split advisors are in the orchestrator's `permission.task`; the orchestrator dispatches them and they dispatch nothing.

## Available testing tools today

Advisors can create and run diagnostics inside their own isolated workspace via the granted sandbox tools. `sandbox_bash` output and `sandbox_diff` do return in-tool; advisors cannot return artifacts to the host. A persisted workspace export would require `sandbox_finish`, which is not registered on their tool surface. The orchestrator's delegated sandbox worker (`general`) remains the path for anything that needs to reach the host. The fixed host tools and bounded read tools (AFT, CodeGraph, AST-grep) are host-side.

**Lifecycle gap:** the granted mutation tools can activate a single-lifecycle worker that an advisor cannot finish or discard, leaving mutable-but-unexportable state. The owner decision on this gap is tracked as Q27.

## Missing capabilities

These are gaps, not available capabilities:

1. No read-only access for advisors to the agent-sandbox-integration project; advisors are scoped to this project.
2. No verified statement of the isolation guarantees the workspace tools rest on: network egress limits, resource caps, workspace lifetime, and side-effect visibility.
3. No verified contract for cross-project read-only inspection.

## Requested

Provide verified tool names and contracts for:

- **Read-only cross-project inspection:** state what the tool bounds, including project/path scope and available operations.
- **Workspace isolation guarantees:** state what is bounded for network egress, resources, workspace lifetime, and side-effect visibility.
