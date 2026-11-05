# Five-tier orchestration acceptance criteria

Objective: build the owner-decided five-tier workflow in Q101–Q103; this is a specification, not an implementation plan.

| Stage | Landing repo | Scope |
|---|---|---|
| A1 | workflow_optimisation | Subscription metering first; measured daily feasibility. |
| A2 | workflow_optimisation | Versioned upper-tier roles; Claude Code role replacement. |
| A3 | workflow_optimisation | Paperclip/Orca setup; Codex handoffs; owner-pasted Tier 3 flow. |
| A4 | workflow_optimisation | Jev alternative-plan comparison; advisor review. |
| B0 | agent-sandbox-integration | P0 native-review feasibility spike before sandbox implementation. |
| B1 | agent-sandbox-integration | Planner/spec split; D24 staging; Engram reachability probe. |
| B2 | agent-sandbox-integration | D22 gate-author contract change, isolated as a high-risk stage. |
| B3 | workflow_optimisation | Matching workflow contracts; orchestrator narrowing; need-to-know; read-only Engram. |
| B4 | workflow_optimisation | Q103: full OpenCode model-assignment review. |

Order: A1 → A2 → A3 → A4; B0 → B1 → B2 → B3 → B4. Tracks A/B are independent (D16); B4 needs A1's baseline for final assignments. Q103 review may start earlier. Track A may delegate to today's OpenCode before Track B is ready. Each stage gets its own plan (D2). No implementation is authorized by a blocked criterion.

Sources: [Tier 2](multi-tier-orchestration.md) (D1–D24, sections 3–14); [advice](../../odd/advice/multi-tier-orchestration-antigravity.md) (verified claims, comparison, owner decisions); [Q101–Q103](../TODO.md). Later owner decisions override stale proposals/raw advice. No assumptions are added. `TBD` names an unresolved owner choice, not an implementation choice. Verification below specifies required proof, not checks executed while writing this file.

## A1

| ID | Stage | Landing repo | Acceptance criterion | Verification |
|---|---|---|---|---|
| S1 | A1 | workflow_optimisation | The usage ledger has an owner-selected repository. | Owner decision naming the repository. |
| S2 | A1 | workflow_optimisation | The ledger records usage per tier per day. | Ledger fixture covering Tiers 1–5. |
| S3 | A1 | workflow_optimisation | Claude Code usage includes each session’s plan-limit window. | One-day Claude baseline artifact. |
| S4 | A1 | workflow_optimisation | OpenAI subscription usage is attributed by tier. | One-day Codex/ChatGPT baseline artifact. |
| S5 | A1 | workflow_optimisation | Antigravity usage is recorded from owner-reported counts per use. | Baseline artifact containing an owner-reported use. |
| S6 | A1 | workflow_optimisation | Existing OpenCode metering is attributed by repository/stage. | Meter output for a named repository/stage. |
| S7 | A1 | workflow_optimisation | Advisor calls appear in Claude usage accounting. | Ledger entry for an advisor call. |
| S8 | A1 | workflow_optimisation | Jev calls appear in TypeSafe usage accounting. | Ledger entry for a Jev call. |
| S9 | A1 | workflow_optimisation | A representative day has a measured feasibility estimate for every subscription. | One-day baseline with per-subscription feasibility calculations. |
| S10 | A1 | workflow_optimisation | Tier 2 downgrades a model before its measured subscription threshold is reached. | Threshold-crossing test using the measured baseline. |
| S11 | A1 | workflow_optimisation | Tier 2 skips optional Tier 3 before its measured subscription threshold is reached. | Optional-Tier-3 threshold test using the measured baseline. |

## A2

