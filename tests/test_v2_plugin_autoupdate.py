"""Automatic V2 plugin updates with guardrails (scripts/v2-plugin-autoupdate.py).

Facts from OpenCode V2 2.2.2 (opencode-v2-probe, FINDINGS-3.md): with a `~x.y.z` range, `plugin check` reports
"(update available)", `plugin update` installs into the package cache without touching the config, the loaded version
changes only after a restart, and the old cached copy stays. `plugin list` and `debug agents` need `--server`, a booted
project and OPENCODE_PASSWORD. The job updates only patch ranges, restarts, gates on every plugin loading, and rolls the
package back to an exact pin when the gate fails.
"""
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "v2-plugin-autoupdate.py"
PKG = "@fro.bot/systematic"


def load():
    spec = importlib.util.spec_from_file_location("v2_autoupdate", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v2_autoupdate"] = mod
    spec.loader.exec_module(mod)
    return mod


LIST_OK = "ID          VERSION  SOURCE\nsystematic  3.27.0   @fro.bot/systematic@~3.27.0\n"
CHECK_AVAILABLE = "Server\n  systematic 3.27.0 (update available)\n"
CHECK_CURRENT = "Server\n  systematic 3.27.2 (current)\n"


class Parsing(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def test_parse_list(self):
        got = self.m.parse_list(LIST_OK)
        self.assertEqual(got, {"systematic": {"version": "3.27.0", "source": "@fro.bot/systematic@~3.27.0"}})

    def test_parse_list_empty_and_garbage(self):
        self.assertEqual(self.m.parse_list("No plugins found\n"), {})
        self.assertEqual(self.m.parse_list(""), {})

    def test_a_failed_plugin_shows_up_with_the_dash_id(self):
        got = self.m.parse_list("ID  VERSION  SOURCE\n-   3.27.3   @fro.bot/systematic@~3.27.0\n")
        self.assertIn("-", got)

    def test_parse_check(self):
        self.assertEqual(self.m.parse_check(CHECK_AVAILABLE), {"systematic": "update available"})
        self.assertEqual(self.m.parse_check(CHECK_CURRENT), {"systematic": "current"})
        self.assertEqual(self.m.parse_check("No package plugins found\n"), {})

    def test_spec_policy(self):
        p = self.m.spec_policy
        self.assertEqual(p("@fro.bot/systematic@~3.27.0"), "patch-range")
        self.assertEqual(p("opencode-x@~1.2.3"), "patch-range")
        self.assertEqual(p("@fro.bot/systematic@3.27.2"), "exact")
        for bad in ["@fro.bot/systematic@^3.27.0", "@fro.bot/systematic@latest", "@fro.bot/systematic", "pkg@*", "pkg@>=1.0.0", "pkg@~3.27", "pkg@~3", "file:///x/y"]:
            self.assertEqual(p(bad), "ineligible", bad)


class Stack:
    """A stub V2 CLI plus a stub restart command, driven by files, so the job runs end to end."""

    def __init__(self, live="3.27.0", latest="3.27.2", broken=None, spec="~3.27.0"):
        self.dir = Path(tempfile.mkdtemp())
        self.state = self.dir / "state"
        self.state.mkdir()
        (self.state / "live").write_text(live)
        (self.state / "cached").write_text(live)
        (self.state / "latest").write_text(latest)
        (self.state / "broken").write_text(broken or "")
        self.config = self.dir / "opencode.json"
        self.config.write_text(json.dumps({"plugins": [f"{PKG}@{spec}"], "autoupdate": False}, indent=2))
        self.password = self.dir / "pw"
        self.password.write_text("THROWAWAY-PW\n")
        self.password.chmod(0o600)
        self.log = self.dir / "calls.log"
        self.bin = self.dir / "opencode2"
        self.bin.write_text(
            "#!/usr/bin/env bash\n"
            f'S="{self.state}"\n'
            f'echo "$* | PW=${{OPENCODE_PASSWORD:-}}" >> "{self.log}"\n'
            'case "$1 $2" in\n'
            '"plugin list")\n'
            '  v=$(cat $S/live); id=systematic; [ "$v" = "$(cat $S/broken)" ] && id=-\n'
            '  src=$(grep -o \'@fro.bot/systematic@[^"]*\' "' + str(self.config) + '" | head -1); printf "ID          VERSION  SOURCE\\n%s  %s   %s\\n" "$id" "$v" "$src" ;;\n'
            '"plugin check")\n'
            '  echo Server; if [ "$(cat $S/live)" != "$(cat $S/cached)" ]; then t="(current)"; elif [ "$(cat $S/live)" != "$(cat $S/latest)" ] && grep -q "~" "' + str(self.config) + '"; then t="(update available)"; else t="(current)"; fi\n'
            '  echo "  systematic $(cat $S/live) $t" ;;\n'
            '"plugin update") cp $S/latest $S/cached; echo "Updated Server plugin systematic" ;;\n'
            '"debug agents") echo "[]" ;;\n'
            'esac\n'
        )
        self.bin.chmod(0o755)
        self.restart = self.dir / "restart.sh"
        self.restart.write_text(
            "#!/usr/bin/env bash\n"
            f'S="{self.state}"; echo restart >> "{self.log}"\n'
            f'spec=$(grep -o \'systematic@[^"]*\' "{self.config}" | head -1 | cut -d@ -f2)\n'
            'case "$spec" in\n'
            '~*) cp $S/cached $S/live ;;\n'
            '*) echo "$spec" > $S/live; echo "$spec" > $S/cached ;;\n'
            'esac\n'
        )
        self.restart.chmod(0o755)

    def run(self, *extra):
        cmd = [sys.executable, str(SCRIPT), "--opencode", str(self.bin), "--server", "http://127.0.0.1:1",
               "--config", str(self.config), "--state-dir", str(self.dir / "jobstate"),
               "--password-file", str(self.password), "--restart-cmd", str(self.restart),
               "--boot-timeout", "5", "--settle", "0", *extra]
        return subprocess.run(cmd, capture_output=True, text=True)

    def live(self):
        return (self.state / "live").read_text().strip()

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def events(self):
        path = self.dir / "jobstate" / "autoupdate.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


class RequiredBranch(unittest.TestCase):
    def setUp(self):
        self.stack = Stack()
        self.checkout = self.stack.dir / "checkout"
        (self.checkout / "scripts").mkdir(parents=True)
        import shutil
        shutil.copy2(SCRIPT, self.checkout / "scripts" / SCRIPT.name)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", str(self.checkout)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "add", "scripts/v2-plugin-autoupdate.py"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "commit", "-m", "fixture"], check=True, capture_output=True)

    def run_checkout(self, *extra):
        cmd = [sys.executable, str(self.checkout / "scripts" / SCRIPT.name), "--opencode", str(self.stack.bin),
               "--server", "http://127.0.0.1:1", "--config", str(self.stack.config),
               "--state-dir", str(self.stack.dir / "branch-jobstate"), "--password-file", str(self.stack.password),
               "--restart-cmd", str(self.stack.restart), "--boot-timeout", "5", "--settle", "0", *extra]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_main_checkout_passes_required_branch_guard(self):
        result = self.run_checkout("--require-branch", "main", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("would-update", result.stdout)

    def test_feature_branch_is_refused_and_names_observed_branch(self):
        subprocess.run(["git", "-C", str(self.checkout), "checkout", "-b", "feature/test"], check=True, capture_output=True)
        result = self.run_checkout("--require-branch", "main", "--dry-run")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("feature/test", result.stderr)

    def test_feature_branch_is_accepted_without_guard(self):
        subprocess.run(["git", "-C", str(self.checkout), "checkout", "-b", "feature/test"], check=True, capture_output=True)
        result = self.run_checkout("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("would-update", result.stdout)

    def test_unit_template_uses_stable_checkout_and_branch_guard(self):
        template = (SCRIPT.parent.parent / "docs/systemd/v2-plugin-autoupdate.service.template").read_text()
        self.assertIn("%h/ai-workspace/workflow_optimisation-main/scripts/v2-plugin-autoupdate.py", template)
        self.assertIn("--require-branch main", template)


class EndToEnd(unittest.TestCase):
    def test_an_available_patch_update_is_installed_restarted_and_gated(self):
        s = Stack()
        r = s.run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(s.live(), "3.27.2")
        self.assertIn("restart", s.calls())
        self.assertTrue(any("plugin update" in c for c in s.calls()))
        self.assertEqual(json.loads(s.config.read_text())["plugins"], [f"{PKG}@~3.27.0"])  # config untouched
        self.assertIn("updated", [e["event"] for e in s.events()])

    def test_nothing_to_update_means_no_update_call_and_no_restart(self):
        s = Stack(live="3.27.2", latest="3.27.2")
        r = s.run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("restart", s.calls())
        self.assertFalse(any("plugin update" in c for c in s.calls()))

    def test_the_password_reaches_the_cli_only_through_the_environment(self):
        s = Stack()
        r = s.run()
        self.assertTrue(any("PW=THROWAWAY-PW" in c for c in s.calls()))
        self.assertTrue(all("THROWAWAY-PW" not in c.split(" | PW=")[0] for c in s.calls()))
        self.assertNotIn("THROWAWAY-PW", r.stdout + r.stderr)
        self.assertNotIn("THROWAWAY-PW", (s.dir / "jobstate" / "autoupdate.jsonl").read_text())

    def test_a_release_that_fails_to_load_is_rolled_back_to_the_previous_exact_version(self):
        s = Stack(broken="3.27.2")
        r = s.run()
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)  # rolled back, reported as a failure
        self.assertEqual(s.live(), "3.27.0")
        self.assertEqual(json.loads(s.config.read_text())["plugins"], [f"{PKG}@3.27.0"])
        self.assertTrue(list(s.dir.glob("opencode.json.bak-*")))
        events = [e["event"] for e in s.events()]
        self.assertIn("gate-failed", events)
        self.assertIn("rolled-back", events)
        self.assertEqual(s.calls().count("restart"), 2)

    def test_a_rollback_that_still_fails_the_gate_exits_3(self):
        s = Stack(broken="3.27.0")
        s.state.joinpath("live").write_text("3.27.0")
        (s.state / "broken").write_text("3.27.0")
        r = s.run()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)

    def test_ranges_wider_than_patch_are_never_updated(self):
        for spec in ("^3.27.0", "latest", "*"):
            s = Stack(spec=spec)
            r = s.run()
            self.assertFalse(any("plugin update" in c for c in s.calls()), spec)
            self.assertNotIn("restart", s.calls(), spec)
            self.assertIn("ineligible", [e["event"] for e in s.events()], spec)

    def test_dry_run_changes_nothing(self):
        s = Stack()
        r = s.run("--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(s.live(), "3.27.0")
        self.assertFalse(any("plugin update" in c for c in s.calls()))
        self.assertNotIn("restart", s.calls())
        self.assertIn("would-update", r.stdout)

    def test_a_loose_password_file_is_refused(self):
        s = Stack()
        s.password.chmod(0o644)
        r = s.run()
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(any("plugin" in c for c in s.calls()))

    def test_a_second_run_while_one_is_active_is_refused(self):
        s = Stack()
        import fcntl
        (s.dir / "jobstate").mkdir()
        with open(s.dir / "jobstate" / "lock", "w") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            r = s.run()
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)
        self.assertFalse(any("plugin update" in c for c in s.calls()))

    def test_the_config_is_never_edited_without_a_failed_gate(self):
        s = Stack()
        before = s.config.read_text()
        s.run()
        self.assertEqual(s.config.read_text(), before)


if __name__ == "__main__":
    unittest.main()
