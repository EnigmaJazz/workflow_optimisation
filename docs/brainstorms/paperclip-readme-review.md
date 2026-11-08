# Paperclip README review (Q119, D13, S36)

Status: **Read-only review artifact. No Paperclip code was installed, cloned, run or downloaded; only GitHub API reads and `docs.paperclip.ing` page reads.** This is a review, not adoption approval and not permission to install or enable any adapter.

## 0. Provenance

| Item | Value |
|---|---|
| Product / repo | Paperclip, `github.com/paperclipai/paperclip` (default branch `master`) |
| Pinned commit | `fcdceaf5fbe16b5fa1b98f36b0a0c8ec06f6c7aa` (still the tip of `master` when checked) |
| Latest release | `v2026.1106.0`, published 2026-11-06T22:31:53Z (GitHub releases API). Whether the commit equals the release tag was **not** checked: UNKNOWN |
| Licence (GitHub API and `LICENSE`) | MIT. `LICENSE` line 3: "Copyright (c) 2025 Paperclip AI"; README line 582: "MIT &copy; 2026 [Paperclip Labs, Inc]" (the two copyright lines differ) |
| Retrieval date | 2026-11-08 |
| Spec plan reviewed against | `docs/brainstorms/paperclip-spike-plan.md` sections 2-4 |

Evidence labels used below:

- **README** = `README.md` at the pinned commit (scratchpad copy, 600 lines; line numbers are of that file).
- **DOC** = a documentation file in the repo at the pinned commit (`docs/...` or `doc/...`).
- **CODE** = a source file at the pinned commit. Read by me; **not executed**. A code reading shows what the code says, not runtime behaviour.
- **LIVE** = a `docs.paperclip.ing` page. These are **not commit-pinned** (retrieved 2026-11-08); treat as unversioned.
- **UNKNOWN** = not found. A silence is not permission.

Linked documents reviewed: `docs/adapters/{overview,claude-local,codex-local,gemini-local,http,process,external-adapters,creating-an-adapter}.md`, `docs/api/{overview,authentication,costs,issues}.md`, `docs/deploy/{overview,deployment-modes,database,environment-variables,storage,local-development,docker}.md`, `docs/guides/agent-developer/cost-reporting.md`, `docs/guides/board-operator/{costs-and-budgets,importing-and-exporting}.md`, `docs/agents-runtime.md`, `doc/DATABASE.md`, `doc/spec/agent-runs.md`, `doc/plans/2026-11-03-accounting-contention-and-budget-enforcement.md`, `SECURITY.md`, `LICENSE`; code: `server/src/adapters/registry.ts`, `server/src/routes/adapters.ts`, `server/src/services/{adapter-settings,adapter-registry-config,adapter-registry-bootstrap,budget-exposure,costs,heartbeat,agent-runner-selection}.ts`, `packages/adapters/{claude-local,codex-local}/src/...`, `packages/shared/src/{constants.ts,validators/cost.ts}`, `packages/db/src/schema/{issues,cost_events}.ts`, `cli/src/commands/db-backup.ts`. LIVE: `reference/cli/installation.md`, `how-to/update-paperclip.md`, `reference/cli/service.md`.

Not reviewed (so UNKNOWN where they would matter): `docs/guides/execution-policy.md`, `docs/guides/board-operator/approvals.md`, `docs/cli/*` beyond `setup-commands` grep, `ROADMAP.md`, `doc/SPEC*.md`, the OpenAPI route (`server/src/routes/openapi.ts` exists; schema not read), `https://paperclip.ing` terms or privacy pages, the Docker image and compose files.

## 1. Headline findings (details in section 3)

1. **No documented global switch disables local CLI adapters or prevents spawning.** The only disable controls found are per adapter type (`PATCH /api/adapters/:type {"disabled": true}`, and the `PAPERCLIP_ADAPTERS` allowlist, which is not in the operator environment-variable reference). Both are documented in code and `doc/DATABASE.md` as hiding the type from new-agent admission while "Disabled adapters remain available to existing agents." That is a configuration claim only; process-spawn prevention is not claimed anywhere and no heartbeat-side check was found.
2. **Both `dangerously*` options are on by default in the code paths read**: `dangerouslySkipPermissions` defaults to `true` for `claude_local` (DOC and CODE), and `dangerouslyBypassApprovalsAndSandbox` resolves to `true` for `codex_local` by default unless the config carries an explicit sandbox or approval restriction. The DOC for codex says only "Skip safety checks (dev only)". This is the OPEN-10 conflict, now evidenced.
3. **The README is silent on provider terms (group H).** Subscription-CLI use is described as a supported path (README line 424; `codex-local.md` "ChatGPT-subscription auth"), with no terms statement. Subscription-billed runs are counted as zero cents against budgets (`budget-exposure.ts:32`).

## 2. Spec-recorded claims versus what was found

