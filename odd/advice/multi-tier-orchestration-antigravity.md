# Advice record: Antigravity alternative plan for the multi-tier orchestration (D20)

**Date:** 2026-11-05. **Source:** Tier 3 (Antigravity), run manually: Tier 2 drafted the prompt, the owner
pasted it, then pasted the output back. Antigravity was told not to read
`docs/specs/multi-tier-orchestration.md` or the Q101-Q103 entries. **Advice is evidence, never approval.**

## 1. Raw output (as pasted by the owner)

Table layout was flattened by the paste; wording is unchanged.

All repository facts cited below were gathered via two read-only evidence_collector runs (8035bad9 and 7e1c7a62). In accordance with your independence constraint, docs/specs/multi-tier-orchestration.md and docs/TODO.md (Q101-Q103) were not read.

### Pre-Implementation Findings (What is Wrong or Missing in the Raw Requirement)

- **F1, BLOCKER.** [inferred] Letting Paperclip's built-in CLI adapters spawn subscription CLIs (claude, codex, gemini) with permission-bypass flags violates subscription TOS, bypasses host approval gates, and breaks Orca session ownership. Evidence: [observed] Zero Paperclip integration exists in agent-sandbox-integration (8035bad9). Existing orchestration uses Orca TUI/CLI shims (broker/src/orca.ts:37, 8035bad9). Recommended change: Use Paperclip strictly as a control-plane state & budget ledger (HTTP API/UI). All CLI session spawning and prompt dispatch must stay in Orca (orca CLI / TUI).
- **F2, BLOCKER.** [observed] Reassigning OpenCode planner away from openai/gpt-6.1-sol to avoid matching Tier 4 (Codex) and to minimize frontier usage conflicts with current hardcoded config and verification anchors. Evidence: WORKFLOW.md:172 and global-config/opencode.json:512-516 pin planner to openai/gpt-6.1-sol, and verify-workflow.sh:5192-5350 enforces anchor tokens and SHA256 digests (7e1c7a62). Recommended change: Reassign planner to a non-OpenAI/non-frontier model (e.g., opencode-go/qwen3.7-plus or opencode-go/deepseek-v4.1-flash) and update WORKFLOW.md anchors + verify-workflow.sh in the same atomic work unit.
- **F3, WARNING.** [observed] Enabling Engram inside OpenCode directly contradicts current global memory guards and risks cross-pollination with tactical Magic Context state. Evidence: global-config/AGENTS.md:218-220 and WORKFLOW.md:75, 204 mandate Magic Context (@cortexkit/opencode-magic-context@0.49.20) and state: "Never call mem_* tools unless user explicitly enabled a separate Engram workflow" (8035bad9). Recommended change: Do not give OpenCode workers or PMs mem_* write tools. Restrict Engram in Tier 5 to read-only pull at session start (or push only at Tier 2 / post-apply ce:compound).
- **F4, WARNING.** [inferred] Implementing all of docs/staging/plan.md (P0-P6, including git merge-tree auto-replay in P4) before using multi-tier orchestration is massive over-engineering. Evidence: [observed] broker/src/service.ts:4591-5302 already implements host_plan_write, host_gate_verdict, and host_task_mark, while host_stage_* (docs/staging/plan.md:285-291) has 0 lines in broker/src/ (7e1c7a62). Recommended change: Implement only P0-P2 of docs/staging/plan.md (git ref chains + stage-review agent + host_stage_list/show/approve/reject/apply). Cut P4 (merge-tree auto-replay) in favor of dropping stale stages and re-running the worker from the new tip.
- **F5, SUGGESTION.** [inferred] Building a custom ML/NLP "Jev classifier" from scratch to check spec-to-plan/code alignment violates YAGNI when structural gate hooks already exist. Evidence: [observed] systematic-routing-guard.ts:981-1204 (7e1c7a62) and broker/src/diff-spec.ts / role-policy.ts (7e1c7a62) already gate transitions deterministically on artifact presence, path scope, and line budgets. Recommended change: Implement the "Jev classifier" as a deterministic + cheap-model rubric check (verifying touched files, test exit codes, and spec checklist IDs via a fast local/cheap endpoint) before escalating to host_gate_verdict on an LLM only when score is ambiguous.

