# Multi-tier orchestration (Tiers 1-5)

**Status:** DRAFT design spec (2026-11-04). Not normative until the owner approves it. It changes no
config, agent, or workflow file. Items marked **OPEN** need an owner decision before implementation.

**Branch:** `Enigmajazz/multi-tier-orchestration-spec`

## 1. Purpose and scope

Define who does what, in what order, and how work and information move between five tiers of
agents across several repositories, so that the owner can plan a day's work once, delegate it, and
review and apply the results in bursts.

In scope: tier roles and boundaries, the lifecycle, the artifact handoff protocol, the role of
Paperclip and Orca, the memory boundary, the Jev gate, usage monitoring, and the conflicts with the
system that already exists.

Out of scope: redesigning the staged-work chain (already decided in
`agent-sandbox-integration/docs/staging/plan.md`; this spec references it), choosing final models
for every seat, and any implementation.

## 2. Decisions already made

| ID | Decision | Source |
|---|---|---|
| D1 | Tier 4 (Codex) writes the **specification** before any OpenCode delegation. The existing Planner keeps the **plan** and the gate verdicts. | Owner, 2026-11-04 |
| D2 | One specification may cover several stages. There is **one plan per stage**. | Owner, 2026-11-04 |
| D3 | The Planner moves off Sol, so a different model writes each plan than the one that wrote the spec. | Owner, 2026-11-04 |
| D4 | Tier 3 (Antigravity) is optional. It cannot be delegated to: the owner opens the TUI and enters the prompt (subscription terms). It belongs to the owner-interaction phase (planning, review, install). | Owner, 2026-11-04 |
| D5 | Tier 2 writes no code and makes no change without an explicit owner override. | Owner, 2026-11-04 |
| D6 | Usage across all subscriptions is monitored, and the plan must be shown feasible against it. | Owner, 2026-11-04 |
| D7 | Frontier models inside OpenCode are reserved for native review. | Owner, 2026-11-04 |
| D8 | A Jev classifier checks plan-vs-spec and implementation-vs-spec per part; an LLM is used only when the classifier is uncertain. | Owner, 2026-11-04 |
| D9 | Tier 2 sits **above** the existing OpenCode setup. The PM layer exists for context management and contract following, so the OpenCode orchestrator session can stay long. | Owner, 2026-11-04 |
| D10 | The OpenCode orchestrator contract is narrowed to simple, repeated steps, focused on the initial plan and delegation. The routing guard will eventually enforce this inside OpenCode. Outside OpenCode, the frontier-model tiers rely on well-defined roles that they follow without a guard. | Owner, 2026-11-04 |
| D11 | The OpenCode refinement includes a strict **need-to-know pass** over the instructions given to each phase, so each agent receives only essential information. | Owner, 2026-11-04 |
| D12 | Codex can be delegated to by other agents. Antigravity cannot be delegated to: Tier 2 may draft the prompt, but the owner reviews it and pastes it. | Owner, 2026-11-04 |
| D13 | The Paperclip README is reviewed once it is downloaded. | Owner, 2026-11-04 |
| D14 | Task tracking is split by level. Paperclip holds the strategic, macro-level oversight. Each repo's own todo and task files hold the micro-level implementation tracking. Paperclip is a role, budget and approval layer and is not the task source of truth. | Owner, 2026-11-04 |
| D15 | The Planner model change (D3) is expanded into a **full review of OpenCode model assignments**, covering every seat, to minimise frontier-model use outside native review (D7). The Planner leaving Sol is one outcome of that review. | Owner, 2026-11-04 |
| D16 | The tiers above OpenCode (1-4) do not depend on the sandbox or on OpenCode workflow changes. They can be built independently and at the same time as the OpenCode-side work. | Owner, 2026-11-04 |

## 3. Tier contracts

