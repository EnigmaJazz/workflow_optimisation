#!/usr/bin/env python3
"""Host-side usage ledger (criteria S2-S11, docs/specs/multi-tier-orchestration.md section 10).

Stores usage counts only (never message content) in sqlite at $USAGE_LEDGER_DB
(default ~/.local/state/usage-ledger/ledger.sqlite). Standard library only.

Commands: ingest-claude, ingest-codex, ingest-opencode, record, report, check.
`check` exit code: 0 ok, 1 downgrade-model, 2 skip-tier3 (worst subscription), 3 bad config.
"""

import argparse
import glob
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta, timezone

COLS = ("source key ts subscription tier kind session model project stage calls "
        "input output cache_read cache_write").split()
SCHEMA = """CREATE TABLE IF NOT EXISTS usage (
  source TEXT NOT NULL, key TEXT NOT NULL, ts TEXT NOT NULL, subscription TEXT NOT NULL, tier TEXT,
  kind TEXT NOT NULL DEFAULT 'usage', session TEXT, model TEXT, project TEXT, stage TEXT,
  calls INTEGER NOT NULL DEFAULT 1, input INTEGER NOT NULL DEFAULT 0, output INTEGER NOT NULL DEFAULT 0,
  cache_read INTEGER NOT NULL DEFAULT 0, cache_write INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (source, key))"""
STATES = ("ok", "downgrade-model", "skip-tier3")


def connect():
    path = os.environ.get("USAGE_LEDGER_DB") or os.path.expanduser("~/.local/state/usage-ledger/ledger.sqlite")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = sqlite3.connect(path)
    db.execute(SCHEMA)
    return db


def put(db, **row):
    v = {c: row.get(c) for c in COLS}
    v["kind"], v["calls"] = v["kind"] or "usage", row.get("calls", 1)
    for c in ("input", "output", "cache_read", "cache_write"):
        v[c] = v[c] or 0
    db.execute(f"INSERT OR REPLACE INTO usage ({','.join(COLS)}) VALUES ({','.join(':' + c for c in COLS)})", v)


def jsonl(root):
    for path in sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)):
        with open(path, errors="replace") as f:
            for n, line in enumerate(f):
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict):
                    yield path, n, d


