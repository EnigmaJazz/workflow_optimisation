# --- 2. Resolve active Systematic install ---
echo "--- 2. Active Systematic install ---"

# Resolve the Systematic source tree from the plugin spec that is actually
# deployed in opencode.json. Never prefer an unrelated @latest/bare cache over
# an exact configured pin: later inventory/model/permission checks must inspect
# the same package version OpenCode is configured to load.
SYSTEMATIC_PLUGIN_SPEC="$(
  node - "$OPENCODE_CONFIG_FILE" <<'EOF_SYSTEMATIC_SPEC' 2>/dev/null || true
const fs = require("fs")
const path = process.argv[2]
try {
  const config = JSON.parse(fs.readFileSync(path, "utf8"))
  const plugins = Array.isArray(config.plugin) ? config.plugin : []
  const specs = plugins.filter((value) =>
    typeof value === "string" &&
    (value === "@fro.bot/systematic" || value.startsWith("@fro.bot/systematic@"))
  )
  if (specs.length === 1) process.stdout.write(specs[0])
  else if (specs.length > 1) process.stdout.write(`__MULTIPLE__\n${specs.join("\n")}`)
} catch {}
EOF_SYSTEMATIC_SPEC
)"

if [ -z "$SYSTEMATIC_PLUGIN_SPEC" ]; then
  fail "SYSTEMATIC_PLUGIN_SPEC_MISSING: no @fro.bot/systematic plugin entry in $OPENCODE_CONFIG_FILE"
elif printf '%s\n' "$SYSTEMATIC_PLUGIN_SPEC" | grep -q '^__MULTIPLE__$'; then
  fail "SYSTEMATIC_PLUGIN_SPEC_AMBIGUOUS: multiple @fro.bot/systematic plugin entries are configured"