| Tier | Agent | Does | Must not | Reads | Writes |
|---|---|---|---|---|---|
| 1 | Claude Code, one session | Cross-project strategy. Plans the day with the owner. Sequences multi-project work. | Write code. Hold repo-level integration detail. | Project registry, Engram strategic memory, Tier 2 summaries | Day plan, cross-repo briefs, strategic memory |
| 2 | Claude Code, one session per repo | Repo-level strategy and the initial plan (no code-level specifics). Delegates to Tiers 4-5. Prepares the Tier 3 prompt and opens its TUI for the owner. Makes the first evaluation of returned work. Uses Haiku subagents to explore. | Write code or change files without owner override (D5). Enter the Tier 3 prompt itself, which only the owner may do. | Repo via Haiku explorers, Engram, Tier 4/5 artifacts | Repo brief, delegation orders, evaluation notes |
| 2s | Claude Code tech support | Owns global dependency and system changes (the procedure in `WORKFLOW.md` "Global Tooling Changes"). Uses Haiku subagents. | Change anything outside a Tier 2 or owner request. | System state | Change records |
| 3 | Antigravity (optional) | Produces an alternative plan for Tier 2 to weigh. Tier 2 opens the TUI and drafts the prompt; the owner enters it. | Receive a prompt entered by an agent. Block the pipeline. | The brief, entered by the owner | An alternative plan, saved by the owner |
| 4 | Codex (can be delegated to by Tiers 1-2 and other agents, D12) | Writes the specification (stages, acceptance criteria). After implementation, reviews the result against the spec and flags defects. May use a `luna` explore subagent. | Write the plan or implement. | Brief, repo via luna | Spec; review verdict |
| 5 | OpenCode gentle orchestrator, one per repo | Writes a plan per stage (Planner, off Sol), delegates implementation by the existing workflow, builds stages unapplied in the sandbox. Native review (frontier models) happens here. | Apply to the host without the owner. Use frontier models outside native review (D7). | Spec, plan, repo | Plan, staged changes, evidence |

## 4. Mapping to what exists

Verified against the files (two items spot-checked, the rest reported by the explorer):

| Existing component | Tier | Relationship |
|---|---|---|
| `planner` (`openai/gpt-6.1-sol`) is the only author of plan documents and gate verdicts (`agent-sandbox-integration/docs/contracts/multi-agent-v2-workflow-prompt.md:13-23`; `WORKFLOW.md:164-172`). | 5 | Keeps plans and gates (D1). The model changes (D3). |
| `planner-evidence` (`gpt-6-luna`) | 4 | Same model family as the proposed Codex `luna` explorer. **OPEN**: reuse or keep separate. |
| PM layer: one PM per work unit (`pm-odd`, `pm-systematic`, `pm-sdd`, `pm-probe`) (`docs/specs/pm-handoff.md`) | 5 | Stays inside Tier 5: it keeps the orchestrator session long by handling context and contract following (D9). Tier 2 sits above it and does not replace it. |
| Staging chain: `BUILDING -> READY -> CHECKING -> CHECKED -> APPROVED -> APPLIED/REJECTED/STALE`, in-order apply (`agent-sandbox-integration/docs/staging/plan.md:54-91`) | 5 | This is Tier 5's unapplied flow. Referenced, not redesigned. |
| Stage-review agent in OpenCode (`staging/plan.md:159-175`) | 5 | The owner's review-then-apply step. |
| Antigravity as external advisor host, not yet in force (`WORKFLOW.md:603-640`) | 3 | The only existing Tier 3 hook. It is an advisor today, not a planner. |
| Gemini Argon advisors on paid API credit | 3 | A non-subscription substitute that never runs in addition to Antigravity. |
| "Global Tooling Changes" procedure (`WORKFLOW.md:399-435`) | 2s | A procedure, not an agent. No tech-support agent exists. |
| Magic Context (mandatory in OpenCode); Engram (not probed by default) (`WORKFLOW.md:202-211`) | all | See section 8. |
| `CLAUDE.md`: Claude Code is advisory by default and implements only on explicit request | 1, 2 | Conflicts with the manager role. See OPEN-7. |
| Codex | 4 | Not referenced anywhere in the workflow files. Greenfield. |

