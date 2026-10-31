"""scripts/opencode-v2-db-swap.sh: put the V1 history into the V2 database, dry run first (queue Q46, cutover step 4)."""
import os
import sqlite3
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "opencode-v2-db-swap.sh"
CRED = "CREATE TABLE credential (id text PRIMARY KEY, integration_id text, label text NOT NULL, value text NOT NULL, active integer, time_created integer NOT NULL)"


def make_v1(path, sessions=3, migrated=True, v2_sessions=None, extra_cred_col=False):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE session (id text PRIMARY KEY)")
    db.execute("CREATE TABLE session_v2 (id text PRIMARY KEY)")
    db.execute("CREATE TABLE kv (key text PRIMARY KEY, value text)")
    db.execute(CRED.replace("time_created integer NOT NULL", "time_created integer NOT NULL, extra text") if extra_cred_col else CRED)
    for i in range(sessions):
        db.execute("INSERT INTO session VALUES (?)", (f"s{i}",))
    for i in range(sessions if v2_sessions is None else v2_sessions):
        db.execute("INSERT INTO session_v2 VALUES (?)", (f"s{i}",))
    if migrated:
        db.execute("INSERT INTO kv VALUES ('migration.v1-v2', '{\"phase\":\"completed\"}')")
    for integration, value in (("deepseek", "v1-deepseek"), ("google", "v1-google"), ("openai", "v1-openai")):
        db.execute("INSERT INTO credential (id, integration_id, label, value, time_created) VALUES (?,?,?,?,1)"
                   if not extra_cred_col else "INSERT INTO credential (id, integration_id, label, value, time_created, extra) VALUES (?,?,?,?,1,'x')",
                   (f"c-v1-{integration}", integration, "API key", value))
    db.commit()
    db.close()


def make_v2(path):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE session_v2 (id text PRIMARY KEY)")
    db.execute(CRED)
    db.execute("INSERT INTO session_v2 VALUES ('v2-test')")
    for integration, value in (("deepseek", "v2-deepseek"), ("openrouter", "v2-openrouter"), ("openai", "v2-openai")):
        db.execute("INSERT INTO credential VALUES (?,?,?,?,1,2)", (f"c-v2-{integration}", integration, integration.title(), value))
    db.commit()
    db.close()


class Fixture:
    def __init__(self, units_active=(), **v1_kwargs):
        self.dir = Path(tempfile.mkdtemp())
        self.v1 = self.dir / "v1" / "opencode.db"
        self.v2data = self.dir / "v2" / "opencode"
        for p in (self.v1.parent, self.v2data):
            p.mkdir(parents=True)
        make_v1(self.v1, **v1_kwargs)
        make_v2(self.v2data / "opencode.db")
        stub = self.dir / "systemctl"
        active = " ".join(units_active)
        stub.write_text(f'#!/usr/bin/env bash\nunit="${{@: -1}}"\nfor u in {active}; do [ "$u" = "$unit" ] && exit 0; done\nexit 3\n')
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
        self.env = {**os.environ, "V1_DB": str(self.v1), "V2_DATA": str(self.v2data), "SYSTEMCTL": str(stub), "STAMP": "T1"}

    def run(self, *args):
        r = subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=self.env)
        return r.returncode, r.stdout + r.stderr

    def v2db(self):
        return self.v2data / "opencode.db"

    def creds(self, path=None):
        db = sqlite3.connect(f"file:{path or self.v2db()}?mode=ro", uri=True)
        try:
            return dict(db.execute("select integration_id, value from credential").fetchall())
        finally:
            db.close()


class DryRun(unittest.TestCase):
    def test_it_changes_nothing_and_prints_the_plan(self):
        f = Fixture()
        before = f.v2db().read_bytes()
        code, out = f.run()
        self.assertEqual(code, 0, out)
        self.assertIn("dry run complete: nothing was changed", out)
        self.assertIn("3 sessions in both forms", out)
        self.assertIn("V2 holds 3 login(s)", out)
        self.assertEqual(f.v2db().read_bytes(), before)
        self.assertEqual(sorted(p.name for p in f.v2data.iterdir()), ["opencode.db"])

    def test_it_is_the_default_and_help_prints_usage(self):
        code, out = Fixture().run("-h")
        self.assertEqual(code, 0)
        self.assertIn("--apply", out)
        self.assertEqual(Fixture().run("--nonsense")[0], 2)


