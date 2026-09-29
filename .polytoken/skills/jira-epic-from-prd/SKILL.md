---
description: Convert a Confluence PRD into a reviewed Jira Epic and child issues for the target project. Runs the full PRD to Epic to issues workflow with research, operator-gated drafting, multi-agent review, and final Jira/Confluence writes. Ends with a Jira Epic and child issues that jira-epic-run can bootstrap from.
polytoken:
  tags: [jira-epic, workflow]
---

# Jira Epic from PRD

Take a PRD page in Confluence and produce a reviewed Jira Epic plus reviewed child issues, wired together with issue links, ready for `jira-epic-run` to bootstrap and execute. This is an eight-phase workflow with operator checkpoints, multi-agent reviewer panels, and deliberate research bounded by a one-level-deep rule.

The Epic is where hard technical problems get resolved while a human is paying close attention. By the time child issues are written, every decision is pinned, every question is resolved, and every issue is merge-ready. Child issues downstream are plug-and-play for implementation.

This skill does not bootstrap `.current-epic/`. After Phase H, the Jira Epic and its child issues exist in Jira. To start execution, invoke `jira-epic-run`, which bootstraps `.current-epic/` from Jira.

## Constants

All values in this block are site-specific placeholders — replace them with your own project values before first use.

- Atlassian cloudId: `<ATLASSIAN_CLOUD_ID>`
- Jira project: `<PROJECT_KEY>`
- Product area: `<PRODUCT_AREA>`
- PRD container: `<PRD_CONTAINER>` (Confluence page `<PRD_CONTAINER_PAGE_ID>`)
- TD container: `<TD_CONTAINER>` (Confluence page `<TD_CONTAINER_PAGE_ID>`)
- PRD authoring guide: `<PRD_GUIDE>` (Confluence page `<PRD_GUIDE_PAGE_ID>`)

## Core Principles

1. **The Epic is a technical document, not a splitter.** One Epic per PRD by default. Multiple Epics signals the PRD is mis-scoped; the first proposal should be to refactor the PRD, not split into Epics.
2. **Child issues are merge-ready units.** An issue's gate is "green build (`just build`), all tests pass (`just test` or the appropriate `just test*` target), this could go to main if we wanted it to." Right-sized is better than small.
3. **Research happens in the Epic phase.** By the time child issues are written, library choices, API variants, and structural questions are resolved and pinned as Technical Decisions. Child issues do not re-open decisions.
4. **Zero open questions survive into issue-writing.** Every Open Question either becomes a Technical Decision, a research page, or an explicit operator-approved deferral. When the Epic is approved, everything is locked.
5. **Reviewer findings are never attributed in Jira.** Review loops happen in Markdown. The final Epic and child issues ship clean.
6. **The operator gates every phase boundary.** The agent handles mechanics within a phase once a shape is approved. The agent never unilaterally decides a phase is done.
7. **Markdown is the authoring medium; Jira is the final destination.** Epic and child issue documents live as Markdown through drafting and review. Jira and Confluence writes happen only in Phase H.

## Task Tracking

This skill is long and operator-gated. Use the todo list as the single durable source of truth. Do not keep parallel internal lists in prose for operator questions to batch, TD candidates, reviewer findings, or gaps.

Create a todo list with one item per phase at the start:

1. Phase A — Orient
2. Phase B — Resolve Research Items and Open Questions
3. Phase C — Cross-cutting sweep
4. Phase D — Draft the Epic (Markdown)
5. Phase E — Epic Review Loop
6. Phase F — Draft Child Issues (Markdown)
7. Phase G — Issue Review Loop
8. Phase H — Commit to Jira and Confluence

Mark the current phase in_progress when you enter it. Every phase ends the same way: present what the phase produces, wait for explicit operator approval, then mark the phase completed and the next in_progress in the same update. Do not mark a phase complete before the operator closes it.

Use sub-items liberally: one per research root question in Phase B, one per TD candidate in Phase C, one per Epic section in Phase D, one per review pass and finding in E and G, one per child issue in Phase F, one per Jira/Confluence write in Phase H.

## Phase Structure

### Phase A — Orient

1. Read the Confluence PRD page fully. Verify its product area is `<PRODUCT_AREA>` and consistent with the content. If the product area is blank, unset, or inconsistent, halt and ask the operator.
2. Read the product area anchoring pages for local rules: the core product-area page (`<PRODUCT_AREA>`, page `<AREA_PAGE_ID>`) and any other anchoring pages your space defines.
3. Read the TD container (`<TD_CONTAINER>`, page `<TD_CONTAINER_PAGE_ID>`). Note existing Live TDs that may be relevant to this PRD.
4. Read the repository's root `AGENTS.md`. Identify the crate layout under `rs/`. The repository map there names the main crates and their purpose.
5. Identify which crates the PRD's work will touch. For each, read its crate-level `AGENTS.md` if present (for example `rs/<your-crate>/AGENTS.md`). Absence is a datum, not an error.
6. Choose investigation depth per area: spawn a `researcher` subagent for breadth across unfamiliar crates; use direct reads for depth when the PRD points at specific existing structure.

