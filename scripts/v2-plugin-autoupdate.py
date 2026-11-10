#!/usr/bin/env python3
"""Automatic, guarded plugin updates for the secured OpenCode V2 server.

  v2-plugin-autoupdate.py --opencode BIN --server URL --config opencode.json --state-dir DIR \\
      --password-file FILE --restart-cmd 'systemctl --user restart secure-opencode-v2.service' [--dry-run]

How it works (facts from OpenCode V2 2.2.2, opencode-v2-probe FINDINGS-3.md): a package plugin configured with a
`~x.y.z` range is refreshed by `opencode plugin update`: the newer patch is installed into the package cache, the config
file is not touched, the old cached copy stays, and the loaded version changes only after a restart.

Guardrails:
  1. Only `~x.y.z` patch ranges are updated. `^`, `*`, `latest`, bare names, `~x.y` and non-registry specs are reported
     as ineligible and never passed to `plugin update`; exact pins are left alone.
  2. After the restart, every plugin that was loaded before must load again (a failed plugin lists with ID `-`).
  3. If that gate fails, each updated package is pinned back to its previous exact version in the config (a timestamped
     backup is kept), the server is restarted and the gate is run again.
  4. Every step is appended to DIR/autoupdate.jsonl. The password is read from a mode 0600 file and handed to the CLI
     only through OPENCODE_PASSWORD; it is never printed, logged or put on a command line.
  5. One run at a time (a lock in DIR); --dry-run changes nothing.

Exit codes: 0 nothing to do or updated and gated; 3 the gate still fails after rollback; 4 rolled back (a release failed
the gate); 5 another run is active; 2 refused (bad arguments, unsafe password file, unreadable config).
"""
import argparse
import fcntl
import json
import os
import re
import shlex
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

NAME = r"(?:@[A-Za-z0-9][\w.-]*/)?[A-Za-z0-9][\w.-]*"
PATCH_RANGE = re.compile(rf"^(?P<name>{NAME})@~(?P<version>\d+\.\d+\.\d+)$")
EXACT = re.compile(rf"^(?P<name>{NAME})@(?P<version>\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)$")


class Refusal(Exception):
    pass


def spec_policy(spec):
    if PATCH_RANGE.match(spec):
        return "patch-range"
    if EXACT.match(spec):
        return "exact"
    return "ineligible"


def parse_list(text):
    """`plugin list` table -> {id: {version, source}}. A plugin that failed to load has the id `-`."""
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] != "ID" and re.match(r"^\d", parts[1]):
            out[parts[0]] = {"version": parts[1], "source": parts[2]}
    return out


