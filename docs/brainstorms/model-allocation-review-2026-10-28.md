# Model allocation review (mapping stage, 2026-10-28)

Status: **mapping only. No config was changed.** This is the evidence base for deciding changes together.

Sources, all read on 2026-10-28:

- Config: `global-config/opencode.json` (45 agents), `global-config/systematic.jsonc` (5 categories, 3 mutators, 37 agents), `global-config/rate-limit-fallback.json`.
- Limits: <https://opencode.ai/docs/go/> (Go and Go Plus tables), <https://commandcode.ai/docs/plans/goat> (GOAT credits).
- Live state: proxy `/health` and `~/.local/state/opencode-go-proxy/proxy.sqlite` (6,836 metered requests, 22–28 Oct), `~/.local/share/opencode/opencode.db` (assistant messages, 19–25 Oct).
- Capability: Artificial Analysis (AA) leaderboard and posts, vendor posts, aggregator sites (links at the end). **Numbers from different sources use different index versions and do not compare across sources.**

## 1. Current allowance state (why this matters now)

| Pool | State | Binding limit |
|---|---|---|
| Go ($10 plan) | monthly **99%** used, resets 9 Nov 21:40 UTC | monthly pool |
| Command Code (cc) | weekly **76.6%** of $35 (resets 30 Oct 06:22 UTC); monthly 38% of $70.07 (resets 22 Nov); 5-hour cap $14 | the weekly window |

The routing proxy is in `live` mode, so with Go nearly exhausted, traffic falls onto cc, and cc's weekly cap is the real constraint.

How the two backends charge, which sets the multiplier in section 3:

- **Go:** every model has its own monthly dollar limit (5h = 20%, week = 50%, month = 100%). The proxy treats it as one pool, where a metered dollar on a model costs `100 / limit` percent of the pool. DeepSeek V4.1 Flash costs 1.25% per dollar, MiniMax M3.1 Flash costs 5% per dollar.
- **cc:** one dollar cap per window ($14 / $35 / $70.07 on this account). **Owner correction (2026-10-28): each provider is one shared pool, not a pool per model.** The per-model "monthly credits" in the cc docs and the per-model limits in the Go docs are therefore relative weights (how fast a model drains the shared pool), not separate allowances. The proxy fits a real "dollars charged per metered dollar" weight per model from usage. In section 3, "Go limit / cc credit" columns read as weights, and "req/mo" means requests if the whole pool went to that model.

## 2. Agent and model map

Checked: source `global-config/` matches the live `~/.config/opencode/` on model and variant for all 45 agents, 37 Systematic agents and 5 categories (0 differences), so no separate "live" column is needed. **The Effort column is unverified:** the provider block defines variants only for a few models (`variants {}` for DeepSeek flash, GLM flash, MiniMax M3.1 Flash, Qwen, Haiku, Luna), so `high`/`xhigh`/`medium` may fall to OpenCode built-ins or be ignored.

"Msgs/wk" is assistant messages 19–25 Oct from `opencode.db`. **Several rows ran on older assignments in that window** (noted), so treat it as a frequency estimate by role, not a measurement of the current config. Tier column is defined in section 3.

### 2.1 Core workflow (`opencode.json`)

| Agent | Model | Effort | Tier | Msgs/wk | Needs |
|---|---|---|---|---|---|
| `gentle-orchestrator` (primary) | opencode-go/deepseek-v4.1-flash | default | VH | ~1,470 | routing, instruction following, long context, cheap |
| `pm-odd`, `pm-systematic` | opencode-go/glm-5.3-flash | high | H | ~1,250 (ran on Sol then) | structured planning, tracker discipline |
| `planner` | openai/gpt-6.1-sol (ChatGPT OAuth) | high | unmetered | 94 | gate verdicts, deepest reasoning |
| `planner-evidence` | openai/gpt-6-luna | medium | unmetered | 9 | facts at path:line |
| `gentle-ai-verify` | openai/gpt-6.1-sol | high | unmetered | 593 | verify code against specs, run examples |
| `gentle-ai-worker`, `odd-apply` | opencode-go/deepseek-v4.1-flash@worker (cc-preferred) | default | VH | ~5,600 | code writing, tool use, test loops |
| `gentle-ai-worker-local` | kinver/professional (local) | none | local | 73 | one-file writes |
| `general` | openai/gpt-6-luna | high | unmetered | ~2,960 | tiny-fix writer, independent of DeepSeek |
| `explore`, `gentle-ai-explore` | opencode-go/deepseek-v4.1-flash | medium | VH | ~810 | read-only mapping, speed |
| `frontend-apply` | deepseek-v4.1-flash@worker | default | VH | ~0 | UI code with vision |
| `frontend-apply-local` | kinver/professional | none | local | ~0 | |
| `frontend-dev` | opencode-go/glm-5.3-flash | high | H | ~0 | UI, vision |
| `frontend-dev-premium` | openai/gpt-6.1-sol | high | unmetered | ~0 | hardest UI |
| `vision` | openai/gpt-6-luna | none | unmetered | ~0 | image reading |
| `jd-fix-agent` | openai/gpt-6.1-sol | none | unmetered | ~0 | surgical fixes |
| `jd-judge-a` | opencode-go/glm-5.3-flash | high | H | ~0 | blind adversarial review |
| `jd-judge-b` | opencode-go/qwen3.7-plus | high | M | ~0 | blind adversarial review |

