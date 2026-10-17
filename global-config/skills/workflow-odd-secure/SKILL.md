---
name: workflow-odd-secure
description: Carry out authorized Organic Driven Development in secure OpenCode with delegated mutation, durable tasks, and separate native RDD review.
---

# Secure ODD route

Load after `workflow-route` selects authorized ODD work. Read [the secure ODD and native review contract](references/odd-and-review.md) before delegating, making a tracker, or starting review. The current `WORKFLOW.md` remains authoritative for task classification and delivery; this reference records the secure adaptation of the upstream protocol.

<!-- workflow:anchor workflow.tiny-fix-odd-route:begin -->
- Tiny-fix route: for understood, mechanically bounded few-line work with no contract/security effect, dispatch one delegated `general` writer on `openai/gpt-6-luna`; create no tracker, advice record, or mirror. It is passive-only; any medium/high assessment automatically escalates out. Its one-way tripwire is escalation-only and the named constants in `global-config/plugins/systematic-routing-guard.ts` are authoritative; changed-line count never selects a route. Record the permit-consumption log, the `ROUTER-LOG.md` row with commit and changed lines, and, for a PM tiny fix, a tracker `## Log` entry.

- Temporary writer deviation (owner decision, 2026-10-17): while the ORCHESTRATOR dispatches directly, use `general` (`openai/gpt-6-luna`) as the ODD implementation writer for model-family independence from the DeepSeek orchestrator. When the PM layer is active, use `odd-apply` as stated above. Revert this deviation at the Q56 PM-layer pilot; it must not outlive that trigger.
<!-- workflow:anchor workflow.tiny-fix-odd-route:end -->
- The orchestrator and PMs are coordinators, not sandbox workers. For an ODD unit, dispatch `odd-apply` as the implementation writer; it owns only the ODD route and does not replace `systematic-implementer`. Project writes, executions and checks use the authorized sandbox worker; the worker does not commit, and the PM commits its applied result through the reviewed fixed `host_git_commit` operation. The upstream inline-edit route maps to a sandbox worker even for one file.

- When the two-file writer (two or more non-trivial files), preparation, or long-session trigger fires, delegate its bounded task. Use the evidence budget instead of file counts: one parallel batch (at most 3 tool/read calls, about 10k tokens); beyond that or more than about 5 sequential lookups goes to one read-only explorer returning at most about 2k tokens with `path:line`. For substantial work record the per-task route and trigger evidence before implementation; persist Task result and actual checks afterward in the tracker and complete Magic Context mirror.
- Keep RDD separate and user-owned. In v3.5 an unset switch resolves on; read effective mode and deciding source per project before review and never toggle it automatically. Use native scoped provider-returned review operations; do not synthesize receipts or replay isolated reviewer prompts. A disabled RDD mode does not prevent ordinary functional checks.
- Before any commit that may become an RDD candidate, require the delegated worker's staged reviewability receipt and enforce the local per-commit line/byte cap from the reference. Native Gentle AI START remains the final 200 KiB serialized-input authority; budget stops are split/abandon signals, never invitations to bypass the guard.
- Confirm real Task dispatch and result, project permissions, exact test runner, relevant Systematic specialist, and applicable review before closing.