| ID | Stage | Landing repo | Acceptance criterion | Verification |
|---|---|---|---|---|
| S12 | A2 | workflow_optimisation | Tier 1/2/2s/4 definitions have a written, versioned home — **blocked by OPEN-13**; the owner must choose the home. | Owner decision plus versioned role artifacts. |
| S13 | A2 | workflow_optimisation | Tier 1 owns the day plan’s cross-repository sequencing. | Tier 1 role section; sample day-plan artifact. |
| S14 | A2 | workflow_optimisation | Tier 1 excludes repository integration detail from its context. | Tier 1 input contract. |
| S15 | A2 | workflow_optimisation | Tier 1 is prohibited from writing code. | Tier 1 role restriction. |
| S16 | A2 | workflow_optimisation | Tier 1 reads only the minimal project registry — **blocked by OPEN-9**; the registry content must be defined. | Owner-approved registry contract. |
| S17 | A2 | workflow_optimisation | Tier 2 has one Claude Code session per repository. | Role/session mapping artifact. |
| S18 | A2 | workflow_optimisation | Tier 2 uses Haiku subagents for repository exploration. | Tier 2 exploration contract. |
| S19 | A2 | workflow_optimisation | Tier 2’s initial plan excludes code-level specifics. | Tier 2 output contract. |
| S20 | A2 | workflow_optimisation | Tier 2 “writes no code” without an explicit owner override (D5). | Role permission section with explicit-override examples. |
| S21 | A2 | workflow_optimisation | Tier 2 “makes no change without an explicit owner override” (D5). | Role permission section with explicit-override examples. |
| S22 | A2 | workflow_optimisation | Tier 2 sits above the existing OpenCode PM layer. | Tier-boundary contract retaining PM context-management duties. |
| S23 | A2 | workflow_optimisation | The Tier 2s role is defined over “Global Tooling Changes” — **blocked by OPEN-3**; the role definition is needed. | Owner-approved Tier 2s role artifact. |
| S24 | A2 | workflow_optimisation | Tier 4 authors the specification before OpenCode implementation delegation. | Tier 4 contract; handoff sequence artifact. |
| S25 | A2 | workflow_optimisation | Tier 4 is prohibited from authoring the per-stage implementation plan. | Tier 4 role restriction. |
| S26 | A2 | workflow_optimisation | Tier 4 is prohibited from implementing the change. | Tier 4 role restriction. |
| S27 | A2 | workflow_optimisation | Tier 4 may use a `luna` exploration subagent. | Tier 4 exploration permission. |
| S28 | A2 | workflow_optimisation | Tier 2 owns all Engram writes (D23). | Memory-author contract excluding writes by every other tier. |
| S29 | A2 | workflow_optimisation | `CLAUDE.md` replaces the advisory-only role with the Tier 1/2 manager role. | `CLAUDE.md` diff against the approved roles. |
| S30 | A2 | workflow_optimisation | Each role’s minimality wording preserves required tests. | Per-role wording reviewed with the owner (section 14). |
| S31 | A2 | workflow_optimisation | Each role’s minimality wording preserves required validation. | Per-role wording reviewed with the owner (section 14). |
| S32 | A2 | workflow_optimisation | Each role’s minimality wording preserves the Risk line. | Per-role wording reviewed with the owner (section 14). |
| S33 | A2 | workflow_optimisation | Review roles treat unnecessary implementation code as a defect. | Review-role wording implementing D19. |
| S34 | A2 | workflow_optimisation | Review roles treat duplicated helpers as a defect. | Review-role wording implementing D19. |
| S35 | A2 | workflow_optimisation | Review roles treat speculative infrastructure as a defect. | Review-role wording implementing D19. |

## A3

