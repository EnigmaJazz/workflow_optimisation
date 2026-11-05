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
| D17 | A Jev comparison of the Antigravity plan and the Tier 2 plan decides whether they differ materially, before Tier 2 has to read the Antigravity plan. | Owner, 2026-11-05 |
| D18 | Claude Code sessions (Tiers 1 and 2) use the advisor to review the final plan before delegation and to judge between competing plans. | Owner, 2026-11-05 |
| D19 | Every stage follows minimality principles (YAGNI and DRY), applied differently per role (section 14). | Owner, 2026-11-05 |
| D20 | For this change, the Antigravity then Codex steps are run manually with copy-and-paste prompts, as a large architectural change that gets full due diligence. | Owner, 2026-11-05 |
| D21 | Orca is the only launcher. Paperclip assigns work through tickets and records cost, but never starts a CLI. | Owner, 2026-11-05 |
| D22 | Gate verdicts: when Jev shows a clear match to the spec, code records the verdict. On a clear fail the work goes back to the Planner to refine. When Jev is unsure it goes to an independent spec-check agent. | Owner, 2026-11-05 |
| D23 | Tier 5 uses Engram read-only. Tier 2 owns all Engram writes. Magic Context stays the in-session memory. | Owner, 2026-11-05 |
| D24 | Staging build scope: P0-P2, a reduced P4 (reject, STALE, re-run from the tip, no merge-tree replay), P6 kept, P5 only if unattended multi-stage work needs it, P3 deferred. | Owner, 2026-11-05 |
| D25 | The usage ledger lives in `workflow_optimisation`. | Owner, 2026-11-05 |
| D26 | The Tier 1, 2, 2s and 4 role definitions live in a `roles/` directory in `workflow_optimisation`, one versioned file per tier. | Owner, 2026-11-05 |
| D27 | The independent spec-check agent (D22) is the existing `advisor-spec-pre` and `advisor-spec-post` seats. Their models are set by the full OpenCode model assignment review (D15), with the family differing from the Planner and the writers. | Owner, 2026-11-05 |

## 3. Tier contracts

| Tier | Agent | Does | Must not | Reads | Writes |
|---|---|---|---|---|---|
| 1 | Claude Code, one session | Cross-project strategy. Plans the day with the owner. Sequences multi-project work. Uses the advisor on the final plan before delegation (D18). | Write code. Hold repo-level integration detail. | Project registry, Engram day plan inputs for Tier 2 to record as strategic memory, Tier 2 summaries | Day plan, cross-repo briefs, day plan inputs for Tier 2 to record as strategic memory |
| 2 | Claude Code, one session per repo | Repo-level strategy and the initial plan (no code-level specifics). Delegates to Tiers 4-5. Prepares the Tier 3 prompt and opens its TUI for the owner. Uses the advisor to review the final plan before delegating and to judge between competing plans (D18). Makes the first evaluation of returned work. Uses Haiku subagents to explore. | Write code or change files without owner override (D5). Enter the Tier 3 prompt itself, which only the owner may do. | Repo via Haiku explorers, Engram, Tier 4/5 artifacts | Repo brief, delegation orders, evaluation notes |
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
   without code-level detail. Optionally Tier 2 writes the Tier 3 prompt to a file and opens the Tier 3 TUI with the existing
   Orca commands (no new Orca command), the owner reviews and pastes it, and the alternative plan comes back. A Jev comparison (section 9)
   decides whether the two plans differ materially; Tier 2 reads the Antigravity plan only if they
   do (D17), and the advisor then judges between them (D18). This phase and phases 6-7 are owner-interactive.
3. **Specification (Tier 4).** Codex writes the spec: numbered acceptance criteria, split into
   stages where needed (D2).
4. **Delegation (Tier 2 to Tier 5).** The advisor reviews the final plan first (D18). Tier 2 then hands the spec and brief to the repo's gentle
   orchestrator. No further owner input is needed until phase 6.
