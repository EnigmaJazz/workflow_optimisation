write_cache_prune_approval() {
  python3 - "$CACHE_PRUNE_APPROVAL" "$OPENCODE_CONFIG_FILE" "$TUI_CONFIG_FILE" "$0" <<'PY_CACHE_APPROVAL'
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

target = Path(sys.argv[1])
config_paths = [Path(sys.argv[2]), Path(sys.argv[3])]
verifier = Path(sys.argv[4]).resolve(strict=True)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

references = set()
digests = {}
for path in config_paths:
    value = json.loads(path.read_text(encoding="utf-8"))
    plugins = value.get("plugin", [])
    if not isinstance(plugins, list) or not all(isinstance(ref, str) for ref in plugins):
        raise RuntimeError(f"invalid plugin list in {path}")
    references.update(plugins)
    digests[path.name] = sha256(path)

approval = {
    "schema": "workflow.cache-prune-approval/v1",
    "approved_at_epoch": int(time.time()),
    "config_sha256": digests,
    "plugin_references": sorted(references),
    "verifier_path": str(verifier),
    "verifier_sha256": sha256(verifier),
}

target.parent.mkdir(parents=True, exist_ok=True)
fd, temp_name = tempfile.mkstemp(prefix=".cache-prune-approval.", dir=target.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(approval, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp_name, 0o600)
    os.replace(temp_name, target)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)
PY_CACHE_APPROVAL
}

