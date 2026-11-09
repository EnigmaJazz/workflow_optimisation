# OPEN-6 provider-terms review (evidence for owner decision)

Evidence only. Not legal advice. The owner decides and signs (section 6). A silent clause is not permission.

## 0 Provenance

- Retrieved: 2026-11-09, by an agent using WebSearch (extended) and WebFetch on provider-owned pages, plus `curl` status checks.
- Caveat on quotes: WebFetch returns text extracted by a small model, not raw HTML. Quotes below are what it returned from the page; several are split fragments of one sentence. The owner should open each URL and confirm the quote before signing. Quotes marked `[search-summary]` come only from a search-result summary and are leads, not quotes.
- Uses: U1 unattended/24-7 runs; U2 agent/orchestrator directing the vendor CLI; U3 several concurrent sessions on one login; U4 subscription login inside a third-party harness; U5 moving/sharing login credentials between hosts or sandboxes.
- Could not retrieve (HTTP 403 to WebFetch and curl): OpenAI Terms of Use (`https://openai.com/policies/row-terms-of-use/`, `https://openai.com/policies/terms-of-use/`); OpenAI Sign in with ChatGPT Terms (`https://openai.com/policies/sign-in-with-chatgpt-terms/`); OpenAI help articles 11369540 and 20001542; Anthropic Commercial Terms (`https://www.anthropic.com/legal/commercial-terms`, 403 first time; only a partial summary returned on a retry within the same run, treated as not retrieved for quoting); Anthropic help article 11145838 returned no automation text.
- Not retrieved at all: Gemini CLI headless/automation docs (authentication.md returned 404); Google One AI Pro additional terms; Gemini API Terms; OpenCode Go, DeepSeek, OpenRouter terms: **not reviewed**.
- Date oddity: the Anthropic Usage Policy page showed effective date "Nov 12, 2026", three days after today. Treat as a pending or future-dated version; confirm which version is in force.

## 1 One-page summary (provider x use, subscription login)

Labels: PROHIBITS / PERMITS EXPRESSLY / SILENT / AMBIGUOUS / COULD NOT RETRIEVE.

| Provider | U1 unattended | U2 agent directs CLI | U3 concurrent, one login | U4 third-party harness | U5 move/share creds |
|---|---|---|---|---|---|
| Anthropic | AMBIGUOUS | AMBIGUOUS | SILENT | AMBIGUOUS (leans PROHIBITS) | AMBIGUOUS |
| OpenAI | AMBIGUOUS (Codex docs); ToU COULD NOT RETRIEVE | SILENT in Codex docs; ToU COULD NOT RETRIEVE | SILENT in Codex docs; ToU COULD NOT RETRIEVE | AMBIGUOUS (PERMITS EXPRESSLY only via Sign in with ChatGPT for participating apps) | PERMITS EXPRESSLY (own auth.json to a headless host), with a password warning |
| Google | SILENT | AMBIGUOUS (leans PROHIBITS where a third-party tool drives it) | SILENT | PROHIBITS | SILENT |

API keys (brief): Anthropic and OpenAI both point automation at API keys. Anthropic consumer terms exempt "an Anthropic API Key"; Codex docs say "API keys are still the recommended default for automation." Google: Gemini API key use is governed by the Gemini API Terms (not retrieved). Lower risk, not reviewed in depth.

## 2 Per-provider evidence

### 2.1 Anthropic

Sources:
- A1 Consumer Terms of Service, `https://www.anthropic.com/legal/consumer-terms`, effective "Oct 8, 2025" (no "last updated").
- A2 Claude Code "Legal and compliance", `https://code.claude.com/docs/en/legal-and-compliance`, no date shown.
- A3 Claude Code "Authentication", `https://code.claude.com/docs/en/authentication`, no date shown.
- A4 Claude Code "Run Claude Code programmatically", `https://code.claude.com/docs/en/headless`, no date shown.
- A5 Usage Policy, `https://www.anthropic.com/legal/aup`, effective "Nov 12, 2026".

