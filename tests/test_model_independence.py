"""Model-family independence checks for the configured writer paths."""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "global-config/opencode.json"
HELPERS_PATH = REPO / "global-config/plugins/lib/routing-guard-helpers.ts"


def model_family(value):
    if isinstance(value, str):
        normalized = value
    elif isinstance(value, dict):
        provider = value.get("providerID", value.get("providerId"))
        model = value.get("modelID", value.get("modelId"))
        normalized = f"{provider}/{model}" if isinstance(provider, str) and isinstance(model, str) else None
    else:
        normalized = None
    normalized = normalized.lower() if normalized else None
    if not normalized:
        return None
    # Owner-confirmed Kinver mapping; use provider identity, not a generic
    # model-name marker that could misclassify unrelated models.
    if normalized.startswith("kinver/"):
        return "qwen"
    model = "/".join(normalized.split("/")[1:])
    if re.search(r"(^|/)gpt-[0-9]", model):
        return "gpt"
    for marker, family in (
        ("deepseek", "deepseek"),
        ("glm-", "glm"),
        ("qwen", "qwen"),
        ("kimi", "kimi"),
        ("ling", "ling"),
        ("claude", "claude"),
        ("mimo", "mimo"),
        ("muse", "muse"),
        ("minimax", "minimax"),
        ("grok", "grok"),
        ("gemini", "gemini"),
    ):
        if marker in model:
            return family
    return None


def assert_independent(test_case, writer_model, coordinator_model):
    writer_family = model_family(writer_model)
    coordinator_family = model_family(coordinator_model)
    test_case.assertIsNotNone(
        writer_family,
        f"Unrecognized writer model family; independence is not proven: {writer_model!r}",
    )
    test_case.assertIsNotNone(
        coordinator_family,
        f"Unrecognized coordinator model family; independence is not proven: {coordinator_model!r}",
    )
    test_case.assertNotEqual(writer_family, coordinator_family)


def assert_task_target_allowed(test_case, targets, target):
    test_case.assertEqual(targets.get(target), "allow")


def configured_writers(config):
    helpers = HELPERS_PATH.read_text(encoding="utf-8")
    match = re.search(r"const ODD_SPECIALIST_WRITERS: readonly string\[\] = \[\.\.\.SPECIALIST_WRITERS,\s*([^\]]+)\]", helpers)
    if match:
        specialist = re.search(r"const SPECIALIST_WRITERS: readonly string\[\] = \[([^\]]+)\]", helpers)
        names = re.findall(r'"([a-z0-9-]+)"', specialist.group(1))
        names.extend(re.findall(r'"([a-z0-9-]+)"', match.group(1)))
        return names
    raise AssertionError("ODD_SPECIALIST_WRITERS definition was not found")


def extract_function(script, name):
    start = script.index(f"function {name}(")
    brace = script.index("{", start)
    depth = 0
    for index in range(brace, len(script)):
        if script[index] == "{":
            depth += 1
        elif script[index] == "}":
            depth -= 1
            if depth == 0:
                return script[start:index + 1]
    raise AssertionError(f"unterminated verifier function: {name}")


class ModelIndependence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.agents = cls.config["agent"]

    def test_tiny_fix_writers_are_independent_from_orchestrator(self):
        for writer in ("general", "gentle-ai-worker-local"):
            with self.subTest(writer=writer):
                assert_independent(
                    self,
                    self.agents[writer]["model"],
                    self.agents["gentle-orchestrator"]["model"],
                )

    def test_orchestrator_tiny_fix_task_target_is_general(self):
        targets = self.agents["gentle-orchestrator"]["permission"]["task"]
        assert_task_target_allowed(self, targets, "general")
        assert_task_target_allowed(self, targets, "gentle-ai-worker-local")
        self.assertNotIn("gentle-ai-worker", targets)

    def test_pm_dispatched_writer_is_independent_from_pm(self):
        assert_independent(
            self,
            self.agents["odd-apply"]["model"],
            self.agents["pm-odd"]["model"],
        )
        self.assertEqual(self.agents["pm-odd"]["permission"]["task"].get("odd-apply"), "allow")

    def test_every_odd_writer_is_in_the_coverage_inventory(self):
        expected = {
            "general",
            "systematic-implementer",
            "frontend-dev",
            "frontend-dev-premium",
            "frontend-apply",
            "frontend-apply-local",
            "jd-fix-agent",
            "pr-comment-resolver",
            "bug-reproduction-validator",
            "design-iterator",
            "gentle-ai-worker",
            "gentle-ai-worker-local",
            "odd-apply",
        }
        self.assertEqual(set(configured_writers(self.config)), expected)


class PositiveControl(unittest.TestCase):
    def test_removed_local_writer_permission_fails_allowlist_assertion(self):
        targets = {"general": "allow", "gentle-ai-worker-local": "allow"}
        targets.pop("gentle-ai-worker-local")
        with self.assertRaises(AssertionError):
            assert_task_target_allowed(self, targets, "gentle-ai-worker-local")

    def test_owner_confirmed_kinver_provider_maps_to_qwen(self):
        self.assertEqual(model_family("kinver/professional"), "qwen")
        self.assertIsNone(model_family("unknown-provider/unrecognized-model"))

    def test_claude_and_ling_are_recognized_and_unknown_fails_closed(self):
        self.assertEqual(model_family("opencode-go/claude-haiku-5-5"), "claude")
        self.assertEqual(model_family("opencode-go/ling-3.1-flash"), "ling")
        self.assertIsNone(model_family("unknown-provider/unrecognized-model"))
        with self.assertRaisesRegex(AssertionError, "independence is not proven"):
            assert_independent(
                self,
                "opencode-go/claude-haiku-5-5",
                "unknown-provider/unrecognized-model",
            )

    def test_verifier_model_family_matches_python_recognition(self):
        script = (REPO / "verify-workflow.sh").read_text(encoding="utf-8")
        runtime = shutil.which("bun") or shutil.which("node")
        if not runtime:
            self.skipTest("Bun or Node is required to execute the extracted verifier functions")
        program = (
            extract_function(script, "normalizeModel")
            + "\n"
            + extract_function(script, "modelFamily")
            + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
            + "\nprocess.stdout.write(JSON.stringify(input.map(modelFamily)))"
        )
        models = [
            "opencode-go/claude-haiku-5-5",
            "opencode-go/ling-3.1-flash",
            "opencode-go/minimax-m3",
            "opencode-go/minimax-m3.1-flash",
            "unknown-provider/unrecognized-model",
        ]
        proc = subprocess.run(
            [runtime, "-e", program],
            input=json.dumps(models),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            json.loads(proc.stdout),
            ["claude", "ling", "minimax", "minimax", None],
        )

    def test_same_family_pairing_fails_independence_assertion(self):
        with self.assertRaises(AssertionError):
            assert_independent(self, "opencode-go/deepseek-v4.1-flash", "other/deepseek-v5")

    def test_unrecognized_writer_family_fails_independence_assertion(self):
        with self.assertRaisesRegex(AssertionError, "independence is not proven"):
            assert_independent(self, "unknown-provider/unrecognized-model", "opencode-go/deepseek-v4.1-flash")


if __name__ == "__main__":
    unittest.main()
