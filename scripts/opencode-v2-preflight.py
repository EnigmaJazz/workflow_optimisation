#!/usr/bin/env python3
"""Read-only readiness report for the OpenCode V2 cutover (queue Q46; runbook: docs/upgrades/opencode-v2-cutover.md).

It automates the checks the runbook can automate and lists the gates it cannot. It writes nothing, restarts nothing and never
prints a secret. Exit code 1 when any check FAILs, otherwise 0. WARN means "look at this", MANUAL means "the owner runs it".

  python3 scripts/opencode-v2-preflight.py            # fast checks
  python3 scripts/opencode-v2-preflight.py --stack    # also run the V2 stack check (about a minute)
  python3 scripts/opencode-v2-preflight.py --json
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOME = Path.home()
V2_ROOT = HOME / ".local/share/opencode-v2"
SANDBOX = HOME / "agent-sandbox-integration"
UNITS = ("secure-opencode-v2.service", "opencode-perm-v2.service")
V1_UNITS = ("secure-opencode.service", "opencode-perm.service")

MANUAL_GATES = (
    "host read routing and mutation blocking",
    "lazy worker activation",
    "sandbox_edit (mode preserved)",
    "sandbox_apply approval with the full preview",
    "a host_git_commit approval",
    "native review end to end",
    "Code Mode cannot bypass approval",
    "no ~/.claude content visible",
    "interactive approval prompt shown in the TUI",
)


def run(argv, cwd=None, timeout=120):
    try:
        done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return done.returncode, done.stdout, done.stderr
    except (OSError, subprocess.TimeoutExpired) as error:
        return 127, "", str(error)


def check_version(runner=run, root=V2_ROOT):
    pinned = json.loads((root / "prefix/package.json").read_text())["dependencies"].get("@opencode/cli", "")
    code, out, _ = runner([str(root / "prefix/node_modules/.bin/opencode2"), "--version"])
    running = out.strip().split()[-1].lstrip("v") if code == 0 and out.strip() else None
    if not re.fullmatch(r"\d+\.\d+\.\d+", pinned):
        return "FAIL", "v2 version", f"the pin '{pinned}' is not an exact version (a caret or tilde lets it drift)"
    if running != pinned:
        return "FAIL", "v2 version", f"pinned {pinned} but the binary reports {running}"
    return "PASS", "v2 version", f"{pinned}, exact pin"


def check_services(runner=run):
    results = []
    for unit in UNITS:
        code, out, _ = runner(["systemctl", "--user", "is-active", unit])
        results.append(("PASS" if out.strip() == "active" else "FAIL", f"service {unit}", out.strip() or "unknown"))
    cold = [u for u in V1_UNITS if runner(["systemctl", "--user", "is-active", u])[1].strip() != "active"]
    results.append(("PASS" if not cold else "WARN", "V1 rollback path", "V1 units active" if not cold else "not active: " + ", ".join(cold)))
    return results


def check_config_in_sync(runner=run):
    code, out, err = runner([sys.executable, str(REPO / "scripts/derive-v2-config.py"), "--source", str(REPO / "global-config"),
                             "--sandbox-repo", str(SANDBOX), "--target", str(V2_ROOT / "config/opencode")])
    if code != 0:
        return "FAIL", "config in sync", (err or out).strip().splitlines()[-1][:160] if (err or out).strip() else f"derive exited {code}"
    pending = [line.split("would ", 1)[1] for line in out.splitlines() if "would " in line and "dry-run" not in line]
    if pending:
        return "WARN", "config in sync", f"{len(pending)} file(s) differ from global-config (run derive --apply): " + "; ".join(p.split("/")[-1] for p in pending[:4])
    return "PASS", "config in sync", "the V2 config root matches global-config"


def check_units_changeset(runner=run):
    code, out, _ = runner([sys.executable, str(REPO / "scripts/changeset.py"), "status", "--set", str(REPO / "changesets/opencode-v2-units"),
                           "--allow-root", str(HOME / ".config/systemd/user")])
    try:
        counts = json.loads(out).get("counts", {})
    except ValueError:
        return "FAIL", "unit files", "the change-set tool gave no report"
    if set(counts) == {"already_applied"}:
        return "PASS", "unit files", "the installed units match the change set"
    return "WARN", "unit files", "installed units differ from the change set: " + json.dumps(counts)


def check_registration_errors(runner=run, log=V2_ROOT / "data/opencode/log/opencode.log"):
    code, out, _ = runner(["systemctl", "--user", "show", "secure-opencode-v2.service", "-p", "ActiveEnterTimestamp", "--value"])
    try:
        since = datetime.strptime(out.strip(), "%a %Y-%m-%d %H:%M:%S %Z").replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        lines = log.read_text(errors="replace").splitlines()
    except (ValueError, OSError):
        return "WARN", "tool registration", "could not read the service start time or the V2 log"
    bad = [l for l in lines if "Skipping invalid" in l and re.search(r"timestamp=(\S{19})", l) and re.search(r"timestamp=(\S{19})", l).group(1) >= since]
    if bad:
        names = sorted({m.group(1) for l in bad for m in [re.search(r"name=(\S+)", l)] if m})
        return "FAIL", "tool registration", f"{len(bad)} rejected registration(s) since start: " + ", ".join(names[:6])
    return "PASS", "tool registration", "no rejected tool or plugin registrations since the service started"


def check_stack(runner=run):
    code, out, err = runner(["bun", "scripts/check-v2-stack.ts"], cwd=str(SANDBOX), timeout=300)
    failed = [l for l in out.splitlines() if l.startswith("FAIL")]
    if code == 0 and "All checks passed" in out:
        return "PASS", "stack check", f"{sum(1 for l in out.splitlines() if l.startswith('PASS'))} checks passed"
    return "FAIL", "stack check", "; ".join(failed[:3]) or (err.strip() or "exited " + str(code))[:160]


def check_repos(runner=run):
    results = []
    for name, path in (("workflow repo", REPO), ("sandbox repo", SANDBOX)):
        code, out, _ = runner(["git", "status", "--porcelain", "--branch"], cwd=str(path))
        if code != 0:
            results.append(("WARN", name, "not readable"))
            continue
        lines = out.splitlines()
        results.append(("INFO", name, f"{lines[0][3:].split('...')[0]}, {len(lines) - 1} uncommitted/untracked path(s); nothing pushed is not checked"))
    return results


def collect(runner=run, stack=False):
    results = [check_version(runner)]
    results += check_services(runner)
    results += [check_config_in_sync(runner), check_units_changeset(runner), check_registration_errors(runner)]
    if stack:
        results.append(check_stack(runner))
    results += check_repos(runner)
    results += [("MANUAL", "gate", gate) for gate in MANUAL_GATES]
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stack", action="store_true", help="also run the V2 stack check")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    results = collect(stack=args.stack)
    if args.json:
        print(json.dumps([{"status": s, "check": n, "detail": d} for s, n, d in results], indent=2))
    else:
        for status, name, detail in results:
            print(f"{status:6} {name}: {detail}")
        failed = sum(1 for s, _, _ in results if s == "FAIL")
        print(f"\n{failed} failing check(s)." if failed else "\nNo failing check. The MANUAL gates are still the owner's to run.")
    return 1 if any(s == "FAIL" for s, _, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
