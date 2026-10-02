import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parent.parent / "scripts" / "plugin-cache-integrity.py"
OLD = time.time() - 3600


def run(*args):
    proc = subprocess.run([sys.executable, str(HELPER), *args], capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)


def age(path, ts):
    for dirpath, dirnames, filenames in os.walk(path, topdown=False):
        for name in dirnames + filenames:
            os.utime(os.path.join(dirpath, name), (ts, ts))
    os.utime(path, (ts, ts))


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.cache = self.tmp / "packages"
        self.quarantine = self.tmp / "q"
        self.lock = self.tmp / ".auto-update.lock"

    def make(self, pkg, ver, manifest_version="same", with_manifest=True):
        root = self.cache / f"{pkg}@{ver}"
        pkg_dir = root / "node_modules" / pkg
        (pkg_dir / "dist").mkdir(parents=True)
        (pkg_dir / "dist" / "index.js").write_text("x")
        (root / "node_modules" / "dep").mkdir(parents=True)
        if with_manifest:
            v = ver if manifest_version == "same" else manifest_version
            (pkg_dir / "package.json").write_text(json.dumps({"name": pkg, "version": v}))
        return root

    def scan(self, *specs, apply=True):
        args = ["scan", "--cache-root", str(self.cache), "--lock", str(self.lock),
                "--quarantine-dir", str(self.quarantine), "--min-age-seconds", "600"]
        for s in specs:
            args += ["--spec", s]
        if apply:
            args.append("--apply")
        return run(*args)[1]["results"]


class CheckPin(Base):
    def check(self, spec):
        return run("check-pin", "--cache-root", str(self.cache), "--spec", spec)

    def test_complete(self):
        self.make("plug", "1.2.3")
        code, out = self.check("plug@1.2.3")
        self.assertEqual(code, 0)
        self.assertTrue(out["complete"])

    def test_scoped(self):
        self.make("@cortexkit/x", "0.1.0")
        code, out = self.check("@cortexkit/x@0.1.0")
        self.assertEqual(code, 0)
        self.assertTrue(out["complete"])

    def test_missing_package_json_incident_shape(self):
        self.make("plug", "1.2.3", with_manifest=False)
        code, out = self.check("plug@1.2.3")
        self.assertEqual(code, 1)
        self.assertFalse(out["complete"])
        self.assertIn("missing", out["reason"])

    def test_version_mismatch(self):
        self.make("plug", "1.2.3", manifest_version="1.2.2")
        code, out = self.check("plug@1.2.3")
        self.assertEqual(code, 1)
        self.assertIn("mismatch", out["reason"])

    def test_absent(self):
        code, out = self.check("plug@9.9.9")
        self.assertEqual(code, 1)
        self.assertFalse(out["complete"])


class Scan(Base):
    def test_quarantines_old_incomplete_without_deleting(self):
        root = self.make("@cortexkit/x", "0.1.0", with_manifest=False)
        age(root, OLD)
        (res,) = self.scan("@cortexkit/x@0.1.0")
        self.assertEqual(res["action"], "quarantined")
        self.assertFalse(root.exists())
        dest = Path(res["quarantined_to"])
        self.assertTrue(str(dest).startswith(str(self.quarantine)))
        self.assertEqual((dest / "node_modules" / "@cortexkit" / "x" / "dist" / "index.js").read_text(), "x")
        self.assertTrue((dest / "node_modules" / "dep").is_dir())

    def test_defers_when_lock_present(self):
        root = self.make("plug", "1.0.0", with_manifest=False)
        age(root, OLD)
        self.lock.write_text("1")
        (res,) = self.scan("plug@1.0.0")
        self.assertEqual(res["action"], "deferred")
        self.assertIn("lock", res["detail"])
        self.assertTrue(root.exists())

    def test_defers_when_recent(self):
        root = self.make("plug", "1.0.0", with_manifest=False)
        (res,) = self.scan("plug@1.0.0")
        self.assertEqual(res["action"], "deferred")
        self.assertTrue(root.exists())

    def test_recent_file_inside_old_dir_defers(self):
        root = self.make("plug", "1.0.0", with_manifest=False)
        age(root, OLD)
        (root / "node_modules" / "plug" / "fresh").write_text("now")
        (res,) = self.scan("plug@1.0.0")
        self.assertEqual(res["action"], "deferred")

    def test_no_apply_reports_only(self):
        root = self.make("plug", "1.0.0", with_manifest=False)
        age(root, OLD)
        (res,) = self.scan("plug@1.0.0", apply=False)
        self.assertEqual(res["action"], "deferred")
        self.assertTrue(root.exists())

    def test_absent_reported_not_quarantined(self):
        (res,) = self.scan("plug@1.0.0")
        self.assertEqual(res["state"], "absent")
        self.assertNotIn("action", res)
        self.assertFalse(self.quarantine.exists())

    def test_complete_untouched(self):
        root = self.make("plug", "1.0.0")
        age(root, OLD)
        (res,) = self.scan("plug@1.0.0")
        self.assertEqual(res["state"], "complete")
        self.assertTrue(root.exists())


if __name__ == "__main__":
    unittest.main()
