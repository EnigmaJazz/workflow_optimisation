"""Verifier V2 mode (queue Q44): plugin packages are resolved from the V2 npm cache against their ~/^ ranges."""
import json
import os
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
        self.assertEqual(got[:4], ["ok", str(newest), "3.27.5", f"{NAME}@~3.27.2"])  # the empty note is a stripped trailing tab

    def test_epochs_compare_numerically_not_alphabetically(self):
        install(self.cache, "~3.27.2", 999, "3.27.2")
        newest = install(self.cache, "~3.27.2", 1000, "3.27.4")
        self.assertEqual(resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)[1], str(newest))

    def test_an_incomplete_newest_install_is_an_error_even_when_an_older_one_is_complete(self):
        install(self.cache, "~3.27.2", 1000, "3.27.2")
        (self.cache / f"{NAME}@~3.27.2" / "2000" / "node_modules").mkdir(parents=True)  # newer epoch, no package.json yet
        got = resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)
        self.assertEqual(got[0], "error")  # V2 loads the newest epoch, so an older complete one must not make this pass
        self.assertIn("epoch 2000", got[1])
        self.assertIn("incomplete or still installing", got[1])
        self.assertIn("older complete install exists (epoch 1000)", got[1])

    def test_only_incomplete_installs_is_an_error_with_no_older_hint(self):
        (self.cache / f"{NAME}@~3.27.2" / "2000" / "node_modules").mkdir(parents=True)
        got = resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)
        self.assertEqual(got[0], "error")
        self.assertNotIn("older complete", got[1])

    def test_a_complete_out_of_range_install_is_never_skipped_for_an_older_one(self):
        install(self.cache, "~3.27.2", 1000, "3.27.2")
        install(self.cache, "~3.27.2", 2000, "3.28.0")
        self.assertIn("outside the configured range", resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)[1])

    def test_a_missing_version_is_a_metadata_error_not_a_range_error(self):
        root = install(self.cache, "~3.27.2", 1, "3.27.2")
        (root / "package.json").write_text(json.dumps({"name": NAME}))
        got = resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)
        self.assertIn("no version in its package.json", got[1])

    def test_a_declared_entry_resolves_the_way_node_does(self):
        root = install(self.cache, "~3.27.2", 1, "3.27.2")

        def with_main(main):
            (root / "package.json").write_text(json.dumps({"name": NAME, "version": "3.27.2", "main": main}))
            return resolve({"plugins": [f"{NAME}@~3.27.2"]}, self.cache)

        self.assertIn("entry file dist/index.js is missing", with_main("dist/index.js")[1])
        (root / "dist").mkdir()
        self.assertIn("entry file dist is missing", with_main("dist")[1])  # an empty directory has no index
        (root / "dist" / "index.js").write_text("")
        self.assertEqual(with_main("dist/index.js")[0], "ok")   # literal file
        self.assertEqual(with_main("dist/index")[0], "ok")      # added extension
        self.assertEqual(with_main("dist")[0], "ok")            # directory index
        self.assertEqual(with_main("./dist/")[0], "ok")         # directory with a trailing slash
        (root / "lib.mjs").write_text("")
        self.assertEqual(with_main("lib")[0], "ok")
        self.assertIn("entry file nope is missing", with_main("nope")[1])
        # Node's last resort when main cannot be resolved is the package root's index, so that layout still loads.
        (root / "empty").mkdir()
        self.assertIn("entry file empty is missing", with_main("empty")[1])
        (root / "index.js").write_text("")
        self.assertEqual(with_main("empty")[0], "ok")
        self.assertEqual(with_main("nope")[0], "ok")

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
                                 ("1.2.3", "1.2.3", True), ("1.2.4", "1.2.3", False), ("junk", "~1.0.0", False),
                                 ("0.0.3", "^0.0.3", True), ("0.0.4", "^0.0.3", False)]:
            self.assertEqual(module.satisfies(version, rng), ok, (version, rng))

    def test_the_real_cache_resolves_when_present(self):
        # Opt-in: the default suite must not depend on what happens to be installed on the host.
        if os.environ.get("WORKFLOW_VERIFY_TEST_LIVE_V2") != "1":
            self.skipTest("set WORKFLOW_VERIFY_TEST_LIVE_V2=1 to check the live V2 install")
        cache = Path.home() / ".local/share/opencode-v2/cache/opencode/npm"
        config = Path.home() / ".local/share/opencode-v2/config/opencode/opencode.json"
        if not (cache.is_dir() and config.is_file()):
            self.skipTest("no V2 install on this machine")
        out = subprocess.run([sys.executable, str(RESOLVER), str(config), str(cache), NAME], capture_output=True, text=True).stdout
        self.assertTrue(out.startswith("ok\t"), out)


