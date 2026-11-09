echo "--- 11. Cache-prune safety approval ---"
# Failure-only runs retain exact V1 wording; failures dominate when skips also occurred.
if [ "$FAIL" -ne 0 ]; then
  echo "   skipped: workflow health has failures; no cleanup approval issued"
elif [ "${#SKIPPED_MESSAGES[@]}" -gt 0 ]; then
  echo "   skipped: required checks were skipped; no cleanup approval issued"
elif [ "$AUTO_REPAIRED" -ne 0 ]; then
  echo "   skipped: configuration was repaired; rerun after restart before cleanup is approved"
elif write_cache_prune_approval; then
  echo "   ok: issued a config-bound cache-prune approval for scheduled maintenance"
else
  fail "CACHE_PRUNE_APPROVAL_WRITE_FAILED: $CACHE_PRUNE_APPROVAL"
fi

echo ""
if [ "$FAIL" -ne 0 ]; then
  echo "${C_BOLD_RED}== Some checks failed — see the summary below ==${C_RESET}"
  echo ""
  echo "${C_BOLD_RED}Failed checks (${#FAIL_MESSAGES[@]}):${C_RESET}"
  idx=0
  for message in "${FAIL_MESSAGES[@]}"; do
    idx=$((idx + 1))
    printf '   %s. %s\n' "$idx" "$message"
  done
  if [ "${#SKIPPED_MESSAGES[@]}" -gt 0 ]; then
    printf '== VERIFICATION_INCOMPLETE: %s required check(s) skipped ==\n' "${#SKIPPED_MESSAGES[@]}"
    idx=0
    for message in "${SKIPPED_MESSAGES[@]}"; do
      idx=$((idx + 1))
      printf '   %s. %s\n' "$idx" "$message"
    done
  fi
  exit 1
elif [ "${#SKIPPED_MESSAGES[@]}" -gt 0 ]; then
  printf '== VERIFICATION_INCOMPLETE: %s required check(s) skipped ==\n' "${#SKIPPED_MESSAGES[@]}"
  idx=0
  for message in "${SKIPPED_MESSAGES[@]}"; do
    idx=$((idx + 1))
    printf '   %s. %s\n' "$idx" "$message"
  done
  exit 3
else
  if [ "$AUTO_REPAIRED" -eq 1 ]; then
    echo "== All checks passed — workflow setup intact (self-repairs applied) =="
  else
    echo "== All checks passed — workflow setup intact =="
  fi
fi
