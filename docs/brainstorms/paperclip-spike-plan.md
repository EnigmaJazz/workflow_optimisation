# Paperclip spike plan

Status: **Pre-download planning; owner decisions required. No Paperclip facts verified against its README.**

This is a download-free plan for Q119. It authorizes no download, install, service, launch, or nono-profile change. Date: 2026-11-08.

Sources read: `docs/specs/multi-tier-orchestration.md` (D1-D37, §§7-8, 10-13); `docs/specs/multi-tier-orchestration-criteria.md` (S1-S11, S36-S59); `docs/TODO.md` (Q101, Q119-Q120, Q102 and nono-probe context); `roles/README.md`; `odd/tasks/multi-tier-orchestration.md` (T1/T4 and L4-L5); `docs/brainstorms/model-allocation-review-2026-10-28.md` (house style).

## 1. Scope and evidence labels

- **Observed in this repository:** Q119 is planned; T4 is pending a Paperclip download, README review (S36), and terms check (S44). Q119 requires owner decisions on install location and attach path before any nono change. T1's ledger is built; S9 still needs a measured day and thresholds remain placeholders.
- **Spec-recorded, unconfirmed until the README review:** all Paperclip product and integration statements below are records in the multi-tier spec, not independent findings.
- The future README review and spike are separate gates. The README review is not permission to install or enable an adapter.

## 2. What the spec records about Paperclip

**Spec-recorded, unconfirmed until the README review:** Paperclip is proposed as the role, ticket, budget, and approval layer, with Orca as transport and launcher. The spec records an org chart with roles, reporting lines, permissions, and budgets; issues with a single assignee, blockers, and comments; heartbeats; and approval gates.

It records local adapters named `claude_local`, `codex_local`, `opencode_local`, and `gemini_local`. Budgets are described per company, agent, and project, with warn and hard-stop thresholds. Cost is reported through a cost-events API; recorded `billingType` values include `subscription_included`. Local CLI runs without a known price are marked `unpriced`, not zero. Enforcement uses recorded spend, so delayed reporting delays a stop. The documented approval gate is a prompt rule in agent instructions, not an enforced control.

**Not established in the spec record; README review required:**

| Open point | Question to resolve |
|---|---|
| Custom adapters | How is one authored and registered, including a non-spawning adapter? |
| Lead delegation | How does a lead agent decide to delegate work? |
| Quotas | Can subscription quotas be read at all? |
| OPEN-6 terms | Do provider terms permit the proposed automated subscription-CLI use? |
| OPEN-5 issue model | Which issue fields exist, and how can they track repo-level work? |

**OPEN-10 security conflict (spec-recorded, unconfirmed until the README review):** `*_local` adapters accept a working directory and appear to start the provider CLI themselves. Their configuration documents `dangerouslySkipPermissions` and `dangerouslyBypassApprovalsAndSandbox`; whether either is required or optional is unknown. A Paperclip `opencode_local` agent would start OpenCode outside the nono-sandboxed `secure-opencode-v2` server protected by `~/.local/bin/opencode2-attach`. This conflicts with D21: Orca alone launches agents; Paperclip never starts a CLI. The spike must retain provider permission checks; no bypass is acceptable.

## 3. README review checklist (D13, S36)

Before adoption, read the downloaded README and linked documentation; capture exact excerpts, URL/path, version or commit, and unresolved questions in a review artifact. Do not infer undocumented behavior.

| Group | Question and evidence to capture |
|---|---|
| A. Deployment/runtime | Install method and dependencies; service model and ports; storage/DB; config paths; upgrade/migration and backup; authentication; whether UI and REST API are separable. Capture the documented commands, defaults, and operational constraints. |
| B. REST API | Auth scheme; issue creation, assignment and status, comments and blockers; cost-events schema and `billingType`; budgets and thresholds; heartbeats and approval gates; webhooks; pagination/idempotency; OpenAPI spec. Capture endpoint, method, required fields, response/error, and source for each used operation. |
| C. Adapter control | Exact config key/flag that disables every local CLI adapter globally; evidence that disabling prevents process spawn; whether a custom non-spawning adapter/webhook can be registered; whether adapters are vendored. Capture default config and proof/test path, not an assumption. |
| D. Permissions/safety | Defaults and effects of both `dangerously*` options; whether they can be removed while retaining operation. Capture config schema, defaults, and documented effect. |
| E. Cost semantics | Manual POST versus adapter-generated events; handling of `subscription_included` and unpriced events; quota visibility; enforcement timing. Capture schema/examples and caveats. |
| F. Issue model | Fields, hierarchy, statuses, custom fields, and single-assignee behavior. Capture schema and constraints relevant to tracker linkage. |
| G. Ownership/export/licence | Data ownership, export/backup mechanisms, and licence. Capture terms and any external-service or data-retention dependency. |
| H. Provider terms | What the README says about provider terms, with citations; what it leaves to each provider and therefore OPEN-6 review. A README silence is not permission. |

