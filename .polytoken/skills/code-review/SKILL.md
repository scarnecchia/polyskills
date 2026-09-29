---
name: code-review
description: Review a pull request (or the current branch) with TWO parallel reviewer subagents — a standard reviewer and an adversarial reviewer. Merge their findings only after both return; deliver an in-chat summary always and post to the PR only with consent. When reviewing your own branch, iterate on the feedback and re-invoke until no findings remain.
polytoken: 
  tags: [productivity]
---

# Code Review

Orchestrate a two-reviewer code review. The main agent does **not** review the diff itself — it dispatches two reviewer **subagents** that run concurrently on using `@mg:review`, waits for **both** to return, merges their findings, and delivers a single review. When the main agent owns the branch under review, it then fixes the findings and re-invokes this skill until the review comes back clean.

This is the reviewer counterpart to `create-pr` (opens the PR). Here, two of Polytoken's own subagents are the reviewers.

> **Subagents + model — non-negotiable.**
> - The review reasoning runs **inside subagents, never in the main agent.** Dispatch **exactly two** `general-purpose` subagents in a **single assistant turn** so they run in parallel.
> - Each subagent using a model from `@mg:review`: The skill's standing requirement *is* the explicit operator request that authorizes this `model_override`.
> - One is the **standard reviewer**, one is the **adversarial reviewer**.
> - The main agent only orchestrates: gather context → dispatch the two → wait for both → merge → deliver → (authoring mode) fix + re-invoke.

## Modes — decide this first

