---
description: Define and reconcile the portable .current-epic runtime state for Jira Epic execution in Polytoken. Use before bootstrapping, resuming, spawning task workers, merging task branches, closing an Epic, or handing the Epic to another runtime.
polytoken:
  tags: [jira-epic, workflow]
---

# Jira Epic State

Use this skill whenever you inspect, create, reconcile, or update `.current-epic/` for Jira Epic execution.

The state rule is:

> A Polytoken session must be able to reconstruct the Epic run from `.current-epic/` plus git history.

Chat memory, todos, running job ids, and subagent claims are not durable truth. They are convenience state only.

## Naming

Jira project keys such as `ABC-73` identify Jira issues. Do not name Epic branches or worktrees `abc-73`; that shape reads like a task branch. Name Epic branches and worktrees with the Epic role:

```text
epic-73
epic-73-task-A
epic-73-task-B
```

When the Jira Epic key is not numeric, choose a short branch-safe slug that starts with `epic-` and records the Jira key in `manifest.txt`.

## Directory Layout

The parent orchestrator works from the Epic worktree. The portable state lives in that Epic worktree:

```text
.current-epic/
  manifest.txt
  dependencies.dot
  workflow.dot
  task-state.json
  merge-gate.json
  events.log
  task-<prefix>.md
  plan-<prefix>.md
  findings-<scope>.jsonl
  deferrals.jsonl

  runtime/
    polytoken/
      jobs.json
      active-worktrees.json
      subagent-results/
        planner-<prefix>.json
        implementor-<prefix>.json
        reviewer-<prefix>.json
```

Portable files:

- `manifest.txt`
- `dependencies.dot`
- `workflow.dot`
- `task-state.json`
- `merge-gate.json`
- `events.log`
- `task-<prefix>.md`
- `plan-<prefix>.md`
- `findings-<scope>.jsonl`, where `<scope>` is a task prefix such as `A`, a docs lane such as `docs-A`, or `epic` for final branch review
- `deferrals.jsonl`, the durable register of every accepted deferral, accepted risk, out-of-scope decision, skipped test tier, or follow-up that is not fixed in the Epic branch before closeout. Every entry must have survived the plan deferral skeptic gate. Entries that were not skeptic-approved are invalid and must be removed (and the work done instead).

Runtime-local files:

- everything under `.current-epic/runtime/polytoken/`

Do not delete runtime-local files during reconciliation. They are advisory evidence for the next Polytoken session.

## Per-Task Context Bundles

Before spawning an implementor or task reviewer, copy the task's local contract into the task worktree:

```text
.current-task/
  task.md
  plan.md
  manifest.txt
  dependency-summary.md
```

The parent creates and updates `.current-task/`. Worker subagents may read it, but they must not treat it as the source of global coordination state. The parent remains the only writer of `.current-epic/task-state.json`, `.current-epic/merge-gate.json`, and `.current-epic/events.log`.

## Manifest Contract

Write `.current-epic/manifest.txt` as plain text:

```text
Flavor: polytoken-parallel
Epic-Key: ABC-73
Epic-URL: https://<site>.atlassian.net/browse/ABC-73
Project: <PROJECT_KEY>
Epic-branch: epic-73
Epic-worktree: .worktrees/epic-73
Base-branch: main

Tasks:
A ABC-81 https://<site>.atlassian.net/browse/ABC-81 Implement durable session index
B ABC-82 https://<site>.atlassian.net/browse/ABC-82 Update CLI help text
```

The task line schema is:

```text
<prefix> <jira-key> <jira-url> <title...>
```

Do not encode task classes or concrete model names in `manifest.txt`. Epic task execution uses one standard review intensity for every task. Concrete Polytoken model choices belong in the orchestrator's subagent calls, `.current-epic/runtime/polytoken/jobs.json`, or the parent transcript.

## Dependency Graph

`dependencies.dot` is Graphviz DOT. An edge `A -> B` means Task A must complete before Task B starts.

Build this graph from Jira issue links such as Blocks / is blocked by. If Jira contains contradictory dependency links, stop and surface the conflicting issue keys.

Use the graph, `task-state.json`, and git trailers to compute task eligibility. Do not rely on in-context memory.

## Task State