| Spec record (plan section 2) | Finding | Label |
|---|---|---|
| Local adapters `claude_local`, `codex_local`, `opencode_local`, `gemini_local` | Present. `gemini_local` is "experimental — adapter package exists, not yet in stable type enum" in `docs/adapters/overview.md`, but `gemini_local` is in `AGENT_ADAPTER_TYPES` in `packages/shared/src/constants.ts` (lines 28-43). DOC and CODE disagree | DOC / CODE |
| Org chart, issues, single assignee, blockers, comments, heartbeats, approval gates | Confirmed at README level (section 3F) | README |
| Budgets per company, agent, project; warn and hard-stop | Confirmed: `BUDGET_SCOPE_TYPES = ["company", "agent", "project"]` (`constants.ts:888`); thresholds `["soft", "hard"]` | CODE |
| `billingType` includes `subscription_included` | Confirmed: `BILLING_TYPES` (`constants.ts:839-846`) | CODE |
| Unpriced is not zero | Confirmed for display: "Missing costs are never treated as proof of free usage." (`cost-reporting.md:22-23`). But budget exposure treats `subscription_included` as zero (see E) | DOC / CODE |
| Enforcement uses recorded spend; delayed reporting delays a stop | Confirmed in README line 296 (quoted in E) | README |
| Approval gate is a prompt rule, not enforced | **Conflicting statements.** README line 216: "Approval gates are enforced, config changes are revisioned, and bad changes can be rolled back safely." Enforcement mechanism not reviewed (`approvals.md`, `execution-policy.md` unread): UNKNOWN | README |
| Custom non-spawning adapter | Partly answered, see C | DOC |
| Lead delegation | `docs/guides/board-operator/delegation.md` not read; README line 129 "Delegation flows up and down the org chart." Decision mechanism: UNKNOWN | README |
| Quota visibility | `claude-local.md:8-18` describes quota-wait classification from typed provider errors, not a quota-read API. Reading subscription quota in advance: UNKNOWN | DOC |

## 3. Answers to groups A-H

### A. Deployment and runtime

**README-stated**

- What it is: README line 43: "Paperclip is a Node.js server and React UI that orchestrates a team of AI agents to run a business."
- Install: README lines 356-362: "With **Node.js 24.11 or newer** installed: `npx paperclipai@latest onboard --yes` ... The CLI runs from npm's cache; your instance configuration and data persist locally."
- Default mode and bind: README line 401: "That quickstart path now defaults to trusted local loopback mode for the fastest first run. To start in authenticated/private mode instead, choose a bind preset explicitly: `... onboard --yes --bind lan` or `--bind tailnet`."
- Port and database: README line 420: "This starts the UI and API at `http://localhost:3100`. An embedded PostgreSQL database is created automatically — no setup required."
- Typical setup: README line 441: "Locally, a single Node.js process manages an embedded Postgres and local file storage. For production, point it at your own Postgres and deploy however you like."
- Remote access: README line 443: "For remote access, use authenticated mode with a private-network bind such as Tailscale, or deploy the persistent server with Docker."
- Extra host dependencies for local subscription sign-in: README line 424: "Local Claude and Codex subscription sign-in also needs Python 3 and the corresponding provider CLI on the Paperclip host. The Docker image includes them."
- Native runner: README line 427: "Source development also builds the native Paperclip Runner when enabled (the self-hosted default). Install a Rust toolchain, or set `PAPERCLIP_RUNNER_BINARY`..." Whether the runner runs for an npx install: UNKNOWN.
- Telemetry (README lines 549 and 554): "Telemetry is **enabled by default**"; disabled by `PAPERCLIP_TELEMETRY_DISABLED=1`, `DO_NOT_TRACK=1`, `CI=true`, or `telemetry.enabled: false`. Outbound destination and payload: README line 549 says "No personal information, issue content, prompts, file paths, or secrets are ever collected" (a vendor assertion, not verified).
- Optional Sentry and OpenTelemetry are opt-in (README lines 543-545).

**Confirmed in versioned DOC or CODE**

