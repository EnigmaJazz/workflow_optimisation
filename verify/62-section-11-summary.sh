echo "--- 11. Cache-prune safety approval ---"
if [ "$FAIL" -ne 0 ]; then
  echo "   skipped: workflow health has failures; no cleanup approval issued"
elif [ "$AUTO_REPAIRED" -ne 0 ]; then
  echo "   skipped: configuration was repaired; rerun after restart before cleanup is approved"
elif write_cache_prune_approval; then
  echo "   ok: issued a config-bound cache-prune approval for scheduled maintenance"
else
  fail "CACHE_PRUNE_APPROVAL_WRITE_FAILED: $CACHE_PRUNE_APPROVAL"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  if [ "$AUTO_REPAIRED" -eq 1 ]; then
    echo "== All checks passed — workflow setup intact (self-repairs applied) =="
  else
    echo "== All checks passed — workflow setup intact =="
  fi
else
  echo "${C_BOLD_RED}== Some checks failed — see the summary below ==${C_RESET}"
  echo ""
  echo "${C_BOLD_RED}Failed checks (${#FAIL_MESSAGES[@]}):${C_RESET}"
  idx=0
  for message in "${FAIL_MESSAGES[@]}"; do
    idx=$((idx + 1))
    printf '   %s. %s\n' "$idx" "$message"
  done
  exit 1
fi
