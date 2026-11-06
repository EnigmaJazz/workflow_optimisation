# --- 7. Recipe consistency ---
echo "--- 7. Recipe consistency ---"

# Q26 stable anchors. Every row is "<id>~<owning file>~<artifact>~<keystone>".
# Markers are unindented whole lines. Each anchor is validated ONLY in its
# owning file (never in the assembled routing contract): exactly one begin and
# one end line, begin before end, a non-empty interior after comment/heading/
# blank lines are removed, and a non-empty keystone literal inside the block. A
# block emptied behind intact markers, a duplicated/traversed pair, a blank
# keystone, or a marker that migrated to another artifact therefore fails.
# Assembled-contract searches cannot satisfy these checks.
#
# What the anchor layer verifies: block structure (exactly one ordered begin/end
# pair in the owning file), a non-empty interior, one non-empty keystone, and the
# ANCHOR_TOKENS table below for specific contractual literals.
# What it deliberately does NOT verify: headings, section titles and transitional
# prose. Heading retitles were the original brittleness (Q30), so those are
# intentionally not asserted here.
#
# ANCHOR_TOKENS classification rule — include a literal ONLY when it is
# contractual and machine-checkable: error codes, CLI verbs, tool names,
# protocol field names, exact caps/thresholds, version pins, sentinel strings,
# and invariant "never/must" sentences. Headings, section titles and
# transitional prose are NOT token-worthy; assert the owning block instead.
ANCHOR_FILES=(
  "$WORKFLOW"
  "$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md"
  "$ROUTER_SKILLS_SOURCE/workflow-route/SKILL.md"
  "$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md"
  "$ROUTER_SKILLS_SOURCE/workflow-systematic/references/specialists.md"
  "$AGENTS_SOURCE"
  "$ROUTING_CANONICAL"
)


anchor_block_body() {
  awk -v b="<!-- workflow:anchor $2:begin -->" -v e="<!-- workflow:anchor $2:end -->" '
    $0 == b { if (seen) dup = 1; seen = 1; want = 1; next }
    $0 == e { if (!want) bad = 1; else { closed = 1; want = 0 } next }
    want { print }
    END { if (!seen || !closed || dup || bad) exit 1 }
  ' "$1"
}

anchor_has() {
  local body
  body=$(anchor_block_body "$1" "$2") || return 2
  printf '%s\n' "$body" | grep -Fq -- "$3"
}

