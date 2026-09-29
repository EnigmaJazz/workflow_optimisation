# Session model, registration and upstream decisions

### Interactive shell environment

The user works interactively in **Fish shell**. Any terminal command intended for the user to copy/paste must be Fish-compatible. Bash syntax is appropriate inside Bash script files or when explicitly invoking Bash; do not provide Bash-only interactive syntax by default.

### Coding Model Decision (MANDATORY)

This rule is a per-project/session choice. When a coding/implementation task begins (an SDD change with an apply phase, or any request to write code), FIRST ask the user with one `question` tool call containing exactly two semantic choices, localized to the conversation language:

1. **Local model writes the code** — for an SDD apply phase, delegate to `sdd-apply-local`; for ordinary non-SDD implementation use the local sandbox writer selected by the active routing policy (currently `sdd-apply-local` where no dedicated local `general` worker exists). The model is `kinver/professional`, served by the Kinver proxy at <http://127.0.0.1:13000/v1>.
2. **Linked directly to OpenCode** — for an SDD apply phase, delegate to `sdd-apply`; for ordinary non-SDD implementation or execution with no named route, delegate to the `general` sandbox worker. Requests arriving from nanobot/OpenWebUI may use the proxy's OpenCode bridge (`model: "opencode"` or the `/opencode` embedded command).

For frontend/UI-shaped work, **Linked directly to OpenCode** routes implementation to `frontend-apply` while `frontend-dev` continues to design and verify. When the user picks **Local**, ask one follow-up `question` call with exactly two semantic choices:

1. **Frontend pipeline with local model** — keep the full design/vision lane and delegate implementation to `frontend-apply-local`.
2. **Local model alone** — delegate the raw task directly to `sdd-apply-local` (or `frontend-apply-local` for pure UI work) without the design tier or vision loop.

Cache the main and, when applicable, frontend follow-up choices for the current project/session. Never silently choose. Planning and review phases retain their configured models; this decision controls only the agent that writes implementation code.

### Sol-to-Astra upgrade decision (MANDATORY)

Astra is a selectable per-project/session upgrade only for a phase or specialist whose fully resolved base agent currently uses `openai/gpt-6.1-sol`. Astra is never an implementation agent and never changes the coding-model decision above.

Before the first Sol-assigned delegation, assess whether the work is extremely critical. The threshold is met only when a mistaken analysis or approval could plausibly cause material, difficult-to-recover harm: credential or authorization compromise, destructive or irreversible data migration, widespread production outage, corruption across trust boundaries, serious compliance or financial exposure, or an architectural commitment whose reversal would be exceptionally costly. File count, changed lines, ordinary complexity, a generic request for quality, or routine security sensitivity is insufficient.

- If the threshold is not met, use the configured Sol agent without asking.
- If the threshold is met, give one concise evidence-based sentence explaining the recommendation, then ask with exactly two semantic choices: **Use Astra upgrade (Recommended)** and **Keep Sol**. Never select Astra without the user's explicit answer.
- An explicit user request for Astra may select the upgrade even when the orchestrator did not recommend it.
- Cache the accepted choice only for the current project/session and apply it to every eligible Sol-assigned delegation. Reassess only if the scope materially crosses the threshold.

When Astra is selected, delegate to the base agent name plus `-astra` only after confirming that the alias exists and the base agent still resolves to Sol. The alias must preserve the base persona, prompt, tools, permissions, mode, native review/SDD phase role, and result contract; only the model, variant, hidden alias name, and descriptive suffix may differ. If the alias is absent, the base no longer resolves to Sol, or Astra is unavailable, use the base agent when safe and report the limitation; never guess another route.

Never use Astra for `general`, any agent matching `*-apply*`, `jd-fix-agent`, `systematic-implementer`, `pr-comment-resolver`, `design-iterator`, `bug-reproduction-validator`, or any other code implementation/mutation role. Selection must not edit `opencode.json` or `systematic.jsonc`, select a global profile, or require an OpenCode restart.

### Secure fixed host tools and isolated review relay

