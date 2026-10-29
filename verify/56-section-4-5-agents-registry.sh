# --- 4. Global AGENTS.md routing section ---
echo "--- 4. Global AGENTS.md routing section ---"
echo "   ok: routing section present and canonical (validated during recovery)"

# --- 5. Skill registry ---
echo "--- 5. Skill registry ---"
if command_exists gentle-ai; then
  if REGISTRY_OUTPUT=$(gentle-ai skill-registry refresh --cwd "$WORKSPACE" 2>&1); then
    echo "$REGISTRY_OUTPUT" | head -1
  else
    echo "$REGISTRY_OUTPUT" | head -12
    fail "gentle-ai skill-registry refresh failed"
  fi
else
  fail "gentle-ai executable not found; registry refresh skipped"
fi

