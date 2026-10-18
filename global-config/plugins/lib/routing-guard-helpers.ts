import { writeFile } from "node:fs/promises"

export let taskWriteFile = writeFile

/** Test seam for exercising hung task-result persistence without changing gate behavior. */
export function setTaskWriteFileForTests(write: typeof writeFile | null): void {
  taskWriteFile = write ?? writeFile
}

export type RouteStage = {
  id: string
  artifactPattern?: RegExp
  skillMarkers?: readonly string[]
  gatesSkillLoads?: readonly string[]
  allowsSpecialists?: readonly string[]
}

const SPECIALIST_WRITERS: readonly string[] = ["general", "systematic-implementer", "frontend-dev", "frontend-dev-premium", "frontend-apply", "frontend-apply-local", "jd-fix-agent", "pr-comment-resolver", "bug-reproduction-validator", "design-iterator", "gentle-ai-worker", "gentle-ai-worker-local"]
const ODD_SPECIALIST_WRITERS: readonly string[] = [...SPECIALIST_WRITERS, "odd-apply"]

/** Only the exact leading description token can signal a tiny-fix Task dispatch. */
export const hasTinyFixDispatchMarker = (description: unknown): boolean =>
  typeof description === "string" && /^\[tiny-fix\](?:\s|$)/.test(description)

/** PM coordinators are dispatch routers, never route-stage implementation writers. */
export const COORDINATOR_PATTERNS: readonly RegExp[] = [/^pm-[a-z0-9-]+$/]

export const isCoordinator = (name: string): boolean =>
  COORDINATOR_PATTERNS.some((pattern) => pattern.test(name))

/**
 * PM sessions must hold their own route's adapter key before gated host mutations and the
 * native review lifecycle. Declarative agent → adapter-skill map; a guardrail input, not an
 * authentication boundary or an identity source.
 */
export const PM_ROUTE_ADAPTER_SKILLS: Readonly<Record<string, string>> = {
  "pm-odd": "workflow-odd-secure",
  "pm-systematic": "workflow-systematic",
}

/**
 * Astra aliases are `<agent>-astra` (created at runtime by astra-sol-upgrade.ts), so a PM's
 * Astra variant must bind to the SAME base adapter skill as the base PM identity.
 */
const ASTRA_SUFFIX = "-astra"

/** The adapter skill a PM session must own, or null for any non-PM agent name. */
export const pmRequiredRouteSkill = (agent: string): string | null => {
  const base = agent.endsWith(ASTRA_SUFFIX) ? agent.slice(0, -ASTRA_SUFFIX.length) : agent
  return Object.prototype.hasOwnProperty.call(PM_ROUTE_ADAPTER_SKILLS, base)
    ? (PM_ROUTE_ADAPTER_SKILLS[base] ?? null)
    : null
}

// Anchored on purpose: under deny-by-default a loose match would let a writer through.
export const READ_ONLY_SPECIALIST_PATTERNS: readonly RegExp[] = [
  /^(?:explore|gentle-ai-explore|gentle-ai-verify|vision|architecture-strategist|spec-flow-analyzer|git-history-analyzer|issue-intelligence-analyst|pattern-recognition-specialist|deployment-verification-agent|repo-research-analyst|best-practices-researcher|framework-docs-researcher|learnings-researcher)$/,
  /^review-/,
  /^asi-review-/,
  /^advisor-/,
  /^jd-judge-/,
  /reviewer$/,
]

/** Ordered artifact marker names for a stage: namespaced, legacy (only while unique), odd legacy. */
export function stageMarkerNames(
  route: string,
  stageId: string,
  routeStages: Record<string, readonly { id: string }[]>,
): string[] {
  const names = [`artifact-${route}-${stageId}`]
  const routesWithId = Object.values(routeStages).filter((stages) => stages.some((stage) => stage.id === stageId))
  if (routesWithId.length <= 1) names.push(`artifact-${stageId}`)
  if (route === "workflow-odd-secure") names.push(`artifact-odd-${stageId}`)
  return names
}

export const ROUTE_STAGES: Record<string, readonly RouteStage[]> = {
  "workflow-odd-secure": [
    {
      id: "advice",
      artifactPattern: /^odd\/advice\/[^/]+\.md$/,
    },
    {
      id: "tracker",
      artifactPattern: /^odd\/tasks\/[^/]+\.md$/,
      allowsSpecialists: ODD_SPECIALIST_WRITERS,
    },
  ],
  "workflow-systematic": [
    {
      id: "requirements",
      artifactPattern: /^docs\/brainstorms\/[^/]+\.md$/,
      skillMarkers: ["ce-brainstorm"],
      gatesSkillLoads: ["ce-plan"],
    },
    {
      id: "advice",
      artifactPattern: /^odd\/advice\/[^/]+\.md$/,
    },
    {
      id: "plan",
      artifactPattern: /^docs\/plans\/[^/]+\.md$/,
      skillMarkers: ["ce-plan"],
      gatesSkillLoads: ["ce-work"],
      allowsSpecialists: SPECIALIST_WRITERS,
    },
    {
      id: "review",
      artifactPattern: /^\.context\/systematic\/ce-review\/[^/]+\/review-summary\.json$/,
      skillMarkers: ["ce-review"],
      gatesSkillLoads: [],
    },
  ],
}