`task-state.json` is the portable status checkpoint. It is advisory when it disagrees with git history. Git trailers win for completion.

Schema:

```json
{
  "schema_version": 1,
  "updated_at": "2026-06-21T12:00:00Z",
  "updated_by": "polytoken",
  "epic": {
    "jira_key": "ABC-73",
    "jira_url": "https://<site>.atlassian.net/browse/ABC-73",
    "branch": "epic-73",
    "worktree": ".worktrees/epic-73",
    "base_branch": "main"
  },
  "tasks": {
    "A": {
      "phase": "pending",
      "jira_key": "ABC-81",
      "jira_url": "https://<site>.atlassian.net/browse/ABC-81",
      "title": "Task title",
      "branch": "epic-73-task-A",
      "worktree": ".worktrees/epic-73-task-A",
      "task_cache": ".current-epic/task-A.md",
      "plan_path": ".current-epic/plan-A.md",
      "task_context_dir": ".worktrees/epic-73-task-A/.current-task",
      "job_id": null,
      "commit": null,
      "last_error": null
    }
  }
}
```

Allowed `phase` values:

- `pending`
- `planner-spawned`
- `plan-authored`
- `implementor-spawned`
- `in-progress`
- `awaiting-review`
- `review-blocked`
- `awaiting-merge`
- `merging`
- `completed`
- `blocked-failure`
- `plan-authored-halted`

Skeptic gates and the orchestrator test gate do not have separate phase values;
they run between existing phases (after review-clean, before the next phase) and
hold the task in its current phase until they pass. Dynamic tasks appended by the
orchestrator use `phase: "pending"` and are processed identically to original
tasks.

When reconstructing missing state, derive task records from `manifest.txt`, `dependencies.dot`, existing `plan-*.md` files, `merge-gate.json`, and git log trailers.

## Merge Gate

Use `.current-epic/merge-gate.json` to serialize task branch merges into the Epic branch:

```json
{
  "holder": null,
  "queue": []
}
```

The holder should be `implementor-<prefix>` or `task-<prefix>`. The merge gate is separate from the repository-level `.merge-lock`, which only protects final merges to `main`.

Grant order:

1. Verify the holder is null.
2. Write `merge-gate.json` with the new holder.
3. Update `task-state.json` phase to `merging`.
4. Append `merge-granted` to `events.log`.

Release order:

1. Verify the task commit exists on the Epic branch with matching trailers.
2. Update `task-state.json` to `completed` and record the commit.
3. Release the holder.
4. Append `task-merged` to `events.log`.

## Deferral Register

`deferrals.jsonl` is portable JSONL and is the durable source of truth for work
that is consciously not fixed before Epic closeout. Chat messages, todos, Jira
comments, and reviewer summaries are not enough. If the parent accepts a
follow-up, skips a relevant test tier, narrows a task scope, carries an accepted
risk, or decides not to fix a review finding in the Epic branch, it must append a
record immediately. **However, deferrals are only permitted when something is
computationally impossible.** Every deferral must survive the plan deferral
skeptic gate (a `general-purpose` subagent with `@mg:arch` using
hostile/skeptical prompting). The skeptic's verdict is binding. A deferral
record that has not been skeptic-approved is invalid.

```json
{"schema_version":1,"deferral_id":"ABC-73-D001","created_at":"2026-06-21T12:00:00Z","scope":"G","jira_key":"ABC-88","kind":"test-tier-skipped","severity":"high","summary":"Compaction-before-continuation was not covered by provider double.","reason":"No deterministic provider double compaction harness exists yet.","operator_decision":"approved","skeptic_approved":true,"skeptic_verdict":"The provider double compaction harness requires daemon API surface changes that are computationally impossible within this task scope.","evidence":[".current-epic/findings-G.jsonl:G-plan-2-F5"],"follow_up":"Create a dedicated compaction harness task before release.","status":"open"}
```