- Data location (DOC `docs/deploy/local-development.md:118-126`): Config `~/.paperclip/instances/default/config.json`; Database `~/.paperclip/instances/default/db`; Storage `~/.paperclip/instances/default/data/storage`; Secrets key `~/.paperclip/instances/default/secrets/master.key`; Logs `~/.paperclip/instances/default/logs`. Override: "`PAPERCLIP_HOME=/custom/path PAPERCLIP_INSTANCE_ID=dev pnpm paperclipai run`" (line 131); `docs/deploy/environment-variables.md:17`: "`PAPERCLIP_HOME` | `~/.paperclip` | Base directory for all Paperclip data".
- Default bind (DOC `docs/deploy/deployment-modes.md:10-16`): "## `local_trusted` The default mode ... **Host binding**: loopback only (localhost) ... **Authentication**: no login required ... **Board identity**: auto-created local board user". `environment-variables.md:12-20`: `PORT` default `3100`; `PAPERCLIP_BIND` default `loopback`; `HOST` default `127.0.0.1`; `PAPERCLIP_DEPLOYMENT_MODE` default `local_trusted`; `PAPERCLIP_DEPLOYMENT_EXPOSURE` default `private`.
- Authentication defaults: `local_trusted` = none (above). `docs/api/authentication.md`: "### Local Trusted Mode: No authentication required. All requests are treated as the local board operator." Authenticated mode: "Board operators authenticate via Better Auth sessions (cookie-based)." Agents: "short-lived JWT via the `PAPERCLIP_API_KEY` environment variable"; long-lived agent keys "hashed at rest".
- `authenticated`+`private` (`docs/deploy/overview.md:28`): "Binds to all interfaces for network access". `docs/deploy/docker.md` manual run passes `-e HOST=0.0.0.0`; which mode the Docker quickstart compose file selects: UNKNOWN (compose file not read).
- UI and REST separable: the UI is "served by the API server in dev middleware mode (same origin)" (`local-development.md:23`). Whether the UI can be disabled while keeping the API: UNKNOWN. The `pnpm dev:mobile` script serves a prebuilt UI separately that proxies `/api` (README line 479), which is not a statement about separability.
- Database: embedded Postgres by default; external via `DATABASE_URL` (`environment-variables.md:16`).
- Service model (LIVE `reference/cli/service.md:5`): "On macOS the service is a launchd agent; on Linux it is a systemd **user** service. Either way it runs as you, in your own account — nothing here needs `sudo`". Linux definition file `~/.config/systemd/user/paperclipai.service`; `--enable-linger` keeps it running without a login session (line 43).
- Managed install (LIVE `installation.md:51,59-65`): installs a `paperclipai` command into `~/.local/bin`; store root `~/.paperclip/cli`.

**Backup, export, upgrade**

- Backup: `paperclipai db:backup` (CODE `cli/src/commands/db-backup.ts`; `scripts/backup-db.sh` says "default: ~/.paperclip/instances/<instance-id>/data/backups"; retention configurable; `environment-variables.md:96` mentions `instance.general.backupRetention`). Restore procedure: not found in the files read (LIVE update page says "restore the pre-update backup" without commands in the lines read): UNKNOWN.
- Export: company export/import packages (README line 325: "Referenced secret values are omitted; review packages before sharing because plain environment values and local paths can remain. Packages share an operating setup; full-instance recovery uses backups."). Command shown in `importing-and-exporting.md:66`: `paperclipai company export abc123 --out ./backup --include company,agents,projects`.
- Upgrade (LIVE `how-to/update-paperclip.md`): line 11 "That checks npm, takes a database backup, swaps in the new version, restarts your background service if you have one, and leaves the previous version sitting there ready for an instant rollback." Line 165: "Rollback reverses the *code*, not your *data*. Database migrations that ran during the update are not undone." Line 169 warns about a hot-restart rollback from v2026.1012.0 or later. Release notes at `releases/vYYYY.MDD.P.md`.
- Pinned and canary installs: LIVE `installation.md:80-83`: `paperclipai install --version 2026.609.0`; `--canary`; `--ref main` ("downloads a repository at that commit and runs its dependency and build scripts on your machine", line 96).
- Update is not automatic by the evidence read; whether the CLI checks for updates in the background: UNKNOWN.

### B. REST API

**README-stated:** README names no endpoints. Routines can be triggered "through an API or webhook" (line 177). Linked docs: `https://docs.paperclip.ing`.

**DOC / CODE (versioned)**

- Base URL: `docs/api/overview.md:10`: "Default: `http://localhost:3100/api`".
- Auth scheme: "All requests require an `Authorization` header: `Authorization: Bearer <token>`", tokens being agent API keys, agent run JWTs, or "User session cookies" (`overview.md:16-26`). Whether `local_trusted` really accepts unauthenticated requests on every route: `authentication.md` says so; contradicts "All requests require" in `overview.md:16`. UNKNOWN which is authoritative.
- Issue create: `POST /api/companies/{companyId}/issues` with `status`, `priority`, `assigneeAgentId`, `parentId` (`docs/api/issues.md:48-62`). Update: `PATCH /api/issues/{issueId}`; "Updatable fields: `title`, `description`, `status`, `priority`, `assigneeAgentId`, `projectId`, `goalId`, `parentId`, `billingCode`" (line 77); `blockedByIssueIds` in the request (lines 108-114). Comments: `POST /api/issues/{issueId}/comments`. Checkout: `POST /api/issues/{issueId}/checkout`; conflict returns `409` "Another agent owns the task. **Do not retry.**" (`overview.md:52`).
- Cost events: `POST /api/companies/{companyId}/cost-events` (see E; schema in `packages/shared/src/validators/cost.ts`).
- Budgets: `PATCH /api/companies/{companyId}` `{ "budgetMonthlyCents": ... }`; `PATCH /api/agents/{agentId}` (`docs/api/costs.md:50-62`).
- Heartbeats and approvals: `docs/api/approvals.md` exists; not read. Wake-by-API specifics: UNKNOWN.
- Pagination: `overview.md:60`: "List endpoints support standard pagination query parameters when applicable." No parameter names for generic lists: UNKNOWN.
- Idempotency: cost events accept `idempotencyKey` (string, max 200) (`validators/cost.ts:6`); issue-thread interactions use `idempotencyKey` (`issues.md:209`). Idempotency for issue create: UNKNOWN.
- Rate limiting: `overview.md:64`: "No rate limiting is enforced in local deployments."
- Webhooks: outbound `http` adapter (see C); inbound routine webhook triggers named in README line 301 ("cron, webhook, and API triggers"); payload and auth: UNKNOWN.
- OpenAPI: a route file `server/src/routes/openapi.ts` exists at the pinned commit; whether a spec is served at runtime and its URL: UNKNOWN. The README does not mention it.
- Doc/code mismatch noticed: `docs/adapters/external-adapters.md` and `overview.md` show `curl -X POST http://localhost:3102/api/adapters` (port 3102), while the route in `server/src/routes/adapters.ts:341` is `router.post("/adapters/install", ...)` and the default port is 3100. Treat the adapter docs' endpoints as unreliable.