Phase A exit. Report to the operator: what the Epic will touch, what is known, what is unknown, any conventions that constrain the work. Nothing drafted; no Jira/Confluence writes. Wait for explicit approval to move to Phase B.

### Phase B — Resolve Research Items and Open Questions

The goal is to arrive at Phase D with zero open research questions. Questions arise from three sources: PRD Research Items, PRD Open Questions, and concerns surfaced by code analysis in Phase A.

**Depth rule: one sub-discovery deep.** Each root question may spawn direct children. Those children may not spawn their own children without stopping and asking the operator whether to go deeper. Siblings at the same depth are unbounded.

**Research dispatch.** Use `researcher` subagents for internet and codebase research. Researcher subagents are exempt from the Jira Epic execution review-loop worker model and portable finding-log contract; they produce research inputs for this PRD-to-Epic workflow, not plan/implementation/docs/branch review verdicts. Use direct file reads and searches for bounded repository questions. Use the `web_search` and `web_fetch` tools for current API and library documentation.

**Resolution outputs:**
- **Technical Decision.** The pinned outcome of a research root. Created as a Confluence TD page under `<TD_CONTAINER>`. Title follows the `A-###: Descriptive Name` convention. Include Page Properties metadata (Type: TD, ID, Product Area, Status: Live) and labels (`<TD_LABEL>`, `<AREA_LABEL>`, `<STATUS_LIVE_LABEL>`). Operator-approved per TD.
- **Research page.** A longer write-up created only when the investigation compared two or more real alternatives AND the decision would be hard to reconstruct from the TD alone. Operator approval required per research page.

**Cheap-verification default.** When a question is knowable in 30 seconds (a library's current API shape, a config key's current name, whether an error type exists), run the lookup with `grep`, `glob`, `file_read`, or `web_search` and get the answer. Do not hedge with "verify at implementation time" when the fact is knowable now. That phrase is reserved for genuine ecosystem drift.

**Research before decision prompts.** Do not ask the operator to choose between "just pick X" and "let me research first." If research would meaningfully inform the decision, run the research first and present the decision with findings in hand.

**TD lookup order.** Before proposing a new TD:
1. Same product area: is there already a Live TD covering this decision? If yes, link it and stop.
2. Same product area, prior Epics: does a prior Epic on the project contain similar decision language never promoted to a TD? If yes, propose retroactively creating the TD.
3. Other product areas: does a Live TD exist for another area that covers the same decision? If yes, propose extending it.
4. New decision: propose alternatives with a recommendation; operator chooses.

Phase B exit. Done when every root question is resolved. Wait for operator approval to proceed to Phase C.

### Phase C — Cross-Cutting Sweep

For each PRD section, ask: "If we built exactly what this section says, what other parts of the system would be affected, and did we account for that?"

Common ripple categories for this repo:
- **Wire types and shared schemas.** New types in the shared core crate that downstream crates consume.
- **Error-type hierarchy.** New errors that bubble to the CLI or daemon routes.
- **Test-harness interaction.** New testing patterns or dependencies of the integration-test harness.
- **Concurrency and state ownership.** Where does new state live? What holds the lock?
- **Dependency graph.** New workspace dependencies; dependency repin if the build system pins or vendors crates.
- **Docs.** Observable behavior changes that require updates under `docs/`. The docs site is load-bearing; check the page-to-source map in `docs/AGENTS.md`.
- **AGENTS.md.** Does the PRD formalize something that was previously implicit? Does a crate-level AGENTS.md need updating?

For each ripple: propose a TD if it should be durable (follow the Phase B lookup order); collect as a note for the Epic body if implementation-level; add a todo sub-item and surface at phase exit if the PRD is ambiguous.

**Migration handling.** Confirm the project migration stance up front (greenfield projects often have none). If the PRD is ambiguous about migration AND the Epic modifies state/schema/interfaces that existing code depends on, halt and ask.

Phase C exit. Present all at once: TD candidates with lookup class, notes for the Epic body, numbered operator prompts for PRD gaps. Wait for answers and approval to move to Phase D.

### Phase D — Draft the Epic (Markdown)

The Epic is authored as Markdown in a temp workspace. Do not create the Jira Epic yet.

Epic body structure (Markdown), in order:

1. **LLM Grounding callout.** Names the Epic, links the PRD (Confluence page link), names the product area, states the merge-ready invariant for downstream issues, states that zero open questions survive into issue-writing.
2. **Summary.** 2-4 sentences of implementation intent.
3. **Current State of the Repo.** What exists today, named at the crate level. Link prior Epics if they exist.
4. **PRD section spine, reflected.** The PRD's structural sections as H2s, each about implementation intent, not restatement. 3-8 sentences per section.
5. **Interfaces (new or changed).** Pin field shapes, HTTP status codes, SSE event types, CLI commands, SDK signatures. Covers extensions of existing interfaces.
6. **Technical Decisions.** Bulleted list of TD Confluence page links, each with a one-line gloss.
7. **Research Links.** Links to Confluence research pages if any. Omit if none.
8. **Task Sketch.** Numbered list. Each entry uses this format:
   ```
   A. <Title> — <2-3 sentences of scope>. Blocks: B, C.
   ```
   The prefix (`A`, `B`, `C`...) is what `jira-epic-run` later uses when bootstrapping its manifest. Every task receives the same planning, implementation, and review intensity. The scope sentences are what the Epic planner later reads for context. The Blocks list references prefixes, not Jira keys (keys do not exist yet). This sketch survives to Jira verbatim.
9. **Notes.** Non-TD items from Phase C.
10. **Out of scope.** Recap the PRD's Non-Goals.

Phase D exit. Present the Markdown Epic for draft sign-off. Operator approves or pushes back. Revisions in Markdown, in-place. Once approved, move to Phase E.

### Phase E — Epic Review Loop

Triggered by operator ("go review it"). Do not dispatch reviewers on your own initiative.

Prepare a review bundle in a temp directory: `prd.md` (PRD extracted to Markdown), `epic.md` (drafted Epic), `technical-decisions.md` (summarized TDs), `research-notes.md` (if any).

Dispatch three `general-purpose` subagents in parallel, all on `@mg:review`, each with a different tilt:

| Subagent | model_override | Tilt |
|---|---|---|
| Reviewer A | `@mg:review` | Architectural coherence, cross-cutting concerns, overengineering/underengineering, replace-vs-edit assessment where the Epic proposes modifying existing systems |
| Reviewer B | `@mg:review` | Requirement coverage: does the Epic cover every PRD requirement? Are acceptance criteria complete and testable? Are there gaps where requirements dropped between PRD and Epic? |
| Reviewer C | `@mg:review` | Contract flow across crates, adversarial ambiguity review, whether interfaces reconcile across consumers, integration risk |

Each reviewer gets: the review bundle path, the repo filesystem for grounding, and a prompt asking them to find real problems. Findings grouped into: load-bearing disagreements, gaps, mis-scoped issues in the sketch, missing research, non-issues.

If a pinned `model_override` does not resolve at runtime, stop and ask the operator. Do not silently substitute a weaker model.

Collect findings, synthesize, present to operator. Operator drives: approve, re-review, or incorporate-and-re-review.

Round 2 and later: validation review, not re-critique. Reference prior findings by number, ask for YES/PARTIAL/NO verdicts, and ask explicitly for new inconsistencies introduced by revisions.

During incorporation: apply straightforward revisions; spawn `researcher` subagents for new research if needed; de-scope or defer requires operator approval. No self-driven revision of substantive content. No review log in the final Epic.

If a finding reveals a PRD error, halt. Revising the PRD mid-Epic is a significant backtrack; surface this and pause for direction.

Phase E exit. Operator says "approved, move to issues." Move to Phase F.

### Phase F — Draft Child Issues (Markdown)

Produce a single Markdown document containing every child issue.

For each issue:
- **Prefix.** `A`, `B`, `C`... matching the Task Sketch from Phase D.
- **Title.** Short, descriptive, unique within this document.
- **Issue type.** Verify against the target project's issue type metadata. Common types: Task, Bug, Story.
- **Priority.** Default Medium unless the Epic or operator says otherwise.
- **Sort Order.** Explicit integer in execution sequence. Gaps of 10 or 100 are fine.
- **Scope.** Multi-paragraph. Full description of what the issue produces and its constraints.
- **Tests.** Unit (`just test-unit`), integration (`just test-integration`), acceptance criteria. Concrete behaviors to verify.
- **Blocks.** Explicit list of issue prefixes this issue blocks. Referenced by prefix.

Constraints:
- **Merge-ready rule.** Each issue, when applied, must leave the tree green: `just build` succeeds, relevant tests pass.
- **No pre-committing to internal types the Epic did not pin.** If the Epic pinned a type via TD, use it. If not, describe the contract in prose.
- **Grep before you specify a type change.** When an issue specifies a change to an existing type, run `grep` across `rs/` for every construction site and match site before finalizing. Include file paths under "Affected sites."
- **Docs awareness.** If an issue changes observable behavior, note which docs pages need updating (check the page-to-source map in `docs/AGENTS.md`). Docs updates may be a separate issue or part of the implementation issue, depending on scope.

