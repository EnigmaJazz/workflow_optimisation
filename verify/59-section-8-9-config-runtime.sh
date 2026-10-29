# --- 8. systematic.jsonc inventory / overlay integrity ---
echo "--- 8. Systematic config inventory ---"
if [ -z "$ACTIVE_ROOT" ] || [ ! -d "$ACTIVE_AGENTS" ]; then
  fail "active Systematic agents directory unavailable; config inventory check skipped"
  STATIC_SYSTEMATIC_OK=0
elif [ ! -f "$SYSTEMATIC_CONFIG" ]; then
  fail "Systematic config missing: $SYSTEMATIC_CONFIG"
  STATIC_SYSTEMATIC_OK=0
else
  JS_RUNTIME=""
  if command_exists node; then
    JS_RUNTIME="node"
  elif command_exists bun; then
    JS_RUNTIME="bun"
  else
    fail "neither node nor bun is available for JSONC validation"
    STATIC_SYSTEMATIC_OK=0
  fi

  if [ -n "$JS_RUNTIME" ]; then
    if SYSTEMATIC_NODE_MODULES="$SYSTEMATIC_NODE_MODULES" "$JS_RUNTIME" "$SYSTEMATIC_CHECKER" "$SYSTEMATIC_CONFIG" "$ACTIVE_AGENTS"; then
      :
    else
      fail "systematic.jsonc inventory/overlay validation failed"
      STATIC_SYSTEMATIC_OK=0
    fi
  fi
fi

# --- 9. Runtime agent registration/models/tools + GGA fallback policy ---
echo "--- 9. OpenCode runtime agents + GGA fallback policy ---"
if [ "$STATIC_SYSTEMATIC_OK" -ne 1 ]; then
  fail "runtime agent checks skipped because static Systematic config validation failed"
elif [ "$CAN_RUNTIME_PROBE" -ne 1 ]; then
  fail "runtime agent checks skipped because the health-plugin recursion guard/digest binding is not ready"
elif ! command_exists opencode; then
  fail "opencode executable not found; runtime agent checks skipped"
