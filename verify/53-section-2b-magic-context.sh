# --- 2b. Resolve the exact Magic Context package OpenCode is configured to load ---
echo "--- 2b. Active Magic Context install ---"
MAGIC_PLUGIN_SPEC="$(
  node - "$OPENCODE_CONFIG_FILE" <<'EOF_MAGIC_SPEC' 2>/dev/null || true
const fs = require("fs")
const file = process.argv[2]
try {
  const config = JSON.parse(fs.readFileSync(file, "utf8"))
  const plugins = Array.isArray(config.plugin) ? config.plugin : []
  const specs = plugins.filter((value) =>
    typeof value === "string" &&
    (value === "@cortexkit/opencode-magic-context" ||
      value.startsWith("@cortexkit/opencode-magic-context@"))
  )
  if (specs.length === 1) process.stdout.write(specs[0])
  else if (specs.length > 1) process.stdout.write(`__MULTIPLE__\n${specs.join("\n")}`)
} catch {}
EOF_MAGIC_SPEC
)"

if [ -z "$MAGIC_PLUGIN_SPEC" ]; then
  fail "MAGIC_CONTEXT_PLUGIN_SPEC_MISSING: no @cortexkit/opencode-magic-context entry in $OPENCODE_CONFIG_FILE"
elif printf '%s\n' "$MAGIC_PLUGIN_SPEC" | grep -q '^__MULTIPLE__$'; then
  fail "MAGIC_CONTEXT_PLUGIN_SPEC_AMBIGUOUS: multiple @cortexkit/opencode-magic-context entries are configured"
else
  echo "   configured: $MAGIC_PLUGIN_SPEC"
  MAGIC_REQUESTED="${MAGIC_PLUGIN_SPEC#@cortexkit/opencode-magic-context@}"
  if [ "$MAGIC_PLUGIN_SPEC" = "@cortexkit/opencode-magic-context" ] || \
     ! printf '%s' "$MAGIC_REQUESTED" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+([+-][0-9A-Za-z.-]+)?$'; then
    fail "MAGIC_CONTEXT_VERSION_NOT_EXACT: configured=$MAGIC_PLUGIN_SPEC"
  else
    MAGIC_ROOT="$MAGIC_PACKAGES_DIR/opencode-magic-context@$MAGIC_REQUESTED/node_modules/@cortexkit/opencode-magic-context"
    if [ ! -f "$MAGIC_ROOT/package.json" ]; then
      MAGIC_ROOT=""
      standard_magic="$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context"
      standard_magic_version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$standard_magic/package.json" 2>/dev/null || true)"
      if [ "$standard_magic_version" = "$MAGIC_REQUESTED" ]; then
        MAGIC_ROOT="$standard_magic"
      else
        while IFS= read -r pkg; do
          [ -n "$pkg" ] || continue
          version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
          if [ "$version" = "$MAGIC_REQUESTED" ]; then
            MAGIC_ROOT="$(dirname "$pkg")"
            break
          fi
        done < <(find "$MAGIC_PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@cortexkit/opencode-magic-context/package.json' -type f -print 2>/dev/null | sort)
      fi
    fi

    if [ -z "$MAGIC_ROOT" ]; then
      discovered="$(
        { find "$MAGIC_PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@cortexkit/opencode-magic-context/package.json' -type f -print 2>/dev/null
          [ -f "$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context/package.json" ] && printf '%s\n' "$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context/package.json"
        } |
        while IFS= read -r pkg; do
          version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
          [ -n "$version" ] && printf '%s=%s\n' "$(dirname "$pkg")" "$version"
        done | sort | paste -sd ';' -
      )"
      fail "MAGIC_CONTEXT_CONFIGURED_VERSION_NOT_INSTALLED: configured=$MAGIC_REQUESTED discovered=${discovered:-<none>}"
    else
      MAGIC_RESOLVED_VERSION="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$MAGIC_ROOT/package.json" 2>/dev/null || true)"
      echo "   resolved cache: $MAGIC_ROOT"
      echo "   version: ${MAGIC_RESOLVED_VERSION:-<unknown>}"
      if [ "$MAGIC_RESOLVED_VERSION" != "$MAGIC_REQUESTED" ]; then
        fail "MAGIC_CONTEXT_PIN_MISMATCH: configured=$MAGIC_REQUESTED resolved=${MAGIC_RESOLVED_VERSION:-<unknown>} path=$MAGIC_ROOT"
      else
        echo "   ok: exact Magic Context pin is materialized and matches opencode.json"
      fi

      stale_magic=()
      while IFS= read -r pkg; do
        [ -n "$pkg" ] || continue
        root="$(dirname "$pkg")"
        [ "$root" = "$MAGIC_ROOT" ] && continue
        version="$(node -e 'try{const p=require(process.argv[1]);process.stdout.write(String(p.version||""))}catch{}' "$pkg" 2>/dev/null || true)"
        stale_magic+=("$root=${version:-unknown}")
      done < <(
        { find "$MAGIC_PACKAGES_DIR" -maxdepth 6 -path '*/node_modules/@cortexkit/opencode-magic-context/package.json' -type f -print 2>/dev/null
          [ -f "$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context/package.json" ] && printf '%s\n' "$OPENCODE_CACHE_DIR/node_modules/@cortexkit/opencode-magic-context/package.json"
        } | sort -u
      )
      if [ "${#stale_magic[@]}" -gt 0 ]; then
        echo "   info: ignored other cached Magic Context trees (not auto-deleted):"
        for item in "${stale_magic[@]}"; do
          echo "      $item"
        done
      fi
    fi
  fi
fi