**README review artifact minimum:** product version/commit; source URL and retrieval date; reviewed README sections and linked documents; exact excerpts with locations; confirmed behaviors versus unknowns; answers to groups A-H; and a list of unresolved decisions with owner and blocking criterion. Separate README-stated behavior from behavior that still needs a spike. S36 is complete only when the artifact is reviewable before adoption.

Do not convert examples into defaults without checking the versioned configuration reference. For every “disable” statement, record whether it disables configuration, prevents process creation, and is global across all local adapters; these are distinct claims. For every budget statement, capture the accounting window and whether a warning or hard stop is documented as enforceable.

## 4. REST/UI-only spike: proof and stop conditions

**Entry criteria:** owner has selected an install location and attach path; README review (S36) is complete; the exact global adapter-disable control and process-spawn behavior are established; terms review defines permitted operations (S44); the owner approves a low-risk real task and two repositories. If any criterion is unmet, do not start.

**Setup:** disable all local CLI adapters before starting Paperclip and retain the config/evidence. Start only after confirming the disablement. Mirror the tier roles in the company/org chart. Create two projects for `workflow_optimisation` and `agent-sandbox-integration`. Paperclip records macro ticket/cost state; each repository tracker remains the micro-level source of truth. Orca launches every agent; no Paperclip-spawned process is permitted.

Run one real, low-risk task spanning the two repositories. Use the approved Orca path for every agent. Keep the task bounded and read-only on repos if possible; do not weaken permissions to make the experiment pass.

**Capture:** complete task lifecycle through REST API and UI (request/response evidence and screenshots or transcript); process-launch evidence showing no Paperclip-spawned process; disabled-adapter config; ticket and assignment; cost-event request and resulting record; one budget-threshold warning; and checks that provider permission/approval controls remain intact. Redact secrets and message content.

For each evidence item, record a stable evidence ID, timestamp, task/repo reference, source (UI/API/process observation), criterion, and observed outcome. Preserve requests and responses with credentials redacted. Distinguish a configuration claim from runtime evidence: disabled config alone does not establish that no process was spawned. Record missing evidence as missing, not as a pass.

The verdict should state which criteria pass, fail, or remain blocked; name the evidence IDs; note any deviation from the entry conditions; and say whether sections 7 and 10 remain viable. A failed gate is a useful result and must not be repaired by weakening permissions during the same run.

| Criterion | Spike evidence |
|---|---|
| S36 | README review artifact completed before adoption. |
| S37 | API/UI-only task lifecycle with local adapters disabled and no CLI launch. |
| S38 | Orca launch-ownership contract plus process-launch evidence. |
| S39 | Ticket assignment artifact showing the responsible assignee. |
| S40 | Cost-event request and resulting cost record, including billing type. |
| S41 | Tracking contract: repo todo/task files own micro work; Paperclip is macro oversight. |
| S42 | Issue-field contract identifying repo/tracker linkage fields. |
| S43 | Tracking-ownership contract naming the phase-boundary sync owner. |
| S44 | Separate terms-review artifact; subscription automation stays blocked until resolved. |
| S45 | Orca transport evidence showing use of the existing sandbox attach client. |
| S46 | Permission-check evidence showing no bypass configuration and preserved checks. |

**Explicit S38/S45/S46 gate:** an API/UI demonstration alone does not prove launcher ownership, secure attach transport, or preserved permission checks. Capture each independently. If Paperclip cannot operate without a local adapter, or cannot emit cost events without one, the spec's proposed split or Paperclip-as-cost-sink is dead; record a negative verdict rather than enabling an adapter. Stop and escalate if success requires enabling any adapter, bypassing permissions, or widening the nono profile.

**Run order:**

1. Verify the owner-approved deployment boundary and the disabled-adapter configuration before service start.
2. Confirm service reachability only through the selected UI/API path; inspect the runtime process boundary before assigning work.
3. Create the two project records and the single bounded task; record baseline process state.
4. Use Orca for every agent launch; observe and capture each launch path and permission prompt/result.
5. Complete ticket and cost-event operations through API/UI; observe the warning threshold without changing thresholds mid-run.
6. Compare before/after process evidence, configuration, ticket state, cost record, and permission evidence; write the verdict.

This order isolates setup from execution. Any unexpected child process, missing event, or permission change pauses the run; preserve evidence and report blocked/failed instead of retrying through an adapter.

## 5. Install location: owner decision