### C. Adapter control

**C1. Exact config key or flag that disables every local CLI adapter.** **UNKNOWN: none documented as global.** The mechanisms found:

| Mechanism | Excerpt and location | Disables configuration? | Prevents process creation? | Global across all local adapters? |
|---|---|---|---|---|
| `PATCH /api/adapters/:type` body `{ "disabled": true\|false }` | CODE `server/src/routes/adapters.ts` ~481-485: "Enable or disable an adapter. Disabled adapters are hidden from agent creation menus but remain functional for existing agents." Requires instance admin (`assertInstanceAdmin`) and is refused when `instance.adapters` is operator-hidden (`assertAdapterManagementVisible`, lines 70-76). | Yes, per type: hides from new-agent selection/admission | **No, by its own comment** ("remain functional for existing agents") | **No**: one type per call; 15 built-in types in `AGENT_ADAPTER_TYPES` (`constants.ts:28-43`), including `process`, `http`, `claude_local`, `codex_local`, `opencode_local`, `gemini_local`, `paperclip_runner`, `cursor`, `pi_local`, `hermes_local`, `kimi_local`, `grok_local` |
| `listEnabledServerAdapters(disabled)` | CODE `registry.ts:1244-1247`: "List adapters excluding those that are disabled in settings. Used for menus and agent creation flows — disabled adapters remain functional for existing agents but hidden from selection." | Yes, menus only | No | No |
| `PAPERCLIP_ADAPTERS` (inline JSON) / `PAPERCLIP_ADAPTERS_FILE` | `doc/DATABASE.md:1119-1123`: "`PAPERCLIP_ADAPTERS` and `PAPERCLIP_ADAPTERS_FILE` declare the effective operator adapter list. The declaration is parsed once for a process configuration and validated at startup. It does not rewrite stored preferences. A conflicting adapter toggle returns 403." CODE `adapter-settings.ts` `effectiveDisabledAdapterTypes`: every known type not listed as enabled is disabled; `adapter-registry-bootstrap.ts:21-27` does the same. Schema `packages/shared/src/validators/adapter-registry.ts`: entries `{adapterType, enabled (default true), runtimeImage?, envKeys?, allowFqdns?, probeCommand?, defaultEnv?}`, strict. | Yes: an allowlist, so an empty array `[]` would mark all known types disabled (reading of CODE, **not run**) | **No evidence**: same "Disabled adapters remain available to existing agents" (`doc/DATABASE.md:1117`) | Effectively all types if the list is empty or lists only non-local types (reading of CODE, not tested). Not in `docs/deploy/environment-variables.md`; found only in `doc/DATABASE.md`, `adapter-registry-config.ts` and tests. Self-hosted persistence: "Self-hosted instances continue to use `adapter-settings.json` for saved preferences." (`DATABASE.md:1123-1124`) |
| Scoped runner restrictions | `agent-runner-selection.ts:196`: "`... is disabled on this instance. Enable its adapter or choose another harness.`" (a creation/selection error for runner-profile harnesses `grok_local`, `pi_local`, `opencode_local`, `claude_local`, `codex_local`) | Yes for those harnesses at selection | Not shown | No |

Process-spawn evidence: the adapter contract is `docs/adapters/overview.md` ("How Adapters Work", lines 10-15): "3. The adapter spawns or calls the agent runtime". `grep` of `server/src/services/heartbeat.ts` (4,539 lines) found no reference to the disabled-type set (only unrelated "disabled" strings at lines 2105 and 3041), consistent with the registry comment that existing agents keep running. This is an absence from one grep, not a proof; a spawn-time check could live in another file. **Whether a disabled type refuses to spawn at runtime is UNKNOWN and requires the spike's process-observation evidence.**

Other controls that bear on spawning (not adapter-disable switches):

- Timer wakeups: `docs/agents-runtime.md:59`: "`intervalSec`: timer interval (0 = disabled)". README line 469: "Agents wake for assigned work and follow-up messages. Optional timer heartbeats let them check for work periodically". So assignment itself wakes an agent and invokes its adapter.
- Linux filesystem confinement for local coding adapters (DOC `doc/spec/agent-runs.md`, under 7.2): "`filesystemScope: "workspace"` adds host-level filesystem confinement around the CLI process. It is disabled by default and independent of the CLI's own approval or sandbox flags." Uses Bubblewrap. Also `networkScope` and `networkAllowlist` keys appear in the sample config. These confine a spawned process; they do not stop it from being spawned.

