---
description: Find and plan a small, self-contained Jira task you can take on with minimal back-and-forth. Use when the operator asks you to find something to work on, pull a ticket, or stay ahead on small nits.
polytoken:
  tags: [jira-solo-tasker, workflow]
---

You operate in the plan facet. Your job is to pick one small, eligible Jira task,
claim it, research it, resolve open questions with the operator, and produce a
handoff plan that names the execute skill `jira-solo-tasker-execute`. Do not
implement anything.

## Constants

All values in this block are site-specific placeholders — replace them with your own project values before first use.

- Atlassian cloudId: `<ATLASSIAN_CLOUD_ID>`
- Jira project: `<PROJECT_KEY>`
- Transitions: To Do `<TO_DO_ID>`, In Progress `<IN_PROGRESS_ID>`, In Review `<IN_REVIEW_ID>`, Done `<DONE_ID>`. These IDs are board-specific, verified 2026-06-18; re-verify via `execute` with `getTransitionsForJiraIssue` if the project board is reconfigured.
- Eligible issue types: Task (`<TASK_TYPE_ID>`), Bug (`<BUG_TYPE_ID>`). Never pick Epic, Feature, or Subtask.

## 1. Scan for candidates

Run one search (no clever predicates):

`searchJiraIssuesUsingJql` with jql
`project = <PROJECT_KEY> AND status = "To Do" ORDER BY priority ASC, created ASC`
and fields `["summary","description","issuetype","priority","labels","status","parent","issuelinks","comment"]`.

Then filter the results in context. A candidate is eligible only if ALL hold:

- issuetype is Task or Bug.
- No `no-auto` label.
- Not epic-backed: `parent` is absent (standalone). Skip anything whose parent is an Epic.
- Not blocked by unresolved work: no `issuelinks` entry with `type.name == "Blocks"` that has an `inwardIssue` (this issue "is blocked by" it) whose status is not Done.
- Moderate-to-small scope, and the summary/description (plus what you can infer from the codebase) is enough to start. If nothing qualifies, say so and stop.

Prefer higher priority and older issues (the ORDER BY already ranks them).

## 2. Claim the chosen issue (before any research)

Pick the best candidate. Read it in full (`getJiraIssue`, fields `["*all"]`) —
this is your baseline research read. Note the `updated`
timestamp and the comment set you observe at this point.

### Double-grab on work-item state

The issue's status is the lock. There is a TOCTOU window between the first full
read and the claim transition: between those two calls another solo-tasker run
could have moved the same issue to In Progress (or left a "Claimed by solo-tasker"
comment). Close that window with a fresh re-read immediately before the
transition — a double-grab on the work-item state.

Immediately before claiming, re-read the issue with `getJiraIssue` (fields
`["status","comment"]`) and compare against your first
read. Back off and pick the next candidate if EITHER is now true:

- The status is no longer "To Do" (e.g. another agent already moved it to In
  Progress).
- A new "Claimed by solo-tasker" comment has appeared since your first read,
  from a session other than this one.

If both checks still pass, claim it immediately: `transitionJiraIssue` with
`transitionId: "<IN_PROGRESS_ID>"`, then add a comment via `execute`:

```
execute:
  name: "addOrEditJiraIssueComment"
  cloudId: "<ATLASSIAN_CLOUD_ID>"
  inputs:
    issueIdOrKey: "<ISSUE-KEY>"
    commentBody: "Claimed by solo-tasker plan run <session-id> at <ISO time>."
```

Use whatever session identifier and the current timestamp you have available.

The claim happens now, not at execute. This is how parallel runs avoid duplicate work. Note: the claim is a side effect, and the plan facet is read-only by default, so the transition and comment will prompt for approval unless `transitionJiraIssue` and the `execute` tool (for `addOrEditJiraIssueComment`) are pre-allowed for this facet in `.polytoken/permissions.yaml`; those pre-allows are a required precondition for unattended runs (see Risks).

## 3. Research and clarify

Investigate the codebase to ground the work (read the relevant modules, confirm
the touch points, identify contracts and tests). Use `ask_user_question` for any
ambiguity that materially changes the implementation — scope, intended behavior,
where something should live. Do not guess on product intent.

### Branching: main only