5. **Staged implementation (Tier 5).** Per stage: a plan (Planner, D3), the Jev plan-vs-spec check,
   implementation in the sandbox, the Jev implementation-vs-spec check. Stages stay **unapplied**.
6. **Review with the owner.** The owner and a review agent step through the staged changes. Native
   review runs, ideally inside the sandbox. See OPEN-1.
7. **Apply to the host.** Only after phase 6, per the staging apply rules.
8. **Evaluation.** The result returns to Tier 2 (first evaluation), then to Tier 4 (does the final
   change meet the spec; identify flaws), as a structured `PASS` or `FLAWS_FOUND` verdict. Defects open a new stage or a new spec revision.
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

Security conflict (**OPEN-10**, resolved by D21: Orca is the only launcher and Paperclip never starts a CLI). The `*_local` adapters take a working directory and
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
| Engram, `global` scope | Writes: Tier 2 only; Tiers 1, 2s and 4 hand findings to Tier 2 (D23). Reads: also Tier 5, read-only | Cross-repo strategy: decisions, spec index, stage outcomes, handoff summaries. Only this scope is visible to other repos. | Written at phase boundaries only, not per message. Tier 5 has no `mem_save`. |
| Engram, `project` scope | Writes: Tier 2 only; Tiers 1, 2s and 4 hand findings to Tier 2 (D23). Reads: also Tier 5, read-only | Repo-specific decisions and discoveries | Stays inside the repo (scoped by git remote). |
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
- Code runs the deterministic checks first (touched paths match the spec, tests exit 0, diff within
  the line budget; the existing broker and guard already gate on path scope and line budgets). Jev
  only sees what code cannot decide.
- Each criterion becomes one Noul (the probability that a statement is true), with the criterion and
  only the relevant plan section or diff as state. The decision logic stays in code: the TypeSafe
  guidance is that Jev supplies judgments and code decides, and it suggests 0.7 and 0.3 as starting
  thresholds for a Noul, with the band between meaning "not settled". Here that band goes to an LLM;
  above 0.7 and below 0.3 are recorded as pass and fail. Confidence alone is not the gate.
- Jev limits (TypeSafe models page, `jev-1.13` and `jev-1.14`, fetched 2026-11-05): 64k tokens per
  request and 32k tokens per question by default. The state plus any one question must fit 32k tokens,
  and the state plus all questions must fit 64k. A long-context header raises both to 262k, but the
  page says it is slower and less accurate, so it is not used by default. No question count, byte size
  or image token cost is stated. Rate limits are per organization and the figures are only in the
  developer console. Consequence: code checks the token size of each criterion's state (criterion plus
  plan section or diff) before the call. A payload over 32k tokens is chunked per criterion or, if it
  cannot be chunked, treated as unsure and routed under D22.
- Gate routing (D22), decided in code from the Jev result and the deterministic checks:

  | Result | Action |
  |---|---|
  | Clear match to the spec | Code records the gate verdict. |
  | Clear fail | Back to the Planner to refine. |
  | Unsure | An independent spec-check agent decides (OPEN-19). |

- Outside the gate, Jev output is **evidence, never approval**: advisor output keeps that rule. The
  D22 gate verdict is the one place where code acts on Jev directly, and it changes who may author
  `host_gate_verdict` (OPEN-16).
- Proposal, not decided: thresholds are set from measured agreement on past stages, and any stage
  that names a high-risk item keeps its independent verifier regardless of the Jev result.

### Plan comparison (D17)

Used when Tier 3 returns an alternative plan. Code sends both plans as state and asks one Noul per
aspect, each a single judgment: do the plans (1) split the work into different stages or a different
order, (2) touch different components or repos, (3) carry different risk items, (4) differ in scope,
with one including work the other omits, (5) disagree on a design decision. Code, not Jev, decides:

- every Noul below 0.3: no material difference, so Tier 2 need not read the Antigravity plan;
- any Noul at 0.3 or above, including the unsettled band: Tier 2 reads it.