Lesson that applies to Tiers 1 and 2: an earlier trial ran Claude **inside** OpenCode (Q94) and was
reverted on the unmerged branch `chore/drop-claude-agent-seats` (commit `216a52d`, neither the trial
nor the revert is on `main`). The reason recorded in that commit: OpenCode replays its history into a
fresh Claude session whenever a context-hook plugin changes it, which broke the prompt cache (Opus
cache hit rate 26% over 14 calls) and burned usage. Native Claude Code sessions do not use that
mechanism, but the cost lesson is why section 10 is a hard requirement.

## 5. Lifecycle

1. **Plan the day (Tier 1 with the owner).** Choose repos and order. Cross-repo dependencies are
   written down here and nowhere else.
2. **Repo brief (Tier 2).** Tier 2 explores with Haiku subagents and writes a strategic plan
   without code-level detail. Optionally Tier 2 opens the Tier 3 TUI and drafts the prompt, the
   owner enters it, and the alternative plan comes back. Tier 2 weighs both. This phase and phases 6-7 are owner-interactive.
3. **Specification (Tier 4).** Codex writes the spec: numbered acceptance criteria, split into
   stages where needed (D2).
4. **Delegation (Tier 2 to Tier 5).** Tier 2 hands the spec and brief to the repo's gentle
   orchestrator. No further owner input is needed until phase 6.
5. **Staged implementation (Tier 5).** Per stage: a plan (Planner, D3), the Jev plan-vs-spec check,
   implementation in the sandbox, the Jev implementation-vs-spec check. Stages stay **unapplied**.
6. **Review with the owner.** The owner and a review agent step through the staged changes. Native
   review runs, ideally inside the sandbox. See OPEN-1.
7. **Apply to the host.** Only after phase 6, per the staging apply rules.
8. **Evaluation.** The result returns to Tier 2 (first evaluation), then to Tier 4 (does the final
   change meet the spec; identify flaws). Defects open a new stage or a new spec revision.
9. **Close.** Tier 2 reports to Tier 1; strategic memory is updated (section 8).

## 6. Handoff protocol

Every handoff is an **artifact with one author**, so nothing is retold by an intermediary (the
same principle as the existing author split).

| Artifact | Author | Consumer |
|---|---|---|
| Day plan | Tier 1 | Tier 2 |
| Repo brief | Tier 2 | Tiers 3, 4 |
| Alternative plan | Tier 3 (saved by the owner) | Tier 2 |
| Specification (`S1..Sn`, stages) | Tier 4 | Tier 2, Tier 5 |
| Plan per stage | Planner (Tier 5) | Tier 5, Jev, Tier 4 |
| Staged change and evidence | Tier 5 writers | Review, Tier 2, Tier 4 |
| Review verdict | Tier 4 | Tier 2, owner |

Transport is Orca (worktrees, terminals, `orca orchestration`). Known gap: a sandboxed OpenCode V2
worker has no shell, so it cannot run `orca orchestration send` or `worker_done`. Tier 2 reads the
worker with `worker-read` or `terminal wait --for tui-idle` instead of waiting for a `worker_done`.
A narrow, security-reviewed broker tool for reporting is a later option, not part of this spec.

## 7. Paperclip and Orca

**Proposed split:** Orca is the transport (worktrees, terminals, launching agents). Paperclip is the
role, ticket, budget and approval layer above it.

Verified from the Paperclip repository and docs (README itself could not be fetched; claims come from
the repository page and the docs mirror):

- Org chart with roles, reporting lines, permissions and budgets; issues with a single assignee,
  blockers and comments; heartbeats; approval gates.
- Adapters including `claude_local`, `codex_local`, `opencode_local` and `gemini_local`.
- Budgets per company, per agent and per project, with warn and hard-stop thresholds. Spend is
  reported through a cost-events API with `billingType` values including `subscription_included`.
  Local CLI runs with no known price are stored as `unpriced`, not as zero.
- Enforcement uses recorded spend, so delayed reporting delays a stop. The documented approval gate
  is a prompt rule in the agent's instructions, not an enforced control.