| Use | Label | Quote and source |
|---|---|---|
| U1 | AMBIGUOUS | A1 s3: "Except when you are accessing our Services via an Anthropic API Key or where we otherwise explicitly permit it," ... "to access the Services through automated or non-human means, whether through a bot, script, or otherwise." Against that, A4 documents scripts and CI: "It's available as a CLI for scripts and CI/CD" and A3: "CLAUDE_CODE_OAUTH_TOKEN ... Use this for CI pipelines and scripts where browser login isn't available." A3 also: "This token authenticates with your Claude subscription and requires a Pro, Max, Ultra, Team, or Enterprise plan." Whether the docs are the "explicitly permit" exception is a reading, not a statement. A2: "Advertised usage limits for Pro, Max, and Ultra plans assume ordinary, individual usage of Claude Code and the Agent SDK." 24/7 operation is not addressed. |
| U2 | AMBIGUOUS | A4 describes programmatic prompting of the CLI (`claude -p`) and the Agent SDK. A2: "Developers building products or services that interact with Claude's capabilities, including those using the Agent SDK, should use API key authentication through Claude Console or a supported cloud provider." "Should", not "must not". A1 bot/script clause above also applies. No sentence addresses one AI agent directing another. |
| U3 | SILENT | No sentence on concurrency found. Related: A2 "assume ordinary, individual usage"; support article (`https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan`, "Updated over a week ago"): "These limits are shared across Claude and Claude Code, meaning all activity in both tools counts against the same limits." A1 s2: "You may not share your Account login information, Anthropic API key, or Account credentials with anyone else" and "or make your Account available to anyone else" (concerns other people, not your own agents). |
| U4 | AMBIGUOUS (leans PROHIBITS) | A2: "OAuth authentication is intended exclusively for purchasers of Claude Free, Pro, Max, Ultra, Team, and Enterprise subscription plans and is designed to support ordinary use of Claude Code and other native Anthropic applications." and "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications, or to route requests through Free, Pro, Max, or Ultra plan credentials on behalf of their users." and "developers may not collect, store, or intermediate Claude.ai credentials or session tokens". Also: "Anthropic reserves the right to take measures to enforce these restrictions and may do so without prior notice." The sentences target third-party developers acting for users; they do not name an individual running OpenCode on their own login. News reports (leads only, not citations; not verified against Anthropic text) describe a Feb 2026 version saying OAuth tokens may not be used in "any other product, tool, or service"; the fetched current page does not contain that wording. |
| U5 | AMBIGUOUS | A3: "set it as the CLAUDE_CODE_OAUTH_TOKEN environment variable wherever you want to authenticate" (own token, own environments). A2 permits "an end user from signing in to the unmodified Claude Code binary with their own Claude subscription, including where a platform hosts Claude Code". But A2 also: "developers may not collect, store, or intermediate Claude.ai credentials or session tokens — sign-in to a Claude account must complete through Anthropic's own flow", and "The Claude Code binary must not be modified." A platform that copies or stores the login file for a user is the case the owner must judge. |

Other: A5 (AUP) has "Agentic use cases must comply with the Usage Policy." and "Utilize automation in account creation or to engage in spammy behavior"; no ban on agent-directed use as such. Commercial Terms: COULD NOT RETRIEVE reliably.

### 2.2 OpenAI

Sources:
- O1 Codex "Authentication", `https://developers.openai.com/codex/auth` (308 redirect to `https://learn.chatgpt.com/docs/auth`), no date shown.
- O2 Codex pricing, `https://learn.chatgpt.com/docs/pricing`, no date shown.
- O3 Sign in with ChatGPT, open-source apps, `https://developers.openai.com/siwc/token-sharing-open-source`, no date shown.
- O4 Terms of Use: COULD NOT RETRIEVE (403). Search summary only `[search-summary]`: consumer terms bar "automatically or programmatically extract data or Output" and "share your account credentials or make your account available to anyone else". Verify on the live page; the exact current wording and regional version (ROW/EU) are unconfirmed.

