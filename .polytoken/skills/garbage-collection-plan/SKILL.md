---
description: "Plan a Polytoken garbage-collection run: read-only broad-phase entropy discovery, verifier review, finding consolidation, todo-tracked state, and a handoff plan for garbage-collection-execute. Use when the operator asks to rationalize, prune, deduplicate, or prepare the codebase for the next expansion phase."
polytoken:
  tags: [garbage-collection, workflow, planning]
---

# Garbage Collection Plan

You operate in the **plan facet**. Your job is to perform a read-only garbage-collection planning pass and produce a handoff plan for `garbage-collection-execute`. Do not implement code changes. Do not create Jira issues. Do not materialize `.current-gc/` in the repository from the plan facet unless the operator explicitly changes the facet/tooling contract; the execute skill owns on-disk GC state.

Garbage collection (GC) is a periodic entropy-reduction workflow for agent-maintained code. It is not a mega-refactor license. The planning pass discovers, verifies, deduplicates, and decomposes cleanup work so the execute facet can perform targeted, behavior-preserving changes on Epic-like worktree rails.

## Core Principles

GC optimizes for future agent legibility, correctness, and local ownership.

1. **Ownership boundaries are respected.** Code should live where the repository map and local `AGENTS.md` files say it belongs. Pure crates stay pure; system-specific boundaries remain intact.
2. **Shared invariants are centralized; incidental similarity is not.** Consolidate duplicated rules and invariants, not merely similar-looking syntax.
3. **Boundaries are typed, validated, and forward-compatible.** Prefer typed contracts and explicit validation over probing guessed shapes or relying on loose data.
4. **Agent-facing maps are accurate and local.** Root and crate `AGENTS.md` files should remain truthful, concise, and positioned near the code they describe.
5. **Tests live at the right layer.** Pure logic needs unit tests; provider-visible behavior needs provider-double coverage; full daemon behavior needs integration coverage; TUI-visible behavior needs render/scenario coverage.
6. **Repeated review comments should become checks.** If humans or reviewers repeatedly enforce a rule, consider whether it should become a lint, `just check-*`, schema assertion, or test.
7. **Modules remain navigable for agents.** Avoid bloated orchestration files, helper sprawl, and APIs that require excessive context to use safely. Treat file and function size as entropy signals: files over roughly 2,000 lines and functions over roughly 300 lines are not automatically wrong, but every GC pass should interrogate them for decomposition opportunities. Prefer smaller focused functions and, where practical, moving large test modules into separate test files because agents reason better over narrower files.
8. **GC remains behavior-preserving.** Anything that changes product behavior, public contracts, configuration, CLI/API/tool surface, permission semantics, or user-facing interaction is ejected from GC and surfaced to the operator.

## Deduplication Rules

Use these rules before recommending consolidation:

- Abstract behavior, not syntax. Similar code is not enough; the code must represent the same invariant or reason to change.
- Ask whether both copies should change for the same reason. If not, preserve duplication.
- Treat a third occurrence as suspicion, not proof. Semantic coupling proves the case.
- Reject abstractions that require many flags, optional parameters, caller-specific branches, or vague generic names.
- Prioritize duplication by discoverability, maintenance overhead, traffic/change frequency, boundary sensitivity, and likelihood that future agents will copy it again.
- Prefer the smallest useful abstraction. Do not add public API surface just for elegance.
- For messy duplication, stabilize and test first; extraction can be a later cleanup unit.
- A valid GC cleanup may inline or delete a bad abstraction instead of creating a new one.

## Todo Discipline Is Mandatory

Because the plan facet does not write the durable `.current-gc/` tracker, the todo system is the live operational tracker during planning. Use it aggressively.

At the start, create todos for at least:

- confirm scope and run id;
- inspect relevant repository instructions;
- deterministic census;
- finder fanout;
- raw finding collection;
- clustering/deduplication;
- verifier fanout;
- gradebook event draft;
- cleanup-unit decomposition;
- operator decision items;
- final handoff plan;
- plan review and handoff.

Keep the todo list current. After every major phase, review the todo list and mark any completed-but-overlooked items done. Do not leave stale pending todos for work already completed. If compaction or a long subagent wait happens, reconcile todos before continuing.

