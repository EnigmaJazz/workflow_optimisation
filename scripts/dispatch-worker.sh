#!/usr/bin/env bash
# Start an Orca supervised worker after making sure its checkout has a CodeGraph index.
# Usage: dispatch-worker.sh <worktree-dir> <orca orchestration worker-start args...>
# The worktree selector is passed as path:<dir>; do not repeat --worktree in the args.
set -eu
dir=${1:?usage: dispatch-worker.sh <worktree-dir> <worker-start args...>}
shift
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
"$here/codegraph-ensure.sh" "$dir"
exec orca orchestration worker-start --worktree "path:$dir" "$@"
