import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SOURCE_PATH = REPO / "global-config" / "opencode.json"
SCRIPT_PATH = REPO / "scripts" / "derive-v2-config.py"
PM_NAMES = ("pm-odd", "pm-systematic")
MUSE_MODEL = "opencode-go/muse-spark-1.3-contributor"
SOL_MODEL = "openai/gpt-6.1-sol"
ASTRA_MODEL = "openai/gpt-6-astra"


def load_deriver():
    spec = importlib.util.spec_from_file_location("derive_v2_pm_git_head", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(config):
    """Return missing or weakened PM host_git_head grants in a derived config."""
    problems = []
    agents = config.get("agent") or {}
    for name in PM_NAMES:
        agent = agents.get(name) or {}
        if (agent.get("tools") or {}).get("host_git_head") is not True:
            problems.append(f"{name}: tools.host_git_head must be true")
        if (agent.get("permission") or {}).get("host_git_head") != "allow":
            problems.append(f"{name}: permission.host_git_head must be allow")
        alias = agents.get(f"{name}-astra")
        if alias is not None and (alias.get("permission") or {}).get("host_git_head") != "allow":
            problems.append(f"{name}-astra: permission.host_git_head must be allow")
    if (config.get("permission") or {}).get("host_git_head") != "deny":
        problems.append("global permission.host_git_head must remain deny")
    return problems


class PMGitHeadGrants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(SOURCE_PATH.read_text())
        cls.deriver = load_deriver()
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.fork_dir = Path(cls.temp_dir.name)
        (cls.fork_dir / "package.json").write_text(json.dumps({"exports": {}}))

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def derive(self, source):
        config, _notes = self.deriver.derive_config(
            source,
            fork_dir=self.fork_dir,
            fork_ref="/v2/vendor/opencode-rate-limit-fallback-mapped",
        )
        self.deriver.add_v2_astra_aliases(config)
        return config

    def test_source_pm_grants_and_global_deny_are_explicit(self):
        self.assertEqual(check(self.source), [])
        self.assertIs(self.source["agent"]["pm-odd"]["tools"]["host_git_head"], True)
        self.assertEqual(self.source["agent"]["pm-odd"]["permission"]["host_git_head"], "allow")
        self.assertIs(self.source["agent"]["pm-systematic"]["tools"]["host_git_head"], True)
        self.assertEqual(self.source["agent"]["pm-systematic"]["permission"]["host_git_head"], "allow")
        self.assertEqual(self.source["permission"]["host_git_head"], "deny")

    def test_derived_config_preserves_pm_grants_and_global_deny(self):
        derived = self.derive(copy.deepcopy(self.source))
        self.assertEqual(check(derived), [])
        for name in PM_NAMES:
            self.assertIs(derived["agent"][name]["tools"]["host_git_head"], True)
            self.assertEqual(derived["agent"][name]["permission"]["host_git_head"], "allow")
        self.assertEqual(derived["permission"]["host_git_head"], "deny")

    def test_muse_pm_agents_do_not_get_sol_only_astra_aliases(self):
        derived = self.derive(copy.deepcopy(self.source))
        for name in PM_NAMES:
            self.assertEqual(derived["agent"][name]["model"], MUSE_MODEL)
            self.assertNotIn(
                f"{name}-astra",
                derived["agent"],
                "V2 Astra aliases are Sol-only: the base model must be openai/gpt-6.1-sol.",
            )

    def test_sol_pm_aliases_preserve_the_host_git_head_grant(self):
        synthetic = copy.deepcopy(self.source)
        for name in PM_NAMES:
            synthetic["agent"][name]["model"] = SOL_MODEL
        derived = self.derive(synthetic)
        self.assertEqual(check(derived), [])
        for name in PM_NAMES:
            alias = derived["agent"][f"{name}-astra"]
            self.assertEqual(alias["model"], ASTRA_MODEL)
            self.assertIs(alias["tools"]["host_git_head"], True)
            self.assertEqual(alias["permission"]["host_git_head"], "allow")

    def test_check_reports_each_removed_or_weakened_grant(self):
        baseline = self.derive(copy.deepcopy(self.source))
        mutations = (
            ("removed PM permission", lambda c: c["agent"]["pm-odd"]["permission"].pop("host_git_head"), "pm-odd: permission.host_git_head must be allow"),
            ("false PM tool", lambda c: c["agent"]["pm-systematic"]["tools"].__setitem__("host_git_head", False), "pm-systematic: tools.host_git_head must be true"),
            ("global allow", lambda c: c["permission"].__setitem__("host_git_head", "allow"), "global permission.host_git_head must remain deny"),
        )
        for label, mutate, expected_problem in mutations:
            with self.subTest(control=label):
                changed = copy.deepcopy(baseline)
                mutate(changed)
                problems = check(changed)
                self.assertIn(expected_problem, problems, f"positive control detected: {label}: {problems}")

        synthetic = copy.deepcopy(self.source)
        synthetic["agent"]["pm-odd"]["model"] = SOL_MODEL
        alias_config = self.derive(synthetic)
        del alias_config["agent"]["pm-odd-astra"]["permission"]["host_git_head"]
        problems = check(alias_config)
        self.assertIn(
            "pm-odd-astra: permission.host_git_head must be allow",
            problems,
            f"positive control detected: dropped alias permission: {problems}",
        )


if __name__ == "__main__":
    unittest.main()