Phase F exit. Present the Markdown issue document for draft sign-off. Once approved, move to Phase G.

### Phase G — Issue Review Loop

Same shape as Phase E. Same three `general-purpose` subagents with the same model overrides and tilts. Review bundle: approved Epic, drafted issues, summarized TDs.

Reviewers evaluate against: merge-ready violations, blocking-graph sanity (cycles, missing edges, contradicting edges), scope fidelity to the Epic, test coverage adequacy, non-issues.

Loop the same way Phase E loops, including the Round-2 validation shape.

Phase G exit. Operator says "approved, commit to Jira." Move to Phase H.

### Phase H — Commit to Jira and Confluence

A single commit step. Once this phase starts, writes begin.

**Cross-reference ordering.** Create referents first, capture keys/URLs, then create referrers. Order: Confluence TD pages → Confluence research pages → Jira Epic → Jira child issues → issue link wiring → PRD metadata update.

1. **Create Confluence TD pages** under `<TD_CONTAINER>` (page `<TD_CONTAINER_PAGE_ID>`). Each page: title (`A-###: Descriptive Name`), decision body, Page Properties metadata, labels (`<TD_LABEL>`, `<AREA_LABEL>`, `<STATUS_LIVE_LABEL>`). Record each page's URL.
2. **Create Confluence research pages** if any, as children of the product area's research page. Record URLs.
3. **Create the Jira Epic issue** in project `<PROJECT_KEY>`. Set: summary, description (the full Epic Markdown), issue type Epic. Record the Epic key.
4. **Create each child issue** in project `<PROJECT_KEY>`. Set: summary, description, issue type, priority, and link to the parent Epic. Record each issue's key in a prefix-to-key map.
5. **Wire Blocks edges.** All issues exist with known keys. For each issue with Blocks entries, create Jira issue links of type Blocks between this issue and the issues it blocks. Resolve targets from the prefix-to-key map.
6. **Update the PRD.** Add the Epic's Jira key to the PRD's Related Jira metadata in its Page Properties block.

**Schema introspection at use time.** Fetch the target project's issue type metadata and the Confluence TD container's current page structure immediately before writing. Do not rely on remembered schemas. Halt on mismatch.

**Partial-failure handling.** If any write fails, halt immediately. Report what succeeded (with keys/URLs), what failed (with error), what remains. Do not auto-retry, do not roll back.

On success, report:
- Epic key and URL.
- Child issue keys with titles, prefixes, and sort order.
- Confirmation that Blocks edges were wired.
- Confirmation that the PRD references the Epic.
- Tell the operator: to start execution, invoke `jira-epic-run`, which bootstraps `.current-epic/` from Jira.

Phase H exit. With the operator's acknowledgment, mark complete. Clean up temp scratch directories.

## Handoff to Execution

After Phase H, the Jira Epic and child issues exist. The task sketch in the Epic description carries the prefix, scope, and blocks information that `jira-epic-run` needs. When the operator invokes `jira-epic-run`:

1. It reads the Jira Epic and its child issues.
2. It bootstraps `.current-epic/manifest.txt` from the child issues (prefix from sort order, key and URL from the issue).
3. It builds `dependencies.dot` from the Blocks issue links.
4. It caches each child issue into `task-<prefix>.md`.
5. It begins the dispatch loop.

No manual state transfer is needed between this skill and `jira-epic-run`.

## Common Mistakes

| Mistake | Why it is wrong | Fix |
|---|---|---|
| Creating the Epic in Jira at the end of Phase D | Reviewers need Markdown | Keep Epic as Markdown through Phase E |
| Splitting one PRD into multiple Epics without pushing back on the PRD | Signals PRD is mis-scoped | Propose PRD refactor first |
| Making issues small instead of merge-ready | Small that leaves the tree half-wired produces dependency hell | Size each issue so `just build` and tests pass after it is applied |
| Carrying Open Questions into issue-writing | Produces avoidable surprises | Resolve via research or operator deferral before Phase F |
| Re-litigating research in issue bodies | Issues are plug-and-play | Every decision downstream issues depend on must be a TD |
| Embedding reviewer names in the final Epic | The Epic is a clean artifact | Findings inform revisions only |
| Using remembered Jira schemas | Schemas drift | Fetch issue type metadata at use time |
| Referencing Jira keys in Markdown before Phase H | Keys do not exist yet | Reference by prefix; resolve in Phase H |
| Dispatching reviewers on your own initiative | Operator gates Phase E | Wait for explicit "go review it" |
| Self-driven "review is done" | Operator closes every phase | Present findings; wait for operator |
| Skipping research to "just get started" | The cost of re-opening decisions during implementation exceeds the cost of doing it right once | The operator can override; the agent cannot cut corners |
