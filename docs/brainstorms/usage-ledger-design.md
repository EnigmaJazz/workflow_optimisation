# Usage ledger design and baseline

Status: **Ledger built (commit `4f1b338`); baseline and threshold calibration pending.**

This is a description and operating procedure for the existing implementation, not a proposal to rebuild it.

## 1. Feasibility first: what cannot be measured

A local usage ledger is not a provider quota meter. Feasibility is therefore a measured-use estimate against known limits where available, and explicitly low-confidence or unknown-ceiling elsewhere.

| Measurement gap | Why it matters | Feasibility consequence |
|---|---|---|
| Provider quota state and reset windows are not locally readable: Claude plan 5-hour/weekly windows, ChatGPT/Codex plan, and Antigravity. | Local token/call totals do not reveal remaining shared allowance or exact reset time. | No exact remaining-quota estimate; use documented ceiling only where one exists, otherwise report unknown ceiling and approved provisional cap. |
| Claude's script-defined 5-hour window is derived from request timestamps per session. | It is not the provider's rolling window shared across sessions, nor evidence of the actual plan boundary. | Treat reported windows as a session-level proxy, not account quota state. Weekly allowance is not measured. |
| OpenAI Sol/Luna seats served through ChatGPT OAuth inside OpenCode do not pass through the Go proxy. | `ingest-opencode` only sees proxy `requests`; these OAuth calls do not appear there. | Their usage is absent unless another supported source is chosen; do not report zero. |
| Antigravity has no local meter and is count-only by design. | Owner-reported calls have no token estimate. | Track calls, not token feasibility; mark confidence low and ceiling unknown unless an owner-approved cap exists. |
| Jev/TypeSafe usage is not in any local log. | No automatic ingestion path is observed. | Record each call manually or accept an explicit gap; S8 needs a ledger entry. |
| Enforcement is after the fact: spend is recorded when the call completes. | A long or runaway call may cross a limit before the ledger sees its completed usage. | `check` is a warning/routing aid, not a preventive quota control or hard stop. |

## 2. Subscription sources and confidence

Observed source formats below come from the existing `scripts/usage_ledger.py`; measured fields are locally recorded usage, not provider quota state.

| Subscription / seats | Source | Measured fields | Not measurable from this source | Confidence |
|---|---|---|---|---|
| Claude Code: Tiers 1, 2, 2s | `~/.claude/projects/**/*.jsonl`; assistant `message.usage` | Input, output, cache-read, cache-creation tokens; session, model, cwd/project, timestamp. `usage.iterations[]` entries of type `advisor_message` add advisor tokens. | Shared plan quota, actual rolling 5-hour/weekly reset state. | Medium for logged calls; low for plan feasibility. |
| OpenAI Codex/ChatGPT: Tier 4 and Planner/Luna seats | Codex `~/.codex/sessions` JSONL: `session_meta`, `turn_context`, `token_count` with `total_token_usage` and `last_token_usage`. | Codex last-turn input/output/cache-write; cached input is subtracted from input and recorded as cache-read; session, cwd, model. Tier attribution can be configured. | ChatGPT/Codex plan quota/reset; Sol/Luna OAuth calls not sent through the Go proxy. | Medium for Codex logs; low/incomplete for OAuth seats and plan feasibility. |
| Google Antigravity: Tier 3 | Manual `record` entry per owner-reported use. | Calls; optional tier and metadata. | Tokens and provider quota/reset. | Low; count-only. |
| OpenCode Go pool + proxy: Tier 5 | Proxy SQLite `requests`; `opencode.db` session → directory lookup. | Calls; `fresh_in`, `cache_read`, `cache_write`, output; backend, model, agent, session, project. | Provider-side quota not otherwise represented in proxy rows; OAuth sessions outside proxy. | High for proxy-observed traffic; not a full OpenCode/plan meter. |
| TypeSafe Jev | Manual `record`; no local Jev log observed. | Calls and any manually supplied token fields. | Automatic call discovery and provider quota. | Low until ingestion evidence exists. |
| Advisor calls | Claude assistant usage `iterations[]` with `type: advisor_message`; TypeSafe advisor calls require manual record if applicable. | Claude advisor input/output/cache fields, stored as `kind=advisor`; manual records can include calls/tokens. | Provider allowance and any advisor route absent from these sources. | Medium for Claude logged advisor usage; low for manual entries. |

