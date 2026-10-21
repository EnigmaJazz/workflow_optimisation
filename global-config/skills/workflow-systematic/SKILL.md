---
name: workflow-systematic
description: Choose and dispatch the installed Systematic skills and named specialists for planned features, fixes, frontend work, and advisory review.
---

# Systematic route

Load after `workflow-route` selects a Systematic step. Read [the specialist and sandbox contract](references/specialists.md) before Task dispatch. Then load the **installed** named Systematic skill; version-managed upstream behavior belongs to that installed skill, not a frozen copy here.

<!-- workflow:anchor workflow.tiny-fix-systematic-route:begin -->
- An understood, mechanically bounded few-line tiny fix without contract/security effect uses the Tiny-fix route: one delegated `general` writer on `openai/gpt-6-luna`, with no tracker, advice record, or mirror. It is passive-only; any medium/high assessment automatically escalates out. Its one-way tripwire is escalation-only and its named constants in `global-config/plugins/systematic-routing-guard.ts` are authoritative; changed-line count never selects a route.
<!-- workflow:anchor workflow.tiny-fix-systematic-route:end -->
- Verification and advice follow the finite `WORKFLOW.md` `Verification and advice budget by task type` matrix over the six existing route classes: one initial writer plus ONE fresh correction across all pre-commit post-code gates, with same-candidate findings batched into one consolidated brief and a targeted recheck. `gentle-ai-worker-local` takes exactly ONE changed file per writer Task; cloud writers may batch a coherent multi-file unit. A true docs/metadata unit inside the allowlist takes zero advisor and verifier Tasks; the PM check and orchestrator readback stand in.
- Clear small features use `ce:plan → ce:work → ce:review`. Substantial ambiguous features begin with `ce:brainstorm`. Bug fixes reproduce/root-cause, use the configured test-first route where applicable, then `ce:work` and advisory `ce:review`. Frontend design uses the named frontend-design route and separate apply tier; documents/global tools use their task-class recipe.
- Read each selected live skill and dispatch its named specialist. Never substitute `general` for `systematic-implementer` or bundled reviewers except for the explicitly selected Tiny-fix route above. `explore` and `general` are otherwise fallbacks only when no named skill owns the task. If independent reviewers are selected, issue all Task calls in one wave and use the installed Systematic review helper sequence.
- Every specialist Task brief that permits repository inspection includes: `SEARCH CONTRACT: AFT=navigation; CodeGraph=relationships/impact; AST-grep=structure; sandbox_grep=bounded literal fallback; native grep unavailable; no shell-search bypass.` Systematic categories deny native `grep`; a child uses known-path read and permitted sandbox inspection instead. If it needs evidence outside its registered project, it returns `EXTERNAL_CONTEXT_REQUIRED` with `Purpose`, `Expected location`, and `Required evidence`, then stops that dependent work. The orchestrator resolves the external evidence separately and may resume the specialist with the bounded result.
- Systematic `ce:review` is advisory; native RDD is a separate user-owned review checkpoint. Preserve sandbox mutation boundaries, actual test evidence and completion metadata.
