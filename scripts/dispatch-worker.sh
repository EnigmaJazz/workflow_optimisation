#!/usr/bin/env bash
# Start an Orca supervised worker after making sure its checkout has a CodeGraph index.
# Usage: dispatch-worker.sh <worktree-dir> <orca orchestration worker-start args...>
# The worktree selector is passed as path:<dir>; do not repeat --worktree in the args.
# For `--agent codex` with an inline --spec, roles/codex-commands.md (the command policy) is
# prepended to the spec so Codex plans around its approval list.
# OpenCode 2 dispatches are retained for reuse; every other settled worker is released with
# scripts/release-settled-workers.py (see roles/README.md "Session lifecycle").
set -eu
dir=${1:?usage: dispatch-worker.sh <worktree-dir> <worker-start args...>}
shift
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
"$here/codegraph-ensure.sh" "$dir" >/dev/null

# Record profile and terminal metadata while preserving the worker-start argument vector.
agent=""
terminal=""
run=""
is_codex=0
prev=""
for a in "$@"; do
  [ "$prev" = "--agent" ] && { agent=$a; [ "$a" = "codex" ] && is_codex=1; }
  [ "$prev" = "--terminal" ] && terminal=$a
  [ "$prev" = "--run" ] && run=$a
  prev=$a
done

# Preserve the Codex policy as an inline prefix on its --spec argument.
args=()
if [ "$is_codex" = 1 ]; then
  policy=$(cat "$here/../roles/codex-commands.md")
  prev=""
  for a in "$@"; do
    if [ "$prev" = "--spec" ]; then
      a="$policy"$'\n\n'"## Task"$'\n'"$a"
    fi
    args+=("$a")
    prev=$a
  done
else
  args=("$@")
fi

# Capture a worker-start failure without allowing set -e to replace its status.
if out=$(orca orchestration worker-start --worktree "path:$dir" "${args[@]}" --json); then
  :
else
  status=$?
  exit "$status"
fi
# Validate receipts uniformly and return a dispatch id, with distinct errors for each rejection.
if id=$(printf '%s' "$out" | python3 -c '
import json, sys
raw = sys.stdin.read()
def reject(code, reason):
    print("dispatch-worker: " + reason, file=sys.stderr)
    raise SystemExit(code)
if not raw.strip():
    reject(2, "empty dispatch receipt")
try:
    receipt = json.loads(raw)
except (TypeError, ValueError):
    reject(3, "unparseable dispatch receipt")

def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)

nodes = list(walk(receipt))
for node in nodes:
    status = node.get("status")
    if (node.get("success") is False or node.get("ok") is False
            or (isinstance(status, str) and status.lower() in {"error", "failed", "failure"})
            or bool(node.get("error"))):
        reject(4, "error receipt reported as successful")
dispatch_id = next((node.get("dispatchId") for node in nodes
                    if isinstance(node.get("dispatchId"), str)
                    and node["dispatchId"].startswith("ctx_")), None)
if dispatch_id is None:
    reject(5, "receipt has no valid dispatch id")
print(dispatch_id)
'); then
  :
else
  status=$?
  exit "$status"
fi

# Return the validated worker-start receipt before downstream metadata or retention work.
printf '%s\n' "$out"

retain_dispatch() {
  if ! orca orchestration worker-retain --dispatch "$id" --json >/dev/null; then
    printf 'dispatch-worker: warning: retention failed for dispatch %s\n' "$id" >&2
  fi
}

# Resolve reused terminal profiles from Orca rather than trusting the caller's agent claim.
if [ -n "$terminal" ]; then
  if terminal_list=$(orca terminal list --json); then
    profile=$(printf '%s' "$terminal_list" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except (TypeError, ValueError):
    raise SystemExit(0)
if not isinstance(data, dict) or data.get("ok") is not True or "error" in data or "errors" in data:
    raise SystemExit(0)
result = data.get("result")
terminals = result.get("terminals") if isinstance(result, dict) else None
if not isinstance(terminals, list):
    raise SystemExit(0)
handle = sys.argv[1]
rows = [entry for entry in terminals if isinstance(entry, dict) and entry.get("handle") == handle]
if len(rows) != 1:
    raise SystemExit(0)
identity = rows[0].get("agentIdentity")
if isinstance(identity, str) and identity and identity == "opencode2":
    print(identity)
' "$terminal")
  else
    profile=""
  fi
else
  profile=$agent
fi

# Retain fresh OpenCode 2 dispatches directly; reused terminals require ownership proof.
owned=0
if [ "$profile" = "opencode2" ] && [ -z "$terminal" ]; then
  retain_dispatch
elif [ "$profile" = "opencode2" ] && [ -n "$terminal" ]; then
  if worker_list=$(orca orchestration worker-list --json); then
    if printf '%s' "$worker_list" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except (TypeError, ValueError):
    raise SystemExit(1)
if not isinstance(data, dict) or data.get("ok") is not True or "error" in data or "errors" in data:
    raise SystemExit(1)
result = data.get("result")
workers = result.get("workers") if isinstance(result, dict) else None
if not isinstance(workers, list):
    raise SystemExit(1)
handle, dispatch_id, run_id = sys.argv[1:]
rows = [row for row in workers if isinstance(row, dict) and row.get("agentTerminalHandle") == handle]
if len(rows) != 1:
    raise SystemExit(1)
row = rows[0]
tied = row.get("dispatchId") == dispatch_id or (bool(run_id) and row.get("runId") == run_id)
resource = row.get("resource")
if not tied or not isinstance(resource, dict) or resource.get("ownershipState") != "owned":
    raise SystemExit(1)
' "$terminal" "$id" "$run"; then
      owned=1
    fi
  fi
  if [ "$owned" = 1 ]; then
    retain_dispatch
  else
    printf 'dispatch-worker: reused terminal %s: ownership unproven, dispatch not retained\n' "$terminal" >&2
  fi
fi
if [ -n "$terminal" ] && [ -z "$profile" ]; then
  printf 'dispatch-worker: reused terminal %s: profile unresolved, dispatch not retained\n' "$terminal" >&2
fi
# Report the validated dispatch id on stderr without changing the stdout receipt document.
printf 'dispatch-worker: dispatch %s\n' "$id" >&2