## 3. Ledger format as built

Observed implementation: SQLite at `$USAGE_LEDGER_DB`, default `~/.local/state/usage-ledger/ledger.sqlite`. One `usage` table uses primary key `(source, key)` and columns `source`, `key`, `ts`, `subscription`, `tier`, `kind` (default `usage`), `session`, `model`, `project`, `stage`, `calls`, `input`, `output`, `cache_read`, and `cache_write`.

`INSERT OR REPLACE` makes re-ingestion idempotent and lets a later streaming partial replace the earlier row with the same key. The ledger stores counts, not message content. `tests/test_usage_ledger.py` uses a secret fixture and asserts it never appears in CLI output; the implementation only maps usage metadata into rows.

**Definition gap:** `ingest-opencode` writes the proxy `agent` column into ledger `stage`. Thus `stage` currently means the OpenCode agent for those rows, not a workflow/staging stage. Do not interpret it as a true stage until that mapping is changed or documented differently.

## 4. Repository ownership, attribution, and configuration (D25, OPEN-14, S1)

Observed repository artifacts: implementation `scripts/usage_ledger.py`, placeholder `scripts/usage-ledger.example.json`, tests `tests/test_usage_ledger.py`. The task tracker records T1 built at commit `4f1b338`, with S1-S8 implemented; S9 needs a measured day and thresholds remain placeholders.

Interpret D25 as the code, schema, config, and derived baseline artifacts living in `workflow_optimisation`; the mutable runtime SQLite database does not. Keep the live DB in host state: it is a mutable binary, may grow, and can contain private usage metadata. Proposed committed outputs under `docs/usage/`: a concise Markdown summary and a TSV produced from `report`, never the SQLite DB.

Attribution behavior observed: an explicit `--tier` on ingestion/record wins. Otherwise `tier_map` uses the first matching entry by project prefix, subscription, and/or model; unmatched rows become `unattributed`. The example config has ordered `tier_map` entries and `thresholds` per subscription. Each threshold defines `unit` (`tokens` or `calls`), `window_hours`, positive `limit`, `downgrade_at`, and `skip_tier3_at`; validation requires `0 < downgrade_at <= skip_tier3_at <= 1`.

## 5. One-day baseline procedure (one day per subscription)

Use a separate DB for the baseline run, preserving the live DB. The example uses 2026-11-09; replace the date only when selecting the actual measurement day. These commands use the CLI's implemented flags and Fish syntax.

1. Select the baseline DB and retain the exact date and timezone in the artifact:

   ```fish
   set -x USAGE_LEDGER_DB ~/.local/state/usage-ledger/baseline-2026-11-09.sqlite
   ```

2. Ingest available local sources for the chosen day. Ingestors may read historical files, so filter the output by the exact day when reporting; use tier maps or source-specific roots to avoid assigning a mixed root one tier.

   ```fish
   python3 scripts/usage_ledger.py ingest-claude --root ~/.claude/projects
   python3 scripts/usage_ledger.py ingest-codex --root ~/.codex/sessions
   python3 scripts/usage_ledger.py ingest-opencode --proxy ~/.local/state/opencode-go-proxy/proxy.sqlite --opencode-db ~/.local/share/opencode/opencode.db
   ```

