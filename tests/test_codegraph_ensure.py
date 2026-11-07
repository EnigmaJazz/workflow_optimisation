"""codegraph-ensure.sh creates a missing CodeGraph index once, and only in real project checkouts."""

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "codegraph-ensure.sh"


class Ensure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.path.expanduser("~"))
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.bin, self.calls = root / "bin", root / "calls.log"
        self.bin.mkdir()
        fake = self.bin / "gentle-ai"
        fake.write_text(
            '#!/usr/bin/env bash\n'
            f'echo "$@" >> "{self.calls}"\n'
            'mkdir -p "${@: -1}/.codegraph"\n'
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        self.repo = root / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def run_ensure(self, *dirs, home=None):
        env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}", "HOME": home or os.environ["HOME"]}
        return subprocess.run([str(SCRIPT), *map(str, dirs)], env=env, capture_output=True, text=True)

    def calls_made(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def test_initialises_a_missing_index_once(self):
        first = self.run_ensure(self.repo)
        self.assertEqual(first.returncode, 0)
        self.assertTrue((self.repo / ".codegraph").is_dir())
        self.assertIn("initialised", first.stdout)
        second = self.run_ensure(self.repo)
        self.assertIn("present", second.stdout)
        self.assertEqual(len(self.calls_made()), 1)

    def test_subdirectory_resolves_to_the_checkout_root(self):
        sub = self.repo / "a" / "b"
        sub.mkdir(parents=True)
        self.run_ensure(sub)
        self.assertTrue((self.repo / ".codegraph").is_dir())
        self.assertFalse((sub / ".codegraph").exists())

    def test_skips_a_non_git_directory(self):
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        result = self.run_ensure(plain)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.calls_made(), [])

    def test_skips_the_home_directory(self):
        subprocess.run(["git", "init", "-q", self.tmp.name], check=True)
        result = self.run_ensure(self.tmp.name, home=self.tmp.name)
        self.assertIn("skip", result.stderr)
        self.assertEqual(self.calls_made(), [])
        self.assertFalse((Path(self.tmp.name) / ".codegraph").exists())

    def test_reports_failure_when_init_creates_nothing(self):
        (self.bin / "gentle-ai").write_text("#!/usr/bin/env bash\nexit 0\n")
        result = self.run_ensure(self.repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAILED", result.stderr)


if __name__ == "__main__":
    unittest.main()


class DispatchWorker(unittest.TestCase):
    """dispatch-worker.sh prepends the Codex command policy to a Codex --spec only."""

    DISPATCH = Path(__file__).resolve().parent.parent / "scripts" / "dispatch-worker.sh"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.path.expanduser("~"))
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.bin, self.out = root / "bin", root / "orca.args"
        self.bin.mkdir()
        for name, body in {
            "orca": f'printf "%s\\n" "$@" >> "{self.out}"\n'
            '[ "$1 $2" = "orchestration worker-start" ] && echo \'{"result":{"dispatch":{"dispatchId":"ctx_abc"}}}\'\n'
            'true\n',
            "gentle-ai": 'mkdir -p "${@: -1}/.codegraph"\n',
        }.items():
            f = self.bin / name
            f.write_text("#!/usr/bin/env bash\n" + body)
            f.chmod(f.stat().st_mode | stat.S_IXUSR)
        self.repo = root / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def dispatch(self, *args):
        env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}"}
        subprocess.run([str(self.DISPATCH), str(self.repo), *args], env=env, check=True, capture_output=True)
        return self.out.read_text()

    def test_codex_spec_gets_the_command_policy_and_keeps_the_task(self):
        sent = self.dispatch("--agent", "codex", "--spec", "REVIEW THE DIFF", "--run", "run_x")
        self.assertIn("## Command policy (Codex)", sent)
        self.assertIn("Never `sed -n`", sent)
        self.assertIn("REVIEW THE DIFF", sent)
        self.assertIn("--run\nrun_x", sent)

    def test_opencode2_dispatch_is_retained_for_reuse_and_codex_is_not(self):
        self.dispatch("--agent", "opencode2", "--spec", "X")
        self.assertIn("worker-retain\n--dispatch\nctx_abc", self.out.read_text())
        self.out.unlink()
        self.dispatch("--agent", "codex", "--spec", "X")
        self.assertNotIn("worker-retain", self.out.read_text())

    def test_other_agents_spec_is_untouched(self):
        sent = self.dispatch("--agent", "opencode2", "--spec", "IMPLEMENT", "--run", "run_x")
        self.assertNotIn("Command policy", sent)
        self.assertIn("IMPLEMENT", sent)
        self.assertNotIn("Routing rules", sent)


class ReleaseSettled(unittest.TestCase):
    """Only settled, owned, not-yet-released workers are released."""

    @staticmethod
    def worker(state="reclaimable", owner="owned", release="not_requested", run="run_1"):
        return {"dispatchId": "ctx_1", "runId": run, "terminalState": state,
                "resource": {"ownershipState": owner, "releaseState": release}}

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "rsw", Path(__file__).resolve().parent.parent / "scripts" / "release-settled-workers.py")
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_releases_a_settled_owned_worker(self):
        self.assertTrue(self.mod.releasable(self.worker()))

    def test_skips_active_retained_user_owned_and_already_released(self):
        for w in (self.worker(state="active"), self.worker(state="retained"),
                  self.worker(owner="user_owned"), self.worker(release="requested")):
            self.assertFalse(self.mod.releasable(w))

    def test_run_filter(self):
        self.assertFalse(self.mod.releasable(self.worker(run="run_2"), "run_1"))


class WatchFilter(unittest.TestCase):
    def test_wanted_filters_by_run_and_sender(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "ow", Path(__file__).resolve().parent.parent / "scripts" / "orca-watch.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        m = {"run_id": "run_a", "from_handle": "term_1"}
        self.assertTrue(mod.wanted(m, [], []))
        self.assertTrue(mod.wanted(m, ["run_a"], []))
        self.assertFalse(mod.wanted(m, ["run_b"], []))
        self.assertTrue(mod.wanted(m, [], ["term_"]))
        self.assertFalse(mod.wanted(m, [], ["structworker_"]))
