import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SET = REPO / "changesets/claude-md-trim"
CHECK = REPO / "scripts" / "claude-overlay-check.py"
CHANGESET = REPO / "scripts" / "changeset.py"
UPSTREAM = SET / "upstream"


def block(text, begin, end):
    lines = text.split("\n")
    assert lines.count(begin) == 1
    assert lines.count(end) == 1
    return "\n".join(lines[lines.index(begin) + 1:lines.index(end)]) + "\n"


def synthetic_claude_md():
    """Build a whole CLAUDE.md from committed content only.

    The private ~/.claude/CLAUDE.md snapshot is not committed, so the fixture is
    the two upstream block bodies between their markers plus short filler outside
    the markers that the change set must leave untouched.
    """
    orchestration = (UPSTREAM / "orchestrator.md").read_bytes()
    routing = (UPSTREAM / "agent-routing.md").read_bytes()
    assert orchestration.endswith(b"\n") and routing.endswith(b"\n")
    return (
        b"# CLAUDE.md\n\n"
        b"Personal preferences outside the gentle-ai managed blocks.\n\n"
        b"<!-- gentle-ai:orchestrator -->\n"
        + orchestration +
        b"<!-- /gentle-ai:orchestrator -->\n\n"
        b"## Local notes\n\nShort filler between the managed blocks.\n\n"
        b"<!-- gentle-ai:agent-routing -->\n"
        + routing +
        b"<!-- /gentle-ai:agent-routing -->\n\n"
        b"Trailing filler after the managed blocks.\n"
    )


def restore_block(current, source, begin, end):
    """Return `current` with one marked block's body replaced by the body in `source`."""
    reference = source.decode()
    body = reference[reference.index(begin) + len(begin):reference.index(end)]
    text = current.decode()
    start = text.index(begin) + len(begin)
    return (text[:start] + body + text[text.index(end):]).encode()


