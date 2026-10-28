"""Q90 PM reassignment: exact seats, fallback chains, and production gates.

Extracts and EXECUTES the verifier's ``pm-seat-policy`` block and its fallback
resolver; it does not reimplement either in Python.

Run: python3 -m unittest tests.test_q90_pm_reassign -v
"""

import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "verify-workflow.sh"
CONFIG = REPO / "global-config" / "opencode.json"
FALLBACK = REPO / "global-config" / "rate-limit-fallback.json"
PMS = ("pm-odd", "pm-systematic")
MODEL, VARIANT = "opencode-go/muse-spark-1.3-contributor", None
BEGIN, END = "// pm-seat-policy:begin", "// pm-seat-policy:end"
CAPS = ["files", "tools", "vision"]
QWEN = {"providerID": "opencode-go", "modelID": "qwen3.8-flash",
        "variant": "high", "capabilities": CAPS}
GEMINI = {"providerID": "openrouter", "modelID": "~google/gemini-flash-latest",
          "capabilities": CAPS}
QWEN_KEY, GEMINI_KEY = "opencode-go/qwen3.8-flash", "openrouter/~google/gemini-flash-latest"
SHARED = [
    ("opencode-go/mimo-v2.6-flash", "high"),
    ("deepseek/deepseek-flash", "high"),
    ("openrouter/deepseek/deepseek-v4.1-flash", "default"),
]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def function(text, name):
    start = text.index(f"function {name}(")
    brace, depth = text.index("{", start), 0
    for index in range(brace, len(text)):
        depth += text[index] == "{"
        depth -= text[index] == "}"
        if depth == 0:
            return text[start:index + 1]
    raise AssertionError(f"unterminated verifier function: {name}")


def pm_block(text=None):
    text = SCRIPT.read_text(encoding="utf-8") if text is None else text
    start, end = text.find(BEGIN), text.find(END)
    if start < 0 or end < start:
        raise AssertionError("pm-seat-policy block not found in verify-workflow.sh")
    return text[start:end + len(END)]


