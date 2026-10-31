#!/usr/bin/env bash
# Put the V1 history into the V2 database (queue Q46, cutover step 4).
#
#   scripts/opencode-v2-db-swap.sh            # dry run: checks everything, prints the plan, changes nothing
#   scripts/opencode-v2-db-swap.sh --apply    # does it
#
# V1's opencode.db already holds the whole history in V2's tables (session_v2, session_message; kv migration.v1-v2 = completed),
# so V2 only needs a consistent copy of that file as its own database. The copy is built next to the live V2 database, checked,
# the V2 logins (credential rows for integrations V2 already has) are merged in, and only then are the files swapped. The old V2
# database files are moved to a dated folder inside the V2 data directory, never deleted. V1's file is only read.
#
# Overrides (tests): V1_DB, V2_DATA, SQLITE3, SYSTEMCTL, STAMP, SKIP_UNIT_CHECK=1.
set -euo pipefail

APPLY=0
case "${1:-}" in
  "") ;;
  --apply) APPLY=1 ;;
  -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
  *) echo "usage: $0 [--apply]" >&2; exit 2 ;;
esac

V1_DB="${V1_DB:-$HOME/.local/share/opencode/opencode.db}"
V2_DATA="${V2_DATA:-$HOME/.local/share/opencode-v2/data/opencode}"
SQLITE="${SQLITE3:-sqlite3}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
STAMP="${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
V2_DB="$V2_DATA/opencode.db"
INCOMING="$V2_DATA/opencode.db.incoming"
ASIDE="$V2_DATA/pre-v1-history-$STAMP"
UNITS=(secure-opencode-v2.service opencode-perm-v2.service secure-opencode.service)

fail() { echo "REFUSED: $*" >&2; exit 1; }
say() { echo "   $*"; }
q() { "$SQLITE" -readonly "$1" "$2"; }

echo "== OpenCode V2 database swap ($([ "$APPLY" -eq 1 ] && echo APPLY || echo dry run)) =="
command -v "$SQLITE" >/dev/null 2>&1 || fail "sqlite3 is not installed"
[ -f "$V1_DB" ] || fail "the V1 database is missing: $V1_DB"
[ -d "$V2_DATA" ] || fail "the V2 data directory is missing: $V2_DATA"
[ -f "$V2_DB" ] || fail "the V2 database is missing: $V2_DB"
[ ! -e "$INCOMING" ] || fail "$INCOMING already exists (a previous run was interrupted); inspect and remove it"
[ ! -e "$ASIDE" ] || fail "$ASIDE already exists"

# Only "inactive" and "failed" count as stopped: "activating" and "deactivating" are still moving, and an unreadable state is not proof.
units_stopped() {
  [ "${SKIP_UNIT_CHECK:-0}" != "1" ] || return 0
  local unit state
  for unit in "${UNITS[@]}"; do
    state=$("$SYSTEMCTL" --user is-active "$unit" 2>/dev/null || true)
    case "$state" in
      inactive|failed) ;;
      *) fail "$unit is running (state: ${state:-unknown}); stop it first: systemctl --user stop ${UNITS[*]}" ;;
    esac
  done
}

echo "-- services must be stopped (the databases must be quiescent)"
units_stopped
if [ "${SKIP_UNIT_CHECK:-0}" = "1" ]; then say "service check SKIPPED by SKIP_UNIT_CHECK (tests and read-only inspection only)"; else say "none of: ${UNITS[*]} is running"; fi

echo "-- V1 history must already be in V2 format"
v1_sessions=$(q "$V1_DB" "select count(*) from session;") || fail "cannot read the V1 session table"
v2_sessions=$(q "$V1_DB" "select count(*) from session_v2;") || fail "the V1 file has no session_v2 table (it was never migrated)"
phase=$(q "$V1_DB" "select value from kv where key='migration.v1-v2';" 2>/dev/null || true)
[ "$v1_sessions" -gt 0 ] || fail "the V1 database has no sessions"
[ "$v1_sessions" = "$v2_sessions" ] || fail "V1 has $v1_sessions sessions but only $v2_sessions in V2 format; the migration is incomplete"
case "$phase" in *completed*) ;; *) fail "kv migration.v1-v2 is not completed (got: ${phase:-none})" ;; esac
say "$v1_sessions sessions in both forms; migration.v1-v2 completed"

echo "-- credential tables must have the same columns"
cols1=$(q "$V1_DB" "select name||':'||type from pragma_table_info('credential') order by cid;")
cols2=$(q "$V2_DB" "select name||':'||type from pragma_table_info('credential') order by cid;") || fail "the V2 database has no credential table"
[ -n "$cols1" ] && [ "$cols1" = "$cols2" ] || fail "the credential tables differ in shape; merge by hand"
v2_creds=$(q "$V2_DB" "select count(*) from credential;")
v2_integrations=$(q "$V2_DB" "select group_concat(integration_id, ',') from credential;")
say "V2 holds $v2_creds login(s) that will replace V1's rows for the same integration (${v2_integrations:-none})"

echo "-- disk space"
need_kb=$(( ($(stat -c %s "$V1_DB") / 1024) * 12 / 10 ))
have_kb=$(df -Pk "$V2_DATA" | awk 'NR==2{print $4}')
[ "$have_kb" -gt "$need_kb" ] || fail "not enough free space in $V2_DATA: need about $((need_kb / 1024)) MB, have $((have_kb / 1024)) MB"
say "about $((need_kb / 1024)) MB needed, $((have_kb / 1024)) MB free"

