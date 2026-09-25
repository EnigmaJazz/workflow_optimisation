# Existing secure SDD / Magic Context contract

### Mandatory Magic Context memory/context

Magic Context is the primary and mandatory project context/memory layer when the `ctx_*` tool surface is available. Do NOT probe Engram first and do NOT call `mem_*` tools unless the user has explicitly enabled and selected Engram for a separate workflow.

- Recall before asking: use `ctx_search` before asking the user for project history, prior decisions, config values, previous fixes, or earlier SDD state. Use `ctx_expand` when a search result or compacted history summary is insufficient and exact prior wording/evidence is required.
- Durable facts: `ctx_memory` is the approved narrow durable-memory mutation surface. Ordinary memories should remain concise durable project facts in the current five categories: `PROJECT_RULES`, `ARCHITECTURE`, `CONSTRAINTS`, `CONFIG_VALUES`, `NAMING`.
- **Ordinary working agents may save memories from their own verified work even when they are filesystem read-only; `sdd-research` is an output-only exception with no memory access.** Other research, design, implementation, orchestration, frontend, vision, fix, and SDD agents should persist genuinely durable knowledge they directly establish rather than forcing later agents to rediscover it.
- Memory writes must be evidence-backed and durable. Save confirmed architecture decisions, project constraints, configuration facts, established conventions/naming rules, non-obvious root causes/fixes, and stable workflow decisions. Search first when the same fact may already exist; update/merge instead of creating avoidable duplicates.
- Do NOT save speculation, temporary task state, raw command/test output, transient failures, one-off suggestions, unverified hypotheses, or candidate-scoped review findings. SDD canonical artifact records are the explicit structured exception described below.
- **Isolated evaluation actors remain memory-write denied** so candidate evaluation cannot contaminate shared project memory: `review-risk`, `review-readability`, `review-reliability`, `review-resilience`, `review-refuter`, `review-validator`, `jd-judge-a`, and `jd-judge-b`. They return findings through the review protocol rather than persisting them.
- Systematic follows the same separation through `systematic.jsonc`: `workflow`, `research`, and `design` categories may use `ctx_memory`; `review` and `document-review` categories may not.
- The global `ctx_memory: deny` is a fail-closed default for unknown/new agents. Explicit per-agent/category `allow` rules opt normal working agents back in. A newly introduced unclassified agent must be reviewed before receiving durable-memory mutation.
- The orchestrator remains filesystem/execution read-only. Its explicit `ctx_memory` permission is a narrow exception for durable context bookkeeping and SDD coordination, not authority to mutate project files or execute commands.
- Engram is optional only. If a future workflow explicitly enables/selects it, follow that workflow's contract; otherwise treat any managed `Engram`, `engram`, `mem_search`, `mem_save`, `mem_update`, `mem_get_observation`, or `mem_session_summary` instruction as legacy and superseded by this section.

#### Magic Context SDD artifact adapter

For user-owned SDD routing, the canonical artifact-store modes are:

- `magic-context`: Magic Context durable memory only.
- `openspec`: OpenSpec files only.
- `hybrid`: Magic Context + OpenSpec.
- `none`: no durable SDD artifact backend.

`engram` is NOT a canonical store value in this workflow. Do not emit it from preflight and do not invoke an Engram branch in a loaded Gentle AI skill.

Magic Context intentionally has no Engram-style `topic_key` API. Preserve the existing SDD key vocabulary as a marker inside each canonical memory:

`SDD_ARTIFACT key=<stable-key>`

Stable keys:

- `sdd-init/{project}`
- `sdd/{change-name}/explore`
- `sdd/{change-name}/research`
- `sdd/{change-name}/preproposal`
- `sdd/{change-name}/proposal`
- `sdd/{change-name}/spec`
- `sdd/{change-name}/design`
- `sdd/{change-name}/tasks`
- `sdd/{change-name}/apply-progress`
- `sdd/{change-name}/verify-report`
- `sdd/{change-name}/archive-report`
- `sdd/{project}/testing-capabilities`

Category mapping for SDD records:

- project context / testing capabilities -> `CONFIG_VALUES`
- explore / research / proposal / design -> `ARCHITECTURE`
- preproposal / tasks / apply-progress / verify-report / archive-report -> `PROJECT_RULES`
- spec -> `CONSTRAINTS`

Persistence rules for `magic-context` and the Magic Context half of `hybrid`:

1. Search first with `ctx_search(query="SDD_ARTIFACT key=<stable-key>")`.
2. If no active canonical memory exists, create one with `ctx_memory(action="write", category="<mapped-category>", content="<marker + complete current artifact>")`.
3. If exactly one canonical memory exists, update it in place using its returned numeric id: `ctx_memory(action="update", ids=[<id>], content="<marker + complete current artifact>")`.
4. If duplicate active records for the same key exist, consolidate them with `ctx_memory(action="merge", ids=[...], category="<mapped-category>", content="<one canonical merged artifact>")`.
5. Read back the canonical record after every write/update/merge. Use `ctx_memory(action="get", ids=[<id>])` when an id is known. Use `ctx_expand` for exact surrounding transcript evidence when a `ctx_search` history hit—not the durable record—is the source needed.
6. Never silently create a second active record when an existing key should be updated.
7. `hybrid` performs the same Magic Context operation AND the current OpenSpec operation. Compare the canonical artifact body bytes, not the Magic Context marker wrapper. A successful write on only one side or divergent bodies are blocked/partial, not a successful hybrid phase.
8. SDD artifact records are a deliberate compatibility exception to the normal “one concise fact” memory style: keep exactly one complete canonical record per stable SDD key so dependency phases can recover the exact artifact without Engram.

