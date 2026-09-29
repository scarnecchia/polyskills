---
description: "Use when recording out-of-scope bugs, collecting permitted non-blocking review follow-ups, closing fixed housekeeping issues, or processing a housekeeping backlog on GitHub or Tangled."
---

# Housekeeping

Record bugs outside the current task's scope as issues in the repository's
GitHub or Tangled issue tracker. Apply the `housekeeping` label so future
work can find them without a parent issue or a dedicated project.

## Scope and Destination

- Use the repository's established issue tracker. If both hosts are used,
  follow its contribution instructions; ask if the destination is unclear.
  File on one host, not both.
- Every issue filed through this skill must have the `housekeeping` label.
  Use the repository's bug template and bug classification where available.
- Keep in-scope fixes in the current task. This skill does not authorize
  deferring required work or bypassing a review gate.
- File out-of-scope observations without a separate confirmation when the
  project's permissions allow it. Filing does not authorize implementation.
- Use authenticated issue tooling or the host's web interface. Check the
  available operations before using a CLI or API; do not assume both hosts
  support the same commands, issue types, or workflow states.
- Keep credentials and sensitive logs out of issue bodies and comments.
  If access or required labels are unavailable, report the blocker and retain
  the draft. Do not claim the issue was filed successfully.

## Filing Procedure

1. **Search before creating.** Search the target repository's open issues
   labeled `housekeeping` for the subsystem, paths, and bug. Read matching
   issue bodies and comments, including later result pages. A shared
   subsystem alone is not a match: the issue must cover the same concern.
   Exclude branch-followup containers from ordinary observation matches.
2. **Check for active work.** An open issue is not necessarily unstarted.
   Inspect available project status, labels, comments, and linked pull
   requests for evidence that implementation has begun. Closed issues and
   issues with active implementation are not append targets.
3. **Append on an eligible match.** Add a dated comment using the observation
   block below. Preserve the existing description and earlier observations.
4. **Create when no eligible match exists.** Create an open bug issue titled
   `housekeeping: <topic>`, apply `housekeeping`, and seed its body with the
   observation block and any required bug-template fields. If the only match
   is active or closed, reference it and explain the remaining or recurring
   bug in the new issue. Do not change the existing issue's status.
5. **Verify and report.** Read back the issue or comment. Confirm the target
   repository, content, label, and open state. Return its URL and issue
   number for the caller's report. If only part of the operation succeeded,
   return the existing URL and the missing step so retries do not duplicate it.

## Observation Block

Each block must contain enough evidence for someone to act without the
original session. Include reproduction steps and expected versus actual
behavior when applicable.

```markdown
**<path:line @ commit SHA>** — <observed bug>.
Evidence: <reproduction steps or other concrete evidence>.
Expected: <intended behavior>.
Actual: <observed behavior>.
Why it matters: <impact on users or future work>.
Suggested: <fix sketch>.
Found: <source issue or pull request URL, branch, or work context>. (<date>)
```

If no code location applies, replace the path with a concrete description
of the affected behavior. Distinguish observed facts from suspected causes.

## Branch-Followup Issues

Use a branch-followup issue to collect non-blocking review findings that
project policy permits deferring. This includes plan-review findings.
Ordinary out-of-scope observations use the filing procedure above instead.

**Keep one branch-followup issue per unit of work**, such as a pull request
or a cleanup batch. All review rounds for that work use the same issue.

1. **Find or create once.** Search issues labeled `housekeeping` and
   `branch-followup` across open and closed states for the source pull
   request, issues, or branch. Reuse the recorded URL on resumed work.
   If several matches exist, inspect their source references to identify
   the original container; report unresolved ambiguity rather than creating
   another. On no match, create an open bug issue titled
   `branch-followup: <source> — deferred non-blocking review feedback`,
   with both labels and source URLs in its body.
2. **Record the URL immediately.** Put it in the finding log and report.
   Designate one filer for creation; parallel reviewers return findings to
   that filer rather than independently creating containers.
3. **Append by URL at review-loop exit.** Apply the active-work and closed
   issue checks above. If the existing container is active or closed, report
   its URL and retain the new findings for coordination instead of creating
   a second container, reopening it, or silently expanding its scope.
4. **Use durable references.** Anchor code findings to a commit SHA,
   preferably the merged commit when available. For plan feedback, restate
   the concern instead of linking to a temporary plan file.

```markdown
**<path:line @ commit SHA | plan-feedback: concrete concern>** —
<finding ID> (<review category>, non-blocking): <observed problem>.
Why it matters: <impact on users or future work>.
Suggested: <fix sketch>.
Source: <pull request and issue URLs; branch or work context>. (<date>)
```

Verify each append and return the container URL. Process branch-followup
issues one per batch, separately from ordinary housekeeping issues.

## Closure Rule

Any work that fixes a housekeeping issue must add a resolution comment
linking the fix commit or merged pull request and describing verification.
Close the issue only when every observation in it is resolved. For a partial
fix, identify the resolved and remaining observations and leave it open.

Read back the issue to verify the resolution comment and final state. If
another action already closed it, verify the fix covers all observations
and add any missing resolution details. Report addressed issue URLs and
any closure failures in the final work summary.

## Batch Pass

List open issues labeled `housekeeping` in the target repository, including
all result pages. Exclude issues with active implementation. Select up to
eight ordinary issues or exactly one branch-followup issue per batch.

Use each issue's observations as the work scope and follow the repository's
implementation and review process. Apply the closure rule to each completed
issue. Report what was fixed, what remains open, and any blocked issues.
Reading or planning the backlog alone does not authorize edits or closure.
