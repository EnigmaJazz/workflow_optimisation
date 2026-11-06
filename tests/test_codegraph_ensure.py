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
