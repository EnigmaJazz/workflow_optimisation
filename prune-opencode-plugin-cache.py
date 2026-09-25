#!/usr/bin/env python3
"""Safely prune health-approved, obsolete OpenCode plugin package caches.

Dry-run is the default. Use --apply to delete candidates. This utility is
designed for a timer, not as an OpenCode service start/stop hook.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


EXACT_VERSION = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?"
    r"(?:\+[0-9A-Za-z.-]+)?$"
)


@dataclass(frozen=True)
class CacheEntry:
    package: str
    version: str
    root: Path
    modified: float
    size: int


class SafetyRefusal(RuntimeError):
    """Expected fail-closed condition; scheduled cleanup should skip cleanly."""


def parse_args() -> argparse.Namespace:
    home = Path.home()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=home / ".config" / "opencode",
        help="OpenCode configuration directory",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=home / ".cache" / "opencode",
        help="OpenCode cache directory",
    )
    parser.add_argument(
        "--keep-rollback",
        type=int,
        default=1,
        help="additional recent non-active versions to preserve per plugin",
    )
    parser.add_argument(
        "--minimum-age-days",
        type=float,
        default=14,
        help="never delete a cache tree modified more recently than this",
    )
    parser.add_argument(
        "--approval-file",
        type=Path,
        default=home
        / "ai-workspace"
        / "workflow_optimisation"
        / ".atl"
        / "opencode-cache-prune-approval.json",
        help="recent safety manifest written by a successful workflow verification",
    )
    parser.add_argument(
        "--approval-max-age-days",
        type=float,
        default=30,
        help="refuse cleanup when the last successful health approval is older",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="delete validated candidates; otherwise perform a dry-run",
    )
    args = parser.parse_args()
    if args.keep_rollback < 0:
        parser.error("--keep-rollback must be zero or greater")
    if args.minimum_age_days < 0:
        parser.error("--minimum-age-days must be zero or greater")
    if args.approval_max_age_days <= 0:
        parser.error("--approval-max-age-days must be greater than zero")
    return args


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot safely read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"expected a JSON object in {path}")
    return value


def split_plugin_reference(reference: str) -> tuple[str, str | None]:
    """Return (package identity, exact version or None)."""
    if reference.startswith("@"):
        separator = reference.rfind("@")
        if separator <= reference.find("/"):
            return reference, None
    else:
        separator = reference.rfind("@")
        if separator <= 0:
            return reference, None
    package = reference[:separator]
    version = reference[separator + 1 :]
    return package, version if EXACT_VERSION.fullmatch(version) else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def configured_plugins(
    config_dir: Path,
) -> tuple[set[str], dict[str, set[str]], list[str], dict[str, str]]:
    identities: set[str] = set()
    active_versions: dict[str, set[str]] = {}
    references: set[str] = set()
    config_sha256: dict[str, str] = {}
    found_config = False
    for name in ("opencode.json", "tui.json"):
        path = config_dir / name
        if not path.exists():
            continue
        found_config = True
        config_sha256[name] = sha256_file(path)
        data = load_json(path)
        config_references = data.get("plugin", [])
        if config_references is None:
            config_references = []
        if not isinstance(config_references, list):
            raise RuntimeError(f"expected {path}: plugin to be an array")
        for reference in config_references:
            if not isinstance(reference, str):
                raise RuntimeError(f"expected plugin references in {path} to be strings")
            references.add(reference)
            package, exact_version = split_plugin_reference(reference)
            identities.add(package)
            if exact_version:
                active_versions.setdefault(package, set()).add(exact_version)
    if not found_config:
        raise RuntimeError(
            f"neither opencode.json nor tui.json exists below {config_dir}"
        )
    return identities, active_versions, sorted(references), config_sha256


def validate_approval(
    approval_file: Path,
    references: list[str],
    config_sha256: dict[str, str],
    maximum_age_days: float,
) -> None:
    try:
        approval = json.loads(approval_file.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SafetyRefusal(
            f"health approval is missing: {approval_file}; run verify-workflow.sh successfully first"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot safely read health approval {approval_file}: {exc}") from exc
    if not isinstance(approval, dict) or approval.get("schema") != "workflow.cache-prune-approval/v1":
        raise SafetyRefusal("health approval has an unsupported schema")
    approved_at = approval.get("approved_at_epoch")
    if not isinstance(approved_at, int) or approved_at <= 0:
        raise SafetyRefusal("health approval has no valid approval time")
    age_seconds = time.time() - approved_at
    if age_seconds < -300 or age_seconds > maximum_age_days * 86400:
        raise SafetyRefusal(
            f"health approval is not recent enough ({age_seconds / 86400:.1f} days old)"
        )
    if approval.get("config_sha256") != config_sha256:
        raise SafetyRefusal("OpenCode/TUI configuration changed after health approval")
    if approval.get("plugin_references") != references:
        raise SafetyRefusal("plugin references changed after health approval")
    verifier_path_value = approval.get("verifier_path")
    verifier_sha256 = approval.get("verifier_sha256")
    if not isinstance(verifier_path_value, str) or not isinstance(verifier_sha256, str):
        raise SafetyRefusal("health approval has no verifier identity")
    verifier_path = Path(verifier_path_value)
    if not verifier_path.is_file() or sha256_file(verifier_path) != verifier_sha256:
        raise SafetyRefusal("workflow verifier changed after health approval")


def ancestor_pids() -> set[int]:
    result: set[int] = set()
    pid = os.getpid()
    while pid > 1 and pid not in result:
        result.add(pid)
        try:
            fields = Path(f"/proc/{pid}/stat").read_text().split()
            pid = int(fields[3])
        except (FileNotFoundError, OSError, IndexError, ValueError):
            break
    return result


def process_start_epoch(pid: int) -> float:
    stat_text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    close = stat_text.rfind(")")
    if close < 0:
        raise RuntimeError(f"cannot parse process metadata for pid {pid}")
    fields_after_comm = stat_text[close + 2 :].split()
    start_ticks = int(fields_after_comm[19])
    boot_time = None
    for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines():
        if line.startswith("btime "):
            boot_time = int(line.split()[1])
            break
    if boot_time is None:
        raise RuntimeError("cannot read system boot time")
    return boot_time + start_ticks / os.sysconf("SC_CLK_TCK")


def process_environment(pid: int) -> dict[str, str]:
    try:
        raw = Path(f"/proc/{pid}/environ").read_bytes()
    except (FileNotFoundError, PermissionError, OSError) as exc:
        raise RuntimeError(f"cannot inspect OpenCode pid {pid} environment") from exc
    result: dict[str, str] = {}
    for item in raw.split(b"\0"):
        if b"=" not in item:
            continue
        key, value = item.split(b"=", 1)
        result[key.decode(errors="replace")] = value.decode(errors="replace")
    return result


def process_config_dir(pid: int, environment: dict[str, str]) -> Path:
    if environment.get("OPENCODE_CONFIG_CONTENT"):
        raise SafetyRefusal(f"OpenCode pid {pid} uses inline configuration")
    explicit_dir = environment.get("OPENCODE_CONFIG_DIR")
    if explicit_dir:
        return Path(explicit_dir).expanduser().resolve()
    explicit_file = environment.get("OPENCODE_CONFIG")
    if explicit_file:
        path = Path(explicit_file).expanduser().resolve()
        return path if path.is_dir() else path.parent
    xdg = environment.get("XDG_CONFIG_HOME")
    if xdg:
        return (Path(xdg).expanduser() / "opencode").resolve()
    home = environment.get("HOME")
    if not home:
        raise SafetyRefusal(f"cannot establish configuration home for OpenCode pid {pid}")
    return (Path(home).expanduser() / ".config" / "opencode").resolve()


def process_cache_dir(pid: int, environment: dict[str, str]) -> Path:
    explicit_dir = environment.get("OPENCODE_CACHE_DIR")
    if explicit_dir:
        return Path(explicit_dir).expanduser().resolve()
    xdg = environment.get("XDG_CACHE_HOME")
    if xdg:
        return (Path(xdg).expanduser() / "opencode").resolve()
    home = environment.get("HOME")
    if not home:
        raise SafetyRefusal(f"cannot establish cache home for OpenCode pid {pid}")
    return (Path(home).expanduser() / ".cache" / "opencode").resolve()


def config_mtime(config_dir: Path) -> float:
    paths = [
        config_dir / name
        for name in ("opencode.json", "tui.json")
        if (config_dir / name).is_file()
    ]
    if not paths:
        raise SafetyRefusal(
            f"running OpenCode configuration has no opencode.json or tui.json: {config_dir}"
        )
    return max(path.stat().st_mtime for path in paths)


def validate_running_opencode_processes(
    config_dir: Path,
    cache_dir: Path,
) -> tuple[list[int], dict[str, set[str]], set[str], list[str]]:
    """Validate known runtimes and return additional cache protections.

    secure-opencode must use the health-approved configuration.  ai-proxy is a
    separate OpenChamber runtime and may intentionally use another config.  If
    it shares this cache, protect every exact version selected by its config;
    for an unpinned plugin, protect every cached version of that package.
    """
    proc = Path("/proc")
    if not proc.is_dir():
        raise RuntimeError("cannot inspect running processes on this platform")
    excluded = ancestor_pids()
    allowed_units = {"secure-opencode.service", "ai-proxy.service"}
    newest_config_mtime = config_mtime(config_dir)
    validated: list[int] = []
    protected_versions: dict[str, set[str]] = {}
    protect_all_versions: set[str] = set()
    notes: list[str] = []
    for item in proc.iterdir():
        if not item.name.isdigit():
            continue
        pid = int(item.name)
        if pid in excluded:
            continue
        try:
            raw = (item / "cmdline").read_bytes()
        except (FileNotFoundError, PermissionError, OSError):
            continue
        args = [part.decode(errors="replace") for part in raw.split(b"\0") if part]
        launchers = [Path(arg).name.lower() for arg in args[:2]]
        if not any(
            name in {"opencode", "opencode.exe"}
            or name.startswith("start-secure-opencode")
            for name in launchers
        ):
            continue
        try:
            cgroup = (item / "cgroup").read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError, OSError) as exc:
            raise RuntimeError(f"cannot inspect cgroup for OpenCode pid {pid}") from exc
        matching_units = [unit for unit in allowed_units if f"/{unit}" in cgroup]
        if not matching_units:
            raise SafetyRefusal(
                f"unrecognized OpenCode pid {pid} is running; close standalone TUI/headless sessions"
            )
        unit = matching_units[0]
        environment = process_environment(pid)
        runtime_cache_dir = process_cache_dir(pid, environment)
        if runtime_cache_dir != cache_dir:
            notes.append(
                f"ignored {unit} pid {pid}: separate cache {runtime_cache_dir}"
            )
            continue
        runtime_config_dir = process_config_dir(pid, environment)
        if unit == "secure-opencode.service" and runtime_config_dir != config_dir:
            raise SafetyRefusal(
                f"secure OpenCode pid {pid} uses config {runtime_config_dir}, "
                f"not health-approved {config_dir}"
            )
        runtime_config_mtime = (
            newest_config_mtime
            if runtime_config_dir == config_dir
            else config_mtime(runtime_config_dir)
        )
        if process_start_epoch(pid) + 2 < runtime_config_mtime:
            raise SafetyRefusal(
                f"{unit} pid {pid} predates its config {runtime_config_dir}; "
                f"restart that service first"
            )
        if runtime_config_dir != config_dir:
            identities, versions, _, _ = configured_plugins(runtime_config_dir)
            for package, selected in versions.items():
                protected_versions.setdefault(package, set()).update(selected)
            protect_all_versions.update(identities - versions.keys())
            notes.append(
                f"protected plugin selections for {unit} pid {pid} using {runtime_config_dir}"
            )
        validated.append(pid)
    return sorted(validated), protected_versions, protect_all_versions, notes


def cache_root_spec(packages_root: Path, candidate: Path) -> tuple[str, str] | None:
    """Parse only direct version-addressed cache roots in the known layout."""
    try:
        relative = candidate.relative_to(packages_root)
    except ValueError:
        return None
    parts = relative.parts
    if len(parts) == 1 and not parts[0].startswith("@"):
        leaf = parts[0]
        split_at = leaf.rfind("@")
        if split_at <= 0:
            return None
        package, version = leaf[:split_at], leaf[split_at + 1 :]
    elif len(parts) == 2 and parts[0].startswith("@"):
        leaf = parts[1]
        split_at = leaf.rfind("@")
        if split_at <= 0:
            return None
        package = f"{parts[0]}/{leaf[:split_at]}"
        version = leaf[split_at + 1 :]
    else:
        return None
    if not EXACT_VERSION.fullmatch(version):
        return None
    return package, version


def expected_manifest(root: Path, package: str) -> Path:
    return root / "node_modules" / Path(*package.split("/")) / "package.json"


def directory_size(root: Path) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [
            name for name in dirnames if not (Path(dirpath) / name).is_symlink()
        ]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                total += path.lstat().st_size
            except FileNotFoundError:
                pass
    return total


def validate_entry(packages_root: Path, root: Path) -> CacheEntry | None:
    if root.is_symlink() or not root.is_dir():
        return None
    parsed = cache_root_spec(packages_root, root)
    if not parsed:
        return None
    package, version = parsed
    manifest = expected_manifest(root, package)
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        resolved_root = root.resolve(strict=True)
        resolved_packages = packages_root.resolve(strict=True)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    if resolved_root.parent != resolved_packages and resolved_root.parent.parent != resolved_packages:
        return None
    if data.get("name") != package or data.get("version") != version:
        return None
    stat = root.stat()
    return CacheEntry(package, version, root, stat.st_mtime, directory_size(root))


def discover_entries(packages_root: Path, identities: set[str]) -> list[CacheEntry]:
    entries: list[CacheEntry] = []
    if not packages_root.is_dir() or packages_root.is_symlink():
        return entries
    for first in packages_root.iterdir():
        if first.is_symlink() or not first.is_dir():
            continue
        if first.name.startswith("@"):
            candidates: Iterable[Path] = first.iterdir()
        else:
            candidates = (first,)
        for candidate in candidates:
            entry = validate_entry(packages_root, candidate)
            if entry and entry.package in identities:
                entries.append(entry)
    return entries


def prerelease_key(value: str | None) -> tuple:
    if value is None:
        return (1,)
    parts: list[tuple[int, object]] = []
    for token in value.split("."):
        parts.append((0, int(token)) if token.isdigit() else (1, token))
    return (0, *parts)


def version_key(version: str) -> tuple:
    match = EXACT_VERSION.fullmatch(version)
    if not match:
        return (-1, -1, -1, (0,))
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        prerelease_key(match.group("pre")),
    )


def select_candidates(
    entries: list[CacheEntry],
    active_versions: dict[str, set[str]],
    keep_rollback: int,
    minimum_age_days: float,
    protect_all_versions: set[str] | None = None,
) -> tuple[list[CacheEntry], dict[str, set[str]]]:
    protect_all_versions = protect_all_versions or set()
    grouped: dict[str, list[CacheEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.package, []).append(entry)
    preserved: dict[str, set[str]] = {}
    candidates: list[CacheEntry] = []
    cutoff = time.time() - minimum_age_days * 86400
    for package, package_entries in grouped.items():
        newest_first = sorted(
            package_entries, key=lambda item: version_key(item.version), reverse=True
        )
        if package in protect_all_versions:
            preserved[package] = {entry.version for entry in package_entries}
            continue
        keep = set(active_versions.get(package, set()))
        non_active = [entry for entry in newest_first if entry.version not in keep]
        if keep:
            keep.update(entry.version for entry in non_active[:keep_rollback])
        else:
            # For an unpinned config, preserve the likely active version plus rollbacks.
            keep.update(
                entry.version for entry in non_active[: keep_rollback + 1]
            )
        preserved[package] = keep
        for entry in package_entries:
            if entry.version not in keep and entry.modified <= cutoff:
                candidates.append(entry)
    candidates.sort(key=lambda item: (item.package, version_key(item.version)))
    return candidates, preserved


def format_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if amount < 1024 or unit == "TiB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{value} B"


def main() -> int:
    args = parse_args()
    config_dir = args.config_dir.expanduser().resolve()
    cache_dir = args.cache_dir.expanduser().resolve()
    packages_root = cache_dir / "packages"

    update_lock = config_dir / ".auto-update.lock"
    if update_lock.exists():
        print(f"skip: auto-update lock exists: {update_lock}")
        return 0

    cache_dir.mkdir(parents=True, exist_ok=True)
    lock_path = cache_dir / ".plugin-cache-prune.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("skip: another cache prune is running")
            return 0

        identities, active_versions, references, config_sha256 = configured_plugins(
            config_dir
        )
        validate_approval(
            args.approval_file.expanduser().resolve(),
            references,
            config_sha256,
            args.approval_max_age_days,
        )
        print("ok: recent matching workflow-health approval validated")
        (
            validated_pids,
            runtime_versions,
            protect_all_versions,
            runtime_notes,
        ) = validate_running_opencode_processes(config_dir, cache_dir)
        for package, versions in runtime_versions.items():
            active_versions.setdefault(package, set()).update(versions)
        for note in runtime_notes:
            print(f"ok: {note}")
        if validated_pids:
            print(
                "ok: known OpenCode service process(es) are cache-safe: "
                + ", ".join(map(str, validated_pids))
            )
        else:
            print("ok: no running OpenCode process needs protection")
        entries = discover_entries(packages_root, identities)
        candidates, preserved = select_candidates(
            entries,
            active_versions,
            args.keep_rollback,
            args.minimum_age_days,
            protect_all_versions,
        )

        print(
            f"managed plugins: {len(set(entry.package for entry in entries))}; "
            f"validated cache versions: {len(entries)}"
        )
        for package in sorted(preserved):
            versions = ", ".join(sorted(preserved[package], key=version_key, reverse=True))
            print(f"keep: {package}: {versions or '<none found>'}")

        reclaimable = sum(entry.size for entry in candidates)
        if not candidates:
            print("ok: no eligible stale cache versions")
            return 0

        action = "delete" if args.apply else "would delete"
        for entry in candidates:
            age_days = (time.time() - entry.modified) / 86400
            print(
                f"{action}: {entry.root} "
                f"({entry.package}@{entry.version}, {format_bytes(entry.size)}, {age_days:.1f} days old)"
            )

        if not args.apply:
            print(
                f"dry-run: {len(candidates)} version(s), {format_bytes(reclaimable)} reclaimable; "
                "rerun with --apply"
            )
            return 0

        deleted = 0
        reclaimed = 0
        for entry in candidates:
            if update_lock.exists():
                raise SafetyRefusal(f"auto-update lock appeared during cleanup: {update_lock}")
            _, _, current_references, current_sha256 = configured_plugins(config_dir)
            if current_references != references or current_sha256 != config_sha256:
                raise SafetyRefusal("OpenCode/TUI configuration changed during cleanup")
            # Revalidate immediately before each irreversible operation.
            current = validate_entry(packages_root, entry.root)
            if current != entry:
                print(f"refuse: cache tree changed during scan: {entry.root}", file=sys.stderr)
                continue
            shutil.rmtree(entry.root)
            deleted += 1
            reclaimed += entry.size
            parent = entry.root.parent
            if parent.name.startswith("@"):
                try:
                    parent.rmdir()
                except OSError:
                    pass
        print(f"pruned: {deleted} version(s), approximately {format_bytes(reclaimed)} reclaimed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SafetyRefusal as exc:
        print(f"skip: {exc}")
        raise SystemExit(0)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
