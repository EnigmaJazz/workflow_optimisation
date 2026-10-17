# Normative Ledger — orchestrator prompt rebuild (Q31 S5a)

Scope: every sentence in the CURRENT prompt (`global-config/opencode.json` →
`agent["gentle-orchestrator"].prompt`, sha256
`c0dd55e85f912807391df4aeb386628a289af1cde86b966d29927cf02b327ee0`, 414 lines)
containing MUST, NEVER, ALWAYS (case-insensitive, word boundary) or "hard rule".
70 candidate sentences: **44 kept, 1 split, 10 superseded-by-base, 15
removed-by-design; zero unclassified.**

Classification meanings:

- `kept` — the rule survives in an overlay block (destination = overlay id).
- `moved` — the rule now lives in another authoritative document (destination = document + section).
- `split` — the sentence's normative content survives in more than one destination; the destination cell names each part.
- `superseded-by-base` — the rendered v4 base states the same rule; our copy is dropped (destination = base heading).
- `removed-by-design` — the rule is deliberately gone (destination = `removed: reason`).

Source line numbers refer to the current prompt. The assembled prompt and its
wiring are produced by `global-config/prompts/gentle-orchestrator/assemble-orchestrator-prompt.py` from `base.md`
+ `overlay.md` (unwired until S5b).

