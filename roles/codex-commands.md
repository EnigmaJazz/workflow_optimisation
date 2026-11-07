## Command policy (Codex)

Your sandbox is read-only and every command that is not on the allow list stops for a human
approval. Plan commands so you rarely need one.

Run without approval: `ls cat head tail wc stat file du tree realpath dirname basename sort uniq
cut tr diff cmp grep jq which date`, `git status|log|diff|show|rev-parse|rev-list|ls-files|
ls-tree|blame|merge-base|cat-file`, `git branch --list|--show-current`, `codegraph
status|query|explore|node|files|callers|callees|impact|affected`, and `orca orchestration
check|inbox|dispatch-show|worker-show|send|reply|ask`.

Always asks for approval: `sed`, `awk`, `find`, `xargs`, `env`, `rg`, `bash`/`sh` wrappers around
anything not listed above, `bun`, `node`, `python`, `curl`, any write, any `git` command that
mutates.

- Read a file range with `head -n <end> <file> | tail -n <count>`, or `cat -n <file>`. Never `sed -n`.
- Search with `grep -n`. Use CodeGraph (`codegraph explore`) before reading files broadly.
- Do not chain commands to dodge the list: a `bash -lc` that mixes allowed and unlisted commands
  asks as a whole.
- Review the diff and the code only. Do not run tests or builds: you review unapplied changes and the implementer reports its own results. Ask the dispatcher if a result is missing.
- Never write, stage, commit or edit. If a fix looks needed, report it with `file:line`.