### 1. Minimal Plan (Stages & Parallelism)

[inferred] By decoupling the upper tiers (1-4) from the OpenCode/sandbox internals (Tier 5), we need only 5 stages across two parallel tracks.

**Track A: Upper Tiers, Metering & Control Plane (No dependency on Sandbox/OpenCode internals)**

- **Stage 1: Subscription Usage Metering & Paperclip Ledger Setup** [PARALLEL with Stage 3]
  - Goal: Prove usage visibility across all 4 providers (OpenCode, Claude Code, Codex, Antigravity) and stand up Paperclip as a passive state/cost ledger without letting Paperclip spawn CLIs.
  - Work units: (a) Write a lightweight host cron/hook script (orca-usage-sync) that parses local Claude Code (~/.claude/), Codex, and Antigravity session/log stats alongside OpenCode's existing opencode-usage-total@0.3.0 (global-config/opencode.json:2797, [observed] via 8035bad9) and POSTs cost/token events to Paperclip's cost-events API. (b) Configure Paperclip org chart (Tier 1 Manager, Tier 2 Repo Managers + Tech Support, Tier 3 Advisor, Tier 4 Spec/Verifier, Tier 5 Executor) with budget caps and webhook/CLI task status updates.
  - "Done" means: Running one prompt in each CLI records a cost/usage event in Paperclip; budget thresholds trigger a warning before Orca dispatches new work.
- **Stage 2: Orca Multi-Tier Role Prompts & Handoff Shims (Tiers 1-4)** [PARALLEL with Stage 3 & 4]
  - Goal: Wire Tiers 1, 2, 3, and 4 using existing Orca sessions and repo artifact conventions (docs/specs/, docs/TODO.md), with zero new daemon infrastructure.
  - Work units: (a) Create role prompt templates for Tier 1 (Claude Code cross-repo planner), Tier 2 (Claude Code repo manager + Haiku exploration subagent config; Tech Support agent), and Tier 4 (Codex spec author/reviewer + openai/gpt-6-luna explorer). (b) Add a tiny Orca helper command (orca tier3-brief) that opens an Antigravity TUI pane and writes the Tier 3 prompt to clipboard/file so the user pastes and submits it manually (TOS-compliant).
  - "Done" means: Tier 2 can delegate a spec request to Tier 4 via Orca, optionally generate a Tier 3 brief for manual user submission, and receive a committed/staged spec markdown file in docs/specs/<change>.md.

**Track B: Tier 5 OpenCode & Sandbox Staging Refinements**

- **Stage 3: Minimum Viable Sandbox Staging (P0-P2 only of docs/staging/plan.md)** [PARALLEL with Stage 1 & 2]
  - Goal: Allow Tier 5 OpenCode workers to complete multi-stage work into git refs without blocking on human prompts, then review and apply in one user burst.
  - Work units: (a) Complete P0 spike in agent-sandbox-integration: verify gentle-ai review assess (WORKFLOW.md:259, [observed] via 8035bad9) can run against refs/opencode-sandbox/chain/<id>/stage/<n> (docs/staging/plan.md:47-50, [observed] via 8035bad9). (b) Implement P1 & P2 in broker/src/service.ts and role-policy.ts: chainCreate/chainStatus git ref tracking and the 5 host_stage_* tools (list, show, approve, reject, apply) plus the read-only primary stage-review OpenCode agent (docs/staging/plan.md:286-287, [observed] via 7e1c7a62).
  - "Done" means: A sandboxed worker completes 2 sequential stages into refs/opencode-sandbox/chain/...; the user opens the stage-review agent, runs native review (asi-review-* lenses, global-config/opencode.json:1410-1615), and applies the chain to the host working tree via host_stage_apply.