anchor_check_row() {
  local id="$1" file="$2" artifact="$3" keystone="$4"
  local begin_marker="<!-- workflow:anchor $id:begin -->"
  local end_marker="<!-- workflow:anchor $id:end -->"
  local begin_count end_count first last body substantive other
  if [ -z "$keystone" ]; then
    fail "ANCHOR_KEYSTONE_EMPTY: $artifact $id: keystone field is blank"
    return
  fi
  if [ ! -f "$file" ]; then
    fail "ANCHOR_MISSING: $artifact $id: owning file unreadable"
    return
  fi
  begin_count=$(grep -Fxc -- "$begin_marker" "$file" 2>/dev/null || true)
  end_count=$(grep -Fxc -- "$end_marker" "$file" 2>/dev/null || true)
  begin_count=${begin_count:-0}
  end_count=${end_count:-0}
  if [ "$begin_count" -eq 0 ] || [ "$end_count" -eq 0 ]; then
    for other in "${ANCHOR_FILES[@]}"; do
      [ "$other" = "$file" ] && continue
      if [ -f "$other" ] && grep -Fxq -- "$begin_marker" "$other" 2>/dev/null; then
        fail "ANCHOR_WRONG_FILE: $artifact $id: begin marker found in $other, not in its owning file"
        return
      fi
    done
    fail "ANCHOR_MISSING: $artifact $id: owning file has begin=$begin_count end=$end_count"
    return
  fi
  if [ "$begin_count" -gt 1 ] || [ "$end_count" -gt 1 ]; then
    fail "ANCHOR_DUPLICATE: $artifact $id: owning file has begin=$begin_count end=$end_count"
    return
  fi
  first=$(grep -Fxn -- "$begin_marker" "$file" 2>/dev/null | head -n1 | cut -d: -f1)
  last=$(grep -Fxn -- "$end_marker" "$file" 2>/dev/null | head -n1 | cut -d: -f1)
  if [ -z "$first" ] || [ -z "$last" ] || [ "$first" -ge "$last" ]; then
    fail "ANCHOR_UNORDERED: $artifact $id: begin line $first is not before end line $last"
    return
  fi
  if ! body=$(anchor_block_body "$file" "$id"); then
    fail "ANCHOR_UNORDERED: $artifact $id: marker pair could not be extracted from the owning file"
    return
  fi
  substantive=$(printf '%s\n' "$body" | awk '
    /^[[:space:]]*$/ { next }
    /^[[:space:]]*#/ { next }
    /^[[:space:]]*<!--/ { next }
    { count++ }
    END { print count + 0 }
  ')
  if [ "${substantive:-0}" -eq 0 ]; then
    fail "ANCHOR_EMPTY: $artifact $id: interior empty after comments, headings and whitespace"
    return
  fi
  if ! printf '%s\n' "$body" | grep -Fq -- "$keystone" 2>/dev/null; then
    fail "ANCHOR_KEYSTONE_MISSING: $artifact $id: keystone literal absent from block interior"
  fi
}

ANCHOR_MANIFEST=(
  "workflow.project-registration~$WORKFLOW~WORKFLOW.md~host_register_project"
  "workflow.technical-lead~$WORKFLOW~WORKFLOW.md~gentle-orchestrator"
  "workflow.odd-delegation~$WORKFLOW~WORKFLOW.md~odd/tasks/<feature-name>.md"
  "workflow.odd-protocol~$WORKFLOW~WORKFLOW.md~ODD_TASKS key=odd/{project}/{feature-name}/tasks"
  "workflow.route-decision~$WORKFLOW~WORKFLOW.md~basis: WORKFLOW.md"
  "workflow.work-unit-review~$WORKFLOW~WORKFLOW.md~authored_changed_lines"
  "workflow.skill-routing-search~$WORKFLOW~WORKFLOW.md~EXTERNAL_CONTEXT_REQUIRED"
  "workflow.execution-boundary~$WORKFLOW~WORKFLOW.md~gentle-ai-verify"
  "workflow.context-backend~$WORKFLOW~WORKFLOW.md~document-review"
  "workflow.review-relay~$WORKFLOW~WORKFLOW.md~asi-review-*"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~review.acknowledge-approved"
  "workflow.frontend-lane~$WORKFLOW~WORKFLOW.md~subagent_depth: 3"
  "workflow.execution-skills~$WORKFLOW~WORKFLOW.md~test-driven-development"
  "workflow.astra-escalation~$WORKFLOW~WORKFLOW.md~astra-sol-upgrade.ts"
  "workflow.session-defaults~$WORKFLOW~WORKFLOW.md~ctx_reduce"
  "workflow.prove-out~$WORKFLOW~WORKFLOW.md~R12"
  "workflow.odd-and-review.odd-delegation~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~route: delegated"
  "workflow.odd-and-review.odd-protocol~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~ODD_TASKS key=odd/{project}/{feature-name}/tasks"
  "workflow.odd-and-review.work-unit-review~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~authored_changed_lines"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~lens_context_budget_exceeded"
  "workflow.odd-and-review.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~GENTLE_AI_REVIEW_CONTEXT"
  "workflow.route-skill.route-statement~$ROUTER_SKILLS_SOURCE/workflow-route/SKILL.md~global-config/skills/workflow-route/SKILL.md~workflow-odd-secure"
  "workflow.session-decisions.shell~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~Fish shell"
  "workflow.session-decisions.coding-model~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~gentle-ai-worker-local"
  "workflow.session-decisions.astra~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~openai/gpt-6.1-sol"
  "workflow.session-decisions.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~GENTLE_AI_REVIEW_CONTEXT"
  "workflow.session-decisions.reviewability-budget~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~authored_patch_bytes"
  "workflow.session-decisions.upstream-lifecycle~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~last_synced_at"
  "workflow.session-decisions.project-registration~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~BROKER_PROJECTS"
  "workflow.session-decisions.technical-lead~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~gentle-orchestrator"
  "workflow.specialists.routing-precedence~$ROUTER_SKILLS_SOURCE/workflow-systematic/references/specialists.md~global-config/skills/workflow-systematic/references/specialists.md~systematic-implementer"
  "workflow.specialists.sandbox-mutation~$ROUTER_SKILLS_SOURCE/workflow-systematic/references/specialists.md~global-config/skills/workflow-systematic/references/specialists.md~sandbox_apply_patch"
  "workflow.agents.secure-router~$AGENTS_SOURCE~global-config/AGENTS.md~skill({name:\"workflow-route\"})"
  "workflow.tiny-fix~$WORKFLOW~WORKFLOW.md~Tiny fix selects one delegated"
  "workflow.tiny-fix-tripwire~$ROUTING_GUARD_SOURCE~systematic-routing-guard.ts~TINY_FIX_MAX_AUTHORED_CHANGED_LINES"
  "workflow.tiny-fix-odd-route~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/SKILL.md~workflow-odd-secure tiny-fix route~Tiny-fix route:"
  "workflow.tiny-fix-systematic-route~$ROUTER_SKILLS_SOURCE/workflow-systematic/SKILL.md~workflow-systematic tiny-fix route~Tiny-fix route:"
  "workflow.tiny-fix-overlay~$WORKSPACE/global-config/prompts/gentle-orchestrator/overlay.md~orchestrator inline boundary~Upstream's “small tasks stay inline” wording is NOT adopted"
  "workflow.pm-brief-readback~$WORKSPACE/global-config/prompts/gentle-orchestrator/overlay.md~PM brief tracker/mirror hashes~tracker_sha256"
)
ANCHOR_FAIL_BEFORE=${#FAIL_MESSAGES[@]}
for anchor_row in "${ANCHOR_MANIFEST[@]}"; do
  IFS='~' read -r anchor_id anchor_file anchor_label anchor_key <<< "$anchor_row"
  anchor_check_row "$anchor_id" "$anchor_file" "$anchor_label" "$anchor_key"
done
if [ "${#FAIL_MESSAGES[@]}" -eq "$ANCHOR_FAIL_BEFORE" ]; then
  echo "   ok: ${#ANCHOR_MANIFEST[@]} stable anchor blocks validated in their owning files"
fi

# Q26 contractual anchor tokens — the ONE literal-checking mechanism. Every row
# is "<anchor id>~<owning file>~<label>~<literal>" with the literal LAST so a
# literal containing '~', '|', '→', backticks, quotes or spaces still parses.
# Each row extracts its anchor interior and fails ANCHOR_TOKEN_MISSING when the
# literal is absent. This replaces the former per-chain anchor_has calls so no
# mixed literal-checking scheme remains. See the classification rule above.
ANCHOR_TOKENS=(
  # WORKFLOW.md
  "workflow.tiny-fix~$WORKFLOW~WORKFLOW.md~Tiny fix selects one delegated writer per the dispatcher-specific selection in the Task Classes row"
  "workflow.tiny-fix~$WORKFLOW~WORKFLOW.md~The one-way tripwire remains an escalation-only pre-install guard"
  "workflow.tiny-fix-tripwire~$ROUTING_GUARD_SOURCE~systematic-routing-guard.ts~TINY_FIX_MAX_AUTHORED_CHANGED_LINES"
  "workflow.route-skill.route-statement~$ROUTER_SKILLS_SOURCE/workflow-route/SKILL.md~workflow-route tiny-fix route~Tiny-fix route:"
  "workflow.tiny-fix-odd-route~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/SKILL.md~workflow-odd-secure tiny-fix route~openai/gpt-6-luna"
  "workflow.tiny-fix-systematic-route~$ROUTER_SKILLS_SOURCE/workflow-systematic/SKILL.md~workflow-systematic tiny-fix route~openai/gpt-6-luna"
  "workflow.tiny-fix-overlay~$WORKSPACE/global-config/prompts/gentle-orchestrator/overlay.md~orchestrator inline boundary~Upstream's “small tasks stay inline” wording is NOT adopted"
  "workflow.work-unit-review~$WORKFLOW~WORKFLOW.md~\`authored_changed_lines\`"
  "workflow.pm-brief-readback~$WORKSPACE/global-config/prompts/gentle-orchestrator/overlay.md~PM brief tracker hash field~tracker_sha256"
  "workflow.pm-brief-readback~$WORKSPACE/global-config/prompts/gentle-orchestrator/overlay.md~PM brief optional mirror hash~\`mirror_sha256\` is optional and must be absent"
  "workflow.work-unit-review~$WORKFLOW~WORKFLOW.md~\`authored_patch_bytes\`"
  "workflow.work-unit-review~$WORKFLOW~WORKFLOW.md~\`generated_or_binary_paths\`"
  "workflow.work-unit-review~$WORKFLOW~WORKFLOW.md~400 authored changed lines and 100 KiB"
  "workflow.work-unit-review~$WORKFLOW~WORKFLOW.md~200 KiB serialized per-runtime review-input budget"
  "workflow.work-unit-review~$WORKFLOW~WORKFLOW.md~\`review-size-exception\`"
  "workflow.work-unit-review~$WORKFLOW~WORKFLOW.md~Close the open medium-risk slice before the next high-risk commit."
  "workflow.work-unit-review~$WORKFLOW~WORKFLOW.md~Do not leave the evidence update uncommitted"
  "workflow.project-registration~$WORKFLOW~WORKFLOW.md~host_register_project"
  "workflow.project-registration~$WORKFLOW~WORKFLOW.md~Fish shell"
  "workflow.odd-delegation~$WORKFLOW~WORKFLOW.md~two or more non-trivial files"
  "workflow.odd-delegation~$WORKFLOW~WORKFLOW.md~more than about 5 sequential lookups"
  "workflow.odd-protocol~$WORKFLOW~WORKFLOW.md~route/trigger evidence"
  "workflow.odd-protocol~$WORKFLOW~WORKFLOW.md~ODD_TASKS key=odd/{project}/{feature-name}/tasks"
  "workflow.frontend-lane~$WORKFLOW~WORKFLOW.md~frontend-dev-premium"
  "workflow.frontend-lane~$WORKFLOW~WORKFLOW.md~Model assignments are authoritative"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~gentle-ai review assess --json"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~gentle-ai review mode enable|disable|status"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~Risk, Resilience, Readability, Reliability"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~status/v8"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~candidate.consumed"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~review_due_reason"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~next_transition.command"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~provider_task.agent"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~provider_task.prompt"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~\`review-<lens>\` → \`asi-review-<lens>\`"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~TRANSPORT-LANE FAILURE"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~eligible_untracked_inventory"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~review.acknowledge-approved"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~\`lens_context_budget_exceeded\`"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~\`correction_context_budget_exceeded\`"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~\`review capture-result --input\`, \`review recover\`"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~Forward the provider-issued task line verbatim"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~two transports cannot own one Task"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~Never grant review lanes to implementation workers or isolated reviewers"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~reviewer's raw JSON object"
  "workflow.native-rdd~$WORKFLOW~WORKFLOW.md~grouped wave without waiting between launches"
  "workflow.review-relay~$WORKFLOW~WORKFLOW.md~two transports cannot own one Task"
  "workflow.review-relay~$WORKFLOW~WORKFLOW.md~provider-issued task line verbatim"
  "workflow.execution-skills~$WORKFLOW~WORKFLOW.md~Systematic v3.18.4+"
  "workflow.execution-skills~$WORKFLOW~WORKFLOW.md~workflow-guard result is authoritative"
  "workflow.execution-boundary~$WORKFLOW~WORKFLOW.md~The orchestrator must not dispatch a writer that shares its own model family."
  "workflow.tiny-fix-odd-route~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/SKILL.md~workflow-odd-secure tiny-fix route~Temporary writer deviation (owner decision, 2026-10-17)"
  "workflow.execution-boundary~$WORKFLOW~WORKFLOW.md~CLOUD or LOCAL tier"
  "workflow.execution-boundary~$WORKFLOW~WORKFLOW.md~provided its model family differs from the orchestrator's"
  "workflow.execution-boundary~$WORKFLOW~WORKFLOW.md~An unrecognized model family is NOT proven independent"
  "workflow.astra-escalation~$WORKFLOW~WORKFLOW.md~astra-sol-upgrade.ts"
  "workflow.astra-escalation~$WORKFLOW~WORKFLOW.md~selection never edits global config or requires an OpenCode restart"
  # global-config/skills/workflow-odd-secure/references/odd-and-review.md
  "workflow.odd-and-review.odd-delegation~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~two or more non-trivial files"
  "workflow.odd-and-review.odd-delegation~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~more than about 5 sequential lookups"
  "workflow.odd-and-review.odd-protocol~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~route/trigger evidence"
  "workflow.odd-and-review.odd-protocol~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~ODD_TASKS key=odd/{project}/{feature-name}/tasks"
  "workflow.odd-and-review.odd-protocol~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~The orchestrator must not dispatch a writer that shares its own model family."
  "workflow.odd-and-review.odd-protocol~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~CLOUD or LOCAL tier"
  "workflow.odd-and-review.odd-protocol~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~provided its model family differs from the orchestrator's"
  "workflow.odd-and-review.odd-protocol~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~An unrecognized model family is NOT proven independent"
  "workflow.odd-and-review.work-unit-review~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~400 authored changed lines and 100 KiB"
  "workflow.odd-and-review.work-unit-review~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~Close the pending medium-risk slice before the next high-risk commit."
  "workflow.odd-and-review.work-unit-review~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~200 KiB serialized per-runtime review-input budget"
  "workflow.odd-and-review.work-unit-review~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~--base-ref <last reviewed boundary> --committed-only --json"
  "workflow.odd-and-review.work-unit-review~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~candidate.consumed"
  "workflow.odd-and-review.work-unit-review~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~review_due_reason"
  "workflow.odd-and-review.work-unit-review~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~next_transition.command"
  "workflow.odd-and-review.work-unit-review~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~Do not leave the evidence update uncommitted"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~gentle-ai review assess --json"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~gentle-ai review mode enable|disable|status"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~status/v8"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~provider_task.agent"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~provider_task.prompt"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~correction_context_budget_exceeded"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~eligible_untracked_inventory"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~reviewer's raw JSON object"
  "workflow.odd-and-review.native-rdd~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~grouped wave without waiting between launches"
  "workflow.odd-and-review.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~Risk, Resilience, Readability, Reliability"
  "workflow.odd-and-review.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~TRANSPORT-LANE FAILURE"
  "workflow.odd-and-review.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~review.acknowledge-approved"
  "workflow.odd-and-review.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~Forward the provider-issued task line verbatim"
  "workflow.odd-and-review.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~two transports cannot own one Task"
  "workflow.odd-and-review.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~Never grant review lanes to implementation workers or isolated reviewers"
  "workflow.odd-and-review.odd-protocol~$ROUTER_SKILLS_SOURCE/workflow-odd-secure/references/odd-and-review.md~global-config/skills/workflow-odd-secure/references/odd-and-review.md~executable-file class: a script/executable extension or content opening with a shebang"
  # global-config/skills/workflow-route/references/session-decisions.md
  "workflow.session-decisions.astra~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~Use Astra upgrade (Recommended)"
  "workflow.session-decisions.astra~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~Astra is never an implementation agent"
  "workflow.session-decisions.shell~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~Fish shell"
  "workflow.session-decisions.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~Forward the provider-issued task line verbatim"
  "workflow.session-decisions.4r-lanes~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~never grant review lanes to implementation workers or isolated reviewers"
  "workflow.session-decisions.reviewability-budget~$ROUTER_SKILLS_SOURCE/workflow-route/references/session-decisions.md~global-config/skills/workflow-route/references/session-decisions.md~Close the accumulated medium-risk slice before the next high-risk commit."
  # global-config/skills/workflow-route/SKILL.md
  "workflow.route-skill.route-statement~$ROUTER_SKILLS_SOURCE/workflow-route/SKILL.md~global-config/skills/workflow-route/SKILL.md~basis: WORKFLOW.md"
  # global-config/AGENTS.md — checked against the reviewed SOURCE, never the deployed copy
  "workflow.agents.secure-router~$AGENTS_SOURCE~global-config/AGENTS.md~final 200 KiB serialized-input authority"
  "workflow.agents.secure-router~$AGENTS_SOURCE~global-config/AGENTS.md~skill({name:\"workflow-route\"})"
  "workflow.agents.secure-router~$AGENTS_SOURCE~global-config/AGENTS.md~route/trigger evidence"
)
ANCHOR_TOKEN_FAIL_BEFORE=${#FAIL_MESSAGES[@]}
for token_row in "${ANCHOR_TOKENS[@]}"; do
  IFS='~' read -r token_anchor token_file token_label token_literal <<< "$token_row"
  if [ -z "$token_anchor" ] || [ -z "$token_file" ] || [ -z "$token_literal" ]; then
    fail "ANCHOR_TOKEN_EMPTY: $token_label $token_anchor: token row has a blank anchor, file or literal field"
    continue
  fi
  if ! anchor_has "$token_file" "$token_anchor" "$token_literal"; then
    fail "ANCHOR_TOKEN_MISSING: $token_anchor $token_file $token_literal"
  fi
done
if [ "${#FAIL_MESSAGES[@]}" -eq "$ANCHOR_TOKEN_FAIL_BEFORE" ]; then
  echo "   ok: ${#ANCHOR_TOKENS[@]} contractual anchor tokens present in their owning blocks"
fi

if [ ! -f "$WORKFLOW" ]; then
  fail "WORKFLOW.md missing: $WORKFLOW"
else
  MISSING_CLASS=""
  for cls in "Tiny fix" "Small feature" "Substantial feature" "Bug investigation" "Documentation" "Global tooling change"; do
    if ! grep -qi -- "$cls" "$WORKFLOW"; then MISSING_CLASS="$MISSING_CLASS $cls"; fi
  done
  if [ -z "$MISSING_CLASS" ]; then
    echo "   ok: all six task classes present"
  else
    fail "missing task classes:$MISSING_CLASS"
  fi

  MISSING_KW=""
  for kw in "ce:brainstorm" "ce:plan" "ce:work" "ce:review" "ce:compound" "RDD" "ROUTED:" "Required Thinking Layers" "## Substantial ODD work units and review" "## Route decision checkpoint" "basis: WORKFLOW.md"; do
    if ! grep -q -- "$kw" "$WORKFLOW"; then MISSING_KW="$MISSING_KW $kw"; fi
  done
  if [ -z "$MISSING_KW" ]; then
    echo "   ok: required-layer keywords present"
  else
    fail "missing keywords:$MISSING_KW"
  fi

  # Q26: the review-budget literals are contractual tokens in the ANCHOR_TOKENS
  # table above; they are checked once each, inside their owning blocks.

  # Q26: this chain's positive coverage is now contractual tokens in the
  # ANCHOR_TOKENS table above; only the negative absence guard remains here.
  if ! grep -q -- "frontend-dev.*=.*openai/gpt-6.1-sol" "$WORKFLOW" 2>/dev/null; then
    echo "   ok: no frontend-dev premium model is hard-coded in the recipe"
  else
    fail "workflow hard-codes a frontend-dev premium model instead of deferring to opencode.json"
  fi

  if grep -q -- "Direct inline edit" "$WORKFLOW" 2>/dev/null || \
     grep -q -- "Inline implementation is" "$WORKFLOW" 2>/dev/null; then
    fail "workflow still contains obsolete inline-mutation guidance"
  else
    echo "   ok: workflow contains no obsolete direct-inline mutation route"
  fi

  if grep -R -Fq -- 'copy `provider_task.agent` unchanged as `subagent_type`' "$WORKFLOW" "$ROUTER_SKILLS_SOURCE" 2>/dev/null || \
     grep -R -Fq -- 'must never substitute for a v8 `provider_task.agent`' "$WORKFLOW" "$ROUTER_SKILLS_SOURCE" 2>/dev/null; then
    fail "GENTLE_AI_V3_4_DIRECT_PROVIDER_REVIEW_ROUTE_REAPPEARED: v8 tasks must map to asi-review-*"
  else
    echo "   ok: v8 provider review names map only to isolated asi-review relay lanes"
  fi
fi

# Gentle AI 3.4 retired RTK from its active product surface. User-owned RTK
# binaries/configuration may remain on disk, but this reviewed workflow must not
# restore an RTK integration, preset selection, or routing instruction.
if grep -R -Iiwq -- 'RTK' "$WORKFLOW" "$AGENTS_SOURCE" "$OPENCODE_CONFIG_SOURCE" "$SKILLS_DIR" 2>/dev/null; then
  fail "GENTLE_AI_V3_4_RETIRED_RTK_INTEGRATION_PRESENT: remove RTK from reviewed workflow/config sources; do not delete user-owned binaries"
else
  echo "   ok: no retired Gentle AI RTK integration in reviewed workflow sources"
fi

if [ ! -f "$REQS" ]; then
  fail "requirements document missing: $REQS"
else
  MISSING_R=""
  for r in 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do
    if ! grep -q -- "- R$r\." "$REQS"; then MISSING_R="$MISSING_R R$r"; fi
  done
  if [ -z "$MISSING_R" ]; then
    echo "   ok: requirements R1-R14 present"
  else
    fail "missing requirements:$MISSING_R"
  fi
fi

# Canonical AGENTS section must exactly equal the verifier-owned repair block.
if python3 - "$AGENTS_FILE" "$ROUTING_CANONICAL" <<'PY_COMPARE'
from pathlib import Path
import sys

agents = Path(sys.argv[1]).read_text(encoding="utf-8") if Path(sys.argv[1]).exists() else ""
canonical = Path(sys.argv[2]).read_text(encoding="utf-8").rstrip("\n")
start = "<!-- user:workflow-routing -->"
end = "<!-- /user:workflow-routing -->"

if agents.count(start) != 1 or agents.count(end) != 1:
    raise SystemExit(1)
a = agents.index(start)
b = agents.index(end, a) + len(end)
raise SystemExit(0 if agents[a:b] == canonical else 1)
PY_COMPARE
then
  echo "   ok: AGENTS.md routing section matches canonical verifier copy"
else
  fail "AGENTS.md routing section differs from canonical verifier copy"
fi

# The reviewed non-routing sections must also be exact and marker-safe.
if python3 - "$AGENTS_FILE" "$AGENTS_SOURCE" <<'PY_COMPARE_BOUNDED'
from pathlib import Path
import sys
active = Path(sys.argv[1]).read_text(encoding="utf-8")
source = Path(sys.argv[2]).read_text(encoding="utf-8")
for start,end in (
    ("<!-- gentle-ai:codegraph-guidance -->", "<!-- /gentle-ai:codegraph-guidance -->"),
    ("<!-- gentle-ai:subagent-cancellation -->", "<!-- /gentle-ai:subagent-cancellation -->"),
    ("<!-- user:grep-tool-enforcement -->", "<!-- /user:grep-tool-enforcement -->"),
):
    if any(blob.count(start) != 1 or blob.count(end) != 1 for blob in (active, source)):
        raise SystemExit(1)
    def body(blob):
        a = blob.index(start)
        b = blob.index(end, a) + len(end)
        return blob[a:b]
    if body(active) != body(source):
        raise SystemExit(1)
PY_COMPARE_BOUNDED
then
  echo "   ok: CodeGraph, cancellation and search-tool blocks match reviewed source"
else
  fail "AGENTS_BOUNDED_BLOCK_DRIFT: reviewed CodeGraph, cancellation or search-tool block differs from active AGENTS.md"
fi

# Q26: these two blocks are byte-compared by PY_COMPARE_BOUNDED, so read the
# reviewed source directly instead of the deployed copy's redundant content.
if grep -Fq -- 'prefer narrow read-only tools (ENFORCED)' "$AGENTS_SOURCE" 2>/dev/null && \
   grep -Fq -- 'built-in `grep` remains `ask`-gated' "$AGENTS_SOURCE" 2>/dev/null && \
   grep -Fq -- 'SEARCH CONTRACT: AFT=navigation' "$SKILLS_DIR/workflow-route/SKILL.md" 2>/dev/null && \
   grep -Fq -- 'all subagents have it disabled' "$WORKFLOW" 2>/dev/null && \
   grep -Fq -- 'EXTERNAL_CONTEXT_REQUIRED' "$WORKFLOW" 2>/dev/null; then
  echo "   ok: narrow search tools prioritized and grep approval preserved"
else
  fail "SEARCH_TOOL_ROUTING_DRIFT: reviewed search-tool order or grep ask boundary missing"
fi

if grep -Fq -- '.atl/rate-limit-fallback.log' "$AGENTS_SOURCE" 2>/dev/null && \
   ! grep -Fq -- '.git/gentle-ai/rate-limit-fallback.log' "$AGENTS_SOURCE" 2>/dev/null && \
   grep -Fq -- 'never substitute the shared OpenCode server cwd' "$AGENTS_SOURCE" 2>/dev/null && \
   grep -Fq -- 'separate from the workflow decision ledger `ROUTER-LOG.md`' "$AGENTS_SOURCE" 2>/dev/null; then
  echo "   ok: fallback reconciliation uses the exact session repo .atl mirror"
else
  fail "FALLBACK_REPO_LOG_ROUTING_DRIFT: canonical .atl mirror or fail-closed session routing missing"
fi

# The compact AGENTS entrypoint is checked against the canonical block
# above. The procedure it loads is checked in the reviewed skill files below.
if cat "$AGENTS_FILE" \
    "$SKILLS_DIR/workflow-route/SKILL.md" \
    "$SKILLS_DIR/workflow-route/references/session-decisions.md" \
    "$SKILLS_DIR/workflow-odd-secure/SKILL.md" \
    "$SKILLS_DIR/workflow-odd-secure/references/odd-and-review.md" \
    "$SKILLS_DIR/workflow-systematic/SKILL.md" \
    "$SKILLS_DIR/workflow-systematic/references/specialists.md" > "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: secure routing contract assembled from recovered skills"
else
  fail "ROUTER_SKILL_CONTRACT_UNAVAILABLE: recovered skill files cannot be read"
  : > "$ROUTING_CONTRACT"
fi

if grep -q -- "Systematic specialist routing precedence" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- 'systematic-implementer' "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: Systematic specialist routing precedence present"
else
  fail "Systematic specialist routing precedence missing"
fi

if grep -q -- "Independent sub-agent fan-out" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "same assistant message" "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: independent sub-agent fan-out contract present"
else
  fail "independent sub-agent fan-out contract missing"
fi

if grep -q -- "Prompt-free read-only inspection" "$ROUTING_CONTRACT" 2>/dev/null && \
   grep -q -- "sandbox_bash.*ask-gated" "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   ok: prompt-free read-only inspection routing contract present"
else
  fail "prompt-free read-only inspection routing contract missing"
fi

# Gentle AI v3 renders its native ODD guidance with a specific heading, but
# sync does not guarantee that that prose appears in this global AGENTS.md.
# Our reviewed user-owned block is the effective secure adapter: it delegates
# project writes and mirrors ODD to Magic Context instead of Engram. The block's
# structure and its route keystones are validated by the anchor manifest and the
# ANCHOR_TOKENS table above, so only the upstream-prose diagnostic remains here.
if ! grep -Fq -- 'ODD protocol (MANDATORY, in this order, on every request)' "$ROUTING_CONTRACT" 2>/dev/null; then
  echo "   info: upstream managed ODD prose absent from global AGENTS.md; secure user-owned v3 route is effective"
fi

# Q26: the assembled-contract literals are contractual tokens in the
# ANCHOR_TOKENS table above, checked once against their reviewed source blocks.

if grep -q -- "<!-- gentle-ai:engram-protocol -->" "$AGENTS_FILE" 2>/dev/null; then
  fail "LEGACY_ENGRAM_PROTOCOL_REAPPEARED: user workflow uses mandatory Magic Context instead"
else
  echo "   ok: no legacy mandatory Engram protocol block"
fi