| ID | Stage | Landing repo | Acceptance criterion | Verification |
|---|---|---|---|---|
| S36 | A3 | workflow_optimisation | The downloaded Paperclip README is reviewed before adopting its integration (D13). | README review artifact. |
| S37 | A3 | workflow_optimisation | The Paperclip spike proves API/UI-only use with local CLI adapters disabled. | Spike result showing a task lifecycle without Paperclip CLI launch. |
| S38 | A3 | workflow_optimisation | “Orca is the only launcher” (D21). | Launch-ownership contract; spike process-launch evidence. |
| S39 | A3 | workflow_optimisation | Paperclip assigns work through tickets. | Spike ticket assignment artifact. |
| S40 | A3 | workflow_optimisation | Paperclip records cost. | Spike cost-event artifact. |
| S41 | A3 | workflow_optimisation | Paperclip remains macro oversight rather than the task source of truth. | Tracking contract identifying repo todo/task files as micro-level authority. |
| S42 | A3 | workflow_optimisation | Paperclip issue fields needed for repo-tracker linkage are specified. | Issue-field contract (OPEN-5 follow-up). |
| S43 | A3 | workflow_optimisation | Responsibility for keeping Paperclip in step with repo trackers is specified. | Tracking-ownership contract (OPEN-5 follow-up). |
| S44 | A3 | workflow_optimisation | Provider subscription automation remains conditional on a terms review — **blocked by OPEN-6**; permitted operation boundaries are needed. | Terms-review artifact for Claude, Codex, Gemini subscription CLIs. |
| S45 | A3 | workflow_optimisation | Tier 5 launch transport uses the existing sandbox attach client. | Orca transport spike evidence, not a Paperclip local-adapter launch. |
| S46 | A3 | workflow_optimisation | The transport preserves provider permission checks. | Spike evidence showing no permission-bypass configuration. |
| S47 | A3 | workflow_optimisation | Tier 2 can delegate a specification request to Codex through Orca. | Specification handoff/return artifact. |
| S48 | A3 | workflow_optimisation | Each handoff artifact has one author. | Handoff contract matching section 6’s author table. |
| S49 | A3 | workflow_optimisation | Tier 4 specifications use numbered atomic testable acceptance criteria. | Sample specification with individually decidable `S#` rows. |
| S50 | A3 | workflow_optimisation | Tier 2 may draft the Tier 3 prompt as a file. | Prompt-file artifact. |
| S51 | A3 | workflow_optimisation | Tier 2 opens the Tier 3 TUI using existing Orca commands. | Transport transcript with no new `orca tier3-brief` command. |
| S52 | A3 | workflow_optimisation | The owner reviews the Tier 3 prompt before submission. | Owner-interactive handoff artifact. |
| S53 | A3 | workflow_optimisation | Only the owner pastes the Tier 3 prompt. | Handoff contract excluding agent submission. |
| S54 | A3 | workflow_optimisation | Skipping optional Tier 3 does not block the pipeline. | Handoff test omitting Tier 3. |
| S55 | A3 | workflow_optimisation | Tier 2 observes sandboxed OpenCode completion through the existing read/wait path. | Transport evidence using `worker-read` or `terminal wait --for tui-idle`, without requiring worker shell reporting. |
| S56 | A3 | workflow_optimisation | Tier 2 performs the first evaluation of returned Tier 5 work. | Return-path artifact preceding the Tier 4 evaluation. |
| S57 | A3 | workflow_optimisation | Tier 4’s final spec evaluation uses the verdict enum `{PASS, FLAWS_FOUND}`. | Structured-verdict artifact with criterion references. |
| S58 | A3 | workflow_optimisation | Reported defects produce a revision of type `{new stage, spec revision}`. | `FLAWS_FOUND` return-path fixture. |
| S59 | A3 | workflow_optimisation | Tier 2 reports the completed outcome to Tier 1. | Completion handoff artifact. |

## A4

