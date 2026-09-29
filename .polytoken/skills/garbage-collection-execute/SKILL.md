---
description: Execute a garbage-collection handoff plan using Epic-like parent and child worktree rails, materialized .current-gc state, todo-tracked lifecycle checkpoints, review loops, and merge-lock finalization. Use when handed a plan from garbage-collection-plan.
polytoken:
  tags: [garbage-collection, workflow, execution]
---

# Garbage Collection Execute

You operate in the **execute facet** on a handoff plan produced by `garbage-collection-plan`. Reinforce the procedural steps here even if the plan already states them.

Garbage collection (GC) is behavior-preserving entropy reduction. It rationalizes code for future agent legibility without changing product contracts or user-visible behavior unless the operator explicitly approved that exception in the handoff plan. If you discover that a cleanup unit requires behavior, API, CLI, config, permission, event, tool, or other public-surface change, stop that unit and surface it as `ejected_from_gc` or an operator decision. Do not quietly broaden scope.

## Required Inputs

The handoff plan must provide:

- execute skill name: `garbage-collection-execute`;
- classification, normally `patch`;
- GC run id;
- scope;
- parent branch name and parent worktree path;
- cleanup units with ids, dependencies, expected areas, tests, and done criteria;
- draft gradebook events / canonical clusters from planning;
- operator decision items and deferrals;
- review strategy;
- merge strategy.

If any required input is missing, stop and ask the operator. Do not invent branch names, run ids, or cleanup-unit scope.

## Todo Discipline Is Mandatory

The todo list is the live execution checklist and compaction recovery rail. Use it before touching files.

Create todos for at least:

- read and validate the handoff plan;
- confirm classification and scope;
- materialize `.current-gc/`;
- create parent GC worktree;
- create every child cleanup worktree;
- execute each cleanup unit;
- run tests for each cleanup unit;
- review each cleanup unit;
- merge each child branch into the parent GC branch;
- update gradebook/events after each unit;
- final GC branch review;
- final test sweep;
- operator acceptance checkpoint;
- repository merge-lock acquisition;
- squash merge to `main`;
- worktree cleanup;
- final report.

After every major checkpoint, list or mentally reconcile todos and mark any completed-but-overlooked item done. Do not leave stale todos pending for completed work. If compaction, long tests, or subagent waits occur, reconcile todos before continuing. If a cleanup unit is ejected, deferred, or blocked, update both the todo and `.current-gc/events.log` / `.current-gc/gradebook.jsonl`.

## On-Disk State

Materialize `.current-gc/` in the parent GC worktree unless the handoff plan explicitly says otherwise. The state is portable and append-oriented. It should be sufficient to resume after compaction.

Recommended layout:

```text
.current-gc/
  manifest.txt
  scope.md
  workflow.dot
  events.log
  gradebook.jsonl
  clusters.jsonl
  cleanup-units/
    A.md
    B.md
  plans/
    plan-A.md
    plan-B.md
  findings/
    findings-A.jsonl
    findings-B.jsonl
    findings-final.jsonl
  deferrals.jsonl
  runtime/polytoken/subagent-results/
```

Append `.current-gc/` to `.gitignore` if absent, unless the operator explicitly wants the runtime state checked in. The default is runtime state, not product source.

### Event-Sourced Gradebook

Use `gradebook.jsonl` as an event log, not a mutable score sheet. Preserve raw findings and canonical cluster transitions as events. Do not rewrite prior events to make the history look cleaner.

Common events:

- `raw_discovered`
- `clustered`
- `verified`
- `rejected`
- `duplicate_merged`
- `needs_more_evidence`
- `cleanup_ready`
- `planned`
- `in_progress`
- `cleaned`
- `deferred`
- `blocked`
- `ejected_from_gc`
- `accepted_risk`
- `stale_expired`

Every event should include:

```json
{"schema_version":1,"run_id":"...","event":"...","at":"<ISO timestamp>","by":"<agent/session>","cluster_id":"...","cleanup_unit":"...","notes":"..."}
```

Include evidence paths and verifier/finder provenance when relevant. Avoid numeric or letter grades unless explicitly approved; prefer compact health summaries such as `clear`, `watch`, `degraded`, and `blocked`.

## Worktree Rails

Start at the repository root.

