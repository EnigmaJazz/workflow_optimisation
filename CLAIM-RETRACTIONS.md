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
| 2026-09-27 | workflow_optimisation | other | That an RDD assessment run with `baseRef=d39a679` had been **confirmed** to cover the last commit `4b79a30` | Git showed `d39a679` carries *identical* stats to `4b79a30` — 2 files, 3 insertions — so the matching counts the claim rested on could not distinguish the two commits; coverage was only established afterwards by the base-ref differential (`baseRef=4b79a30` returning `0 paths / 0 lines`, proving HEAD) combined with the parent link (`4b79a30^ = d39a679`) | Confirm the parent commit and run the empty-range differential probe *before* claiming confirmation — or label the claim `inferred` from counts alone | owner report |
| 2026-09-27 | workflow_optimisation | other | That assessing with `baseRef=<previous commit>` satisfied the per-commit RDD checkpoint requirement | The documented form takes the last REVIEWED BOUNDARY, not the previous commit; a one-commit window is always `under_budget`, so use of the previous commit as the base made `review_due` unreachable and the checkpoint never fired | Re-read the documented base-ref form before claiming the checkpoint was satisfied; and record the reviewed boundary with the work unit so the next assessment can pass it | owner report |
| 2026-09-27 | workflow_optimisation | mechanism | That the accumulated review `changed_lines` shortfall could not be explained by a net base-diff collapsing lines re-edited across commits | The arithmetic fits exactly: the first three commits summed to the reported 110, and the only shortfalls (−10, then −4) fall on the two commits that re-touched lines their predecessor had introduced; a base-to-HEAD candidate counts each line once, while summing per-commit stats double-counts re-edited lines | Do the arithmetic against the per-commit stats before dismissing the hypothesis — and prefer the net base-diff count, which is what a reviewer actually sees | owner report |
| 2026-09-27 | the approval fix "was reverted / never installed" | observed | rg \.\.\.details | the target reads "...input.details"; that pattern cannot match the spread form | reading the builder directly | not reverted; it was present throughout
| 2026-09-27 | "no approval occurred at all" | inferred | none | a prompt that had fired would show * | the user clarified what the prompt displayed | a prompt fired; only its content was missing
| 2026-09-27 | "the state GC pruned the bundle" | inferred | none | the bundle directory would hold files if pruned | listing the directory | the directory was empty; the bundle was never written
| 2026-09-27 | "a new session is required" to use a newly installed tool | assumed | none | the tool would be visible to the current session | trying it | it worked in-session
| 2026-09-27 | a credential failure from "Incorrect API key" | inferred | none | a bad key would fail consistently | the user knew of the provider outage | a provider outage, not a credential fault
| 2026-09-27 | "metadata shape causes the blank approval prompt" | assumed | none | the renderer would read metadata for custom permission names | reading OpenChamber PermissionCard | three fixes addressed mechanisms that did not exist; the real cause was suppressant keys
| 2026-09-27 | "read is limited to read/glob outside the project" | assumed | none | read would fail outside the project | the workflow agent tested it | read already lists directories and reads outside the project
| 2026-09-27 | "context is exhausted" | assumed | none | the harness would stop accepting input | the directive explicitly forbids this | WORKFLOW.md:316 manages context; announcing exhaustion is forbidden
| date | claim | class | check performed | positive control | caught by | corrected conclusion

## Adding a row

Append below the last entry, keep the column order, and add the row in the same
change that records the task in `ROUTER-LOG.md`. Never rewrite an earlier row to
read better; a retraction that was itself wrong stays visible.

