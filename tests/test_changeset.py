"""Acceptance tests for scripts/changeset.py (spec: docs/specs/changeset-tool.md).

Every test drives the CLI exactly as production does and inspects files, the
journal and the JSON report. Run: python3 -m unittest tests/test_changeset.py -v
"""

import fcntl
import hashlib
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
SCRIPT = REPO / "scripts" / "changeset.py"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="changeset-test-"))
        self.root = self.tmp / "root"          # the only allowed root
        self.root.mkdir()
        self.outside = self.tmp / "outside"    # never allowed
        self.outside.mkdir()
        self.journals = self.tmp / "journals"
        self.set_dir = self.tmp / "set"
        self.set_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- helpers ---------------------------------------------------------
    def write_set(self, ops, set_id="test-set", schema="workflow-changeset/v1"):
        doc = {"schema": schema, "id": set_id, "description": "test", "ops": ops}
        (self.set_dir / "changeset.json").write_text(json.dumps(doc, indent=2))

    def run_cli(self, *args, extra_roots=()):
        cmd = [sys.executable, str(SCRIPT), *args, "--allow-root", str(self.root)]
        for r in extra_roots:
            cmd += ["--allow-root", str(r)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        # Spec section 7: every invocation prints exactly one JSON report object.
        try:
            report = json.loads(proc.stdout)
        except ValueError:
            self.fail(f"no JSON report on stdout (exit {proc.returncode}): "
                      f"{proc.stdout[:200]!r} {proc.stderr[-300:]!r}")
        self.assertIsInstance(report, dict)
        for key in ("command", "results", "counts", "verify", "refused"):
            self.assertIn(key, report)
        return proc.returncode, report, proc

    def apply(self, *extra):
        return self.run_cli("apply", "--set", str(self.set_dir),
                            "--journal-root", str(self.journals), *extra)

    def revert(self, journal, *extra):
        return self.run_cli("revert", "--journal", str(journal),
                            "--journal-root", str(self.journals), *extra)

    def journal_files(self):
        return sorted(self.journals.rglob("journal.jsonl")) if self.journals.exists() else []

    def only_journal(self):
        files = [p for p in self.journal_files() if not p.parent.name.startswith("revert-")]
        self.assertEqual(len(files), 1, files)
        return files[0]

    def outcomes(self, report):
        return [r["outcome"] for r in report["results"]]


class ScriptPresent(unittest.TestCase):
    def test_script_exists(self):
        self.assertTrue(SCRIPT.is_file(), f"{SCRIPT} missing (implementation not built yet)")


class JsonSet(Case):
    ORIGINAL = ('{\n  "a": 1,\n  "agent": {\n    "x": {"model": "old", "keep": [1,2]}\n  },\n'
                '    "z":   true\n}\n')

    def setUp(self):
        super().setUp()
        self.target = self.root / "cfg.json"
        self.target.write_text(self.ORIGINAL)

    def op(self, expect="old", value="new"):
        return {"op": "json_set", "file": str(self.target), "path": "/agent/x/model",
                "expect_before": expect, "value": value}

    def test_applies_and_preserves_every_other_byte(self):
        self.write_set([self.op()])
        code, report, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(self.outcomes(report), ["applied"])
        self.assertEqual(self.target.read_text(), self.ORIGINAL.replace('"old"', '"new"'))

    def test_second_apply_is_already_applied_and_writes_nothing(self):
        self.write_set([self.op()])
        self.apply()
        before = self.target.read_bytes()
        code, report, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(self.outcomes(report), ["already_applied"])
        self.assertEqual(self.target.read_bytes(), before)

    def test_conflict_leaves_file_byte_identical_and_exits_2(self):
        self.write_set([self.op(expect="something-else")])
        code, report, _ = self.apply()
        self.assertEqual(code, 2)
        self.assertEqual(self.outcomes(report), ["conflict"])
        self.assertEqual(self.target.read_text(), self.ORIGINAL)

    def test_conflict_does_not_stop_later_ops(self):
        other = self.root / "other.json"
        other.write_text('{"k": "v1"}\n')
        self.write_set([self.op(expect="nope"),
                        {"op": "json_set", "file": str(other), "path": "/k",
                         "expect_before": "v1", "value": "v2"}])
        code, report, _ = self.apply()
        self.assertEqual(code, 2)
        self.assertEqual(self.outcomes(report), ["conflict", "applied"])
        self.assertEqual(json.loads(other.read_text()), {"k": "v2"})

    def test_absent_expectation_adds_member(self):
        f = self.root / "add.json"
        f.write_text('{\n  "a": 1\n}\n')
        self.write_set([{"op": "json_set", "file": str(f), "path": "/b",
                         "expect_before": {"$absent": True}, "value": {"n": 2}}])
        code, report, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(f.read_text()), {"a": 1, "b": {"n": 2}})
        self.assertTrue(f.read_text().startswith('{\n  "a": 1'))

    def test_absent_expectation_conflicts_when_member_exists(self):
        self.write_set([{"op": "json_set", "file": str(self.target), "path": "/a",
                         "expect_before": {"$absent": True}, "value": 5}])
        code, report, _ = self.apply()
        self.assertEqual(code, 2)
        self.assertEqual(self.outcomes(report), ["conflict"])
        self.assertEqual(self.target.read_text(), self.ORIGINAL)

    def test_unparseable_json_is_conflict(self):
        self.target.write_text('{"a": 1,,}\n')
        self.write_set([self.op()])
        code, report, _ = self.apply()
        self.assertEqual(code, 2)
        self.assertEqual(self.outcomes(report), ["conflict"])
        self.assertEqual(self.target.read_text(), '{"a": 1,,}\n')

    def test_missing_file_is_conflict(self):
        self.target.unlink()
        self.write_set([self.op()])
        code, report, _ = self.apply()
        self.assertEqual(code, 2)
        self.assertEqual(self.outcomes(report), ["conflict"])
        self.assertFalse(self.target.exists())

    def test_concurrent_change_before_commit_is_conflict(self):
        intruder = '{"agent": {"x": {"model": "changed-by-sync"}}}\n'
        hook = f"printf '%s' '{intruder}' > \"$1\""
        self.write_set([self.op()])
        env = dict(os.environ, CHANGESET_TEST_BEFORE_COMMIT=hook)
        proc = subprocess.run([sys.executable, str(SCRIPT), "apply", "--set", str(self.set_dir),
                               "--journal-root", str(self.journals), "--allow-root", str(self.root)],
                              capture_output=True, text=True, timeout=60, env=env)
        report = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(report["results"][0]["outcome"], "conflict")
        self.assertEqual(report["results"][0]["reason"], "concurrent_change")
        self.assertEqual(self.target.read_text(), intruder)
        leftovers = [p.name for p in self.root.iterdir() if p.name != "cfg.json"]
        self.assertEqual(leftovers, [], "temporary file must be removed")

    def test_mode_bits_preserved(self):
        os.chmod(self.target, 0o600)
        self.write_set([self.op()])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["applied"]))
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o600)