| ID | Stage | Landing repo | Acceptance criterion | Verification |
|---|---|---|---|---|
| S60 | A4 | workflow_optimisation | Plan comparison uses TypeSafe’s hosted Jev rather than a custom classifier service. | Integration diff identifying the TypeSafe API call. |
| S61 | A4 | workflow_optimisation | A Jev comparison precedes Tier 2 reading the alternative plan. | Handoff-order test. |
| S62 | A4 | workflow_optimisation | The comparison asks one Noul per aspect listed in section 9’s “Plan comparison”. | Request fixture covering the five specified aspects. |
| S63 | A4 | workflow_optimisation | Every comparison Noul below `0.3` avoids requiring Tier 2 to read the alternative plan. | Routing test with all values below `0.3`. |
| S64 | A4 | workflow_optimisation | Any comparison Noul `>= 0.3` requires Tier 2 to read the alternative plan. | Boundary routing test at `0.3`; fixture in the unsettled band. |
| S65 | A4 | workflow_optimisation | Code decides the plan-comparison route from Jev judgments. | Routing logic diff. |
| S66 | A4 | workflow_optimisation | Plan-comparison requests require owner consent to send both plans to TypeSafe. | Consent artifact before the first request using `TYPESAFE_API_KEY`. |
| S67 | A4 | workflow_optimisation | Comparison payload handling fits Jev’s documented model limits — **blocked by Jev input-size limits**; model limits plus a compliant payload strategy are needed. | Documented limits with representative payload-size verification. |
| S68 | A4 | workflow_optimisation | The advisor judges between materially competing plans. | Competing-plan advisor artifact (D18). |
| S69 | A4 | workflow_optimisation | Claude Code Tiers 1/2 use the advisor on the final plan before delegation. | Final-plan advisor artifact preceding delegation (D18). |

## B0

| ID | Stage | Landing repo | Acceptance criterion | Verification |
|---|---|---|---|---|
| S70 | B0 | agent-sandbox-integration | P0 records whether native review can inspect unapplied sandbox stages before host apply. | P0 execution transcript with observed feasibility result. |
| S71 | B0 | agent-sandbox-integration | The review location/fallback is owner-resolved before staging review behavior is finalized — **blocked by OPEN-1**; a P0-backed owner decision is needed. | Owner decision citing the P0 result. |

## B1

| ID | Stage | Landing repo | Acceptance criterion | Verification |
|---|---|---|---|---|
| S72 | B1 | agent-sandbox-integration | Sandbox implementation uses a clean starting checkout outside the existing dirty worktree. | Initial workspace status artifact excluding the existing dirty checkout. |
| S73 | B1 | agent-sandbox-integration | The Planner remains the sole author of each stage’s plan. | Planner author contract; plan-author test. |
| S74 | B1 | agent-sandbox-integration | There is “one plan per stage” (D2). | Two-stage specification fixture producing two stage plans. |
| S75 | B1 | agent-sandbox-integration | One specification may cover several stages. | Multi-stage specification accepted by the Planner contract. |
| S76 | B1 | agent-sandbox-integration | P1 builds dependent stages as unapplied sandbox work. | Two-stage build fixture showing the second stage based on the preceding tip. |
| S77 | B1 | agent-sandbox-integration | The staged build leaves host changes unapplied. | Host-tree comparison before owner apply. |
| S78 | B1 | agent-sandbox-integration | P2 exposes owner review of the staged changes. | Stage-review interaction artifact. |
| S79 | B1 | agent-sandbox-integration | Native review runs before host apply — **blocked by OPEN-1**; the P0-backed review-location decision is needed. | Stage review/apply execution evidence under the owner-approved decision. |
| S80 | B1 | agent-sandbox-integration | Host apply requires owner approval after review. | Apply test rejecting absent owner approval. |
| S81 | B1 | agent-sandbox-integration | Stage application follows the existing staging plan’s in-order rule. | Out-of-order apply rejection test. |
| S82 | B1 | agent-sandbox-integration | Reduced P4 supports stage rejection. | Rejection test using the existing staging contract. |
| S83 | B1 | agent-sandbox-integration | Reduced P4 marks dependent staged work `STALE` after rejection. | Dependent-stage state test. |
| S84 | B1 | agent-sandbox-integration | Reduced P4 rebuilds stale work from the current tip. | Rebuild base-identity test. |
| S85 | B1 | agent-sandbox-integration | Reduced P4 excludes merge-tree replay. | Staging diff showing no merge-tree replay implementation. |
| S86 | B1 | agent-sandbox-integration | P3 is deferred. | Stage plan/diff excludes P3 per-stage advisors. |
| S87 | B1 | agent-sandbox-integration | P5 is included only if unattended multi-stage execution requires it. | Stage plan records the demonstrated need, or its omission. |
| S88 | B1 | agent-sandbox-integration | P6 retains staging acceptance tests. | P6 executed acceptance-test evidence. |
| S89 | B1 | agent-sandbox-integration | P6 retains owner sign-off. | P6 owner sign-off artifact. |
| S90 | B1 | agent-sandbox-integration | The staging plan records the D24 scope change. | `docs/staging/plan.md` note quoting “P0-P2, a reduced P4 (reject, STALE, re-run from the tip, no merge-tree replay), P6 kept, P5 only if unattended multi-stage work needs it, P3 deferred.” |
| S91 | B1 | agent-sandbox-integration | The `opencode-v2-secure` Engram read probe records its observed result. | Profile-scoped MCP/store read transcript (OPEN-11 probe). |
| S92 | B1 | agent-sandbox-integration | Tier 5 Engram read access is enabled only after reachability succeeds — **blocked by OPEN-11**; a successful profile-scoped read probe is needed. | Profile permission diff plus successful read transcript. |
| S93 | B1 | agent-sandbox-integration | Tier 5 has no Engram mutation capability. | Permission test denying Engram write operations (D23). |