recover_opencode_config() {
  python3 - "$OPENCODE_CONFIG_FILE" "$OPENCODE_CONFIG_SOURCE" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" "$LOCAL_AUTO_UPDATE_REF" "$PLUGIN_CACHE_INTEGRITY_HELPER" "$OPENCODE_CACHE_DIR/packages" <<'PY_RECOVER_OPENCODE'
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlparse

target = Path(sys.argv[1])
source = Path(sys.argv[2])
backup_root = Path(sys.argv[3])
run_id = sys.argv[4]
local_auto_update_ref = sys.argv[5]
integrity_helper = sys.argv[6]
packages_cache_root = sys.argv[7]
auto_update_identity = "opencode-plugin-auto-update"

parsed_local_ref = urlparse(local_auto_update_ref)
if parsed_local_ref.scheme != "file" or parsed_local_ref.netloc not in ("", "localhost"):
    print("error\treviewed local auto-update reference must be a local file URI")
    raise SystemExit(0)
local_auto_update_path = Path(unquote(parsed_local_ref.path))
if not local_auto_update_path.is_file():
    print(f"error\treviewed local auto-update build is missing: {local_auto_update_path}")
    raise SystemExit(0)

required_agents = {
    "gentle-orchestrator", "general", "explore",
    "gentle-ai-explore", "gentle-ai-worker", "gentle-ai-worker-local", "gentle-ai-verify",
    "gentle-ai-verify-routine", "pm-odd", "pm-systematic", "odd-apply",
    "frontend-dev", "frontend-dev-premium",
    "asi-review-risk", "asi-review-resilience", "asi-review-readability",
    "asi-review-reliability", "asi-review-refuter", "asi-review-validator",
    "advisor-design-pre", "advisor-security-pre", "advisor-integration-pre",
    "advisor-testing-pre", "advisor-maintainability-pre",
    "advisor-design-post", "advisor-security-post", "advisor-integration-post",
    "advisor-testing-post", "advisor-maintainability-post",
    "advisor-gemini-pre", "advisor-gemini-post", "advisor-gemini-evidence",
}

# These package identities are intentionally version-managed by the reviewed
# local auto-update plugin. The auto-update plugin itself is deliberately not
# in this set: its exact file URI is owned by this workflow and is immutable
# during recovery.
auto_updated_plugin_packages = {
    "@fro.bot/systematic",
    "@cortexkit/opencode-magic-context",
    "@cortexkit/aft-opencode",
    "opencode-usage-total",
}

def package_identity(ref):
    if not isinstance(ref, str) or ref.startswith(("file:", "/", ".")):
        return None
    if ref.startswith("@"):
        slash = ref.find("/")
        if slash < 2:
            return None
        version_at = ref.find("@", slash)
        return ref if version_at < 0 else ref[:version_at]
    version_at = ref.find("@")
    return ref if version_at < 0 else ref[:version_at]

def managed_identity(ref):
    if ref == local_auto_update_ref:
        return auto_update_identity
    return package_identity(ref)

def safe_versioned_ref(ref, identity):
    if not isinstance(ref, str) or package_identity(ref) != identity:
        return False
    suffix = ref[len(identity):]
    if not suffix.startswith("@") or len(suffix) < 2:
        return False
    tag = suffix[1:]
    return all(ch.isalnum() or ch in ".+_-" for ch in tag)

def semver_core(ref, identity):
    if not safe_versioned_ref(ref, identity):
        return None
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", ref[len(identity) + 1:])
    return tuple(map(int, match.groups())) if match else None

def pin_is_complete(ref):
    # A newer deployed pin is only trustworthy when its package is fully
    # installed in the OpenCode cache (an interrupted install leaves no package.json),
    # or when the cache is not yet filled and the auto-updater's install in the
    # config dir declares that version (OpenCode fills the cache at its next start).
    try:
        proc = subprocess.run(
            [sys.executable, integrity_helper, "check-pin",
             "--cache-root", packages_cache_root,
             "--installed-root", str(target.parent), "--spec", ref],
            capture_output=True, text=True, timeout=30)
        return proc.returncode == 0
    except Exception:
        return False

def safe_same_or_newer(current_ref, canonical_ref, identity):
    current_version = semver_core(current_ref, identity)
    canonical_version = semver_core(canonical_ref, identity)
    if current_version is None or canonical_version is None:
        return current_ref == canonical_ref
    return current_version >= canonical_version

try:
    canonical = json.loads(source.read_text(encoding="utf-8"))
except FileNotFoundError:
    print(f"error\tcanonical OpenCode source missing: {source}")
    raise SystemExit(0)
except Exception as exc:
    print(f"error\tcanonical OpenCode source is invalid: {exc}")
    raise SystemExit(0)

if not isinstance(canonical, dict):
    print("error\tcanonical OpenCode source must be a JSON object")
    raise SystemExit(0)

# Normalize an older reviewed source in memory so even a staggered deployment
# cannot replace the fixed local build with the abandoned npm release. The
# distributed canonical config also contains the local URI directly.
canonical_plugins_raw = canonical.get("plugin")
if not isinstance(canonical_plugins_raw, list) or not all(isinstance(ref, str) for ref in canonical_plugins_raw):
    print("error\tcanonical OpenCode source must contain a string plugin list")
    raise SystemExit(0)
canonical_plugins_normalized = []
auto_update_seen = False
for ref in canonical_plugins_raw:
    identity = managed_identity(ref)
    if identity == auto_update_identity:
        if not auto_update_seen:
            canonical_plugins_normalized.append(local_auto_update_ref)
            auto_update_seen = True
    else:
        canonical_plugins_normalized.append(ref)
if not auto_update_seen:
    print("error\tcanonical OpenCode source has no reviewed auto-update plugin entry")
    raise SystemExit(0)
canonical["plugin"] = canonical_plugins_normalized

agents = canonical.get("agent")
missing = sorted(required_agents - set(agents if isinstance(agents, dict) else {}))
if missing:
    print(f"error\tcanonical OpenCode source is missing reviewed agents: {','.join(missing)}")
    raise SystemExit(0)
if canonical.get("default_agent") != "gentle-orchestrator":
    print("error\tcanonical OpenCode source has the wrong default_agent")
    raise SystemExit(0)

target_valid = False
current = {}
if target.is_file():
    try:
        current = json.loads(target.read_text(encoding="utf-8"))
        target_valid = isinstance(current, dict)
    except Exception:
        target_valid = False

# The reviewed source owns every key it declares. Unknown future top-level keys
# from OpenCode/Gentle AI survive, but nested security/agent maps are replaced
# atomically so a sync cannot retain unsafe local aliases or prompt drift.
merged = deepcopy(current) if target_valid else {}
for key, value in canonical.items():
    merged[key] = deepcopy(value)

preserved_pins = []
unpreserved_pins = []
canonical_plugins = canonical.get("plugin")
current_plugins = current.get("plugin") if target_valid else None
if isinstance(canonical_plugins, list) and isinstance(current_plugins, list):
    current_by_identity = {}
    for ref in current_plugins:
        identity = managed_identity(ref)
        if identity == auto_update_identity and ref == local_auto_update_ref:
            current_by_identity.setdefault(identity, []).append(ref)
        elif identity in auto_updated_plugin_packages and safe_versioned_ref(ref, identity):
            current_by_identity.setdefault(identity, []).append(ref)

    effective_plugins = []
    for canonical_ref in canonical_plugins:
        identity = managed_identity(canonical_ref)
        candidates = current_by_identity.get(identity, [])
        if identity == auto_update_identity:
            effective_plugins.append(local_auto_update_ref)
        elif (identity in auto_updated_plugin_packages and len(candidates) == 1 and
                safe_same_or_newer(candidates[0], canonical_ref, identity)):
            if candidates[0] == canonical_ref:
                effective_plugins.append(candidates[0])
            elif pin_is_complete(candidates[0]):
                effective_plugins.append(candidates[0])
                preserved_pins.append(candidates[0])
            else:
                # Incomplete install: keep the canonical pin; the overlay
                # rewrite below restores it to the live config.
                effective_plugins.append(deepcopy(canonical_ref))
                unpreserved_pins.append(candidates[0])
        else:
            effective_plugins.append(deepcopy(canonical_ref))
    merged["plugin"] = effective_plugins

owned_clean = target_valid and all(current.get(key) == merged.get(key) for key in canonical)
pin_detail = ""
for ref in unpreserved_pins:
    print(f"!! AUTO_UPDATED_PIN_INCOMPLETE_NOT_PRESERVED: {ref}", file=sys.stderr)
if unpreserved_pins:
    pin_detail += "; AUTO_UPDATED_PIN_INCOMPLETE_NOT_PRESERVED: " + ", ".join(unpreserved_pins)
if preserved_pins:
    pin_detail += "; preserved auto-update pins: " + ", ".join(preserved_pins)
# Reconcile the canonical source with pins the auto-updater advanced: the
# deployed pin is the reviewed floor, so write the newer version back into the
# canonical file. Textual and format-preserving; idempotent when already equal.
canonical_synced = []
canonical_skipped = []
if preserved_pins and isinstance(canonical_plugins, list):
    canonical_ref_by_identity = {}
    for ref in canonical_plugins:
        if isinstance(ref, str):
            canonical_ref_by_identity[managed_identity(ref)] = ref
    source_path = Path(source)
    source_text = None
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except Exception as exc:
        canonical_skipped.append(f"unreadable canonical source ({exc.__class__.__name__})")
    if source_text is not None:
        updated_text = source_text
        for ref in preserved_pins:
            identity = managed_identity(ref)
            canonical_ref = canonical_ref_by_identity.get(identity)
            if not canonical_ref:
                canonical_skipped.append(f"{identity} (no canonical counterpart)")
                continue
            if updated_text.count(canonical_ref) != 1:
                canonical_skipped.append(f"{identity} (ambiguous canonical match)")
                continue
            updated_text = updated_text.replace(canonical_ref, ref, 1)
            canonical_synced.append(f"{canonical_ref} -> {ref}")
        if canonical_synced and updated_text != source_text:
            try:
                sync_backup_dir = backup_root / run_id
                sync_backup_dir.mkdir(parents=True, exist_ok=True)
                os.chmod(sync_backup_dir, 0o700)
                shutil.copy2(source_path, sync_backup_dir / "opencode.json.source.before")
                sync_temp = source_path.with_name(source_path.name + ".tmp-sync")
                sync_temp.write_text(updated_text, encoding="utf-8")
                os.replace(sync_temp, source_path)
            except Exception as exc:
                canonical_skipped.append(f"write failed ({exc.__class__.__name__})")
                canonical_synced = []
if canonical_synced:
    pin_detail += "; synced canonical pins: " + ", ".join(canonical_synced)
if canonical_skipped:
    pin_detail += "; canonical pin sync skipped: " + ", ".join(canonical_skipped)
if owned_clean:
    print("clean\treviewed OpenCode overlay is current" + pin_detail)
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "opencode.json.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".opencode.json.recovery.", dir=target.parent)
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

print(f"repaired\t{backup}{pin_detail}")
PY_RECOVER_OPENCODE
}

