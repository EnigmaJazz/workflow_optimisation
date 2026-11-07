# Advisor

Consult the advisor before locking a plan, after hitting the same error twice, and before calling a
task done. Also consult it, without waiting to be asked, at each of these:

- **A fix did not clear the failure.** The same typed refusal or error comes back after a change that
  was meant to fix it. Call before the next attempt, not after the third.
- **A cause or a menu is about to reach the owner.** Before stating a root cause for a blocker, or
  offering the owner options to choose between, call once with the evidence gathered so far. A cause
  stated without evidence is a hypothesis; label it as one.
- **A retry hook fires** (for example a "Jev-retry" notice on a repeated call). Treat it as an
  instruction to call the advisor before retrying.
- **The next step costs the owner an action** (a restart, a consent, an attestation, a profile edit).
  Confirm the step is necessary and that nothing cheaper is untried.
- **Competing plans.** Before choosing between two or more plans or designs, or recommending one to
  the owner, call with the options and the evidence for each.
- **A critical or security issue without an immediate, simple fix.** Whether you, a worker, a reviewer
  or another agent found it (auth, permissions, credentials, sandbox boundaries, data loss, a broken
  guard). Call before deciding the response, and before telling the owner it is fine to proceed.
- **More than one dispatch round on one blocker** with no new evidence between rounds.

Run the read-only checks the advisor names in one batch, then act on them. If the advisor contradicts
evidence already in hand, state the conflict in a second call instead of switching silently.
