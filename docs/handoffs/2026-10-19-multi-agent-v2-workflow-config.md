# Handover: multi-agent setup v2, workflow config half

**For:** the OpenCode agents in `workflow_optimisation`.
**From:** Claude Code (advisory review of the owner's v2 brief), 2026-10-19.
**Status:** design handover. Implementation needs the owner's go-ahead.
**Depends on:** the `agent-sandbox-integration` handover
`docs/handoffs/2026-10-19-multi-agent-v2-host-tools-agent-sandbox-integration.md`
(`host_plan_write`, `host_gate_verdict`, `host_task_mark`, the apply deny list, and the Tiny size
guard). Do not enable those tools here before they exist; the verifier would flag them.

## Read first

`WORKFLOW.md`, `docs/TODO.md` Q53-Q61 (the PM layer) and the owner's v2 brief. This is **not a
new track**. It revises the PM layer (Q55-Q61) and absorbs the unmerged planner-tier plan on
branch `docs/pm-planner-delegation` (`9938cd1`). That plan used the number Q67, which collides
with the existing Q67 ("Retired SDD command detector") on `feat/gentle-ai-v4`, so renumber it.

## Revisions to the owner's brief (from the advisory review)

1. **The PM runs the lenses, not Sol.** Each advisor result returned into Sol's context costs
   subscription turns. Gate 1, gate 2 and up to two REFINEs already make 4+ Sol sessions per
   subproject. The PM dispatches the lenses and gives Sol one synthesized findings pack, and Sol
   judges. This serves design goal 1.
2. **The gate tier comes from the native assessment, not from frontmatter.** See host tool 3 in
   the companion handover.
3. **The Tiny escape hatch is enforced by the apply tool, not by Luna's self-report.** See host
   tool 5.
4. **The Tiny route is not "covered by the normal gentle AI review".** Under gentle-ai 4.1.0,
   `review assess` sets `review_due` only for `high` risk, so Tiny and low-risk Small get no
   automatic review. State that plainly, or require one post-code lens on Tiny as well.
5. **Judgment-day is not a native review lens.** Native review is the 4R set (risk, resilience,
   readability, reliability) plus refuter and validator. Keep judgment-day as an optional skill
   for high-stakes work; the owner uses it very rarely (2026-10-21), so its judge cost barely
   touches the pool. See "Model assignment" below.
6. **Frontend route independence: resolved.** The revision seats `kimi-k2.7-code` (Moonshot)
   on native readability and two advisor lenses. There is no Kimi frontend worker (owner,
   2026-10-21), so rule 2 holds. If a Moonshot worker is ever added, move those seats.
7. **OpenCode Go is ONE shared pool, not a per-model allowance (owner correction, 2026-10-19).**
   The brief's "limits are per model" and design goal 4 ("spread load across per-model pools")
   are wrong. Every request draws on the same monthly dollar cap, and the 5-hour (20%) and weekly
   (50%) windows apply to the total. The requests/month figures are therefore relative costs:
   against `deepseek-v4.1-flash` (1x), `glm-5.3-flash` is ~5x, `qwen3.7-plus` ~8x,
   `claude-haiku-5-5` ~9x, `minimax-m3` ~11x, `kimi-k2.7-code` ~26x, `deepseek-v4-pro` ~33x,
   `grok-4.7` ~205x, `qwen3.8-max` ~214x and `kimi-k3` ~353x. Consequences:
   - Family spread remains a review-quality rule (rules 1-4), never a capacity rule.
   - **`qwen3.8-max` only where it runs rarely** (owner, 2026-10-21): `jd-judge-a` (judgment
     day is rarely used) and the planner-chosen high-risk architecture escalation. Never in a
     default seat.
   - **`grok-4.7` and `kimi-k3` are in no seat.** A lens that reads files makes 5-15 requests,
     not 1-3, so one Grok lens call costs as much as about 1-3k DeepSeek Flash requests.
   - DeepSeek peak hours (doubled cost) now drain the shared pool.
   - Any per-session token limit (Haiku now sits on the validator) protects the whole pool.
8. **Policy change to make deliberately:** `PASS` from `host_gate_verdict` turns advice into
   approval, but `WORKFLOW.md` says advice is evidence, never approval. **OWNER DECISION:** rewrite
   that rule for the gated routes, or keep the gate advisory.

## Model assignment (owner revision, 2026-10-21)

This replaces the 2026-10-19 tables. Thinking-level names vary by provider: `glm-5.3-flash`
offers only low, high and max; `kimi-k2.7-code` forces thinking with no level; `minimax-m3`
offers only adaptive. Map each level to the real variant name and use the nearest level where a
name does not exist. `opencode.json` has no `variants` block today, so every level is new config.

**Fixed seats.** Every `review-*` and `asi-review-*` agent is in `excludeAgents`, and both judges
and the advisors are in `noFallbackAgents` (`global-config/rate-limit-fallback.json:893`). Each
seat runs only its own model, so it must be independent of every model that writes code,
including that writer's fallbacks (see fix 1 below).

### Core roles

| Role | Model · level | Note |
|---|---|---|
| Orchestrator | `deepseek-v4.1-flash` · high | |
| Explorer | `deepseek-v4.1-flash` · non-thinking (or lowest) | |
| Planner | `openai/gpt-6.1-sol` · high; xhigh for gate 1 on multistep or high-risk work | Avoid max (owner-cited benchmark: costlier than xhigh, lower on one agentic test) |
| PM | `glm-5.3-flash` · high; fallback `qwen3.8-flash` · high | Needs an `agentFallbackModels` entry; the model-level fallback for GLM is mimo |
| Workers | `deepseek-v4.1-flash` · high; `deepseek-v4-pro` · high for algorithm-heavy or repo-level work | |
| Tiny route | `openai/gpt-6-luna` · medium, never above high | Owner-cited: Luna xhigh scored below high. OpenAI provider (fix 6) |

### Native review (fixed)

| Agent (+ `asi-` relay) | 2026-10-19 proposal | Now |
|---|---|---|
| `review-risk` | `qwen3.7-plus` | `qwen3.8-flash` · high |
| `review-resilience` | `glm-5.3-flash` | `glm-5.3-flash` · high (Flash gains little from max) |
| `review-reliability` | `claude-haiku-5-5` | `minimax-m3` · adaptive, max output ≥32K (see fix 3) |
| `review-readability` | `muse-spark-1.3-contributor` | `kimi-k2.7-code` · forced thinking (see item 6) |
| `review-validator` | `minimax-m3` | `claude-haiku-5-5` · high |
| `review-refuter` | `grok-4.7` | `mimo-v2.6-flash` · default thinking, max output ≥32K (see fix 1) |

The `asi-review-*` agents are the lanes native review actually runs on in OpenCode. Change them
too, not only `review-*`, and keep each mirroring its lens's model and level.

### Judgment day (rarely used)

| Agent | Model · level |
|---|---|
| `jd-judge-a` | `qwen3.8-max` · high |
| `jd-judge-b` | `glm-5.3` · max |
| `jd-fix-agent` | `openai/gpt-6-luna` · high; Sol · high for consequential cases |

### Advisors (pre → post)

| Lens | Pre | Post |
|---|---|---|
| Scope & requirements | `qwen3.8-flash` · medium | — |
| Testing | `glm-5.3-flash` · high | `qwen3.8-flash` · medium |
| Bug hunt (post only) | — | `glm-5.3-flash` · high |
| Security | `glm-5.3-flash` · high | `mimo-v2.6-flash` · default (see fix 1) |
| Integration | `minimax-m3` · adaptive | `qwen3.8-flash` · medium |
| Architecture (pre only) | `qwen3.8-flash` · medium | — |
| Data & migration | `qwen3.8-flash` · medium | `glm-5.3-flash` · high |
| Performance | `qwen3.8-flash` · medium | `minimax-m3` · adaptive |
| Concurrency | `qwen3.8-flash` · medium | `glm-5.3-flash` · high |
| Resilience | `minimax-m3` · adaptive | `glm-5.3-flash` · high |
| Dependencies / config | `minimax-m3` · adaptive | `kimi-k2.7-code` · forced |
| UX / accessibility | `kimi-k2.7-code` · forced | `qwen3.8-flash` · medium |

Qwen advisors run at medium because of its verbose-output cost; the gate lens keeps high. GLM
advisors run at high because GLM has no medium. Rule 4 holds: no lens uses the same model pre and
post. Map these lenses onto the existing `advisor-*` agents (verify item 6).

**High-risk escalations (the planner chooses):** Architecture `qwen3.8-max` · high; Bug hunt
`glm-5.3` · max; auth or payment security on `google/gemini-4-argon`, fed by a
`google/gemini-flash-latest` evidence subagent (see fix 5).

**If `minimax-m3.1-flash` becomes paid on Go:** `review-reliability` moves to it at xhigh (the
vendor reports most of the gain by xhigh) and every `minimax-m3` advisor seat moves to it at high.
Its thinking cannot be switched off, so even high adds latency. Switch only if its Go allowance is
at least M3's and it passes the OpenCode session and hang checks.

### Fixes to apply with this table (Claude Code review, 2026-10-21)

1. **Worker fallback reaches the refuter.** `rate-limit-fallback.json` sends
   `deepseek-v4.1-flash` and `deepseek-v4-flash` (and `glm-5.3-flash`, `kimi-k2.7-code`,
   `qwen3.7-plus`, `muse-spark-1.3-contributor`) to `mimo-v2.6-flash`. A throttled worker then
   writes as mimo, and the mimo refuter and mimo post-code Security lens rule on its code.
   **Owner decision (2026-10-21): change the fallback.** Remove `opencode-go/mimo-v2.6-flash`
   from the `opencode-go/deepseek-v4.1-flash` and `opencode-go/deepseek-v4-flash` chains. What
   remains (`deepseek/deepseek-flash`, then `openrouter/deepseek/deepseek-v4.1-flash`) stays in
   the DeepSeek family and outside the Go pool. Add a verifier check that no code-writing agent's
   fallback chain reaches a model in a review or post-code seat.
2. **`qwen3.8-max` stays, scoped:** judge A and the architecture escalation only (owner,
   2026-10-21: judgment day is very rarely used).
3. **The M3 hang.** Swapping reliability with readability moves a hang to another fixed seat
   with no fallback; it does not fix it. If the hang is present, keep `minimax-m3` out of every
   native seat and use it only for advisors. This repo holds no record of the hang; verify it.
4. **Model IDs not configured anywhere yet:** `claude-haiku-5-5`, `qwen3.8-flash`,
   `qwen3.8-max`. `glm-5.3` appears only as a fallback entry. Confirm each exists on Go before
   building (verify item 1).
5. **Gemini escalation (owner decision, 2026-10-21): `google/gemini-4-argon` judges, with a
   `google/gemini-flash-latest` subagent gathering information.** This pattern already exists:
   `advisor-gemini-pre` and `advisor-gemini-post` run on Argon, and `advisor-gemini-evidence`
   gathers facts for them but runs `google/gemini-3.8-flash`. Move that evidence agent to
   `google/gemini-flash-latest` rather than adding a new one. Gemini bills outside the Go pool.
   Argon dispatching the evidence agent is a nested dispatch; probe it (verify item 6).
6. **Luna's provider (owner decision, 2026-10-21): `openai/gpt-6-luna`** for the Tiny route and
   `jd-fix-agent`. It bills outside the Go pool. Its existing fallback chain starts at
   `opencode-go/gpt-6-luna` (shared pool), then DeepSeek; both stay independent of every review
   seat.

Unverified, owner-cited: the thinking-level names above and the Sol and Luna benchmark claims.

All model-assignment decisions are recorded. Re-check rules 1-3 after any worker model change.

## Gap list for this repo

| Change | Files |
|---|---|
| New agents (PM, planner, Tiny/Luna, lens agents per the brief) with models, task permissions and per-agent tool enablement; each custom tool enabled only on its own agent | `global-config/opencode.json` |
| Orchestrator `permission.task`: route to PM and Tiny only; keep `asi-review-*` and `advisor-*` allowed | `global-config/opencode.json` (`gentle-orchestrator`, ~line 466) |
| Fallbacks: drop mimo from the DeepSeek chains (fix 1); `agentFallbackModels` for the PM | `global-config/rate-limit-fallback.json` |
| Guard: new agents in `ROUTE_STAGES` (deny by default), new host tools in the host-tool list | `global-config/plugins/systematic-routing-guard.ts` (:219-224), `global-config/plugins/lib/routing-guard-helpers.ts` |
| Route skills: Tiny/Small/Multistep selection, escape-hatch reroute, the single tick writer | `global-config/skills/workflow-route/`, `workflow-odd-secure/` |
| Recipe: routes, gates and the advice-versus-approval rule | `WORKFLOW.md` |
| Verifier: the new agents exist, their models resolve, tools are enabled only on their agent, and the relay agents mirror their review agent's model and variant. Re-pin the digest. | `verify-workflow.sh`, `global-config/plugins/workflow-health-check.ts` |
| Queue: revise Q55-Q61, renumber the planner tier | `docs/TODO.md`, `docs/PLAN.md` |

The specialist policy is stated in three places that must agree: the guard's `ROUTE_STAGES`,
the task permissions in `opencode.json`, and the route skills. Change them in one work unit.

## Risks specific to gentle-ai 4.1

- **#5403 restricts the OpenCode orchestrator to Gentle AI subagents.** `gentle-ai sync` will
  strip every new agent from the orchestrator's permissions, and the verifier must restore them
  on each sync. Add a verifier check that fails loudly when they are missing.
- OpenCode permissions now follow the "Pi safety model" (#5273). Confirm by a live run that the
  restored overlay still takes effect.

## Things to verify (from the brief, with what is already known)

1. Model IDs: run `opencode models opencode-go` (or the equivalent) and record the results.
2. Subagent session resume for gate 2: unverified. If unavailable, the plan file is the
   contract, as the brief says.
3. Calling-agent identity: **yes**, `ctx.agent` is available (see the companion handover).
4. The ODD plan lives on disk at `odd/tasks/<feature>.md` and is mirrored to Magic Context. ODD's
   own flow ticks tasks today; route that through `host_task_mark` once it exists.
5. Worker/PM/lens pairings: check rules 1-2 against the 2026-10-21 table, including worker
   fallbacks after fix 1.
6. Existing advisor and lens definitions: map the `advisor-*-pre` agents and the post lenses to
   the brief's lens list, and propose renames or merges. Nested dispatch of `advisor-*` from a
   subagent is unproven (`opencode run --agent advisor-*` already misbehaves, Q51), so probe it
   before relying on it.
7. Unverified claim: Haiku's price rising 5x above 100K tokens. Confirm before setting a session
   limit on the Haiku validator.

## Trial metrics

Log these from the first run: Sol turns per subproject by route; findings and accepted findings
per lens; gate outcome counts; how often the Tiny guard refuses; shared Go pool dollars per model
per subproject, and per 5-hour window against the 20% cap.

## Order

1. `agent-sandbox-integration` builds and tests the host tools.
2. Owner decisions: item 8 and the `host_plan_write` approval decision.
3. This repo: queue revision, then config, guard and skills in one work unit, then the verifier.
4. Verifier mirror, owner restart, behavioral probes (including nested advisor dispatch).
