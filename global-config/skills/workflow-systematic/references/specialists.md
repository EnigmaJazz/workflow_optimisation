# Existing Systematic specialist and sandbox contract

### Systematic specialist routing precedence

When a task has been routed through a Systematic skill, the Systematic skill's native specialist/subagent routing takes precedence over Gentle AI's generic delegated-direct `general` / `explore` fallback for the duration of that Systematic workflow.

- Do not replace a Systematic-named specialist requested by an active Systematic skill with OpenCode's `general` or `explore` agent.
- If `ce:work` selects subagent execution, dispatch implementation units to `systematic-implementer` exactly as the active Systematic skill specifies.
- If a Systematic skill specifies another bundled specialist such as `repo-research-analyst`, `git-history-analyzer`, `bug-reproduction-validator`, `correctness-reviewer`, or another current bundled agent, dispatch that named specialist directly.
- `explore` is the ordinary read-only researcher fallback and `general` is the ordinary sandbox worker fallback when no active Systematic or other named workflow specialist owns the work.
- Systematic skill instructions control specialist selection only within the Systematic workflow they belong to; they do not convert unrelated Gentle direct work into Systematic work.
- Systematic v3.18.4 workflow-guard completion metadata is authoritative. Preserve terminal `reasonCode` values across replay of the same `callID`; never reinterpret `invalid-transition`, `guard-unavailable`, `finalization-failed`, or `failed-operation` as success, and never let metadata-only replay overwrite a host failure sentinel.

### Sandbox-only project mutation

Native host project mutation is forbidden for every model agent.

- Native `edit`, `write`, and `apply_patch` are disabled/denied globally and must not be re-enabled by an agent override.
- The `gentle-orchestrator` is a strictly read-only coordinator. Native host Bash/edit/write and all sandbox mutation/execution/lifecycle capabilities are denied; fixed host workflow-control tools and dedicated read-only inspection remain available.
- SDD artifact writers use sandbox tools and never native host edit/write; `sdd-apply` additionally writes implementation code. `sdd-research` is an output-only external evidence collector with no local read/write or memory access. `sdd-verify` runs optional diagnostics and does not issue an archive certificate.
- Other implementation/fix workers use `sandbox_read`, `sandbox_list`, `sandbox_grep`, `sandbox_diff`, `sandbox_bash`, `sandbox_edit`, `sandbox_write`, and `sandbox_apply_patch` inside the worker.
- Sandbox host-boundary/lifecycle operations such as apply, copy-in/out, finish, and discard remain approval-gated for writer agents. They are not ordinary worker-local writes.
- Read-only reviewers, researchers, judges, refuters, validators, and coordinators do not receive sandbox file-mutation tools unless their current source role explicitly requires mutation.
- Systematic bundled agents that declare native `Edit` or `Write` must be sandbox-routed through the supported user-level `systematic.jsonc` `permission` overlay. Never create same-name Systematic agent stubs in `opencode.json`: native agent entries shadow plugin emission and can discard the bundled prompt/model. Category overlays deny mutation by default; exact mutator overlays may enable worker-local sandbox mutation. New Systematic agents without such a declaration remain non-mutating by default.
- AFT, CodeGraph, Context7, Magic Context, Systematic skill/status tools, and other explicitly allowed custom tools remain available to ordinary agents. Do not add `"*": false` to an ordinary worker merely to remove host writes; deny only the mutating capability. Immutable prompt-carried review actors may intentionally remain tool-less.
