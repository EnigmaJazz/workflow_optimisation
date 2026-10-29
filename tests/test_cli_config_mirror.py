"""Q44 unit 3: global-config/cli.json is mirrored before the first V2 TUI start, and the plugin-cache prune
and its health approval know about it.

V2 migrates only tui.json to cli.json on first TUI start, which would copy V1-only plugins across; a
mirrored cli.json (owned by this repo) prevents that. cli.json uses the key `plugins` (V1 files use `plugin`)."""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RECOVER = REPO / "verify" / "checkers" / "recover-cli-config.py"
PRUNE = REPO / "prune-opencode-plugin-cache.py"
SOURCE = {"$schema": "https://opencode.ai/v2/cli.json", "plugins": []}


def recover(live_text, source=SOURCE):
    tmp = Path(tempfile.mkdtemp())
    live, src, backups = tmp / "cfg" / "cli.json", tmp / "src.json", tmp / "backups"
    if source is not None:
        src.write_text(json.dumps(source))
    if live_text is not None:
        live.parent.mkdir()
        live.write_text(live_text)
    r = subprocess.run([sys.executable, str(RECOVER), str(live), str(src), str(backups), "run1"],
                       capture_output=True, text=True)
    return r, live, backups


class Recovery(unittest.TestCase):
    def test_missing_live_file_is_created_from_source(self):
        r, live, backups = recover(None)
        self.assertTrue(r.stdout.startswith("repaired\t"), r.stdout + r.stderr)
        self.assertEqual(json.loads(live.read_text()), SOURCE)
        self.assertTrue((backups / "run1" / "cli.json.before").exists())

    def test_identical_live_file_is_left_alone(self):
        r, live, backups = recover(json.dumps(SOURCE))
        self.assertTrue(r.stdout.startswith("clean\t"), r.stdout)
        self.assertFalse(backups.exists())

    def test_v1_only_plugins_copied_by_a_migration_are_removed_but_other_keys_survive(self):
        live = {"$schema": "x", "plugins": ["herdr@1.0.0"], "theme": "dark"}
        r, path, backups = recover(json.dumps(live))
        self.assertTrue(r.stdout.startswith("repaired\t"), r.stdout)
        got = json.loads(path.read_text())
        self.assertEqual(got["plugins"], [])
        self.assertEqual(got["theme"], "dark")
        self.assertEqual(json.loads((backups / "run1" / "cli.json.before").read_text()), live)

    def test_unreadable_live_file_is_replaced_and_backed_up(self):
        r, path, backups = recover("{not json")
        self.assertTrue(r.stdout.startswith("repaired\t"), r.stdout)
        self.assertEqual(json.loads(path.read_text()), SOURCE)
        self.assertEqual((backups / "run1" / "cli.json.before").read_text(), "{not json")

    def test_missing_source_is_an_error_and_touches_nothing(self):
        r, path, _ = recover(json.dumps({"plugins": ["a"]}), source=None)
        self.assertTrue(r.stdout.startswith("error\t"), r.stdout)
        self.assertEqual(json.loads(path.read_text()), {"plugins": ["a"]})


class Wiring(unittest.TestCase):
    def test_env_defines_the_cli_config_paths(self):
        text = (REPO / "verify" / "10-env.sh").read_text()
        self.assertIn("CLI_CONFIG_FILE=", text)
        self.assertIn("global-config/cli.json", text)

    def test_the_recovery_section_runs_the_helper(self):
        text = (REPO / "verify" / "50-section-0-recover.sh").read_text()
        self.assertIn("recover-cli-config.py", text)


def load_prune():
    spec = importlib.util.spec_from_file_location("prune_mod", PRUNE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Prune(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "opencode.json").write_text(json.dumps({"plugin": ["a@1.0.0"]}))

    def test_cli_json_plugins_are_protected_from_pruning(self):
        (self.tmp / "cli.json").write_text(json.dumps({"plugins": ["b@2.0.0"]}))
        ids, versions, refs, digests = load_prune().configured_plugins(self.tmp)
        self.assertEqual(ids, {"a", "b"})
        self.assertEqual(versions["b"], {"2.0.0"})
        self.assertIn("b@2.0.0", refs)
        self.assertIn("cli.json", digests)

    def test_without_cli_json_nothing_changes(self):
        ids, _, refs, digests = load_prune().configured_plugins(self.tmp)
        self.assertEqual((ids, refs, sorted(digests)), ({"a"}, ["a@1.0.0"], ["opencode.json"]))

    def test_cli_json_counts_for_the_running_config_mtime(self):
        (self.tmp / "cli.json").write_text("{}")
        os.utime(self.tmp / "opencode.json", (1000, 1000))
        os.utime(self.tmp / "cli.json", (5000, 5000))
        self.assertEqual(load_prune().config_mtime(self.tmp), 5000)


class Approval(unittest.TestCase):
    def approve(self, with_cli):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "opencode.json").write_text(json.dumps({"plugin": ["a@1.0.0"]}))
        (tmp / "tui.json").write_text(json.dumps({"plugin": []}))
        if with_cli:
            (tmp / "cli.json").write_text(json.dumps({"plugins": ["b@2.0.0"]}))
        script = f'source "{REPO}/verify/30-recover-config.sh"\nwrite_cache_prune_approval\n'
        env = {**os.environ, "CACHE_PRUNE_APPROVAL": str(tmp / "approval.json"),
               "OPENCODE_CONFIG_FILE": str(tmp / "opencode.json"), "TUI_CONFIG_FILE": str(tmp / "tui.json"),
               "CLI_CONFIG_FILE": str(tmp / "cli.json")}
        r = subprocess.run(["bash", "-c", script, str(REPO / "verify-workflow.sh")], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads((tmp / "approval.json").read_text()), tmp

    def test_present_cli_json_is_in_the_approval(self):
        approval, tmp = self.approve(True)
        self.assertEqual(approval["config_sha256"]["cli.json"], hashlib.sha256((tmp / "cli.json").read_bytes()).hexdigest())
        self.assertIn("b@2.0.0", approval["plugin_references"])

    def test_absent_cli_json_leaves_the_approval_as_before(self):
        approval, _ = self.approve(False)
        self.assertEqual(sorted(approval["config_sha256"]), ["opencode.json", "tui.json"])


if __name__ == "__main__":
    unittest.main()