### 2.2 Native review (`review-*` and mirrored `asi-review-*`, identical assignments)

Read-only, no tools, bounded token output. Rare but heavy per request: about 100 messages a week in total.

| Seat | Model | Effort | Tier | Observed cost per request |
|---|---|---|---|---|
| risk | qwen3.7-plus | high | M | ~$0.006, 640 out tokens |
| resilience | glm-5.3-flash | high | H | ~$0.0045 (1.7k out) |
| readability | muse-spark-1.3-contributor | high | VH | ~$0.004 (3.5k out) |
| reliability | **minimax-m3.1-flash** | **xhigh** | L | ~$0.0062 cc, $0.0074 Go (3.8k out) |
| refuter | **grok-4.7** | high | VL | **~$0.25 per call** (~20k reasoning tokens) |
| validator | claude-haiku-5-5 | high | H (<100k) | no recorded runs in `opencode.db` (see section 5) |

All twelve are in `excludeAgents` of the fallback plugin, so they never fail over.

### 2.3 Advisors (all in `noFallbackAgents`)

| Agent | Model | Tier | Msgs/wk (old assignments) |
|---|---|---|---|
| `advisor-design-pre`, `advisor-security-pre` | openai/gpt-6.1-sol | unmetered | 8, 52 |
| `advisor-integration-pre` | minimax-m3.1-flash (high) | L | 518 (was Kimi K2.7 Code for half) |
| `advisor-testing-pre` | glm-5.3-flash (high) | H | 50 |
| `advisor-maintainability-pre` | minimax-m3.1-flash (high) | L | 22 |
| `advisor-design-post`, `advisor-security-post` | qwen3.7-plus | M | 131 (security) |
| `advisor-integration-post` | qwen3.8-flash | H | **806** (was Kimi K2.7 Code) |
| `advisor-testing-post` | qwen3.8-flash | H | 42 (was Kimi) |
| `advisor-maintainability-post` | ling-3.1-flash | M | ~0 |
| `advisor-gemini-pre/post` | google/gemini-4-argon (paid Google API credits) | VL | 4 |
| `advisor-gemini-evidence` | google/gemini-3.8-flash | L | 68 |

### 2.4 Systematic (`systematic.jsonc`)

- Category defaults (workflow, research, review, document-review, design): all `deepseek-v4.1-flash` (VH).
- Mutators `systematic-implementer` (**xhigh**), `bug-reproduction-validator`, `pr-comment-resolver`: DeepSeek flash. `design-iterator`: glm-5.3-flash.
- Researchers and low-stakes reviewers on DeepSeek flash (low to medium): spec-flow-analyzer, repo-research-analyst, git-history-analyzer, best-practices-researcher, framework-docs-researcher, issue-intelligence-analyst, learnings-researcher, maintainability, project-standards, agent-native, performance, previous-comments, code-simplicity, pattern-recognition, scope-guardian.
- glm-5.3-flash: api-contract, architecture-strategist (high), reliability, data-migrations, deployment-verification, feasibility reviewers.
- qwen3.7-plus: correctness-reviewer. gpt-6-luna (low to medium): slack-researcher, testing, cli-readiness, kieran-typescript, coherence, design-lens, product-lens reviewers.
- gpt-6.1-sol (high): adversarial, security, security-lens, adversarial-document reviewers (each has a hidden `-astra` alias).
- Frequency: `ce:review` personas are rare (correctness 18, testing 13, project-standards 10 messages in the week).