When writing the handoff plan, include a required execute-facet todo checklist and tell execute to materialize the todo state into `.current-gc/events.log` and `.current-gc/gradebook.jsonl`.

## Scope Modes

Support variadic scope. Ask the operator only when scope is materially ambiguous.

- **whole-repo catchup**: full repository survey; expected for the first GC run.
- **crate-cluster**: a named cluster such as daemon tools + project_fs, TUI + client + event types, providers + core provider traits, or config + docs + schemas.
- **principle scope**: one or more principles across the repo, such as deduplication, boundary ownership, docs/AGENTS drift, or test layering.
- **recent-delta**: inspect changes since a base ref/tag/commit and ask whether recent work introduced entropy.

A large survey is allowed. Large unstructured code diffs are not. The plan should decompose work into coherent cleanup units.

## Finder Fanout

Run read-only `general-purpose` subagents as finders. Prefer large-context models such as `@mg:review` when available and when the operator has requested that model. If a pinned model does not resolve, stop and ask; do not silently weaken the gate.

Use overlapping finder prompts. Combine:

- **principle finders**: ownership, dedup/shared invariants, typed boundaries, AGENTS/doc drift, test layering, mechanizable rules, module navigability, behavior-preserving scope;
- **system graph finders**: traits and all impls/call sites, routes and wire types, provider interfaces and implementations, tool definitions and registry/execution paths, config keys and schema/docs/runtime users, TUI state/render/event paths, crate boundaries and dependencies.

Finder agents must return raw findings only. They must not edit files, write plans, or decide final execution scope.

Each raw finding should include:

```yaml
schema_version: 1
run_id: <gc-run-id>
raw_finding_id: <finder-stable-id>
principle: <principle>
kind: duplication|boundary_drift|typed_boundary_gap|doc_drift|test_gap|module_bloat|oversized_file|oversized_function|deadweight|mechanize_rule|other
summary: <one paragraph>
canonical_paths: [<path>]
evidence:
  - path: <path>
    lines: <line or range>
    excerpt: <short excerpt when useful>
severity: low|medium|high|critical
confidence: low|medium|high
classification_hint: patch|minor|unclear
why_it_matters_for_agents: <specific future-agent risk>
suggested_cleanup: <behavior-preserving cleanup idea or null>
needs_operator_decision: true|false
```

## Clustering And Canonicalization

The parent planner, not the finders, deduplicates raw findings into canonical clusters.

For each cluster, draft a stable fingerprint from:

- principle;
- normalized canonical path set;
- finding kind;
- concise invariant/concern description.

Line numbers are evidence, not identity. If line numbers drift, the fingerprint should still identify the concern.

Canonical cluster statuses:

- `raw_discovered`
- `candidate`
- `clustered`
- `verified`
- `cleanup_ready`
- `planned`
- `deferred`
- `rejected`
- `duplicate_merged`
- `needs_more_evidence`
- `blocked`
- `ejected_from_gc`
- `stale_expired`
- `accepted_risk`

Statuses should be monotonic where possible. Do not mutate the meaning of an original raw finding; append disposition events.

## Verifier Fanout

Verifier agents provide second opinions. They should mirror finder **coverage**, not finder psychology.

Use narrower prompts and smaller/more numerous models, such as `@mg:arch` when the operator requests it and the model resolves. Verifiers inspect canonical clusters, not free-form repo areas. Give them evidence and GC rules; do not ask them to rubber-stamp the finder hypothesis.

Verifier decisions:

- `verified`: finding is real and suitable for GC consideration;
- `rejected`: not a real finding under GC rules;
- `duplicate_merged`: same concern as another cluster;
- `needs_more_evidence`: cannot conclude from evidence;
- `deferred`: valid but not for this run;
- `ejected_from_gc`: implies behavior/contract/product/surface change;
- `operator_decision`: requires architectural/product judgment.

Run at least one verifier per cluster selected for possible cleanup. Use additional verifiers for high-impact, high-risk, or ambiguous clusters. A verified finding must cite evidence and explain why the suggested cleanup remains behavior-preserving.

## Gradebook Draft

The plan facet should draft gradebook events in the handoff plan; execute materializes them on disk.

