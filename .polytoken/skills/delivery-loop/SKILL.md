---
name: delivery-loop
description: Drive any branch → push → PR → review → merge-ready loop to mechanical completion — declare a completion marker the delivery-completion-proof stop hook verifies, keep commits clean, push and verify the remote head by SHA, run a review loop bounded at 3 rounds, and prove completion (unpushed == 0, PR head SHA == local HEAD, marker cleared) before handing back. Use whenever the session will push a branch or open a pull request.
polytoken:
  tags: [git, review, delivery]
---

# delivery-loop — finish delivery, don't hand back early

## 1. When to use

Any work that ends in a pushed branch or pull request: feature branches, review fixes, release cuts, chore bumps. If the session will push or open a PR, start this skill before the first delivery commit.

## 2. Baseline

- `git status --short --branch` — current branch, dirty files, ahead/behind.
- Detect the base branch from the remote, never from assumption (`gh repo view --json defaultBranchRef --jq .defaultBranchRef.name` on GitHub; `atgc repo view` on Tangled).
- Triage the dirty tree: commit what belongs to this delivery, stash or ask about what does not. Never mix unrelated changes into the delivery commits.

## 3. Declare the completion marker

Before starting delivery work, declare the marker via `shell_exec`. The shell environment may not carry the harness variables, so use the guarded idiom below: `${XDG_STATE_HOME:-$HOME/.local/state}` falls back exactly like the hook does, and the `${POLYTOKEN_SESSION_ID:?…}` guard fails loudly instead of writing a misnamed file — when it fails, re-run the command prefixed with `POLYTOKEN_SESSION_ID=<session id>` using the session id from harness context. Never leave a placeholder value in a written file.

```bash
sid_raw="${POLYTOKEN_SESSION_ID:?POLYTOKEN_SESSION_ID is not set in this shell — re-run this command prefixed with POLYTOKEN_SESSION_ID=<session id from harness context>}"; sid="$(printf '%s' "$sid_raw" | tr -c 'A-Za-z0-9._-' '_')"; state="${XDG_STATE_HOME:-$HOME/.local/state}"; mkdir -p "$state/polytoken/hooks/completion-proof" && chmod 700 "$state/polytoken/hooks/completion-proof" && printf '{"expect_push": true, "expect_pr": "", "budget": 3, "nudges": 0, "paused": false}' > "$state/polytoken/hooks/completion-proof/$sid.json" && chmod 600 "$state/polytoken/hooks/completion-proof/$sid.json"
```

Set `"expect_pr"` to the PR URL once it exists — it is informational for the operator.

Pause protocol: before any intentional handback to the operator (question, ambiguity, destructive-operation approval), either set `"paused": true` in the marker or delete it entirely. The hook honors `paused` with an immediate stop and consumes no budget. Re-declare (with `"paused": false`) on resume.

After any mid-delivery push, re-declare the marker if delivery work remains — the hook deletes the marker as soon as unpushed reaches 0, so the next stop would otherwise pass silently.

## 4. Branch and commit discipline

- One logical change per commit; follow the repo's commit-message conventions.
- Never force-push a shared branch without explicit operator approval.
- Wrong branch → move the work to the right one (switch + cherry-pick/rebase); destructive resets need operator confirmation (§8).

## 5. Push + PR

Open the PR via @skill:create-pr (`gh` on GitHub, `atgc` on Tangled; drafts on GitHub). The push is only real when verified by SHA: local `git rev-parse HEAD` must equal the remote/PR head — `gh pr view <PR> --json headRefOid` on GitHub, `atgc pr view` on Tangled. Never report a push as done without that SHA check.

## 6. Review loop (bounded at 3 rounds)

Run reviews via @skill:code-review for a diff-range review using `@mg:review` (model override as needed). Each round:

1. Collect findings.
2. Using the `housekeeping` skill, any low or nit findings should be filed as bugs
3. Fix or explicitly rebut every finding of medium or higher — rebuttals cite evidence, not hope.
4. Re-run the review on the updated code.
5. Maintain a resolved/unresolved findings ledger.

The loop is bounded at **3 rounds**. After round 3, stop churning and list remaining unresolved findings for the operator.

## 7. Documentation loop

Give each subagent the delivery diff and applicable project instructions.
Instruct each subagent to load `ste-writing` before writing.

1. **Code comments.** Dispatch a `general-purpose-mini` subagent.
   Instruct it to load `writing-code-comments` and revise comments added or
   changed in the diff.
2. **Project context.** Dispatch a `project-context-librarian` subagent.
   Have it update or create project context files affected by the changes.
3. **README.** Follow @skill:writing-good-readmes to dispatch a
   `general-purpose` subagent with
   `model_override: "@mg:review"`.
   Instruct it to load `writing-for-a-technical-audience` and `ste-writing`
   before writing. Have it create or update `README.md` using the skill's
   required structure: title, short description, beginner setup, and
   developer setup. Leave an accurate README unchanged.

Review each result against the diff and project files. Return corrections
to the responsible subagent until the documentation is accurate and complete.
Use the required README writer model and skills for every README revision.

## 8. Completion-proof checklist

All must hold before reporting done:

- No unpushed commits: `git rev-list --count @{upstream}..HEAD` returns 0 (unpushed == 0).
- PR head SHA == local HEAD (`gh pr view --json headRefOid` vs `git rev-parse HEAD`), or the push verified on the no-PR path.
- Unresolved review findings explicitly listed for the operator.
- Marker cleared:

```bash
sid_raw="${POLYTOKEN_SESSION_ID:?re-run prefixed with POLYTOKEN_SESSION_ID=<session id from harness context>}"; sid="$(printf '%s' "$sid_raw" | tr -c 'A-Za-z0-9._-' '_')"; state="${XDG_STATE_HOME:-$HOME/.local/state}"; rm -f "$state/polytoken/hooks/completion-proof/$sid.json"
```

## 9. Recovery

- Wrong branch: switch to the right branch, then cherry-pick or rebase the work over.
- Rewriting pushed history (reset/rebase on the remote branch) is destructive and requires explicit operator confirmation.
- If the stop hook says "Completion proof pending … unpushed commit(s)", the marker says delivery is in progress but the push is missing: push and verify the remote head, or clear the marker if delivery is genuinely not in progress.

## 10. Cross-references

- @skill:create-pr — open the draft PR and verify it on the forge.
- @skill:code-review — two-reviewer loop for your own branch.
- @skill:using-git-worktrees — isolated workspace before starting.
