# Q100 — host_plan_archive permission coverage

## Objective
Restore fail-closed V2 derivation coverage for the archive host tool using exactly two canonical configuration insertions. This is a configuration-layer unit, not delivery, deployment, or end-to-end archive activation.

## Unit and route
- unit_id: q100-host-plan-archive-permission-u1
- task_id: T1
- task_class: global tooling change
- Risk: security-boundary authorization configuration, despite a two-line source diff.
- route: delegated; workflow-route and workflow-odd-secure loaded by Planner. Secure policy requires delegated implementation/execution. Planner dispatches no writer or native review lens.
- Feature branch / anchor (supplied by PM, not independently executed by Planner): chore/coordinator-selection at 3970311718482b928759c54b537e4a999a27056e.
- RDD mode (supplied): on, source global; never toggle automatically.
- Supplied pending review target identity: sha256:029ec5a5bfaeea1927b68da154361b24a952b3fb1823094ec223bad6c176f9ea. This is not established as a Git baseRef; the orchestrator must recover the actual last-reviewed commit from native authority, not reinterpret this identity as a commit.
- Owner decision supplied for 2026-11-04: hold the open high-risk slice pending, fix this blocker first, then run one native review over the combined committed tree. Preserve the pending boundary; do not claim this is a review waiver or delivery approval.
- Forecast: 2 source insertions plus this bounded tracker and one ROUTER-LOG row; staged authored receipt must establish the actual total, below 400 changed lines and 100 KiB authored patch.
- Delivery strategy: ask-on-risk; no push, PR, merge, restart, deployment, or archive execution authorized by this unit.

## Problem and evidence
- Supplied by PM: derive RealConfig failures report `[derive-v2] refused: tools without an explicit permission rule (V2 would allow them silently): host_plan_archive`; downstream failures follow absent temporary output. Not executed by Planner.
- Supplied external evidence, not read by Planner: agent-sandbox-integration tool-specs-host-ops.ts:173-197 defines host_plan_archive, archives finished odd/tasks or odd/mini documents without an approval request, and rejects missing, occupied, escaping, protected, staged, or conflicted paths. External implementation is not an allowed edit surface.
- Observed: scripts/derive-v2-config.py check_rules:99-117 requires every inventory tool at top-level permission and resolves explicit agent entries over the global value. build:390-393 checks before writing output. derive_config:355-363 copies non-plugin values.
- Observed: global-config/opencode.json identifies gentle-orchestrator at :772, its permission map at :776, and host_orca_report allow at :876. Top-level host_task_mark deny at :2849 is followed by host_test_run deny. Both insertion anchors already have commas, permitting pure insertions.
- Observed: tests/test_derive_v2_config.py:118 skips RealConfig unless its HOME-relative external checkout exists; :123 uses temporary --out; :149-153 compares permissions against source. A passing skip is not validation of the real inventory.
- Observed: tests/test_review_pipeline_permissions.py:836-847 explicitly tests clean skips when Bun cannot execute; full Python discovery alone cannot prove those controls ran.
- Observed: docs/TODO.md:7-13 gates starting on queue registration and requires each planned unit once with prerequisites. A covering queue entry has not been established; docs/TODO.md is outside the allowed paths. Explorer reported no Q100 heading; that heading check alone does not exclude all possible embedded rows.
- Observed: global-config/prompts/gentle-orchestrator/overlay.md:213 authorizes explicitly ask-gated registered host mutations and enumerates other plan tools; :214 separately allows host_test_run. This excerpt does not authorize the proposed allow-gated archive mutation. Adding a configuration key is not proof of prompt/broker authority.
- Reading used AFT/read fallback after the local CodeGraph check yielded no usable index; no index initialization attempted.

## Exact requested contract
> Add exactly two rules: host_plan_archive deny in global/top-level permission map beside :2849, and host_plan_archive allow in gentle-orchestrator agent permission map beside host_orca_report allow at :876. Archiving a finished tracker is orchestrator closure work; no other agent gains it. Nothing else changes — no reformatting, reserialisation, version bumps.

> Only the two new rules, the tracker, and the ROUTER-LOG.md row may change.

> Derive dry run into temp dir (--out), never --apply.

Allowed edits only:
- global-config/opencode.json: precisely the two new permission entries.
- odd/tasks/q100-host-plan-archive-permission.md: planning, task state and factual evidence.
- ROUTER-LOG.md: one unit row and its factual closure fields.

No test-file, prompt, plugin, pin, verifier entry/module/digest, version, or other tool-rule changes; no reformatting or JSON reserialization. Never touch either live configuration root. No derive --apply, restart, deployment, full verifier/self-heal, or actual archive call.

## T1 — bounded implementation plan
- [ ] T1: Add the global deny and orchestrator-only allow; execute scoped verification; obtain Gate 2 before commit.

