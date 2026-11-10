#!/usr/bin/env bash
# Report-only: a gentle-ai sync restores ~/.claude/CLAUDE.md to upstream text, so the
# changesets/claude-* overlays must be re-applied afterwards. This never fails the run.
echo "--- 10b. Claude overlay drift (report-only) ---"
CLAUDE_OVERLAY_OUT=$(timeout 120s python3 "$WORKSPACE/scripts/claude-overlay-check.py" --root "$WORKSPACE" 2>&1)
CLAUDE_OVERLAY_STATUS=$?
case "$CLAUDE_OVERLAY_STATUS" in
  0) echo "   ok: every changesets/claude-* overlay is applied" ;;
  1) echo "   !! report-only: a Claude overlay set conflicts with the current bytes:"
     printf '%s\n' "$CLAUDE_OVERLAY_OUT" | sed 's/^/      /' ;;
  2) echo "   !! report-only: a gentle-ai sync restored upstream text; run: python3 scripts/claude-overlay-check.py --reapply"
     printf '%s\n' "$CLAUDE_OVERLAY_OUT" | sed 's/^/      /' ;;
  *) echo "   !! report-only: claude overlay check could not run (exit $CLAUDE_OVERLAY_STATUS)"
     printf '%s\n' "$CLAUDE_OVERLAY_OUT" | sed 's/^/      /' ;;
esac
