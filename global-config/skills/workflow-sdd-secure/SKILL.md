---
name: workflow-sdd-secure
description: Route explicitly selected Gentle AI SDD phases through secure specialists and the Magic Context artifact adapter.
---

# Secure SDD route

Load only for explicitly selected SDD. Read [the SDD and Magic Context adapter](references/sdd-magic-adapter.md) before choosing a store or phase. Consult native `gentle-ai.sdd-status/v2` where OpenSpec-backed; for Magic Context-only mode retrieve actual phase artifacts. Phase agents and their installed skills own the phase instructions: do not recreate them here.

- Delegate the next native phase to its named `sdd-*` agent and loaded skill. Respect `blockedReasons`, dependency states, user-selected pace and product choices. Research is optional and output-only; verification is optional diagnostics and does not independently certify archive.
- Every repository-inspection phase brief includes: `SEARCH CONTRACT: AFT=navigation; CodeGraph=relationships/impact; AST-grep=structure; sandbox_grep=bounded literal fallback; native grep unavailable; no shell-search bypass.` Use dedicated read for known allowed files. If a phase needs evidence outside its registered project, it returns `EXTERNAL_CONTEXT_REQUIRED` with `Purpose`, `Expected location`, and `Required evidence`; the orchestrator obtains that context separately rather than widening the phase agent's filesystem access.
- Route implementation and artifact writes to authorized sandbox workers; the read-only orchestrator has no host Bash or write authority. Use `ctx_search`, `ctx_memory` and the exact artifact markers for the configured Magic Context store. Do not invoke Engram unless the user separately selected an Engram workflow.
- Inside SDD do not start native RDD review or consent. Keep phase handoffs and full artifact readback, not a parallel ODD tracker for SDD work.
