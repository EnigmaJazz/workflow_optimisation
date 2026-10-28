"""Orphaned AFT download temp files are pruned by prune-opencode-plugin-cache.py.

The AFT plugin downloads its binary to ``~/.cache/aft/bin/v<version>/`` through a
temp file named ``aft.<pid>.<epoch-ms>.<hex>.tmp``. Interrupted downloads leave
those behind (about 31 GiB were found on 2026-10-28). The prune pass must delete
only provably orphaned ones: exact name shape, regular file, writer pid dead,
older than the minimum age. It runs independently of the OpenCode health
approval, which still gates plugin-cache pruning exactly as before.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "prune-opencode-plugin-cache.py"
TWO_HOURS_AGO = time.time() - 2 * 3600


def dead_pid() -> int:
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


class AftTempPrune(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.config = self.tmp / "config"
        self.config.mkdir()
        (self.config / "opencode.json").write_text(json.dumps({"plugin": []}))
        self.cache = self.tmp / "cache"
        self.approval = self.tmp / "approval.json"  # deliberately missing
        self.bin = self.tmp / "aft" / "bin"
        self.version_dir = self.bin / "v0.60.0"
        self.version_dir.mkdir(parents=True)

    def temp_file(self, pid, directory=None, age=TWO_HOURS_AGO, name=None):
        directory = directory or self.version_dir
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (name or f"aft.{pid}.1792276122914.fe27d886224ad8.tmp")
        path.write_bytes(b"x" * 4096)
        os.utime(path, (age, age))
        return path

    def run_prune(self, *extra, apply=True):
        args = [
            sys.executable,
            str(SCRIPT),
            "--config-dir", str(self.config),
            "--cache-dir", str(self.cache),
            "--approval-file", str(self.approval),
            "--aft-bin-dir", str(self.bin),
            "--aft-temp-min-age-hours", "1",
            *extra,
        ]
        if apply:
            args.append("--apply")
        return subprocess.run(args, capture_output=True, text=True)

    def test_dry_run_reports_orphan_and_deletes_nothing(self):
        orphan = self.temp_file(dead_pid())
        proc = self.run_prune(apply=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"would delete: {orphan}", proc.stdout)
        self.assertIn("aft temp: 1 file(s)", proc.stdout)
        self.assertTrue(orphan.exists())

    def test_apply_deletes_old_orphan(self):
        orphan = self.temp_file(dead_pid())
        proc = self.run_prune()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(orphan.exists())
        self.assertIn("pruned aft temp: 1 file(s)", proc.stdout)

    def test_keeps_file_younger_than_minimum_age(self):
        young = self.temp_file(dead_pid(), age=time.time())
        proc = self.run_prune()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(young.exists())

    def test_keeps_file_whose_writer_is_still_running(self):
        live = self.temp_file(os.getpid())
        proc = self.run_prune()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(live.exists())

    def test_keeps_files_that_do_not_match_the_exact_shape(self):
        pid = dead_pid()
        keep = [
            self.temp_file(pid, name="aft"),  # the real binary
            self.temp_file(pid, name=f"aft.{pid}.tmp"),
            self.temp_file(pid, name=f"other.{pid}.1792276122914.fe27d886224ad8.tmp"),
            self.temp_file(pid, directory=self.version_dir / "nested"),
            self.temp_file(pid, directory=self.bin / "not-a-version"),
            self.temp_file(pid, directory=self.bin),  # directly in bin/, not a version dir
        ]
        proc = self.run_prune()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for path in keep:
            self.assertTrue(path.exists(), path)

    def test_keeps_symlink_and_its_target(self):
        target = self.tmp / "outside.bin"
        target.write_bytes(b"precious")
        link = self.version_dir / f"aft.{dead_pid()}.1792276122914.fe27d886224ad8.tmp"
        link.symlink_to(target)
        os.utime(link, (TWO_HOURS_AGO, TWO_HOURS_AGO), follow_symlinks=False)
        proc = self.run_prune()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(link.is_symlink())
        self.assertEqual(target.read_bytes(), b"precious")

    def test_runs_without_approval_and_plugin_prune_still_refuses(self):
        orphan = self.temp_file(dead_pid())
        proc = self.run_prune()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(orphan.exists())
        self.assertIn("health approval is missing", proc.stdout + proc.stderr)

    def test_runs_while_auto_update_lock_exists(self):
        (self.config / ".auto-update.lock").write_text("")
        orphan = self.temp_file(dead_pid())
        proc = self.run_prune()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(orphan.exists())
        self.assertIn("skip: auto-update lock exists", proc.stdout)

    def test_missing_aft_directory_is_not_an_error(self):
        proc = subprocess.run(
            [
                sys.executable, str(SCRIPT),
                "--config-dir", str(self.config),
                "--cache-dir", str(self.cache),
                "--approval-file", str(self.approval),
                "--aft-bin-dir", str(self.tmp / "absent"),
                "--apply",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ok: no aft temp files", proc.stdout)

    def test_unreadable_version_dir_does_not_abort_the_run(self):
        locked = self.bin / "v0.61.0"
        locked.mkdir()
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o755)
        orphan = self.temp_file(dead_pid())
        proc = self.run_prune()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(orphan.exists())
        self.assertIn("health approval is missing", proc.stdout + proc.stderr)

    def test_out_of_range_pid_is_kept_and_does_not_abort_the_run(self):
        huge = self.temp_file(0, name="aft.99999999999999999999.1792276122914.ab.tmp")
        orphan = self.temp_file(dead_pid())
        proc = self.run_prune()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(huge.exists())
        self.assertFalse(orphan.exists())

    def test_rejects_negative_minimum_age(self):
        proc = self.run_prune("--aft-temp-min-age-hours", "-1")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--aft-temp-min-age-hours", proc.stderr)


if __name__ == "__main__":
    unittest.main()
