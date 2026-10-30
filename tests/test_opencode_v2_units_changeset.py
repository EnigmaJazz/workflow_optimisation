"""The OpenCode V2 units change set (changesets/opencode-v2-units, queue Q46).

It carries the only authorable content outside git for the V2 cutover: three systemd user unit files. These tests run the real
change-set tool in a throwaway HOME, so nothing touches the live ~/.config/systemd/user.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "scripts" / "changeset.py"
SET = REPO / "changesets" / "opencode-v2-units"
SANDBOX = Path.home() / "agent-sandbox-integration"


class UnitsChangeSet(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.units = self.home / ".config/systemd/user"
        (self.units / "secure-opencode-v2.service.d").mkdir(parents=True)
        self.journals = self.home / "journals"
        self.env = {"PATH": os.environ["PATH"], "HOME": str(self.home)}

    def run_tool(self, *args):
        result = subprocess.run([sys.executable, str(TOOL), *args], env=self.env, capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)

    def apply(self, *extra):
        return self.run_tool("apply", "--set", str(SET), "--journal-root", str(self.journals), "--allow-root", str(self.units), *extra)

    def outcomes(self, report):
        return [r["outcome"] for r in report["results"]]

    def journal(self, report):
        return report["journal"]

    def test_apply_creates_the_three_units_with_the_set_bytes_and_mode(self):
        code, report = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["applied"] * 3))
        for name, target in (("secure-opencode-v2.service", "secure-opencode-v2.service"),
                             ("github-review.conf", "secure-opencode-v2.service.d/github-review.conf"),
                             ("opencode-perm-v2.service", "opencode-perm-v2.service")):
            path = self.units / target
            self.assertEqual(path.read_bytes(), (SET / name).read_bytes(), name)
            self.assertEqual(path.stat().st_mode & 0o777, 0o644, name)

    def test_a_second_apply_changes_nothing(self):
        self.apply()
        code, report = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["already_applied"] * 3))

    def test_revert_removes_what_apply_created(self):
        _, applied = self.apply()
        code, reverted = self.run_tool("revert", "--journal", self.journal(applied), "--journal-root", str(self.journals), "--allow-root", str(self.units))
        self.assertEqual((code, self.outcomes(reverted)), (0, ["reverted"] * 3))
        self.assertFalse((self.units / "opencode-perm-v2.service").exists())  # positive control: it existed before the revert

    def test_revert_reports_drift_and_keeps_a_unit_edited_by_hand(self):
        _, applied = self.apply()
        edited = self.units / "opencode-perm-v2.service"
        edited.write_text(edited.read_text() + "Environment=EXTRA=1\n")
        code, reverted = self.run_tool("revert", "--journal", self.journal(applied), "--journal-root", str(self.journals), "--allow-root", str(self.units))
        self.assertEqual(code, 2)
        self.assertIn("drift", self.outcomes(reverted))
        self.assertIn("EXTRA=1", edited.read_text())

    def test_a_missing_drop_in_directory_is_a_conflict_not_a_created_directory(self):
        (self.units / "secure-opencode-v2.service.d").rmdir()
        code, report = self.apply()
        self.assertEqual(code, 2)
        self.assertIn("conflict", self.outcomes(report))
        self.assertFalse((self.units / "secure-opencode-v2.service.d").exists())

    def test_paths_outside_the_allowed_root_are_refused(self):
        code, report = self.run_tool("apply", "--set", str(SET), "--journal-root", str(self.journals), "--allow-root", str(self.home / "elsewhere"))
        self.assertEqual(code, 3)
        self.assertFalse((self.units / "opencode-perm-v2.service").exists())


class UnitContent(unittest.TestCase):
    def test_the_permission_unit_is_the_repo_template(self):
        self.assertEqual((SET / "opencode-perm-v2.service").read_bytes(), (REPO / "systemd" / "opencode-perm-v2.service").read_bytes())

    @unittest.skipUnless((SANDBOX / "docs/secure-opencode-v2.service.template").exists(), "sandbox repo not present")
    def test_the_server_unit_is_the_sandbox_template(self):
        self.assertEqual((SET / "secure-opencode-v2.service").read_bytes(), (SANDBOX / "docs/secure-opencode-v2.service.template").read_bytes())

    def test_the_drop_in_only_adds_the_github_token_file(self):
        self.assertEqual((SET / "github-review.conf").read_text(), "[Service]\nEnvironmentFile=%h/.config/opencode/github-review.env\n")


if __name__ == "__main__":
    unittest.main()
