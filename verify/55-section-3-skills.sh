# --- 3. Systematic bundled skills / obsolete symlinks ---
echo "--- 3. Systematic bundled skills ---"
if [ -n "$ACTIVE_SKILLS" ]; then
  for skill in "${REQUIRED_SKILLS[@]}"; do
    bundled="$ACTIVE_SKILLS/$skill/SKILL.md"
    if [ -f "$bundled" ]; then
      echo "   ok: $skill bundled by active Systematic install"
    else
      fail "required Systematic skill missing: $skill (expected $bundled)"
    fi
  done

  for required_pipeline in "$ACTIVE_SKILLS/ce-review/scripts/validate-review.mjs" "$ACTIVE_SKILLS/ce-review/references/pipeline-invocation.md" "$ACTIVE_SKILLS/ce-review-cleanup/scripts/cleanup.mjs"; do
    if [ ! -f "$required_pipeline" ]; then fail "SYSTEMATIC_REVIEW_PIPELINE_MISSING: $required_pipeline"; fi
  done

  # Systematic now registers its bundled skills directly. Old symlinks under
  # ~/.config/opencode/skills only make OpenCode discover the same skill twice.
  REMOVED_LINKS=0
  if [ -d "$SKILLS_DIR" ]; then
    while IFS= read -r -d '' link; do
      raw_target=$(readlink "$link" 2>/dev/null || true)
      resolved_target=$(readlink -f "$link" 2>/dev/null || true)
      if [[ "$raw_target" == *"/@fro.bot/systematic/"* ]] || \
         [[ "$resolved_target" == *"/@fro.bot/systematic/"* ]]; then
        repair_note "removing obsolete Systematic skill symlink: $link -> $raw_target"
        if rm -- "$link"; then
          REMOVED_LINKS=$((REMOVED_LINKS + 1))
        else
          fail "could not remove obsolete Systematic skill symlink: $link"
        fi
      fi
    done < <(find "$SKILLS_DIR" -mindepth 1 -maxdepth 1 -type l -print0 2>/dev/null)
  fi

  if [ "$REMOVED_LINKS" -eq 0 ]; then
    echo "   ok: no redundant Systematic skill symlinks"
  else
    echo "   ok: removed $REMOVED_LINKS redundant Systematic skill symlink(s)"
  fi
fi

# gentle-ai v4 retired the secure SDD route. Detect-only: a stale deployed copy
# is a hard failure because the owner removes it once (no auto-delete here). The
# reviewed recovery manifest never lists these names, so this fixed list is the
# only detection surface. Do not derive it from the manifest.
retiredWorkflowSkills=("workflow-sdd-secure")
retiredWorkflowSkillsFound=0
for retired_skill in "${retiredWorkflowSkills[@]}"; do
  if [ -d "$SKILLS_DIR/$retired_skill" ]; then
    fail "RETIRED_WORKFLOW_SKILL_PRESENT: $SKILLS_DIR/$retired_skill exists; remove it once with: rm -rf $SKILLS_DIR/$retired_skill"
    retiredWorkflowSkillsFound=$((retiredWorkflowSkillsFound + 1))
  fi
done
if [ "${#retiredWorkflowSkills[@]}" -gt 0 ] && [ "$retiredWorkflowSkillsFound" -eq 0 ]; then
  echo "   ok: no retired workflow skill directories present"
fi

# gentle-ai v4 also retired the SDD slash-commands that shipped as managed
# command files. Detect-only: a stale deployed copy is a hard failure because
# the owner removes it once (no auto-delete here). commands/ is USER SPACE, so
# this MUST stay a fixed denylist: a pattern such as sdd-*.md would false-
# positive on a user's own sdd-notes.md. Never derive it from a manifest and
# never replace it with a glob. A missing COMMANDS_DIR is a legitimate state
# (no commands installed) and must NOT become a directory-existence failure;
# the per-name [ -f ] test already yields no match.
retiredSddCommands=("sdd-apply" "sdd-archive" "sdd-code" "sdd-continue" "sdd-explore" "sdd-ff" "sdd-init" "sdd-new" "sdd-onboard" "sdd-research" "sdd-status" "sdd-verify")
retiredSddCommandsFound=0
for retired_cmd in "${retiredSddCommands[@]}"; do
  if [ -f "$COMMANDS_DIR/$retired_cmd.md" ]; then
    fail "RETIRED_SDD_COMMAND_PRESENT: $COMMANDS_DIR/$retired_cmd.md exists; remove it once with: rm $COMMANDS_DIR/$retired_cmd.md"
    retiredSddCommandsFound=$((retiredSddCommandsFound + 1))
  fi
done
if [ "${#retiredSddCommands[@]}" -gt 0 ] && [ "$retiredSddCommandsFound" -eq 0 ]; then
  echo "   ok: no retired SDD commands present"
fi

