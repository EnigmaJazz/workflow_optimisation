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
| 2026-08-11 | R2 achievements: resume paused SDD cycle (tasks phase + S1 apply) | substantial | none | gate not fired (no code change) | false | weight_loss openspec/changes/r2-achievements/ | Tasks phase done (17 tasks, 3 PRs); S1 apply blocked by transport (sdd_task_result_empty x2, #538 session poison) — no code landed, no receipt expected; ledger reset by maintainer; resume in fresh session |
| 2026-08-11 | Fallback plugin: revert to original model per turn (chat.message hook) | small | none | RDD receipt | false | ~/.config/opencode/plugins/opencode-rate-limit-fallback-mapped commit 5e0f903 | Verified root cause in opencode 1.18.16 source (TUI sends explicit model synced from last user msg; promptAsync→createUserMessage fires chat.message); design → sdd-apply writer (opencode-linked) → 53 bun tests + tsc clean → gentle-ai review (lineage review-9215b1e10494181c, R3 lens, 0 BLOCKER, WARNING+SUGGESTION info-only) → pre-commit gate allow → committed; no remote configured |
| 2026-08-11 | Fallback plugin follow-ups: deterministic anti-loop test + I/O out of session lock | small | none | RDD receipt | false | ~/.config/opencode/plugins/opencode-rate-limit-fallback-mapped commit 178a162 | Review findings (WARNING timing-dependent test, SUGGESTION I/O under lock) fixed per spec; 53 bun tests + tsc clean; gentle-ai review lineage review-7ad5c9025c3749a4 (R3, 0 findings) → pre-commit gate allow → committed |
| 2026-08-11 | R2 achievements: resume paused SDD cycle (S1-S3 apply, verify, archive) | substantial | none | RDD disabled clone-wide (#528) — delivered under ordinary policy (.gga hook + CI + full suites) | false | weight_loss: PRs #52/#53/#54 merged (S1 409, S2 282, S3 322 lines); verify PASS w/ warnings 9/9 reqs + 20/20 scenarios, validator admitted; archived openspec/changes/archive/2026-08-11-r2-achievements/ @ eac47c5; ledger closed (2 maintainer resets: S1 +409 budget, archive 1756 spec-sync) |
| 2026-08-11 | Fallback plugin: exclude bound review agents from replay (agent-aware exclusion) | small | none | RDD receipt | false | ~/.config/opencode/plugins/opencode-rate-limit-fallback-mapped commit 8dc657a | Prompt spec (tmp/fallback-fix-prompt.md): review-agent sessions never replayed (replay bypassed review plugin's context injection → retry-after-refusal loops); excludeAgents default = 4 review agents; startCycle short-circuits pre-chain; 61 bun tests + tsc clean; RDD lineage review-33f11e8eda833c68 (fresh candidate after provider_command emission conflict poisoned first lineage slot) → pre-commit allow → committed; no remote |
| 2026-08-11 | Fallback fix acceptance: complete stuck 4-lens review review-2a1bfe11a622fa3c | bug | none | RDD receipt | false | workflow_optimisation: 4 reviewers returned valid manifests (R1 1 CRITICAL, R2 2W+3S, R3 1W+2S, R4 clean); correction commit 39f88a0 (digest-pin verify-workflow.sh, R1-001) → targeted validation passed → lineage approved → pre-commit allow | Review was stuck (slots un-captured) due to the replay bug; fixed plugin + embedded-evidence launches completed it; CRITICAL R1-001 (startup script execution without trust step) fixed by pinning sha256 in the plugin (fail-closed); follow-ups: pipefail SIGPIPE bug in verify-workflow.sh step 5, 6th task class inconsistency |
| 2026-08-11 | Workflow follow-ups: SIGPIPE bug, 6th-class consistency, plugin verdict decoupling | small | none | RDD receipt | false | workflow_optimisation commit 62c45fd | Recorded validator follow-ups fixed: step 5 exit-status capture (no pipe/SIGPIPE), 'global tooling change' propagated to diagram+R1+AGENTS.md heredoc+deployed AGENTS.md, plugin verdict via exit code + pin updated to 07c40b97; verified end-to-end ('All checks passed'); 4-lens lineage review-59015664a1ffc9ea (0 blockers, 1 SUGGESTION: diagram label 'global tooling' vs canonical name) → approved → pre-commit allow; deployed plugin re-mirrored by verify-workflow.sh |