Use an event-sourced shape, not a mutable score spreadsheet. Raw finder output stays separate from canonical cleanup-bearing entries.

Event examples:

```json
{"schema_version":1,"event":"raw_discovered","run_id":"gc-2026-06-catchup","raw_finding_id":"...","by":"finder-...","model":"@mg:review","evidence":["path:line"]}
{"schema_version":1,"event":"clustered","run_id":"gc-2026-06-catchup","cluster_id":"...","fingerprint":"...","raw_finding_ids":["..."]}
{"schema_version":1,"event":"verified","run_id":"gc-2026-06-catchup","cluster_id":"...","by":"verifier-...","model":"@mg:arch","decision":"verified","confidence":"high"}
{"schema_version":1,"event":"cleanup_ready","run_id":"gc-2026-06-catchup","cluster_id":"...","cleanup_unit":"A"}
```

Avoid false precision. Prefer `clear`, `watch`, `degraded`, `blocked` summaries over numeric or letter grades unless the operator explicitly asks for scores.

## Cleanup Units

Only verified or operator-approved clusters can become cleanup units. A cleanup unit should be individually understandable and testable.

Each cleanup unit must include:

- id (`A`, `B`, ...);
- title;
- source cluster ids;
- classification: normally `patch`; `minor` or `unclear` requires operator decision and usually ejection from GC;
- expected files/areas;
- behavior-preserving implementation intent;
- explicit non-goals;
- risk level;
- test strategy with applicable tiers;
- docs/AGENTS impact;
- file/function size assessment when relevant, including whether large source or test modules should be decomposed;
- dependencies on other cleanup units;
- done criteria.

## Operator Decisions

Ask the operator when a decision materially changes execution, especially:

- whether a finding that may change behavior should be ejected or converted into normal product work;
- whether to accept a high/critical risk deferral;
- whether to include a large cleanup unit in the current run;
- whether a proposed abstraction is architecturally desired.

Do not create Jira issues. Larger architectural concerns should be listed as operator decision items.

## Plan Tool Use

Use the plan-facet tools as control-plane tools:

- `write_plan`: write the final GC execution handoff plan.
- `edit_plan`: revise the active plan after reviewer/operator feedback using a unique string replacement.
- `handoff_plan`: submit the latest written plan to execute. Call it only after the plan is ready and by itself.

The handoff plan must name `garbage-collection-execute` as the execute skill.

## Handoff Plan Required Shape

The plan passed to execute must include:

1. `## Classification: patch` unless the operator explicitly approved otherwise. GC is behavior-preserving by default.
2. Goal and scope.
3. Run id and branch names:
   - parent branch: `gc-<date-or-label>`
   - parent worktree: `.worktrees/<parent-branch>`
   - child branches/worktrees: `<parent-branch>-task-<prefix>`
4. Explicit instruction that execute materializes `.current-gc/` on disk.
5. Todo checklist requiring execute to track every phase and reconcile completed-but-overlooked todos after each checkpoint.
6. Golden principles applied.
7. Finder fanout summary.
8. Verifier fanout summary.
9. Draft gradebook events and canonical clusters.
10. Cleanup units with dependencies and done criteria.
11. Operator decision items and deferrals.
12. Acceptance criteria.
13. Test strategy, including applicable unit/provider-double/integration/UI tiers per cleanup unit.
14. Review strategy:
    - child implementation review loops;
    - final GC branch review;
    - fix/rebut every finding;
    - re-run while any critical/high remains.
15. Documentation strategy, including AGENTS/doc updates and human-review warning for any `docs/` changes.
16. Merge strategy under `.merge-lock` after operator acceptance.
17. Final report requirements.

## Review Before Handoff

Before `handoff_plan`, review the plan. Prefer a panel patterned after Epic/solo-tasker review when the run is large. Reviewers must audit:

- whether every cleanup unit follows GC principles;
- whether verifier decisions are recorded;
- whether behavior-changing work was ejected;
- whether tests are mapped to the right tiers;
- whether todo and `.current-gc` materialization instructions are explicit;
- whether the execution plan is decomposed enough for child worktrees.

Fix valid findings with `edit_plan`, or record explicit rebuttals/accepted risks in the plan. Do not hand off with unresolved critical/high plan findings.