- **Stage 4: OpenCode Model Reassignment, Need-to-Know Diet & Narrowed Orchestrator** [PARALLEL with Stage 2]
  - Goal: Strip frontier models out of routine Tier 5 execution (reserving them for native review), narrow gentle-orchestrator to routing/delegation, and enable scoped Engram reads.
  - Work units: (a) In global-config/opencode.json and WORKFLOW.md: reassign planner (:512), gentle-ai-verify (:316), and advisor-*-pre (:577-584) off openai/gpt-6.1-sol to non-frontier/pool models (opencode-go/qwen3.7-plus / glm-5.3-flash), keeping gpt-6.1-sol solely on asi-review-validator (opencode.json:1615, [observed] via 8035bad9). (b) Strip phase prompts in global-config/prompts/gentle-orchestrator/ and global-config/skills/workflow-*/ to strict need-to-know inputs; tighten systematic-routing-guard.ts (:1138-1179, [observed] via 7e1c7a62) so gentle-orchestrator can only emit initial stage plan requests and delegate to pm-odd/pm-systematic. (c) Allow read-only engram lookup at Tier 2 / Tier 5 session initialization while keeping Magic Context (@cortexkit/opencode-magic-context@0.49.20) as the sole in-session memory manager (AGENTS.md:218-220, [observed] via 8035bad9). (d) Run verify-workflow.sh (7e1c7a62) and update anchor tokens/hashes.
  - "Done" means: verify-workflow.sh passes (bun test tests/routing-guard green), gentle-orchestrator is blocked by the routing guard from doing anything except initial stage planning and PM delegation, and zero gpt-6.1-sol calls occur outside native review.

**Convergence**

- **Stage 5: Deterministic + Jev Gate Classifier & End-to-End Acceptance** [DEPENDS ON Stages 1-4]
  - Goal: Replace routine LLM gate verdicts in Tier 5 with a fast classifier check and validate the full Tier 1 -> Tier 5 -> Tier 2 -> Tier 4 loop.
  - Work units: (a) Add a pre-verdict classifier hook before host_gate_verdict (broker/src/service.ts:4591, [observed] via 7e1c7a62): verify deterministic invariants first (all spec file targets touched, diff within line budget, test command exit 0) plus a fast Jev classifier score on [spec section <-> diff/plan]. Auto-pass Gate 1/Gate 2 on high confidence; invoke the Planner LLM only when ambiguous. (b) Run one full end-to-end change across the tiers and verify Paperclip cost logging, staged review/apply, and Tier 4 post-apply spec sign-off.
  - "Done" means: End-to-end test task completes from Tier 2 plan -> Tier 4 spec -> Tier 5 multi-stage sandbox build -> stage review & host apply -> Tier 4 final evaluation, with all subscription usage logged in Paperclip.

### 2. Role Contract Per Tier

