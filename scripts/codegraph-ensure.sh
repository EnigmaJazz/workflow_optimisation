#!/usr/bin/env bash
# Idempotently create the CodeGraph index for a project checkout or worktree.
# Usage: codegraph-ensure.sh <dir>...
# Every worktree needs its own .codegraph/ (never copy or link another checkout's index).
# Skips $HOME, temporary directories and non-git directories. Safe to run repeatedly.
set -u

status=0
for dir in "$@"; do
  if ! root=$(cd "$dir" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null); then
    echo "codegraph-ensure: skip (not a git checkout): $dir" >&2
    continue
  fi
  root=$(cd "$root" && pwd -P)
  home=$(cd "$HOME" 2>/dev/null && pwd -P)
  case "$root" in
    "$home" | /tmp | /tmp/* | /var/tmp | /var/tmp/*)
      echo "codegraph-ensure: skip (home or temporary directory): $root" >&2
      continue
      ;;
  esac
  if [ -d "$root/.codegraph" ]; then
    echo "codegraph-ensure: present: $root"
    continue
  fi
  if gentle-ai codegraph init --cwd "$root" >&2 && [ -d "$root/.codegraph" ]; then
    echo "codegraph-ensure: initialised: $root"
  else
    echo "codegraph-ensure: FAILED: $root" >&2
    status=1
  fi
done
exit "$status"
