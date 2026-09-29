---
description: Close a Jira Epic runtime after all tasks are merged to the Epic branch. Use for final reconciliation, cross-task code review, linear docs work, Jira summary, and handoff before any final merge to main.
polytoken:
  tags: [jira-epic, workflow]
---

# Jira Epic Close

Close a Jira Epic after every manifest task has a verified `Task:` trailer on the Epic branch. The goal is to reconcile state, review the shipped Epic branch, complete documentation work, and stop before the final merge to `main` unless the operator gives a fresh explicit instruction.

## Preconditions

1. Invoke `jira-epic-state`.
2. `.current-epic/manifest.txt` exists.
3. Every manifest task key has a matching `Task:` trailer in `git log --format=%B <base>..HEAD`.
4. `merge-gate.json.holder` is null.
5. No task in `task-state.json` is `in-progress`, `awaiting-review`, `awaiting-merge`, or `merging`.
6. The **epic closeout skeptic** has passed (see Epic Closeout Skeptic in `jira-epic-run`).

If any precondition fails, stop and surface the exact mismatch.

## Deferral Invariant

Any accepted risk, skipped relevant test tier, narrowed scope, follow-up, or
remaining notable that is not fixed before closeout must be recorded in
`.current-epic/deferrals.jsonl` using the schema in `jira-epic-state`. However,
deferrals are only permitted when something is **computationally impossible**.
Every deferral must have `skeptic_approved: true` with a `skeptic_verdict`
explaining why the work is literally impossible. Chat, todos, Jira comments, and
reviewer summaries are not sufficient. Before writing any final Jira summary or
operator handoff, read `deferrals.jsonl`; if you find a remaining deferral that
is not recorded there or that lacks skeptic approval, do not append it — instead,
create a dynamic task to fix the work. Every open (skeptic-approved) deferral must
be surfaced in the Jira summary and final message.

## Final Code Review

1. Reconcile portable state.
2. Append `closing-started` to `events.log`.
3. Dispatch the standard three-member `general-purpose` branch review panel in the Epic worktree, all on `@mg:review`:
   - `@mg:review` for architecture and cross-task coherence.
   - `@mg:review` for mechanical correctness, omissions, edge cases, and test adequacy.
   - `@mg:review` for adversarial contract review, ambiguity, and integration risk.
   If any pinned `model_override` does not resolve, stop and ask the operator; do not silently substitute another model.
4. Ask reviewers to answer:
   - Does the shipped code match each Jira task and accepted plan?
   - Does the shipped code work as code independent of the tickets?
   - Do the completed tasks compose correctly after being merged together?
5. Classify findings:
   - `critical`: must fix before handoff.
   - `high`: must fix before handoff.
   - `medium`: fix by default unless the operator explicitly defers.
   - `low`: defer unless trivial and adjacent.
6. Fix critical/high findings on the Epic branch. Use only the Epic trailer:
   ```text
   Epic: <epic-key>
   ```
7. Re-run the standard branch review panel until the review loop exit condition from `jira-epic-run` is satisfied.

## Documentation Closeout

After code review is clean:

1. Decide docs lanes from the Epic diff and docs map.
2. Run docs lanes linearly by spawning `general-purpose` docs writers with `model_override: "default_model:full"` and prompts that load `jira-epic-docs`.
3. For each docs lane, run the standard three-member `general-purpose` docs review panel against the resulting docs generation.
4. Feed the full portable docs finding log into the next docs writer generation for the same lane.
5. Do not start the next docs lane until the review loop exit condition from `jira-epic-run` is satisfied for the current lane.
6. Track every touched docs file for the final human-review warning.

## Jira Summary

Add an Epic comment with:

- completed task keys,
- commit range reviewed,
- tests run,
- review rounds completed,
- docs files touched,
- open deferrals from `.current-epic/deferrals.jsonl`,
- remaining notables or operator decisions.

Do not transition the Epic or child tasks automatically unless the operator approved that policy for this Epic run.

## Final State

1. Reconcile `.current-epic/` one final time.
2. Append `closing-completed` to `events.log`.
3. Leave `.current-epic/` in place.
4. Do not merge to `main`, push, or create a PR unless the operator gives a new explicit instruction after this closeout.

## Final Message

Report:

- Final verdict: `READY-TO-MERGE`, `READY-WITH-NOTABLES`, or `BLOCKED`.
- Epic key, Epic branch, and base branch.
- Commit range reviewed.
- Task commits and Epic-level fix commits.
- Tests run.
- Docs files touched, with a prominent human-review warning.
- Open deferrals from `.current-epic/deferrals.jsonl`, including accepted risks, skipped test tiers, narrowed scope, and follow-up work.
- Notables or remaining operator decisions.
- Confirmation that `.current-epic/` remains in place.