class ClaudeOverlay(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="claude-overlay-"))
        self.home = self.tmp / "home"
        (self.home / ".claude/skills/gentle-ai-orchestration").mkdir(parents=True)
        (self.home / ".claude/rules").mkdir(parents=True)
        self.claude = self.home / ".claude/CLAUDE.md"
        self.synthetic_fixture = synthetic_claude_md()
        self.claude.write_bytes(self.synthetic_fixture)
        self.journal = self.tmp / "journals"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def env(self):
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["XDG_CONFIG_HOME"] = str(self.tmp / "xdg")
        return env

    def run_overlay(self, args):
        proc = subprocess.run(
            [sys.executable, str(CHECK), "--root", str(REPO), "--journal-root",
             str(self.journal), "--json", *args], capture_output=True, text=True,
            timeout=300, env=self.env())
        return proc.returncode, json.loads(proc.stdout)

    def fixture(self):
        root = self.tmp / "repo"
        shutil.rmtree(root, ignore_errors=True)
        (root / "scripts").mkdir(parents=True)
        shutil.copy2(CHANGESET, root / "scripts/changeset.py")
        (root / "changesets").mkdir()
        return root

    def add_set(self, root, set_id, ops, content):
        set_dir = root / "changesets" / set_id
        set_dir.mkdir(parents=True)
        (set_dir / "changeset.json").write_text(json.dumps({
            "schema": "workflow-changeset/v1", "id": set_id,
            "description": "fixture", "ops": ops}))
        for name, data in content.items():
            (set_dir / name).write_bytes(data)

    def run_in(self, root, args):
        proc = subprocess.run(
            [sys.executable, str(CHECK), "--root", str(root), "--journal-root",
             str(self.journal), "--json", *args], capture_output=True, text=True,
            timeout=300, env=self.env())
        return proc.returncode, json.loads(proc.stdout)

    def state(self, report, name):
        return next(entry for entry in report["sets"] if entry["set"] == name)

    def test_changeset_expect_before_matches_upstream_byte_for_byte(self):
        doc = json.loads((SET / "changeset.json").read_text())
        self.assertEqual(doc["schema"], "workflow-changeset/v1")
        self.assertEqual(doc["id"], "claude-md-trim")
        self.assertEqual([op["op"] for op in doc["ops"]],
                         ["block_replace", "block_replace", "file_create"])
        orch = (SET / "upstream/orchestrator.md").read_text()
        routing = (SET / "upstream/agent-routing.md").read_text()
        snapshot = self.synthetic_fixture.decode()
        for op, expected in zip(doc["ops"][:2], (orch, routing)):
            self.assertEqual(op["expect_before"], expected)
            self.assertEqual(op["expect_before"], block(snapshot, op["begin"], op["end"]))
            self.assertNotEqual(op["expect_before"], op["value"])
            self.assertIn("~/.claude/skills/gentle-ai-orchestration/SKILL.md", op["value"])
        self.assertIn(block(routing, "<!-- gentle-ai:remote-authorization -->",
                            "<!-- /gentle-ai:remote-authorization -->"), doc["ops"][1]["value"])
        self.assertEqual(doc["ops"][-1]["op"], "file_create")
        self.assertEqual(doc["ops"][-1]["content_file"], "skill.md")
        self.assertEqual(doc["ops"][-1]["mode"], "0644")

    def test_skill_keeps_the_moved_text_verbatim_and_has_valid_frontmatter(self):
        skill = (SET / "skill.md").read_text()
        parts = skill.split("---\n")
        self.assertEqual(parts[0], "")
        metadata = dict(line.split(": ", 1) for line in parts[1].splitlines())
        self.assertEqual(metadata["name"], "gentle-ai-orchestration")
        description = metadata["description"].lower()
        for phrase in ("implementation", "delegation", "odd", "task sizing", "native review", "rdd"):
            self.assertIn(phrase, description)
        self.assertIn((SET / "upstream/orchestrator.md").read_text(), skill)
        self.assertIn((SET / "upstream/agent-routing.md").read_text(), skill)

    def test_snapshot_is_reapplicable_and_is_not_changed_by_a_report(self):
        code, report = self.run_overlay([])
        self.assertEqual(code, 2)
        self.assertEqual(self.state(report, "claude-md-trim")["state"], "reapplicable")
        self.assertEqual(report["counts"]["conflict"], 0)
        self.assertEqual(self.claude.read_bytes(), self.synthetic_fixture)

    def test_reapply_trims_creates_the_skill_and_stays_under_thirty_kilobytes(self):
        before = self.claude.read_bytes()
        code, report = self.run_overlay(["--reapply"])
        self.assertEqual(code, 2)
        entry = self.state(report, "claude-md-trim")
        self.assertEqual(entry["state"], "applied")
        self.assertTrue(entry["reapplied"])
        trimmed = self.claude.read_bytes()
        self.assertLess(len(trimmed), len(before))
        self.assertIn(b"Personal preferences outside the gentle-ai managed blocks.", trimmed)
        self.assertLess(len(trimmed), 30 * 1024)
        text = trimmed.decode()
        self.assertIn("<!-- gentle-ai:orchestrator -->", text)
        self.assertIn("<!-- gentle-ai:agent-routing -->", text)
        self.assertIn("gentle-ai-orchestration/SKILL.md", text)
        skill_path = self.home / ".claude/skills/gentle-ai-orchestration/SKILL.md"
        self.assertTrue(skill_path.is_file())
        self.assertEqual(skill_path.read_bytes(), (SET / "skill.md").read_bytes())

    def test_resync_makes_it_reapplicable_and_reapply_restores_the_trim(self):
        self.run_overlay(["--reapply"])
        trimmed = self.claude.read_bytes()
        self.claude.write_bytes(self.synthetic_fixture)
        code, report = self.run_overlay([])
        self.assertEqual(code, 2, report)
        self.assertEqual(self.state(report, "claude-md-trim")["state"], "reapplicable")
        self.assertEqual(self.claude.read_bytes(), self.synthetic_fixture)
        code, report = self.run_overlay(["--reapply"])
        self.assertEqual(code, 2, report)
        self.assertEqual(self.state(report, "claude-md-trim")["state"], "applied")
        self.assertEqual(self.claude.read_bytes(), trimmed)

    def check_partial_restoration(self, begin, end):
        self.run_overlay(["--reapply"])
        trimmed = self.claude.read_bytes()
        partially_restored = restore_block(trimmed, self.synthetic_fixture, begin, end)
        self.assertNotEqual(partially_restored, trimmed)
        self.assertNotEqual(partially_restored, self.synthetic_fixture)
        self.claude.write_bytes(partially_restored)
        code, report = self.run_overlay([])
        self.assertEqual(code, 2, report)
        self.assertEqual(self.state(report, "claude-md-trim")["state"], "reapplicable", report)
        self.assertEqual(self.claude.read_bytes(), partially_restored)
        code, report = self.run_overlay(["--reapply"])
        self.assertEqual(code, 2, report)
        self.assertEqual(self.state(report, "claude-md-trim")["state"], "applied", report)
        self.assertEqual(self.claude.read_bytes(), trimmed)

    def test_restoring_only_the_orchestrator_block_keeps_the_set_reapplicable(self):
        self.check_partial_restoration(
            "<!-- gentle-ai:orchestrator -->", "<!-- /gentle-ai:orchestrator -->")

    def test_restoring_only_the_agent_routing_block_keeps_the_set_reapplicable(self):
        self.check_partial_restoration(
            "<!-- gentle-ai:agent-routing -->", "<!-- /gentle-ai:agent-routing -->")

    def test_changed_upstream_text_is_a_conflict_and_bytes_stay_untouched(self):
        changed = self.synthetic_fixture.replace(
            b"Gentle AI is an ecosystem configurator",
            b"Gentle AI is a changed ecosystem configurator", 1)
        self.assertNotEqual(changed, self.synthetic_fixture)
        self.claude.write_bytes(changed)
        before = self.claude.read_bytes()
        code, report = self.run_overlay(["--reapply"])
        self.assertEqual(code, 1)
        entry = self.state(report, "claude-md-trim")
        self.assertEqual(entry["state"], "conflict")
        self.assertFalse(entry["reapplied"])
        self.assertEqual(self.claude.read_bytes(), before)

    def test_revert_restores_the_snapshot_byte_for_byte(self):
        self.run_overlay(["--reapply"])
        journals = [p for p in (self.journal / "claude-md-trim").rglob("journal.jsonl")
                    if not p.parent.name.startswith("revert-")]
        self.assertTrue(journals, "apply journal missing")
        journal = max(journals, key=lambda p: p.stat().st_mtime_ns)
        proc = subprocess.run(
            [sys.executable, str(CHANGESET), "revert", "--journal", str(journal),
             "--journal-root", str(self.journal)], capture_output=True, text=True,
            timeout=300, env=self.env())
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(any(row.get("outcome") == "drift"
                             for row in json.loads(proc.stdout)["results"]))
        self.assertEqual(self.claude.read_bytes(), self.synthetic_fixture)
        self.assertFalse((self.home / ".claude/skills/gentle-ai-orchestration/SKILL.md").exists())

    def test_check_ignores_non_claude_sets(self):
        _, report = self.run_overlay([])
        expected = sorted(p.name for p in (REPO / "changesets").glob("claude-*")
                          if (p / "changeset.json").is_file())
        self.assertEqual(sorted(entry["set"] for entry in report["sets"]), expected)
        self.assertEqual(self.state(report, "claude-advisor-triggers")["state"], "superseded")
        self.assertTrue(self.state(report, "claude-md-trim")["persistent"])
        self.assertFalse(self.state(report, "claude-advisor-triggers")["persistent"])

    def test_reverted_set_is_never_reapplied(self):
        root = self.fixture()
        op = {"op": "file_create", "file": "~/.claude/rules/probe.md",
              "content_file": "probe.md", "mode": "0644"}
        self.add_set(root, "claude-md-trim", [op], {"probe.md": b"probe\n"})
        code, report = self.run_in(root, ["--reapply"])
        self.assertEqual(code, 2)
        self.assertEqual(self.state(report, "claude-md-trim")["state"], "applied")
        target = self.home / ".claude/rules/probe.md"
        self.assertTrue(target.is_file())
        target.unlink()
        shutil.rmtree(self.journal / "claude-md-trim", ignore_errors=True)
        journal = self.journal / "claude-md-trim/20260101T000000000000Z-1/journal.jsonl"
        journal.parent.mkdir(parents=True)
        journal.write_text(json.dumps({"type": "header", "schema": "workflow-changeset-journal/v1",
                                       "kind": "revert", "set_id": "claude-md-trim",
                                       "started": "2026-01-01T00:00:00+00:00"}) + "\n")
        code, report = self.run_in(root, ["--reapply"])
        entry = self.state(report, "claude-md-trim")
        self.assertEqual(code, 0)
        self.assertEqual(entry["state"], "reverted")
        self.assertFalse(entry["persistent"])
        self.assertFalse(target.exists())

    def test_remove_plus_create_is_judged_by_final_state(self):
        root = self.fixture()
        ops = [{"op": "file_remove", "file": "~/.claude/rules/probe.md",
                "expect_sha256": hashlib.sha256(b"old\n").hexdigest()},
               {"op": "file_create", "file": "~/.claude/rules/probe.md",
                "content_file": "new.md", "mode": "0644"}]
        self.add_set(root, "claude-delegation", ops, {"new.md": b"new\n"})
        target = self.home / ".claude/rules/probe.md"
        target.write_bytes(b"new\n")
        code, report = self.run_in(root, [])
        self.assertEqual(code, 0)
        self.assertEqual(self.state(report, "claude-delegation")["state"], "applied")
        target.write_bytes(b"other\n")
        code, report = self.run_in(root, [])
        self.assertEqual(code, 1)
        self.assertEqual(self.state(report, "claude-delegation")["state"], "conflict")

    def test_superseded_set_is_skipped(self):
        ops = [{"op": "file_remove", "file": "~/.claude/rules/probe.md",
                "expect_sha256": hashlib.sha256(b"old\n").hexdigest()},
               {"op": "file_create", "file": "~/.claude/rules/probe.md",
                "content_file": "new.md", "mode": "0644"}]
        root = self.fixture()
        self.add_set(root, "claude-advisor-triggers", ops, {"new.md": b"new\n"})
        (self.home / ".claude/rules/probe.md").write_bytes(b"other\n")
        code, report = self.run_in(root, [])
        entry = self.state(report, "claude-advisor-triggers")
        self.assertEqual(code, 0)
        self.assertEqual(entry["state"], "superseded")
        self.assertIn("claude-model-routing", entry["reason"])
        root = self.fixture()
        self.add_set(root, "claude-delegation", ops, {"new.md": b"new\n"})
        code, report = self.run_in(root, [])
        self.assertEqual(code, 1)
        self.assertEqual(self.state(report, "claude-delegation")["state"], "conflict")

    def test_non_persistent_set_is_reported_but_not_reapplied(self):
        op = {"op": "file_create", "file": "~/.claude/rules/probe.md",
              "content_file": "probe.md", "mode": "0644"}
        root = self.fixture()
        self.add_set(root, "claude-delegation", [op], {"probe.md": b"probe\n"})
        code, report = self.run_in(root, ["--reapply"])
        entry = self.state(report, "claude-delegation")
        self.assertEqual(code, 0)
        self.assertEqual(entry["state"], "reapplicable")
        self.assertFalse(entry["persistent"])
        self.assertFalse((self.home / ".claude/rules/probe.md").exists())
        root = self.fixture()
        self.add_set(root, "claude-md-trim", [op], {"probe.md": b"probe\n"})
        code, report = self.run_in(root, ["--reapply"])
        self.assertEqual(code, 2)
        self.assertEqual(self.state(report, "claude-md-trim")["state"], "applied")
        self.assertTrue((self.home / ".claude/rules/probe.md").is_file())


if __name__ == "__main__":
    unittest.main()