| Use | Label | Quote and source |
|---|---|---|
| U1 | AMBIGUOUS | O1: "Use API key authentication for programmatic Codex CLI workflows, such as CI/CD jobs." and "API keys are still the recommended default for automation." and "Access tokens are intended for trusted scripts, schedulers, and private CI runners." Recommendation, not a prohibition; the ChatGPT-login case for unattended runs is not addressed. O4 programmatic-extraction clause unconfirmed. |
| U2 | SILENT (docs); ToU COULD NOT RETRIEVE | No sentence on one agent directing the Codex CLI. |
| U3 | SILENT (docs); ToU COULD NOT RETRIEVE | O2: "Local messages and cloud chats share your plan's usage allowance." and "Usage limits are shared with other agentic features once pricing for those features is effective." No concurrency limit stated. Paperclip's own docs recommend per-agent API keys for high-concurrency fleets (technical advice, see paperclip-readme-review.md 3H). |
| U4 | AMBIGUOUS | O3: "can request permission to use the user's ChatGPT plan for eligible Responses API requests." That is an OpenAI-sanctioned route for open-source apps that register; it is not a statement that extracting the Codex CLI's login for another harness is allowed. That OpenCode is a launch partner is from secondary press only (The New Stack, search summary): unverified against OpenAI. Sign in with ChatGPT Terms (anti-pooling/anti-resale, per search summary only) COULD NOT RETRIEVE. A secondary blog argues the ToU are silent on this; lead only. |
| U5 | PERMITS EXPRESSLY (own auth.json to headless host) | O1: describes copying `~/.codex/auth.json` from a logged-in machine to a headless machine (SSH and Docker examples), and: "Treat `~/.codex/auth.json` like a password: it contains access tokens." and "Don't commit it, paste it into tickets, or share it in chat." Applies to the user's own hosts; ToU credential-sharing clause (O4) unconfirmed. |

### 2.3 Google

Sources:
- G1 Google Antigravity Additional Terms of Service, `https://antigravity.google/terms`, no effective date shown.
- G2 Gemini CLI "Terms of Service and Privacy Notice", `https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/tos-privacy.md`, no date shown (GitHub docs, `main`).
- G3 Gemini CLI maintainer announcement, `https://github.com/google-gemini/gemini-cli/discussions/20632`, 2026-02-27, author jackwotherspoon (project maintainer; vendor-employee statement, label as such).
- G4 Gemini CLI quota and pricing, `https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/quota-and-pricing.md`, no date shown.
- G5 Google Terms of Service, `https://policies.google.com/terms`, "Effective July 30, 2026".

| Use | Label | Quote and source |
|---|---|---|
| U1 | SILENT | G4 does not address automation, headless or CI. G1 s4 contemplates agents: "perform actions or tasks on your behalf in a supervised or autonomous manner that you may create, orchestrate, or initiate within the Service" (agents inside the product). G5: prohibits "using automated means to access content from any of our services in violation of the machine-readable instructions" (robots.txt context only). |
| U2 | AMBIGUOUS (leans PROHIBITS) | G1 s6: "Using third party software, tools, or services to access the Service (e.g. using OpenClaw with Antigravity OAuth) is a breach of this Agreement." An orchestrator that drives the CLI is arguably a third-party tool; the clause does not name vendor-CLI-driven-by-agent. G1 s4 also says the user is "solely responsible for ... exercising judgment and supervision when and if an AI Agent is used in production environments". |
| U3 | SILENT | No account-sharing, multi-session or circumvention clause in G1 (tool reported none). G3 refers to users acknowledging "bypassing system measures or circumventing usage limits is prohibited" (vendor-employee statement). G4: "Requests are limited per user per minute and are subject to the availability of the service in times of high demand." |
| U4 | PROHIBITS | G1 s6 (above), plus: "Such actions may be grounds for suspension or termination of your Antigravity and/or Gemini CLI accounts." G2: "using third-party software, tools, or services" ... "is a violation of applicable terms and policies" ... "Such actions may be grounds for suspension or termination of your account." (fragments). G3 (maintainer): "Using third-party software, tools, or services to harvest or piggyback on Gemini CLI's OAuth authentication to access our backend services is a direct violation of Gemini CLI's applicable terms and policies." |
| U5 | SILENT | No sentence on moving credentials. G3 prohibits "harvest[ing]" the OAuth authentication via third-party tools, which a managed sandbox that copies the auth file could be read as. Not a direct quote on file copying. |

Note: Google forum staff gave conflicting answers on whether a personal sign-in may be used with a named third-party agent (Oct 26 versus Oct 30 replies, Google AI Developers Forum; seen only in a search summary, not fetched). Enforcement reports (403 PERMISSION_DENIED, bans) are user reports and not cited.

### 2.4 Others

OpenCode Go, DeepSeek, OpenRouter: **not reviewed**.

## 3 Check of the owner's belief ("only Google prohibits direction of its tools by another agent")

Verdict: **PARTLY SUPPORTED; NOT SUPPORTED as worded.**

