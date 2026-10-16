"""Model-family independence checks for the configured writer paths."""

import json
import re
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
    model = "/".join(normalized.split("/")[1:]).lower() if normalized else None
    if not model:
        return None
    if re.search(r"(^|/)gpt-[0-9]", model):
        return "gpt"
    for marker, family in (
        ("deepseek", "deepseek"),
        ("glm-", "glm"),
        ("qwen", "qwen"),
        ("kimi", "kimi"),
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


def configured_writers(config):
    helpers = HELPERS_PATH.read_text(encoding="utf-8")
    match = re.search(r"const ODD_SPECIALIST_WRITERS: readonly string\[\] = \[\.\.\.SPECIALIST_WRITERS,\s*([^\]]+)\]", helpers)
    if match:
        specialist = re.search(r"const SPECIALIST_WRITERS: readonly string\[\] = \[([^\]]+)\]", helpers)
        names = re.findall(r'"([a-z0-9-]+)"', specialist.group(1))
        names.extend(re.findall(r'"([a-z0-9-]+)"', match.group(1)))
        return names
    raise AssertionError("ODD_SPECIALIST_WRITERS definition was not found")


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
        self.assertEqual(targets.get("general"), "allow")
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
    def test_same_family_pairing_fails_independence_assertion(self):
        with self.assertRaises(AssertionError):
            assert_independent(self, "opencode-go/deepseek-v4.1-flash", "other/deepseek-v5")

    def test_unrecognized_writer_family_fails_independence_assertion(self):
        with self.assertRaisesRegex(AssertionError, "independence is not proven"):
            assert_independent(self, "kinver/professional", "opencode-go/deepseek-v4.1-flash")


if __name__ == "__main__":
    unittest.main()
