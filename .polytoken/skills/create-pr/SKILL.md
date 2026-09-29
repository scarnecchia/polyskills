---
description: Create a consistently structured draft pull request for the current repository with gh on GitHub or atgc on Tangled, verifying the created PR before reporting success.
polytoken:
  tags: [git, github, tangled, release]
---

# Create a draft PR

Use this skill when the requesting agent wants the current repository changes opened as a **draft** GitHub or Tangled pull request. Use the `gh` command-line tool for GitHub operations and use the `atgc` command-line tool for Tangled operations; do not substitute a browser workflow or claim success without verifying the created PR. Drafts are a GitHub concept: Tangled has no draft flag, so report a Tangled pull request as ready for review rather than claiming it is a draft.

## Preconditions and repository inspection

1. Confirm the working directory is the intended project repository. Inspect `git status --short --branch`, the current branch, the remote, the commit range, and the diff. Also inspect relevant test/build results and project guidance so the PR description is factual.
2. Refuse to create a PR from a detached HEAD, an empty change set, or a branch that is the repository's default branch. Do not include secrets, credentials, generated local state, or unrelated changes; stop and ask for clarification when the change set is mixed or unsafe.
3. Determine the forge from the repository, not from assumption. A remote on GitHub means the `gh` path. A Tangled-hosted checkout is confirmed with `atgc repo view` (it reports the repo's identity, hosting, and live git state); if it shows the checkout is not configured for the current account, run `atgc repo configure` first — it writes the Tangled git identity and installs the Change-Id hook. If the repository could be either forge, or neither tool can see it, stop and ask.
4. Check for an existing PR for the current head branch before creating another one: `gh pr list --head <branch> --state all` on GitHub; `atgc pr view`, which defaults to the current branch's pull, or `atgc pr list`, on Tangled. If one exists, report it rather than creating a duplicate; on Tangled, updating it means `pr resubmit` (a new round) plus `pr edit` (title and body), never a second `pr create`.
5. Confirm access and repository identity on the chosen forge: `gh repo view` on GitHub, `atgc repo view` on Tangled. If authentication, repository permissions, or the remote configuration prevents the operation, report the exact blocker and do not pretend that a PR was created.

## Prepare the branch

Determine the base branch from the repository rather than assuming `main`.

### GitHub

- Get the base with `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`.
- Ensure all intended commits are present on the current branch and push it to its configured remote with `git push -u origin HEAD` when needed. Never force-push as part of this skill. If pushing would overwrite someone else's work or the remote is not `origin`, stop and ask before proceeding.
- Recheck the final remote commit and diff after pushing. The PR head must be the current branch, not a temporary or unrelated local ref.

### Tangled

- Do not push by hand: `atgc pr create` pushes the branch for you, and every later push (`pr resubmit`) carries a lease on the head the pull last recorded, so a rewritten branch lands while one somebody else moved refuses. A refusal is information about someone else's work — never answer it with a manual push, and never `--force` past it blind.
- Pass the base explicitly with `--target <base>`; it otherwise defaults to the repository's default branch.
- If you have no push access on the target repository, use `atgc pr create --patch-only`, which opens the pull from the patch alone and records no source branch.

## Stable PR structure

Write the body using this exact section order on every PR:

```markdown
## Summary
- <What changed and why, in one to three bullets.>

## Changes
- <Important implementation or behavior changes.>
- <Include notable API, migration, configuration, or compatibility details.>

## Validation
- <Commands/tests actually run and their results.>
- <If not run, write: `Not run — <specific reason>`.>

## Review notes
- <Known limitations, follow-ups, risks, or reviewer focus areas.>
- <If none, write: `None known.`>
```

Keep the title concise, imperative or outcome-oriented, and specific to the change. Derive every bullet from inspected repository state. Never invent test results, reviewer approvals, issue links, or behavior that was not verified. Keep unrelated discussion out of the body. Supply title and body explicitly on both forges rather than letting `atgc` default the title to the first commit's subject; a temporary `--body-file` is preferred for Markdown fidelity, and on Tangled `atgc` uploads and embeds local image paths found in the body (1 MB max).

## Create and verify the PR

### GitHub

1. Create the PR with `gh pr create` and the `--draft` flag, supplying the explicit base, current head, title, and body (a temporary `--body-file` is preferred for Markdown fidelity). Do not use a command that omits `--draft`.
2. Capture the URL printed by `gh`.
3. Verify it with `gh pr view <url-or-number> --json isDraft,url,title,baseRefName,headRefName,state`. Confirm that `isDraft` is `true`, the base/head are correct, and the PR is open. If verification fails, report the failure and its output.
4. Return the PR URL plus the final title, base/head, draft status, and a short summary of the validation recorded in the body.

### Tangled

1. Create the PR with `atgc pr create --title '<title>' --body-file <file> --target <base>`. atgc pushes the branch itself — never `git push` by hand first. Use `--patch-only` only when you have no push access on the target.
2. Capture the pull number and URL printed by `atgc`.
3. Verify it with `atgc pr view <number>`: confirm the title, body, target branch, and that the pull is open. If verification fails, report the failure and its output.
4. Return the PR URL plus the final title, base/head, and a short summary of the validation recorded in the body, stating plainly that Tangled pulls have no draft state.

A successful result means the PR was actually created and verified on its forge. A push or create error is not success; preserve the error details and leave the repository in its existing non-destructive state.