The bias is deliberate, because the error to avoid is missing a better plan. Jev answers "does it
differ", never "which is better"; judging between plans is the advisor's job (D18). Both plans are
sent to the TypeSafe API, which needs the owner's `TYPESAFE_API_KEY` and the owner's consent for that
data. The input size limits above apply here too.

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

Advisor calls (D18) draw on Claude usage and Jev calls (D17, section 9) are metered by TypeSafe; both
belong in the ledger.

No numeric budget is set here; it must come from a measured baseline.

## 11. Open decisions and conflicts

| ID | Question |
|---|---|
| OPEN-1 | The staging plan prefers review before apply and accepts native review after apply as a fallback. The owner wants native review in the sandbox before apply. Is in-sandbox native review feasible, or is the fallback the reality? |
| OPEN-2 | **Resolved (D9):** Tier 2 sits above the existing OpenCode setup; the PM layer stays for context management and contract following. Remaining work: narrow the orchestrator contract to simple repeated steps (D10), and run the need-to-know pass over each phase's instructions (D11). |
| OPEN-3 | Tier 2s has no agent today. Define it as a role over the "Global Tooling Changes" procedure. |
| OPEN-4 | Allow read-only Engram (search and read, no `mem_save`) in OpenCode and amend `WORKFLOW.md:204` and the matching write ban (D23). |
| OPEN-5 | **Resolved (D14):** Paperclip = macro oversight; repo todo and tasks (`docs/TODO.md`, `odd/tasks/`, staging) = micro implementation tracking. Remaining work: define which fields Paperclip issues carry and who keeps them in step with the repo trackers. |
| OPEN-6 | Terms-of-service review for automated driving of Claude, Codex and Gemini subscription CLIs. |
| OPEN-7 | **Resolved (owner, 2026-11-04):** Tiers 1 and 2 are the new intended role of Claude Code and overwrite the advisory-only rule. Remaining work: rewrite the `CLAUDE.md` "Claude Code's role here" section when the spec is approved. |
| OPEN-8 | Full OpenCode model assignment review (D15), replacing the single Planner decision. Inputs: `docs/brainstorms/model-allocation-review-2026-10-28.md`, the usage baseline (section 10), vendor-independence rules, and D7. |
| OPEN-9 | Tier 1 must not hold repo integration detail yet must know the repo set. Define the minimal project registry it reads. |
| OPEN-10 | **Resolved as a decision (D21).** Remaining check: Paperclip must be usable through its REST API and UI alone, with its local CLI adapters disabled. Test this first in the spike. |
| OPEN-11 | Can the `opencode-v2-secure` nono profile reach Engram's MCP server and store for **reads**? Section 8's Tier 5 row depends on it. |
| OPEN-12 | **Resolved (D12):** Tier 2 writes the Antigravity prompt for owner review; the owner pastes it. Still worth checking against the Antigravity subscription terms (OPEN-6). |
| OPEN-13 | **Resolved (D26):** `roles/` in `workflow_optimisation`, one versioned file per tier. |
| OPEN-14 | **Resolved (D25):** the usage ledger lives in `workflow_optimisation`. |
| OPEN-15 | **Resolved (D21).** |
| OPEN-16 | **Resolved (D22).** Remaining: it changes who may author `host_gate_verdict`, a contract others consume (high-risk item 3, in `agent-sandbox-integration`), so it needs its own commit and an independent verifier. See OPEN-19. |
| OPEN-17 | **Resolved (D23).** |
| OPEN-18 | **Resolved (D24).** It changes the plan decided on 2026-10-12, so `agent-sandbox-integration/docs/staging/plan.md` needs a matching note. |
| OPEN-19 | **Resolved (D27).** |

## 12. Proving the design before building

