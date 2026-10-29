"""Native review actors never receive a hidden Astra alias, even when they run on Sol.

The alias plugin derives ``<name>-astra`` for every non-primary Sol agent that is not an
implementation route. The six native review actors (four lenses, refuter, validator, in both
the ``review-`` and ``asi-review-`` spellings) are read-only relay lanes with guard tests that
enumerate them, so an Astra upgrade of one is never wanted. The plugin and the verifier must
agree on the exclusion.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "global-config" / "plugins" / "astra-sol-upgrade.ts"
VERIFIER = REPO / "verify-workflow.sh"
SOL = "openai/gpt-6.1-sol"
ACTORS = [f"{prefix}review-{role}" for prefix in ("", "asi-")
          for role in ("risk", "resilience", "readability", "reliability", "refuter", "validator")]

RUNNER = """
import plugin from %s
try:
    from tests.verifier_source import verifier_text
except ImportError:  # run as a script from tests/
    from verifier_source import verifier_text
const names = JSON.parse(process.argv[1])
const agents = { "gentle-orchestrator": { mode: "primary", model: "x/y", permission: { task: {} } },
  "planner": { mode: "subagent", model: "%s" } }
for (const n of names) agents[n] = { mode: "subagent", model: "%s" }
const hooks = await plugin.server({})
await hooks.config({ agent: agents })
console.log(JSON.stringify(Object.keys(agents).filter((k) => k.endsWith("-astra")).sort()))
""" % (json.dumps(str(PLUGIN)), SOL, SOL)


@unittest.skipUnless(shutil.which("bun"), "bun is required to execute the plugin")
class AstraReviewActors(unittest.TestCase):
    def aliases(self, names):
        out = subprocess.run(["bun", "-e", RUNNER, json.dumps(names)], capture_output=True,
                             text=True, check=True, cwd=str(REPO)).stdout
        return json.loads(out.strip().splitlines()[-1])

    def test_positive_control_a_sol_planner_still_gets_an_alias(self):
        self.assertEqual(self.aliases([]), ["planner-astra"])

    def test_no_review_actor_on_sol_gets_an_alias(self):
        self.assertEqual(self.aliases(ACTORS), ["planner-astra"])

    def test_verifier_uses_the_same_exclusion(self):
        pattern = r"(asi-)?review-(risk|resilience|readability|reliability|refuter|validator)"
        self.assertIn(pattern, PLUGIN.read_text(encoding="utf-8"))
        self.assertIn(pattern, verifier_text())


if __name__ == "__main__":
    unittest.main()