All work lands on `main` only — this project uses a single long-lived branch with
rolling releases (see root `AGENTS.md` "Branch Model"). There is **no**
patch/minor branching classification and **no** `stable` branch, so the plan
does NOT carry a classification field and the merge gate does NOT branch on it.
Do not emit any `## Classification:` heading in the plan.

## 4. Write the handoff plan

Call `write_plan` with a plan that:

- **The plan must open with a worktree preamble** before the Goal section, stating in bold: the execute facet MUST create a worktree with `direnv exec . just worktree-create <branch>` and `pushd .worktrees/<branch>` before doing any work. No implementation, no file edits, no commits outside the worktree. The preamble must also name `jira-solo-tasker-execute` as the required execute skill and state the plan is produced by the solo-tasker workflow. (This reinforces the naming requirement in the next bullet — both are kept; the preamble places the requirement at the top of the written plan where it survives compaction, while the next bullet remains the general requirement in the skill's instruction list.)
- **The plan must close with a worktree reminder** after the Risks section, restating in bold: the execute facet MUST operate inside the worktree created by `direnv exec . just worktree-create <branch>` and `pushd .worktrees/<branch>` for all implementation, testing, and review work. The reminder must reiterate that `jira-solo-tasker-execute` is the execute skill and that `popd` to the project root happens only at the merge gate. This is the second mandatory statement of the worktree requirement — it appears at the bottom so it survives compaction.
- Names `jira-solo-tasker-execute` as the skill the execute facet must invoke, and says the plan is produced by this workflow.
- References the ticket by key (e.g. `ABC-23`) throughout. The plan must name the ticket key explicitly in the title and in the Jira lifecycle instructions so execute cannot lose track of it.
- States the ticket is already In Progress (claimed) and that execute must verify, not re-claim.
- Specifies the worktree branch name as a concrete literal of the form `<project-prefix>-<number>_<short-description>` (for example `abc-23_fix-permissions-yaml`): the number is the ticket number, and the description is a lowercase kebab-case phrase of no more than three words drawn from the ticket summary. It directs execute to create it with `just worktree-create <branch>`, then `pushd .worktrees/<branch>` once to jail all implementation, build/test, and file work in the worktree. `pushd` is session state, so it persists across every subsequent tool call (shell, file, glob, grep, and spawned subagents) — unlike per-process `cd`, which dies with each bash call. The plan must also instruct execute to `popd` back to the project root before the merge gate, because the merge runs against `main` in the main tree.
- Includes todos for the surrounding work, not just the implementation: set up the worktree; confirm the ticket is In Progress; implement; write tests and commit through `direnv exec .` inside the worktree (the pre-commit hook runs the full suite); **run the test sufficiency gate**; run the implementation review loop; commit review fixes; move to In Review; on acceptance squash-merge to `main` under the lock; **move to Done**; remove the worktree; and report the outcome to the operator including a full test inventory.
- **Encodes the test sufficiency gate (mandatory, before implementation review):** the plan must instruct execute to spawn one `general-purpose` subagent with `model_override` `@mg:review` that audits every acceptance criterion for test coverage. The subagent receives the acceptance criteria, the Coverage Matrix, the list of written test files, and the commit hook result. It returns a per-criterion covered/not-covered verdict. The gate loops: execute must write any missing tests, commit them (the hook re-validates), and re-spawn the subagent until every acceptance criterion is confirmed covered. Execute must not proceed to the implementation review loop until this gate is clean.
- **Encodes the implementation review loop:** spawn three focused `general-purpose` reviewers with `model_override` `@mg:arch` (architecture & approach — replace-vs-edit, over/under-engineering, scope creep), `@mg:workhorse` (correctness & contracts — edge cases, error handling, type safety), and `@mg:workhorse` (test quality — false-green detection, tautological assertions, tests that don't exercise the new behavior); fix or rebut every finding; re-run all three while any critical or high remains. Each reviewer gets a focused mandate — do not ask one reviewer to cover another's lens. The test sufficiency gate owns test coverage existence and AC mapping; the implementation reviewers own code quality, production-code correctness, and test correctness respectively. **Reviewer-suggested tests that align with acceptance criteria are mandatory** — execute must add them, not skip them by claiming low severity.
- **Encodes the Jira lifecycle as mandatory checkpoints.** The plan must explicitly state all four transitions and their triggers: In Progress (already done by plan skill), In Review (after commit, transition `31`), and Done (after merge, transition `41`). The plan must call out that the Done transition is the most commonly missed step and is mandatory before reporting completion. The plan must also state that if the operator cancels mid-execute, execute should surface the current ticket state rather than abandoning it.
- Encodes the merge gate (main only): after the test sufficiency gate and implementation review loop pass, commit, `transitionJiraIssue` `31` (In Review), and prompt the operator to review. Only on explicit operator acceptance: acquire `.merge-lock` atomically (see AGENTS.md "Merge Lock"). Then fetch and fast-forward `main` in the project root, rebase `.worktrees/<branch>` onto `main`, squash-merge the branch into `main` and commit through `direnv exec .`. Release the lock (owner-checked), **`transitionJiraIssue` `41` (Done)**, then run `direnv exec . just worktree-remove <branch>` to clean up the worktree now that the merge is in and the lock is released. There is no `stable` branch and no cherry-pick; work lands on `main` once.
- **Encodes the final report with a mandatory test inventory.** After the worktree is removed, run `direnv exec . just run-cli --help` to prime the CLI cache, then report to the operator: restate the ticket (key and summary), confirm the ticket is in Done, summarize what was changed, and provide a **Test Inventory** section listing every new test by tier (unit, integration, TUI, live) with test file paths and function names, mapping each test to the acceptance criterion it covers. **If the test inventory does not include at least one test for every acceptance criterion, execute must abort the report and go back to implement the missing tests.** The operator should never have to ask whether tests were written. Give concrete advice on how to test it. If it's something related to tools within a conversation, propose a prompt for the operator to administer that will effectively exercise the new work and explain (placing verification conditions outside the prompt, unless the agent running it can verify itself during its runtime).

Follow the standard plan-facet plan shape (Goal, Implementation Summary, Implementation Plan, Acceptance Criteria, Test Strategy, Review Strategy, Documentation Strategy, Risks).

### Test Strategy In The Plan

The plan's Test Strategy section must contain a **Coverage Matrix**. A plan that
only says "add unit tests" or "run tests" is incomplete. For every behavior in
scope, add a row with:

| Behavior | Unit test? | Provider-double / daemon test? | TUI render/scenario test? | Test files or harness | Validation (pre-commit hook) | If N/A, why? |
|---|---|---|---|---|---|---|

Rules for the Coverage Matrix:

- Every changed behavior needs an explicit yes/no decision for each applicable
  tier. "N/A" is allowed only with a concrete technical reason tied to the
  behavior. "Too hard," "not worth it," "covered indirectly," or "integration
  test exists" are not valid reasons.
- Unit tests are not optional for pure logic. If the behavior includes pure
  functions, data transforms, parsers, config loading, state transitions, path
  selection, validation, or formatting, plan crate-local unit coverage in
  `#[cfg(test)]` modules or nearby `tests/` modules.
- Integration or live-provider coverage is not a substitute for unit coverage
  when pure behavior is present.
- **"Verified by code inspection" is not a valid test strategy.** Every
  acceptance criterion must have at least one executable test that would fail if
  the criterion's behavior regressed. If a criterion is structural or
  architectural, write a test that exercises the invariant (e.g., a decoy-config
  test that proves isolation). Do not mark criteria as "implicitly verified" or
  "code inspection only" — this is how acceptance criteria end up with zero
  tests.
- The matrix must name concrete likely test files, helper modules, or harnesses.
  If the exact file is unknown, name the crate/local area to inspect first.
- The matrix must name the validation path for each tier. The pre-commit hook
  runs the full suite (`just test` on non-main branches, `just test-all` on
  `main`) on every commit — the matrix does not need to repeat those commands.
  Instead, name any feature-specific build-system targets or special harness
  invocations the plan requires beyond what the hook already covers.

Polytoken has several layers of test infrastructure. Identify which applies to
each behavior:

**Tier 1: Pure unit tests** for pure functions, data transforms, parsers,
config loading, state transitions, path selection, validation, and formatting.
No I/O, no provider, no daemon. Prefer crate-local `#[cfg(test)]` modules or
nearby `tests/` modules. These run as part of the full suite on commit via the
pre-commit hook; name any feature-specific build-system target required by the affected
crate.

**Tier 2: provider-double-backed daemon/playback tests** for any behavior that flows
through the agent loop or depends on provider-visible state. Use the project's scriptable provider double — a rule-driven fake with
no network I/O. Ordered rules match on prompt and tool-call shape (exact or
substring text, regex, or presence of prior history in the next prompt) and
return scripted responses (text chunks, tool calls, errors, stalls, usage
accounting), exposing the last system prompt and tool choice for assertions. When behavior depends on prior turns, tool
results, notifications, reminders, compaction fenceposts, or other replayed
history being visible in the next turn, use history-contains matching.

**Tier 3: Full daemon integration tests** with
the project integration harness with the provider double
for behavior that depends on the full daemon stack: routes, SSE, persistence,
hooks, process boundaries, session files, or restart/reload behavior. Env-var
knobs control tool registration, iteration caps, idle-stall timeouts, and other
test fixtures. These run as part of the full suite on commit via the pre-commit
hook.

**Tier 4: TUI render and scenario tests** for observable TUI behavior. Use
buffer/TestBackend-style assertions for exact text, style, layout, wrapping,
scrollbars, hit testing, modal/focus behavior, prompt/history navigation, mouse
interaction, terminal events, and rendered runtime hydration. The TUI scenario
harness is feature-gated; when a change needs it, the plan must call out the
feature-specific build-system target named in `rs/<app-crate>/src/tui/AGENTS.md`.

Any test that exercises behavior flowing through the provider MUST use
A provider double rather than mocking at a lower layer. This includes model text,
tool calls, tool results, provider errors at stream start or mid-stream, retries,
streaming, multi-turn history, system prompt composition, forced tool choice,
permission/classifier turns, idle-stall recovery, and compaction fences. Do not
write a unit test for daemon/provider behavior by calling internal functions
directly when a provider double can drive the behavior through the real agent loop.

The test strategy must cover happy path, error path, and edge cases for each
behavior. For provider-dependent behavior, explicitly consider provider errors
at stream start, provider errors mid-stream, tool execution errors, multi-turn
replay, retry, and idle-stall behavior. For TUI-visible behavior, explicitly
consider narrow widths, wrapping/truncation, selection/focus, scrolling,
mouse/keyboard interaction, and absence/empty-state rendering where relevant.

Before finalizing, inspect the relevant crate's test patterns: grep for
provider-double and test_provider names, check `tests/` directories and helper modules,
look for `<PROJECT>_TEST_*` env vars, read the crate `AGENTS.md`, and for TUI
work read `rs/<app-crate>/src/tui/AGENTS.md`. The plan should cite the
important anchors it found so execute does not rediscover them from scratch.

## 5. Heavy plan approval loop

Before `handoff_plan`, run THREE `plan-reviewer` subagents in parallel. Each
reviewer gets a distinct lens through the prompt:

| Reviewer | model_override | Lens |
|---|---|---|
| Architecture & approach | `@mg:arch` | Plan shape, codebase grounding, replace-vs-edit assessment, abstraction level, complexity appropriateness |
| Coverage & completeness | `@mg:review` | Test-to-AC coverage, tier appropriateness, missing behaviors, plan completeness |
| Adversarial & integration | `@mg:workhorse` | Contract risks, ambiguity, integration risk, scope creep |

All three reviewers must audit the Coverage Matrix explicitly: does every
behavior have the right unit, provider-double/daemon, and UI tier decisions; are
any tiers incorrectly marked N/A; are any acceptance criteria marked "code
inspection" or "implicit" without an executable test; are exact test harnesses
and commands named; and are skip/gating risks surfaced rather than hidden. Each
reviewer should prioritize its lens but all check the Coverage Matrix.

Fix or explicitly rebut **every** finding in the plan with `edit_plan` — at
every severity, not just critical/high. There is no "follow-up" tier: any
finding you do not resolve will never be captured. Re-run all reviewers while
any reviewer returns any critical or high finding; medium and low findings
must also be fixed or rebutted before handoff. Only call `handoff_plan` when
all reviewers are clean and every finding has a disposition. If a pinned
`model_override` does not resolve at runtime, stop and ask the operator; do
not silently substitute a weaker model and weaken the approval gate.

## 6. If the operator cancels

If the operator cancels (rejects the handoff, or you judge the issue unviable),
release the claim: `transitionJiraIssue` with `transitionId: "11"` (To Do).
Leave a brief comment if useful. Do not leave issues stranded In Progress.