1. A Paperclip spike through its REST API and UI only, with its local CLI adapters disabled (D21,
   OPEN-10): record cost-events and tickets for one real task across two repos, with Orca launching
   every agent. Confirms or kills sections 7 and 10.
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
8. Due diligence for this change (D20): the Tier 2 plan (this spec), a manual Antigravity run with an
   owner-pasted prompt, the comparison, the advisor's judgment between plans, then a manual Codex run
   for the specification.

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
| This spec; Tier 1, 2, 2s and 4 role definitions (`roles/`, D26) | `workflow_optimisation` |
| `CLAUDE.md` role rewrite (OPEN-7); remove the advisory-only rule | `workflow_optimisation` (also check the `CLAUDE.md` in the other repo) |
| Narrowing the orchestrator contract; need-to-know pass; guard enforcement (D10, D11) | `workflow_optimisation` (`WORKFLOW.md`, `global-config/skills`, routing guard) |
| Full OpenCode model assignment review, including the Planner off Sol (D3, D15, OPEN-8) | `workflow_optimisation` (`global-config/opencode.json`, `systematic.jsonc`, `rate-limit-fallback.json`) |
| `WORKFLOW.md:204` Engram amendment (OPEN-4) | `workflow_optimisation` |
| Planner author-split contract and plan-per-stage handling; the D22 change to who authors `host_gate_verdict` (high-risk item 3, own commit and independent verifier) | `agent-sandbox-integration` (`docs/contracts/multi-agent-v2-workflow-prompt.md`, broker), then the matching `WORKFLOW.md` text |
| Staging chain at the D24 scope, review-before-apply, in-sandbox native review (OPEN-1) | `agent-sandbox-integration` (`docs/staging/plan.md`, broker, host tools) |
| nono profile: Engram reachability, Paperclip attach path (OPEN-10, OPEN-11) | `agent-sandbox-integration` (`nono/profile`) |
| Usage ledger (section 10, D25) | `workflow_optimisation` |

### Landing order

Two independent tracks that can be built at the same time (D16):

- **Track A, above OpenCode (Tiers 1-4):** usage metering first (D6 makes feasibility a gate), then role definitions, Paperclip and Orca setup, the Codex
  spec role, the Tier 3 prompt flow and the usage ledger. None of it depends on the sandbox or on
  OpenCode workflow changes. This spec lands with it.
- **Track B, OpenCode side:** the P0 native-review spike first, because the staging plan already requires it (OPEN-1). Then (1) `agent-sandbox-integration` first: anything the OpenCode side
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

## 14. Minimality principles (D19)

The owner's base prompt, kept verbatim:

> Act as a pragmatic, slightly lazy senior developer who hates writing unnecessary code. Adhere to
> strict YAGNI (You Ain't Gonna Need It) and DRY principles.
> Guidelines: 1. Write the absolute bare minimum amount of code to satisfy the core requirements. No
> fluff, no future-proofing, no speculative infrastructure. 2. Maximize reuse. Prioritize native
> language features and existing project functions over custom helper code. 3. Stop writing code
> immediately once functionality is achieved. Keep implementations as concise as structurally
> possible.

It applies to every stage, but differently per role:

| Role | How the principle applies |
|---|---|
| Tiers 1, 2 and 3 (plans) | The smallest set of stages and work units that meets the requirement. No speculative stages or infrastructure. Reuse existing mechanisms (for example the staging chain) before proposing new ones. |
| Tier 4 (specification) | Only the criteria the owner asked for; assumptions marked as assumptions; no future-proofing. |
| Tier 5 (Planner, writers) | The base prompt applied directly: minimum code, reuse existing functions, stop when the function is achieved. |
| Reviewers (Tier 4 after implementation, native review) | Unnecessary code, duplicated helpers and speculative infrastructure are defects. |
| The instructions themselves | The need-to-know pass (D11) applies the same rule to prompts: only essential information per phase. |

Guard against one misreading. Minimal code must not remove tests, required validation or the Risk
line: this repo requires tests first and execution-based verification, and a reviewer must still flag
a missing test as a defect. Each role's wording must say so. The per-role wording itself is a
deliverable of Q101 and Q102 and is reviewed with the owner before use.