| # | Source | Sentence (short) | Classification | Destination |
|---|--------|------------------|----------------|-------------|
| 1 | L11 | "SDD is explicit or accepted only; its optional research/verification never gate proposal/archive solely for missing artifacts; SDD never launches RDD." | removed-by-design | removed: gentle-ai v4 retires SDD; the assembled prompt carries no SDD branch (Q31) |
| 2 | L15 | "Triggers only select direct delegation; they never select SDD or create SDD artifacts." | kept | overlay:user:always-delegate |
| 3 | L19 | "Every repository-inspection Task brief must include the SEARCH CONTRACT ... A child needing evidence outside its registered project must stop and return EXTERNAL_CONTEXT_REQUIRED." | kept | overlay:user:workflow-routing |
| 4 | L23 | "Never assume that a remembered summary or a skill registry substitutes for the current canonical recipe." | kept | overlay:user:workflow-routing |
| 5 | L25 | "Read the active selected skill and follow its named specialist routing; never replace systematic-implementer or a selected reviewer with a generic worker." | kept | overlay:user:workflow-routing |
| 6 | L33 | "A failed or unavailable assessment never lowers risk: treat the commit as due and run scoped preflight STATUS with the same selectors." | kept | overlay:user:review-boundary |
| 7 | L33 | "Stop the affected review path; never substitute an unscoped accumulated branch." | kept | overlay:user:review-boundary |
| 8 | L35 | "Never parse, append to, fence, or reconstruct the provider-issued task line." | kept | overlay:user:review-boundary |
| 9 | L35 | "Launch independent lens inputs in one grouped wave without waiting between launches and never set a background flag." | kept | overlay:user:review-boundary |
| 10 | L43 | "Never dispatch a review Task to the plain review-* names while the installed transport is loaded." | kept | overlay:user:review-boundary |
| 11 | L44 | "Never grant review lanes to implementation workers or isolated reviewers." | kept | overlay:user:review-boundary |
| 12 | L46 | "On correction_context_budget_exceeded, obtain the exact review abandon binding template through the reviewed host boundary; never substitute review invalidate." | kept | overlay:user:review-boundary |
| 13 | L48 | "Recompute from work-unit commits; when forecast or running total crosses about 400, apply the chosen strategy before the next commit. The accumulated delivery budget controls slices, never code shrinking." | split | overlay:user:secure-odd-protocol (budget shapes slicing; never shrink correct code) + WORKFLOW.md "Substantial ODD work units and review" (recompute/apply-strategy mechanics) |
| 14 | L48 | "A routed work-unit commit trailer states the task/class at commit time; later review outcome belongs in tracker and router log, never rewritten retroactively into that commit." | kept | overlay:user:secure-odd-protocol |
| 15 | L51 | "Never edit/write project files, never use native host Bash, never run project mutation/execution yourself, and never use sandbox mutation, sandbox execution, or sandbox lifecycle tools." | kept | overlay:user:read-only-boundary |
| 16 | L64 | "Known uncertainties, hazards, or questions the worker must resolve rather than silently guess." | kept | overlay:user:technical-lead-contract |
| 17 | L84 | "Never delegate host_register_project to general, explore, SDD agents, Systematic agents, frontend agents, reviewers, or judges." | kept | overlay:user:project-registration |
| 18 | L86 | "The target must be the user's intended absolute project root." | kept | overlay:user:project-registration |
| 19 | L86 | "Never guess another directory, register $HOME, a temporary directory, the sandbox control directory, or broaden the request to parent/sibling roots." | kept | overlay:user:project-registration |
| 20 | L88 | "Re-running an already registered project is acceptable and must not be treated as a reason to edit the control files manually." | kept | overlay:user:project-registration |
| 21 | L89 | "Never request or infer --create-remote, repository visibility, or an initial push unless the user explicitly asks for remote creation/push." | kept | overlay:user:project-registration |
| 22 | L97 | "Never summarize, abbreviate, reorder, relabel, merge, or omit choices." | superseded-by-base | base:### Lossless Blocking Prompts (MANDATORY) |
| 23 | L97 | "Never silently split an atomic business choice across multiple interactions." | superseded-by-base | base:### Lossless Blocking Prompts (MANDATORY) |
| 24 | L99 | "Native-tool-only wording elsewhere never disables this fallback." | superseded-by-base | base:### Lossless Blocking Prompts (MANDATORY) |
| 25 | L106 | "A Gentle AI workflow merely hosting a failure is not enough: a failure produced by the client runtime belongs to that runtime." | superseded-by-base | base:#### Gentle AI Provider Defect Handoff (MANDATORY) |
| 26 | L108 | "When it is ours, never offer to switch to, inspect, modify, or directly repair the Gentle AI repository from that workflow." | superseded-by-base | base:#### Gentle AI Provider Defect Handoff (MANDATORY) |
| 27 | L118 | "Never reopen automatically." | superseded-by-base | base:#### Gentle AI Provider Defect Handoff (MANDATORY) |
| 28 | L120 | "Never infer creation from output text alone." | superseded-by-base | base:#### Gentle AI Provider Defect Handoff (MANDATORY) |
| 29 | L124 | "Never synthesize the decline command, target, token, or consumer continuation from prose." | superseded-by-base | base:#### Gentle AI Provider Defect Handoff (MANDATORY) |
| 30 | L130 | "Never resume against unpublished code: a source checkout, a local build, or an unmerged pull request." | superseded-by-base | base:#### Gentle AI Provider Defect Handoff (MANDATORY) |
| 31 | L134 | "Never translate or alter the machine answer tokens (granted, declined), commands, paths, or invocations." | removed-by-design | removed: SDD edit-authority consent relay retired with SDD (Q31); answer-token integrity is preserved by the base consent handoff |
| 32 | L134 | "Never summarize, reshape, reorder, merge, or omit any part." | removed-by-design | removed: SDD edit-authority consent relay retired with SDD (Q31) |
| 33 | L134 | "The human decides: never answer on the human's behalf and never run the grant unprompted." | removed-by-design | removed: SDD edit-authority consent relay retired with SDD (Q31); the lossless consent contract in base retains human-decides |
| 34 | L143 | "When delegating, forward this contract to the executor so persona voice never becomes the artifact or public-comment default." | superseded-by-base | base:### Language Domain Contract |
| 35 | L147 | "Crossing a threshold selects delegated direct work; it never selects SDD, creates SDD state, or invokes an sdd-* phase." | kept | overlay:user:always-delegate |
| 36 | L149 | "It MUST NOT mutate project state, run host or sandbox shell commands, run tests/builds/installers, or perform implementation inline." | kept | overlay:user:read-only-boundary |
| 37 | L172 | "Execution rule: tests, builds, installs, shell commands, Git mutation, and other project execution are always delegated to an executor/worker." | kept | overlay:user:always-delegate-triggers |
| 38 | L173 | "Select SDD only after an explicit request or accepted proposal; risk alone never forces SDD." | removed-by-design | removed: v4 retires SDD (Q31); no SDD selection surface remains |
| 39 | L177 | "For non-SDD work, finish mutating normalizers before native review START; freeze candidate bytes; use provider-returned STATUS and exact invocations; approved acknowledgement ends review but never authorizes delivery." | kept | overlay:user:review-boundary |
| 40 | L177 | "Inside SDD, perform configured TDD/functional checks, and never launch RDD from a phase or make native review an archive gate." | removed-by-design | removed: SDD phase lifecycle retired (Q31); generic test-first forwarding retained in overlay:user:secure-odd-protocol |
| 41 | L184 | "Review evidence never grants push/PR/merge/release; substantial ODD work-unit commits are authorized by the original implementation request after checks, not by review evidence." | kept | overlay:user:review-boundary |
| 42 | L204 | "Commands intended for the user to paste into their terminal must be Fish-compatible." | kept | overlay:user:shell-environment |
| 43 | L217 | "Memory writes must be evidence-backed and durable." | kept | overlay:user:magic-context |
| 44 | L221 | "A newly introduced unclassified agent must be reviewed before receiving durable-memory mutation." | kept | overlay:user:magic-context |
| 45 | L267 | "Never silently create a second active record when an existing key should be updated." | kept | overlay:user:magic-context |
| 46 | L285 | "hybrid -> Magic Context + OpenSpec; both writes must succeed" | removed-by-design | removed: OpenSpec artifact-store modes retired (Q31); Magic Context is the only store in the assembled prompt |
| 47 | L298 | "/sdd-verify -> optional practical diagnostics; reports observed findings and never grants archive authority" | removed-by-design | removed: v4 retires SDD (Q31) |
| 48 | L320 | "Never launch sdd-apply just because the user asked to implement a feature." | removed-by-design | removed: v4 retires SDD (Q31) |
| 49 | L332 | "Never invoke mem_* without an explicitly selected Engram workflow." | kept | overlay:user:magic-context |
| 50 | L366 | "hybrid: persist both Magic Context and OpenSpec; both sides must read back successfully." | removed-by-design | removed: OpenSpec artifact-store modes retired (Q31) |
| 51 | L405 | "Never shrink correct code merely to meet a size budget." | kept | overlay:user:secure-odd-protocol |
| 52 | L431 | "ALL sub-agent launch prompts that involve reading, writing, or reviewing code MUST include pre-resolved skill paths from the skill registry." | kept | overlay:user:magic-context-skill-resolution |
| 53 | L457 | "The orchestrator still passes task-specific artifact references and critical decisions explicitly; never assume a child inherited the parent's live conversation." | kept | overlay:user:magic-context-delegated-tasks |
| 54 | L481 | "If research was selected, sdd-propose must not launch from partial/blocked evidence or unconfirmed product decisions." | removed-by-design | removed: SDD phases retired (Q31) |
| 55 | L483 | "Each phase must retrieve the exact canonical record and read back its own persisted result before returning success." | removed-by-design | removed: SDD phases retired (Q31); the ODD tracker/mirror readback is retained in overlay:user:secure-odd-protocol |
| 56 | L494 | "You MUST follow strict-tdd.md." | removed-by-design | removed: SDD apply/verify launch instruction retired (Q31); generic TDD forwarding retained in overlay:user:secure-odd-protocol |
| 57 | L503 | "The writer must update/merge the existing Magic Context record, preserving all prior completed tasks and evidence; never create a second active apply-progress record." | removed-by-design | removed: SDD apply-progress continuity retired (Q31) |
| 58 | L515 | "Read-only requests end after findings; never create a tracker or delegate a writer." | kept | overlay:user:secure-odd-protocol |
| 59 | L517 | "Update and read back both after each completed task or accepted scope change; never mark a task complete without observed checks." | kept | overlay:user:secure-odd-protocol |
| 60 | L519 | "The orchestrator remains read-only for project files and execution: it delegates the track/write/check actions, never creates the tracker with native host tools." | kept | overlay:user:read-only-boundary |
| 61 | L519 | "Systematic ce:review stays advisory when selected, and its helper pipeline must run in an authorized sandbox worker." | kept | overlay:user:review-boundary |
| 62 | L521 | "Never substitute the orchestrator for an implementation worker or for independent reviewer personas." | kept | overlay:user:always-delegate |
| 63 | L527 | "For Magic Context-only mode, derive only from actual retrieved phase artifacts and never claim that native OpenSpec status inspected those records." | removed-by-design | removed: SDD/OpenSpec artifact backend retired (Q31); Magic Context is the only store |
| 64 | L532 | "A fixed host operation never grants ordinary host Bash, project file editing, or sandbox mutation to the orchestrator." | kept | overlay:user:host-tools-relay |
| 65 | L534 | "Map each provider-returned plain review-* name to its asi-review-* target while forwarding the provider-issued task line verbatim; never dispatch the plain name." | kept | overlay:user:review-boundary |
| 66 | L534 | "A reply that the required GENTLE_AI_REVIEW_CONTEXT block was not supplied is a transport-lane failure, not a review finding, and must be re-dispatched through the mapped relay without recording or adjudicating it." | kept | overlay:user:review-boundary |
| 67 | L534 | "Never grant relay lanes to implementation workers or isolated reviewers." | kept | overlay:user:review-boundary |
| 68 | L534 | "Never use fallback session replay for either set because replay bypasses Task prompt injection." | kept | overlay:user:review-boundary |
| 69 | L540 | "Always launch the three baseline reviewers (correctness, testing, project standards) and any candidate-specific reviewers selected by screening in the same independent wave." | kept | overlay:user:review-boundary |
| 70 | L75 | "Before dispatching a unit to a project-manager, the ORCHESTRATOR MUST read its tracker mirror and supply both hashes in the PM brief." | kept | overlay:user:secure-odd-protocol |

## Structural coupling note

The `<!-- gentle-ai:opencode-desktop-delegation-progress -->` /
`<!-- /gentle-ai:opencode-desktop-delegation-progress -->` comment pair lives entirely inside the
single base section `#### Delegation Visibility (OpenCode Desktop)`, so a replace/remove of that
section carries or drops both halves together and can never leave half the pair behind. The
`#### Cost and Context Balance` extent no longer carries either half, so the
`user:always-delegate-cost-context` replacement does not re-emit one. The assembler documents this
managed-marker invariant (a pair must not straddle a section boundary) but deliberately does not
lint block bodies for balanced pairs.