def ts_of(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def claude_tokens(u):
    return dict(input=u.get("input_tokens"), output=u.get("output_tokens"),
                cache_read=u.get("cache_read_input_tokens"), cache_write=u.get("cache_creation_input_tokens"))


def ingest_claude(db, a):
    for _, _, d in jsonl(a.root):
        m = d.get("message")
        u = m.get("usage") if isinstance(m, dict) else None
        if not u or m.get("model") == "<synthetic>":
            continue
        key = f"{m.get('id') or d.get('uuid')}:{d.get('requestId')}"  # streaming partials share it; last wins
        common = dict(source="claude", ts=d["timestamp"], subscription="claude", tier=a.tier,
                      session=d.get("sessionId"), project=d.get("cwd"))
        put(db, key=key, model=m.get("model"), **common, **claude_tokens(u))
        for i, it in enumerate(u.get("iterations") or []):
            if it.get("type") == "advisor_message":  # advisor tokens are not in the top-level usage
                put(db, key=f"{key}:adv{i}", kind="advisor", model=it.get("model"), **common, **claude_tokens(it))


def ingest_codex(db, a):
    meta = {}  # per file: session id, cwd, current model, last seen totals (events repeat unchanged totals)
    for path, n, d in jsonl(a.root):
        p, m = d.get("payload") or {}, meta.setdefault(path, {})
        if d.get("type") == "session_meta":
            m.update(session=p.get("id"), cwd=p.get("cwd"))
        elif d.get("type") == "turn_context":
            m["model"] = p.get("model")
        elif p.get("type") == "token_count" and p.get("info") and p["info"]["total_token_usage"] != m.get("total"):
            m["total"], u = p["info"]["total_token_usage"], p["info"]["last_token_usage"]
            if not (u.get("input_tokens") or u.get("output_tokens")):
                continue
            cached = u.get("cached_input_tokens") or 0
            put(db, source="codex", key=f"{os.path.basename(path)}:{n}", ts=d["timestamp"], subscription="openai",
                tier=a.tier, session=m.get("session"), model=m.get("model"), project=m.get("cwd"),
                input=(u.get("input_tokens") or 0) - cached, output=u.get("output_tokens"), cache_read=cached,
                cache_write=u.get("cache_write_input_tokens"))


def ingest_opencode(db, a):
    ro = lambda path: sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    dirs = dict(ro(a.opencode_db).execute("SELECT id, directory FROM session")) if os.path.exists(a.opencode_db) else {}
    for r in ro(a.proxy).execute("SELECT id, started_at, session_key, agent, COALESCE(logical_model, requested_model),"
                                 " backend, fresh_in, cache_read, cache_write, output FROM requests"):
        put(db, source="opencode", key=str(r[0]), ts=r[1], subscription=f"opencode-{r[5]}", tier="5", session=r[2],
            stage=r[3], model=r[4], project=dirs.get(r[2]), input=r[6], cache_read=r[7], cache_write=r[8], output=r[9])


def record(db, a):
    put(db, source="manual", key=str(uuid.uuid4()), ts=a.ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        subscription=a.subscription, tier=a.tier, kind=a.kind, session=a.session, model=a.model, project=a.project,
        stage=a.stage, calls=a.calls, input=a.input, output=a.output)


def die(msg):
    print(f"usage_ledger: {msg}", file=sys.stderr)
    sys.exit(3)


def load_config(path):
    if not path:
        return {}
    try:
        cfg = json.load(open(path))
        for sub, t in cfg.get("thresholds", {}).items():
            if t["unit"] not in ("tokens", "calls") or t["limit"] <= 0 or t["window_hours"] <= 0:
                raise ValueError(f"{sub}: unit must be tokens|calls; limit and window_hours must be positive")
            if not 0 < t["downgrade_at"] <= t["skip_tier3_at"] <= 1:
                raise ValueError(f"{sub}: need 0 < downgrade_at <= skip_tier3_at <= 1")
    except (OSError, ValueError, KeyError, TypeError) as e:
        die(f"bad config {path}: {e!r}")
    return cfg


def load_rows(db, cfg, window_hours=5):
    rows = [dict(zip(COLS, r)) for r in db.execute(f"SELECT {','.join(COLS)} FROM usage ORDER BY ts")]
    start = None  # Claude plan-limit window: opens at the first request after the previous one closed
    for r in rows:
        if not r["tier"]:  # explicit tier wins; else first matching tier_map entry
            r["tier"] = next((m["tier"] for m in cfg.get("tier_map", []) if all(
                (r[k] or "").startswith(v) if k == "project" else r[k] == v for k, v in m.items() if k != "tier")),
                "unattributed")
        if r["subscription"] == "claude":
            if start is None or ts_of(r["ts"]) >= start + timedelta(hours=window_hours):
                start = ts_of(r["ts"])
            r["window"] = (start, start + timedelta(hours=window_hours))
    return rows


def report(db, a):
    rows = [r for r in load_rows(db, load_config(a.config), a.window_hours)
            if r["ts"].startswith(a.day or "") and (r["project"] or "").startswith(a.project or "")
            and (not a.stage or r["stage"] == a.stage)]
    days, windows = {}, {}
    for r in rows:
        t = days.setdefault((r["ts"][:10], r["subscription"], r["tier"]), [0] * 5)
        for i, v in enumerate((r["calls"], r["input"], r["output"], r["cache_read"], r["cache_write"])):
            t[i] += v
        if "window" in r:
            windows[(r["session"], *r["window"])] = windows.get((r["session"], *r["window"]), 0) + r["input"] + r["output"]
    for k, v in sorted(days.items()):
        print("\t".join(map(str, (*k, *v))))
    for (session, s, e), tokens in sorted(windows.items(), key=lambda x: (x[0][1], str(x[0][0]))):
        print("\t".join(("window", str(session), s.isoformat(), e.isoformat(), str(tokens))))


def check(db, a):
    cfg = load_config(a.config)
    now = ts_of(a.now) if a.now else datetime.now(timezone.utc)
    rows, worst = load_rows(db, cfg), 0
    for sub, t in sorted(cfg.get("thresholds", {}).items()):
        since = now - timedelta(hours=t["window_hours"])
        used = sum(r["calls"] if t["unit"] == "calls" else r["input"] + r["output"]
                   for r in rows if r["subscription"] == sub and since < ts_of(r["ts"]) <= now)
        frac = used / t["limit"]
        state = 2 if frac >= t["skip_tier3_at"] else 1 if frac >= t["downgrade_at"] else 0
        worst = max(worst, state)
        print(f"{sub}\t{STATES[state]}\t{used}/{t['limit']} {t['unit']} in {t['window_hours']}h")
    return worst


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    home = os.path.expanduser

    def cmd(name, fn, **defaults):
        s = sub.add_parser(name)
        s.set_defaults(fn=fn)
        for flag, default in defaults.items():
            s.add_argument("--" + flag.replace("_", "-"), default=default)
        return s

    cmd("ingest-claude", ingest_claude, root=home("~/.claude/projects"), tier=None)
    cmd("ingest-codex", ingest_codex, root=home("~/.codex/sessions"), tier=None)
    cmd("ingest-opencode", ingest_opencode, proxy=home("~/.local/state/opencode-go-proxy/proxy.sqlite"),
        opencode_db=home("~/.local/share/opencode/opencode.db"))
    r = cmd("record", record, tier=None, ts=None, kind="usage", session=None, model=None, project=None, stage=None)
    r.add_argument("--subscription", required=True)
    for f, d in (("calls", 1), ("input", 0), ("output", 0)):
        r.add_argument("--" + f, type=int, default=d)
    cmd("report", report, config=None, day=None, project=None, stage=None).add_argument(
        "--window-hours", type=float, default=5)
    cmd("check", check, now=None).add_argument("--config", required=True)
    a = p.parse_args(argv)
    db = connect()
    result = a.fn(db, a)
    db.commit()
    return result or 0


if __name__ == "__main__":
    sys.exit(main())