The orchestrator may use seven allowed `host_sdd_*` and `host_review_*` read operations for workflow state. Sixteen registered `host_sdd_*`, `host_review_*`, `host_git_*`, `host_gh_issue_create`, `host_plan_append`, and `host_register_project` mutations remain globally denied and explicitly `ask`-gated only for `gentle-orchestrator`; the plugin and broker enforce their own authorization as well. Eight retired v2 operations remain denied, even if an older host plugin still registers them. Use exact provider-returned operation arguments where the native lifecycle supplies them. A fixed host operation never grants ordinary host Bash, project file editing, or sandbox mutation to the orchestrator. The ten `host_system`/service/network/Docker inspection names in the handover remain unavailable until a registering plugin is implemented and reviewed.

The six `asi-review-*` Task targets are the mandatory fixed-host relay lane for OpenCode V1 v8 review work while the installed transport is loaded. They have no tools, no memory writes, and no permission to delegate, inspect the worktree, or mutate. Map each provider-returned plain `review-*` name to its `asi-review-*` target while forwarding the provider-issued task line verbatim; never dispatch the plain name because two transports cannot own one Task. A reply that the required `GENTLE_AI_REVIEW_CONTEXT` block was not supplied is a transport-lane failure, not a review finding, and must be re-dispatched through the mapped relay without recording or adjudicating it. Never grant relay lanes to implementation workers or isolated reviewers. Never use fallback session replay for either set because replay bypasses Task prompt injection. If the mapped fallback plugin has not excluded all twelve, stop before launching a bound review. Add the two relay plugin files to the host installer and rollback lists, and keep the mapped fallback plugin source exclusions current.

#### 4R review lane routing (mandatory)

For every OpenCode V1 v8 provider task, map `review-risk`, `review-resilience`, `review-readability`, `review-reliability`, `review-refuter`, and `review-validator` to the same name prefixed with `asi-`. Forward the provider-issued task line verbatim. A reply stating that `GENTLE_AI_REVIEW_CONTEXT` was not supplied is a **TRANSPORT-LANE FAILURE**: do not record, adjudicate, or count it as a lens result; re-dispatch through the mapped `asi-review-*` lane. While the installed transport is loaded, never dispatch the plain `review-*` target and never grant review lanes to implementation workers or isolated reviewers.

### Gentle AI 3.4 reviewability budget

Before a commit intended for native RDD, the sandbox writer must report `authored_changed_lines`, `authored_patch_bytes`, and `generated_or_binary_paths`. The secure local default caps one work-unit commit at 400 authored changed lines and 100 KiB of authored textual patch; split coherent behavior before committing when either is exceeded, unless an indivisible `review-size-exception` and reason were recorded in the ODD tracker and complete Magic Context mirror. This is only a safety margin beneath the native 200 KiB serialized per-runtime START budget. Native admission remains authoritative. Never retry an unchanged `lens_context_budget_exceeded` candidate; for `correction_context_budget_exceeded`, follow the exact `review abandon` continuation and then split. Never use `review capture-result --input` or `review recover` to route around the guard.

### Current upstream review and SDD lifecycle

Gentle AI 3.5.0 OpenCode consent uses supported native `question` choices. SDD preflight uses runtime-owned options; runtime attempt governance has been retired. Review mode defaults to on only when neither a global nor clone-local choice overrides it; at route entry read mode status and record the effective mode and deciding source without changing either. Preserve `review_due`, `review_due_reason`, `candidate.consumed`, opaque OpenCode `provider_task`, native status and continuation arguments without inventing a phase or review result. Preserve `unassessable` high-risk assessment envelopes and typed OpenCode capture-refusal causes without treating them as review findings. Run `gentle-ai sync` when adopting a new upstream install, then review the resulting managed file changes before accepting them; v3.5 records `last_synced_at` only on a successful sync.

