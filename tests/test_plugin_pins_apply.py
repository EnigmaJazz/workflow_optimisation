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