def run_js(program, stdin=""):
    runtime = shutil.which("bun") or shutil.which("node")
    if not runtime:
        raise unittest.SkipTest("Bun or Node is required to execute the production block")
    result = subprocess.run([runtime, "-e", program], input=stdin, capture_output=True,
                            text=True, timeout=30, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise AssertionError(f"extracted verifier code failed: {result.stderr or result.stdout}")
    return result.stdout


def seat_failures(agents):
    script = SCRIPT.read_text(encoding="utf-8")
    program = ("const show=(value)=>JSON.stringify(value);"
               + function(script, "normalizeModel") + "\n"
               + function(script, "modelFamily") + "\n" + pm_block(script)
               + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
               + "\nprocess.stdout.write(JSON.stringify(pmSeatFailures(input)))")
    return json.loads(run_js(program, json.dumps(agents)))


def resolve(fallback, model, agent):
    script = SCRIPT.read_text(encoding="utf-8")
    start, end = script.find("function modelString(value)"), script.find("function addRole(")
    if start < 0 or end <= start:
        raise AssertionError("fallback resolver block not found in verify-workflow.sh")
    program = (
        "const fail=(message)=>{throw new Error(message)};"
        "const show=(value)=>JSON.stringify(value);"
        "const hasOwn=(object,key)=>Object.prototype.hasOwnProperty.call(object,key);"
        + script[start:end]
        + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
        + "process.stdout.write(JSON.stringify({model:effectiveFallbacks(input.fallback,"
        + "input.model,input.agent,'model'),provider:effectiveFallbacks(input.fallback,"
        + "input.model,input.agent,'provider')}))"
    )
    payload = json.dumps({"fallback": fallback, "model": model, "agent": agent})
    return json.loads(run_js(program, payload))


class PmSeatGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agents = load(CONFIG)["agent"]

    def test_configured_muse_spark_without_variant_is_accepted(self):
        for name in PMS:
            self.assertEqual((self.agents[name]["model"], self.agents[name].get("variant")),
                             (MODEL, VARIANT))
        self.assertEqual(seat_failures(self.agents), [])

    def test_each_pm_on_an_openai_model_is_rejected(self):
        for name in PMS:
            for model in ("openai/gpt-6.1-sol", "openai/gpt-6-luna"):
                with self.subTest(agent=name, model=model):
                    mutated = copy.deepcopy(self.agents)
                    mutated[name]["model"] = model
                    self.assertEqual(seat_failures(mutated), [
                        f"PM_SEAT_OPENAI_MODEL: {name}={json.dumps(model)}"])

    def test_wrong_or_missing_variant_is_rejected(self):
        for name in PMS:
            with self.subTest(agent=name, variant="medium"):
                mutated = copy.deepcopy(self.agents)
                mutated[name]["variant"] = "medium"
                self.assertEqual(seat_failures(mutated), [
                    f'PM_SEAT_VARIANT_MISMATCH: {name}="medium"'])
            with self.subTest(agent=name, variant="high"):
                mutated = copy.deepcopy(self.agents)
                mutated[name]["variant"] = "high"
                self.assertEqual(seat_failures(mutated), [
                    f'PM_SEAT_VARIANT_MISMATCH: {name}="high"'])

    def test_production_verifier_calls_the_pm_seat_gate(self):
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("function pmSeatFailures(agents)", pm_block(script))
        self.assertIn("for (const failure of pmSeatFailures(deployedAgents)) fail(failure)",
                      script)


class FallbackPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fallback = load(FALLBACK)

    def test_both_pm_agent_chains_are_identical_and_exact(self):
        for name in PMS:
            with self.subTest(agent=name):
                self.assertEqual(self.fallback["agentFallbackModels"][name], [QWEN, GEMINI])
                self.assertNotIn("deepseek", json.dumps(
                    self.fallback["agentFallbackModels"][name]).lower())

    def test_pm_chains_are_active(self):
        for name in PMS:
            self.assertNotIn(name, self.fallback["excludeAgents"])
            self.assertNotIn(name, self.fallback["noFallbackAgents"])

    def test_shared_muse_policy_matches_the_pinned_chain(self):
        self.assertIn(MODEL, self.fallback["fallbackModels"],
                      "Muse Spark PM model has no exact fallback policy")
        keys = [(f"{entry['providerID']}/{entry['modelID']}", entry.get("variant"))
                for entry in self.fallback["fallbackModels"][MODEL]]
        self.assertEqual(keys, SHARED)
        self.assertNotEqual(self.fallback["fallbackModels"][MODEL],
                            self.fallback["agentFallbackModels"]["pm-odd"])

    def test_real_resolver_keeps_qwen_for_model_failure(self):
        for name in PMS:
            with self.subTest(agent=name):
                self.assertEqual(resolve(self.fallback, MODEL, name)["model"],
                                 [QWEN_KEY, GEMINI_KEY])

    def test_real_filter_leaves_nonempty_cross_provider_survivors(self):
        for name in PMS:
            with self.subTest(agent=name):
                survivors = resolve(self.fallback, MODEL, name)["provider"]
                self.assertEqual(survivors, [GEMINI_KEY])
                self.assertTrue(all(not item.startswith("opencode-go/") for item in survivors))

    def test_removing_the_cross_provider_target_empties_the_filter(self):
        fallback = copy.deepcopy(self.fallback)
        fallback["agentFallbackModels"]["pm-odd"] = [QWEN]
        self.assertEqual(resolve(fallback, MODEL, "pm-odd")["provider"], [])

    def test_removed_or_shared_pm_override_breaks_the_qwen_chain(self):
        expected, shared = [QWEN_KEY, GEMINI_KEY], [key for key, _ in SHARED]
        for name, label in [(n, m) for n in PMS for m in ("removed", "shared-muse")]:
            fallback = copy.deepcopy(self.fallback)
            if label == "removed": fallback["agentFallbackModels"].pop(name)
            else: fallback["agentFallbackModels"][name] = copy.deepcopy(fallback["fallbackModels"][MODEL])
            with self.subTest(agent=name, mutation=label):
                chain = resolve(fallback, MODEL, name)["model"]
                self.assertEqual(chain, shared)
                self.assertNotEqual(chain, expected)


if __name__ == "__main__":
    unittest.main()