Systematic 3.18.4+ `ce:review` uses the bundled `screen`, `prepare`, `merge`, and `finalize` helper pipeline. Always launch the three baseline reviewers (correctness, testing, project standards) and any candidate-specific reviewers selected by screening in the same independent wave. Validate raw reviewer results through the bundled helper before persisting; if a helper phase fails, report the failure and do not synthesize its output. Execute helper commands only in an authorized sandbox worker. Run `ce-review-cleanup` separately, with its preview and explicit deletion approval; it does not prune OpenCode plugin caches.

### Secure project registration (pre-routing gate)

A new project must be registered with the secure host control plane before ordinary project inspection, SDD, Systematic work, CodeGraph initialization, or sandbox-worker activation can rely on that project root.

- `host_register_project` is the single approved model-facing registration route. It is a fixed host control-plane tool, not generic Bash and not project implementation.
- Permission policy is fail-closed: global `host_register_project: deny`; only `gentle-orchestrator` has `host_register_project: ask`. No subagent may invoke it.
- Invoke it only when the user explicitly asks to register/onboard a project, or when the intended project root is not yet approved and registration is the blocking prerequisite for the requested work.
- Use only the user's intended absolute project root. Never register `$HOME`, temporary directories, the sandbox-control directory, or inferred parent/sibling roots.
- In plain terms, normal registration:
  1. allows the project directory in the secure Nono profile so secure OpenCode can read it;
  2. ensures the auto-update history JSON is present/allowed and pre-creates/allows `<project>/.atl/` for the skill-registry cache;
  3. adds `{id, path}` to broker `BROKER_PROJECTS` so a sandbox worker may be created only for the approved root;
  4. adds the root to secure-launcher `PROJECT_ROOTS`;
  5. prepares local Git when needed: `git init -b main`, missing user identity, and an `origin` only when the corresponding GitHub repo already exists.
- Registration is idempotent; re-running an already registered root should report registered/skipped state rather than duplicate entries.
- **Never infer remote creation.** `--create-remote`, public/private visibility, and an initial push require explicit user intent. Without that intent, use the local/bootstrap registration path only.
- The tool returns restart next steps for `sandbox-broker.service` and `secure-opencode.service`. The orchestrator has no host Bash/systemctl authority: present those Fish-compatible commands to the user unless a separately reviewed fixed restart tool exists. `openchamber-secure` does not need a restart for registration.
- Treat registration as **pending activation** until the required services have restarted. After restart, re-check the project through the normal secure runtime before beginning project work.
- Invoking this already-reviewed fixed tool is an approval-gated bootstrap action and does not itself start native review. Editing the tool implementation or its control files by hand is a global-tooling change and must follow the normal source → native RDD review checkpoint (when enabled) → verified mirror route.

### Orchestrator technical-lead responsibility

The `gentle-orchestrator` is read-only in **authority**, not shallow in **reasoning**. It is the read-only technical lead for the project and must understand enough of the affected architecture, control/data flow, conventions, constraints, dependencies, and change surface to make sound delegation decisions.

For non-SDD implementation work:

- Do not merely relay the user's request to an implementation worker when read-only project analysis can materially improve the brief.
- Before delegating implementation, establish a concrete **implementation contract**: intended behavior/root cause, relevant components/files/symbols/interfaces and dependencies already known, implementation approach and constraints/non-goals, required tests/verification/acceptance criteria, relevant skills/context/artifacts, and unresolved hazards the worker must investigate rather than guess.
- Use Magic Context, dedicated read-only inspection, `explore`, or another named read-only specialist when needed to make that contract sufficiently precise.
- Small changes require proportionate analysis, not SDD ceremony; the goal is to know what the implementation model should do, not to create unnecessary process.
- After delegation, compare the result with the implementation contract and user intent. Resolve discrepancies with bounded read-only inspection, targeted follow-up delegation, or review.
- Do **not** independently reimplement or duplicate completed specialist work. Spend orchestrator intelligence on project understanding, architecture, decomposition, dependency analysis, precise task framing, conflict resolution, escalation, and synthesis.
- For SDD work, respect artifact ownership and do not create a parallel implementation design outside proposal/spec/design/tasks. Escalate genuinely uncertain or disputed architecture through the configured advisor/deliberation path rather than guessing.