3. Record every Antigravity use and every manual/TypeSafe call. Example syntax (replace values with observed metadata):

   ```fish
   python3 scripts/usage_ledger.py record --subscription google --tier 3 --kind usage --calls 1 --project workflow_optimisation --stage owner-reported
   python3 scripts/usage_ledger.py record --subscription typesafe --tier 2 --kind jev --calls 1 --input 1200 --output 80 --project workflow_optimisation
   ```

   The implemented record flags are `--subscription` (required), and optional `--tier`, `--ts`, `--kind`, `--session`, `--model`, `--project`, `--stage`, `--calls`, `--input`, and `--output`. If `--ts` is omitted, the current UTC time is used; specify timestamps that fall within the baseline day.

4. Produce day totals and the Claude session-window view. Capture report output as a TSV artifact; the command itself writes tab-separated rows to stdout.

   ```fish
   python3 scripts/usage_ledger.py report --config scripts/usage-ledger.example.json --day 2026-11-09
   python3 scripts/usage_ledger.py report --config scripts/usage-ledger.example.json --day 2026-11-09 --window-hours 5
   ```

   `report` accepts `--config`, `--day`, `--project`, `--stage`, and `--window-hours`. It groups daily output by day/subscription/tier and prints Claude windows separately. Record the observed totals per subscription and tier, including counts, input/output and cache fields; note that the output does not itself label `kind`.

5. For each subscription, calculate used / known documented limit only where the limit and matching window are documented. Otherwise write **unknown ceiling**, confidence, and any owner-approved conservative cap; do not present the cap as a provider limit. Include the gaps from §1 that affected this day, including missing OAuth seats, absent TypeSafe/Antigravity tokens, and the per-session Claude-window caveat.

6. Run `check` only against an owner-reviewed config; example values are placeholders. Record the exit code and output. `check --config <path>` returns 0 for ok, 1 for downgrade-model, 2 for skip-tier3, and 3 for bad config. For `unit: tokens`, it sums input + output only; cache-read/write are excluded. For `unit: calls`, it sums calls.

7. Write the derived Markdown summary and TSV under `docs/usage/`, with date, scope, source coverage, calculations, confidence, gaps, and config revision. Commit only those derived artifacts; keep the DB in host state.

**Minimum Markdown artifact fields:**

| Field | What to record |
|---|---|
| Measurement window | Local timezone, UTC offset, start/end, and selected day. |
| Coverage | Each source ingested, root/database path class, and missing source. Never publish credentials or private paths unnecessarily. |
| Attribution | Tier rule used for each row group; list unmatched `unattributed` totals separately. |
| Totals | Subscription, tier, calls, input, output, cache-read, cache-write; retain the raw TSV alongside. |
| Feasibility | Used amount, ceiling and window if documented, ratio, confidence, or `unknown ceiling`. |
| Decisions | Approved provisional caps, approver, threshold config revision, and unresolved gaps. |
| Privacy | Confirm output contains only derived counts and metadata, not prompts, responses, or secrets. |

Before interpreting totals, check that the selected day is represented in each source's timestamps and that every manually recorded call has an explicit timestamp. A blank subscription/tier total means no rows were observed, not zero provider usage. Keep distinct source coverage and actual zero-use findings distinct.

The ledger does not provide a day argument to ingestion; day filtering happens in `report`. The report groups by subscription/tier but not by `kind`, so include the advisor/JeV classifications as contextual notes or inspect them through an approved derived reporting method without committing the raw DB.

Implemented CLI forms: `ingest-claude [--root]`, `ingest-codex [--root]`, `ingest-opencode [--proxy --opencode-db]`, `record --subscription ... [--tier --ts --kind --session --model --project --stage --calls --input --output]`, `report [--config --day --project --stage --window-hours]`, and `check --config`.

**Baseline coverage map:**

