"""Pin the live acknowledge grant; any future legitimate holder updates this test in the same change."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
CHECKER = REPO / "verify" / "checkers" / "check-runtime-agents.cjs"
CONFIG = REPO / "global-config" / "opencode.json"
DERIVE = REPO / "scripts" / "derive-v2-config.py"
TOOL = "host_review_acknowledge_approved"
COORDINATORS = ("gentle-orchestrator", "pm-odd", "pm-systematic")
BEGIN_MARKER = "// acknowledge-grant-policy:begin"
END_MARKER = "// acknowledge-grant-policy:end"


def load_deriver():
    spec = importlib.util.spec_from_file_location("derive_v2_acknowledge_grant_pin", DERIVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_policy(checker_source, runtime):
    try:
        start = checker_source.index(BEGIN_MARKER) + len(BEGIN_MARKER)
        end = checker_source.index(END_MARKER, start)
    except ValueError as error:
        raise AssertionError(f"acknowledge-grant-policy marker block is missing: {error}") from error
    return (
        checker_source[start:end]
        + "\nconst input=JSON.parse(require('fs').readFileSync(0,'utf8'));"
        + "let result=[];"
        + "if(input.mode==='coordinator') result=hostReviewAcknowledgeAllowFailures(input.agent);"
        + "else if(input.mode==='outside') result=acknowledgeGrantOutsideFailures(input.agents,input.allowed);"
        + "else if(input.mode==='resolved') result=input.agents.map(([name,agent])=>[name,resolvedPermissionValue(agent,'host_review_acknowledge_approved')]);"
        + "process.stdout.write(JSON.stringify(result))"
    )


class AcknowledgeGrantPin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = shutil.which("node") or shutil.which("bun")
        if cls.runtime is None:
            raise unittest.SkipTest("no JavaScript runtime found (node or bun)")
        cls.checker_source = CHECKER.read_text(encoding="utf-8")
        cls.program = build_policy(cls.checker_source, cls.runtime)
        cls.source = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.deriver = load_deriver()
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.fork_dir = Path(cls.temp_dir.name)
        (cls.fork_dir / "package.json").write_text(json.dumps({"exports": {}}), encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp_dir"):
            cls.temp_dir.cleanup()

    def run_policy(self, data):
        result = subprocess.run(
            [self.runtime, "-e", self.program], input=json.dumps(data),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def resolve(self, agents):
        return dict(self.run_policy({"mode": "resolved", "agents": list(agents.items())}))

    def derive(self, source):
        config, _notes = self.deriver.derive_config(
            source, fork_dir=self.fork_dir,
            fork_ref="/v2/vendor/opencode-rate-limit-fallback-mapped",
        )
        self.deriver.add_v2_astra_aliases(config)
        return config

    def check(self, config, allowed=COORDINATORS):
        failures = []
        permissions = config.get("permission") or {}
        if permissions.get(TOOL) != "deny":
            failures.append("global permission must be deny")
        agents = config.get("agent") or {}
        for name in allowed:
            failures.extend(self.run_policy({
                "mode": "coordinator", "agent": agents.get(name),
            }))
        failures.extend(self.run_policy({"mode": "outside", "agents": agents, "allowed": list(allowed)}))
        return failures

    def assert_clean_config(self, config):
        self.assertEqual(self.check(config), [])
        self.assertEqual(
            {name for name, value in self.resolve(config.get("agent") or {}).items() if value == "allow"},
            set(COORDINATORS),
        )
        resolved = self.resolve(config.get("agent") or {})
        for name, value in resolved.items():
            if name not in COORDINATORS:
                self.assertIn(value, (None, "deny"), f"unexpected {TOOL} for {name}: {value}")

    def test_live_source_and_derived_v2_holder_sets_are_exact(self):
        self.assert_clean_config(self.source)
        derived = self.derive(copy.deepcopy(self.source))
        self.assert_clean_config(derived)

    def test_non_coordinator_grant_mutations_are_rejected(self):
        baseline = self.derive(copy.deepcopy(self.source))
        mutations = (
            ("exact allow", lambda config: config["agent"]["fourth-agent"].__setitem__("permission", {TOOL: "allow"})),
            ("exact ask", lambda config: config["agent"]["fourth-agent"].__setitem__("permission", {TOOL: "ask"})),
            ("wildcard ask", lambda config: config["agent"]["fourth-agent"].__setitem__("permission", {"host_review_*": "ask"})),
            ("wildcard allow", lambda config: config["agent"]["fourth-agent"].__setitem__("permission", {"host_review_*": "allow"})),
        )
        for label, mutate in mutations:
            with self.subTest(control=label):
                changed = copy.deepcopy(baseline)
                changed["agent"]["fourth-agent"] = {}
                mutate(changed)
                self.assertTrue(self.check(changed), f"positive control failed to detect {label}")

    def test_coordinator_requires_exact_own_allow_and_global_deny(self):
        baseline = self.derive(copy.deepcopy(self.source))
        mutations = (
            ("removed exact key", lambda config: config["agent"]["pm-odd"]["permission"].pop(TOOL)),
            ("exact ask", lambda config: config["agent"]["pm-odd"]["permission"].__setitem__(TOOL, "ask")),
            ("wildcard only", lambda config: config["agent"]["pm-odd"].__setitem__("permission", {"host_review_*": "allow"})),
            ("global allow", lambda config: config["permission"].__setitem__(TOOL, "allow")),
        )
        for label, mutate in mutations:
            with self.subTest(control=label):
                changed = copy.deepcopy(baseline)
                mutate(changed)
                self.assertTrue(self.check(changed), f"positive control failed to detect {label}")

    def test_explicit_deny_and_ordered_deny_controls_are_clean(self):
        baseline = self.derive(copy.deepcopy(self.source))
        cases = (
            ("explicit deny", {TOOL: "deny"}),
            ("ordered wildcard then exact deny", {"host_review_*": "allow", TOOL: "deny"}),
            ("omitted", {}),
            ("string deny", "deny"),
        )
        for label, permission in cases:
            with self.subTest(control=label):
                changed = copy.deepcopy(baseline)
                changed["agent"]["fourth-agent"] = {"permission": permission}
                self.assertEqual(self.check(changed), [])


if __name__ == "__main__":
    unittest.main()
