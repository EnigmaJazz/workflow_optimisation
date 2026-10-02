#!/usr/bin/env python3
"""Plugin package cache integrity helper (stdlib only, JSON output).

check-pin: succeed only when <cache-root>/<pkg>@<ver>/node_modules/<pkg>/package.json
           exists and declares the pinned version.
scan:      report configured specs whose cache dir exists but is incomplete and,
           with --apply, MOVE (never delete) safely idle ones into quarantine.
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

# An incomplete package dir is quarantined only after this quiet period, so a
# dir OpenCode is still installing into (no lock covers its cache install) is
# never moved mid-install. Single source for the verifier and the tests.
QUIET_PERIOD_SECONDS = 600


def split_spec(spec):
    at = spec.rfind("@")
    if at <= 0:
        raise ValueError(f"spec must be <pkg>@<version>: {spec}")
    return spec[:at], spec[at + 1:]


def spec_dir(cache_root, spec):
    pkg, ver = split_spec(spec)
    return Path(cache_root) / f"{pkg}@{ver}"


def inspect(cache_root, spec):
    """Return (state, reason): state is complete | incomplete | absent."""
    pkg, ver = split_spec(spec)
    root = spec_dir(cache_root, spec)
    if not root.is_dir():
        return "absent", f"{root} does not exist"
    manifest = root / "node_modules" / pkg / "package.json"
    if not manifest.is_file():
        return "incomplete", f"missing {manifest}"
    try:
        found = json.loads(manifest.read_text(encoding="utf-8")).get("version")
    except Exception as exc:
        return "incomplete", f"unreadable {manifest} ({exc.__class__.__name__})"
    if found != ver:
        return "incomplete", f"version mismatch: pinned={ver} found={found}"
    return "complete", "package.json present and version matches"


def newest_mtime(root):
    newest = os.lstat(root).st_mtime
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            try:
                newest = max(newest, os.lstat(os.path.join(dirpath, name)).st_mtime)
            except OSError:
                pass
    return newest


def cmd_check_pin(args):
    state, reason = inspect(args.cache_root, args.spec)
    complete = state == "complete"
    print(json.dumps({"spec": args.spec, "complete": complete, "state": state, "reason": reason}))
    return 0 if complete else 1


def cmd_scan(args):
    results = []
    lock_present = Path(args.lock).exists()
    stamp = time.strftime("%Y%m%dT%H%M%S")
    for spec in args.spec:
        state, reason = inspect(args.cache_root, spec)
        entry = {"spec": spec, "state": state, "reason": reason}
        if state == "incomplete":
            root = spec_dir(args.cache_root, spec)
            age = time.time() - newest_mtime(root)
            defer = None
            if not args.apply:
                defer = "report only (no --apply)"
            elif lock_present:
                defer = f"auto-update lock present: {args.lock}"
            elif age < args.min_age_seconds:
                defer = f"modified {int(age)}s ago (< {args.min_age_seconds}s)"
            if defer:
                entry.update(action="deferred", detail=defer, path=str(root))
            else:
                dest_dir = Path(args.quarantine_dir) / stamp
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / spec.replace("/", "__")
                shutil.move(str(root), str(dest))
                entry.update(action="quarantined", path=str(root), quarantined_to=str(dest))
        results.append(entry)
    print(json.dumps({"results": results}))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check-pin")
    c.add_argument("--cache-root", required=True)
    c.add_argument("--spec", required=True)
    c.set_defaults(fn=cmd_check_pin)
    s = sub.add_parser("scan")
    s.add_argument("--cache-root", required=True)
    s.add_argument("--spec", action="append", default=[])
    s.add_argument("--lock", required=True)
    s.add_argument("--quarantine-dir", required=True)
    s.add_argument("--min-age-seconds", type=int, default=QUIET_PERIOD_SECONDS)
    s.add_argument("--apply", action="store_true")
    s.set_defaults(fn=cmd_scan)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
