#!/usr/bin/env python3
"""Backport cortexkit/aft#1144 onto the installed @cortexkit/aft-opencode 0.62.0 plugin (queue Q44).

OpenCode 2.2.1+ rejects every AFT tool of 0.62.0 ("undefined is not an object (evaluating 'a.ref')", cortexkit/aft#1141): the host reads
a Standard JSON Schema converter from each tool's input, and 0.62.0 does not expose one. #1144 (plugin JavaScript only, no binary or
protocol change) adds it. 0.63.4 carries that fix but cannot start inside the V2 sandbox (docs/upstream/aft-storage-lease-root-open.md),
so V2 keeps the 0.62.0 plugin and binary and gets this one change applied to the installed copy.

    scripts/patch-aft-v2-schema.py PLUGIN_DIR [--apply]      # dry run unless --apply
    scripts/patch-aft-v2-schema.py --check PLUGIN_DIR        # exit 0 only if every target is patched

PLUGIN_DIR is the installed package directory (.../npm/@cortexkit/aft-opencode@0.62.0/<epoch>/node_modules/@cortexkit/aft-opencode). It
patches dist/index.js and dist/entry/server.js, which both bundle the function. It refuses any other package version and any file
whose function text is not exactly the 0.62.0 text, and a second run changes nothing. A reinstall of the plugin cache brings back the
unpatched files: run it again (and the verifier's V2 check reports it).
"""
import argparse
import json
import sys
from pathlib import Path

VERSION = "0.62.0"
TARGETS = ("dist/index.js", "dist/entry/server.js")
MARKER = "// aft#1144 backport (workflow_optimisation scripts/patch-aft-v2-schema.py)"

BEFORE = """  const currentInput = () => {
    const input = tool.schema.object(projectArguments(name, definition));
    assertV2Contract(hostName, input);
    return input;
  };
"""

AFTER = """  const currentInput = () => {
    const input = tool.schema.object(projectArguments(name, definition));
    assertV2Contract(hostName, input);
    """ + MARKER + """
    const toJSONSchema = (io, { target }) => {
      if (target !== "draft-2020-12") {
        throw new Error(`Unsupported JSON Schema target: ${target}`);
      }
      return tool.schema.toJSONSchema(input, { io, target: "draft-2020-12" });
    };
    return Object.assign(input, {
      "~standard": {
        ...input["~standard"],
        jsonSchema: {
          input: (options) => toJSONSchema("input", options),
          output: (options) => toJSONSchema("output", options)
        }
      }
    });
  };
"""


class PatchError(Exception):
    pass


def plan(plugin_dir):
    """-> [(path, new_text or None when already patched)]; raises PatchError on anything unexpected."""
    plugin_dir = Path(plugin_dir)
    package = plugin_dir / "package.json"
    if not package.is_file():
        raise PatchError(f"no package.json in {plugin_dir}")
    meta = json.loads(package.read_text())
    if meta.get("name") != "@cortexkit/aft-opencode" or meta.get("version") != VERSION:
        raise PatchError(f"{plugin_dir} is {meta.get('name')}@{meta.get('version')}, not @cortexkit/aft-opencode@{VERSION}")
    out = []
    for rel in TARGETS:
        path = plugin_dir / rel
        if not path.is_file():
            raise PatchError(f"missing {path}")
        text = path.read_text()
        if MARKER in text:
            if text.count(MARKER) != 1 or text.count(AFTER) != 1:
                raise PatchError(f"{path} carries the marker but not exactly the expected patch")
            out.append((path, None))
        elif text.count(BEFORE) == 1:
            out.append((path, text.replace(BEFORE, AFTER)))
        else:
            raise PatchError(f"{path} does not contain exactly one copy of the 0.{VERSION[2:]} function; refusing to patch an unknown build")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("plugin_dir")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true", help="exit 0 only if every target is already patched; writes nothing")
    args = ap.parse_args(argv)
    try:
        steps = plan(args.plugin_dir)
    except PatchError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    pending = [p for p, new in steps if new is not None]
    if args.check:
        print("patched" if not pending else "NOT patched: " + ", ".join(str(p) for p in pending))
        return 0 if not pending else 1
    if not pending:
        print("already patched; nothing to do")
        return 0
    for path, new in steps:
        if new is None:
            continue
        print(f"{'patching' if args.apply else 'would patch'} {path}")
        if args.apply:
            backup = path.with_name(path.name + f".orig-{VERSION}")
            if not backup.exists():
                backup.write_text(path.read_text())
            path.write_text(new)
    if not args.apply:
        print("dry run: nothing changed. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