**C2. Custom non-spawning adapter or webhook.**

- `http` adapter (DOC `docs/adapters/http.md:6`): "The `http` adapter sends a webhook request to an external agent service. The agent runs externally and Paperclip just triggers it." Config: `url` (required), `headers`, `timeoutSec`. Body: `runId`, `agentId`, `companyId`, `context{taskId, wakeReason, commentId}` (lines 34-49). The agent calls back using "`PAPERCLIP_API_URL` and an API key" (line 51). This is a built-in, non-CLI path.
- `hermes_gateway` and `openclaw_gateway` also call an already-running service: "Use `hermes_gateway` when Hermes is already running as an HTTP/SSE API server and Paperclip should call that server instead of spawning a process." (`overview.md`, "Hermes local vs gateway").
- `process` adapter (DOC `docs/adapters/process.md:30`): "1. Paperclip spawns the configured command as a child process". This **spawns**, so a "non-spawning" claim cannot rest on the name `process`.
- External adapter plugins (DOC `docs/adapters/external-adapters.md`, `overview.md` "External Adapters"): installed "from npm packages or local directories"; "External adapters work exactly like built-in adapters — they execute agents, parse output, and render transcripts". Registered by `POST` install route, UI "Settings → Adapters → Install from npm", or `adapter-plugins.json`. They run as JavaScript in the Paperclip server (they are "loaded at startup via the plugin system"); whether they are sandboxed is UNKNOWN. Whether such a plugin spawns is the plugin's own choice.
- Whether an adapter-less or "do nothing" adapter is supported so that issues and cost events can be used with no agent invocation at all: UNKNOWN. An `http` agent pointed at an Orca endpoint is the documented non-CLI shape.
- Vendored adapters: built-in adapters live in `packages/adapters/*` in the monorepo (e.g. `packages/adapters/claude-local`, `codex-local`), published as part of the Paperclip package set. Whether the npm `paperclipai` package bundles them: UNKNOWN.
- Default config and proof or test path for "disabled adapters do not spawn": none found. `server/src/routes/adapters.test.ts` and `adapter-settings-*.test.ts` exist at the pinned commit but were not read. The spike must generate the proof.

### D. Permissions and safety

| Option | Documented excerpt | Default (DOC) | Default (CODE) | Effect |
|---|---|---|---|---|
| `dangerouslySkipPermissions` (`claude_local`, also referenced for `opencode_local`) | `docs/adapters/claude-local.md:38`: "Skip permission prompts (default: `true`); required for headless runs where interactive approval is impossible" | `true` | `packages/adapters/claude-local/src/server/execute.ts:446`: `asBoolean(config.dangerouslySkipPermissions, true)`; UI default `ui/src/components/agent-config-defaults.ts:11`: `dangerouslySkipPermissions: true` | `permissions.ts:11-13`: when true, adds `--dangerously-skip-permissions`; when false, no flag (`[]`). With `targetIsSandbox`, also sets env `IS_SANDBOX=1` |
| `dangerouslyBypassApprovalsAndSandbox` (`codex_local`) | `docs/adapters/codex-local.md:28`: "Skip safety checks (dev only)" (no default stated) | UNKNOWN in the DOC | `packages/adapters/codex-local/src/index.ts:20`: `DEFAULT_CODEX_LOCAL_BYPASS_APPROVALS_AND_SANDBOX = true`; lines 38-40 resolve it to the explicit boolean if set (also legacy alias `dangerouslyBypassSandbox`), else `defaultBypass`, which is true unless an explicit `--sandbox`/`--profile`/`--full-auto`/`approval_policy` setting is in `extraArgs` or network access is off. UI form default `dangerouslyBypassSandbox: false` (`agent-config-defaults.ts:14`) but `codex-local/src/ui/build-config.ts:54-57` writes the saved value or falls back to the constant `true` | `doc/spec/agent-runs.md`: "Unsandboxed mode: add `--dangerously-bypass-approvals-and-sandbox` when enabled" |