class SandboxPlugins(unittest.TestCase):
    CHECKER = REPO / "verify" / "checkers" / "v2-sandbox-plugins-check.py"

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.repo, self.plugins = self.dir / "repo", self.dir / "plugins"
        (self.repo / "scripts").mkdir(parents=True)
        (self.repo / "opencode").mkdir()
        self.plugins.mkdir()
        (self.repo / "scripts" / "secure-launcher-v2.conf").write_text(
            'V2_PLUGIN_FILES=(\n  "opencode/a.ts|a.ts"\n  "opencode/lib/b.ts|lib/b.ts"\n)\n')
        (self.repo / "opencode" / "lib").mkdir()
        for rel in ("a.ts", "lib/b.ts"):
            (self.repo / "opencode" / rel).write_text("same")
            (self.plugins / rel).parent.mkdir(exist_ok=True)
            (self.plugins / rel).write_text("same")

    def run_checker(self):
        return subprocess.run([sys.executable, str(self.CHECKER), str(self.repo), str(self.plugins)], capture_output=True, text=True).stdout.strip()

    def test_matching_files_are_clean(self):
        self.assertTrue(self.run_checker().startswith("clean\tall 2 sandbox plugin files match"))

    def test_a_drifted_missing_or_sourceless_file_is_an_error(self):
        (self.plugins / "a.ts").write_text("changed")
        self.assertIn("1 differ from source (a.ts)", self.run_checker())
        (self.plugins / "lib" / "b.ts").unlink()
        out = self.run_checker()
        self.assertIn("1 not installed (lib/b.ts)", out)
        self.assertIn("install-user-files-v2", out)
        (self.repo / "opencode" / "a.ts").unlink()
        self.assertIn("source opencode/a.ts is missing", self.run_checker())

    def run_with_workflow(self, workflow):
        return subprocess.run([sys.executable, str(self.CHECKER), str(self.repo), str(self.plugins), str(workflow)], capture_output=True, text=True).stdout.strip()

    def test_an_unlisted_loadable_plugin_is_an_error_but_workflow_plugins_backups_and_libs_are_not(self):
        workflow = self.dir / "workflow"
        workflow.mkdir()
        (workflow / "health.ts").write_text("x")
        (self.plugins / "health.ts").write_text("x")             # a workflow plugin derive installs
        (self.plugins / "a.ts.bak-20261030").write_text("old")   # a backup is not loaded
        (self.plugins / "README.md").write_text("doc")
        (self.plugins / "lib" / "extra.ts").write_text("x")      # imported, never auto-loaded
        self.assertTrue(self.run_with_workflow(workflow).startswith("clean"), self.run_with_workflow(workflow))
        (self.plugins / "stale.ts").write_text("x")
        (self.plugins / "planted.mjs").write_text("x")
        out = self.run_with_workflow(workflow)
        self.assertTrue(out.startswith("error\t"), out)
        self.assertIn("2 unlisted plugin file(s) V2 would load (planted.mjs, stale.ts)", out)

    def test_without_the_workflow_argument_unlisted_files_are_not_judged(self):
        (self.plugins / "stale.ts").write_text("x")
        self.assertTrue(self.run_checker().startswith("clean"))

    def test_an_unreadable_or_empty_list_is_an_error_not_a_pass(self):
        (self.repo / "scripts" / "secure-launcher-v2.conf").write_text("V2_PLUGIN_FILES=(\n)\n")
        self.assertIn("no V2_PLUGIN_FILES entries", self.run_checker())
        (self.repo / "scripts" / "secure-launcher-v2.conf").unlink()
        self.assertTrue(self.run_checker().startswith("error\tcannot read"))

    def test_the_real_install_list_parses(self):
        sandbox = Path.home() / "agent-sandbox-integration"
        if not (sandbox / "scripts" / "secure-launcher-v2.conf").is_file():
            self.skipTest("the sandbox repository is not present")
        out = subprocess.run([sys.executable, str(self.CHECKER), str(sandbox), str(self.dir / "empty")], capture_output=True, text=True).stdout
        self.assertIn("not installed", out)  # an empty plugins dir: every listed file is missing, proving the list parsed


