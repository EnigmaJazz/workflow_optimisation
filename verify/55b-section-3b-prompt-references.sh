#!/usr/bin/env bash
# Verify prompt-named skills resolve in the installed skill registry.
echo "--- 3b. Prompt-named skills ---"
if [ ! -d "$SKILLS_DIR" ]; then
  fail "PROMPT_REFERENCE_SKILLS_ROOT_MISSING: $SKILLS_DIR"
else
  PROMPT_REF_DIR=$(mktemp -d 2>/dev/null)
  if [ -z "$PROMPT_REF_DIR" ] || [ ! -d "$PROMPT_REF_DIR" ]; then
    fail "PROMPT_REFERENCE_CHECK_FAILED: could not create a temporary foreign repo"
  else
    PROMPT_REF_RESULT=$(python3 "$VERIFY_MODULE_DIR/checkers/check-prompt-references.py" "$PROMPT_REF_DIR" "$SKILLS_DIR" --this-repo "$WORKSPACE" 2>&1)
    case "$PROMPT_REF_RESULT" in
      ok$'\t'*) echo "   $PROMPT_REF_RESULT" ;;
      error$'\t'*) fail "PROMPT_REFERENCE_UNRESOLVED: ${PROMPT_REF_RESULT#*$'\t'}" ;;
      *) fail "PROMPT_REFERENCE_CHECK_FAILED: $PROMPT_REF_RESULT" ;;
    esac

    PROMPT_REF_PROBE_RESULT=$(python3 "$VERIFY_MODULE_DIR/checkers/check-prompt-references.py" "$PROMPT_REF_DIR" "$SKILLS_DIR" --this-repo "$WORKSPACE" --probe q128-deliberately-unresolvable 2>&1)
    case "$PROMPT_REF_PROBE_RESULT" in
      error$'\t'*q128-deliberately-unresolvable*) echo "   ok: positive control fails as required" ;;
      ok$'\t'*) fail "PROMPT_REFERENCE_POSITIVE_CONTROL_DID_NOT_FAIL: $PROMPT_REF_PROBE_RESULT" ;;
      *) fail "PROMPT_REFERENCE_CHECK_FAILED: $PROMPT_REF_PROBE_RESULT" ;;
    esac
    rm -rf -- "$PROMPT_REF_DIR"
  fi
fi