1. Create the parent GC worktree from `main` using the exact branch name in the handoff plan, for example:

   ```text
   direnv exec . just worktree-create gc-2026-06-catchup
   ```

2. `pushd .worktrees/<parent-branch>` once. `pushd` is session state and persists across later file, grep, glob, shell, and subagent calls. Stay pushed into the parent worktree for GC orchestration until the final repository merge gate.

3. Materialize `.current-gc/` in the parent worktree. Write the handoff plan’s clusters, gradebook draft events, cleanup units, workflow graph, and deferrals into the layout above.

4. For each cleanup unit, create a child worktree/branch from the parent GC branch:

   ```text
   <parent-branch>-task-A
   <parent-branch>-task-B
   ```

   Use the project’s worktree helper when possible. Pass each child worktree as the subagent `cwd`. Child agents must not `popd` above their worktree, coordinate with siblings, merge to the parent branch, delete worktrees, or mutate `.current-gc/` coordination files except files explicitly copied into their child worktree.

5. The parent owns all merges from child task branches into the parent GC branch.

## Cleanup Unit Execution

For each cleanup unit:

1. Confirm dependencies are complete.
2. Write/copy the unit plan to `.current-gc/plans/plan-<unit>.md`.
3. Append `in_progress` to `gradebook.jsonl` and `events.log`.
4. Spawn a `general-purpose` implementor subagent in the child worktree. The prompt must include:
   - run id;
   - cleanup unit id;
   - child branch/worktree;
   - parent branch/worktree;
   - plan path;
   - exact scope and non-goals;
   - behavior-preserving requirement;
   - test commands;
   - commit trailer requirement, if the plan defines one;
   - prior reviewer findings if this is a later generation.
5. Independently verify the implementor result. Do not trust a ready claim without checking commits, tests, and scope.
6. Run required tests through `direnv exec .` in the appropriate worktree.
7. Run review loop before merging.

If a cleanup unit is impossible as written, append `blocked` with a concrete reason and ask the operator or re-plan. Difficulty is not impossibility.

## Test Requirements

Use the handoff plan’s test strategy as the minimum. Add focused tests when implementation reveals missing coverage.

Rules:

- Pure logic requires crate-local unit tests.
- Provider-dependent behavior must use provider-double-backed daemon or integration tests rather than lower-level mocks.
- Full daemon-stack behavior should use the project integration harness (real daemon with the provider double) where applicable.
- TUI-visible behavior requires render/scenario tests for observable text, layout, style, focus, scrolling, input, mouse, or hydration behavior as applicable.
- Running a broad suite is not proof of coverage for new cleanup behavior. New or modified tests must exercise the behavior-preserving invariant the cleanup could break.
- A skipped test is not a pass. Record exact skip reasons in `.current-gc/deferrals.jsonl` and the final report.

Normally run, as applicable:

```text
direnv exec . just fix
```

Then commit to the task branch — the pre-commit hook runs the full project
test suite (`just test` on non-main branches: unit + integration, no live
providers) plus `just build` and `just machete`. Do not manually run `just
test-unit`, `just test-integration`, or `just test`; the hook is the test
runner. If the hook fails, fix and re-commit.

Use feature-specific build-system/TUI targets when the handoff plan or local `AGENTS.md` requires them. `just test-all` runs automatically via the pre-commit hook when merging to `main`.

## Implementation Review Loop

For each cleanup unit, run implementation reviewers before parent merge. Prefer the repository’s standard heavy review shape unless the handoff plan specifies a stricter one.

A typical panel:

- `general-purpose` with `model_override: @mg:arch` — architecture, over/under-engineering, boundary fit;
- `general-purpose` with `model_override: @mg:workhorse` or another operator-approved medium model — mechanical correctness, omissions, edge cases;
- `general-purpose` with `model_override: @mg:review` — adversarial contract and integration risk.

If the handoff plan specifies verifier models such as `@mg:arch`, use those exact models. If a pinned model does not resolve, stop and ask the operator. Do not silently substitute a weaker model.

Reviewers must check:

