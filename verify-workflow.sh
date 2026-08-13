#!/usr/bin/env bash
# verify-workflow.sh — health check + self-heal for the global workflow setup.
# Run after updating opencode, Systematic, or gentle-ai:
#   bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh
# Re-verifies: RDD mode on, skill symlinks resolve to the active install,
# global AGENTS.md routing section present, skill registry current.
set -uo pipefail

WORKSPACE="/home/james/ai-workspace/workflow_optimisation"
SKILLS_DIR="/home/james/.config/opencode/skills"
PACKAGES_DIR="/home/james/.cache/opencode/packages/@fro.bot"
AGENTS_FILE="/home/james/.config/opencode/AGENTS.md"
ROUTING_MARKER="<!-- user:workflow-routing -->"
REQUIRED_SKILLS=("test-driven-development" "frontend-design" "reproduce-bug")
FAIL=0

echo "== Workflow setup health check =="

# --- 1. Receipt-driven review mode ---
echo "--- 1. Receipt-driven review ---"
MODE=$(gentle-ai review mode status --cwd "$WORKSPACE" 2>/dev/null | head -1)
echo "   $MODE"
if [[ "$MODE" != *"on"* ]]; then
  echo "   !! RDD is OFF — re-enable with: gentle-ai review mode enable --scope global"
  FAIL=1
fi

# --- 2. Resolve active Systematic install ---
echo "--- 2. Active Systematic install ---"
ACTIVE=""
# opencode.jsonc references @latest; prefer it when present, else the bare sibling
if [ -d "$PACKAGES_DIR/systematic@latest/node_modules/@fro.bot/systematic/skills" ]; then
  ACTIVE="$PACKAGES_DIR/systematic@latest/node_modules/@fro.bot/systematic/skills"
  echo "   active: @latest (matches opencode.jsonc)"
elif [ -d "$PACKAGES_DIR/systematic/node_modules/@fro.bot/systematic/skills" ]; then
  ACTIVE="$PACKAGES_DIR/systematic/node_modules/@fro.bot/systematic/skills"
  echo "   active: bare @fro.bot/systematic (no @latest dir found)"
else
  echo "   !! No Systematic skills install found under $PACKAGES_DIR"
  FAIL=1
fi

# --- 3. Skill symlinks ---
echo "--- 3. Skill symlinks ---"
if [ -n "$ACTIVE" ]; then
  for skill in "${REQUIRED_SKILLS[@]}"; do
    link="$SKILLS_DIR/$skill"
    expected="$ACTIVE/$skill"
    if [ -L "$link" ] && [ "$(readlink "$link")" = "$expected" ] && [ -f "$link/SKILL.md" ]; then
      echo "   ok: $skill -> $expected"
    else
      echo "   !! fixing: $skill (target: $expected)"
      ln -sfn "$expected" "$link"
      if [ -f "$link/SKILL.md" ]; then
        echo "      ok: $skill re-linked and resolves"
      else
        echo "      !! still broken after re-link"
        FAIL=1
      fi
    fi
  done
fi

# --- 4. Global AGENTS.md routing section ---
echo "--- 4. Global AGENTS.md routing section ---"
if [ -f "$AGENTS_FILE" ] && grep -q "$ROUTING_MARKER" "$AGENTS_FILE"; then
  echo "   ok: routing section present"
else
  echo "   !! routing section missing — re-appending"
  cat >> "$AGENTS_FILE" <<'EOF'

<!-- user:workflow-routing -->
## Task Routing: gentle-ai + Systematic division of labor (MANDATORY)

This routing recipe applies in **every repository** on this machine. It is user-owned; gentle-ai updates never remove it.

**Canonical recipe:** `/home/james/ai-workspace/workflow_optimisation/WORKFLOW.md` — read it before starting task work. It is the single source of truth for task classification and routing.

- Classify every incoming task by decision content, not file count: tiny fix, small feature, substantial feature, bug investigation, documentation, global tooling change.
- If classification is ambiguous, ask the user; default to **substantial**.
- Re-classification is allowed at any planning boundary with user confirmation.
- Every code change passes the receipt-driven review gate before delivery (RDD is enabled globally). Tiny fixes pass via silent structural readback; docs pass via human review with no code gate.
- Substantial features run the full pipeline: Systematic brainstorm (requirements) → SDD phases → RDD gate → Systematic compound learning loop. The Systematic thinking steps are REQUIRED, not optional: no SDD proposal without the brainstorm requirements artifact, no archive-close without the compound step. Small features require a Systematic plan before implementation; bug fixes require reproduce-bug + test-first discipline. Substantial and small features also run ce:review (advisory, pre-gate) before the RDD gate — it covers performance, API contract, migrations, repo standards, plan-requirements verification, and learnings that RDD does not provide; RDD remains the single enforced gate.
- After each routed task, log one row in `/home/james/ai-workspace/workflow_optimisation/ROUTER-LOG.md` (date, task, class, reclassification, gate outcome, probe flag, evidence).
- The runnable-router encoding decision (R12) triggers after ten consecutive routed tasks across at least four task classes without re-classification or gate escape, per the recipe.
<!-- /user:workflow-routing -->
EOF
  if grep -q "$ROUTING_MARKER" "$AGENTS_FILE"; then
    echo "   ok: routing section restored"
  else
    echo "   !! could not restore routing section"
    FAIL=1
  fi
fi

# --- 5. Skill registry ---
echo "--- 5. Skill registry ---"
if ! REGISTRY_OUTPUT=$(gentle-ai skill-registry refresh --cwd "$WORKSPACE" 2>&1); then
  FAIL=1
fi
echo "$REGISTRY_OUTPUT" | head -1

# --- 6. Global plugin mirror ---
echo "--- 6. Global plugin mirror ---"
PLUGIN_SOURCE="$WORKSPACE/global-config/plugins/workflow-health-check.ts"
PLUGIN_DEPLOYED="/home/james/.config/opencode/plugins/workflow-health-check.ts"
if [ -f "$PLUGIN_SOURCE" ]; then
  if [ -f "$PLUGIN_DEPLOYED" ] && cmp -s "$PLUGIN_SOURCE" "$PLUGIN_DEPLOYED"; then
    echo "   ok: workflow-health-check.ts mirror is current"
  else
    echo "   !! re-mirroring workflow-health-check.ts from reviewed source"
    cp "$PLUGIN_SOURCE" "$PLUGIN_DEPLOYED"
    if cmp -s "$PLUGIN_SOURCE" "$PLUGIN_DEPLOYED"; then
      echo "      ok: mirror restored (restart opencode to load the updated plugin)"
    else
      echo "      !! could not re-mirror plugin"
      FAIL=1
    fi
  fi
else
  echo "   !! plugin source missing from workspace — cannot verify mirror"
  FAIL=1
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "== All checks passed — workflow setup intact =="
else
  echo "== Some checks failed — see messages above =="
  exit 1
fi
