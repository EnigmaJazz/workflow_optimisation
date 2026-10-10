/**
 * workflow-health-check
 *
 * Startup health monitor for the user's global Gentle AI + Systematic workflow.
 *
 * The reviewed verifier (`verify-workflow.sh`) is the source of truth for the
 * setup health check. It currently verifies and, where explicitly safe, repairs:
 *   - Gentle AI v3.5.0+, mandatory ODD delegation, optional SDD research/verification,
 *     the effective user-owned RDD mode/source, successful sync witness,
 *     and telemetry status are verified
 *   - required Systematic v3.18.4+ bundled skills exist in the active install
 *   - DeepSeek V4.1 Flash primary/fallback and multimodal frontend policy is intact
 *   - obsolete duplicate Systematic skill symlinks are removed
 *   - the compact global AGENTS.md router and four recovered skills are present
 *   - the canonical user-owned secure ODD routing override is present,
 *     whether or not sync generated its separate native ODD prose
 *   - user-owned opencode.json and AGENTS.md overlays overwritten by a
 *     Gentle AI sync are restored atomically after timestamped backups while
 *     allowlisted auto-updated plugin version pins, including Systematic and
 *     Magic Context, remain current
 *   - the installed TUI's plugin discovery list is recovered after backup;
 *     TUI-only integrations remain present while overlapping package refs are
 *     synchronized to the auto-updated versions selected by opencode.json
 *   - accidental rollback of systematic.jsonc security/memory/model overlays
 *     and the mapped fallback policy is recovered from reviewed sources
 *   - the gentle-ai skill registry refresh succeeds
 *   - reviewed workflow plugins are mirrored into ~/.config/opencode/plugins
 *   - this plugin pins the exact reviewed verifier digest
 *   - the Systematic routing guard is deployed and the obsolete tiering plugin
 *     remains disabled
 *   - the Astra Sol-upgrade plugin is mirrored and its derived runtime aliases
 *     preserve each eligible Sol agent's tools and effective permission authority
 *   - workflow recipe / requirements / routing invariants remain consistent
 *   - systematic.jsonc covers the current bundled Systematic agent inventory
 *   - the exact configured Magic Context package is materialized in cache
 *   - other Magic Context cache trees are reported but never deleted while
 *     another process or project may still reference them
 *   - OpenCode's resolved Systematic agent model/variant allocation matches
 *     systematic.jsonc, using a recursion-safe neutral runtime probe
 *   - output-only SDD research and retired SDD host operations stay denied
 *   - runtime content hashes are certified against a systemd service invocation,
 *     avoiding false restart loops when startup code rewrites unchanged files
 *
 * This plugin runs the verifier once per OpenCode process and injects status into
 * session system prompts only when attention is useful:
 *   - FAILED: the verifier could not establish/repair a healthy setup
 *   - SELF-REPAIRED: the verifier repaired one or more artifacts successfully;
 *     the current OpenCode process may still have pre-repair plugin/skill state,
 *     so the user should restart OpenCode before relying on the repaired setup
 *   - CLEAN: no injected message
 *
 * Recursion guard:
 *   verify-workflow.sh runs `opencode debug config` to inspect the effective
 *   runtime agent configuration. That child OpenCode process loads local plugins,
 *   including this one. The verifier sets WORKFLOW_HEALTH_CHECK_PROBE=1 for the
 *   child process; this plugin must return immediately in that mode or startup
 *   would recurse: OpenCode -> verifier -> OpenCode -> verifier -> ...
 *
 * Integrity:
 *   The SHA256 below pins the exact reviewed verify-workflow.sh artifact. If the
 *   script changes without the pin being updated, this plugin refuses to execute
 *   it and reports a failed health check. Updating the verifier is therefore a
 *   reviewed-pipeline operation:
 *
 *     1. Edit/review verify-workflow.sh.
 *     2. Compute `sha256sum verify-workflow.sh`.
 *     3. Update VERIFY_SCRIPT_SHA256 below.
 *     4. Review this plugin source.
 *     5. Run verify-workflow.sh manually; it mirrors reviewed plugin sources.
 *     6. Restart OpenCode.
 *
 * Persistence:
 *   The reviewed source lives under the workflow_optimisation workspace and is
 *   mirrored to ~/.config/opencode/plugins/workflow-health-check.ts by the
 *   verifier. OpenCode auto-loads local plugins from that directory; no explicit
 *   opencode.json plugin entry is required.
 */

import type { Plugin } from "@opencode-ai/plugin"
import { execFile } from "child_process"
import { promisify } from "util"

const execFileAsync = promisify(execFile)

const VERIFY_SCRIPT = "/home/james/ai-workspace/workflow_optimisation/verify-workflow.sh"
// Runtime alias equivalence checks probe multiple agents in bounded parallel
// batches; keep the asynchronous startup monitor tolerant of a cold plugin cache.
const VERIFY_TIMEOUT_MS = 300_000

// Pinned sha256 digest of the reviewed verify-workflow.sh. Keep this assignment
// on one line: verify-workflow.sh deliberately parses this source line to confirm
// that the reviewed plugin and verifier are bound to one another.
const VERIFY_SCRIPT_SHA256 = "38c5dbfaebc3bc0d1493afac1916022fba9cfb0bdbbbb15aa62b9e3986b46674";