- **Tier 1, Overall Manager** (Claude Code). May: plan daily cross-project priorities with user; read/write Paperclip macro goals & Engram strategic memory. May not: read/write repo source code; know repo-internal implementation details; spawn workers directly. Inputs: user goals, Paperclip dashboard/budgets, Engram cross-repo summaries. Outputs: daily priority queue in Paperclip; high-level task briefs for Tier 2.
- **Tier 2, Repo Manager** (Claude Code + Haiku explore subagents). May: explore repo via Haiku; draft repo-level change approach; delegate to Tier 4 & Tier 5 via Orca; evaluate outputs; write Engram summaries. May not: edit repo code/configs (unless explicit user override); author detailed specs; run Tier 3 directly. Inputs: Tier 1 brief, repo docs/TODO.md, Haiku exploration reports, Tier 3 alt-plan, Tier 4 final eval. Outputs: repo task brief for Tier 4; Tier 3 prompt file; delegation commands to Tier 5; final sign-off to Tier 1.
- **Tier 2b, Tech Support** (Claude Code + Haiku). May: manage global host dependencies, system packages, nono sandbox profiles, and cross-repo tooling. May not: modify project feature code or bypass user approval on destructive host changes. Inputs: escalations from Tier 2 / Tier 5 on missing host tools or broken environment. Outputs: host environment fixes, updated global tool configs, resolution report to Tier 2.
- **Tier 3, Alternative Planner (Optional)** (Antigravity, user-submitted in TUI). May: propose an independent YAGNI alternative plan and risk critique for Tier 2. May not: modify any files; be invoked headlessly by Tier 2 (TOS constraint). Inputs: generated prompt file from Tier 2 + read-only repo access. Outputs: alternative plan markdown response returned to Tier 2.
- **Tier 4, Spec Author & Final Evaluator** (Codex + gpt-6-luna explore subagent). May: explore code via luna; write multi-stage specifications before coding; evaluate applied host changes against spec post-apply. May not: write implementation code; author Tier 5 per-stage execution plans (must use different model from Tier 5 Planner). Inputs: Tier 2 approved approach; post-apply git diff + test/review artifacts. Outputs: docs/specs/<change>.md (pre-code); Final Spec Compliance Verdict (PASS / FLAWS_FOUND) to Tier 2.
- **Tier 5a, OpenCode Orchestrator, Planner & PM** (gentle-orchestrator: deepseek-v4.1-flash; planner: non-OpenAI model; pm-*: muse-spark-1.3). Orchestrator may route and delegate to PM; Planner may write 1 stage plan per spec stage (host_plan_write) and resolve ambiguous Jev gates (host_gate_verdict); PM may manage work-unit context (Magic Context), dispatch writers, tick tasks (host_task_mark). May not: Orchestrator writes code, plans, or tasks (WORKFLOW.md:151-154); Planner uses Codex's model (gpt-6.1-sol) or dispatches writers; all mutate the host tree directly or emit unapproved engram writes. Inputs: docs/specs/<change>.md, Jev classifier scores, worker results via broker/src/orca.ts (host_orca_report). Outputs: stage plans (odd/tasks/**, docs/plans/**), gate verdicts, staged git refs (refs/opencode-sandbox/chain/<id>/stage/<n>).
- **Tier 5b, Stage Reviewer & Native Review** (OpenCode stage-review agent + gentle-ai review: asi-review-*, frontier gpt-6.1-sol on validator only). May: walk user through staged diffs; run native review inside sandbox; invoke ask-gated host_stage_approve/reject/apply. May not: write feature code; self-approve or batch-approve protected paths (docs/staging/plan.md:89-91). Inputs: staged git ref chain (READY/CHECKED), spec, user interactive approval. Outputs: native review findings; applied commits on host branch (or REJECTED stage notes).

### 3. Handoff and Return Path (End-to-End Data Flow)

[inferred] Built on existing Orca + Broker primitives (broker/src/orca.ts:37-169, docs/staging/plan.md:47-88, [observed] via 8035bad9):

