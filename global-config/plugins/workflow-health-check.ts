/**
 * workflow-health-check
 *
 * Runs the workflow setup health check when OpenCode starts and surfaces a
 * warning into the session system prompt when any global piece of the
 * gentle-ai + Systematic workflow setup is broken or was auto-repaired:
 *   - receipt-driven review mode (RDD) is off
 *   - skill symlinks resolve to a stale/missing Systematic install
 *   - the routing section in the global AGENTS.md was removed by a sync
 *
 * The check runs the self-healing script (verify-workflow.sh), which repairs
 * symlinks and the AGENTS.md section automatically. This plugin's job is only
 * to notice when the script could NOT repair something (or RDD is off) and to
 * make sure the agent in every session knows about it.
 *
 * Persistence: this file is user-owned and auto-loaded from
 * ~/.config/opencode/plugins/ (no opencode.json entry needed). gentle-ai
 * updates only rewrite its own AGENTS.md markers and agent prompts; they never
 * touch this directory, so the enforcement survives both opencode and
 * gentle-ai updates.
 */

import type { Plugin } from "@opencode-ai/plugin"
import { execFile } from "child_process"
import { promisify } from "util"

const execFileAsync = promisify(execFile)

const VERIFY_SCRIPT = "/home/james/ai-workspace/workflow_optimisation/verify-workflow.sh"
const VERIFY_TIMEOUT_MS = 60_000

// Pinned sha256 digest of the reviewed verify-workflow.sh. The plugin refuses
// to execute a script that does not match this digest, so startup execution is
// always the reviewed artifact: tampering with the repository script fails
// closed (no execution, FAILED banner) instead of running arbitrary code as
// the user. Updating the script is a reviewed-pipeline step: edit
// verify-workflow.sh, recompute with `sha256sum verify-workflow.sh`, update
// this pin, run the RDD review on the plugin source, then re-mirror.
const VERIFY_SCRIPT_SHA256 = "07c40b971fd088f304826a0343242e760844137c22d0f11ac38933c845d751b3"

interface HealthResult {
  ok: boolean
  tail: string
}

// Module-level cache: check once per process, inject the result into every
// session's system prompt so the warning is visible regardless of when the
// check completes relative to session start.
let health: HealthResult | null = null
let checkStarted = false

async function verifyScriptIntegrity(): Promise<boolean> {
  try {
    const { stdout } = await execFileAsync("sha256sum", [VERIFY_SCRIPT])
    return stdout.trim().split(/\s+/)[0] === VERIFY_SCRIPT_SHA256
  } catch {
    return false
  }
}

async function runHealthCheck(): Promise<void> {
  if (!(await verifyScriptIntegrity())) {
    health = {
      ok: false,
      tail: `verify-workflow.sh does not match the reviewed digest ${VERIFY_SCRIPT_SHA256}; refusing to execute.`,
    }
    console.error("[workflow-health-check] script digest mismatch — refusing to execute")
    return
  }
  try {
    const { stdout } = await execFileAsync("bash", [VERIFY_SCRIPT], {
      timeout: VERIFY_TIMEOUT_MS,
    })
    const output = stdout.trim()
    // execFileAsync resolves only when the script exits 0, and verify-workflow.sh
    // exits 0 only when every check passed — so a resolved call is success, with
    // no string coupling to the script's success echo.
    health = { ok: true, tail: output.split("\n").slice(-12).join("\n") }
    console.log("[workflow-health-check] all checks passed")
  } catch (err) {
    const e = err as { stdout?: string; stderr?: string; message?: string }
    const detail = (e.stdout ?? "") + (e.stderr ?? "")
    health = {
      ok: false,
      tail: (detail.trim() || e.message || String(err)).split("\n").slice(-12).join("\n"),
    }
    console.error("[workflow-health-check] check failed to complete:", e.message ?? err)
  }
}

export const WorkflowHealthCheckPlugin: Plugin = async () => {
  if (!checkStarted) {
    checkStarted = true
    // Don't await — keep OpenCode startup responsive. The script is cheap
    // (cached registry refresh, no network).
    runHealthCheck().catch((err) => {
      console.error("[workflow-health-check] unexpected error:", err)
    })
  }

  return {
    "experimental.chat.system.transform": async (
      _input: unknown,
      output: { system?: string[] },
    ) => {
      if (!health || health.ok) return
      if (!Array.isArray(output.system)) return
      output.system.push(
        [
          "## Workflow health check FAILED",
          "The global gentle-ai + Systematic workflow setup has a problem that the startup check could not fully repair. Run `bash " +
            VERIFY_SCRIPT +
            "` and offer the user the result; if RDD is off, re-enable it with `gentle-ai review mode enable --scope global`.",
          "```",
          health.tail,
          "```",
        ].join("\n"),
      )
    },
  }
}

export default WorkflowHealthCheckPlugin
