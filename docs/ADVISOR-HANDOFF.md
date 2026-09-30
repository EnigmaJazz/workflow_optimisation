# Advisor Handoff

This handoff records the current advisor setup and its verified capability boundaries for the agent-sandbox-integration project.

## Registered advisors

Five advisors are registered; all use `"hidden": true`, `"mode": "subagent"`, and `"variant": "medium"`:

| Advisor | Model |
|---|---|
| `advisor-design` | `opencode-go/deepseek-v4.1-flash` |
| `advisor-integration` | `opencode-go/deepseek-v4.1-flash` |
| `advisor-security` | `opencode-go/deepseek-v4.1-flash` |
| `advisor-testing` | `opencode-go/kimi-k2.7-code` |
| `advisor-maintainability` | `opencode-go/mimo-v2.6-flash` |

## Current permissions

**Read tools:** `read`, `sandbox_read`, `sandbox_list`, `sandbox_grep`, `sandbox_diff`, `codegraph_codegraph_explore`.

**Workspace-local mutation and execution (granted):** `sandbox_write`, `sandbox_edit`, `sandbox_apply_patch`, `sandbox_bash`.

**Denied because they cross back to the host or grant unrestricted host access:** `sandbox_finish`, `sandbox_apply`, `sandbox_copy_out`, `sandbox_copy_in`, `sandbox_discard`, and native `edit`, `write`, `bash`.

**Also denied:** `grep`, `task` (advisors cannot delegate), and `ctx_memory` (no shared-memory writes).

All five advisors are in the orchestrator's `permission.task`; the orchestrator dispatches them and they dispatch nothing.

## Available testing tools today

Advisors can create and run diagnostic scripts inside their own isolated workspace via the granted sandbox tools, but cannot return results from it. The orchestrator's delegated sandbox worker (`general`) remains the path for anything that needs to reach the host. The fixed host tools and bounded read tools (AFT, CodeGraph, AST-grep) are host-side.

## Missing capabilities

These are gaps, not available capabilities:

1. No read-only access for advisors to the agent-sandbox-integration project; advisors are scoped to this project.
2. No verified statement of the isolation guarantees the workspace tools rest on: network egress limits, resource caps, workspace lifetime, and side-effect visibility.
3. No verified contract for cross-project read-only inspection.

## Requested

Provide verified tool names and contracts for:

- **Read-only cross-project inspection:** state what the tool bounds, including project/path scope and available operations.
- **Workspace isolation guarantees:** state what is bounded for network egress, resources, workspace lifetime, and side-effect visibility.