| Subscription slice | Collection action | Attribution / caveat |
|---|---|---|
| Claude Tiers 1, 2, 2s | Ingest Claude JSONL once for the selected source root. | Use source-specific roots or first-match project-prefix mappings; do not stamp a mixed tree with one tier. |
| Claude advisors | Same Claude ingest. | `advisor_message` is a separate `kind=advisor` row under Claude; report totals aggregate kinds. |
| Codex Tier 4 | Ingest Codex session JSONL. | Use explicit `--tier` only if the root contains one tier; otherwise map project/model. |
| OpenAI Planner/Luna | No proxy ingestion for ChatGPT OAuth sessions. | Report the blind spot; do not fabricate a manual token estimate. |
| Antigravity Tier 3 | Manual `record` for every owner-reported use. | `calls` only unless an observed token measurement exists. |
| OpenCode Go/proxy Tier 5 | Ingest proxy rows and session-directory mapping. | Backend determines the subscription value; `stage` contains agent name. |
| Jev / TypeSafe | Manual `record` for each call. | Include measured fields only; no automatic source currently exists. |

A baseline is complete only when every subscription row has either measured totals or a specific “not measurable” entry, plus a confidence statement. An empty row is not evidence that a subscription was unused.

## 6. Threshold calibration (S10-S11)

The example config's numeric limits and fractions are placeholders, not measured values. Calibrate `limit` from a provider-documented ceiling when one exists and its window matches the ledger. Otherwise the measured day is a lower bound on observed use, not a ceiling; label any provisional limit as an owner-approved conservative cap with low confidence.

Choose `downgrade_at` and `skip_tier3_at` so a normal day remains below both and a runaway day crosses the intended threshold. Test both threshold transitions before relying on them. Prefer several representative days, including peak usage, before fixing numbers. One day is the S9 minimum and a useful baseline, not the ideal calibration set. `check` observes completed usage and cannot prevent an in-flight call from exceeding a limit.

| Calibration case | Expected result |
|---|---|
| Usage below downgrade fraction | `ok` (exit 0). |
| Usage at/above downgrade fraction but below skip fraction | `downgrade-model` (exit 1). |
| Usage at/above skip fraction | `skip-tier3` (exit 2). |
| Invalid units, limits, windows, or fractions | Bad config (exit 3). |

Test using a disposable DB and controlled recorded rows; do not alter the live DB or rely on a real provider limit crossing. For token thresholds, cached tokens do not contribute to `check`'s numerator, so compare the test's input + output with the expected fraction explicitly.

Threshold approval should occur only after the baseline artifact is reviewed:

1. Confirm source coverage and tier attribution, including every `unattributed` row.
2. Record any provider-documented ceiling with its source and matching reset window.
3. Separate measured values from estimates, caps, and unobserved usage.
4. Choose provisional downgrade/skip fractions and identify the owner approving them.
5. Exercise all `check` states in a disposable DB and verify exit codes.
6. Review whether a normal and a high-use day produce sensible routing states.
7. Publish the approved config change separately from baseline evidence; retain its revision in the artifact.

Do not use an `ok` result as proof that quota remains. It means only that recorded rows are below the configured limit in the configured window.

## 7. Known gaps and decisions needed

| Decision | Required owner choice |
|---|---|
| OAuth-served OpenCode models | Add an ingestion path from `opencode.db`, or accept and disclose the Sol/Luna blind spot. `opencode.db` message/token fields are not currently consumed by the ledger. |
| Claude windows | Keep the current per-session five-hour model, or design a provider-wide/account-level approximation; provider quota state remains unreadable either way. |
| TypeSafe/Jev | Define a supported ingestion path or retain manual `record` entries and accept omission risk. |
| Antigravity | Accept count-only feasibility or select an owner-approved proxy/cap; the ledger has no local token meter. |
| Live DB policy | Confirm that the runtime DB is never committed (recommended: no, keep only derived artifacts). |
| Baseline duration | One day minimum or three/multiple representative days before threshold approval. |
| `stage` semantics | Rename or derive a workflow stage, or document that OpenCode ingestion currently stores agent name there. |
| Threshold authority | Name who approves limits, downgrade/skip fractions, and any conservative cap. |