class JsonPointerAndIndent(Case):
    def test_pointer_escapes(self):
        f = self.root / "p.json"
        f.write_text('{"a/b": {"c~d": "old"}}\n')
        self.write_set([{"op": "json_set", "file": str(f), "path": "/a~1b/c~0d",
                         "expect_before": "old", "value": "new"}])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["applied"]))
        self.assertEqual(f.read_text(), '{"a/b": {"c~d": "new"}}\n')

    def test_missing_parent_is_conflict(self):
        f = self.root / "p.json"
        f.write_text('{"a": 1}\n')
        self.write_set([{"op": "json_set", "file": str(f), "path": "/no/such",
                         "expect_before": {"$absent": True}, "value": 1},
                        {"op": "json_delete", "file": str(f), "path": "/no/such",
                         "expect_before": 1}])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (2, ["conflict", "conflict"]))
        self.assertEqual(f.read_text(), '{"a": 1}\n')
        code, report, _ = self.run_cli("status", "--set", str(self.set_dir))
        self.assertEqual((code, self.outcomes(report)), (2, ["conflict", "conflict"]))

    def test_multiline_value_indented_to_target_line(self):
        f = self.root / "p.json"
        f.write_text('{\n  "agent": {\n    "x": 1\n  }\n}\n')
        value = {"model": "m", "tools": {"read": True}}
        self.write_set([{"op": "json_set", "file": str(f), "path": "/agent/x",
                         "expect_before": 1, "value": value}])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        text = f.read_text()
        self.assertEqual(json.loads(text), {"agent": {"x": value}})
        self.assertTrue(text.startswith('{\n  "agent": {\n    "x": '))
        self.assertTrue(text.endswith('\n  }\n}\n'))
        inner = text.split('"x": ', 1)[1].rsplit('\n  }\n}', 1)[0].splitlines()[1:]
        for line in inner:
            self.assertTrue(line.startswith("    "), f"not indented to target line: {line!r}")


