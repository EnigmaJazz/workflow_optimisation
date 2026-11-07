import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable, cast

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "verify" / "checkers" / "sandbox-tool-decisions.py"
SOURCE = CHECKER.read_text(encoding="utf-8")
NAMESPACE: dict[str, Any] = {"__name__": "sandbox_tool_decisions_test"}
exec(compile(SOURCE, str(CHECKER), "exec"), NAMESPACE)
check = cast(Callable[[Any, Any], tuple[str, str]], NAMESPACE["check"])


class ToolDecisionCoverageTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {"tools": [{"name": "read"}, {"name": "sandbox_read"}]}
        self.config = {
            "permission": {"read": "allow", "sandbox_read": "deny"},
            "agent": {"worker": {"tools": {"read": True}, "permission": {"read": "allow"}}},
        }

    def test_clean(self):
        self.assertEqual(check(self.config, self.fixture)[0], "clean")

    def test_missing_global_decision(self):
        config = json.loads(json.dumps(self.config))
        del config["permission"]["sandbox_read"]
        status, detail = check(config, self.fixture)
        self.assertEqual(status, "error")
        self.assertIn("global.sandbox_read", detail)

    def test_enabled_agent_without_decision(self):
        config = json.loads(json.dumps(self.config))
        del config["agent"]["worker"]["permission"]["read"]
        status, detail = check(config, self.fixture)
        self.assertEqual(status, "error")
        self.assertIn("worker.read", detail)

    def test_non_enabled_agent_tool_is_exempt(self):
        config = json.loads(json.dumps(self.config))
        config["agent"]["worker"]["tools"]["sandbox_read"] = False
        self.assertEqual(check(config, self.fixture)[0], "clean")

    def test_wildcard_enables_tools_but_false_override_disables_one(self):
        config = json.loads(json.dumps(self.config))
        config["agent"]["worker"]["tools"] = {"*": True, "read": False}
        config["agent"]["worker"]["permission"]["sandbox_read"] = "ask"
        self.assertEqual(check(config, self.fixture)[0], "clean")
        del config["agent"]["worker"]["permission"]["sandbox_read"]
        status, detail = check(config, self.fixture)
        self.assertEqual(status, "error")
        self.assertIn("worker.sandbox_read", detail)

    def test_duplicate_fixture_tool_names_are_rejected(self):
        fixture = {"tools": [{"name": "read"}, {"name": "read"}]}
        status, detail = check(self.config, fixture)
        self.assertEqual(status, "error")
        self.assertIn("duplicate", detail)

    def test_non_dict_agent_entry_is_skipped(self):
        config = json.loads(json.dumps(self.config))
        config["agent"] = {
            "broken": "not-an-object",
            "worker": config["agent"]["worker"],
        }
        self.assertEqual(check(config, self.fixture)[0], "clean")

    def test_malformed_config_and_fixture(self):
        self.assertEqual(check([], self.fixture)[0], "error")
        self.assertEqual(check(self.config, {"tools": []})[0], "error")
        self.assertEqual(check(self.config, {"tools": [{"name": 3}]})[0], "error")

    def test_positive_control_minimal_missing_decision_names_tool(self):
        status, detail = check({"agent": {}}, {"tools": [{"name": "example_tool"}]})
        self.assertEqual(status, "error")
        self.assertIn("global.example_tool", detail)

    def test_cli_clean_with_real_config_and_synthetic_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_path = Path(directory) / "surface.json"
            fixture_path.write_text(json.dumps({"tools": [{"name": "host_git_head"}]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(CHECKER), str(ROOT / "global-config" / "opencode.json"), str(fixture_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "clean\texplicit decisions cover 1 fixture tools and enabled agent tools\n")


if __name__ == "__main__":
    unittest.main()
