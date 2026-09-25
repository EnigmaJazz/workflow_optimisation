---
name: workflow-systematic
description: Choose and dispatch the installed Systematic skills and named specialists for planned features, fixes, frontend work, and advisory review.
---

# Systematic route

Load after `workflow-route` selects a Systematic step. Read [the specialist and sandbox contract](references/specialists.md) before Task dispatch. Then load the **installed** named Systematic skill; version-managed upstream behavior belongs to that installed skill, not a frozen copy here.

- Tiny understood fixes can use one delegated sandbox writer without inventing `ce:plan`. Clear small features use `ce:plan → ce:work → ce:review`. Substantial ambiguous features begin with `ce:brainstorm`; offer SDD only if durable specification would materially help and wait for explicit selection. Bug fixes reproduce/root-cause, use the configured test-first route where applicable, then `ce:work` and advisory `ce:review`. Frontend design uses the named frontend-design route and separate apply tier; documents/global tools use their task-class recipe.
- Read each selected live skill and dispatch its named specialist. Never substitute `general` for `systematic-implementer` or bundled reviewers. `explore` and `general` are fallbacks only when no named skill owns the task. If independent reviewers are selected, issue all Task calls in one wave and use the installed Systematic review helper sequence.
- Every specialist Task brief that permits repository inspection includes: `SEARCH CONTRACT: AFT=navigation; CodeGraph=relationships/impact; AST-grep=structure; sandbox_grep=bounded literal fallback; native grep unavailable; no shell-search bypass.` Systematic categories deny native `grep`; a child uses known-path read and permitted sandbox inspection instead. If it needs evidence outside its registered project, it returns `EXTERNAL_CONTEXT_REQUIRED` with `Purpose`, `Expected location`, and `Required evidence`, then stops that dependent work. The orchestrator resolves the external evidence separately and may resume the specialist with the bounded result.
- Systematic `ce:review` is advisory; non-SDD native RDD is a separate user-owned review checkpoint. Preserve sandbox mutation boundaries, actual test evidence and completion metadata.