class JsonInsertExact(Case):
    def insert(self, text, key="b", value=2):
        f = self.root / "i.json"
        f.write_text(text)
        self.write_set([{"op": "json_set", "file": str(f), "path": "/" + key,
                         "expect_before": {"$absent": True}, "value": value}])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["applied"]))
        return f.read_text()

    def test_single_line_object(self):
        self.assertEqual(self.insert('{"a": 1}\n'), '{"a": 1, "b": 2}\n')

    def test_multi_line_object(self):
        self.assertEqual(self.insert('{\n  "a": 1\n}\n'), '{\n  "a": 1,\n  "b": 2\n}\n')

    def test_multi_line_object_with_object_value(self):
        self.assertEqual(self.insert('{\n  "a": 1\n}\n', value={"n": 2}),
                         '{\n  "a": 1,\n  "b": {\n    "n": 2\n  }\n}\n')

    def test_empty_object(self):
        self.assertEqual(self.insert('{}\n'), '{"b": 2}\n')
        self.assertEqual(self.insert('{ }\n'), '{"b": 2}\n')

    def test_replace_with_object_matches_spec_example(self):
        f = self.root / "r.json"
        f.write_text('{\n  "agent": {\n    "x": 1\n  }\n}\n')
        self.write_set([{"op": "json_set", "file": str(f), "path": "/agent/x",
                         "expect_before": 1, "value": {"model": "m"}}])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(f.read_text(),
                         '{\n  "agent": {\n    "x": {\n      "model": "m"\n    }\n  }\n}\n')


class JsonDelete(Case):
    def test_delete_only_member(self):
        f = self.root / "d.json"
        f.write_text('{\n  "a": 1\n}\n')
        self.write_set([{"op": "json_delete", "file": str(f), "path": "/a", "expect_before": 1}])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(f.read_text(), '{\n}\n')

    def test_delete_only_element_single_line(self):
        f = self.root / "d.json"
        f.write_text('{"p": ["x"]}\n')
        self.write_set([{"op": "json_delete", "file": str(f), "path": "/p/0", "expect_before": "x"}])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(f.read_text(), '{"p": []}\n')

    def test_delete_middle_member(self):
        f = self.root / "d.json"
        f.write_text('{\n  "a": 1,\n  "b": 2,\n  "c": 3\n}\n')
        self.write_set([{"op": "json_delete", "file": str(f), "path": "/b", "expect_before": 2}])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(f.read_text(), '{\n  "a": 1,\n  "c": 3\n}\n')

    def test_delete_last_member(self):
        f = self.root / "d.json"
        f.write_text('{\n  "a": 1,\n  "c": 3\n}\n')
        self.write_set([{"op": "json_delete", "file": str(f), "path": "/c", "expect_before": 3}])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(f.read_text(), '{\n  "a": 1\n}\n')

    def test_delete_array_element(self):
        f = self.root / "d.json"
        f.write_text('{"p": ["x", "y", "z"]}\n')
        self.write_set([{"op": "json_delete", "file": str(f), "path": "/p/1", "expect_before": "y"}])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(f.read_text(), '{"p": ["x", "z"]}\n')

    def test_delete_already_absent_is_already_applied(self):
        f = self.root / "d.json"
        f.write_text('{\n  "a": 1\n}\n')
        self.write_set([{"op": "json_delete", "file": str(f), "path": "/b", "expect_before": 2}])
        code, report, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(self.outcomes(report), ["already_applied"])

    def test_delete_with_wrong_expectation_is_conflict(self):
        f = self.root / "d.json"
        text = '{\n  "a": 1,\n  "b": 9\n}\n'
        f.write_text(text)
        self.write_set([{"op": "json_delete", "file": str(f), "path": "/b", "expect_before": 2}])
        code, report, _ = self.apply()
        self.assertEqual(code, 2)
        self.assertEqual(f.read_text(), text)


class BlockReplace(Case):
    TEXT = "head\n<!-- begin:x -->\nold line 1\nold line 2\n<!-- end:x -->\ntail\n"

    def setUp(self):
        super().setUp()
        self.f = self.root / "doc.md"
        self.f.write_text(self.TEXT)

    def op(self, expect="old line 1\nold line 2\n", value="new block\n"):
        return {"op": "block_replace", "file": str(self.f), "begin": "<!-- begin:x -->",
                "end": "<!-- end:x -->", "expect_before": expect, "value": value}

    def test_replaces_only_the_block(self):
        self.write_set([self.op()])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(self.f.read_text(),
                         "head\n<!-- begin:x -->\nnew block\n<!-- end:x -->\ntail\n")

    def test_already_applied(self):
        self.write_set([self.op()])
        self.apply()
        code, report, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(self.outcomes(report), ["already_applied"])

    def test_missing_marker_is_conflict(self):
        self.f.write_text("head\nno markers here\n")
        self.write_set([self.op()])
        code, report, _ = self.apply()
        self.assertEqual(code, 2)
        self.assertEqual(self.f.read_text(), "head\nno markers here\n")

    def test_duplicate_marker_is_conflict(self):
        text = self.TEXT + "<!-- begin:x -->\n"
        self.f.write_text(text)
        self.write_set([self.op()])
        code, _, _ = self.apply()
        self.assertEqual(code, 2)
        self.assertEqual(self.f.read_text(), text)

    def test_changed_block_is_conflict(self):
        text = self.TEXT.replace("old line 2", "edited by someone")
        self.f.write_text(text)
        self.write_set([self.op()])
        code, _, _ = self.apply()
        self.assertEqual(code, 2)
        self.assertEqual(self.f.read_text(), text)