type HealthState = "clean" | "repaired" | "failed"

interface HealthResult {
  state: HealthState
  tail: string
}

// Module-level cache: run once per OpenCode process. The result is injected on
// subsequent system-prompt transforms, so every session can see a persistent
// failure/repair notice without rerunning the verifier per turn.
let health: HealthResult | null = null
let checkStarted = false

function tailLines(text: string, count = 16): string {
  return text.trim().split("\n").slice(-count).join("\n")
}

async function verifyScriptIntegrity(): Promise<boolean> {
  try {
    const { stdout } = await execFileAsync("sha256sum", [VERIFY_SCRIPT])
    return stdout.trim().split(/\s+/)[0]?.toLowerCase() === VERIFY_SCRIPT_SHA256
  } catch {
    return false
  }
}

async function runHealthCheck(): Promise<void> {
  if (!(await verifyScriptIntegrity())) {
    health = {
      state: "failed",
      tail:
        `verify-workflow.sh does not match the reviewed digest ${VERIFY_SCRIPT_SHA256}; ` +
        "refusing to execute it.",
    }
    console.error(
      "[workflow-health-check] verifier digest mismatch — refusing to execute",
    )
    return
  }

  try {
    const { stdout, stderr } = await execFileAsync("bash", [VERIFY_SCRIPT], {
      timeout: VERIFY_TIMEOUT_MS,
      maxBuffer: 1024 * 1024,
      env: process.env,
    })

    // verify-workflow.sh exits 0 only when every check passes. It explicitly
    // marks the success banner when self-repairs were applied, which lets us
    // distinguish a clean startup from a repaired one without coupling to the
    // individual repair messages.
    const output = [stdout, stderr].filter(Boolean).join("\n").trim()
    const repaired = output.includes(
      "== All checks passed — workflow setup intact (self-repairs applied) ==",
    )

    health = {
      state: repaired ? "repaired" : "clean",
      tail: tailLines(output),
    }

    if (repaired) {
      console.warn(
        "[workflow-health-check] checks passed after self-repair; restart OpenCode to load any repaired plugin/skill state",
      )
    } else {
      console.log("[workflow-health-check] all checks passed")
    }
  } catch (err) {
    const e = err as {
      stdout?: string
      stderr?: string
      message?: string
      code?: string | number
      signal?: string
    }

    const detail = [e.stdout ?? "", e.stderr ?? ""].filter(Boolean).join("\n")
    const fallback = [
      e.message ?? String(err),
      e.code !== undefined ? `exit/code: ${String(e.code)}` : "",
      e.signal ? `signal: ${e.signal}` : "",
    ]
      .filter(Boolean)
      .join("\n")

    health = {
      state: "failed",
      tail: tailLines(detail.trim() || fallback),
    }

    console.error(
      "[workflow-health-check] check failed to complete:",
      e.message ?? err,
    )
  }
}

export const WorkflowHealthCheckPlugin: Plugin = async () => {
  // Critical recursion guard for verify-workflow.sh's nested
  // `opencode debug config` runtime-resolution probe. The child process must
  // still load the rest of the normal OpenCode/plugin stack so Systematic's
  // effective agent overlays can be inspected; only this health-check launch is
  // suppressed.
  const isProbe = process.env.WORKFLOW_HEALTH_CHECK_PROBE === "1"

  if (!isProbe && !checkStarted) {
    checkStarted = true

    // Keep OpenCode startup responsive. The verifier is local-only; failures
    // are cached and surfaced through subsequent system-prompt transforms.
    void runHealthCheck().catch((err) => {
      health = {
        state: "failed",
        tail: tailLines(err instanceof Error ? err.message : String(err)),
      }
      console.error("[workflow-health-check] unexpected error:", err)
    })
  }

  return {
    "experimental.chat.system.transform": async (
      _input: unknown,
      output: { system?: string[] },
    ) => {
      if (!health || health.state === "clean") return
      if (!Array.isArray(output.system)) return

      if (health.state === "repaired") {
        output.system.push(
          [
            "## Workflow health check SELF-REPAIRED",
            "The global Gentle AI + Systematic workflow verifier repaired one or more user-owned workflow artifacts during this OpenCode process. The verifier now passes, but this process may still have pre-repair plugin, skill, or routing state loaded in memory.",
            "Tell the user that the workflow self-repaired and recommend restarting OpenCode before relying on the repaired setup. Do not rerun or modify the workflow automatically unless the user asks.",
            "Verifier tail:",
            "```",
            health.tail,
            "```",
          ].join("\n"),
        )
        return
      }

      output.system.push(
        [
          "## Workflow health check FAILED",
          "The global Gentle AI + Systematic workflow setup has a problem that the startup verifier could not fully repair or validate.",
          `Run \`bash ${VERIFY_SCRIPT}\` and offer the user the result. If RDD is off, re-enable it with \`gentle-ai review mode enable --scope global\`. Do not claim the workflow is healthy until the verifier exits successfully.`,
          "Verifier tail:",
          "```",
          health.tail,
          "```",
        ].join("\n"),
      )
    },
  }
}

export default WorkflowHealthCheckPlugin