The README is reviewed once Paperclip is downloaded (D13); the points below stay unconfirmed until then.

Not established, and required before commitment:

- How a custom adapter is written (needed for Antigravity's paste step and the sandboxed OpenCode).
- How delegation decisions are made by a lead agent.
- Whether subscription quotas can be read at all.
- Whether driving subscription CLIs this way is permitted by each provider's terms (**OPEN-6**).
- Which fields a Paperclip issue carries and how it stays in step with the repo trackers (D14; **OPEN-5** follow-up).

Security conflict to resolve first (**OPEN-10**). The `*_local` adapters take a working directory and
appear to start the provider CLI themselves, and their config documents options named
`dangerouslySkipPermissions` and `dangerouslyBypassApprovalsAndSandbox` (whether those are required
or optional was not established). Two consequences:

- A Paperclip `opencode_local` agent would start OpenCode itself, outside the nono-sandboxed
  `secure-opencode-v2` server that the attach-client design
  (`~/.local/bin/opencode2-attach`) exists to protect. Tier 5 must be driven through the existing
  attach client, or not by Paperclip at all.
- Claude and Codex adapters run with permissions that must not be bypassed, or D5 is not enforceable
  for Tier 2.

## 8. Memory boundary

Decided by the owner: Engram is added in OpenCode to share strategic information with the other
repos that already use it, and Magic Context remains the main memory manager for OpenCode sessions.
Everything below that is a **proposal** for the owner to confirm.

| Store | Used by | Holds | Proposed rule |
|---|---|---|---|
| Engram, `global` scope | Tiers 1, 2, 2s, 4; Tier 5 orchestrator through MCP | Cross-repo strategy: decisions, spec index, stage outcomes, handoff summaries. Only this scope is visible to other repos. | Written at phase boundaries only, not per message. |
| Engram, `project` scope | Same | Repo-specific decisions and discoveries | Stays inside the repo (scoped by git remote). |
| Magic Context | Tier 5 sessions only | In-session state of the OpenCode sessions | Remains the main memory manager in OpenCode. Not mirrored into Engram. |

Constraints that already exist and stay: review and Judgment Day agents are memory-write denied
(`WORKFLOW.md:205-207`); Claude Code cannot reach Magic Context (`CLAUDE.md`). `WORKFLOW.md:204`
states Engram is not probed by default, which must change to let Tier 5 share strategy (**OPEN-4**).

Not yet checked (**OPEN-11**): whether the nono profile `opencode-v2-secure` can reach Engram's MCP
server and store at all. That profile already lacks some paths (for example `~/orca`), so the Tier 5
row depends on a probe, not on this document.

## 9. Jev gate

Two checkpoints per stage: (a) the plan against the spec, (b) the implementation against the spec.

- The spec's acceptance criteria are the unit of checking, so each must be atomic, numbered and
  testable. This is a requirement on Tier 4's output.
- Each criterion becomes one Noul (the probability that a statement is true), with the criterion and
  only the relevant plan section or diff as state. The decision logic stays in code: the TypeSafe
  guidance is that Jev supplies judgments and code decides, and it suggests 0.7 and 0.3 as starting
  thresholds for a Noul, with the band between meaning "not settled". Here that band goes to an LLM;
  above 0.7 and below 0.3 are recorded as pass and fail. Confidence alone is not the gate.
- To check: the input size limits of the Jev models (documented on the TypeSafe models page, not yet
  read). If one criterion plus a stage diff exceeds them, the diff must be chunked per criterion
  before this design holds.
- Jev output is **evidence, never approval**, consistent with the existing rule for advice.
- Proposal, not decided: thresholds are set from measured agreement on past stages, and any stage
  that names a high-risk item keeps its independent verifier regardless of the Jev result.

## 10. Usage monitoring and feasibility

Requirement D6. Today only OpenCode is metered (`~/.local/state/opencode-go-proxy/proxy.sqlite` and
`~/.local/share/opencode/opencode.db`). No meter exists for Claude Code, Codex or Antigravity, and
the ChatGPT-plan usage of the Sol and Luna seats is unmeasured. The OpenCode Go pool was reported 99%
used until 9 November in the model-allocation review dated 2026-10-28 (a week-old figure, to be
re-measured).

| Subscription | Tiers | Metered today | Needed |
|---|---|---|---|
| Claude (Code) | 1, 2, 2s | No | Per-session usage and the plan limit window |
| OpenAI (Codex, ChatGPT plan) | 4, and the Planner/luna seats today | No | Same, split by tier |
| Google (Antigravity) | 3 | No (manual by design) | Owner-reported count per use |
| OpenCode Go pool and proxy | 5 | Yes | Keep; attribute by repo and stage |

Required outputs: a usage ledger per tier per day, a per-subscription feasibility estimate for one
representative day, and thresholds that make Tier 2 downgrade a model or skip optional Tier 3
before a limit is reached. Paperclip's cost-events API is a candidate sink but does not read
subscription quotas itself.

No numeric budget is set here; it must come from a measured baseline.

## 11. Open decisions and conflicts

| ID | Question |
|---|---|
| OPEN-1 | The staging plan prefers review before apply and accepts native review after apply as a fallback. The owner wants native review in the sandbox before apply. Is in-sandbox native review feasible, or is the fallback the reality? |
| OPEN-2 | **Resolved (D9):** Tier 2 sits above the existing OpenCode setup; the PM layer stays for context management and contract following. Remaining work: narrow the orchestrator contract to simple repeated steps (D10), and run the need-to-know pass over each phase's instructions (D11). |
| OPEN-3 | Tier 2s has no agent today. Define it as a role over the "Global Tooling Changes" procedure. |
| OPEN-4 | Allow Engram for Tier 5 and amend `WORKFLOW.md:204`. |
| OPEN-5 | **Resolved (D14):** Paperclip = macro oversight; repo todo and tasks (`docs/TODO.md`, `odd/tasks/`, staging) = micro implementation tracking. Remaining work: define which fields Paperclip issues carry and who keeps them in step with the repo trackers. |
| OPEN-6 | Terms-of-service review for automated driving of Claude, Codex and Gemini subscription CLIs. |
| OPEN-7 | **Resolved (owner, 2026-11-04):** Tiers 1 and 2 are the new intended role of Claude Code and overwrite the advisory-only rule. Remaining work: rewrite the `CLAUDE.md` "Claude Code's role here" section when the spec is approved. |
| OPEN-8 | Full OpenCode model assignment review (D15), replacing the single Planner decision. Inputs: `docs/brainstorms/model-allocation-review-2026-10-28.md`, the usage baseline (section 10), vendor-independence rules, and D7. |
| OPEN-9 | Tier 1 must not hold repo integration detail yet must know the repo set. Define the minimal project registry it reads. |
| OPEN-10 | Paperclip's local adapters start the provider CLI themselves. Paperclip must drive Tier 5 through the existing sandbox attach client, or not at all, and must not run Claude or Codex with permissions bypassed (section 7). |
| OPEN-11 | Can the `opencode-v2-secure` nono profile reach Engram's MCP server and store? Section 8's Tier 5 row depends on it. |
| OPEN-12 | **Resolved (D12):** Tier 2 writes the Antigravity prompt for owner review; the owner pastes it. Still worth checking against the Antigravity subscription terms (OPEN-6). |
| OPEN-13 | Where do the Tier 1, 2, 2s and 4 role definitions live? Tiers 1-4 have no guard, so they need a written, versioned home. |
| OPEN-14 | Which repo owns the usage ledger (section 10)? |

## 12. Proving the design before building

1. A Paperclip spike: first test OPEN-10 (can Paperclip drive Tier 5 through the sandbox attach
   client, and run Claude and Codex without bypassing permissions). Only then one company with
   adapters for Claude Code, Codex and OpenCode and one real task across two repos. Confirms or kills
   sections 7 and 10.
2. An Engram reachability probe from the `opencode-v2-secure` profile (OPEN-11).
3. A one-day usage baseline per subscription, to turn section 10 into numbers.
4. One end-to-end stage using the existing staging chain, with Codex writing the spec and the Planner
   on a new model, to prove the handoff artifacts in section 6.
5. A Jev calibration run on past stages, to set the section 9 thresholds.
6. The OpenCode workflow refinement (D10, D11): narrow the orchestrator contract to simple repeated
   steps, then a need-to-know pass over the instructions each phase receives. The routing guard
   enforces the result inside OpenCode later; Tiers 1-4 get written role definitions instead, since
   no guard covers them.
7. The full OpenCode model assignment review (D15, OPEN-8), started from the 2026-10-28
   model-allocation review and re-run against the measured usage baseline.

## 13. Affected repositories

Two repositories change. Each has its own `docs/TODO.md`, routed commits and review, so every work
unit is assigned to exactly one repo.

| Repo | Remote | Role in this design |
|---|---|---|
| `workflow_optimisation` | `EnigmaJazz/workflow_optimisation` | Routing recipe, canonical OpenCode config, plugins, guard and verifier. Holds this spec. |
| `agent-sandbox-integration` | `EnigmaJazz/Sandbox-Agents` | Sandbox stack: broker, nono profiles, host tools, staging chain, Planner contract. |

### Owner of each change

| Change | Repo |
|---|---|
| This spec; Tier 1, 2, 2s and 4 role definitions (home to be chosen, **OPEN-13**) | `workflow_optimisation` |
| `CLAUDE.md` role rewrite (OPEN-7); remove the advisory-only rule | `workflow_optimisation` (also check the `CLAUDE.md` in the other repo) |
| Narrowing the orchestrator contract; need-to-know pass; guard enforcement (D10, D11) | `workflow_optimisation` (`WORKFLOW.md`, `global-config/skills`, routing guard) |
| Full OpenCode model assignment review, including the Planner off Sol (D3, D15, OPEN-8) | `workflow_optimisation` (`global-config/opencode.json`, `systematic.jsonc`, `rate-limit-fallback.json`) |
| `WORKFLOW.md:204` Engram amendment (OPEN-4) | `workflow_optimisation` |
| Planner author-split contract and plan-per-stage handling | `agent-sandbox-integration` (`docs/contracts/multi-agent-v2-workflow-prompt.md`), then the matching `WORKFLOW.md` text |
| Staging chain, review-before-apply, in-sandbox native review (OPEN-1) | `agent-sandbox-integration` (`docs/staging/plan.md`, broker, host tools) |
| nono profile: Engram reachability, Paperclip attach path (OPEN-10, OPEN-11) | `agent-sandbox-integration` (`nono/profile`) |
| Usage ledger (section 10) | Undecided (**OPEN-14**); the OpenCode proxy data lives outside both repos |

### Landing order

Two independent tracks that can be built at the same time (D16):

- **Track A, above OpenCode (Tiers 1-4):** role definitions, Paperclip and Orca setup, the Codex
  spec role, the Tier 3 prompt flow and the usage ledger. None of it depends on the sandbox or on
  OpenCode workflow changes. This spec lands with it.
- **Track B, OpenCode side:** (1) `agent-sandbox-integration` first: anything the OpenCode side
  depends on, namely the profile changes, the Planner contract and the staging and review behaviour.
  (2) `workflow_optimisation` second: the workflow text, the model assignment review outcome, config,
  guard and `CLAUDE.md` changes that assume step 1 is in place. The verifier mirrors config to the
  live directory, so these take effect only after a verifier run and an owner restart.

The tracks meet at one point: Tier 2 delegates to Tier 5. Until Track B is ready, Tier 2 can
delegate to the OpenCode setup as it stands today.

`docs/advisor/` is a contract shared by both repos and is never synced over; changes to it are made
in one repo and carried to the other deliberately.

### Working-tree note

When this spec was written, `agent-sandbox-integration` was on branch `refactor/p0-shared-tool-table`
with uncommitted edits under `broker/src/`. Implementation there must start from a clean branch or a
fresh worktree (a sibling under the user's home, with its own CodeGraph index), never on top of that
work.