### 2.5 Fallback chain (`rate-limit-fallback.json`)

Every DeepSeek/Go model falls back to `deepseek/deepseek-flash` (direct API, max) then `openrouter` DeepSeek V4.1 Flash. Sol/Luna fall back to the same. So **a Go or ChatGPT exhaustion silently turns Sol/Luna/GLM roles into DeepSeek**, which defeats the writer/reviewer independence the workflow assumes (WORKFLOW.md already says to dispatch an independent specialist if that happens).

## 3. Model tiers (usage allowance)

Method: requests per month if a model had the whole pool, using a profile that matches our traffic, not the docs' "typical request". Profile: 5k fresh input, 100k cached input, plus the model's own measured output tokens (DeepSeek 0.75k, GLM flash 1.7k, MiniMax M3.1 Flash 3.8k, Kimi 0.6k, Qwen3.7 Plus 0.64k, others 1k). Our requests are about 4x heavier than the docs' typical request (docs: 800 fresh, 50k cached, 125–200 output), so docs counts are roughly 4x ours. Backends are summed where the proxy registry allows both. cc is capped at the $70.07 account pool and uses fitted weights where measured (MiniMax M3.1 Flash 3.46x, Kimi 1.17x, GLM flash 0.93x, DeepSeek 0.90x).

Thresholds: **VH** ≥ 30k, **H** 12–30k, **M** 5–12k, **L** 1.5–5k, **VL** < 1.5k requests a month.

| Tier | Model | Req/mo (ours) | Go docs req/mo | Go limit / cc credit | Note |
|---|---|---|---|---|---|
| VH | deepseek-v4.1-flash | ~88k | 173k | $80 / $80 | peak 01–04 and 06–10 UTC weekdays costs 2x |
| VH | mimo-v2.6-flash | ~64k | 150k | $60 / $20 | planned refuter, not used today |
| VH | muse-spark-1.3-contributor | ~43k (Go only) | 227k | $60 / none | training-data terms accepted 5 Oct |
| VH | longcat-2.0 (**not in config**) | ~33k | 57k | $60 / $50 | |
| H | glm-5.3-flash | ~29k | 31.6k | $60 / $80 | |
| H | hy3 | ~27k | 21.5k | $60 / $70 | |
| H | qwen3.8-flash | ~18k | 27k | $30 / $20 | |
| H below 100k context, **L above** | claude-haiku-5-5 | ~10–12k under 100k; **~1.5k Go, ~2k cc above** | 19.2k | $15 / $20 | price steps up 5x at 100k tokens; the section 3 profile (105k) is above it. Measured contexts: lenses 37–60k, `gentle-ai-verify` ~70k (below); orchestrator ~208k, `advisor-integration-pre` ~150k, explore ~110k (above) |
| H | gpt-6-luna (Go/cc route) | ~17.5k | 21k | $15 / $20 | we use it through ChatGPT OAuth instead |
| M | qwen3.7-plus | ~8.5k (Go only) | 21.6k | $60 / none | |
| M | ling-3.1-flash | ~8.3k (cc only) | n/a | none / $100 | |
| M | mimo-v2.6-pro (not in config) | ~9k | 16.3k | $15 / $20 | AA ~30 vs flash 27 |
| M | minimax-m3 | ~6.3k (Go only) | 16k | $60 / $47 | |
| L | **minimax-m3.1-flash** | ~4.4k Go, ~1.3k cc | 19.4k | **$20** / $20 | see section 4 |
| L | kimi-k2.7-code | ~4.2k | 6.75k | $60 / $60 | |
| L | deepseek-v4-pro | ~3.4k | 5.2k | $15 / $20 | |
| L | gemini-3.8-flash | ~1.2k (cc only) | n/a | none / $40 | |
| VL | gemini-4-argon | ~0.75k (Go) | 2.1k | $30 / none | **50% off ends 30 Nov**, then half |
| VL | glm-5.3, qwen3.8-max, muse-spark-1.3 | ~0.7–0.8k | 0.8–1.1k | $15 / $20 | |
| VL | kimi-k3, claude-sonnet-5-5, grok-4.7 | 0.2–0.5k | 0.5k / 0.25k cc / 0.85k | $15 / $10–20 | Grok at the refuter's 20k-token profile |
| n/a | gpt-6.1-sol, gpt-6-luna (as used) | unmetered by the proxy | | ChatGPT OAuth | plan limits not visible to us; cc lists GPT-5.6 Sol at $20 / ~590 req a month |

