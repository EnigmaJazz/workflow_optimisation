#!/usr/bin/env bash
# Install the multi-tier work into the live OpenCode V2 stack (owner runs this; agents do not).
#
# Order: preflight -> register the V2 worktree root -> install V2 plugin files and the nono profile ->
# derive and apply the V2 opencode.json from global-config/ -> validate the profile -> restart -> health check.
# Every step stops the script on failure. Each file the steps replace gets a timestamped .bak first.
#
# Usage:  bash scripts/install-multi-tier-v2.sh [--dry-run]     (default is --apply; --dry-run changes nothing)
set -euo pipefail

SANDBOX="${SANDBOX_REPO:-$HOME/agent-sandbox-integration}"          # the checkout the systemd units run from
WORKFLOW="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"          # the workflow_optimisation checkout holding global-config/
WT_ROOT="${V2_WORKTREE_PROJECT:-$HOME/ai-workspace/worktrees/workflow_optimisation}"
V2_CONFIG="$HOME/.local/share/opencode-v2/config/opencode"
MODE=apply
[[ "${1:-}" == "--dry-run" ]] && MODE=dry-run
say() { printf '\n== %s\n' "$*"; }

say "preflight"
# The broker and the V2 launcher run from $SANDBOX, so a restart only loads code that is committed there.
for sha in ${REQUIRED_SANDBOX_COMMITS:-bc2716a}; do
  git -C "$SANDBOX" merge-base --is-ancestor "$sha" HEAD \
    || { echo "STOP: $SANDBOX does not contain sandbox commit $sha. Merge it there first (a restart alone would not load it)."; exit 1; }
done
grep -q "Run independent implementation units in parallel" "$WORKFLOW/global-config/opencode.json" \
  || { echo "STOP: $WORKFLOW/global-config/opencode.json lacks the parallel-writers rule (wrong branch?)"; exit 1; }
[[ -z "$(git -C "$WORKFLOW" status --porcelain --untracked-files=no)" ]] \
  || { echo "STOP: $WORKFLOW has uncommitted tracked changes"; exit 1; }
echo "ok: $SANDBOX contains the required commits; $WORKFLOW is clean"

DRY=(); [[ $MODE == dry-run ]] && DRY=(--dry-run)

say "1. register the V2 worktree root ($WT_ROOT)"
(cd "$SANDBOX" && bun scripts/register-project.ts "${DRY[@]}" --worktree-root "$WT_ROOT")

say "2. install V2 plugins, libraries and the nono profile"
if [[ $MODE == apply ]]; then bash "$SANDBOX/scripts/install-user-files-v2" --apply; else bash "$SANDBOX/scripts/install-user-files-v2" --dry-run; fi

say "3. derive the V2 opencode.json from global-config/ and apply it"
if [[ $MODE == apply ]]; then
  python3 "$WORKFLOW/scripts/derive-v2-config.py" --source "$WORKFLOW/global-config" --sandbox-repo "$SANDBOX" --target "$V2_CONFIG" --apply
else
  python3 "$WORKFLOW/scripts/derive-v2-config.py" --source "$WORKFLOW/global-config" --sandbox-repo "$SANDBOX" --target "$V2_CONFIG"
fi

if [[ $MODE == dry-run ]]; then say "dry run complete: nothing was installed or restarted"; exit 0; fi

say "4. validate the installed V2 nono profile"
nono profile validate "$HOME/.config/nono/profiles/opencode-v2-secure.json"

say "5. restart the broker and the V2 stack"
systemctl --user daemon-reload
systemctl --user restart sandbox-broker.service secure-opencode-v2.service

say "6. health check"
(cd "$SANDBOX" && bun scripts/check-v2-stack.ts)
echo; echo "done. Start a NEW secure OpenCode V2 session; running sessions keep the old config."
