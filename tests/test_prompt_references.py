import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "verify" / "checkers" / "check-prompt-references.py"
MODULE = REPO / "verify" / "55b-section-3b-prompt-references.sh"
REQUIRED_SKILLS = (
    "pm-handoff",
    "work-unit-commits",
    "chained-pr",
    "workflow-route",
    "workflow-odd-secure",
    "workflow-systematic",
)


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.foreign = self.root / "foreign"
        self.skills = self.root / "skills"
        self.foreign.mkdir()
        self.skills.mkdir()
        for name in REQUIRED_SKILLS:
            self.add_skill(name)

    def add_skill(self, name, declared_name=None):
        skill_dir = self.skills / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {declared_name or name}\ndescription: Test skill\n---\n"
        )

    def run(self, *args, cwd=None):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(CHECKER), str(self.foreign), str(self.skills), *args],
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd,
        )

    def close(self):
        self.temp.cleanup()


class PromptReferenceChecker(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture()

    def tearDown(self):
        self.fixture.close()

    def test_all_required_skills_resolve_from_the_skills_root(self):
        proc = self.fixture.run()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(proc.stdout.startswith("ok\t"), proc.stdout)
        self.assertIn(str(self.fixture.skills.resolve()), proc.stdout)
        self.assertIn(f"(checked from {self.fixture.foreign.resolve()}; cwd {self.fixture.foreign.resolve()})", proc.stdout)
        self.assertNotIn(f"cwd {REPO}", proc.stdout)

    def test_checker_changes_to_foreign_repo_even_when_invoked_from_repository_root(self):
        proc = self.fixture.run(cwd=REPO)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"cwd {self.fixture.foreign.resolve()}", proc.stdout)
        self.assertNotIn(f"cwd {REPO}", proc.stdout)

    def test_missing_skill_reports_name_and_expected_path(self):
        missing = "work-unit-commits"
        (self.fixture.skills / missing / "SKILL.md").unlink()
        proc = self.fixture.run()
        self.assertTrue(proc.stdout.startswith("error\t"), proc.stdout)
        self.assertIn(missing, proc.stdout)
        self.assertIn(str(self.fixture.skills / missing / "SKILL.md"), proc.stdout)

    def test_frontmatter_name_must_match_directory_name(self):
        self.fixture.add_skill("pm-handoff", "different-name")
        proc = self.fixture.run()
        self.assertTrue(proc.stdout.startswith("error\t"), proc.stdout)
        self.assertIn("pm-handoff", proc.stdout)
        self.assertIn("frontmatter", proc.stdout)

    def test_unterminated_frontmatter_is_rejected(self):
        skill_path = self.fixture.skills / "pm-handoff" / "SKILL.md"
        skill_path.write_text("---\nname: pm-handoff\n")

        proc = self.fixture.run()

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(proc.stdout.startswith("error\t"), proc.stdout)
        self.assertIn("pm-handoff", proc.stdout)
        self.assertIn(str(skill_path), proc.stdout)
        self.assertIn("unterminated frontmatter", proc.stdout)
        self.assertNotIn("ok\t", proc.stdout)

    def test_skill_markdown_symlink_is_not_a_regular_file(self):
        target = self.fixture.root / "outside.md"
        target.write_text("---\nname: pm-handoff\n---\n")
        skill_md = self.fixture.skills / "pm-handoff" / "SKILL.md"
        skill_md.unlink()
        skill_md.symlink_to(target)
        proc = self.fixture.run()
        self.assertTrue(proc.stdout.startswith("error\t"), proc.stdout)
        self.assertIn("pm-handoff", proc.stdout)
        self.assertIn("not a regular file", proc.stdout)

    def test_unresolvable_probe_is_rejected(self):
        probe = "q128-deliberately-unresolvable"
        proc = self.fixture.run("--probe", probe)
        self.assertTrue(proc.stdout.startswith("error\t"), proc.stdout)
        self.assertIn(probe, proc.stdout)

    def test_foreign_repo_contents_do_not_affect_resolution(self):
        docs = self.fixture.foreign / "docs" / "specs"
        docs.mkdir(parents=True)
        (docs / "pm-handoff.md").write_text("conflicting specification")
        conflicting = self.fixture.foreign / "skills" / "pm-handoff"
        conflicting.mkdir(parents=True)
        (conflicting / "SKILL.md").write_text("---\nname: pm-handoff\n---\n")
        proc = self.fixture.run()
        self.assertTrue(proc.stdout.startswith("ok\t"), proc.stdout)
        self.assertIn(str(self.fixture.skills), proc.stdout)

    def test_foreign_repo_must_differ_from_this_repo(self):
        proc = self.fixture.run("--this-repo", str(self.fixture.foreign))
        self.assertTrue(proc.stdout.startswith("error\t"), proc.stdout)

    def test_inventory_matches_names_in_prompt_sources(self):
        prompt_text = (REPO / "global-config" / "opencode.json").read_text()
        # References are prompt sources too; they can name required skills.
        for path in sorted((REPO / "global-config" / "skills").rglob("*.md")):
            prompt_text += "\n" + path.read_text()
        for name in REQUIRED_SKILLS:
            with self.subTest(name=name):
                self.assertIn(name, prompt_text)


class ModuleWiring(unittest.TestCase):
    def test_module_runs_checker_with_foreign_repo_and_positive_control(self):
        text = MODULE.read_text()
        self.assertIn("check-prompt-references.py", text)
        self.assertIn('--this-repo "$WORKSPACE"', text)
        self.assertIn("--probe q128-deliberately-unresolvable", text)
        self.assertIn("ok: positive control fails as required", text)
        self.assertIn("PROMPT_REFERENCE_SKILLS_ROOT_MISSING", text)
        self.assertNotIn("info: skipping prompt-reference check; skills directory is absent", text)
        proc = subprocess.run(["bash", "-n", str(MODULE)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_missing_skills_root_fails_with_the_expected_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "missing-skills"
            script = (
                'fail() { printf "%s\\n" "$1"; return 1; }; '
                'SKILLS_DIR="$1"; source "$2"'
            )
            proc = subprocess.run(
                ["bash", "-c", script, "test", str(missing), str(MODULE)],
                capture_output=True,
                text=True,
                cwd=REPO,
            )
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"PROMPT_REFERENCE_SKILLS_ROOT_MISSING: {missing}", proc.stdout)


if __name__ == "__main__":
    unittest.main()