## B2

| ID | Stage | Landing repo | Acceptance criterion | Verification |
|---|---|---|---|---|
| S94 | B2 | agent-sandbox-integration | The `host_gate_verdict` author change is isolated in its own commit. | Commit diff containing the D22 contract change; high-risk item 3. |
| S95 | B2 | agent-sandbox-integration | An independent verifier checks the D22 author-contract change. | Independent verifier result for the isolated commit. |
| S96 | B2 | agent-sandbox-integration | Every stage has a plan-versus-spec checkpoint. | Gate test identifying each stage’s plan checkpoint. |
| S97 | B2 | agent-sandbox-integration | Every stage has an implementation-versus-spec checkpoint. | Gate test identifying each stage’s implementation checkpoint. |
| S98 | B2 | agent-sandbox-integration | Code checks touched-path scope before Jev. | Gate-order test using an out-of-scope diff. |
| S99 | B2 | agent-sandbox-integration | Code checks test exit status before Jev. | Gate-order test using a nonzero test result. |
| S100 | B2 | agent-sandbox-integration | Code checks the existing diff-line budget before Jev. | Gate-order test using an over-budget diff. |
| S101 | B2 | agent-sandbox-integration | Jev receives only checks not already decided deterministically. | Request fixture excluding deterministically settled checks. |
| S102 | B2 | agent-sandbox-integration | Each acceptance criterion is checked by one Noul. | Plan/spec and implementation/spec request fixtures keyed by `S#`. |
| S103 | B2 | agent-sandbox-integration | Each Noul receives only the evidence relevant to its criterion. | Request fixtures containing the relevant plan section or diff. |
| S104 | B2 | agent-sandbox-integration | Gate payload handling fits Jev’s documented model limits — **blocked by Jev input-size limits**; model limits plus a criterion-level payload strategy are needed. | Documented limits with per-criterion payload-size verification. |
| S105 | B2 | agent-sandbox-integration | Code records the verdict for a clear match to the spec (D22). | Clear-match routing test verifying code authorship after deterministic checks. |
| S106 | B2 | agent-sandbox-integration | A clear fail returns work to the Planner for refinement (D22). | Clear-fail routing test. |
| S107 | B2 | agent-sandbox-integration | An unsure result reaches an independent spec-check agent — **blocked by OPEN-19**; the agent identity is needed. | Unsure routing test against the owner-selected agent. |
| S108 | B2 | agent-sandbox-integration | The spec-check agent’s family differs from the Planner’s family — **blocked by OPEN-19**; the selected agent family is needed. | Agent-assignment comparison. |
| S109 | B2 | agent-sandbox-integration | The spec-check agent’s family differs from the writers’ families — **blocked by OPEN-19**; the selected agent family is needed. | Agent-assignment comparison. |
| S110 | B2 | agent-sandbox-integration | A classifier’s confidence alone cannot authorize the gate verdict. | Gate fixture with high confidence but failed deterministic evidence. |