### Prerequisites — unresolved, no writer dispatch yet
1. PM must produce the exact existing docs/TODO.md entry covering this unit and prerequisites, or obtain explicit owner authority for a queue-only prerequisite update/waiver. No implicit waiver is inferred from the three-file restriction. If authority expands scope, reconcile the plan before implementation; do not silently add a fourth path.
2. Resolve the overlay authorization finding: obtain explicit owner acceptance that this unit is permission coverage only, archive invocation remains out of scope pending prompt/authority alignment, or obtain authority for a separately scoped prompt correction. Do not broaden this patch. Advice does not authorize archive use.
3. PM/writer must verify actual root, branch, HEAD and status against the supplied anchor. Cleanliness is supplied, not observed here; account for the newly authorized tracker as expected metadata and stop on unrelated changes. Before writer dispatch, PM must resolve the recipe's writer-tier decision; no unknown model-family decision is inherited.
4. Required execution must have an approved inventory/fixture boundary. The registered-project child must not fetch or inspect an external checkout opportunistically. If inventory or required runtime tests are inaccessible, report BLOCKED/EXTERNAL_CONTEXT_REQUIRED with the concrete evidence request, not a skipped pass.

### Approach
- Start with existing regression tests and capture baseline before source changes; no new repository test file is permitted. Record exact failing test IDs, errors, skips, command, environment and output references. Expected refusal must name host_plan_archive; unrelated baseline failures in the required fully-passing derive module are blockers, not permission to expand scope.
- Make minimal targeted textual insertions only: top-level permission.host_plan_archive = deny immediately after host_task_mark; agent.gentle-orchestrator.permission.host_plan_archive = allow immediately after host_orca_report. No tools-map entries or serializer roundtrip.
- Check exact patch contents as well as per-file numstat: exactly two added lines, zero deleted lines in global-config/opencode.json. Duplicate-aware parse; assert both exact nested values and that every other semantic value matches baseline.
- Execute temporary policy assertions against canonical AND derived output: sweep all other agent maps for exact grants and tool-level wildcard matches, including ask/allow and effective ordering. Exclude task-name and read-path submaps from tool-name matching. Include generated aliases/access mirrors. Stop on unexplained non-orchestrator access rather than changing more rules. check_rules alone is not an OpenCode authorization evaluator; if effective ordering cannot be established, report the coverage gap.
- Non-vacuity controls operate on in-memory clones, never canonical edits: inventory must contain host_plan_archive; fixed check_rules input passes; removing the global rule must raise naming host_plan_archive; removing the orchestrator grant must make the positive grant assertion fail. Assert supplied no-approval inventory semantics; unexpected ask semantics stop the unit. Never invoke the real archive tool as a probe.

### Required verification and acceptance
1. git diff --numstat -- global-config/opencode.json reports 2 additions and 0 deletions; actual textual patch is exactly the two intended insertions. Entire changed-path inventory is confined to the three authorized paths.
2. python3 scripts/derive-v2-config.py --source global-config --sandbox-repo <approved inventory checkout> --out <isolated temporary root> exits 0, without missing-permission refusal; output opencode.json exists and passes the permission/agent sweep. Never --apply. Record actual argv and inventory evidence. Use an argv-safe temporary-directory procedure, not shell substitutions/pipes, and remove temporary outputs before export.
3. python3 -m unittest tests.test_derive_v2_config -v fully passes. Report concrete RealConfig IDs and counts as executed, not skipped. Record HOME and approved checkout resolution; do not force host HOME/access to bypass sandbox restrictions. Missing approved inventory is BLOCKED, not a reduced acceptance criterion.
4. python3 scripts/verifier_manifest.py check passes without any manifest/pin update.
5. python3 -m unittest discover -s tests has no new failure IDs or errors against the documented, same-runner/same-environment pre-edit baseline; compare skips too. Supplied environment categories (missing sqlite3, denied node, HOME=/nonexistent) and historical counts are not blanket waivers. The expected derive failures must disappear. If a trustworthy comparable baseline is unavailable, report the gap rather than claim no regressions.
6. Execute bun tests/test_review_pipeline_permissions.js, or demonstrate that all equivalent Python-invoked Bun permission controls actually executed, non-skipped, on this same candidate. Include runtime availability and result. This uses existing tests, not test-file changes.
7. First post-code pass includes aft_inspect or applicable static diagnostics for every changed path, alongside tests, independent verifier and required post advice on the SAME initial candidate. JSON/Markdown checks may establish applicable coverage; disclose analyzer gaps. Do not first collect diagnostics after correction.
8. Tracker records observed commands, exits, test counts/IDs/errors/skips, baseline comparison, raw evidence references, advice dispositions and unresolved limits. ROUTER-LOG has one row, global tooling class, no reclassification, pending review, source-only deploy status and tracker reference. PENDING-COMMIT is valid before commit.
9. Writer returns actual root/branch/anchor/status, complete diff/path inventory and the staged reviewability receipt (authored additions+deletions, raw authored patch bytes, generated/binary paths separately). No implementation commit before Gate 2.