- cleanup remains behavior-preserving;
- no public/user-visible contract changed unintentionally;
- deduplication follows the GC rules and did not introduce a wrong abstraction;
- ownership boundaries remain correct;
- file and function sizes remain agent-legible: files over roughly 2,000 lines and functions over roughly 300 lines are not automatic blockers, but reviewers must interrogate whether they should be decomposed; prefer smaller focused functions and separate test files where practical;
- tests cover the right layer;
- docs/AGENTS updates are correct when applicable;
- no new entropy was introduced.

**Fix or explicitly rebut every finding at every severity.** There is no "follow-up" tier — any finding not fixed or rebutted in this pass is effectively dropped because no external tracking captures it. Re-run reviewers while any critical or high finding remains; medium and low findings must also be resolved before merge. Append findings and dispositions to `.current-gc/findings/findings-<unit>.jsonl`. A later clean review does not erase unresolved earlier findings.

## Parent Merge Of Child Branches

Only the parent merges child branches into the parent GC branch.

Before merging a child branch:

- child branch has committed work;
- required tests passed or deferrals are operator-approved;
- no critical/high review findings remain (medium/low must also be fixed or rebutted);
- all prior findings have dispositions;
- `.current-gc/gradebook.jsonl` has an event for the unit’s current state.

Merge one child branch at a time into the parent GC worktree. Prefer squash merges unless the handoff plan explicitly requires preserving child commits. After merging, append `cleaned` for the cleanup unit with the parent-branch commit hash when available. Mark corresponding todos complete.

## Final GC Branch Review

After all selected cleanup units are merged into the parent GC branch:

1. Reconcile todos; mark completed-but-overlooked items done.
2. Reconcile `.current-gc/gradebook.jsonl`, `events.log`, `deferrals.jsonl`, and findings logs.
3. Run the final test sweep required by the handoff plan.
4. Spawn a final branch review panel over the parent GC branch against `main`. Reviewers must look for:
   - cross-unit conflicts;
   - behavior or contract drift;
   - wrong abstractions introduced by deduplication;
   - oversized files or functions left unexamined, especially files over roughly 2,000 lines, functions over roughly 300 lines, and large inline test modules that could become separate test files;
   - tests that no longer map to cleanup risk;
   - docs/AGENTS drift;
   - unresolved deferrals that should block merge.
5. Fix or rebut **all** findings at every severity. Re-run while any critical/high finding remains.
6. Surface all accepted risks, deferrals, and ejected findings to the operator before asking for merge acceptance.

## Final Merge Gate

Only after explicit operator acceptance:

1. `popd` back to the project root. If already at the root and `popd` errors at the stack floor, continue.
2. Acquire `.merge-lock` atomically per root `AGENTS.md`. Acquire the lock before touching `main`. Dirty `main` before lock acquisition is not a failure; another lock holder may be mid-merge. Wait for the lock rather than stashing/resetting.
3. Bring `main` up to date with `direnv exec . git fetch` and a fast-forward merge.
4. Rebase the parent GC worktree branch onto updated `main`.
5. Run the final required test command(s) after rebase.
6. Squash-merge the parent GC branch into `main` and commit through `direnv exec .` so hooks and credentials are available.
7. Branch policy: all work lands on `main` only (see root `AGENTS.md` "Branch Model"). There is no `stable` branch and no cherry-pick dual-merge.
8. Release `.merge-lock` owner-checked.
9. Remove child and parent worktrees with the project helper, normally `direnv exec . just worktree-remove <branch>`.
10. Reconcile todos again and mark completed items done.

## Documentation Rules

If cleanup changes human-facing documentation under `docs/`, prominently tell the operator in the final report and name the touched files. Human review is required. AGENTS.md files are robot-facing and do not require that warning, but still require correctness.

If observable behavior changes would require docs, the unit probably left GC scope. Stop and surface the mismatch unless the handoff plan explicitly approved the behavior change.

## Final Report

After worktrees are removed, run:

```text
direnv exec . just run-cli --help
```

to prime the CLI cache when practical.

Report:

- GC run id and scope;
- parent branch merged;
- cleanup units completed;
- tests and review panels run;
- gradebook/event summary;
- deferrals and accepted risks;
- ejected architectural/product concerns;
- files or subsystems changed;
- any docs requiring human review;
- concrete advice for how the operator can inspect or exercise the cleanup.

The run is not complete until todos are reconciled, `.current-gc` state is updated, merge-lock is released, worktrees are removed, and the final report is delivered.
