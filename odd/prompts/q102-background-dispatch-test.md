# Q102 unit B: background-dispatch probe for secure OpenCode V2

Paste the block below into a secure OpenCode V2 session (OpenChamber or `opencode2`). It is read-only: it
changes no file, branch, commit, config or memory. The live orchestrator prompt only gains the new rule after
a verifier run, so this probe tests the capability (D32), not the rule text.

```
Read-only capability probe. Do not write, edit, commit, create branches, change config or save memory. Do
not run verify-workflow.sh. Use no sandbox write worker.

1. In ONE message, launch two independent read-only exploration Tasks as BACKGROUND subagents (non-blocking),
   so both start before either returns:
   - Task A: list the names (not contents) of the files directly inside docs/specs/ and report the count.
   - Task B: list the names (not contents) of the files directly inside roles/ and report the count.
2. After launching, do not poll, sleep, or re-check them. If your runtime has no background launch, say so
   plainly and stop; do not fall back to sequential Tasks and call it a pass.
3. End your turn with one line: "Launched A and B in background; waiting for completion events."
4. When each completion event resumes you, record it in one line (which task, its count, whether the other
   was still running at that point). When both are in, answer with:
   - background launch supported: yes/no, with the tool or parameter you used
   - A and B overlapped in time: yes/no, with the evidence (start and finish order)
   - you polled: yes/no
   - files changed: run `git status --short` and report its exact output.

Pass: background supported = yes, overlapped = yes, polled = no, and git status output is unchanged from
before the probe.
```
