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
"$here/codegraph-ensure.sh" "$dir"

is_codex=0
prev=""
for a in "$@"; do
  [ "$prev" = "--agent" ] && [ "$a" = "codex" ] && is_codex=1
  prev=$a
done

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
out=$(orca orchestration worker-start --worktree "path:$dir" "${args[@]}" --json)
printf '%s\n' "$out"
# OpenCode 2 sessions are reused (Magic Context builds project understanding): keep them out of
# release-settled-workers.py. Re-prompt one with `worker-start --terminal <handle> --spec ...`.
if printf '%s\n' "$*" | grep -q -- '--agent opencode2'; then
  id=$(printf '%s' "$out" | python3 -c 'import json,sys
def f(x):
    if isinstance(x,dict):
        if str(x.get("dispatchId","")).startswith("ctx_"): return x["dispatchId"]
        for v in x.values():
            r=f(v)
            if r: return r
    elif isinstance(x,list):
        for v in x:
            r=f(v)
            if r: return r
try: print(f(json.load(sys.stdin)) or "")
except ValueError: pass')
  [ -n "$id" ] && orca orchestration worker-retain --dispatch "$id" --json >/dev/null
fi