else
  LIST_STATUS=0
  (
    cd "$AGENT_PROBE_CWD" || exit 1
    WORKFLOW_HEALTH_CHECK_PROBE=1 \
    SYSTEMATIC_ROUTING_GUARD_MODE=off \
    timeout 45s opencode agent list >"$AGENT_LIST_OUT" 2>"$AGENT_LIST_STDERR"
  ) || LIST_STATUS=$?

  if [ "$LIST_STATUS" -ne 0 ]; then
    fail "opencode agent list probe failed (exit $LIST_STATUS)"
    if [ "$LIST_STATUS" -eq 124 ]; then
      echo "   info: agent registration exceeded the 45-second cold-start budget; inspect plugin-load errors and retry from a warm cache"
    fi
    tail -12 "$AGENT_LIST_STDERR" 2>/dev/null | sed 's/^/      /'
  else
    # Every agent the embedded runtime checker reads via readDebug must be probed
    # here: github-scoped agents and the Systematic baseline reviewers. A missing
    # probe fails section 9.
    PROBE_NAMES=(
      gentle-orchestrator general explore
      frontend-dev frontend-dev-premium frontend-dev-premium-astra
      jd-judge-a jd-judge-b
      review-risk review-readability review-reliability review-resilience review-refuter review-validator
      asi-review-risk asi-review-resilience asi-review-readability asi-review-reliability asi-review-refuter asi-review-validator
      advisor-design-pre-astra advisor-security-pre-astra
      correctness-reviewer testing-reviewer project-standards-reviewer repo-research-analyst adversarial-document-reviewer
      adversarial-document-reviewer-astra adversarial-reviewer adversarial-reviewer-astra
      security-reviewer security-reviewer-astra security-lens-reviewer security-lens-reviewer-astra
      api-contract-reviewer architecture-strategist reliability-reviewer
      data-migrations-reviewer deployment-verification-agent feasibility-reviewer design-iterator
    )
    while IFS= read -r listed; do
      # Probe every agent the runtime registers, so the probe set cannot drift
      # from the agents the runtime checker reads via readDebug.
      if [[ "$listed" =~ ^([^[:space:]]+)[[:space:]]+\((primary|subagent|all)\)$ ]]; then
        PROBE_NAMES+=("${BASH_REMATCH[1]}")
      fi
    done < "$AGENT_LIST_OUT"
    while IFS= read -r md; do
      [ -f "$md" ] || continue
      base=$(basename "$md" .md)
      [ "${base,,}" = "readme" ] && continue
      tools_line=$(sed -nE 's/^tools:[[:space:]]*(.*)$/\1/ip' "$md" | head -1)
      if printf '%s' "$tools_line" | grep -qiE '(^|,)[[:space:]]*(Edit|Write)([[:space:]]*,|$)'; then
        PROBE_NAMES+=("$base")
      fi
    done < <(find "$ACTIVE_AGENTS" -mindepth 1 -maxdepth 2 -type f -name '*.md' -print 2>/dev/null)

    UNIQUE_PROBES=()
    declare -A SEEN_PROBE=()
    for name in "${PROBE_NAMES[@]}"; do
      if [ -z "${SEEN_PROBE[$name]+x}" ]; then
        UNIQUE_PROBES+=("$name")
        SEEN_PROBE[$name]=1
      fi
    done

    MAX_PARALLEL=4
    RUNNING=0
    # The embedded runtime checker reads agents by name. Literal readDebug(...)
    # targets plus its agent-name arrays are extracted here and must all be in
    # the probe set. Runtime-derived targets (astra aliases, Systematic
    # inventory mutators) are covered because every registered agent is probed
    # above. The guard fails closed if the extraction itself goes stale.
    CHECKER_AGENT_REFS="$(
      {
        grep -oE 'readDebug\("[^"]+"\)' "$RUNTIME_AGENT_CHECKER" 2>/dev/null
        grep -oE '(githubReaderNames|githubBlockedNames|gga)=\[[^]]*\]' "$RUNTIME_AGENT_CHECKER" 2>/dev/null
      } | grep -oE '"[a-z][a-z0-9-]*"' | tr -d '"' | sort -u
    )"
    if [ -z "$CHECKER_AGENT_REFS" ]; then
      fail "PROBE_LIST_AGENT_EXTRACTION_EMPTY: no checker agent references found in $RUNTIME_AGENT_CHECKER"
    fi
    while IFS= read -r checker_agent; do
      [ -n "$checker_agent" ] || continue
      if [ -z "${SEEN_PROBE[$checker_agent]+x}" ]; then
        fail "PROBE_LIST_MISSING_CHECKER_AGENT: ${checker_agent} is read by the runtime checker but never probed"
      fi
    done <<< "$CHECKER_AGENT_REFS"
    for name in "${UNIQUE_PROBES[@]}"; do
      (
        cd "$AGENT_PROBE_CWD" || exit 1
        status=0
        WORKFLOW_HEALTH_CHECK_PROBE=1 \
        SYSTEMATIC_ROUTING_GUARD_MODE=off \
        timeout 15s opencode debug agent "$name" \
          >"$DEBUG_AGENT_DIR/$name.json" 2>"$DEBUG_AGENT_DIR/$name.stderr" || status=$?
        printf '%s\n' "$status" >"$DEBUG_AGENT_DIR/$name.status"
      ) &
      RUNNING=$((RUNNING + 1))
      if [ "$RUNNING" -ge "$MAX_PARALLEL" ]; then
        wait -n || true
        RUNNING=$((RUNNING - 1))
      fi
    done
    wait || true

    PROBE_FAILURE=0
    for name in "${UNIQUE_PROBES[@]}"; do
      status=$(cat "$DEBUG_AGENT_DIR/$name.status" 2>/dev/null || printf 'missing')
      if [ "$status" != "0" ]; then
        echo "   !! opencode debug agent $name failed (status $status)"
        tail -8 "$DEBUG_AGENT_DIR/$name.stderr" 2>/dev/null | sed 's/^/      /'
        PROBE_FAILURE=1
      elif grep -qiE 'level=ERROR|failed to load plugin' "$DEBUG_AGENT_DIR/$name.stderr" 2>/dev/null; then
        echo "   !! opencode debug agent $name reported plugin-load error(s)"
        grep -iE 'level=ERROR|failed to load plugin' "$DEBUG_AGENT_DIR/$name.stderr" | tail -6 | sed 's/^/      /'
        PROBE_FAILURE=1
      fi
    done

    if [ "$PROBE_FAILURE" -ne 0 ]; then
      fail "one or more per-agent runtime probes failed"
    elif SYSTEMATIC_NODE_MODULES="$SYSTEMATIC_NODE_MODULES" "$JS_RUNTIME" "$RUNTIME_AGENT_CHECKER" \
      "$SYSTEMATIC_CONFIG" "$ACTIVE_AGENTS" "$AGENT_LIST_OUT" "$DEBUG_AGENT_DIR" "$OPENCODE_CONFIG_FILE" \
      "$FALLBACK_POLICY_SOURCE" "$WORKSPACE"; then
      echo "   ok: runtime agent registration/model/tool and GGA fallback checks passed"
    else
      fail "OpenCode runtime agent registration/model/tool or GGA fallback policy check failed"
    fi
  fi
fi