New-in-the-docs models not in our config: LongCat-2.0, MiMo-V2.6-Pro, GLM-5.2, Kimi K3.1 Pro, Hy4 preview, Step 5 Preview, GPT 5.6 Luna, Muse Spark 1.2 Contributor, **Beam Free and Iceman Contributor Free (unlimited, "limited time")**.

## 4. Capability findings (low confidence on exact numbers)

Relative picture, from AA's leaderboard page (one consistent snapshot): GPT-6.1 Sol high 50 (max 55), Gemini 4 Argon high 50, Kimi K3.1 Pro 46, Grok 4.7 high 35, Qwen3.8 Max 34, Claude Haiku 5.5 high 30 (max 36), DeepSeek V4.1 Flash 32, GLM-5.3 32, MiMo-V2.6-Pro 30, MiniMax-M3.1-Flash 29, Ling 3.1 Flash 1019 29, MiMo-V2.6-Flash 27, GPT-6 Luna high 21 (max 28), MiniMax-M3 19. No AA score found for Qwen3.7 Plus, Qwen3.8 Flash, Hy3 (25 on an older index, trails GLM flash), Muse Spark 1.3 Contributor, Kimi K2.7 Code (42 on an older index).

- **DeepSeek V4.1 Flash:** top of the cheap tier on coding and terminal work (vendor: DeepSWE 74%, Terminal-Bench 2.1 90.6%; AA calls it verbose). Right choice for the workhorse seats.
- **GLM-5.3-Flash:** about level with DeepSeek flash on AA's index, DeepSWE 63%, Terminal-Bench 2.1 84%. Credible PM and mid reviewer.
- **MiniMax M3.1 Flash:** index 42 vs GLM flash 42 on the older index (29 vs DeepSeek 32 on the newer one), DeepSWE 73.7%. AA reports a **93% hallucination rate** (it answers instead of abstaining). For a reviewer that flags defects, that is the wrong failure mode. Single-source claim, worth confirming.
- **Claude Haiku 5.5:** best tool-use and Terminal-Bench of the cheap models that are a different family (TB 4.0 about 33–39% vs Luna 13–16%, Grok 26–38%). Fast (190–240 tok/s).
- **Grok 4.7:** index 35, low hallucination (29% listed), but very token-hungry: at the refuter's profile it is the most expensive call in the workflow.
- **GPT-6 Luna:** weak (index 21 at high, Terminal-Bench 13–16%). Fine for tiny fixes and facts, a poor choice anywhere judgment matters.
- **GPT-6.1 Sol:** strongest model in the config, and cheap per task on AA (about $0.59 at high). Its only cost to us is ChatGPT plan headroom.
- **Gemini 4 Argon:** matches Sol high on the index; hallucination rate reported as the lowest on one leaderboard (conflicting sources). Different family from every other seat.
- **Kimi K2.7 Code:** strong at MCP/tool use (81.1 MCP Mark), mediocre on AA (index fell 44→42). Expensive for what it did: OpenCode's own cost estimate shows **$18.74 + $6.91 + $1.43 + $1.93 across four advisor/lens seats** before those were reassigned (it is now in no agent). The proxy meters $11.67 of Kimi on cc, since it only started logging on 22 Oct.
- **Qwen3.8 Flash / Flash-Next:** vendor DeepSWE 58.7% (Flash-Next); independent small test put it below GLM flash (70% vs 79%). Unstable on very long chains per community reports.
- **Muse Spark 1.3:** vendor claims DeepSWE 75%, index 62 for the max variant. The "Contributor" variant is cheap and VH on allowance, but no independent score for it exists.

## 5a. Outcome (final assignments, 2026-10-28)

Decisions taken after this mapping, with commits. The observations in section 5 below are the original reasoning and are kept as written; where they differ from this section, this section wins.