class FileOps(Case):
    def test_create_applies_then_already_applied(self):
        (self.set_dir / "content.txt").write_bytes(b"hello\n")
        target = self.root / "sub" / "new.txt"
        target.parent.mkdir()
        self.write_set([{"op": "file_create", "file": str(target), "content_file": "content.txt"}])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["applied"]))
        self.assertEqual(target.read_bytes(), b"hello\n")
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["already_applied"]))

    def test_create_conflicts_with_different_existing_file(self):
        (self.set_dir / "content.txt").write_bytes(b"hello\n")
        target = self.root / "new.txt"
        target.write_bytes(b"someone else\n")
        self.write_set([{"op": "file_create", "file": str(target), "content_file": "content.txt"}])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (2, ["conflict"]))
        self.assertEqual(target.read_bytes(), b"someone else\n")

    def test_create_never_makes_directories(self):
        (self.set_dir / "content.txt").write_bytes(b"hello\n")
        target = self.root / "missing-dir" / "new.txt"
        self.write_set([{"op": "file_create", "file": str(target), "content_file": "content.txt"}])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (2, ["conflict"]))
        self.assertFalse(target.parent.exists())

    def test_create_mode_default_and_explicit(self):
        (self.set_dir / "content.txt").write_bytes(b"hello\n")
        plain = self.root / "plain.txt"
        script = self.root / "run.sh"
        self.write_set([
            {"op": "file_create", "file": str(plain), "content_file": "content.txt"},
            {"op": "file_create", "file": str(script), "content_file": "content.txt", "mode": "0755"},
        ])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(stat.S_IMODE(plain.stat().st_mode), 0o644)
        self.assertEqual(stat.S_IMODE(script.stat().st_mode), 0o755)

    def test_remove_moves_into_journal_never_deletes(self):
        target = self.root / "old.txt"
        target.write_bytes(b"retire me\n")
        self.write_set([{"op": "file_remove", "file": str(target),
                         "expect_sha256": sha256(b"retire me\n")}])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["applied"]))
        self.assertFalse(target.exists())
        copies = list(self.journals.rglob("removed/*"))
        copies = [c for c in copies if c.is_file()]
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0].read_bytes(), b"retire me\n")

    def test_remove_with_wrong_hash_is_conflict(self):
        target = self.root / "old.txt"
        target.write_bytes(b"changed\n")
        self.write_set([{"op": "file_remove", "file": str(target),
                         "expect_sha256": sha256(b"retire me\n")}])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (2, ["conflict"]))
        self.assertTrue(target.exists())

    def test_remove_absent_is_already_applied(self):
        self.write_set([{"op": "file_remove", "file": str(self.root / "gone.txt"),
                         "expect_sha256": sha256(b"x")}])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["already_applied"]))