- **Authoring mode** — *you wrote the changes under review* (the branch you've been building, or a PR you authored). After the review you **iterate**: fix the findings and re-invoke until clean.
- **External mode** — *you're reviewing someone else's PR.* **Read-only**: deliver feedback, never edit their code, never iterate on their behalf.

If it's ambiguous who owns the changes, ask one clarifying question before reviewing.

## The Loop

```
identify target + mode (authoring | external)
        │
        ▼
gather diff + context  (main agent, any model)
        │
        ▼
dispatch TWO reviewer subagents in ONE turn — parallel:
   • standard reviewer            • adversarial reviewer
        │
        ▼
WAIT for BOTH to return   ◄── deliver / post / fix NOTHING until both terminal
        │
        ▼
merge + dedupe findings → one severity-ranked review
        │
        ▼
deliver: in-chat summary (always) + post only if open PR & consent
        │
   ┌────┴───────────────────────────────┐
external mode                       authoring mode
   │                                     │
  done                          findings? ──no──► clean — done
                                         │
                                        yes → fix root cause + tests
                                              │
                                              ▼
                                  RE-INVOKE this skill (fresh 2-reviewer pass)
                                  until no new findings  (cap 5 cycles)
```

## Steps

### 1. Identify the target and the mode

- **Target:** a PR number if the user gave one; otherwise the current branch vs. the repo's default base.
  ```bash
  BASE=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
  OWNER=$(gh repo view --json owner --jq .owner.login)
  REPO=$(gh repo view --json name --jq .name)
  ```
- **Mode:** *authoring* if you are the author of the changes (your working branch, or a PR whose author is you); *external* if you're reviewing changes you didn't write. Check the PR author if there's a PR:
  ```bash
  gh pr view <PR> --json author,headRefName,state,url --jq '{author:.author.login,state,url}'
  ```
  If ownership is unclear, ask one question. The mode decides whether step 6 runs.

### 2. Gather the diff and context (main agent)

```bash
git fetch origin "$BASE" --quiet
git diff "origin/$BASE...HEAD" --name-only      # changed files
git log  "origin/$BASE..HEAD" --oneline         # commits
git diff "origin/$BASE...HEAD"                    # full diff
gh pr view <PR> --json title,body,url,state,isDraft,baseRefName,headRefName   # if a PR exists
```

Assemble a **context bundle** to hand to both subagents: changed-files list, commit log, the full diff, the PR title/body (intent), and the touched subsystem/prefix (e.g. `discord_smite_ui/` → smite-ui). This is cheap orchestration work — fine on any model.

### 3. Dispatch the two reviewer subagents

In a **single assistant turn**, call the `subagent` tool **twice** (so both run concurrently), `subagent_type: general-purpose`, `model_override`. Hand each the full context bundle and tell it: read-only on source (it may read files / run `git diff` to dig deeper, but must not modify code or branch state); return findings as its result in the format below.

**Reviewer A — Standard.** A balanced, thorough review across, in priority order:
1. Correctness & logic (does it do what the PR claims?)
2. Edge cases & error handling
3. Security (injection, authz/authn, secrets, unvalidated trust-boundary input)
4. Concurrency (races, shared mutable state, cancellation)
5. Performance & resource use (N+1s, unbounded growth, hot-path cost)
6. API & compatibility (breaking signatures/schemas, migration safety)
7. Tests (is the new behavior covered? tests that would fail before the change?)
8. Readability & maintainability (nits, lowest priority)
Also call out **what's good**.

**Reviewer B — Adversarial.** Assume the change is subtly broken and *try to break it.* Hunt the worst-case: the exploitable security hole, the race, the malformed/hostile input that isn't handled, the invariant the author assumed but didn't enforce, the edge case the happy-path tests skip. Be skeptical of the tests themselves — do they actually pin the contract, or do they pass vacuously? Prefer one real, well-argued blocker over ten nits.

**Finding format (both reviewers):** a one-line verdict, then each finding as `severity · path:line — problem → why it matters → fix direction`. Severity scale: `Blocker · High · Medium · Low · Nit`. Use the diff's new-side line numbers. No hypotheticals stated as fact — unverifiable downstream effects are marked "unverified".

### 4. Wait for BOTH, then merge (main agent)

- Use `job_block` to wait until **both** subagents are terminal. **Deliver nothing, post nothing, fix nothing until both have returned** — no acting on whichever finished first.
- **Merge, don't concatenate:** dedupe overlapping findings (same `path:line` / same issue), keep the higher severity, and tag each finding's source — `standard`, `adversarial`, or `both`. Adversarial-only findings are usually the subtle ones; don't drop them.
- Build one unified review: verdict line, a severity-ranked table (`Severity | path:line | source | one-liner`), the per-finding detail, and a "what's good" note when warranted.

### 5. Deliver the merged review (after both returned)

- **Always** print the merged review in chat — this is the guaranteed deliverable.
- **Posting is gated:** only if an **open** PR exists for the branch **and** the user consents.
  ```bash
  gh pr view <PR-or-branch> --json number,state,url --jq '{number,state,url}'
  ```
  No open PR (or closed/merged) → summary only, don't ask. If open, ask whether to post (show PR #/URL); default to not posting. On consent, post **comment-only** (never `--approve`/`--request-changes` unless asked), prefixing every comment with `Polytoken:3 `:
  ```bash
  gh api "repos/$OWNER/$REPO/pulls/<PR>/comments" -X POST \
    -f body="Polytoken:3 <severity> — <problem + fix direction>" \
    -f commit_id="$(gh pr view <PR> --json headRefOid --jq .headRefOid)" \
    -f path="<file>" -F line=<new-side line> -f side="RIGHT"
  gh pr review <PR> --comment --body "Polytoken:3 <verdict + severity table>"
  ```

### 6. Authoring mode — iterate, then re-invoke (skip in external mode)

- **External mode:** stop after step 5. Never edit someone else's code; never loop.
- **Authoring mode:** if the merged review has findings, fix them:
  1. Dispatch a `general-purpose` subagent using `@mg:workhorse` and fix the **root causes** — no workarounds, no disabling/skipping tests, no `--no-verify`. Then:
    1. Add or adjust a test that **would have failed before** the fix, pinning the contract.
    2. Run the relevant test suite + lint; fix any breakage before continuing.
  3. **Re-invoke this skill from step 2** — a fresh two-reviewer pass on the updated code.
- Repeat until a cycle returns **no new findings** — that clean pass is "done".
- **Guardrails**
  - Print `Code-review cycle N` at the top of each pass so progress is visible.
  - **Cap: 5 cycles.** If still not clean after 5, stop and hand back with the current findings.
  - **Same finding twice in a row = stop and ask** — the fix isn't fixing it; don't churn variations.

## Rules

- **Reviewing happens in subagents, never the main agent.** Exactly two, dispatched in one turn so they run in parallel: standard + adversarial.
- **Reviewers run on a `@mg:review` model**. If a subagent can't be routed to one of those models, stop and say so — don't review on the default model.
- **No feedback before both return.** Don't deliver, post, or start fixing until both subagents are terminal. No partial reviews.
- **Merge, don't staple.** Dedupe, keep the higher severity, keep adversarial-only findings, tag sources.
- **Mode gates iteration.** Authoring → fix + re-invoke until clean. External → read-only, deliver only, never touch their code.
- **Posting needs an open PR + explicit consent.** Comment-only, `Polytoken:3 ` prefix. No open PR → summary only.
- **Fix root causes; tests gate every cycle.** Cap 5 cycles; same finding twice → stop and ask.
- **Ground every finding in code** (`path:line`); mark unverifiable downstream effects "unverified". Severity is your honest read — don't inflate nits or hedge a real blocker.

## Quick reference

| Phase | Who / model | Output |
|-------|-------------|--------|
| Identify + gather (1–2) | main agent / any model | context bundle + mode |
| Review (3) | **2 subagents | two finding sets, in parallel |
| Wait + merge (4) | main agent | one severity-ranked review |
| Deliver (5) | main agent | chat summary always; post if open PR + consent |
| Iterate (6, authoring only) | main agent | fixes + re-invoke until clean (cap 5) |

## Notes for the operator

- **Two reviewers, run together:** the adversarial pass catches what the balanced pass rationalizes away. Running them concurrently (not one after the other) keeps it fast and keeps the merge honest.
- **Wait-for-both** exists so you never act on half a review — a blocker from the slower reviewer shouldn't be missed because the other finished first.
- **The authoring loop re-invokes the whole skill**, so each cycle is a fresh, unbiased two-reviewer pass on the latest code. "No new findings" is then a real signal, not an agent rubber-stamping its own fix.
- **External mode is deliberately read-only** — reviewing someone else's PR never edits their branch.