| Candidate | Tradeoff to assess; not a recommendation |
|---|---|
| (a) Host user service | Data under `~/.local/share/paperclip`; unit under `~/.config/systemd/user`. Convenient host service lifecycle; requires careful user-service and filesystem isolation. |
| (b) Workspace directory | `~/ai-workspace/paperclip` with a user unit. Keeps app state visible alongside workspace; must not become a repo or inherit repo write access. |
| (c) Container/Compose | Compose project under `~/ai-workspace/paperclip`. May isolate runtime dependencies; introduces image, volume, and upgrade/backup decisions. |
| (d) Hosted/remote | Consider only if the project documents such a deployment. Adds remote access, data custody, authentication, and network trust questions. |

Every viable option must meet each constraint below. These are acceptance conditions, not claims about any Paperclip deployment mode.

| Constraint | Required evidence before approval |
|---|---|
| Data location | Confirm database, logs, uploads, and backups all remain outside every repo working tree. |
| Repository access | Verify runtime identity cannot write to either repository; do not rely only on UI permissions. |
| CLI isolation | Verify no provider credentials are available and provider CLI binaries are absent from runtime `PATH`; confirm no local adapter can spawn them. |
| Network | Verify the service binds localhost only; document how the UI/API is accessed. |
| Operations | Document backup/restore and upgrade/migration steps, including the owner of each. |
| Profile boundary | No nono change before the attach path is decided and separately approved. |

The README determines which options are real. No default is chosen here. If a candidate cannot demonstrate any row, reject it before install rather than treating the requirement as a post-install hardening task.

## 6. Attach path and OPEN-11 are separate decisions

**Driving Tier 5 (D21):** Paperclip never launches Tier 5. Orca launches with `--agent opencode2`; the approved client path is `~/.local/bin/opencode2-attach`. If Paperclip needs Tier 5 state, it consumes state Orca/the broker already publishes, or a host-side bridge calls Paperclip's REST API. Paperclip must never attach to the secure server or launch a CLI.

**OPEN-11:** whether the `opencode-v2-secure` nono profile can reach Engram's MCP server and store read-only is an Engram/profile probe, not a Paperclip requirement. It is listed here only because both topics can result in changes to `agent-sandbox-integration/nono/profile`. The design needing no profile change is: the owner's browser is outside the sandbox and Orca is host-side, so UI and REST calls need no grant. Only an agent inside the sandbox calling Paperclip's API would need a localhost network allow, not a filesystem grant. Nono profiles are owner-installed; any change is a separate owner decision.

For the OPEN-11 probe, record the profile name, MCP endpoint, read attempt, denial paths reported by `nono why --profile opencode-v2-secure`, and observed result. Do not change the profile as part of this planning artifact or Paperclip spike.

## 7. Issue fields and tracker ownership (D14, OPEN-5, S42-S43)

Proposed minimum fields, to validate against the README/API: external id (`repo` + Q/S reference), repo, tracker path, owner tier, macro state, assignee role, budget reference, links (commit/PR/spec), and last-synced timestamp.

**Authority:** the repository tracker is the source of truth; Paperclip holds macro state only. Proposal: one-way repo → Paperclip sync at phase boundaries, owned by Tier 2 (consistent with D23). Owner/Tier 1 owns budget and approval fields. Tier 5 never writes Paperclip. Keep synchronization manual during the spike so the evidence isolates the API/UI behavior and the authority boundary stays clear.

## 8. Owner questions

1. Which install-location option is acceptable? Blocks any download or runtime setup.
2. Which Tier 5 attach/state path is approved? Blocks adapter configuration and any profile discussion.
3. What is the permitted scope of the low-risk, two-repo task? Blocks spike execution.
4. Who completes and signs the OPEN-6 provider terms review? Blocks any subscription automation.
5. Is a documented hosted instance acceptable, or must this be local? Blocks deployment selection if the README supports both.
6. Who owns the issue-field and phase-boundary sync contract? Blocks S42-S43 closure.
7. What evidence is sufficient to prove no process spawn and preserved permissions? Blocks a defensible S37-S38/S45-S46 verdict.
8. Is any agent-in-sandbox REST access actually required? If yes, blocks the spike until a separate owner decision on a localhost network grant.

## 9. Next steps and deliverables

1. Owner answers install-location and attach-path questions; separately defines terms-review ownership and spike scope.
2. Download only after authorization; preserve version/source metadata and review the README before adoption.
3. Produce the README review artifact for S36, including uncertainties and evidence references.
4. Run the gated REST/UI-only spike and produce a pass/fail evidence artifact for S37-S46.
5. Record a verdict on spec sections 7 and 10; revise the proposal or mark it dead if the kill criteria are met.

The final spike packet contains the README review, owner decisions, deployment/config evidence, task timeline, redacted API/UI and process evidence, S36-S46 matrix, deviations, and a signed pass/fail/blocked verdict. It does not include credentials, provider tokens, or a nono-profile patch.

A spike pass validates only the tested version, deployment, configuration, task flow, and permissions; it does not establish provider-term compliance or quota visibility.