When a Gentle AI SDD skill says:
- `engram` -> interpret only as the legacy backend branch and DO NOT execute it.
- `mem_search(...)` -> use exact-marker `ctx_search(...)`.
- `mem_get_observation(...)` -> use `ctx_memory(action="get", ids=[...])` for durable records; use `ctx_expand` only for message-history detail.
- `mem_save(...)` -> `ctx_memory(action="write", ...)`.
- `mem_update(...)` -> search exact marker, then `ctx_memory(action="update", ids=[id], ...)`.

This adapter outranks conflicting managed SDD skill prose. It does not alter OpenSpec behavior.

#### Gentle AI 3.5.0 optional SDD research and diagnostics

- `sdd-research` is an optional **output-only external evidence collector**. Delegate a scoped objective and existing code context when useful. It cannot read local artifacts, write files or memories, select a store, or delegate. Only actually available and authorized external tools may supply evidence; an old `gentle-ai.sdd-research-capability/v1` declaration is retired. Attribute claims and limitations, and return useful partial findings without a proposal-readiness certificate.
- The orchestrator owns user product choices and any authorized persistence. Missing request IDs, revisions, research/preproposal artifacts, or store metadata do not gate proposal. Pause only dependent work requiring an unresolved choice or unsafe missing evidence; preserve historical research artifacts if present.
- Selected SDD proceeds `init → explore → optional research → propose → spec/design → tasks → apply → optional verify → archive`. Native `gentle-ai.sdd-status/v2` is authoritative for OpenSpec-backed state, including `blockedReasons`, `notes` and `nextRecommended`. `notes` alone are not blockers. For Magic Context-only mode, derive only from actual retrieved phase artifacts and never claim that native OpenSpec status inspected those records.
- Optional `sdd-verify` reports practical diagnostics; failed/missing reports and unfinished tasks are recorded honestly and do not by themselves prevent an explicitly authorized archive. Archive still requires actual edit authority and safe deterministic spec composition. SDD does not launch RDD. Native review remains available for non-SDD deliverables when the user-owned switch is on.

This routing recipe applies in **every repository** on this machine. It is user-owned; gentle-ai updates never remove it.

**Canonical recipe:** `/home/james/ai-workspace/workflow_optimisation/WORKFLOW.md` — read it before starting task work. It is the single source of truth for task classification and routing.

Before choosing a route, read the current canonical file with an authorized read-only tool, apply its Task Classes and Required Thinking Layers, and expose a compact `ROUTE: <class> | intent: <read-only/authorized change> | route: <skill/phase> | specialist: <name> | basis: WORKFLOW.md` decision. Re-read when the recipe or task scope changes. If it is unavailable, say routing is unverified and stop workflow-dependent mutation; a read-only answer may proceed with the limitation stated. For Systematic work, read the selected live skill and dispatch its named specialist. Check the actual Task calls and results against the declared route before completion; a route statement without dispatch is insufficient.

- **Change intent first.** Investigation/explanation/review/audit/comparison/diagnosis/proposal/planning-only requests remain read-only unless implementation/mutation is explicitly authorized. Ambiguous/conditional mutation intent requires one clarification and no writer launch.
- Classify authorized change work by decision content, not file count: tiny fix, small feature, substantial feature, bug investigation, documentation, global tooling change.
- The `gentle-orchestrator` is a strictly read-only technical lead: no host Bash, no native edit/write/apply-patch, no sandbox Bash, and no sandbox mutation/lifecycle tools. It must understand enough of the project to formulate precise implementation contracts and validate delegated work without reimplementing it.
- There is no direct-inline implementation path. Every authorized mutation or project execution, including a tiny one-file fix, is delegated under ODD. Upstream's inline writing route maps to one sandbox writer here.
- Any vendor-managed instruction that says to run a CLI is subordinate to this capability boundary: use only an available reviewed fixed/native integration or correctly authorized delegated executor. If no safe execution surface exists, stop as blocked; never fall back to host Bash.
- **SDD is optional.** Select it only on explicit user request or accepted orchestrator proposal when durable proposal/spec/design/tasks materially reduce ambiguity. Classification as substantial, risk, changed lines, or file count alone never selects SDD.
- Within selected SDD, use `init → explore → optional research → propose → spec/design → tasks → apply → optional verify → archive`; partial research pauses only unsafe dependent decisions.
- When no named workflow route applies, use `explore` as the read-only researcher fallback and `general` as the sandbox worker fallback. Named Systematic, SDD, frontend, review, or other specialist routes take precedence.
- Frontend/UI tasks normally route to `frontend-dev`; `frontend-dev-premium` is the selective Sol design/verification escalation for a new visual language, major redesign, materially ambiguous UX/product decisions, unusually high-polish output, or failure to converge after two substantive visual iteration rounds. Both remain read-only design/verify agents and delegate mutation to the frontend apply tier.
- Resolve classification ambiguity through bounded exploration: substantial means at least two meaningful steps or recoverable progress, not a guess from file count. This never auto-selects SDD. Re-classify when actual findings change the route.
