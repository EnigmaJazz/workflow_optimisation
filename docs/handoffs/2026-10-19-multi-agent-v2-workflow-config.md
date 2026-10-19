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
   for high-stakes work. The brief assigns no model to native `risk` and `reliability`; see
   "Native review model assignment" below.
6. **Frontend route independence gap: resolved by the lens table below.** With the Kimi
   worker, the brief's post-code Security and Performance (`kimi-k3`, Moonshot) broke rule 2. The
   revised table uses no Moonshot model in any triggered lens.
7. **OpenCode Go is ONE shared pool, not a per-model allowance (owner correction, 2026-10-19).**
   The brief's "limits are per model" and design goal 4 ("spread load across per-model pools")
   are wrong. Every request draws on the same monthly dollar cap, and the 5-hour (20%) and weekly
   (50%) windows apply to the total. The requests/month figures are therefore relative costs:
   against `deepseek-v4.1-flash` (1x), `glm-5.3-flash` is ~5x, `qwen3.7-plus` ~8x,
   `claude-haiku-5-5` ~9x, `minimax-m3` ~11x, `kimi-k2.7-code` ~26x, `deepseek-v4-pro` ~33x,
   `grok-4.7` ~205x, `qwen3.8-max` ~214x and `kimi-k3` ~353x. Consequences:
   - Family spread remains a review-quality rule (rules 1-4), never a capacity rule.
   - **Drop `qwen3.8-max` entirely** (owner decision). It is not configured today.
   - **`grok-4.7`: refuter only. `kimi-k3`: only on an explicit high-stakes run.** A lens that
     reads files makes 5-15 requests, not 1-3, so one Grok lens call costs as much as about 1-3k
     DeepSeek Flash requests.
   - `minimax-m3.1-flash-free` is the main lever while it is free, because it costs the pool
     nothing. Prefer it wherever its quality holds.
   - DeepSeek peak hours (doubled cost) now drain the shared pool.
   - The Haiku PM's 100K-token limit protects the whole pool, not just a Haiku allowance.
8. **Policy change to make deliberately:** `PASS` from `host_gate_verdict` turns advice into
   approval, but `WORKFLOW.md` says advice is evidence, never approval. **OWNER DECISION:** rewrite
   that rule for the gated routes, or keep the gate advisory.

## Native review model assignment

**Fixed-model constraint.** Each native review agent has one model in `opencode.json`, so the
brief's rule 5 (switch to a lens's alternative per route) cannot apply to native review without
rewriting config per route. Each 4R model must therefore be independent of every worker family
at once: DeepSeek, Moonshot (Kimi, the frontend worker) and OpenAI (Luna on Tiny, Sol). That rules
out Moonshot and DeepSeek for all native lenses.

Current values are from `global-config/opencode.json` as of 2026-10-19. Each `asi-review-*` relay
must keep mirroring its `review-*` agent's model and variant; it does today.

| Agent (+ `asi-` relay) | Current | Proposed | Reason |
|---|---|---|---|
| `review-risk` | `qwen3.7-plus` (high) | keep | Independent of all worker families |
| `review-resilience` | `glm-5.3-flash` (high) | keep | The brief's `qwen3.7-plus` would give Qwen two of the four lenses (rule 3) |
| `review-readability` | `muse-spark-1.3-contributor` (high) | keep | Owner is not concerned about training use (2026-10-19); keeps Meta in the family mix |
| `review-reliability` | `kimi-k2.7-code` | `claude-haiku-5-5` (owner decision) | Kimi breaks rule 2 on the frontend route; `hy4-preview` rejected on cost versus unproven quality. Shares cost with the PM, so watch it |
| `review-refuter` | `grok-4.7` (high) | keep | Reserve the Grok pool for this role and the security lens |
| `review-validator` | `minimax-m3` | keep | Same family as readability; acceptable, since it validates corrections, not the original change |
| `jd-judge-a` / `jd-judge-b` | `glm-5.3-flash` / `qwen3.7-plus` (high) | keep | The brief's `qwen3.8-max` + `grok-4.7` pair costs ~200x per request |
| `jd-fix-agent` | `gpt-6.1-sol` | `deepseek-v4-pro` | Sol here draws on the Plus subscription (goal 1); DeepSeek is independent of both judges, while GLM would collide with judge A |

## Advisor lens assignment (revises the brief's tables)

Default lenses keep the brief's models, except that the brief's `qwen3.8-max` alternative for
Test strategy becomes `minimax-m3`. Note that Test adequacy (`kimi-k2.7-code`, ~26x) is the
costliest always-on lens; its alternative `glm-5.3-flash` (~5x) is required on the frontend route
and is the first cut if cost runs high.

| Triggered lens | Pre | Post |
|---|---|---|
| Security | `qwen3.7-plus` | `claude-haiku-5-5` (`grok-4.7` or `kimi-k3` only on an explicit high-stakes run) |
| Integration / contracts | `qwen3.7-plus` | `glm-5.3-flash` |
| Architecture fit (pre only) | `minimax-m3` | — |
| Data & migration | `qwen3.7-plus` | `glm-5.3-flash` |
| Performance | `minimax-m3` | `glm-5.3-flash` |
| Concurrency / state | `glm-5.3-flash` | `claude-haiku-5-5` |
| Resilience / operability | `minimax-m3.1-flash-free` | `qwen3.7-plus` (`hy4-preview` dropped) |
| Dependencies / config / supply chain | `minimax-m3.1-flash-free` | `qwen3.7-plus` |
| UX / accessibility | `muse-spark-1.3-contributor` | `minimax-m3.1-flash-free` with screenshots |

Rule 4 holds: no lens uses the same model pre- and post-code. Rule 2 holds on every route: no
lens is DeepSeek, Moonshot or OpenAI. `qwen3.7-plus` now carries the native risk lens plus
several advisor lenses. At ~8x it should hold, but it is the model to watch.

**OWNER DECISION:** accept or amend the native and advisor tables. Re-check rules 1-3 against it after any worker
model change.

## Gap list for this repo

| Change | Files |
|---|---|
| New agents (PM, planner, Tiny/Luna, lens agents per the brief) with models, task permissions and per-agent tool enablement; each custom tool enabled only on its own agent | `global-config/opencode.json` |
| Orchestrator `permission.task`: route to PM and Tiny only; keep `asi-review-*` and `advisor-*` allowed | `global-config/opencode.json` (`gentle-orchestrator`, ~line 466) |
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
5. Worker/PM/lens pairings: only the frontend route breaks rules 1-2 (item 6 above). Re-check
   after any model change.
6. Existing advisor and lens definitions: map the `advisor-*-pre` agents and the post lenses to
   the brief's lens list, and propose renames or merges. Nested dispatch of `advisor-*` from a
   subagent is unproven (`opencode run --agent advisor-*` already misbehaves, Q51), so probe it
   before relying on it.
7. Unverified claim: Haiku's price rising 5x above 100K tokens. Confirm before using it as a hard
   PM session limit.

## Trial metrics

Log these from the first run: Sol turns per subproject by route; findings and accepted findings
per lens; gate outcome counts; how often the Tiny guard refuses; shared Go pool dollars per model
per subproject, and per 5-hour window against the 20% cap.

## Order

1. `agent-sandbox-integration` builds and tests the host tools.
2. Owner decisions 5, 6 and 8 above, plus the `host_plan_write` approval decision.
3. This repo: queue revision, then config, guard and skills in one work unit, then the verifier.
4. Verifier mirror, owner restart, behavioral probes (including nested advisor dispatch).
