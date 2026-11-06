"""scripts/plugin_pins.py: consume the auto-update plugin's pending-updates.json (OpenCode V2 prep)."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("plugin_pins", ROOT / "scripts" / "plugin_pins.py")
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)

SERVER = '{\n  "plugin": [\n    "a@1.0.0",\n    "@s/b@2.0.0",\n    "/local.ts"\n  ],\n  "x": 1\n}\n'
TUI = '{\n  "plugin": [\n    "a@1.0.0",\n    "c@3.0.0"\n  ]\n}\n'


def proposals(**over):
    base = [
        {"name": "a", "current": "1.0.0", "candidate": "1.0.1", "verdict": "propose", "reason": "ok", "checkedAt": 1},
        {"name": "@s/b", "current": "2.0.0", "candidate": "3.0.0", "verdict": "hold", "reason": "major-bump", "checkedAt": 1},
        {"name": "c", "current": "3.0.0", "candidate": "3.1.0", "verdict": "reject", "reason": "v2-only", "checkedAt": 1},
    ]
    return {"schema": pp.SCHEMA, "generatedAt": "t", "host": {"major": 1, "version": "1.19.5"}, "proposals": base, **over}


class Case(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)
        self.cfg = self.d / "global-config"
        self.cfg.mkdir()
        (self.cfg / "opencode.json").write_text(SERVER)
        (self.cfg / "tui.json").write_text(TUI)
        self.pending = self.d / "pending.json"
        self.pending.write_text(json.dumps(proposals()))

    def apply(self, approve, **kw):
        return pp.apply(self.pending, self.cfg, approve, **kw)


class ApplyTests(Case):
    def test_apply_changes_only_the_pin_in_every_file(self):
        self.apply(["a"])
        self.assertEqual((self.cfg / "opencode.json").read_text(), SERVER.replace("a@1.0.0", "a@1.0.1"))
        self.assertEqual((self.cfg / "tui.json").read_text(), TUI.replace("a@1.0.0", "a@1.0.1"))

    def test_unapproved_proposals_untouched(self):
        self.apply(["a"])
        self.assertIn("@s/b@2.0.0", (self.cfg / "opencode.json").read_text())

    def test_hold_and_reject_cannot_be_approved(self):
        for name in ("@s/b", "c"):
            with self.assertRaises(pp.Refusal):
                self.apply([name])
        self.assertEqual((self.cfg / "opencode.json").read_text(), SERVER)

    def test_stale_proposal_is_refused(self):
        (self.cfg / "opencode.json").write_text(SERVER.replace("a@1.0.0", "a@1.0.5"))
        with self.assertRaises(pp.Refusal):
            self.apply(["a"])

    def test_explicit_version_must_match_candidate(self):
        with self.assertRaises(pp.Refusal):
            self.apply(["a=9.9.9"])
        self.apply(["a=1.0.1"])

    def test_unknown_name_is_refused(self):
        with self.assertRaises(pp.Refusal):
            self.apply(["zzz"])

    def test_dry_run_writes_nothing(self):
        out = self.apply(["a"], dry_run=True)
        self.assertEqual((self.cfg / "opencode.json").read_text(), SERVER)
        self.assertEqual(out, [("opencode.json", "a", "1.0.0", "1.0.1"), ("tui.json", "a", "1.0.0", "1.0.1")])

    def test_bad_schema_is_refused(self):
        self.pending.write_text(json.dumps(proposals(schema="other/v9")))
        with self.assertRaises(pp.Refusal):
            self.apply(["a"])

    def test_result_must_stay_valid_json(self):
        (self.cfg / "opencode.json").write_text('{"plugin": ["a@1.0.0",]}')
        with self.assertRaises(pp.Refusal):
            self.apply(["a"])

    def test_no_occurrence_is_refused(self):
        (self.cfg / "opencode.json").write_text('{"plugin": []}')
        (self.cfg / "tui.json").write_text('{"plugin": []}')
        with self.assertRaises(pp.Refusal):
            self.apply(["a"])


class InputValidationTests(Case):
    def write_pending(self, candidate, current="1.0.0"):
        doc = proposals()
        doc["proposals"][0].update({"candidate": candidate, "current": current})
        self.pending.write_text(json.dumps(doc))

    def test_candidate_with_a_quote_cannot_splice_a_new_entry(self):
        self.write_pending('1.0.1", "evil@9.9.9')
        with self.assertRaises(pp.Refusal) as ctx:
            self.apply(["a"])
        self.assertIn("plain version", str(ctx.exception))
        self.assertEqual((self.cfg / "opencode.json").read_text(), SERVER)

    def test_non_semver_candidates_are_refused(self):
        for bad in ("latest", "1.0", "v1.0.1", "1.0.1 ", "1.0.1\n", "../x", ""):
            self.write_pending(bad)
            with self.assertRaises(pp.Refusal, msg=repr(bad)):
                self.apply(["a"])

    def test_prerelease_and_build_versions_are_plain_versions(self):
        self.write_pending("1.0.1-rc.1+build.5")
        self.apply(["a"])
        self.assertIn('"a@1.0.1-rc.1+build.5"', (self.cfg / "opencode.json").read_text())

    def test_the_same_name_approved_twice_is_applied_once(self):
        out = self.apply(["a", "a", "a=1.0.1"])
        self.assertEqual(out, [("opencode.json", "a", "1.0.0", "1.0.1"), ("tui.json", "a", "1.0.0", "1.0.1")])
        self.assertIn("a@1.0.1", (self.cfg / "opencode.json").read_text())

    def test_conflicting_versions_for_one_name_are_refused(self):
        with self.assertRaises(pp.Refusal):
            self.apply(["a=1.0.1", "a=1.0.2"])
        self.assertEqual((self.cfg / "opencode.json").read_text(), SERVER)


class HardeningTests(Case):
    def test_partial_write_failure_rolls_back_both_files(self):
        real = pp.os.replace
        calls = {"n": 0}

        def flaky(src, dst):
            calls["n"] += 1
            if calls["n"] == 2:
                raise PermissionError("simulated")
            return real(src, dst)

        pp.os.replace = flaky
        try:
            with self.assertRaises(pp.Refusal):
                self.apply(["a"])
        finally:
            pp.os.replace = real
        self.assertEqual((self.cfg / "opencode.json").read_text(), SERVER)
        self.assertEqual((self.cfg / "tui.json").read_text(), TUI)
        self.assertEqual([p.name for p in self.cfg.iterdir()], ["opencode.json", "tui.json"])

    def test_duplicate_pin_in_one_file_is_refused(self):
        (self.cfg / "opencode.json").write_text(SERVER.replace('"/local.ts"', '"a@1.0.0"'))
        with self.assertRaises(pp.Refusal):
            self.apply(["a"])

    def test_cli_refuses_config_dir_outside_the_repo_source(self):
        rc = pp.main(["--pending", str(self.pending), "--config-dir", str(self.cfg), "apply", "--approve", "a", "--dry-run"])
        self.assertEqual(rc, 3)
        rc = pp.main(["--pending", str(self.pending), "--config-dir", str(self.cfg), "--allow-outside-repo", "apply", "--approve", "a", "--dry-run"])
        self.assertEqual(rc, 0)

    def test_default_config_dir_is_the_repo_global_config(self):
        self.assertEqual(pp.DEFAULT_CONFIG_DIR, ROOT / "global-config")


class ReportTests(Case):
    def test_report_lists_each_verdict(self):
        rows = pp.report(self.pending, self.cfg)
        self.assertEqual([(r["name"], r["verdict"], r["in_source"]) for r in rows],
                         [("a", "propose", True), ("@s/b", "hold", True), ("c", "reject", True)])

    def test_report_flags_source_drift(self):
        (self.cfg / "tui.json").write_text(TUI.replace("c@3.0.0", "c@3.0.2"))
        row = [r for r in pp.report(self.pending, self.cfg) if r["name"] == "c"][0]
        self.assertFalse(row["in_source"])


if __name__ == "__main__":
    unittest.main()
