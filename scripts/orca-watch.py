#!/usr/bin/env python3
"""Block until a NEW substantive Orca orchestration message arrives, print it, exit 0.

Run it with the harness's background mode (Claude Code: Bash run_in_background) so the session is
re-invoked on exit. `orca orchestration check --wait` is not usable for this: it replays old
messages. This snapshots the inbox first and reports only ids it has not seen, ignoring
heartbeats ("alive", "heartbeat").

Usage: orca-watch.py [--run RUN_ID]... [--from-prefix PREFIX]... [--timeout-seconds N] [--interval-seconds N] [--limit N]

The inbox is global. Without --run/--from-prefix every run's messages wake you; pass --run once per
run you coordinate so another project's traffic does not.
Exit: 0 new message printed; 2 timeout with nothing new.
"""

import argparse
import json
import subprocess
import sys
import time

IGNORED_SUBJECTS = {"alive", "heartbeat"}


def collect(node, out):
    if isinstance(node, dict):
        if "id" in node and "subject" in node:
            out.append(node)
            return
        for value in node.values():
            collect(value, out)
    elif isinstance(node, list):
        for value in node:
            collect(value, out)


def fetch(limit):
    proc = subprocess.run(
        ["orca", "orchestration", "inbox", "--full", "--limit", str(limit), "--json"],
        capture_output=True,
        text=True,
    )
    messages = []
    try:
        collect(json.loads(proc.stdout), messages)
    except ValueError:
        pass
    return messages


def substantive(message):
    return str(message.get("subject", "")).strip().lower() not in IGNORED_SUBJECTS


def wanted(message, runs, prefixes):
    if runs and message.get("run_id") not in runs:
        return False
    if prefixes and not str(message.get("from_handle", "")).startswith(tuple(prefixes)):
        return False
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--timeout-seconds", type=int, default=3300)
    parser.add_argument("--interval-seconds", type=int, default=20)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--run", action="append", default=[], help="only messages of this run id (repeatable)")
    parser.add_argument("--from-prefix", action="append", default=[], help="only senders starting with this handle prefix (repeatable)")
    args = parser.parse_args(argv)

    seen = {m["id"] for m in fetch(args.limit)}
    deadline = time.time() + args.timeout_seconds
    while time.time() < deadline:
        time.sleep(args.interval_seconds)
        fresh = [m for m in fetch(args.limit) if m["id"] not in seen]
        seen.update(m["id"] for m in fresh)
        fresh = [m for m in fresh if substantive(m) and wanted(m, args.run, args.from_prefix)]
        if fresh:
            for message in fresh:
                print("###", message["id"], message.get("from_handle", ""), message["subject"])
                print(message.get("body", ""))
            return 0
    print("TIMEOUT: no new messages")
    return 2


if __name__ == "__main__":
    sys.exit(main())
