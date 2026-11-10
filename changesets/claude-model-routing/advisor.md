# Advisor

The advisor is an expensive, stronger model. Consult it only at these three points. This rule
replaces the harness's default advice to consult before starting and before declaring done.

1. **Stuck.** The same failure, error or typed refusal returns after a change meant to fix it; a
   retry hook fires (for example a "Jev-retry" notice); or a second dispatch round on one blocker
   brought no new evidence. Call before the next attempt.
2. **A genuine discrepancy between recommended plans.** Two plans, designs or pieces of advice
   conflict and the evidence in hand does not settle which is right. Call with each option and its
   evidence before choosing or recommending one to the owner.
3. **Final acceptance of a plan for a big change.** Before a large or high-risk plan is locked and
   delegated (Task Size "large", or a Risk line naming a high-risk item). Small and routine work
   does not qualify.

Outside these points, decide without the advisor: raise effort, add a check (test, build, script)
or ask the owner one question instead. A cause stated without evidence is still a hypothesis;
label it as one.

Run the read-only checks the advisor names in one batch, then act on them. If the advisor
contradicts evidence already in hand, state the conflict in a second call instead of switching
silently.
