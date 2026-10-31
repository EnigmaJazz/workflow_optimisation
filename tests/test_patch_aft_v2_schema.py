"""scripts/patch-aft-v2-schema.py: the aft#1144 backport onto the installed 0.62.0 plugin (queue Q44)."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "patch-aft-v2-schema.py"


def load():
    spec = importlib.util.spec_from_file_location("patch_aft", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def make_plugin(version="0.62.0", name="@cortexkit/aft-opencode", body=None):
    m = load()
    root = Path(tempfile.mkdtemp())
    (root / "dist" / "entry").mkdir(parents=True)
    (root / "package.json").write_text(json.dumps({"name": name, "version": version}))
    text = "head\nfunction projectV2Tool(name, definition, location, consumers = {}) {\n  const hostName = v2HostToolName(name);\n" + (body if body is not None else m.BEFORE) + "  currentInput();\n}\ntail\n"
    for rel in m.TARGETS:
        (root / rel).write_text(text)
    return root, m


class Patch(unittest.TestCase):
    def test_dry_run_changes_nothing_and_apply_patches_both_bundles(self):
        root, m = make_plugin()
        before = {rel: (root / rel).read_text() for rel in m.TARGETS}
        self.assertEqual(m.main([str(root)]), 0)
        self.assertEqual({rel: (root / rel).read_text() for rel in m.TARGETS}, before)
        self.assertEqual(m.main([str(root), "--apply"]), 0)
        for rel in m.TARGETS:
            text = (root / rel).read_text()
            self.assertIn(m.MARKER, text)
            self.assertIn('"~standard"', text)
            self.assertIn("Unsupported JSON Schema target", text)
            self.assertEqual((root / (rel + ".orig-0.62.0")).read_text(), before[rel])  # the original is kept
        self.assertEqual(m.main(["--check", str(root)]), 0)

    def test_check_fails_on_an_unpatched_plugin_and_writes_nothing(self):
        root, m = make_plugin()
        self.assertEqual(m.main(["--check", str(root)]), 1)
        self.assertFalse(any(p.name.endswith(".orig-0.62.0") for p in root.rglob("*")))

    def test_a_second_apply_changes_nothing(self):
        root, m = make_plugin()
        m.main([str(root), "--apply"])
        once = {rel: (root / rel).read_text() for rel in m.TARGETS}
        self.assertEqual(m.main([str(root), "--apply"]), 0)
        self.assertEqual({rel: (root / rel).read_text() for rel in m.TARGETS}, once)

    def test_another_package_version_is_refused(self):
        for version in ("0.62.1", "0.63.4"):
            root, m = make_plugin(version=version)
            before = (root / m.TARGETS[0]).read_text()
            self.assertEqual(m.main([str(root), "--apply"]), 1)
            self.assertEqual((root / m.TARGETS[0]).read_text(), before)

    def test_another_package_is_refused(self):
        root, m = make_plugin(name="@cortexkit/something-else")
        self.assertEqual(m.main([str(root), "--apply"]), 1)

    def test_a_build_whose_function_differs_is_refused_without_touching_either_file(self):
        root, m = make_plugin()
        (root / m.TARGETS[1]).write_text("function projectV2Tool() { /* different build */ }\n")
        before = (root / m.TARGETS[0]).read_text()
        self.assertEqual(m.main([str(root), "--apply"]), 1)
        self.assertEqual((root / m.TARGETS[0]).read_text(), before)  # all-or-nothing: the first bundle is not patched either

    def test_a_marker_without_the_exact_patch_is_refused(self):
        root, m = make_plugin()
        (root / m.TARGETS[0]).write_text("// " + m.MARKER + "\n")
        self.assertEqual(m.main([str(root), "--apply"]), 1)

    def test_the_patched_text_is_valid_javascript(self):
        import shutil
        import subprocess
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        root, m = make_plugin()
        m.main([str(root), "--apply"])
        for rel in m.TARGETS:
            r = subprocess.run([node, "--check", str(root / rel)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
