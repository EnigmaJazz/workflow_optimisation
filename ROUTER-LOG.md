# ROUTER-LOG

One row per routed task. Append after every task — including probes (flagged `probe: true`). **Probe rows are excluded from the R12 prove-out count**; the count starts only after probe verification (Unit 4) completes.

## Prove-Out Rule (R12, verbatim)

> The router starts as this documented recipe; encoding it as a runnable command or skill is deferred until the recipe proves out in use — **ten consecutive routed tasks across at least four task classes complete their flows without re-classification or gate escape**, with misclassifications logged to feed the encoding decision.

## Row Contract

| Date | Task | Class chosen | Reclassification | Gate outcome | Probe | Evidence reference | Notes |
|---|---|---|---|---|---|---|---|
| 2026-08-10 | Probe: greeting wording | tiny fix | none | structural readback receipt | true | probes/tiny-fix/ | One-file mechanical edit; medium-tier consolidated review (1 lens) since executable code |
| 2026-08-10 | Probe: shout formatter | small feature | none | RDD receipt | true | probes/small-feature/ | Multi-file clear behavior; medium-tier, 1 lens |
| 2026-08-10 | Probe: count_words bug | bug | none | RDD receipt | true | probes/bug/ | Reproduce → root cause → test-first RED/GREEN |
| 2026-08-10 | Probe: repo README | documentation | none | zero-lens structural readback | true | probes/documentation/ | Docs-only change: low risk, no lenses, no consent |
| 2026-08-10 | Probe: stats module | substantial | none | RDD receipt | true | probes/substantial/ | SDD propose/spec/design/tasks → apply → gate; AE4 skill paths injected into apply prompt |


## Usage Notes

- **Log after every routed task**: date, task, class chosen, reclassification (none/from→to), gate outcome (receipt / readback / human review), probe flag, evidence reference, notes.
- **Reclassification**: record when a task crosses a planning boundary (small→substantial, substantial→small). See WORKFLOW.md classification rules.
- **Probe flag**: `true` for synthetic probe runs; probe rows never count toward the ten-consecutive-tasks trigger.
- **Gate outcome**: the enforced gate that actually fired (RDD receipt, structural readback receipt, or human review for docs). Record the failure explicitly if a gate did not fire — do not leave the cell blank.
- **AE5/AE6 note**: the chained-PR threshold question (AE5) was asserted during probes — no question fired below 400 lines. The reclassification scenario (AE6) was NOT exercised in the probe phase; it is deferred to real routed tasks, which will populate the Reclassification column in normal use.
- **Single-writer discipline**: one session appends rows at a time; the workspace is a git repo so concurrent appends surface as conflicts rather than silent clobbers.
