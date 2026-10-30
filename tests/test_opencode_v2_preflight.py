"""scripts/opencode-v2-preflight.py: the read-only readiness report for the V2 cutover (queue Q46).

Every check takes an injected command runner, so each branch runs without touching systemd, the V2 server or the repos.
"""
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "opencode-v2-preflight.py"


def load():
    spec = importlib.util.spec_from_file_location("preflight", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runner(table):
    """A fake runner: the first key whose words all appear in the command wins."""
    def run(argv, cwd=None, timeout=120):
        text = " ".join(argv)
        for words, answer in table.items():
            if all(w in text for w in words.split("|")):
                return answer
        return 127, "", "no fake answer for: " + text
    return run


class Version(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.root = Path(tempfile.mkdtemp())
        (self.root / "prefix").mkdir()

    def pin(self, value):
        (self.root / "prefix/package.json").write_text(json.dumps({"dependencies": {"@opencode/cli": value}}))

    def test_an_exact_pin_that_matches_the_binary_passes(self):
        self.pin("2.2.0")
        self.assertEqual(self.m.check_version(runner({"--version": (0, "opencode v2.2.0\n", "")}), self.root)[0], "PASS")

    def test_a_caret_pin_fails_because_it_can_drift(self):
        self.pin("^2.2.2")
        status, _, detail = self.m.check_version(runner({"--version": (0, "opencode v2.2.2\n", "")}), self.root)
        self.assertEqual(status, "FAIL")
        self.assertIn("not an exact version", detail)

    def test_a_binary_that_differs_from_the_pin_fails(self):
        self.pin("2.2.0")
        self.assertEqual(self.m.check_version(runner({"--version": (0, "opencode v2.2.2\n", "")}), self.root)[0], "FAIL")


class Services(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def test_active_v2_units_pass_and_a_stopped_v1_only_warns(self):
        fake = runner({"is-active|secure-opencode-v2": (0, "active\n", ""), "is-active|opencode-perm-v2": (0, "active\n", ""),
                       "is-active|secure-opencode.service": (3, "inactive\n", ""), "is-active|opencode-perm.service": (0, "active\n", "")})
        by_name = {n: s for s, n, _ in self.m.check_services(fake)}
        self.assertEqual(by_name["service secure-opencode-v2.service"], "PASS")
        self.assertEqual(by_name["V1 rollback path"], "WARN")

    def test_a_stopped_v2_unit_fails(self):
        fake = runner({"is-active": (3, "inactive\n", "")})
        self.assertEqual([s for s, n, _ in self.m.check_services(fake) if n.startswith("service ")], ["FAIL", "FAIL"])


class ConfigAndUnits(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def test_a_dry_run_with_pending_files_warns_and_names_them(self):
        out = "[derive-v2] would replace /x/opencode.json\n[derive-v2] dry-run - nothing was written.\n"
        status, _, detail = self.m.check_config_in_sync(runner({"derive-v2-config": (0, out, "")}))
        self.assertEqual(status, "WARN")
        self.assertIn("opencode.json", detail)

    def test_a_dry_run_with_nothing_pending_passes(self):
        self.assertEqual(self.m.check_config_in_sync(runner({"derive-v2-config": (0, "[derive-v2] dry-run - nothing was written.\n", "")}))[0], "PASS")

    def test_a_derive_failure_fails(self):
        self.assertEqual(self.m.check_config_in_sync(runner({"derive-v2-config": (2, "", "[derive-v2] refused: x\n")}))[0], "FAIL")

    def test_the_unit_files_pass_only_when_every_op_is_already_applied(self):
        ok = json.dumps({"counts": {"already_applied": 3}})
        drift = json.dumps({"counts": {"already_applied": 2, "conflict": 1}})
        self.assertEqual(self.m.check_units_changeset(runner({"changeset.py": (0, ok, "")}))[0], "PASS")
        self.assertEqual(self.m.check_units_changeset(runner({"changeset.py": (2, drift, "")}))[0], "WARN")
        self.assertEqual(self.m.check_units_changeset(runner({"changeset.py": (3, "not json", "")}))[0], "FAIL")


class RegistrationErrors(unittest.TestCase):
    def setUp(self):
        self.m = load()
        self.log = Path(tempfile.mkdtemp()) / "opencode.log"
        self.start = "Fri 2026-10-30 10:00:00 GMT"
        self.fake = runner({"ActiveEnterTimestamp": (0, self.start + "\n", "")})

    def test_a_rejected_registration_after_the_start_fails_and_names_the_tool(self):
        self.log.write_text('timestamp=2026-10-30T10:05:00.000Z level=ERROR message="Skipping invalid tool registration" name=read error="x"\n')
        status, _, detail = self.m.check_registration_errors(self.fake, self.log)
        self.assertEqual(status, "FAIL")
        self.assertIn("read", detail)

    def test_an_old_rejection_before_the_start_is_ignored(self):
        self.log.write_text('timestamp=2026-10-30T09:59:59.000Z level=ERROR message="Skipping invalid tool registration" name=read error="x"\n')
        self.assertEqual(self.m.check_registration_errors(self.fake, self.log)[0], "PASS")

    def test_an_unreadable_log_warns_instead_of_passing(self):
        self.assertEqual(self.m.check_registration_errors(self.fake, self.log.parent / "missing.log")[0], "WARN")


class Report(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def test_the_manual_gates_are_always_listed_and_never_pass_themselves(self):
        gates = [(s, d) for s, n, d in self.m.collect(runner({}), stack=False) if n == "gate"]
        self.assertEqual([g[0] for g in gates], ["MANUAL"] * len(self.m.MANUAL_GATES))
        self.assertIn("Code Mode cannot bypass approval", [g[1] for g in gates])

    def test_the_stack_check_runs_only_when_asked(self):
        names = lambda stack: [n for _, n, _ in self.m.collect(runner({}), stack=stack)]
        self.assertNotIn("stack check", names(False))
        self.assertIn("stack check", names(True))

    def test_the_stack_check_reports_failing_lines(self):
        out = "PASS a\nFAIL plugins: none failed to load (x)\n"
        status, _, detail = self.m.check_stack(runner({"check-v2-stack": (1, out, "")}))
        self.assertEqual(status, "FAIL")
        self.assertIn("plugins", detail)


if __name__ == "__main__":
    unittest.main()
