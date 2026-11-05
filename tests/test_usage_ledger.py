"""Tests for scripts/usage_ledger.py (spec: criteria S1-S11, docs/specs/multi-tier-orchestration.md section 10).

Every test drives the CLI as production does, with synthetic fixtures only.
Run: python3 -m unittest tests.test_usage_ledger -v
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "usage_ledger.py"
SECRET = "SECRET-MESSAGE-CONTENT"


class Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="usage-ledger-test-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.db = self.tmp / "ledger.sqlite"

    def run_cli(self, *args, env=None, expect=0):
        e = {**os.environ, "USAGE_LEDGER_DB": str(self.db), **(env or {})}
        p = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, env=e)
        self.assertEqual(p.returncode, expect, p.stdout + p.stderr)
        return p.stdout

    def rows(self, sql="select * from usage order by ts, key"):
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        return [dict(r) for r in c.execute(sql)]

    def write_jsonl(self, path, objs):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(o) + "\n" for o in objs))

    def record(self, sub, tier, ts, calls=1, **kw):
        extra = [x for k, v in kw.items() for x in (f"--{k.replace('_', '-')}", v)]
        self.run_cli("record", "--subscription", sub, "--tier", tier, "--ts", ts, "--calls", calls, *extra)

    def config(self, **cfg):
        p = self.tmp / "config.json"
        p.write_text(json.dumps(cfg))
        return p


class ClaudeIngest(Case):
    def fixture(self):
        usage = {"input_tokens": 4, "output_tokens": 496, "cache_read_input_tokens": 100,
                 "cache_creation_input_tokens": 50,
                 "iterations": [{"type": "message", "input_tokens": 2, "output_tokens": 84},
                                {"type": "advisor_message", "model": "claude-opus-x", "input_tokens": 97494,
                                 "output_tokens": 5327, "cache_read_input_tokens": 7, "cache_creation_input_tokens": 3}]}
        partial = {**usage, "output_tokens": 10, "iterations": []}
        base = {"type": "assistant", "sessionId": "s1", "cwd": "/work/proj", "requestId": "r1"}

        def line(u, ts):
            return {**base, "timestamp": ts, "message": {"id": "m1", "role": "assistant", "model": "claude-sonnet-x",
                                                         "content": [{"type": "text", "text": SECRET}], "usage": u}}
        self.root = self.tmp / "claude"
        self.write_jsonl(self.root / "p" / "s1.jsonl", [
            {"type": "user", "sessionId": "s1", "message": {"role": "user", "content": SECRET}},
            line(partial, "2026-11-04T10:00:00.000Z"),   # streaming partial, superseded by the next line
            line(usage, "2026-11-04T10:00:01.000Z"),
            {**base, "timestamp": "2026-11-04T10:00:02.000Z",
             "message": {"id": "m2", "model": "<synthetic>", "usage": {"input_tokens": 0, "output_tokens": 0}}},
        ])

    def test_stores_usage_fields_only_and_dedupes_streaming_partials(self):
        self.fixture()
        out = self.run_cli("ingest-claude", "--root", self.root)
        self.assertNotIn(SECRET, out)
        main = [r for r in self.rows() if r["kind"] == "usage"]
        self.assertEqual(len(main), 1)  # partial replaced, synthetic skipped
        r = main[0]
        self.assertEqual((r["subscription"], r["session"], r["model"], r["project"]),
                         ("claude", "s1", "claude-sonnet-x", "/work/proj"))
        self.assertEqual((r["input"], r["output"], r["cache_read"], r["cache_write"]), (4, 496, 100, 50))
        self.assertNotIn(SECRET.encode(), self.db.read_bytes())

    def test_advisor_iteration_becomes_its_own_row(self):
        self.fixture()
        self.run_cli("ingest-claude", "--root", self.root)
        adv = [r for r in self.rows() if r["kind"] == "advisor"]
        self.assertEqual(len(adv), 1)
        self.assertEqual((adv[0]["subscription"], adv[0]["model"], adv[0]["input"], adv[0]["output"]),
                         ("claude", "claude-opus-x", 97494, 5327))

    def test_ingest_is_idempotent_and_tier_flag_stamps_rows(self):
        self.fixture()
        self.run_cli("ingest-claude", "--root", self.root, "--tier", "2")
        n = len(self.rows())
        self.run_cli("ingest-claude", "--root", self.root, "--tier", "2")
        self.assertEqual(len(self.rows()), n)
        self.assertEqual({r["tier"] for r in self.rows()}, {"2"})


class CodexIngest(Case):
    def test_input_excludes_cached_and_model_comes_from_turn_context(self):
        root = self.tmp / "codex"
        usage = {"input_tokens": 1000, "cached_input_tokens": 400, "output_tokens": 50, "cache_write_input_tokens": 0}
        tc = {"type": "event_msg", "timestamp": "2026-11-04T09:00:00.000Z",
              "payload": {"type": "token_count", "info": {"total_token_usage": usage, "last_token_usage": usage}}}
        self.write_jsonl(root / "2026" / "11" / "04" / "rollout-a.jsonl", [
            {"type": "session_meta", "payload": {"id": "c1", "cwd": "/work/codex-proj"}},
            {"type": "turn_context", "payload": {"model": "gpt-x"}},
            {"type": "response_item", "payload": {"type": "message", "content": SECRET}},
            {"type": "event_msg", "timestamp": "2026-11-04T08:59:00.000Z", "payload": {"type": "token_count", "info": None}},
            tc,
            {**tc, "timestamp": "2026-11-04T09:00:01.000Z"},  # repeated event with unchanged totals
        ])
        out = self.run_cli("ingest-codex", "--root", root, "--tier", "4")
        self.assertNotIn(SECRET, out)
        (r,) = self.rows()
        self.assertEqual((r["subscription"], r["tier"], r["session"], r["model"], r["project"]),
                         ("openai", "4", "c1", "gpt-x", "/work/codex-proj"))
        self.assertEqual((r["input"], r["cache_read"], r["output"]), (600, 400, 50))
        self.assertNotIn(SECRET.encode(), self.db.read_bytes())


class OpencodeIngest(Case):
    def fixture(self, with_sessions=True):
        proxy = self.tmp / "proxy.sqlite"
        c = sqlite3.connect(proxy)
        c.execute("create table requests (id integer primary key, started_at text, session_key text, agent text,"
                  " requested_model text, logical_model text, backend text, fresh_in int, cache_read int,"
                  " cache_write int, output int)")
        c.execute("insert into requests values (1,'2026-11-04T08:00:00.000Z','ses_a','planner','m','kimi','go',10,20,30,40)")
        c.execute("insert into requests values (2,'2026-11-04T08:01:00.000Z','ses_b',null,'m2',null,'cc',1,null,null,2)")
        c.commit()
        oc = self.tmp / "opencode.db"
        if with_sessions:
            c = sqlite3.connect(oc)
            c.execute("create table session (id text primary key, directory text)")
            c.execute("insert into session values ('ses_a', '/work/repo-a')")
            c.commit()
        return proxy, oc

    def test_attributes_repository_and_stage_where_known(self):
        proxy, oc = self.fixture()
        self.run_cli("ingest-opencode", "--proxy", proxy, "--opencode-db", oc)
        a, b = self.rows()
        self.assertEqual((a["subscription"], a["tier"], a["project"], a["stage"], a["model"]),
                         ("opencode-go", "5", "/work/repo-a", "planner", "kimi"))
        self.assertEqual((a["input"], a["cache_read"], a["cache_write"], a["output"]), (10, 20, 30, 40))
        self.assertEqual((b["subscription"], b["project"], b["stage"], b["model"], b["cache_read"]),
                         ("opencode-cc", None, None, "m2", 0))

    def test_missing_opencode_db_still_ingests_without_repository(self):
        proxy, oc = self.fixture(with_sessions=False)
        self.run_cli("ingest-opencode", "--proxy", proxy, "--opencode-db", oc)
        self.assertEqual({r["project"] for r in self.rows()}, {None})
        self.assertEqual(len(self.rows()), 2)

    def test_source_databases_are_not_modified(self):
        proxy, oc = self.fixture()
        before = (proxy.read_bytes(), oc.read_bytes())
        self.run_cli("ingest-opencode", "--proxy", proxy, "--opencode-db", oc)
        self.assertEqual((proxy.read_bytes(), oc.read_bytes()), before)


class Record(Case):
    def test_manual_entries_for_antigravity_advisor_and_jev(self):
        self.record("google", "3", "2026-11-04T12:00:00Z", calls=3, kind="antigravity")
        self.record("claude", "2", "2026-11-04T12:01:00Z", kind="advisor", model="opus", input="900", output="40")
        self.record("typesafe", "2", "2026-11-04T12:02:00Z", kind="jev")
        ag, adv, jev = self.rows()
        self.assertEqual((ag["subscription"], ag["tier"], ag["kind"], ag["calls"]), ("google", "3", "antigravity", 3))
        self.assertEqual((adv["subscription"], adv["kind"], adv["input"], adv["output"]), ("claude", "advisor", 900, 40))
        self.assertEqual((jev["subscription"], jev["kind"], jev["calls"]), ("typesafe", "jev", 1))

    def test_default_db_path_is_outside_the_repo_under_home(self):
        home = self.tmp / "home"
        env = {"HOME": str(home)}
        e = {k: v for k, v in os.environ.items() if k != "USAGE_LEDGER_DB"}
        subprocess.run([sys.executable, str(SCRIPT), "record", "--subscription", "google", "--calls", "1"],
                       env={**e, **env}, check=True, capture_output=True)
        self.assertTrue((home / ".local/state/usage-ledger/ledger.sqlite").exists())


class Report(Case):
    def test_usage_per_tier_per_day(self):
        for tier in "12345":
            self.record("sub", tier, "2026-11-04T10:00:00Z", input="10", output="1")
        self.record("sub", "1", "2026-11-04T23:00:00Z", input="5")
        self.record("sub", "1", "2026-11-05T01:00:00Z", input="7")
        out = self.run_cli("report")
        lines = [l.split("\t") for l in out.splitlines()]
        self.assertIn(["2026-11-04", "sub", "1", "2", "15", "1", "0", "0"], lines)
        self.assertIn(["2026-11-05", "sub", "1", "1", "7", "0", "0", "0"], lines)
        self.assertEqual(sum(1 for l in lines if l[0] == "2026-11-04"), 5)

    def test_tier_from_config_mapping_and_unattributed(self):
        self.run_cli("record", "--subscription", "openai", "--ts", "2026-11-04T10:00:00Z",
                     "--project", "/work/spec/sub", "--model", "gpt-x")
        self.run_cli("record", "--subscription", "openai", "--ts", "2026-11-04T10:00:00Z", "--project", "/other")
        cfg = self.config(tier_map=[{"project": "/work/spec", "model": "gpt-x", "tier": "4"}])
        out = self.run_cli("report", "--config", cfg)
        self.assertIn("2026-11-04\topenai\t4\t1", out)
        self.assertIn("2026-11-04\topenai\tunattributed\t1", out)

    def test_filters_by_project_and_stage(self):
        self.record("s", "5", "2026-11-04T10:00:00Z", project="/repo-a", stage="plan", input="1")
        self.record("s", "5", "2026-11-04T10:00:00Z", project="/repo-b", stage="build", input="2")
        out = self.run_cli("report", "--project", "/repo-a", "--stage", "plan")
        self.assertIn("\t5\t1\t1\t", out)
        self.assertNotIn("\t5\t1\t2\t", out)

    def test_claude_plan_limit_windows_per_session(self):
        self.record("claude", "2", "2026-11-04T00:00:00Z", session="a", input="10")
        self.record("claude", "2", "2026-11-04T04:59:00Z", session="b", input="20", output="1")
        self.record("claude", "2", "2026-11-04T05:00:00Z", session="a", input="40")  # exactly 5h: new window
        self.record("openai", "4", "2026-11-04T00:00:00Z", session="x", input="99")  # not Claude: no window
        out = self.run_cli("report")
        win = [l.split("\t") for l in out.splitlines() if l.startswith("window\t")]
        self.assertEqual(sorted(win), sorted([
            ["window", "a", "2026-11-04T00:00:00+00:00", "2026-11-04T05:00:00+00:00", "10"],
            ["window", "b", "2026-11-04T00:00:00+00:00", "2026-11-04T05:00:00+00:00", "21"],
            ["window", "a", "2026-11-04T05:00:00+00:00", "2026-11-04T10:00:00+00:00", "40"]]))


class Check(Case):
    CFG = {"thresholds": {"claude": {"unit": "tokens", "window_hours": 5, "limit": 1000,
                                     "downgrade_at": 0.7, "skip_tier3_at": 0.9}}}
    NOW = "2026-11-04T12:00:00Z"

    def check(self, tokens, expect, state, cfg=None, extra=()):
        self.db.unlink(missing_ok=True)
        if tokens is not None:
            self.record("claude", "2", "2026-11-04T10:00:00Z", input=str(tokens))
        out = self.run_cli("check", "--config", self.config(**(cfg or self.CFG)), "--now", self.NOW, *extra, expect=expect)
        self.assertEqual(out.split("\t")[:2], ["claude", state])

    def test_states_cross_thresholds_before_the_limit(self):
        self.check(None, 0, "ok")
        self.check(699, 0, "ok")
        self.check(700, 1, "downgrade-model")
        self.check(899, 1, "downgrade-model")
        self.check(900, 2, "skip-tier3")      # still below the limit of 1000

    def test_rows_outside_the_window_do_not_count(self):
        self.record("claude", "2", "2026-11-04T06:59:00Z", input="5000")  # 5h01m before now
        self.record("claude", "2", "2026-11-04T10:00:00Z", input="10")
        out = self.run_cli("check", "--config", self.config(**self.CFG), "--now", self.NOW)
        self.assertTrue(out.startswith("claude\tok\t10/1000"), out)

    def test_calls_unit_and_exit_code_is_the_worst_state(self):
        cfg = {"thresholds": {**self.CFG["thresholds"],
                              "google": {"unit": "calls", "window_hours": 24, "limit": 10,
                                         "downgrade_at": 0.5, "skip_tier3_at": 0.8}}}
        self.record("google", "3", "2026-11-04T01:00:00Z", calls=8, kind="antigravity")
        self.record("claude", "2", "2026-11-04T10:00:00Z", input="800")
        out = self.run_cli("check", "--config", self.config(**cfg), "--now", self.NOW, expect=2)
        self.assertIn("claude\tdowngrade-model", out)
        self.assertIn("google\tskip-tier3", out)

    def test_invalid_config_is_rejected_with_exit_3(self):
        bad = {"thresholds": {"claude": {**self.CFG["thresholds"]["claude"], "downgrade_at": 0.95}}}
        self.run_cli("check", "--config", self.config(**bad), expect=3)
        self.run_cli("check", "--config", self.config(thresholds={"x": {"unit": "usd"}}), expect=3)

    def test_example_config_is_valid(self):
        example = SCRIPT.with_name("usage-ledger.example.json")
        self.run_cli("check", "--config", example, "--now", self.NOW)


if __name__ == "__main__":
    unittest.main()