recover_tui_config() {
  python3 - "$TUI_CONFIG_FILE" "$TUI_CONFIG_SOURCE" "$OPENCODE_CONFIG_FILE" "$RECOVERY_BACKUP_ROOT" "$RECOVERY_RUN_ID" "$LOCAL_AUTO_UPDATE_REF" <<'PY_RECOVER_TUI'
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from urllib.parse import unquote, urlparse

target = Path(sys.argv[1])
source = Path(sys.argv[2])
runtime_config = Path(sys.argv[3])
backup_root = Path(sys.argv[4])
run_id = sys.argv[5]
local_auto_update_ref = sys.argv[6]
auto_update_identity = "opencode-plugin-auto-update"

parsed_local_ref = urlparse(local_auto_update_ref)
if parsed_local_ref.scheme != "file" or parsed_local_ref.netloc not in ("", "localhost"):
    print("error\treviewed local auto-update reference must be a local file URI")
    raise SystemExit(0)
local_auto_update_path = Path(unquote(parsed_local_ref.path))
if not local_auto_update_path.is_file():
    print(f"error\treviewed local auto-update build is missing: {local_auto_update_path}")
    raise SystemExit(0)

def load_object(path, label):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error\t{label} missing: {path}")
        raise SystemExit(0)
    except Exception as exc:
        print(f"error\t{label} is invalid JSON: {exc}")
        raise SystemExit(0)
    if not isinstance(value, dict):
        print(f"error\t{label} must be a JSON object")
        raise SystemExit(0)
    return value

def package_identity(ref):
    if not isinstance(ref, str) or ref.startswith(("file:", "/", ".")):
        return None
    if ref.startswith("@"):
        slash = ref.find("/")
        if slash < 2:
            return None
        version_at = ref.find("@", slash)
        return ref if version_at < 0 else ref[:version_at]
    version_at = ref.find("@")
    return ref if version_at < 0 else ref[:version_at]

def managed_identity(ref):
    if ref == local_auto_update_ref:
        return auto_update_identity
    return package_identity(ref)

canonical = load_object(source, "canonical TUI source")
runtime = load_object(runtime_config, "active OpenCode config")
required_plugins = canonical.get("plugin")
if not isinstance(required_plugins, list) or not required_plugins or not all(isinstance(ref, str) and ref for ref in required_plugins):
    print("error\tcanonical TUI source must contain a non-empty string plugin list")
    raise SystemExit(0)

# The local updater participates in the TUI discovery surface. Replace any old
# npm reference and add the reviewed file URI when upgrading an older source.
normalized_required_plugins = []
auto_update_seen = False
for ref in required_plugins:
    if managed_identity(ref) == auto_update_identity:
        if not auto_update_seen:
            normalized_required_plugins.append(local_auto_update_ref)
            auto_update_seen = True
    else:
        normalized_required_plugins.append(ref)
if not auto_update_seen:
    normalized_required_plugins.append(local_auto_update_ref)
required_plugins = normalized_required_plugins

runtime_by_identity = {}
for ref in runtime.get("plugin", []):
    identity = managed_identity(ref)
    if identity:
        runtime_by_identity.setdefault(identity, []).append(ref)
ambiguous = sorted(identity for identity, refs in runtime_by_identity.items() if len(refs) != 1)
if ambiguous:
    print(f"error\tactive OpenCode config has ambiguous plugin identities: {','.join(ambiguous)}")
    raise SystemExit(0)

target_valid = False
current = {}
if target.exists() and not target.is_file():
    print(f"error\tTUI config path is not a regular file: {target}")
    raise SystemExit(0)
if target.is_file():
    try:
        current = json.loads(target.read_text(encoding="utf-8"))
        target_valid = isinstance(current, dict)
    except Exception as exc:
        print(f"error\tTUI config is invalid JSON; refusing automatic repair: {exc}")
        raise SystemExit(0)
    if not target_valid:
        print("error\tTUI config must be a JSON object")
        raise SystemExit(0)

# The installed OpenCode/CortexKit TUI uses this list as a UI-extension
# discovery surface. Preserve every existing TUI-only plugin, restore reviewed
# required entries, and replace only overlapping npm package refs with the exact
# version currently selected by the auto-updated opencode.json.
merged = deepcopy(current) if target_valid else {}
if "$schema" not in merged and isinstance(canonical.get("$schema"), str):
    merged["$schema"] = canonical["$schema"]

current_plugins = current.get("plugin") if target_valid else None
if current_plugins is not None and not isinstance(current_plugins, list):
    print("error\tTUI config plugin must be an array")
    raise SystemExit(0)
combined = list(current_plugins or []) + list(required_plugins)
if not all(isinstance(ref, str) and ref for ref in combined):
    print("error\tTUI config plugin entries must be non-empty strings")
    raise SystemExit(0)

effective_plugins = []
seen = set()
syncs = []
for ref in combined:
    identity = managed_identity(ref)
    key = ("package", identity) if identity else ("literal", ref)
    if key in seen:
        continue
    seen.add(key)
    runtime_refs = runtime_by_identity.get(identity, []) if identity else []
    effective = runtime_refs[0] if len(runtime_refs) == 1 else ref
    effective_plugins.append(effective)
    if effective != ref:
        syncs.append(f"{ref}->{effective}")
merged["plugin"] = effective_plugins

if target_valid and current == merged:
    print(f"clean\tTUI plugin surface is current ({len(effective_plugins)} entries)")
    raise SystemExit(0)

backup_dir = backup_root / run_id
backup_dir.mkdir(parents=True, exist_ok=True)
os.chmod(backup_dir, 0o700)
backup = backup_dir / "tui.json.before"
if target.exists():
    shutil.copy2(target, backup)
else:
    backup.write_text("<missing before recovery>\n", encoding="utf-8")

target.parent.mkdir(parents=True, exist_ok=True)
mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".tui.json.recovery.", dir=target.parent)
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

detail = f"; synchronized: {', '.join(syncs)}" if syncs else ""
print(f"repaired\t{backup}; TUI plugin surface restored ({len(effective_plugins)} entries){detail}")
PY_RECOVER_TUI
}

