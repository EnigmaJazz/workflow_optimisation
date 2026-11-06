recover_systematic_config() {
  python3 - "$SYSTEMATIC_CONFIG" "$SYSTEMATIC_CONFIG_SOURCE" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" <<'PY_RECOVER_SYSTEMATIC'
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile

target = Path(sys.argv[1])
source = Path(sys.argv[2])
backup_root = Path(sys.argv[3])
run_id = sys.argv[4]

def parse_jsonc(path):
    text = path.read_text(encoding="utf-8")
    out = []
    i = 0
    in_string = False
    escaped = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated block comment")
            i = end + 2
            continue
        out.append(ch)
        i += 1
    stripped = "".join(out)
    stripped = re.sub(r",\s*([}\]])", r"\1", stripped)
    return json.loads(stripped)

try:
    canonical = parse_jsonc(source)
except FileNotFoundError:
    print(f"error\tcanonical Systematic source missing: {source}")
    raise SystemExit(0)
except Exception as exc:
    print(f"error\tcanonical Systematic source is invalid: {exc}")
    raise SystemExit(0)

if not isinstance(canonical, dict) or not isinstance(canonical.get("categories"), dict) or not isinstance(canonical.get("agents"), dict):
    print("error\tcanonical Systematic source lacks categories/agents overlays")
    raise SystemExit(0)

# Systematic rejects `tools` in its agents overlays and disables all bundled
# agents when configuration validation fails. Refuse a bad reviewed source
# before recovery can deploy it to a working OpenCode installation.
for name, overlay in canonical["agents"].items():
    if isinstance(overlay, dict) and "tools" in overlay:
        print(f"error\tSYSTEMATIC_UNSUPPORTED_AGENT_TOOLS: {name}; remove tools from reviewed Systematic source")
        raise SystemExit(0)

current = {}
target_valid = False
if target.is_file():
    try:
        current = parse_jsonc(target)
        target_valid = isinstance(current, dict)
    except Exception:
        target_valid = False

# Preserve unknown future top-level settings, but the reviewed schema,
# categories, agents, profiles, and policy controls remain authoritative.
merged = deepcopy(current) if target_valid else {}
for key, value in canonical.items():
    merged[key] = deepcopy(value)

# Profiles are reviewed routing policy, not an unknown forward-compatible key.
# If the canonical source intentionally has no profiles map, remove any older
# map (including the retired global astra-critical profile) during recovery.
if "profiles" not in canonical:
    merged.pop("profiles", None)

# Systematic 3.16 permits an active named profile. Preserve only a selection
# that names a reviewed canonical profile; discard stale or unknown selections.
selected = current.get("profile") if target_valid else None
profiles = canonical.get("profiles")
if isinstance(selected, str) and isinstance(profiles, dict) and selected in profiles:
    merged["profile"] = selected
else:
    merged.pop("profile", None)

if target_valid and current == merged:
    detail = "reviewed Systematic overlays are current"
    if isinstance(selected, str):
        detail += f"; active profile={selected}"
    print(f"clean\t{detail}")
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "systematic.jsonc.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".systematic.jsonc.recovery.", dir=target.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(merged, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, mode)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

print(f"repaired\t{backup}")
PY_RECOVER_SYSTEMATIC
}

recover_fallback_policy() {
  python3 - "$FALLBACK_POLICY_DEPLOYED" "$FALLBACK_POLICY_SOURCE" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" <<'PY_RECOVER_FALLBACK'
from pathlib import Path
import json
import os
import shutil
import stat
import sys
import tempfile

target = Path(sys.argv[1])
source = Path(sys.argv[2])
backup_root = Path(sys.argv[3])
run_id = sys.argv[4]

try:
    canonical_bytes = source.read_bytes()
    parsed = json.loads(canonical_bytes)
except FileNotFoundError:
    print(f"error\tcanonical fallback policy missing: {source}")
    raise SystemExit(0)
except Exception as exc:
    print(f"error\tcanonical fallback policy is invalid: {exc}")
    raise SystemExit(0)
if not isinstance(parsed, dict):
    print("error\tcanonical fallback policy must be a JSON object")
    raise SystemExit(0)

if target.is_file() and target.read_bytes() == canonical_bytes:
    print("clean\treviewed fallback policy is current")
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "rate-limit-fallback.json.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".rate-limit-fallback.json.recovery.", dir=target.parent)
try:
    with os.fdopen(fd, "wb") as handle:
        handle.write(canonical_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, mode)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)

print(f"repaired\t{backup}")
PY_RECOVER_FALLBACK
}


read_verify_script_pin() {
  local path="$1"
  python3 - "$path" <<'PY_VERIFY_PIN'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
try:
    text = path.read_text(encoding="utf-8")
except Exception:
    raise SystemExit(1)

# Accept normal TypeScript formatting, including line breaks around '=' and the
# quoted digest. Require a real const assignment ending in ';' so comments or
# documentation examples cannot satisfy the verifier accidentally.
match = re.search(
    r'''\bconst\s+VERIFY_SCRIPT_SHA256\s*=\s*(["'])(([0-9a-fA-F]{64}))\1\s*;''',
    text,
    flags=re.MULTILINE,
)
if not match:
    raise SystemExit(1)
print(match.group(2).lower())
PY_VERIFY_PIN
}

# Put temporary probe files under the user's cache when possible. This avoids
# project-local OpenCode config discovery while remaining writable in the
# normal and Nono-secured OpenCode environments.