## B3

| ID | Stage | Landing repo | Acceptance criterion | Verification |
|---|---|---|---|---|
| S111 | B3 | workflow_optimisation | `WORKFLOW.md` reflects the landed D22 verdict authorship. | Workflow diff matching the sandbox contract, replacing Planner-only gate ownership. |
| S112 | B3 | workflow_optimisation | The orchestrator contract is narrowed to simple repeated initial-planning/delegation steps. | D10 contract diff retaining the internal PM layer. |
| S113 | B3 | workflow_optimisation | Each phase receives only essential instructions after the need-to-know pass. | Phase-input contract mapping each retained instruction to its phase duty. |
| S114 | B3 | workflow_optimisation | OpenCode’s Engram instructions permit read-only strategy access — **blocked by OPEN-11**; the profile read probe must pass. | `WORKFLOW.md` memory-rule diff plus Tier 5 read evidence. |
| S115 | B3 | workflow_optimisation | Magic Context remains the OpenCode in-session memory manager. | Memory contract diff retaining Magic Context. |
| S116 | B3 | workflow_optimisation | Magic Context state is not mirrored into Engram. | Memory-flow contract excluding such mirroring. |
| S117 | B3 | workflow_optimisation | OpenCode role wording preserves section 14’s minimality principles. | Seat-instruction diff checked against section 14, including required tests/validation/Risk line. |
| S118 | B3 | workflow_optimisation | Changed workflow/config artifacts satisfy the repository verifier. | Successful `verify-workflow.sh` result covering affected source artifacts. |
| S119 | B3 | workflow_optimisation | Live deployment occurs through the verifier mirror. | Verifier deployment evidence, not direct live-config editing. |
| S120 | B3 | workflow_optimisation | The owner restarts OpenCode before changed live configuration takes effect. | Owner restart artifact after the verifier mirror. |

## B4

| ID | Stage | Landing repo | Acceptance criterion | Verification |
|---|---|---|---|---|
| S121 | B4 | workflow_optimisation | Q103 reviews every OpenCode seat across the three assignment files. | Review matrix for `global-config/opencode.json`, `global-config/systematic.jsonc`, `global-config/rate-limit-fallback.json`. |
| S122 | B4 | workflow_optimisation | The review uses the 2026-10-28 model-allocation review as an input. | Q103 review artifact referencing `docs/brainstorms/model-allocation-review-2026-10-28.md`. |
| S123 | B4 | workflow_optimisation | Final assignment choices use the measured subscription baseline — **blocked by OPEN-8**; the full assignment decision after baseline review is needed. | Owner-approved Q103 assignment matrix with baseline references. |
| S124 | B4 | workflow_optimisation | The Planner moves off Sol — **blocked by OPEN-8**; the replacement model must be selected by Q103. | Planner model diff against the approved assignment matrix. |
| S125 | B4 | workflow_optimisation | The Planner’s model differs from the specification author’s model — **blocked by OPEN-8**; approved assignments are needed. | Spec-author/Planner model comparison. |
| S126 | B4 | workflow_optimisation | “Frontier models inside OpenCode are reserved for native review” (D7) — **blocked by OPEN-8**; the complete seat assignment is needed. | Primary/fallback assignment matrix proving no non-review frontier seats. |
| S127 | B4 | workflow_optimisation | Changed model assignments preserve existing vendor-independence rules. | Assignment checks against the repository’s existing independence constraints. |
| S128 | B4 | workflow_optimisation | Changed model assignments preserve the verifier’s digest/anchor consistency. | Successful repository verifier result for the assignment diff. |
