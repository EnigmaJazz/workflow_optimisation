# Public GitHub MCP in secure OpenCode

Use GitHub's `/mcp/readonly` endpoint with `repos,pull_requests,issues` and `X-MCP-Readonly: true`. The reviewed `opencode.json` disables its tools globally and enables them only for the read-only orchestrator, the read-only `explore` fallback, and output-only `sdd-research`. Systematic's `repo-research-analyst` does not receive GitHub tools: the installed Systematic config rejects `tools` under an agent overlay, and placing a same-name agent in `opencode.json` shadows its bundled persona. Give it attributed evidence from `explore` when useful. There is no installed `upstream-change-reviewer` persona. `sdd-explore` does not get GitHub tools; delegate external evidence to `sdd-research`.

## Credential

Create a **separate fine-grained GitHub PAT** with access to public repositories only, no private repositories selected, and no write permissions. Supply it through the secure service's host-managed environment as `GITHUB_REVIEW_TOKEN`. Do not put the token in OpenCode JSON, Git, prompts, worker briefs, or the verification output. The verifier checks the placeholder and the live MCP connection; only GitHub can attest the token's actual grants.

For Fish, enter the token without putting its value on the command line or in shell history:

```fish
set token_file ~/.config/opencode/github-review.env
set dropin_dir ~/.config/systemd/user/secure-opencode.service.d
mkdir -p "$dropin_dir"
read --silent --prompt-str 'Public-only GitHub token: ' github_review_token
printf 'GITHUB_REVIEW_TOKEN=%s\n' "$github_review_token" > "$token_file"
chmod 0600 "$token_file"
set -e github_review_token
printf '[Service]\nEnvironmentFile=%%h/.config/opencode/github-review.env\n' > "$dropin_dir/github-review.conf"
chmod 0644 "$dropin_dir/github-review.conf"
systemctl --user daemon-reload
systemctl --user restart secure-opencode.service
```

The service account must be able to reach `api.githubcopilot.com` through the existing Nono proxy policy. Approve only that host if the policy currently denies it; do not enable unrestricted egress or expose the token to tools. Review the sandbox worker's environment inheritance separately: putting a token in the OpenCode service environment by itself does not prove that child processes cannot inherit it.

Run `bash /home/james/ai-workspace/workflow_optimisation/verify-workflow.sh` after the restart. The `9a` section must report `github_ro` connected and section `9` must report scoped read tools with no mutation tool exposed. A disconnected server or blocked Nono egress is a failure, not a passing read-only check. `GET http://127.0.0.1:4096/mcp` is the direct status endpoint; avoid posting credentials or listing private repository contents as a probe.
