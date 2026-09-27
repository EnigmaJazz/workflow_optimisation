# CLAIM-RETRACTIONS — rejected agent claims and what caught them

One row per claim an agent reported and then had to retract. Purpose: make claim
drift measurable across sessions instead of felt. Governing rules live in the
evidence-discipline block of the global `AGENTS.md`: absence claims need a stated
search plus a positive control, mechanism claims need a differential, and every
factual statement is labelled `observed`, `inferred` or `assumed`.

## Columns

| Column | Meaning |
|---|---|
| Date | When the claim was retracted |
| Project | Where the work happened |
| Kind | `absence` (missing/reverted/not installed/not live), `mechanism` (a named cause), or `other` |
| Claim as reported | The claim, as the agent actually stated it |
| What caught it | The observation that falsified it |
| Instrument that would have caught it first | The approval-free tool or single question that should have preceded the claim |
| Source | `owner report` or `agent observed` — never upgrade an owner report into an agent observation |

## Measurement

Count rows per session and per project. The acceptance test for the
evidence-discipline rules is that the rate of retracted claims declines across
subsequent sessions. A row exists only when an agent withdraws or corrects a
claim it previously reported; near-misses caught before reporting are not rows.

## Entries

| Date | Project | Kind | Claim as reported | What caught it | Instrument that would have caught it first | Source |
|---|---|---|---|---|---|---|
| 2026-09-25 | approval-metadata work | absence | An approval-metadata fix "was reverted / never installed" | Reading the builder showed the code is `...input.details`; the search pattern `\.\.\.details` could not match it | `aft_zoom` on the builder, one call | owner report |
| 2026-09-25 | approval-metadata work | absence | "No approval occurred at all" | A prompt had fired and rendered only `*`; nobody asked what it displayed | Asking the user what the prompt displayed | owner report |
| 2026-09-25 | session export work | mechanism | "The state GC pruned the bundle" | The bundle had never been written; the directory was empty | A directory listing before making a causal claim | owner report |
| 2026-09-25 | newly installed host tool | absence | "A new session is required" to use the tool | It worked in-session | Trying the tool once | owner report |
| 2026-09-25 | model/provider call | mechanism | Credential failure, read from the literal text "Incorrect API key provided" | A provider outage explained it; the error string was treated as the root cause | Treating an error string as a symptom, and probing before naming a cause | owner report |
| 2026-09-25 | evidence-discipline change | mechanism | "The key has been rotated or revoked", and every gpt-pinned agent was unusable | The owner reported a global provider outage | Label the inference `inferred` instead of presenting it as a finding | agent observed |

## Adding a row

Append below the last entry, keep the column order, and add the row in the same
change that records the task in `ROUTER-LOG.md`. Never rewrite an earlier row to
read better; a retraction that was itself wrong stays visible.
