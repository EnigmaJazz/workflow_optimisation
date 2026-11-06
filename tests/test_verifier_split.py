"""verify-workflow.sh is a thin entry that sources digest-bound modules from verify/ (queue Q04).

The entry pins every module's sha256 and refuses to run on any mismatch, missing module or unlisted
module file, so the single VERIFY_SCRIPT_SHA256 in workflow-health-check.ts still binds the whole
verifier. scripts/verifier_manifest.py regenerates the manifest and the pin."""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "verify-workflow.sh"
MODULES = REPO / "verify"
PLUGIN = REPO / "global-config/plugins/workflow-health-check.ts"
TOOL = REPO / "scripts/verifier_manifest.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(entry_text):
    block = re.search(r"# BEGIN VERIFY_MODULES\n(.*?)# END VERIFY_MODULES", entry_text, re.S).group(1)
    return re.findall(r'^\s*"([^ "]+) ([0-9a-f]{64})"', block, re.M)


def loader_text(entry_text):
    return re.search(r"(# BEGIN VERIFY_LOADER\n.*?# END VERIFY_LOADER)", entry_text, re.S).group(1)


class Manifest(unittest.TestCase):
    def test_manifest_matches_the_module_files_in_order(self):
        listed = manifest(ENTRY.read_text())
        self.assertGreater(len(listed), 10)
        on_disk = sorted(str(p.relative_to(MODULES)) for p in MODULES.rglob("*") if p.is_file())
        self.assertEqual([n for n, _ in listed], on_disk)
        for name, digest in listed:
            self.assertEqual(sha(MODULES / name), digest, name)

    def test_the_embedded_checkers_are_standalone_digest_bound_files(self):
        names = [n for n, _ in manifest(ENTRY.read_text())]
        for expected in ("checkers/check-runtime-agents.cjs", "checkers/check-systematic-resolution.cjs",
                         "checkers/check-parallel-dispatch.py", "checkers/routing-canonical.md"):
            self.assertIn(expected, names)

    def test_checkers_are_valid_scripts(self):
        for node_file in sorted((MODULES / "checkers").glob("*.cjs")):
            r = subprocess.run(["node", "--check", str(node_file)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{node_file.name}: {r.stderr[:200]}")
        for py_file in sorted((MODULES / "checkers").glob("*.py")):
            r = subprocess.run([sys.executable, "-I", "-c", f"import ast,sys;ast.parse(open(sys.argv[1]).read())", str(py_file)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{py_file.name}: {r.stderr[:200]}")

    def test_modules_install_each_checker_by_copying_it_not_by_embedding_it(self):
        text = "\n".join(p.read_text() for p in MODULES.glob("*.sh"))
        for var, name in (("RUNTIME_AGENT_CHECKER", "check-runtime-agents.cjs"), ("SYSTEMATIC_CHECKER", "check-systematic-resolution.cjs"),
                          ("PARALLEL_CHECKER", "check-parallel-dispatch.py"), ("ROUTING_CANONICAL", "routing-canonical.md")):
            self.assertIn(f'cat "$VERIFY_MODULE_DIR/checkers/{name}" > "${var}"', text)
            self.assertNotRegex(text, rf'cat > "\${var}" <<')

    def test_the_single_statement_modules_write_exactly_the_checker_bytes(self):
        for module, var, name in (("41-checker-systematic.sh", "SYSTEMATIC_CHECKER", "check-systematic-resolution.cjs"),
                                  ("42-checker-runtime-agents.sh", "RUNTIME_AGENT_CHECKER", "check-runtime-agents.cjs")):
            d = Path(tempfile.mkdtemp())
            try:
                out = d / "written"
                script = f'VERIFY_MODULE_DIR="{MODULES}"\n{var}="{out}"\nsource "{MODULES / module}"\n'
                r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, stdin=subprocess.DEVNULL)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(out.read_bytes(), (MODULES / "checkers" / name).read_bytes(), module)
            finally:
                shutil.rmtree(d, ignore_errors=True)

    def test_every_module_parses_cleanly(self):
        for module in sorted(MODULES.glob("*.sh")):
            r = subprocess.run(["bash", "-n", str(module)], capture_output=True, text=True)
            self.assertEqual((r.returncode, r.stderr.strip()), (0, ""), module.name)

    def test_the_plugin_pins_the_entry(self):
        pin = re.search(r'^const VERIFY_SCRIPT_SHA256 = "([0-9a-f]{64})";', PLUGIN.read_text(), re.M).group(1)
        self.assertEqual(pin, sha(ENTRY))

    def test_the_entry_has_no_checks_of_its_own(self):
        text = ENTRY.read_text()
        self.assertNotIn("check_plugin_loads", text)
        self.assertLess(len(text.splitlines()), 200)


class Loader(unittest.TestCase):
    """Runs the entry's own loader block against a scratch module directory."""

    def run_loader(self, files, listed=None, extra=None):
        d = Path(tempfile.mkdtemp())
        try:
            for name, body in files.items():
                (d / name).write_text(body)
            entries = listed if listed is not None else [(n, sha(d / n)) for n in sorted(files)]
            lines = "\n".join(f'  "{n} {h}"' for n, h in entries)
            script = f'VERIFY_MODULE_DIR="{d}"\nVERIFY_MODULES=(\n{lines}\n)\n{loader_text(ENTRY.read_text())}\necho "LOADED A=${{A:-unset}}"\n'
            for name, body in (extra or {}).items():
                (d / name).write_text(body)
            r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, stdin=subprocess.DEVNULL)
            return r.returncode, r.stdout, r.stderr
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_sources_in_order_and_shares_variables(self):
        rc, out, err = self.run_loader({"10-a.sh": "A=one\n", "20-b.sh": 'A="${A}-two"\n'})
        self.assertEqual((rc, out.strip()), (0, "LOADED A=one-two"), err)

    def test_a_tampered_module_is_refused_before_it_runs(self):
        rc, out, err = self.run_loader({"10-a.sh": "A=ran\n"}, listed=[("10-a.sh", "0" * 64)])
        self.assertEqual(rc, 2)
        self.assertNotIn("LOADED", out)
        self.assertIn("digest mismatch", err + out)

    def test_a_missing_module_is_refused(self):
        rc, out, err = self.run_loader({"10-a.sh": "A=1\n"}, listed=[("10-a.sh", "0" * 64), ("20-gone.sh", "1" * 64)])
        self.assertEqual(rc, 2)

    def test_an_unlisted_module_file_is_refused(self):
        rc, out, err = self.run_loader({"10-a.sh": "A=1\n"}, extra={"99-unlisted.sh": "A=evil\n"})
        self.assertEqual(rc, 2)
        self.assertIn("unlisted", err + out)

    def test_a_tampered_checker_file_is_refused_and_an_unlisted_one_too(self):
        d = Path(tempfile.mkdtemp())
        try:
            (d / "checkers").mkdir()
            (d / "10-a.sh").write_text("A=ok\n")
            (d / "checkers/x.cjs").write_text("// x\n")
            def run(listed):
                lines = "\n".join(f'  "{n} {h}"' for n, h in listed)
                script = f'VERIFY_MODULE_DIR="{d}"\nVERIFY_MODULES=(\n{lines}\n)\n{loader_text(ENTRY.read_text())}\necho "LOADED A=${{A:-unset}}"\n'
                r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, stdin=subprocess.DEVNULL)
                return r.returncode, r.stdout + r.stderr
            good = [("10-a.sh", sha(d / "10-a.sh")), ("checkers/x.cjs", sha(d / "checkers/x.cjs"))]
            self.assertEqual(run(good)[0], 0)                                  # control: clean run loads, .cjs is not sourced
            (d / "checkers/x.cjs").write_text("// tampered\n")
            rc, out = run(good)
            self.assertEqual(rc, 2)
            self.assertIn("checkers/x.cjs", out)
            (d / "checkers/x.cjs").write_text("// x\n")
            (d / "checkers/y.cjs").write_text("// unlisted\n")
            rc, out = run(good)
            self.assertEqual(rc, 2)
            self.assertIn("unlisted", out)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_positive_control_a_clean_run_loads(self):
        rc, out, err = self.run_loader({"10-a.sh": "A=ok\n"})
        self.assertEqual((rc, out.strip()), (0, "LOADED A=ok"))


class Tool(unittest.TestCase):
    def sandbox(self):
        d = Path(tempfile.mkdtemp())
        shutil.copy2(ENTRY, d / "verify-workflow.sh")
        shutil.copytree(MODULES, d / "verify")
        (d / "global-config/plugins").mkdir(parents=True)
        shutil.copy2(PLUGIN, d / "global-config/plugins/workflow-health-check.ts")
        return d

    def run_tool(self, d, *args):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(d), *args], capture_output=True, text=True)

    def test_check_passes_on_the_repo_and_fails_after_a_module_edit(self):
        d = self.sandbox()
        try:
            self.assertEqual(self.run_tool(d, "check").returncode, 0)
            with open(d / "verify/10-env.sh", "a") as f:
                f.write("# drift\n")
            r = self.run_tool(d, "check")
            self.assertEqual(r.returncode, 1)
            self.assertIn("10-env.sh", r.stdout + r.stderr)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_update_rewrites_the_manifest_and_repin_the_plugin(self):
        d = self.sandbox()
        try:
            with open(d / "verify/10-env.sh", "a") as f:
                f.write("# drift\n")
            self.assertEqual(self.run_tool(d, "update").returncode, 0)
            entry_sha = sha(d / "verify-workflow.sh")
            plugin = (d / "global-config/plugins/workflow-health-check.ts").read_text()
            self.assertIn(f'const VERIFY_SCRIPT_SHA256 = "{entry_sha}";', plugin)
            self.assertEqual(self.run_tool(d, "check").returncode, 0)
            self.assertIn(("10-env.sh", sha(d / "verify/10-env.sh")), manifest((d / "verify-workflow.sh").read_text()))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_update_is_idempotent(self):
        d = self.sandbox()
        try:
            self.run_tool(d, "update")
            first = sha(d / "verify-workflow.sh")
            self.run_tool(d, "update")
            self.assertEqual(first, sha(d / "verify-workflow.sh"))
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
