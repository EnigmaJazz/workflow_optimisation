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

const SPECIALIST_WRITERS: readonly string[] = ["general", "systematic-implementer", "frontend-dev", "frontend-dev-premium", "frontend-apply", "frontend-apply-local", "jd-fix-agent", "pr-comment-resolver", "bug-reproduction-validator", "design-iterator", "sdd-apply", "sdd-apply-local", "gentle-ai-worker", "gentle-ai-worker-local"]
const ODD_SPECIALIST_WRITERS: readonly string[] = [...SPECIALIST_WRITERS, "odd-apply"]

/** PM coordinators are dispatch routers, never route-stage implementation writers. */
export const COORDINATOR_PATTERNS: readonly RegExp[] = [/^pm-[a-z0-9-]+$/]

export const isCoordinator = (name: string): boolean =>
  COORDINATOR_PATTERNS.some((pattern) => pattern.test(name))

// Anchored on purpose: under deny-by-default a loose match would let a writer through.
export const READ_ONLY_SPECIALIST_PATTERNS: readonly RegExp[] = [
  /^(?:explore|gentle-ai-explore|gentle-ai-verify|sdd-explore|sdd-verify|sdd-research|vision|architecture-strategist|spec-flow-analyzer|git-history-analyzer|issue-intelligence-analyst|pattern-recognition-specialist|deployment-verification-agent|repo-research-analyst|best-practices-researcher|framework-docs-researcher|learnings-researcher)$/,
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
  "workflow-odd-secure": [{
    id: "tracker",
    artifactPattern: /^odd\/tasks\/[^/]+\.md$/,
    allowsSpecialists: ODD_SPECIALIST_WRITERS,
  }],
  "workflow-systematic": [
    {
      id: "requirements",
      artifactPattern: /^docs\/brainstorms\/[^/]+\.md$/,
      skillMarkers: ["ce-brainstorm"],
      gatesSkillLoads: ["ce-plan"],
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
