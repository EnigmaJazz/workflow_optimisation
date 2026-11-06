# Draft upstream issue: AFT 0.63.4 storage lease fails when `/` cannot be opened

Status: DRAFT, not filed. Filing publishes to a public tracker, so it is the owner's action.
Form: https://github.com/cortexkit/aft/issues/new?template=bug_report.yml (fields below match the form, in order).

Before filing: the form asks for the output of `npx @cortexkit/aft@latest doctor --issue` in the Diagnostics field. It was not run here (it downloads and executes a package). Run it yourself, outside the sandbox, review it for your username and paths, and paste it into Diagnostics. The manual values below can stay in the other fields.

---

## Short description

`aft` 0.63.4 exits with "cannot acquire storage lease ... Permission denied" under a Landlock sandbox that does not allow opening `/`

## What happened?

AFT 0.62.0 starts inside our Landlock-based sandbox (nono). AFT 0.63.4 exits during startup with:

```
[aft] cannot acquire storage lease for $HOME/.local/share/opencode-v2/data/cortexkit/aft: Permission denied (os error 13)
```

The storage directory itself is readable and writable under the sandbox (creating a file in it succeeds). The only failed file operation in the start-up trace is an open of the filesystem root:

```
openat(AT_FDCWD, "$HOME/.local/share/opencode-v2/data/cortexkit/aft", O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_DIRECTORY) = 4
openat(4, ".artifact-owner-locks", O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_DIRECTORY) = 5
statx(5, "", AT_STATX_SYNC_AS_STAT|AT_EMPTY_PATH, ...) = 0
openat(AT_FDCWD, "/", O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_DIRECTORY) = -1 EACCES (Permission denied)
```

The same binary starts normally outside the sandbox.

Expected: the lease is acquired, or an unreadable `/` does not stop it. A Landlock rule applies to a whole subtree, so allowing `open("/")` would mean granting read access to the entire filesystem, which defeats the sandbox. Sandboxed hosts of AFT cannot run 0.63.4, and cannot move to OpenCode 2.2.1+ either, because 0.62.0 does not register tools there (#1141, fixed in #1144).

Where it probably comes from (not confirmed): `hold_process_storage_lease` in `crates/aft/src/main.rs` calls `root_cache::acquire_daemon_storage_lease` and exits on any error. The ancestor walk in `crates/aft/src/private_storage.rs` (for example `tighten_sqlite_file`) starts from `open("/")` with `O_NOFOLLOW|O_DIRECTORY`. I did not confirm which call in the lease path reaches `open("/")`; the trace shows only the failing call.

Possible fixes: walk from a directory descriptor the process already holds (the storage root), or treat `EACCES` on `/` as "ancestor check unavailable" and continue with a log line.

Reproduction:
1. Run `aft` under a Landlock profile that grants the storage directory read/write but not `/`.
2. Observe the exit with the message above.
3. Run the same binary without the sandbox: it starts.

## Diagnostics

(paste the output of `npx @cortexkit/aft@latest doctor --issue` here)

## Plugin version

0.63.4 (`@cortexkit/aft-opencode@~0.63.4`; 0.62.0 does not hit this)

## AFT binary version

0.63.4

## Platform

linux x64 (kernel 7.0), nono 0.73.0 and 0.74.0 as the Landlock sandbox (the trace was taken with 0.74.0, the live server runs 0.73.0), host OpenCode V2 2.2.0

## Log output (optional)

```
[aft-plugin] [aft] cannot acquire storage lease for $HOME/.local/share/opencode-v2/data/cortexkit/aft: Permission denied (os error 13)
[aft-plugin] Process exited: code=1, signal=null
[aft-plugin] Binary crashed (restarts: 3).
[aft-plugin] Max restarts (3) reached, giving up.
```

(username and home path replaced with `$HOME`)