## Advice selection and raw evidence — T1 / pre-code
Selection: one affected configuration/derivation authorization surface, plus compulsory specification carrier; two independent model families, no vote or approval claim.
- advisor-integration-pre selected for configuration inheritance, global-versus-agent rules, derivation consumers, wildcard/alias blast radius and executable permission controls. Configured model opencode-go/mimo-v2.6-flash. Actual dispatch/result: ses_e58d91ef4ffdbrrw5rW4m7uCN7; RAW output read by Planner.
- advisor-gemini-pre selected as compulsory specification carrier in place of advisor-spec-pre while Antigravity lane is inactive; model google/gemini-4-argon. Actual dispatch/result: ses_e58d91ef4ffeFrJqTTfIcwV8eH; RAW output read. Exactly one specification carrier dispatched.
- advisor-spec-pre skipped because the substitute carrier occupies that position. advisor-gemini-post is reserved for the compulsory post position, replacing advisor-spec-post, not in addition to it.
- Separate security/design/testing/maintainability passes skipped: no second independent implementation surface; the configuration advisor covered this permission boundary and controls, and the compulsory carrier checked exact specification/edge cases. No deployment integration is implemented. Subscription Gemini advisors are not dispatched while the external lane is PLANNED.
- planner-evidence skipped: bounded own reads plus explore established in-project planning facts. Actual read-only explore result: ses_e58deedc1ffe6ygatfY02aFdot. No advisor-gemini-evidence was needed.

### Findings and dispositions
- Integration F1: incorporated explicit Bun permission controls/non-skipped equivalent.
- Integration F2: prompt authorization mismatch verified at overlay.md:213-214; unresolved prerequisite above. Do not silently edit prompts or present the grant as runtime authority.
- Integration F3: routing-guard asymmetry is outside this permission-coverage patch; record as later route-gating work, not permission to alter plugins. No archive invocation/activation is claimed here. Broader route-gate parity is not independently required to prove derivation coverage.
- Integration F4/F6: require exact expected red-to-green refusal, actual inventory membership, and concrete non-skipped RealConfig execution; stop on other derive failures.
- Integration F5/F7/F8: incorporated wildcard/derived-output sweep, exact middle-of-map insertions, duplicate-aware parse, and config-layer-only verification claim.
- Integration F9 and SPEC-F1: queue prerequisite unresolved; Gate 1 must REFINE until exact entry or explicit scoped authority is supplied.
- SPEC-F2/F3/F4: incorporated environment resolution, argv-safe ephemeral probes and insertion anchors. Rejected suggestion to infer a queue waiver from the strict scope: that would invent owner authority. No forced host HOME bypass is authorized.

## Post-code and Gate 2 handoff
After prerequisites and Gate 1 permit implementation, PM dispatches the authorized ODD writer; Planner does not. Global tooling/security budget owes one independent gentle-ai-verify (security tier, PM/orchestrator dispatched), PM self-check and independent orchestrator readback. Gather writer output, verifier evidence and initial static diagnostics, then Planner dispatches advisor-gemini-post with exact specification, allowed paths, actual diff/relevant code and evidence. No advisor-spec-post duplicate. Required advice findings are evidence, never approval.

Gate 2 requires the installed candidate, writer/verifier/post-advisor evidence and pre-commit assessment, BEFORE commit and before PM ticks/completes T1. If a required surface/evidence is unavailable, stop BLOCKED; do not substitute post-commit native review. One initial writer plus ONE fresh consolidated correction maximum. Install any correction, targeted-recheck finding IDs and affected controls, then run Gate 2 again. Second Gate 2 passes unless a true blocker remains; a second REFINE/ESCALATE returns to human. Non-blockers become later work.

After Gate 2 PASS, the authorized PM commit path and metadata closure apply. Record actual commit and native assessment. Per the supplied owner decision, native review occurs only afterward over the combined committed tree with the held high-risk slice, through provider-returned authority; it is not Gate 2 input. Pending native review is not delivery or deployment approval. Do not archive this tracker as part of verification or closure under this unit's configuration-layer evidence.

## Log
- 2026-11-04 — Planner read current route/ODD contract, inspected configuration and derivation/test excerpts, dispatched one config-surface advisor plus compulsory API specification carrier independently, and read both RAW results. No implementation, tests, deployment, native review or writer dispatch performed by Planner.
- Gate 1 planned disposition: REFINE for unresolved queue/authorization prerequisites; technical verdict is recorded separately by host_gate_verdict. T1 remains unchecked. No check result is fabricated.


## Revisions
- r1 2026-11-04T15:44:52Z planner: Finalize T1 plan and raw pre-advice dispositions; Gate 1 requires scope/queue authorization resolution before writer.