class Refusals(unittest.TestCase):
    def refused(self, fixture, fragment, *args):
        before = fixture.v2db().read_bytes()
        code, out = fixture.run(*args)
        self.assertEqual(code, 1, out)
        self.assertIn("REFUSED", out)
        self.assertIn(fragment, out)
        self.assertEqual(fixture.v2db().read_bytes(), before)  # a refusal never touches the V2 database
        self.assertEqual(sorted(p.name for p in fixture.v2data.iterdir()), ["opencode.db"])

    def test_a_running_service_is_refused_even_with_apply(self):
        for unit in ("secure-opencode-v2.service", "opencode-perm-v2.service", "secure-opencode.service"):
            self.refused(Fixture(units_active=[unit]), f"{unit} is running", "--apply")

    def test_history_that_is_not_fully_in_v2_format_is_refused(self):
        self.refused(Fixture(v2_sessions=2), "migration is incomplete", "--apply")
        self.refused(Fixture(migrated=False), "migration.v1-v2 is not completed", "--apply")
        self.refused(Fixture(sessions=0), "no sessions", "--apply")

    def test_differing_credential_tables_are_refused(self):
        self.refused(Fixture(extra_cred_col=True), "credential tables differ", "--apply")

    def test_missing_files_are_refused(self):
        f = Fixture()
        f.v1.unlink()
        self.refused(f, "V1 database is missing", "--apply")

    def test_a_leftover_incoming_file_or_aside_folder_is_refused(self):
        f = Fixture()
        (f.v2data / "opencode.db.incoming").write_text("x")
        code, out = f.run("--apply")
        self.assertEqual(code, 1)
        self.assertIn("previous run was interrupted", out)
        f = Fixture()
        (f.v2data / "pre-v1-history-T1").mkdir()
        self.assertIn("already exists", f.run("--apply")[1])


class Apply(unittest.TestCase):
    def test_apply_installs_the_v1_history_merges_the_v2_logins_and_keeps_the_old_files(self):
        f = Fixture()
        code, out = f.run("--apply")
        self.assertEqual(code, 0, out)
        db = sqlite3.connect(f"file:{f.v2db()}?mode=ro", uri=True)
        self.assertEqual(db.execute("select count(*) from session_v2").fetchone()[0], 3)  # V1's history, not the V2 test session
        self.assertEqual(db.execute("select count(*) from session_v2 where id='v2-test'").fetchone()[0], 0)
        db.close()
        self.assertEqual(f.creds(), {"deepseek": "v2-deepseek", "openai": "v2-openai", "openrouter": "v2-openrouter", "google": "v1-google"})
        self.assertEqual(stat.S_IMODE(f.v2db().stat().st_mode), 0o600)
        aside = f.v2data / "pre-v1-history-T1"
        self.assertEqual(f.creds(aside / "opencode.db"), {"deepseek": "v2-deepseek", "openai": "v2-openai", "openrouter": "v2-openrouter"})
        self.assertFalse((f.v2data / "opencode.db.incoming").exists())
        self.assertIn("Rollback:", out)

    def test_the_v1_database_is_only_read(self):
        f = Fixture()
        before = f.v1.read_bytes()
        self.assertEqual(f.run("--apply")[0], 0)
        self.assertEqual(f.v1.read_bytes(), before)

    def test_a_failure_while_building_leaves_the_v2_database_and_no_incoming_file(self):
        f = Fixture()
        sqlite_stub = f.dir / "sqlite3"
        sqlite_stub.write_text('#!/usr/bin/env bash\nfor a in "$@"; do case "$a" in *.backup*) echo boom >&2; exit 9;; esac; done\nexec sqlite3 "$@"\n'.replace("exec sqlite3", f"exec {subprocess.check_output(['which', 'sqlite3'], text=True).strip()}"))
        sqlite_stub.chmod(sqlite_stub.stat().st_mode | stat.S_IEXEC)
        f.env["SQLITE3"] = str(sqlite_stub)
        before = f.v2db().read_bytes()
        code, _ = f.run("--apply")
        self.assertNotEqual(code, 0)
        self.assertEqual(f.v2db().read_bytes(), before)
        self.assertEqual(sorted(p.name for p in f.v2data.iterdir()), ["opencode.db"])

    def test_wal_files_of_the_old_database_move_aside_with_it(self):
        f = Fixture()
        (f.v2data / "opencode.db-wal").write_bytes(b"")
        (f.v2data / "opencode.db-shm").write_bytes(b"shm")
        self.assertEqual(f.run("--apply")[0], 0)
        aside = sorted(p.name for p in (f.v2data / "pre-v1-history-T1").iterdir())
        self.assertEqual(aside, ["opencode.db", "opencode.db-shm", "opencode.db-wal"])
        self.assertFalse((f.v2data / "opencode.db-shm").exists())


if __name__ == "__main__":
    unittest.main()