1. Macro to Repo (Tier 1 -> Tier 2): Tier 1 plans the day's work with the user and updates Paperclip task states. Tier 2 (1 persistent Claude Code session per repo) picks up its repo's top task, uses Haiku subagents to inspect the repo, and drafts a high-level approach.
2. Optional Alternative Plan (Tier 2 <-> User <-> Tier 3): For non-trivial changes, Tier 2 runs orca tier3-brief, generating a self-contained prompt and opening an Antigravity TUI session. The user pastes/submits the prompt in Antigravity (respecting subscription TOS). Tier 2 reads the resulting critique and finalizes the strategic approach.
3. Spec Authoring (Tier 2 -> Tier 4 -> Tier 2): Tier 2 dispatches Tier 4 (Codex + gpt-6-luna explorer) via Orca. Tier 4 writes the multi-stage specification to docs/specs/<change>.md (defining stage boundaries and acceptance criteria) and exits.
4. Unattended Multi-Stage Execution (Tier 2 -> Tier 5 Gentle Orchestrator -> Sandbox Ref Chain): Tier 2 delegates the spec to the repo's ongoing Tier 5 gentle-orchestrator session. For each stage n in the spec: gentle-orchestrator delegates to planner (on a non-OpenAI model) to write that stage's plan via host_plan_write (broker/src/service.ts:4664, [observed] via 7e1c7a62); the Jev classifier checks [Spec Stage n <-> Stage n Plan] at Gate 1, and only if ambiguous does planner run an LLM host_gate_verdict; pm-systematic / pm-odd dispatches sandboxed DeepSeek workers (gentle-ai-worker / odd-apply) starting from stage n-1's git ref tip (refs/opencode-sandbox/chain/<id>/stage/<n-1>); workers report completion outward via host_orca_report (broker/src/orca.ts:94-169, [observed] via 8035bad9); broker records refs/opencode-sandbox/chain/<id>/stage/<n>; the Jev classifier checks [Spec Stage n <-> Stage n Diff + Test Result] at Gate 2 (escalating to LLM only if unclear), and pm-* marks the work unit done (host_task_mark); execution advances immediately to stage n+1 without prompting the user or touching the host working tree.
5. User Burst: Native Review & Host Apply (Tier 5 Stage-Review Agent + User): Once all stages are CHECKED, the user enters the Tier 5 stage-review agent session. Native review (gentle-ai review using in-OpenCode asi-review-* relays, with frontier gpt-6.1-sol restricted to asi-review-validator, WORKFLOW.md:267-275, [observed] via 8035bad9) runs against the staged ref chain. If a stage is rejected via host_stage_reject, revision notes go back to the Tier 5 worker loop. If approved via host_stage_approve, host_stage_apply fast-forwards/applies the stages in order onto the host repo.
6. Final Return & Spec Evaluation (Tier 5 -> Tier 2 -> Tier 4 -> Tier 2 -> Tier 1): After host apply, control returns to Tier 2. Tier 2 dispatches Tier 4 (Codex) to review the applied host diff + test logs against docs/specs/<change>.md. Tier 4 returns a structured PASS or FLAWS_FOUND report to Tier 2. If FLAWS_FOUND: Tier 2 either loops a fix stage back to Tier 5 or escalates to the user. If PASS: Tier 2 updates docs/TODO.md, writes any cross-project strategic takeaways to Engram, and marks the Paperclip task complete for Tier 1.

### 4. What to Cut or Defer (Strict YAGNI)

1. CUT Paperclip's Local CLI Process Spawners. Why: [observed] Orca already manages sessions and worker reporting (broker/src/orca.ts:1-176, 8035bad9). Paperclip's CLI adapters spawn processes with permission-bypass flags, risking TOS violations and breaking nono sandbox boundaries. Use Paperclip solely as a budget/task database via its REST API.
2. DEFER Staging Phases P3, P4, P5, and P6 (docs/staging/plan.md:288-291). Why: [observed] Phase P4 builds automated git merge-tree --write-tree stage replay on rejection (docs/staging/plan.md:120-128, 289, 8035bad9, 7e1c7a62), which the plan itself notes has the "highest risk of subtle bugs". If Stage 2 of 3 is rejected during review, simply mark Stages 2-3 stale and let the cheap DeepSeek worker re-run Stage 3 on top of the fixed Stage 2 tip. You only need P0-P2 (chainCreate + host_stage_* + stage-review agent) to get unattended multi-stage execution.
3. CUT Direct Engram Write Access Inside OpenCode (Tier 5). Why: [observed] OpenCode already enforces @cortexkit/opencode-magic-context@0.49.20 and explicitly bans mem_* calls (global-config/AGENTS.md:218-220, 8035bad9). Giving 15+ OpenCode subagents both Magic Context and Engram causes prompt bloat and memory pollution. Let Tier 2 (Claude Code) read/write Engram for cross-repo strategy, and at most inject a read-only Engram strategic summary into Tier 5 at session start.
4. CUT Training/Hosting a Heavy Custom "Jev Classifier" Service. Why: [inferred] Do not build a standalone ML pipeline before proving the gate rubric. Implement a two-step gate check in the broker/plugin: (a) deterministic checks (touched paths match spec, tests pass, diff within budget), and (b) a single zero-temperature rubric call to a local/cheap classifier endpoint returning {score: 0..1, ambiguous: bool}.