Required fields: `schema_version`, `deferral_id`, `created_at`, `scope`, `kind`,
`severity`, `summary`, `reason`, `operator_decision`, `skeptic_approved`, and
`status`. When `skeptic_approved` is true, include `skeptic_verdict` with the
skeptic's reasoning. Use stable
`deferral_id` values and append updates rather than rewriting history. Allowed
`status` values are `open`, `closed`, and `superseded`. Allowed `kind` values
include `accepted-risk`, `scope-deferral`, `test-tier-skipped`, `docs-deferral`,
`follow-up`, and `operator-decision`. Critical/high deferrals require an explicit
operator decision note; do not invent approval. A deferral with
`skeptic_approved: false` or missing `skeptic_approved` is invalid and the work
must be done instead.

At closeout, every open deferral must be surfaced in the Jira summary and final
operator message. If an open deferral is discovered during reconciliation but is
not in `deferrals.jsonl`, append it before continuing.

## Events Log

`events.log` is JSONL. Append one line per state transition:

```json
{"ts":"2026-06-21T12:00:00Z","runtime":"polytoken","event":"plan-authored","task_prefix":"A","details":{"plan_path":".current-epic/plan-A.md"}}
```

Use this event vocabulary when possible:

- `bootstrap-started`
- `bootstrap-completed`
- `plan-spawned`
- `plan-authored`
- `implementor-spawned`
- `implementation-started`
- `review-spawned`
- `review-completed`
- `merge-requested`
- `merge-granted`
- `task-merged`
- `task-blocked`
- `runtime-handoff`
- `closing-started`
- `closing-completed`

The log is audit evidence, not the current-state source of truth.

## Commit Trailers

Every task merge commit on the Epic branch must include Jira keys:

```text
Epic: ABC-73
Task: ABC-81
```

Task completion is true only when the Epic branch contains a commit between `Base-branch..HEAD` with the matching `Task:` trailer. If `task-state.json` says `completed` but no matching trailer exists, mark the task blocked and surface the corruption.

Epic-level fix commits made during closeout include only the Epic trailer:

```text
Epic: ABC-73
```

## Reconciliation Procedure

When bootstrapping, resuming, or handing off:

1. Read `manifest.txt`.
2. Read `dependencies.dot`.
3. Read `task-state.json` if present.
4. Read `merge-gate.json` if present; otherwise create `{"holder": null, "queue": []}`.
5. Scan `.current-epic/plan-*.md`.
6. Scan `.current-epic/findings-*.jsonl` and reconstruct the latest finding disposition for each stable finding id. These files cover task plan/implementation reviews, docs lane reviews, and final Epic branch review. If two records share a `finding_id` but disagree on `scope` or `phase`, stop and surface state corruption.
7. Scan `.current-epic/deferrals.jsonl` if present and reconstruct open/closed/superseded deferrals. If an accepted-risk finding, skipped relevant test tier, narrowed scope, or follow-up appears in portable findings or review summaries but has no matching deferral record, append one before continuing. Critical/high deferrals require an explicit operator decision note.
8. Defensively scan completed review results under `.current-epic/runtime/polytoken/subagent-results/`. If a completed review generation has findings absent from the matching portable finding log, append them to the portable log as `open` before applying gates. Runtime files remain advisory after this fold-in step.
9. Run `git log --format=%H%n%B <base>..HEAD` on the Epic branch.
10. For each manifest task:
   - If git has the task trailer, set `phase = completed` and record the commit.
   - Else if a plan exists and phase is missing, set `phase = plan-authored`.
   - Else preserve the existing non-completed phase if plausible.
   - Else set `phase = pending`.
11. If a task has open critical/high plan findings, keep it at `review-blocked` rather than `plan-authored`. If a task has open critical/high implementation findings, keep it at `review-blocked` rather than `awaiting-merge` or `completed` unless git already has the matching `Task:` trailer. If `findings-epic.jsonl` or any `findings-docs-*.jsonl` file has open critical/high findings, do not consider closeout clean on resume.
12. If `merge-gate.json.holder` references a completed task, release it after verifying the trailer.
13. Append `runtime-handoff`, `bootstrap-completed`, or another appropriate event.

## Handoff Rules

Before a long pause or runtime handoff:

1. Stop spawning new work.
2. Let in-flight merges finish or explicitly mark them blocked.
3. Reconcile `task-state.json` against git trailers.
4. Write `merge-gate.json`.
5. Append `runtime-handoff` with the outgoing runtime and known active task/job ids.
6. Leave `.current-epic/` in place.

Never delete `.current-epic/` during handoff.
