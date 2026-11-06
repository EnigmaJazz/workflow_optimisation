"""Mirror global-config/cli.json into the live OpenCode config directory (queue Q44).

usage: recover-cli-config.py <live-cli.json> <source-cli.json> <backup-root> <run-id>
Prints one line: clean|repaired|error <TAB> detail (the verifier's recovery protocol).

V2 migrates tui.json to cli.json on its first TUI start, copying V1-only plugins. The source file keeps the
`plugins` list under this repository's control; every key the source sets overrides the live file, and keys it
does not set (settings V2 writes itself) are preserved. An unreadable live file is backed up and replaced."""
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path


def main(argv):
    target, source, backup_root, run_id = Path(argv[1]), Path(argv[2]), Path(argv[3]), argv[4]
    try:
        wanted = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(wanted, dict):
            raise ValueError("not a JSON object")
    except (OSError, ValueError) as exc:
        print(f"error\tcannot read the cli.json source {source}: {exc}")
        return 0

    live_ok = False
    current = {}
    if target.exists():
        try:
            current = json.loads(target.read_text(encoding="utf-8"))
            live_ok = isinstance(current, dict)
        except (OSError, ValueError):
            live_ok = False
    merged = {**current, **wanted} if live_ok else dict(wanted)

    if live_ok and current == merged:
        print(f"clean\tcli.json is current ({len(wanted.get('plugins', []))} plugins)")
        return 0

    backup_dir = backup_root / run_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    backup = backup_dir / "cli.json.before"
    if target.exists():
        shutil.copy2(target, backup)
    else:
        backup.write_text("<missing before recovery>\n", encoding="utf-8")

    target.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE((target if target.exists() else source).stat().st_mode)
    fd, temp_name = tempfile.mkstemp(prefix=".cli.json.recovery.", dir=target.parent)
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
    print(f"repaired\t{backup}; cli.json mirrored from {source.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