### 5. Three Biggest Risks & Mitigations

1. Subscription TOS violations and silent quota burn across unmetered CLIs. Evidence: [observed] only OpenCode is metered today via opencode-usage-total@0.3.0 (global-config/opencode.json:2797, 8035bad9); Claude Code, Codex, and Antigravity are unmetered, and Antigravity forbids automated headless delegation. Mitigation: Stage 1 builds orca-usage-sync to parse local CLI session logs/sqlite DBs and push token/request counts into Paperclip's cost-events API before scaling up multi-tier runs. Tier 3 (Antigravity) is strictly gated behind a human copy-paste TUI handoff (orca tier3-brief), and Paperclip CLI adapters are disabled.
2. Breaking verify-workflow.sh digest and anchor invariants during OpenCode refactoring. Evidence: [observed] verify-workflow.sh (5,960 lines) enforces SHA256 self-pins in workflow-health-check.ts (:4755-4794), prompt assembly byte-identity (:202-250), and 30+ workflow:anchor blocks across WORKFLOW.md and global-config/ (:5134-5350, 7e1c7a62). Mitigation: Confine all WORKFLOW.md and global-config/ changes to Stage 4, edit global-config/prompts/gentle-orchestrator/ via assemble-orchestrator-prompt.py rather than hand-editing opencode.json, and require verify-workflow.sh + bun test tests/routing-guard to pass as the Stage 4 exit gate.
3. Native review failing on unapplied staged git refs. Evidence: [observed] WORKFLOW.md:259 runs gentle-ai review assess --cwd <repo> --agent opencode --base-ref <ref> --committed-only, which expects committed git refs in <repo>, while docs/staging/plan.md:285 flags in P0 that running native review on a stage ref (refs/opencode-sandbox/chain/<id>/stage/<n>) before host apply is an unverified spike (8035bad9, 7e1c7a62). Mitigation: Make the P0 spike the very first task of Stage 3. If gentle-ai review requires a worktree or branch ref rather than a bare refs/opencode-sandbox/... ref, materialize a temporary read-only detached git worktree inside the sandbox for the stage-review agent without mutating the host working tree.

### 6. Questions the Owner Must Answer (Ranked by Plan Impact)

1. [HIGH IMPACT, shapes Stage 5] What exactly is the "Jev classifier" in your environment? Is "Jev" an existing local model/endpoint (e.g., behind kinver on 127.0.0.1:13000 in opencode.json:2800), a specific library/rubric, or a typo for a zero-shot/embedding verifier?
2. [HIGH IMPACT, shapes Stage 1] How do you want Paperclip deployed and connected? Should Paperclip run strictly as a local passive dashboard/API receiving events from Orca, or do you require initiating tasks from the Paperclip UI (via a webhook that tells Orca to open a Tier 2 session)?
3. [MEDIUM IMPACT, shapes Stage 4] Which non-OpenAI model should replace openai/gpt-6.1-sol for the Tier 5 OpenCode planner? Since Tier 4 (Codex) writes the spec on OpenAI and we must use a different model for the OpenCode Planner while minimizing frontier usage, should planner move to opencode-go/qwen3.7-plus or opencode-go/deepseek-v4.1-flash?
4. [MEDIUM IMPACT, shapes Stage 3] Are you willing to cut automatic git merge-tree stage replay (Phase P4 of docs/staging/plan.md) for v1? If rejecting Stage n simply marks Stages n+1.. stale and re-runs the worker from Stage n, Stage 3 shrinks by ~50%.
5. [LOW IMPACT, shapes Stage 4] Is read-only Engram access at Tier 5 session start sufficient? Can Tier 2 (Claude Code) own all Engram writes after a change is applied, keeping Tier 5 OpenCode sessions strictly on Magic Context (@cortexkit/opencode-magic-context) during execution?

## 2. Verification of its claims (Tier 2, 2026-11-05)