- Required or optional: both are optional config fields ("Required: No"). Whether the adapters operate with the option set to `false` (claude: no flag, so the CLI's own approval prompts return; headless runs "where interactive approval is impossible" may stall): README and DOC are silent beyond the quoted "required for headless runs" for Claude. For Codex whether a non-bypassed run completes headlessly: UNKNOWN.
- The plan's OPEN-10 statement that both options are documented in `*_local` config is confirmed. The plan's "required or optional is unknown" is answered: optional in config, **default-on in code** for both.
- The README mentions neither option. README line 284 says "Sandbox providers extend execution beyond the local host" and line 111 lists "sandboxing, integrations & MCP servers".

### E. Cost semantics

**README-stated**

- README line 135: "Company, agent, and project budgets. Track reported spend, get threshold alerts, and pause work at configured limits."
- README line 296: "Token and cost tracking by company, agent, project, goal, issue, provider, and model. Scoped budget policies with warning thresholds and hard stops. Enforcement uses recorded spend; usage reporting and in-flight work can delay a stop."
- README line 201: "Spend tracking, budget alerts, and automatic pauses help you control the cost of ongoing work."

**DOC / CODE**

| Statement | Excerpt and source | Accounting window | Enforcement timing |
|---|---|---|---|
| Legacy budget doc | `docs/api/costs.md:64-71`: "80% Soft alert — agent should focus on critical tasks"; "100% Hard stop — agent is auto-paused"; "Budget windows reset on the first of each month (UTC)." | Calendar month, UTC | Hard stop is "auto-paused"; timing not stated |
| Board doc | `costs-and-budgets.md:113-120`: "100% Hard stop — agent is auto-paused, no more heartbeats"; "aggregated per agent per month (UTC calendar month)" | Calendar month, UTC | "no more heartbeats" after the pause; when the pause triggers is not stated |
| Code constants | `constants.ts:894`: `BUDGET_WINDOW_KINDS = ["calendar_month_utc", "lifetime"]`; `BUDGET_METRICS = ["billed_cents"]`; `BUDGET_THRESHOLD_TYPES = ["soft", "hard"]` (lines 891, 897) | `calendar_month_utc` or `lifetime` | not in constants |
| Investigation doc (dated 2026-11-03, status "Investigation complete; first admission optimization implemented locally, remaining stages proposed") | `2026-11-03-accounting-contention-and-budget-enforcement.md:94-95`: "mid-run enforcement depends on available provider reports or supported prices. Providers reporting only at completion cannot provide exact mid-call detection." Line 194: "Budget detection | Coalesced evaluation from committed evidence; a measurable delay is allowed"; "concurrent admission against a not-yet-reflected spend increase can overshoot" | n/a | **Best-effort and delayed**; overshoot possible. This is a proposal document, not a shipped contract: whether the proposed delay model is what runs at the pinned commit is UNKNOWN |

Hard stop documented as enforceable? The DOCs state that a hard stop pauses the agent; the README and the investigation doc state that enforcement is delayed and best-effort. There is **no documented guarantee that a hard stop prevents overspend**.

**Manual POST versus adapter events.** DOC example (`docs/api/costs.md:10-19`): `POST /api/companies/{companyId}/cost-events` with `agentId, provider, model, inputTokens, outputTokens, costCents`; "Typically reported automatically by adapters after each heartbeat." CODE schema (`validators/cost.ts:5-26`) accepts also `idempotencyKey`, `issueId`, `projectId`, `goalId`, `heartbeatRunId`, `billingCode`, `biller`, `billingType` (enum, default `"unknown"`), `costStatus` (enum `reported|estimated|unpriced`, default `"reported"`), `cachedInputTokens`, `providerRequestId`, `pricingProvenance`, and a **required** `occurredAt` (ISO datetime). The DOC example omits `occurredAt` and the billing fields, so the DOC example alone is not a valid request according to the schema (reading only; not executed).

- `BILLING_TYPES` (`constants.ts:839-846`): `metered_api`, `subscription_included`, `subscription_overage`, `credits`, `fixed`, `unknown`.
- Unpriced handling: `cost_events` index excludes `subscription_included` from the unpriced set (`cost_events.ts:49`); the dashboard shows "a dash instead of $0.00" for unpriced-only totals (`cost-reporting.md:33-35`).
- **Budget exposure treats subscription runs as zero.** `server/src/services/budget-exposure.ts:32`: `if (usage.billingType === "subscription_included" || usage.billingType === "subscription") return "0";`. So a subscription-billed CLI run does not consume the cents budget by this function (reading of CODE; budget semantics elsewhere not reviewed). A cents budget therefore cannot cap subscription-billed use. Token budgets: only `billed_cents` metric exists in `BUDGET_METRICS`.
- Quota visibility: UNKNOWN beyond error-driven quota waits (`claude-local.md:8-18`).

### F. Issue model

- README line 272: "Issues carry company/project/goal/parent links, atomic checkout with execution locks, first-class blocker dependencies, comments, documents, attachments, work products, labels, and inbox state."
- README line 213: "Atomic task checkout. | A single assignee and execution locks prevent competing runs from claiming the same task."
- Statuses (DOC `issues.md:341-349`): `backlog -> todo -> in_progress -> in_review -> done`, plus `blocked`; "`in_progress` requires checkout (single assignee)"; "Terminal states: `done`, `cancelled`".
- Columns of `issues` (CODE `packages/db/src/schema/issues.ts`): `companyId`, `projectId`, `goalId`, `parentId` (hierarchy), `title`, `description`, `status`, `priority` (default `medium`), `assigneeAgentId`, `assigneeUserId`, `identifier`, `issueNumber`, `originKind` (default `manual`), `originId`, `originRunId`, `originFingerprint`, `billingCode`, `executionPolicy`, `executionWorkspaceId`, etc.
- Tracker-linkage candidates: `originKind`/`originId`/`billingCode` exist, but whether they can be set through the public create/update API: `originKind` and `originId` are not in the "Updatable fields" list (`issues.md:77`); create-field list partially shown. Custom user-defined fields: **none found** in the schema or docs read. Labels are README-stated; their API was not read. Repo-level work tracking (OPEN-5): README line 463 "(Bring-your-own-ticket-system is on the Roadmap)" and README line 531 "⚪ Bring-your-own-ticket-system (Asana / Linear / Jira as on-ramps)" (not started). So external tracker linkage is a roadmap item, not a feature.
- Single-assignee behaviour: `assigneeAgentId` plus `assigneeUserId` columns; the interplay is not documented in the files read.
- Blockers: `blockedByIssueIds` accepted on update and echoed with `blockedBy` summaries (`issues.md:108-114`).

### G. Ownership, export and licence

- Licence: MIT (GitHub API; `LICENSE`; README line 582). Dual copyright lines differ (section 0).
- Data ownership statement: README line 348: "Open source. Self-hosted. No Paperclip account required." No data-ownership clause beyond that was found; a hosted option exists as a waitlist only (README line 32: "Sign up for the Paperclip Cloud waitlist"); README roadmap line 529: "🟡 Cloud deployments".
- External-service and retention dependencies: telemetry on by default (A). Optional external services: S3-compatible storage (`storage.md:21-29`), Sentry, OTLP, provider CLIs, npm registry for `npx`.
- Export mechanisms: company export (README line 325) and `db:backup` (A). Secrets: README line 313: "Secret references supply credentials to authorized runs without copying values into ordinary agent configuration." Master key at `~/.paperclip/instances/default/secrets/master.key` (`local-development.md:125`); losing it versus restoring a backup: UNKNOWN.
- `SECURITY.md`: vulnerabilities via GitHub Security Advisories. README line 18 shows a third-party "Security posture verified by Superagent" badge (a vendor-linked claim, not verified).

### H. Provider terms

- **README text on provider terms: none found.** A search of the README for "terms", "ToS", "usage policy" and "automat" found nothing relating to providers. The README only says "Bring your own agents" (line 43), "Choose models and harnesses per agent" (line 43), and lists supported harnesses (lines 61-73).
- What the README and DOC state about subscription use, without a terms statement:
  - README line 424: "Local Claude and Codex subscription sign-in also needs Python 3 and the corresponding provider CLI on the Paperclip host."
  - `claude-local.md:23-25`: prerequisites include "a Claude Code subscription login available to the execution target".
  - `codex-local.md` (credential-ownership section): "ChatGPT-subscription auth uses the subscription's flat-plan economics and quota behavior. Pick the mode deliberately for the fleet's cost and concurrency profile." and "For high-concurrency sandbox fleets, prefer a per-agent `OPENAI_API_KEY` over a shared ChatGPT-subscription login ... avoids many concurrent sandboxes sharing one rotating subscription credential." This is a technical recommendation, not a terms statement, and it shows shared-subscription fleets are an intended use.
  - `overview.md` credential section: on managed sandbox targets, `claude_local` uploads sanitized Claude settings and "the sandbox image's own `$HOME/.claude`" login, and Codex symlinks the host `~/.codex/auth.json` into a managed home and uploads it. Credentials move between hosts under Paperclip control.
- Left to each provider: everything. Nothing in the README or the DOC read grants, limits or interprets provider terms for automated, unattended, 24/7 or multi-agent subscription-CLI use (README line 89 promotes "agents running **autonomously 24/7**"). A README silence is not permission: **OPEN-6 and S44 stay open and must be answered from the providers' own terms**, not from Paperclip. `https://paperclip.ing` terms and privacy pages were not read: UNKNOWN.

## 4. README-stated behaviour versus what still needs a spike

| Behaviour | README-stated | Versioned DOC or CODE | Needs spike evidence |
|---|---|---|---|
| Loopback default, no login | line 401 | `deployment-modes.md:10-16`, env defaults | Confirm the bound address with a listener check on the chosen install |
| Disable local adapters | not stated | per-type only, existing agents unaffected (C1) | Process-launch observation with all local types disabled; the global-disable control remains UNKNOWN |
| No Paperclip-spawned CLI | not stated | adapter "spawns or calls" (overview) | Process baseline before/after (S38) |
| `dangerously*` off | not stated | both default on in CODE (D) | Config proof that both are `false` per agent, and that the CLI still runs (S46) |
| Cost event with `subscription_included` | not stated | schema accepts `billingType`; budget exposure = 0 (E) | A real POST and resulting record (S40) |
| Hard stop timing | "in-flight work can delay a stop" | investigation doc says best-effort | One warning threshold observed (S37); hard-stop timing not testable without spend |
| Approval gate enforcement | line 216 "enforced" | not read | Out of scope of this review: UNKNOWN |
| Tracker linkage fields | roadmap item only | no custom fields found (F) | Issue-field contract (S42) |

## 5. Install-location options the README supports (no choice made)

| Option | What README or versioned DOC says | Constraints and unknowns |
|---|---|---|
| Host user service | README line 441 "a single Node.js process manages an embedded Postgres and local file storage". LIVE `service.md:5`: Linux systemd **user** service, "runs as you ... nothing here needs `sudo`"; definition `~/.config/systemd/user/paperclipai.service`; data under `~/.paperclip` | Runs as the owner's user, so any spawned CLI would run with the owner's credentials and `~` unless adapters are controlled. Default loopback bind, no login (`local_trusted`). Needs Node 24.11+. Provider CLIs are looked up on the host `PATH`. Telemetry on by default |
| Workspace directory (isolated data dir) | README line 378-379: test-drive without `--data-dir` gets "a unique, retained temporary directory"; `--data-dir <path>` isolates all state (LIVE `installation.md:168`, `onboard --data-dir`, `run --data-dir`); `PAPERCLIP_HOME` / `PAPERCLIP_INSTANCE_ID` (`local-development.md:131`) | Isolates state, **not** the process user or network. The service manager is per instance id (`--instance`). Whether a service can be installed for a non-default data dir: UNKNOWN |
| Container | README line 443 and `docs/deploy/docker.md`: compose quickstart, default host port 3100, data directory `./data/docker-paperclip`; manual run passes `-e HOST=0.0.0.0` and a volume. README line 424: "The Docker image includes them" (Python 3 and provider CLIs) | Docker image includes provider CLIs, which makes local adapters available inside it. Mode and auth used by the quickstart compose file: UNKNOWN (not read). Whether a container can reach the host's nono-sandboxed OpenCode attach socket: UNKNOWN. Native runner and Rust requirement apply to source builds (README line 427) |
| Hosted | README line 32 "Sign up for the Paperclip Cloud waitlist"; roadmap line 529 "🟡 Cloud deployments" | Not generally available per the README; terms and data handling UNKNOWN. Not an option the README currently supports without the waitlist |

## 6. Unresolved decisions and questions

| # | Item | Owner | Blocking criterion |
|---|---|---|---|
| 1 | Is there a supported global control that disables every local CLI adapter (or `PAPERCLIP_ADAPTERS=[]` plus per-type `PATCH`) and does it prevent spawn for existing agents? | Owner of the spike (Tier 2), then spike evidence | S37/S38: blocks any start. Gate: observed no-child-process evidence. If only per-type, existing-agent, config-only disable exists, the plan's entry criterion is unmet |
| 2 | Can Paperclip operate (issues, assignment, cost sink) with every local adapter disabled and only an `http` or custom adapter? | Spike | S37; if not, plan section 4 records a negative verdict |
| 3 | Install location (host user service, workspace dir, container, hosted) | Owner (decision, plan section 5) | Needed before any nono profile change and before any install |
| 4 | Attach path and OPEN-11 | Owner (plan section 6) | Needed before the spike; separate from this review |
| 5 | `dangerously*` defaults are on in code: require explicit `false` on every agent created, and verify the CLI still functions headless | Owner decision plus spike | S46: no bypass is acceptable; blocks the run if the CLI cannot run with both `false` |
| 6 | Provider terms for automated subscription-CLI use (OPEN-6) | Owner, from each provider's own terms | S44: subscription automation stays blocked until resolved; README gives nothing |
| 7 | Subscription runs count as zero cents against budgets; define how the budget is enforced for subscription billing (S40) | Owner (design) | Blocks relying on Paperclip budgets as a cap |
| 8 | Is the v2026.1106.0 release the same code as the pinned commit; which version is to be adopted (pinned `install --version` versus `master`)? | Spike | Before any install |
| 9 | Approval-gate enforcement: README says enforced, spec records prompt rule | Spike (read `approvals.md`, `execution-policy.md`, test) | Before relying on an approval gate for the tier model |
| 10 | Tracker linkage fields and phase-boundary sync owner (OPEN-5, S42, S43) | Owner (decision) | No custom fields found; blocks any claim that Paperclip links repo-level work |
| 11 | Telemetry default-on and outbound traffic: set the opt-out and verify with network inspection | Owner | Before the first start on a host with network egress |
| 12 | Backup and restore commands for the chosen location, and secrets master-key handling | Spike | Before holding real data |
| 13 | Doc/code mismatches: adapter install endpoint and port in `docs/adapters/*`; cost-event doc example lacks required `occurredAt`; auth wording in `docs/api/overview.md:16` versus `authentication.md` | Spike | Use the code route and a real call, not the docs, when scripting |
| 14 | Pages not read: approvals, execution policy, OpenAPI route output, paperclip.ing terms/privacy, Docker compose | Spike | Needed for groups B, D and H completeness |

## 7. Limits of this review

- All CODE statements are readings, not execution. "Not found" means not found in the files and greps listed in section 0; code search ran over the GitHub default branch, which was the pinned commit at the time.
- LIVE pages are not pinned to the commit; the LIVE installation and update pages may describe a later or earlier CLI than `fcdceaf`.
- S36 is satisfied only to the extent that this artifact is reviewable; open items in section 6 remain before adoption.