echo "-- plan"
say "1. build $INCOMING from a consistent copy of $V1_DB"
say "2. merge the V2 logins into it, check integrity and counts"
if [ -n "${POOL_PROXY_KEY:-}" ]; then
  say "   the stored opencode-go key (V1's own key) is set to POOL_PROXY_KEY, because V2 sends the stored key, not the config's {env:POOL_PROXY_KEY}"
else
  say "   WARNING: POOL_PROXY_KEY is not in the environment, so the stored opencode-go key stays V1's own key and every proxy call will answer 401."
  say "   Re-run as: env (systemctl --user show-environment | grep '^POOL_PROXY_KEY=') bash $0 ... (Fish), or fix the row afterwards (docs/upgrades/opencode-v2-cutover.md, step 4)"
fi
say "3. move the current V2 database files to $ASIDE (V2 sessions that are not in V1 leave the live database and stay only there)"
say "4. install the new database as $V2_DB (mode 600)"
if [ "$APPLY" -ne 1 ]; then
  echo "== dry run complete: nothing was changed. Re-run with --apply. =="
  exit 0
fi

cleanup_incoming() { rm -f "$INCOMING" "$INCOMING-shm" "$INCOMING-wal"; }
trap cleanup_incoming EXIT
umask 077  # the copy holds the logins: it must never exist with wider permissions than the final file

echo "-- 1. copy"
"$SQLITE" -readonly "$V1_DB" ".backup '$INCOMING'"
echo "-- 2. merge and verify"
"$SQLITE" "$INCOMING" <<SQL
ATTACH DATABASE 'file:$V2_DB?mode=ro' AS v2live;
BEGIN IMMEDIATE;
DELETE FROM credential WHERE integration_id IN (SELECT integration_id FROM v2live.credential);
INSERT INTO credential SELECT * FROM v2live.credential;
COMMIT;
DETACH DATABASE v2live;
SQL
# V2 sends the credential stored for the provider, not the config's {env:POOL_PROXY_KEY}. V1's own opencode-go key came across in the
# copy and the proxy rejects it (401 "Missing or invalid proxy key"). The key is read from the environment inside python: it is never
# on a command line and never printed.
if [ -n "${POOL_PROXY_KEY:-}" ]; then
  python3 -I - "$INCOMING" <<'PY_SETKEY' || fail "could not set the stored opencode-go key"
import json, os, sqlite3, sys
db = sqlite3.connect(sys.argv[1])
row = db.execute("select value from credential where integration_id = 'opencode-go'").fetchone()
if row is None:
    print("   no stored opencode-go credential: nothing to set")
    raise SystemExit(0)
data = json.loads(row[0])
if not isinstance(data, dict):
    raise SystemExit("the stored opencode-go credential is not a JSON object")
data["key"] = os.environ["POOL_PROXY_KEY"]
db.execute("update credential set value = ? where integration_id = 'opencode-go'", (json.dumps(data),))
db.commit()
print("   stored opencode-go key set to POOL_PROXY_KEY")
PY_SETKEY
fi
[ "$("$SQLITE" -readonly "$INCOMING" 'pragma integrity_check;')" = "ok" ] || fail "integrity_check failed on the new database"
[ "$(q "$INCOMING" 'select count(*) from session_v2;')" = "$v2_sessions" ] || fail "the new database lost sessions"
# Compare against the live V2 database itself: every V2 login must be present, with the same value, in the new file.
lost=$("$SQLITE" -readonly "$INCOMING" "ATTACH DATABASE 'file:$V2_DB?mode=ro' AS v2live; select group_concat(v.integration_id, ',') from v2live.credential v left join credential c on c.integration_id = v.integration_id and c.value = v.value where c.integration_id is null;")
[ -z "$lost" ] || fail "V2 login(s) missing or changed after the merge: $lost"
say "integrity ok; $v2_sessions sessions; $(q "$INCOMING" 'select count(*) from credential;') logins"

units_stopped  # last check before anything is moved: a unit started during the copy would still be writing
MOVED=0  # stays 0 until an old V2 file has actually moved: before that, the recovery text would destroy the live database
ROLLBACK_SHOWN=0
show_rollback() {
  [ "$ROLLBACK_SHOWN" -eq 0 ] || return 0
  ROLLBACK_SHOWN=1
  echo "Rollback (if anything below fails): stop V2, then: rm -f '$V2_DB' '$V2_DB-shm' '$V2_DB-wal' && mv '$ASIDE'/opencode.db* '$V2_DATA'/"
}
on_exit() {
  if [ "$MOVED" -eq 1 ]; then
    echo "INTERRUPTED after the old V2 files were moved aside. If $INCOMING still exists it is the new database: finish by hand (mv it to $V2_DB, chmod 600). If it is gone the install already moved it, so check that $V2_DB exists and is mode 600. Or roll back with the command printed above." >&2
  else
    cleanup_incoming
  fi
}
trap on_exit EXIT
echo "-- 3. move the old files aside"
mkdir -p "$ASIDE"
for f in "$V2_DB" "$V2_DB-shm" "$V2_DB-wal"; do
  if [ -e "$f" ]; then
    mv "$f" "$ASIDE/"
    MOVED=1
    show_rollback
  fi
done
echo "-- 4. install"
mv "$INCOMING" "$V2_DB"
[ ! -e "$INCOMING-shm" ] || mv "$INCOMING-shm" "$V2_DB-shm"
[ ! -e "$INCOMING-wal" ] || mv "$INCOMING-wal" "$V2_DB-wal"
chmod 600 "$V2_DB"
trap - EXIT
echo "== done. The previous V2 database is in $ASIDE =="
echo "Rollback: stop V2, then: rm -f '$V2_DB' '$V2_DB-shm' '$V2_DB-wal' && mv '$ASIDE'/opencode.db* '$V2_DATA'/"