| Claim | Result |
|---|---|
| Planner pinned to `openai/gpt-6.1-sol` (`WORKFLOW.md:172`, `opencode.json:512-516`) | Confirmed. |
| `host_stage_*` has no code in `broker/src/` | Confirmed (0 files). Plan-writer logic exists in `service.ts` (around 4625, 4721); the literal string `host_plan_write` does not appear there, so the tool's internal naming differs. |
| Staging plan P4 is "Highest risk of subtle bugs"; P1-P2 "deliver most of the value" | Confirmed (`docs/staging/plan.md:289` and the line after the table). |
| `qwen3.7-plus`, `deepseek-v4.1-flash` exist in the config | Confirmed. |
| `orca tier3-brief` | **False.** No such Orca command exists. Invented. |
| F3 quote "Never call mem_* tools unless ..." at `global-config/AGENTS.md:218-220` | **Not found.** `global-config/AGENTS.md` has no `mem_` or Engram text. The only support is `WORKFLOW.md:204` ("Engram is not probed by default"). |
| F5: the Jev classifier must be built | **Wrong premise.** Jev is TypeSafe's hosted System One model, called through its API. |
| Usage logs for Claude Code and Codex are parseable | Plausible: `~/.claude/projects` and `~/.codex` exist. No Antigravity directory was found; `~/.gemini` exists, contents unchecked. |
| F1: Paperclip adapters violate subscription terms | Unverified. Same open question as spec OPEN-6. |
| `broker/src/diff-spec.ts` exists | Confirmed. |
| Not checked | The `verify-workflow.sh` and `systematic-routing-guard.ts` line cites. |

## 3. Comparison with the Tier 2 plan (spec as committed at d343eb7, plus D17-D20)

Material differences, so under D17 reading the Antigravity plan was warranted:

| Aspect | Spec | Antigravity | Verdict |
|---|---|---|---|
| Paperclip | Role, budget and approval layer; OPEN-10 left to a spike | Never spawns CLIs; Orca is the only launcher | Adopt as an owner decision (OPEN-15) |
| Gate verdict when Jev is clear | Contradictory (D8 vs "evidence, never approval") | Auto-pass on high confidence | Owner decision (OPEN-16) |
| Engram at Tier 5 | Tier 5 writes at phase boundaries (proposal) | Tier 2 owns writes; Tier 5 reads only | Owner decision (OPEN-17) |
| Staging scope | Reference the existing plan whole | P0-P2 only, cut P4 and P6 | Counter-proposal (OPEN-18) |
| Deterministic checks before Jev | Absent | Present | Adopt |
| Metering first in Track A | Section 10 only | Stage 1 | Adopt |
| P0 native-review spike first | OPEN-1 | First task of Track B | Adopt |
| Structured Tier 4 PASS/FLAWS_FOUND verdict | Prose | Structured | Adopt |
| `orca tier3-brief` | Not in the spec | Invented command | Reject; use a prompt file and the existing Orca commands |
| Model picks for the Planner and seats | Q103 review (D15) | Decided inline | Inputs to Q103, not decisions |

## 4. Advisor judgment (D18)

Merge the useful parts into the spec; do not replace it. "P0-P2 only" over-cuts: P4 holds the reject and
STALE semantics that `host_stage_reject` depends on, and P6 is the acceptance tests and owner sign-off the
repo's verification rule requires. Counter-proposal: P0-P2, a reduced P4 (reject, STALE, re-run from the tip,
no merge-tree replay), P6 kept, P5 only if unattended multi-stage work needs it, P3 deferred (its per-stage
advisors overlap the Jev gates, so one of them must own per-stage checking).

## 5. Owner decisions on the comparison (2026-11-05)

Recorded in the spec as D21-D24: Orca is the only launcher (D21); gate verdicts are recorded by code on a
clear Jev match, sent back to the Planner on a clear fail, and sent to an independent spec-check agent when
unsure (D22); Tier 5 uses Engram read-only and Tier 2 owns all writes (D23); staging scope is P0-P2, a reduced
P4, P6 kept, P5 if needed, P3 deferred (D24).