class Refusals(Case):
    def setUp(self):
        super().setUp()
        self.f = self.root / "cfg.json"
        self.f.write_text('{"k": "v1"}\n')
        self.good_op = {"op": "json_set", "file": str(self.f), "path": "/k",
                        "expect_before": "v1", "value": "v2"}

    def assert_untouched(self):
        self.assertEqual(self.f.read_text(), '{"k": "v1"}\n')

    def test_unknown_op_refuses_whole_set(self):
        self.write_set([self.good_op, {"op": "rm_rf", "file": str(self.f)}])
        code, report, _ = self.apply()
        self.assertEqual(code, 3)
        self.assertEqual(report["refused"], "invalid_set")
        self.assert_untouched()

    def test_unknown_schema_refuses(self):
        self.write_set([self.good_op], schema="workflow-changeset/v99")
        code, _, _ = self.apply()
        self.assertEqual(code, 3)
        self.assert_untouched()

    def test_invalid_id_refuses(self):
        self.write_set([self.good_op], set_id="../escape")
        code, _, _ = self.apply()
        self.assertEqual(code, 3)
        self.assert_untouched()

    def test_path_outside_allowed_roots_refuses_whole_run(self):
        out = self.outside / "x.json"
        out.write_text('{"k": "v1"}\n')
        self.write_set([self.good_op, {"op": "json_set", "file": str(out), "path": "/k",
                                       "expect_before": "v1", "value": "v2"}])
        code, report, _ = self.apply()
        self.assertEqual(code, 3)
        self.assertEqual(report["refused"], "path_outside_allowed_roots")
        self.assert_untouched()
        self.assertEqual(out.read_text(), '{"k": "v1"}\n')

    def test_symlink_escaping_root_refuses(self):
        real = self.outside / "real.json"
        real.write_text('{"k": "v1"}\n')
        link = self.root / "link.json"
        link.symlink_to(real)
        self.write_set([{"op": "json_set", "file": str(link), "path": "/k",
                         "expect_before": "v1", "value": "v2"}])
        code, report, _ = self.apply()
        self.assertEqual(code, 3)
        self.assertEqual(real.read_text(), '{"k": "v1"}\n')

    def lock_path(self, set_id="test-set"):
        return self.journals / set_id / ".lock"

    def hold_flock(self, set_id="test-set"):
        # A separate process holds the per-set flock until stopped (spec section 5).
        self.lock_path(set_id).parent.mkdir(parents=True, exist_ok=True)
        holder = subprocess.Popen(
            [sys.executable, "-c",
             "import fcntl,sys,time; f=open(sys.argv[1],'a'); "
             "fcntl.flock(f, fcntl.LOCK_EX); print('held', flush=True); time.sleep(60)",
             str(self.lock_path(set_id))], stdout=subprocess.PIPE, text=True)

        def stop():
            holder.kill()
            holder.wait()
            holder.stdout.close()
        self.addCleanup(stop)
        self.assertEqual(holder.stdout.readline().strip(), "held")
        return holder

    def test_held_flock_refuses(self):
        self.hold_flock()
        self.write_set([self.good_op])
        code, report, _ = self.apply()
        self.assertEqual(code, 3)
        self.assertEqual(report["refused"], "lock_held")
        self.assert_untouched()

    def test_leftover_lock_file_without_holder_does_not_block(self):
        self.lock_path().parent.mkdir(parents=True)
        self.lock_path().write_text("leftover content is never interpreted")
        self.write_set([self.good_op])
        code, report, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(self.outcomes(report), ["applied"])
        self.assertNotIn("stale_lock_cleared", report)

    def test_flock_released_after_run(self):
        self.write_set([self.good_op])
        code, _, _ = self.apply()
        self.assertEqual(code, 0)
        with open(self.lock_path(), "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)  # raises if still held

    def test_lock_is_per_set(self):
        self.hold_flock(set_id="other-set")
        self.write_set([self.good_op])
        code, report, _ = self.apply()
        self.assertEqual((code, self.outcomes(report)), (0, ["applied"]))

    def test_content_file_outside_set_dir_is_invalid_set(self):
        secret = self.outside / "secret.txt"
        secret.write_bytes(b"do not copy\n")
        target = self.root / "copied.txt"
        self.write_set([{"op": "file_create", "file": str(target),
                         "content_file": "../outside/secret.txt"}])
        code, report, _ = self.apply()
        self.assertEqual(code, 3)
        self.assertEqual(report["refused"], "invalid_set")
        self.assertFalse(target.exists())

    def test_verify_cmd_failing_before_refuses(self):
        self.write_set([self.good_op])
        code, report, _ = self.apply("--verify-cmd", "exit 7")
        self.assertEqual(code, 3)
        self.assertEqual(report["refused"], "verify_failed")
        self.assertEqual(report["verify"]["before"], 7)
        self.assert_untouched()

    def test_verify_cmd_runs_before_and_after(self):
        self.write_set([self.good_op])
        code, report, _ = self.apply("--verify-cmd", "exit 0")
        self.assertEqual(code, 0)
        self.assertEqual(report["verify"], {"before": 0, "after": 0})

    def test_failing_post_verify_is_reported_not_rolled_back(self):
        marker = self.tmp / "ran-once"
        cmd = f'if [ -e "{marker}" ]; then exit 4; else touch "{marker}"; exit 0; fi'
        self.write_set([self.good_op])
        code, report, _ = self.apply("--verify-cmd", cmd)
        self.assertEqual(report["verify"], {"before": 0, "after": 4})
        self.assertEqual(self.outcomes(report), ["applied"])
        self.assertEqual(json.loads(self.f.read_text()), {"k": "v2"})


class DryRunAndStatus(Case):
    def setUp(self):
        super().setUp()
        self.f = self.root / "cfg.json"
        self.f.write_text('{"k": "v1", "m": "x"}\n')
        self.write_set([
            {"op": "json_set", "file": str(self.f), "path": "/k", "expect_before": "v1", "value": "v2"},
            {"op": "json_set", "file": str(self.f), "path": "/m", "expect_before": "nope", "value": "y"},
        ])

    def test_dry_run_reports_without_writing(self):
        code, report, _ = self.apply("--dry-run", "--verify-cmd", "exit 9")
        self.assertEqual(code, 2)
        self.assertTrue(report["dry_run"])
        self.assertEqual(self.outcomes(report), ["applied", "conflict"])
        self.assertEqual(self.f.read_text(), '{"k": "v1", "m": "x"}\n')
        leftovers = list(self.journals.rglob("*")) if self.journals.exists() else []
        self.assertEqual(leftovers, [], "dry run must create no lock, journal or directory")
        self.assertEqual(report["verify"], {"before": None, "after": None})

    def test_status_is_read_only(self):
        code, report, _ = self.run_cli("status", "--set", str(self.set_dir))
        self.assertEqual(code, 2)
        self.assertEqual(report["command"], "status")
        self.assertEqual(self.outcomes(report), ["applied", "conflict"])
        self.assertEqual(self.f.read_text(), '{"k": "v1", "m": "x"}\n')


class Journal(Case):
    def setUp(self):
        super().setUp()
        self.f = self.root / "cfg.json"
        self.f.write_text('{"k": "v1"}\n')
        self.write_set([{"op": "json_set", "file": str(self.f), "path": "/k",
                         "expect_before": "v1", "value": "v2"}])

    def lines(self, path):
        return [json.loads(l) for l in path.read_text().splitlines()]

    def test_structure_and_seal(self):
        code, report, _ = self.apply()
        self.assertEqual(code, 0)
        journal = self.only_journal()
        self.assertEqual(Path(report["journal"]).resolve(), journal.resolve())
        rows = self.lines(journal)
        self.assertEqual(rows[0]["type"], "header")
        self.assertEqual(rows[0]["schema"], "workflow-changeset-journal/v1")
        self.assertEqual(rows[0]["set_id"], "test-set")
        types = [r["type"] for r in rows]
        self.assertEqual(types, ["header", "intent", "outcome", "seal"])
        self.assertEqual(rows[1]["index"], 0)
        self.assertEqual(rows[2]["outcome"], "applied")
        raw = journal.read_text().splitlines(keepends=True)
        self.assertEqual(rows[-1]["sha256"], sha256("".join(raw[:-1]).encode()))
        self.assertTrue(journal.parent.parent.name == "test-set")


class Revert(Case):
    def setUp(self):
        super().setUp()
        self.a = self.root / "a.json"
        self.b = self.root / "b.json"
        self.a.write_text('{\n  "k": "v1"\n}\n')
        self.b.write_text('{"k": "w1"}\n')
        self.ops = [
            {"op": "json_set", "file": str(self.a), "path": "/k", "expect_before": "v1", "value": "v2"},
            {"op": "json_set", "file": str(self.b), "path": "/k", "expect_before": "w1", "value": "w2"},
        ]

    def test_revert_restores_exact_bytes(self):
        self.write_set(self.ops)
        self.apply()
        code, report, _ = self.revert(self.only_journal())
        self.assertEqual(code, 0)
        self.assertEqual(sorted(self.outcomes(report)), ["reverted", "reverted"])
        self.assertEqual(self.a.read_text(), '{\n  "k": "v1"\n}\n')
        self.assertEqual(self.b.read_text(), '{"k": "w1"}\n')

    def test_revert_preserves_drift(self):
        self.write_set(self.ops)
        self.apply()
        self.b.write_text('{"k": "changed-by-sync"}\n')
        code, report, _ = self.revert(self.only_journal())
        self.assertEqual(code, 2)
        by_file = {r["file"]: r["outcome"] for r in report["results"]}
        self.assertEqual(by_file[str(self.a)], "reverted")
        self.assertEqual(by_file[str(self.b)], "drift")
        self.assertEqual(self.b.read_text(), '{"k": "changed-by-sync"}\n')

    def test_revert_twice_is_already_reverted(self):
        self.write_set(self.ops)
        self.apply()
        journal = self.only_journal()
        self.revert(journal)
        code, report, _ = self.revert(journal)
        self.assertEqual(code, 0)
        self.assertEqual(set(self.outcomes(report)), {"already_reverted"})

    def test_conflicted_op_is_not_reverted(self):
        self.b.write_text('{"k": "not-w1"}\n')
        self.write_set(self.ops)
        self.apply()
        self.b.write_text('{"k": "w1"}\n')  # now equals the op's 'before'
        code, report, _ = self.revert(self.only_journal())
        files = [r["file"] for r in report["results"]]
        self.assertNotIn(str(self.b), files)
        self.assertEqual(self.b.read_text(), '{"k": "w1"}\n')

    def test_revert_of_conflict_only_journal_is_a_clean_no_op(self):
        self.a.write_text('{\n  "k": "not-v1"\n}\n')
        self.write_set([self.ops[0]])
        code, _, _ = self.apply()
        self.assertEqual(code, 2)
        code, report, _ = self.revert(self.only_journal())
        self.assertEqual(code, 0)
        self.assertEqual(report["results"], [])
        self.assertEqual(self.a.read_text(), '{\n  "k": "not-v1"\n}\n')

    def test_revert_restores_removed_file_mode(self):
        removed = self.root / "tool.sh"
        removed.write_bytes(b"#!/bin/sh\n")
        os.chmod(removed, 0o755)
        self.write_set([{"op": "file_remove", "file": str(removed),
                         "expect_sha256": sha256(b"#!/bin/sh\n")}])
        self.apply()
        code, _, _ = self.revert(self.only_journal())
        self.assertEqual(code, 0)
        self.assertEqual(stat.S_IMODE(removed.stat().st_mode), 0o755)

    def test_interrupted_file_remove_is_restored_by_revert(self):
        removed = self.root / "old.txt"
        removed.write_bytes(b"keep me\n")
        self.write_set([{"op": "file_remove", "file": str(removed),
                         "expect_sha256": sha256(b"keep me\n")}])
        self.apply()
        journal = self.only_journal()
        rows = [json.loads(l) for l in journal.read_text().splitlines()]
        kept = [r for r in rows if r["type"] in ("header", "intent")]   # crash after unlink
        journal.write_text("".join(json.dumps(r) + "\n" for r in kept))
        self.assertFalse(removed.exists())
        code, report, _ = self.revert(journal)
        self.assertEqual(code, 0)
        self.assertEqual(self.outcomes(report), ["reverted"])
        self.assertEqual(removed.read_bytes(), b"keep me\n")

    def test_older_journal_refused_until_newer_reverted(self):
        self.write_set([self.ops[0]])
        self.apply()
        first = self.only_journal()
        self.write_set(self.ops)            # second run applies op on b
        self.apply()
        journals = sorted(p for p in self.journal_files() if not p.parent.name.startswith("revert-"))
        second = [p for p in journals if p != first][0]
        header = json.loads(second.read_text().splitlines()[0])
        self.assertEqual(Path(header["previous_journal"]).resolve(), first.resolve())
        code, report, _ = self.revert(first)
        self.assertEqual(code, 3)
        self.assertEqual(report["refused"], "newer_journal_not_reverted")
        self.assertEqual(json.loads(self.a.read_text()), {"k": "v2"})
        code, _, _ = self.revert(second)
        self.assertEqual(code, 0)
        code, _, _ = self.revert(first)
        self.assertEqual(code, 0)
        self.assertEqual(self.a.read_text(), '{\n  "k": "v1"\n}\n')
        self.assertEqual(self.b.read_text(), '{"k": "w1"}\n')

    def test_revert_of_middle_array_delete_restores_exact_bytes(self):
        f = self.root / "arr.json"
        original = '{"p": ["x", "y", "z"]}\n'
        f.write_text(original)
        self.write_set([{"op": "json_delete", "file": str(f), "path": "/p/1", "expect_before": "y"}])
        self.apply()
        self.assertEqual(f.read_text(), '{"p": ["x", "z"]}\n')
        code, report, _ = self.revert(self.only_journal())
        self.assertEqual((code, self.outcomes(report)), (0, ["reverted"]))
        self.assertEqual(f.read_text(), original)

    def test_revert_of_middle_array_delete_reports_drift_when_array_changed(self):
        f = self.root / "arr.json"
        f.write_text('{"p": ["x", "y", "z"]}\n')
        self.write_set([{"op": "json_delete", "file": str(f), "path": "/p/1", "expect_before": "y"}])
        self.apply()
        f.write_text('{"p": ["x", "z", "added"]}\n')
        code, report, _ = self.revert(self.only_journal())
        self.assertEqual((code, self.outcomes(report)), (2, ["drift"]))
        self.assertEqual(f.read_text(), '{"p": ["x", "z", "added"]}\n')

    def test_corrupt_newer_journal_fails_closed(self):
        self.write_set([self.ops[0]])
        self.apply()
        first = self.only_journal()
        self.write_set(self.ops)
        self.apply()
        second = [p for p in self.journal_files()
                  if p != first and not p.parent.name.startswith("revert-")][0]
        second.write_text(second.read_text() + "{corrupt\n")
        code, report, _ = self.revert(first)
        self.assertEqual(code, 3)
        self.assertEqual(report["refused"], "invalid_journal")
        self.assertIn(str(second.parent.name), json.dumps(report.get("detail")))
        self.assertEqual(json.loads(self.a.read_text()), {"k": "v2"})
        code, report, _ = self.apply()
        self.assertEqual(code, 3)
        self.assertEqual(report["refused"], "invalid_journal")

    def test_revert_restores_removed_file_and_retires_created_file(self):
        removed = self.root / "old.txt"
        removed.write_bytes(b"keep me\n")
        (self.set_dir / "c.txt").write_bytes(b"created\n")
        created = self.root / "new.txt"
        self.write_set([
            {"op": "file_remove", "file": str(removed), "expect_sha256": sha256(b"keep me\n")},
            {"op": "file_create", "file": str(created), "content_file": "c.txt"},
        ])
        self.apply()
        code, _, _ = self.revert(self.only_journal())
        self.assertEqual(code, 0)
        self.assertEqual(removed.read_bytes(), b"keep me\n")
        self.assertFalse(created.exists())
        moved = [p for p in self.journals.rglob("*") if p.is_file() and p.read_bytes() == b"created\n"]
        self.assertTrue(moved, "created file must be moved into the revert journal, not deleted")

    def test_revert_writes_its_own_journal(self):
        self.write_set(self.ops)
        self.apply()
        self.revert(self.only_journal())
        reverts = [p for p in self.journal_files() if p.parent.name.startswith("revert-")]
        self.assertEqual(len(reverts), 1)

    def test_missing_journal_refuses(self):
        code, report, _ = self.revert(self.tmp / "nope" / "journal.jsonl")
        self.assertEqual(code, 3)

    def test_corrupt_journal_refuses_and_touches_nothing(self):
        self.write_set(self.ops)
        self.apply()
        journal = self.only_journal()
        journal.write_text(journal.read_text() + "{not json\n")
        code, report, _ = self.revert(journal)
        self.assertEqual(code, 3)
        self.assertEqual(report["refused"], "invalid_journal")
        self.assertEqual(json.loads(self.a.read_text()), {"k": "v2"})

    def test_tampered_seal_refuses(self):
        self.write_set(self.ops)
        self.apply()
        journal = self.only_journal()
        lines = journal.read_text().splitlines(keepends=True)
        lines[1] = lines[1].replace('"v2"', '"v3"')
        journal.write_text("".join(lines))
        code, _, _ = self.revert(journal)
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(self.a.read_text()), {"k": "v2"})

    def test_unsealed_journal_reverts_applied_ops_and_reports_unknown(self):
        self.write_set(self.ops)
        self.apply()
        journal = self.only_journal()
        rows = [json.loads(l) for l in journal.read_text().splitlines()]
        # Simulate a crash after op 0 completed and op 1's intent was written, before its outcome.
        kept = [r for r in rows if r["type"] in ("header",)
                or (r["type"] in ("intent", "outcome") and r["index"] == 0)
                or (r["type"] == "intent" and r["index"] == 1)]
        journal.write_text("".join(json.dumps(r) + "\n" for r in kept))
        code, report, _ = self.revert(journal)
        self.assertEqual(code, 2)
        by_file = {r["file"]: r["outcome"] for r in report["results"]}
        self.assertEqual(by_file[str(self.a)], "reverted")
        self.assertEqual(by_file[str(self.b)], "unknown")
        self.assertEqual(json.loads(self.b.read_text()), {"k": "w2"})


class Resume(Case):
    def test_rerun_after_partial_application_completes(self):
        a = self.root / "a.json"
        b = self.root / "b.json"
        a.write_text('{"k": "v2"}\n')   # op 0 already took effect before the "crash"
        b.write_text('{"k": "w1"}\n')
        self.write_set([
            {"op": "json_set", "file": str(a), "path": "/k", "expect_before": "v1", "value": "v2"},
            {"op": "json_set", "file": str(b), "path": "/k", "expect_before": "w1", "value": "w2"},
        ])
        code, report, _ = self.apply()
        self.assertEqual(code, 0)
        self.assertEqual(self.outcomes(report), ["already_applied", "applied"])


if __name__ == "__main__":
    unittest.main()