class Sections(unittest.TestCase):
    """Run the V2 branches of sections 2 and 2b for real against a fake config root and npm cache."""

    def run_section(self, module, systematic_version="3.27.2", with_skills=True, magic=True, config_plugins=None, spec="~3.27.2"):
        base = Path(tempfile.mkdtemp())
        cache, root = base / "npm", base / "root"
        root.mkdir()
        plugins = config_plugins if config_plugins is not None else [f"@fro.bot/systematic@{spec}", "@cortexkit/opencode-magic-context@~0.49.29"]
        (root / "opencode.json").write_text(json.dumps({"plugins": plugins}))
        sysroot = install(cache, spec, 1, systematic_version)
        if with_skills:
            (sysroot / "skills").mkdir()
            (sysroot / "agents").mkdir()
        if magic:
            install(cache, "~0.49.29", 1, "0.49.30", name="@cortexkit/opencode-magic-context")
        script = (f'fail() {{ echo "FAIL:$*"; }}\nOC_MAJOR=2\nVERIFY_MODULE_DIR="{REPO}/verify"\nV2_CONFIG_ROOT="{root}"\nV2_NPM_CACHE="{cache}"\n'
                  f'source "{REPO}/verify/{module}"\necho "ACTIVE_ROOT=${{ACTIVE_ROOT:-}}"\necho "MAGIC_ROOT=${{MAGIC_ROOT:-}}"\n')
        return subprocess.run(["bash", "-c", script], capture_output=True, text=True).stdout

    def test_section_2_resolves_a_healthy_install(self):
        out = self.run_section("52-section-2-systematic-install.sh")
        self.assertNotIn("FAIL:", out)
        self.assertRegex(out, r"ACTIVE_ROOT=\S+/node_modules/@fro\.bot/systematic")
        self.assertIn("ok: the V2 Systematic install is materialized", out)

    def test_section_2_fails_on_the_version_floor_missing_dirs_and_resolver_errors(self):
        self.assertIn("v3.18.4+ is required", self.run_section("52-section-2-systematic-install.sh", systematic_version="3.18.3", spec="~3.18.0"))
        out = self.run_section("52-section-2-systematic-install.sh", with_skills=False)
        self.assertIn("SYSTEMATIC_V2_INSTALL_INCOMPLETE", out)
        self.assertIn("ACTIVE_ROOT=\n", out)  # nothing downstream may use a half-resolved install
        self.assertIn("SYSTEMATIC_V2_RESOLUTION_FAILED", self.run_section("52-section-2-systematic-install.sh", config_plugins=[]))

    def test_section_2b_resolves_and_fails_closed(self):
        self.assertRegex(self.run_section("53-section-2b-magic-context.sh"), r"MAGIC_ROOT=\S+/node_modules/@cortexkit/opencode-magic-context")
        self.assertIn("MAGIC_CONTEXT_V2_RESOLUTION_FAILED", self.run_section("53-section-2b-magic-context.sh", magic=False))


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

    def test_2c_is_skipped_on_v2_and_section_6_checks_the_sandbox_plugins_there_without_dropping_the_digest_binding(self):
        c = self.text("54-section-2c-package-integrity.sh")
        self.assertIn("skipped on V2", c.partition("\nelse\n")[0])
        self.assertIn("PLUGIN_CACHE_INTEGRITY_HELPER", c.partition("\nelse\n")[2])
        m = self.text("57-section-6-plugin-mirrors.sh")
        before, _, after = m.partition("SELF_PATH=$(readlink -f")
        v2 = before.partition("\nelse\n")[0]
        self.assertIn("v2-sandbox-plugins-check.py", v2)
        self.assertIn("HOST_TOOL_PLUGIN_SOURCE_DRIFT", v2)
        self.assertIn('global-config/plugins"', v2)  # the workflow plugins are passed so they are not reported as unlisted
        self.assertIn("HOST_TOOL_PLUGIN_MISSING", before.partition("\nelse\n")[2])  # the V1 check is intact
        self.assertTrue(before.rstrip().endswith("fi"))
        self.assertIn("SELF_SHA", after)  # outside the skipped branch

    def test_the_v2_paths_are_defined_once_in_the_environment_module(self):
        env = self.text("10-env.sh")
        for variable in ("V2_CONFIG_ROOT", "V2_NPM_CACHE", "V2_SANDBOX_REPO"):
            self.assertEqual(len(re.findall(rf"^{variable}=", env, re.M)), 1, variable)
            self.assertNotRegex(self.text("50-section-0-recover.sh"), rf"^\s*{variable}=")


if __name__ == "__main__":
    unittest.main()
