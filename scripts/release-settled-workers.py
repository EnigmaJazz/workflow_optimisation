#!/usr/bin/env python3
"""Release the terminals of settled workers this run owns, so sessions do not pile up.

A worker is released only when Orca reports it reclaimable (settled), owned by us (not
user_owned/retained) and not already releasing. OpenCode 2 workers are meant to be reused, so
dispatch-worker.sh retains them and they are skipped here.

Usage: release-settled-workers.py [--run RUN_ID] [--dry-run]
"""
import argparse
import json
import subprocess
import sys


def orca(*args):
    out = subprocess.run(["orca", "orchestration", *args, "--json"], capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except ValueError:
        return {}


def workers(node, acc):
    if isinstance(node, dict):
        if "dispatchId" in node and "resource" in node:
            acc.append(node)
            return
        for v in node.values():
            workers(v, acc)
    elif isinstance(node, list):
        for v in node:
            workers(v, acc)


def releasable(w, run=None):
    r = w.get("resource") or {}
    return (
        w.get("terminalState") == "reclaimable"
        and r.get("ownershipState") == "owned"
        and r.get("releaseState") == "not_requested"
        and (run is None or w.get("runId") == run)
    )


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--run")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    found = []
    workers(orca("worker-list"), found)
    done = 0
    for w in filter(lambda x: releasable(x, a.run), found):
        print(("would release " if a.dry_run else "releasing ") + w["dispatchId"])
        if not a.dry_run:
            orca("worker-release", "--dispatch", w["dispatchId"])
        done += 1
    print(f"{done} worker(s) {'matched' if a.dry_run else 'released'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
