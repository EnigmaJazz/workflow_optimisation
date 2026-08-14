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
- Frontend/UI tasks (design, layout, components, visual verification) route to the `frontend-dev` subagent: it owns design and verification, delegates implementation to `frontend-apply` (cheap tier + vision bridge for screenshots), and iterates between the two.
- Frontend lane ↔ SDD (hybrid): UI tasks INSIDE an SDD change ride the frontend lane — at `sdd-apply` launch, the orchestrator routes the UI task bundle to `frontend-dev` (its spec→apply→verify loop) and non-UI tasks to `sdd-apply`, merging results into apply-progress; `sdd-verify` still validates the whole change. Standalone UI requests (no SDD change) route directly to `frontend-dev`.
- If classification is ambiguous, ask the user; default to **substantial**.
- Re-classification is allowed at any planning boundary with user confirmation.
- Every code change passes the receipt-driven review gate before delivery (RDD is enabled globally). Tiny fixes pass via silent structural readback; docs pass via human review with no code gate.
- Substantial features run the full pipeline: Systematic brainstorm (requirements) → SDD phases → RDD gate → Systematic compound learning loop. The Systematic thinking steps are REQUIRED, not optional: no SDD proposal without the brainstorm requirements artifact, no archive-close without the compound step. Small features require a Systematic plan before implementation; bug fixes require reproduce-bug + test-first discipline. Small features and bug investigations execute through ce:work (structured execution: triage → task list → subagent strategy → test-as-you-go → incremental commits), then ce:review (advisory, pre-gate), then the RDD gate. Substantial and small features also run ce:review (advisory, pre-gate) before the RDD gate — it covers performance, API contract, migrations, repo standards, plan-requirements verification, and learnings that RDD does not provide; RDD remains the single enforced gate.
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

# --- 7. Recipe consistency ---
echo "--- 7. Recipe consistency ---"
WORKFLOW="$WORKSPACE/WORKFLOW.md"
REQS="$WORKSPACE/docs/brainstorms/2026-08-10-workflow-routing-requirements.md"

# 7a. All six task classes present in the recipe (case-insensitive: the recipe
# uses title-case class names but lowercase in some prose and the AGENTS heredoc)
MISSING_CLASS=""
for cls in "Tiny fix" "Small feature" "Substantial feature" "Bug investigation" "Documentation" "Global tooling change"; do
  if ! grep -qi -- "$cls" "$WORKFLOW"; then MISSING_CLASS="$MISSING_CLASS $cls"; fi
done
if [ -z "$MISSING_CLASS" ]; then
  echo "   ok: all six task classes present"
else
  echo "   !! missing task classes:$MISSING_CLASS"
  FAIL=1
fi

# 7b. Required-layer keywords present in the recipe
MISSING_KW=""
for kw in "ce:brainstorm" "ce:plan" "ce:work" "ce:review" "ce:compound" "RDD" "ROUTED:" "Required Thinking Layers"; do
  if ! grep -q -- "$kw" "$WORKFLOW"; then MISSING_KW="$MISSING_KW $kw"; fi
done
if [ -z "$MISSING_KW" ]; then
  echo "   ok: required-layer keywords present"
else
  echo "   !! missing keywords:$MISSING_KW"
  FAIL=1
fi

# 7c. Requirements doc R1-R14 present
MISSING_R=""
for r in 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do
  if ! grep -q -- "- R$r\." "$REQS"; then MISSING_R="$MISSING_R R$r"; fi
done
if [ -z "$MISSING_R" ]; then
  echo "   ok: requirements R1-R14 present"
else
  echo "   !! missing requirements:$MISSING_R"
  FAIL=1
fi

# 7d. AGENTS.md routing section in the repair heredoc matches the deployed section.
# Guard against the empty==empty false pass: require BOTH extractions to be
# non-empty before comparing, and fail loudly if either is empty.
HEREDOC_SECTION=$(awk '/# --- 4\. Global AGENTS\.md routing section/,/^EOF$/' "$WORKSPACE/verify-workflow.sh" | sed -n '/<!-- user:workflow-routing -->/,/<!-- \/user:workflow-routing -->/p')
DEPLOYED_SECTION=$(sed -n '/<!-- user:workflow-routing -->/,/<!-- \/user:workflow-routing -->/p' "$AGENTS_FILE")
if [ -z "$HEREDOC_SECTION" ] || [ -z "$DEPLOYED_SECTION" ]; then
  echo "   !! could not extract routing sections (heredoc or deployed empty) — extraction failure, not a match"
  FAIL=1
elif [ "$HEREDOC_SECTION" = "$DEPLOYED_SECTION" ]; then
  echo "   ok: AGENTS.md repair heredoc matches deployed routing section"
else
  echo "   !! AGENTS.md repair heredoc differs from deployed routing section"
  FAIL=1
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "== All checks passed — workflow setup intact =="
else
  echo "== Some checks failed — see messages above =="
  exit 1
fi