- Supported in part: Google alone has a short, express, example-bearing prohibition on third-party tools accessing the service (G1 s6, G3). No provider's retrieved text expressly bans "agent directing agent" as such.
- Contradicted by Anthropic: A1 s3 bars access "through automated or non-human means, whether through a bot, script, or otherwise" unless via an API key or "where we otherwise explicitly permit it". A2 says third-party developers may not "route requests through Free, Pro, Max, or Ultra plan credentials on behalf of their users" and may not "collect, store, or intermediate Claude.ai credentials or session tokens". These cover U1, U4 and arguably U5 for Anthropic. Anthropic's own docs also document scripted use (A3, A4), so the position is ambiguous, not clear permission.
- OpenAI: unconfirmed. The Terms of Use could not be retrieved; Codex docs recommend API keys for automation but do not prohibit subscription use; OpenAI has a sanctioned partner route (O3).
- A silent clause is not permission: Google U1/U3/U5, OpenAI U2/U3, Anthropic U3 are SILENT, not allowed.

## 4 Ambiguities and what to ask each vendor

- Anthropic: (a) Do the `claude -p` and `setup-token` docs count as "where we otherwise explicitly permit it" for subscription logins in unattended scripts, including 24/7? (b) Does an orchestrator that launches the unmodified `claude` binary with the owner's own login count as "ordinary, individual usage"? (c) Is an individual running OpenCode on their own Claude login inside A2's "third-party developers" restriction? (d) Is copying the owner's own login or token into a sandbox a prohibited "collect, store, or intermediate"? (e) Which Usage Policy version applies (effective date Nov 12, 2026)? Route: contact sales (A2 gives this path).
- OpenAI: (a) Current Terms of Use text on programmatic use and credential sharing (not retrieved). (b) Is unattended, concurrent use of the Codex CLI on a ChatGPT login allowed when API keys are only "recommended"? (c) Is OpenCode using the Sign in with ChatGPT route, or an extracted Codex login, in the owner's setup? (d) Sign in with ChatGPT Terms on pooling.
- Google: (a) Is an orchestrator launching the official Gemini CLI binary (headless) a "third party software, tool, or service" under G1 s6 / G2? (b) Do Gemini CLI headless/CI runs on a personal Google login have a stated allowance? (c) Which Gemini subscription terms govern a Google AI Pro login in the CLI (G2 names "Google One Additional Terms of Service", not retrieved).

## 5 Limits

Terms change often: Anthropic's policy text appears to have changed in 2026 and one policy page is future-dated. This is a snapshot as of 2026-11-09, extracted by a model and not verified against raw HTML. Several key OpenAI documents were not retrievable. Enforcement behaviour can differ from text. Not legal advice; contract interpretation is for the owner or counsel.

## 6 Decision record (owner to complete; not filled by the agent)

| Provider | Use | Decision (permit / forbid / ask vendor / use API key) | Conditions |
|---|---|---|---|
| Anthropic | U1 | | |
| Anthropic | U2 | | |
| Anthropic | U3 | | |
| Anthropic | U4 | | |
| Anthropic | U5 | | |
| OpenAI | U1 | | |
| OpenAI | U2 | | |
| OpenAI | U3 | | |
| OpenAI | U4 | | |
| OpenAI | U5 | | |
| Google | U1 | | |
| Google | U2 | | |
| Google | U3 | | |
| Google | U4 | | |
| Google | U5 | | |

Owner statement (given in chat, 2026-11-09, recorded verbatim by the coordinator in place of a handwritten signature):

> "I am happy to sign off on use of agents in the proposed setup with the planned exception that all interaction with antigravity is directly user driven"

Recorded meaning:
- Sign-off covers agent use in the proposed setup, for Anthropic and OpenAI, as reviewed above.
- Exception: all Antigravity (Google) interaction is directly user-driven. No agent, orchestrator or script drives it (Google U1, U2, U4 are therefore forbidden for agent-driven use).
- The per-row table above was not filled in. The AMBIGUOUS and SILENT cells in sections 1 and 2 remain unresolved readings; this sign-off accepts the risk, it does not clear them. The section 4 vendor questions remain open if the owner wants certainty.
- The Anthropic Usage Policy version question (effective Nov 12, 2026) and the unretrieved OpenAI Terms of Use are not resolved by this sign-off.

Signature: recorded by chat approval, not handwritten.  Date: 2026-11-09
