# Draft upstream issue: AFT 0.63.4 exits under a filesystem sandbox because the storage lease opens `/`

Status: DRAFT, not filed. Filing is the owner's decision (it publishes to a public tracker).
Target: https://github.com/cortexkit/aft (issues)

## Title

`aft` 0.63.4 exits with "cannot acquire storage lease ... Permission denied" when the process cannot open `/` (Landlock sandbox)

## Summary

AFT 0.62.0 starts inside our Landlock-based sandbox (nono). AFT 0.63.4 exits during startup:

```
[aft] cannot acquire storage lease for $HOME/.local/share/opencode-v2/data/cortexkit/aft: Permission denied (os error 13)
```

The storage directory itself is readable and writable under the sandbox (a `touch` inside it succeeds). The only failed syscall in the start-up trace is an open of the filesystem root:

```
openat(AT_FDCWD, "$HOME/.local/share/opencode-v2/data/cortexkit/aft", O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_DIRECTORY) = 4
openat(4, ".artifact-owner-locks", O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_DIRECTORY) = 5
statx(5, "", AT_STATX_SYNC_AS_STAT|AT_EMPTY_PATH, ...) = 0
openat(AT_FDCWD, "/", O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_DIRECTORY) = -1 EACCES (Permission denied)
```

The same binary starts normally outside the sandbox.

## Why this is a problem

A Landlock rule applies to a directory subtree. Allowing `open("/")` means granting read access to the entire filesystem, which defeats the sandbox. Sandboxed hosts of AFT (here: an OpenCode V2 server confined by nono, with the AFT plugin running inside it) therefore cannot run 0.63.4, and cannot move to OpenCode 2.2.1+ either, because 0.62.0 does not register tools there (#1141, fixed in #1144).

## Where it probably comes from

`crates/aft/src/main.rs` `hold_process_storage_lease` calls `root_cache::acquire_daemon_storage_lease`, which exits the process on any error. The hardening in `crates/aft/src/private_storage.rs` (for example `tighten_sqlite_file`) walks every ancestor of a path starting from `open("/")` with `O_NOFOLLOW|O_DIRECTORY`. We have not confirmed which call site in the lease path reaches `open("/")`; the trace above only shows the failing call.

## Expected behaviour

Either of:

1. Walk from a directory descriptor the process already holds (the storage root, which `tighten_within` already pins), not from `/`.
2. Treat `EACCES` on `/` as "ancestor check unavailable" and continue, with a log line, instead of failing the lease and exiting.

## Environment

- AFT 0.63.4 (`aft` binary from the versioned cache), Linux 7.0, x86_64
- Sandbox: nono 0.73.0 and 0.74.0 (Landlock; the trace was taken with 0.74.0, the live server runs 0.73.0); data and cache directories granted read/write, `/` not granted
- Host: OpenCode V2 2.2.0 with `@cortexkit/aft-opencode@~0.63.4`

## Reproduction

1. Run `aft` under a Landlock profile that grants the storage directory read/write but not `/`.
2. Observe the exit with the message above.
3. Run the same binary without the sandbox: it starts.

## Not included

No credentials or session data. Paths are shown with `$HOME`.