| Seat | Before | Now | Commit |
|---|---|---|---|
| Fallback targets (direct DeepSeek) | `max` | `high` | `63a0b83` |
| PM prompts (route marker, identifiers, commits) | none | discipline paragraph; tiny-fix marker only for a side fix | `86eae9a`, `b322c68` |
| Reliability lens (both copies) | minimax-m3.1-flash xhigh | claude-haiku-5-5 high | `3e2264d` |
| Validators (both copies) | claude-haiku-5-5 high | openai/gpt-6.1-sol high (review actors excluded from Astra aliases) | `3e2264d` |
| `advisor-integration-pre` | minimax-m3.1-flash | mimo-v2.6-flash | `3e2264d` |
| `advisor-integration-post`, `advisor-maintainability-pre` | qwen3.8-flash, minimax-m3.1-flash | glm-5.3-flash high | `3e2264d` |
| Verifier | gentle-ai-verify (Sol) only | `gentle-ai-verify-routine` (Haiku high) default, Sol for high-risk Risk lines | `4507394`, `2283c20` |
| PM seats | glm-5.3-flash high | muse-spark-1.3-contributor, no variant (after trial vs mimo-v2.6-flash) | `a129733`, `8f8bf48` |
| Refuter | grok-4.7 high | unchanged (owner) | `ac16dd4` |
| Six Luna `ce:review` personas | gpt-6-luna medium | glm-5.3-flash high | `b684fb7` |
| `performance`, `pattern-recognition`, `maintainability`, `agent-native` personas | deepseek-v4.1-flash | minimax-m3.1-flash high (independent family, recall-oriented, rare) | `46d3093` |
| `project-standards` persona | deepseek-v4.1-flash | mimo-v2.6-flash | `46d3093` |

Corrections made during the work:

- **Shared pools:** each provider is one shared pool, not a pool per model. Per-model limits and credits are relative weights, not separate allowances.
- **Registry:** Qwen 3.7 Plus, Grok 4.7, Muse Spark Contributor and MiniMax M3 are all on Command Code; the proxy registry gap was fixed in the proxy repo (`b179e97`).
- **Haiku validator:** the 137 failed Haiku calls came from another client, not the validator.
- **Refuter cost:** about $0.25 a call at about 5 calls a week, so a small cost, not a problem. It stays on Grok.
- **MiniMax M3.1 Flash:** it is a poor fit for high-volume seats (its Go limit is $20 and it emits about 5 times the tokens), and a good fit for rare, recall-oriented seats. The hang/session acceptance gate is cleared by the owner.
- **Argon:** stays the external advisor route.

Still open: the owner restart of `secure-opencode.service`; `general` and `planner-evidence` stay on Luna (the ChatGPT plan load is unmeasured); the three checklist `ce:review` personas stay on DeepSeek.

## 5. Observations on potential changes

Ordered by urgency, then by how much allowance or quality they affect. None is applied.