else
  echo "   configured: $SYSTEMATIC_PLUGIN_SPEC"

  SYSTEMATIC_REQUESTED="${SYSTEMATIC_PLUGIN_SPEC#@fro.bot/systematic}"
  SYSTEMATIC_REQUESTED="${SYSTEMATIC_REQUESTED#@}"
  [ "$SYSTEMATIC_PLUGIN_SPEC" = "@fro.bot/systematic" ] && SYSTEMATIC_REQUESTED=""

  is_exact_version=0
  if printf '%s' "$SYSTEMATIC_REQUESTED" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([+-][0-9A-Za-z.-]+)?$'; then
    is_exact_version=1
  fi

  candidate_root=""
  if [ "$is_exact_version" -eq 1 ]; then
    exact_cache="$PACKAGES_DIR/systematic@$SYSTEMATIC_REQUESTED/node_modules/@fro.bot/systematic"
    if [ -d "$exact_cache/skills" ] && [ -d "$exact_cache/agents" ] && [ -f "$exact_cache/package.json" ]; then
      candidate_root="$exact_cache"
    else
      # Current upstream OpenCode documents a shared node_modules cache, while
      # the auto-update plugin may materialize spec-addressed package trees.
      # Accept either layout, but only when package.json proves the exact pin.
      standard_cache="$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic"
      standard_version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$standard_cache/package.json" 2>/dev/null || true)"
      if [ "$standard_version" = "$SYSTEMATIC_REQUESTED" ] && [ -d "$standard_cache/skills" ] && [ -d "$standard_cache/agents" ]; then
        candidate_root="$standard_cache"
      fi

      # Cache naming is an implementation detail. If it changes, locate a
      # candidate by the nested package's authoritative package.json version.
      if [ -z "$candidate_root" ]; then
        while IFS= read -r pkg; do
          [ -n "$pkg" ] || continue
          version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
          root="$(dirname "$pkg")"
          if [ "$version" = "$SYSTEMATIC_REQUESTED" ] && [ -d "$root/skills" ] && [ -d "$root/agents" ]; then
            candidate_root="$root"
            break
          fi
        done < <(find "$PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@fro.bot/systematic/package.json' -type f -print 2>/dev/null | sort)
      fi
    fi

    if [ -z "$candidate_root" ]; then
      discovered="$(
        { find "$PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@fro.bot/systematic/package.json' -type f -print 2>/dev/null
          [ -f "$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic/package.json" ] && printf '%s\n' "$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic/package.json"
        } |
        while IFS= read -r pkg; do
          version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
          [ -n "$version" ] && printf '%s=%s\n' "$(dirname "$pkg")" "$version"
        done | sort | paste -sd ';' -
      )"
      fail "SYSTEMATIC_CONFIGURED_VERSION_NOT_INSTALLED: configured=$SYSTEMATIC_REQUESTED discovered=${discovered:-<none>}"
    fi
  else
    # Non-exact specs remain supported, but are intentionally reported as such.
    # They cannot prove reproducibility as strongly as an exact semver pin.
    suffix="${SYSTEMATIC_REQUESTED:-bare}"
    if [ -n "$SYSTEMATIC_REQUESTED" ]; then
      tagged="$PACKAGES_DIR/systematic@$SYSTEMATIC_REQUESTED/node_modules/@fro.bot/systematic"
    else
      tagged="$PACKAGES_DIR/systematic/node_modules/@fro.bot/systematic"
    fi
    if [ -d "$tagged/skills" ] && [ -d "$tagged/agents" ] && [ -f "$tagged/package.json" ]; then
      candidate_root="$tagged"
    else
      fail "SYSTEMATIC_CONFIGURED_CACHE_NOT_FOUND: configured=$SYSTEMATIC_PLUGIN_SPEC expected=$tagged"
    fi
  fi

  if [ -n "$candidate_root" ]; then
    ACTIVE_ROOT="$candidate_root"
    ACTIVE_SKILLS="$ACTIVE_ROOT/skills"
    ACTIVE_AGENTS="$ACTIVE_ROOT/agents"
    SYSTEMATIC_NODE_MODULES="$(dirname "$(dirname "$ACTIVE_ROOT")")"

    VERSION="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$ACTIVE_ROOT/package.json" 2>/dev/null || true)"
    echo "   resolved cache: $ACTIVE_ROOT"
    echo "   version: ${VERSION:-<unknown>}"

    if [ -z "$VERSION" ] || [ "$(printf '%s\n' "3.18.4" "$VERSION" | sort -V | head -n 1)" != "3.18.4" ]; then
      fail "Systematic v3.18.4+ is required for workflow-guard terminal replay fidelity; got ${VERSION:-<unknown>}"
    fi

    if [ "$is_exact_version" -eq 1 ] && [ "$VERSION" != "$SYSTEMATIC_REQUESTED" ]; then
      fail "SYSTEMATIC_PIN_MISMATCH: configured=$SYSTEMATIC_REQUESTED resolved=${VERSION:-<unknown>} path=$ACTIVE_ROOT"
      ACTIVE_ROOT=""
      ACTIVE_SKILLS=""
      ACTIVE_AGENTS=""
      SYSTEMATIC_NODE_MODULES=""
    elif [ "$is_exact_version" -eq 1 ]; then
      echo "   ok: exact Systematic pin is materialized and source checks will use it"
    else
      echo "   !! Systematic is not configured with an exact semver pin; source checks use the configured cache tag"
    fi

    # Stale caches are diagnostic only. They are harmless once source resolution
    # is anchored to the configured plugin spec, but listing them makes cleanup
    # straightforward.
    stale=()
    while IFS= read -r pkg; do
      [ -n "$pkg" ] || continue
      root="$(dirname "$pkg")"
      [ "$root" = "$ACTIVE_ROOT" ] && continue
      version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
      stale+=("$root=${version:-unknown}")
    done < <(
      { find "$PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@fro.bot/systematic/package.json' -type f -print 2>/dev/null
        [ -f "$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic/package.json" ] && printf '%s\n' "$OPENCODE_CACHE_DIR/node_modules/@fro.bot/systematic/package.json"
      } | sort -u
    )
    if [ "${#stale[@]}" -gt 0 ]; then
      echo "   info: ignored other cached Systematic trees:"
      for item in "${stale[@]}"; do
        echo "      $item"
      done
    fi
  fi
fi