def parse_check(text):
    """`plugin check` -> {id: 'current' | 'update available'}."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^\s+(\S+)\s+\S+\s+\((current|update available)\)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def read_specs(config_path):
    """The package specs in a JSON/JSONC config (`plugins` or `plugin`; string or {package: ...} entries)."""
    text = Path(config_path).read_text(encoding="utf-8")
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    data = json.loads(text)
    specs = []
    for key in ("plugins", "plugin"):
        for entry in data.get(key) or []:
            spec = entry if isinstance(entry, str) else (entry or {}).get("package")
            if isinstance(spec, str):
                specs.append(spec)
    return specs


class Job:
    def __init__(self, args):
        self.a = args
        self.state = Path(args.state_dir)
        self.state.mkdir(parents=True, exist_ok=True)
        self.password = self._read_password(args.password_file)

    @staticmethod
    def _read_password(path):
        p = Path(path)
        info = p.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise Refusal(f"password file must be owned by you with mode 0600: {path}")
        value = p.read_text(encoding="utf-8").strip()
        if not value:
            raise Refusal(f"password file is empty: {path}")
        return value

    def log(self, event, **fields):
        record = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, **fields}
        with open(self.state / "autoupdate.jsonl", "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        print(f"[autoupdate] {event} " + " ".join(f"{k}={v}" for k, v in fields.items()))

    def cli(self, *argv, timeout=180):
        env = {**os.environ, "OPENCODE_PASSWORD": self.password, "OPENCODE_DISABLE_FREE_MODELS": "1", "NO_COLOR": "1"}
        return subprocess.run([self.a.opencode, *argv, "--server", self.a.server], env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=timeout)

    def boot(self):
        """Wake the project (plugins activate on first use) and wait until it answers."""
        deadline = time.monotonic() + self.a.boot_timeout
        while True:
            try:
                if self.cli("debug", "agents", timeout=60).returncode == 0:
                    return True
            except subprocess.TimeoutExpired:
                pass
            if time.monotonic() >= deadline:
                return False
            time.sleep(min(3, max(0.2, self.a.boot_timeout / 10)))

    def snapshot(self):
        if not self.boot():
            return None, None
        return parse_list(self.cli("plugin", "list").stdout), parse_check(self.cli("plugin", "check").stdout)

    def restart(self):
        subprocess.run(["bash", "-c", self.a.restart_cmd], check=True, stdin=subprocess.DEVNULL)
        time.sleep(self.a.settle)

    def gate(self, before):
        after, _ = self.snapshot()
        if after is None:
            return False, "the server did not come back"
        if "-" in after:
            return False, "a plugin failed to load"
        missing = sorted(set(before) - set(after))
        if missing:
            return False, f"plugins missing after restart: {', '.join(missing)}"
        return True, ""

    def pin_back(self, previous):
        """Replace each updated package's range with its previous exact version; keeps a timestamped backup."""
        path = Path(self.a.config)
        text = path.read_text(encoding="utf-8")
        for spec, version in previous.items():
            name = PATCH_RANGE.match(spec).group("name")
            text = text.replace(f'"{spec}"', f'"{name}@{version}"')
        backup = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%dT%H%M%S.%f"))
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    def run(self):
        specs = read_specs(self.a.config)
        eligible = []
        for spec in specs:
            policy = spec_policy(spec)
            if policy == "ineligible":
                self.log("ineligible", spec=spec, reason="only ~x.y.z patch ranges are updated automatically")
            elif policy == "patch-range":
                eligible.append(spec)
        before, check = self.snapshot()
        if before is None:
            self.log("server-unreachable")
            return 3
        outdated = [i for i, status in check.items() if status == "update available"]
        if not eligible or not outdated:
            self.log("up-to-date", eligible=len(eligible), outdated=len(outdated))
            return 0
        if self.a.dry_run:
            self.log("would-update", targets=",".join(eligible), outdated=",".join(outdated))
            return 0
        previous = {}
        for spec in eligible:
            name = PATCH_RANGE.match(spec).group("name")
            for info in before.values():
                if info["source"] == spec or info["source"].split("@")[0] == name or name.endswith("/" + info["source"]):
                    previous[spec] = info["version"]
            if spec not in previous and len(before) == 1:
                previous[spec] = next(iter(before.values()))["version"]
        for spec in eligible:
            result = self.cli("plugin", "update", spec)
            self.log("update-ran", spec=spec, rc=result.returncode, output=result.stdout.strip()[:120])
        self.log("updated", before={s: v for s, v in previous.items()}, restart="yes" if self.a.restart_cmd else "required")
        if not self.a.restart_cmd:
            return 0
        self.restart()
        ok, why = self.gate(before)
        if ok:
            self.log("gate-passed")
            return 0
        self.log("gate-failed", reason=why)
        self.pin_back(previous)
        self.log("pinned-back", versions=json.dumps(previous))
        self.restart()
        ok, why = self.gate(before)
        if ok:
            self.log("rolled-back", versions=json.dumps(previous))
            return 4
        self.log("rollback-failed", reason=why)
        return 3


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--opencode", required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--state-dir", required=True)
    ap.add_argument("--password-file", required=True)
    ap.add_argument("--restart-cmd", default="")
    ap.add_argument("--require-branch", default="")
    ap.add_argument("--boot-timeout", type=float, default=90)
    ap.add_argument("--settle", type=float, default=5)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.require_branch:
            checkout = Path(__file__).resolve().parents[1]
            result = subprocess.run(["git", "-C", str(checkout), "rev-parse", "--abbrev-ref", "HEAD"],
                                   capture_output=True, text=True)
            observed = result.stdout.strip() if result.returncode == 0 else (result.stderr or result.stdout).strip()
            if result.returncode != 0 or observed != args.require_branch:
                raise Refusal(f"checkout branch {observed or 'unknown'} does not match required branch {args.require_branch}: {checkout}")
    except Refusal as err:
        print(f"[autoupdate] refused: {err}", file=sys.stderr)
        return 2
    Path(args.state_dir).mkdir(parents=True, exist_ok=True)
    lock = open(Path(args.state_dir) / "lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("[autoupdate] another run is active", file=sys.stderr)
        return 5
    try:
        return Job(args).run()
    except Refusal as err:
        print(f"[autoupdate] refused: {err}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError) as err:
        print(f"[autoupdate] refused: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
