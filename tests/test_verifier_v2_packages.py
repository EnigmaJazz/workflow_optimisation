"""Verifier V2 mode (queue Q44): plugin packages are resolved from the V2 npm cache against their ~/^ ranges."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESOLVER = REPO / "verify" / "checkers" / "v2-plugin-resolve.py"
NAME = "@fro.bot/systematic"


def resolve(config, cache, name=NAME):
    path = Path(tempfile.mkdtemp()) / "opencode.json"
    path.write_text(json.dumps(config))
    out = subprocess.run([sys.executable, str(RESOLVER), str(path), str(cache), name], capture_output=True, text=True).stdout.strip()
    return out.split("\t")


def install(cache, spec, epoch, version, name=NAME):
    root = Path(cache) / f"{name}@{spec}" / str(epoch) / "node_modules" / name
    root.mkdir(parents=True)
    (root / "package.json").write_text(json.dumps({"name": name, "version": version}))
    return root


class Resolver(unittest.TestCase):
    def setUp(self):
        self.cache = Path(tempfile.mkdtemp())

    def test_a_tilde_range_resolves_to_the_newest_epoch(self):
        install(self.cache, "~3.27.2", 1000, "3.27.2")
        newest = install(self.cache, "~3.27.2", 2000, "3.27.5")
        got = resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)
        self.assertEqual(got, ["ok", str(newest), "3.27.5", f"{NAME}@~3.27.2"])

    def test_epochs_compare_numerically_not_alphabetically(self):
        install(self.cache, "~3.27.2", 999, "3.27.2")
        newest = install(self.cache, "~3.27.2", 1000, "3.27.4")
        self.assertEqual(resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)[1], str(newest))

    def test_the_v1_plugin_key_is_read_too(self):
        install(self.cache, "3.27.2", 1, "3.27.2")
        self.assertEqual(resolve({"plugin": [f"{NAME}@3.27.2"]}, self.cache)[0], "ok")

    def test_a_version_outside_the_range_is_an_error(self):
        install(self.cache, "~3.27.2", 1, "3.28.0")
        got = resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)
        self.assertEqual(got[0], "error")
        self.assertIn("outside the configured range", got[1])

    def test_a_range_that_is_not_installed_is_an_error(self):
        got = resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)
        self.assertEqual(got[0], "error")
        self.assertIn("not materialized", got[1])

    def test_unpinned_missing_and_duplicate_entries_are_errors(self):
        self.assertIn("not pinned", resolve({"plugins": [NAME]}, self.cache)[1])
        self.assertIn("not pinned", resolve({"plugins": [f"{NAME}@latest"]}, self.cache)[1])
        self.assertIn("no @fro.bot/systematic plugin entry", resolve({"plugins": ["other@1.0.0"]}, self.cache)[1])
        self.assertIn("multiple", resolve({"plugins": [f"{NAME}@~3.27.2", f"{NAME}@3.27.2"]}, self.cache)[1])

    def test_a_similarly_named_package_is_not_matched(self):
        install(self.cache, "~3.27.2", 1, "3.27.2")
        self.assertEqual(resolve({"plugins": [f"{NAME}-extra@~3.27.2"]}, self.cache)[0], "error")

    def test_an_unreadable_config_is_an_error_not_a_pass(self):
        self.assertEqual(subprocess.run([sys.executable, str(RESOLVER), "/nonexistent.json", str(self.cache), NAME], capture_output=True, text=True).stdout.split("\t")[0], "error")

    def test_range_semantics(self):
        sys.path.insert(0, str(RESOLVER.parent))
        import importlib.util
        spec = importlib.util.spec_from_file_location("v2_plugin_resolve", RESOLVER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for version, rng, ok in [("3.27.2", "~3.27.2", True), ("3.27.1", "~3.27.2", False), ("3.28.0", "~3.27.2", False),
                                 ("0.49.30", "~0.49.29", True), ("0.50.0", "~0.49.29", False),
                                 ("3.9.0", "^3.2.0", True), ("4.0.0", "^3.2.0", False), ("0.3.5", "^0.3.1", True), ("0.4.0", "^0.3.1", False),
                                 ("1.2.3", "1.2.3", True), ("1.2.4", "1.2.3", False), ("junk", "~1.0.0", False)]:
            self.assertEqual(module.satisfies(version, rng), ok, (version, rng))

    def test_the_real_cache_resolves_when_present(self):
        cache = Path.home() / ".local/share/opencode-v2/cache/opencode/npm"
        config = Path.home() / ".local/share/opencode-v2/config/opencode/opencode.json"
        if not (cache.is_dir() and config.is_file()):
            self.skipTest("no V2 install on this machine")
        out = subprocess.run([sys.executable, str(RESOLVER), str(config), str(cache), NAME], capture_output=True, text=True).stdout
        self.assertTrue(out.startswith("ok\t"), out)


class Wiring(unittest.TestCase):
    def text(self, name):
        return (REPO / "verify" / name).read_text()

    def test_every_module_still_parses(self):
        for name in ("10-env.sh", "50-section-0-recover.sh", "52-section-2-systematic-install.sh", "53-section-2b-magic-context.sh",
                     "54-section-2c-package-integrity.sh", "57-section-6-plugin-mirrors.sh"):
            self.assertEqual(subprocess.run(["bash", "-n", str(REPO / "verify" / name)]).returncode, 0, name)

    def test_sections_2_and_2b_resolve_through_the_v2_cache_in_v2_mode(self):
        for name, package in (("52-section-2-systematic-install.sh", "@fro.bot/systematic"), ("53-section-2b-magic-context.sh", "@cortexkit/opencode-magic-context")):
            text = self.text(name)
            v2, _, v1 = text.partition("\nelse\n")
            self.assertIn('[ "${OC_MAJOR:-0}" = "2" ]', v2)
            self.assertIn("v2-plugin-resolve.py", v2)
            self.assertIn(package, v2)
            self.assertNotIn("PACKAGES_DIR", v2)
            self.assertIn("PACKAGES_DIR", v1)  # the V1 resolution is intact
            self.assertTrue(text.rstrip().endswith("fi"))

    def test_2c_and_the_section_6_mirror_check_are_skipped_on_v2_but_the_digest_binding_is_not(self):
        c = self.text("54-section-2c-package-integrity.sh")
        self.assertIn("skipped on V2", c.partition("\nelse\n")[0])
        self.assertIn("PLUGIN_CACHE_INTEGRITY_HELPER", c.partition("\nelse\n")[2])
        m = self.text("57-section-6-plugin-mirrors.sh")
        before, _, after = m.partition("SELF_PATH=$(readlink -f")
        self.assertIn("skipped on V2", before)
        self.assertTrue(before.rstrip().endswith("fi"))
        self.assertIn("SELF_SHA", after)  # outside the skipped branch

    def test_the_v2_paths_are_defined_once_in_the_environment_module(self):
        env = self.text("10-env.sh")
        for variable in ("V2_CONFIG_ROOT", "V2_NPM_CACHE", "V2_SANDBOX_REPO"):
            self.assertEqual(len(re.findall(rf"^{variable}=", env, re.M)), 1, variable)
            self.assertNotRegex(self.text("50-section-0-recover.sh"), rf"^\s*{variable}=")


if __name__ == "__main__":
    unittest.main()