0. **Registry gap: four models are treated as Go-only but all are on Command Code (corrected by the owner, 2026-10-28).** The GOAT docs list Qwen 3.7 Plus ($33 credit), Grok 4.7 ($20), Muse Spark 1.3 Contributor ($20) and MiniMax M3 ($47). The proxy registry (`opencode-go-proxy/src/registry.jsonc`) gives `qwen3.7-plus`, `grok-4.7` and `muse-spark-1.3-contributor` no cc backend ("not in the routing brief"), and flags `minimax-m3` `prefer: go-only` although it already has a cc entry. With Go at 99% until 9 Nov, the seats using them (risk lens, refuter, readability lens, `jd-judge-b`, `advisor-design-post`, `advisor-security-post`, `correctness-reviewer`) cannot move to cc, and the lenses and advisors have no fallback, so they fail outright. First fix: add the cc backends (needs each model's cc catalogue `model_id`, protocol and ZDR setting; the cc side has caps and the tier boundaries differ from Go) and clear the `go-only` flag. Section 3 "Go only" notes for these models are stale until then.
1. **MiniMax M3.1 Flash is the costly outlier you suspected.** Same list price as DeepSeek flash, but Go gives it a $20 limit (4x the pool weight), it emits ~5x the tokens per request (3.8k vs 0.75k), and on cc the fitted weight is 3.46x its metered cost (+246% vs seed, only 8 fitted intervals, so noisy). Net per request: about **8x DeepSeek's Go-pool share and ~16x its cc share on observed metered cost** (about 10x on Go under the section 3 profile), plus the hallucination concern. It sits in 4 seats (reliability lens x2, integration-pre, maintainability-pre). Candidates: glm-5.3-flash or claude-haiku-5-5 for the advisors; for the reliability lens, a model with low hallucination (Haiku, Argon).
2. **`gentle-ai-verify` shares a model with `planner` (Sol high).** A difficulty-based split is feasible: routine verification (re-run authorized examples, check each `S#`, read the diff) needs reliable tool use rather than frontier reasoning, so a cheaper non-DeepSeek family fits (Haiku 5.5 high). Haiku only stays in its H allowance tier below 100k tokens of context; `gentle-ai-verify` averages ~70k today, but a long unit would cross it. Reserve Sol for the verifier on units that name a high-risk item. This needs a second verifier agent or a variant, and the dispatch rule in WORKFLOW.md.
3. **Review lenses: keep independent, but the lens seats are rare enough to afford better models.** About 100 messages a week against ~16k for everything else. The refuter is the exception on cost: ~$0.25 a call (~1.7% of the Go pool per call). The planned refuter, mimo-v2.6-flash, is VH but weak; Haiku (xhigh/max) is the middle path.
4. **Advisors: independence between advisors can drop.** Today there are 10 advisor seats on 6 models. Two models cover it: one strong seat for design and security (Sol, already unmetered) and one H-tier seat for integration/testing/maintainability. Tradeoffs: more Sol load lands on the ChatGPT plan we cannot see (observation 9), and the Planner (also Sol) would judge raw advice from its own model, which weakens the cross-check. The post-code advisors must still differ from the author's family (DeepSeek). That is a different constraint from advisor-vs-advisor independence, which is the one you are relaxing. `advisor-integration-post` is the busiest advisor (806 messages a week).
5. **Underused cheap capacity.** Muse Spark Contributor (227k docs req/mo), MiMo flash (150k) and LongCat-2.0 (57k) are almost idle. Beam Free and Iceman Contributor Free are unlimited. Candidates for explore/research/low-stakes review seats once quality is checked.
6. **Owner decision (2026-10-28): Gemini 4 Argon stays the external advisor route** (`advisor-gemini-*`), so it is not a candidate for verifier, lens or refuter seats. Remaining question is only where it is paid from: it is cheap on Go until 30 Nov (2,120 req/mo on Go vs paid Google credits for the `advisor-gemini-*` seats). `opencode-go/gemini-4-argon` is not defined in the provider block or the proxy registry yet.
7. **The Haiku validator has never been observed running.** `opencode.db` has no `review-validator` or `asi-review-validator` messages, so there is no evidence it works or fails. The 137 failed Haiku calls in the proxy log (HTTP 400, "protocol mismatch: claude-haiku-5-5 is `an` but was called on /chat/completions") have an empty agent field and went to `/chat/completions`, while our provider block uses `@ai-sdk/anthropic` (`/messages`). The registry note says Haiku traffic on that endpoint comes from OpenChamber, so they are probably another client. Worth one dry run of the validator seat before relying on it.
8. **Fallback erodes independence.** Any Go/ChatGPT exhaustion collapses every role to DeepSeek. With Go at 99% this is live now.
9. **ChatGPT OAuth is a blind spot.** Sol and Luna carry ~4.6k messages a week at zero metered cost, but we cannot see that plan's limits. Moving routine Luna work (`general` tiny fixes) to a VH Go/cc model would free it, at the price of the DeepSeek-family conflict in WORKFLOW.md.
10. **`systematic-implementer` is DeepSeek flash at xhigh**, while `odd-apply` runs default; check xhigh exists for that model before relying on it.
11. **Change cost:** independence rules are enforced by `tests/test_model_independence.py` and `verify-workflow.sh`. Any reassignment needs the tests, `WORKFLOW.md` tables and the `VERIFY_SCRIPT_SHA256` pin updated in the same change.

Not yet done: no quality benchmark of our own, so seat-level choices rest on public numbers; the cc fitted weights for newer models are based on few intervals.

## Sources

- <https://opencode.ai/docs/go/>, <https://commandcode.ai/docs/plans/goat>
- <https://artificialanalysis.ai/leaderboards/models>, <https://x.com/ArtificialAnlys/status/2112211865128608002>
- <https://venturebeat.com/technology/minimaxs-new-m3-1-flash-beats-deepseek-and-opus-5-on-a-key-business-benchmark-at-lower-cost-but-with-a-high-hallucination-rate>
- <https://arxiv.org/pdf/2609.19969>, <https://qubrid.com/blog/glm-53-flash-benchmarks-official-and-independent-results>
- <https://kingy.ai/blog/claude-haiku-5-5-benchmarks-specs-sol-luna/>, <https://benchlm.ai/benchmarks/terminal-bench-4>
- <https://www.eesel.ai/blog/muse-spark-1-3>, <https://www.mindstudio.ai/blog/qwen-3-8-flash-next-benchmarks>
- <https://www.buildfastwithai.com/blogs/kimi-k2-7-code-review-2026>
