---
description: Execute a Jira solo-tasker handoff plan end to end. Worktree, implement, test sufficiency gate, heavy review loop, commit, move to In Review, and on operator acceptance squash-merge to main under the merge lock. Use when you are handed a plan that names this skill.
polytoken:
  tags: [jira-solo-tasker, workflow]
---

You operate in the execute facet on a plan produced by `jira-solo-tasker-plan`.
Reinforce the procedural steps here even if the plan already states them.

## ⚠️ Worktree requirement (non-negotiable)

You MUST create a worktree before doing any work. Do not implement, edit
files, run builds, or commit in the main working tree. The worktree is created
with `direnv exec . just worktree-create <branch>` (where `<branch>` is the
branch name from the plan), then you enter it with `pushd .worktrees/<branch>`.
All implementation, testing, file edits, and review subagent runs happen inside
that worktree. You return to the project root with `popd` only at the merge gate
(step 10), because the merge runs against `main` in the main tree. If you find
yourself editing files or running commands without having created the worktree
first, stop and create it.

All work lands on `main` only — this project uses a single long-lived branch with
rolling releases (see root `AGENTS.md` "Branch Model"). There is no
patch/minor branching classification and no `stable` branch. Do not expect a
classification field in the plan; carry `main`-only through the merge gate.

## Constants

All values in this block are site-specific placeholders — replace them with your own project values before first use.

- Atlassian cloudId: `<ATLASSIAN_CLOUD_ID>`
- Jira project: `<PROJECT_KEY>`
- Transitions: To Do `<TO_DO_ID>`, In Progress `<IN_PROGRESS_ID>`, In Review `<IN_REVIEW_ID>`, Done `<DONE_ID>`. These IDs are board-specific, verified 2026-06-18; re-verify with `getTransitionsForJiraIssue` if the project board is reconfigured.

## Jira ticket discipline

The ticket is your anchor throughout the entire run. Observed failures across
multiple sessions — tickets left stranded In Review, Done transitions never
fired, agents losing track of the ticket key after compaction — require these
hard rules:

- **Carry the key everywhere.** Reference the ticket key (e.g. `ABC-175`) in
  every Jira API call, every operator-facing status message, and in your todo
  titles. If compaction or a context boundary makes you lose the key, recover it
  from the plan or the session state before doing anything else.
- **Advance the lifecycle at every checkpoint.** The lifecycle is:
  To Do → In Progress → In Review → Done. Each transition is a mandatory
  checkpoint. Do not skip any of them. The most common failure is reaching
  In Review and then never advancing to Done after the merge.
- **Done is not optional.** The run is incomplete until the ticket is in Done.
  After a successful merge, the Done transition (`<DONE_ID>`) is the final required
  Jira action — it must happen before you report completion. If you merged and
  forgot to transition to Done, do it immediately.
- **Never abandon a ticket mid-lifecycle.** If the session is interrupted,
  cancelled, or the operator rejects the work, surface the current ticket state
  to the operator so it can be reconciled. Do not silently leave a ticket In
  Review or In Progress.

## Procedural checklist

1. **Confirm the claim.** The plan skill already moved the ticket to In Progress.
   Verify with `getJiraIssue`. If it is somehow not In Progress, do not re-claim
   blindly — surface it to the operator.
2. **Worktree.** Create the worktree with the exact branch name the handoff plan
   specifies (it is of the form `<project-prefix>-<number>_<short-description>`, e.g.
   `abc-23_fix-permissions-yaml`): `direnv exec . just worktree-create <branch>`
   (it lands at `.worktrees/<branch>`). Then `pushd .worktrees/<branch>` once.
   `pushd` is session state: it persists across every subsequent tool call, so
   shell, file, glob, and grep all resolve inside the worktree with no
   per-command `cd` prefix — run e.g. `direnv exec . just fix` directly
   (`direnv exec .` loads the worktree's `.envrc`, the same file as the project
   root since it is checked into git, so credentials and the mise toolchain are
   present). Subagents spawned while pushed inherit the worktree as their floor
   automatically and have their own independent `pushd`/`popd` stack. Stay
   pushed through implementation, build/test, and the review loop; `popd` back
   to the project root before the merge gate (step 10), which runs against `main`
   in the main tree. Relative paths resolve inside the worktree after `pushd`;
   absolute paths also work and are fine for describing the files you edit.
3. **Todos.** Make sure the todo list covers the work around the implementation,
   not only the code change: worktree setup, Jira state, implementation, write
   tests and commit, **test sufficiency gate** (step 6), implementation review loop,
   commit, In Review, merge gate, and Done transition. The Jira lifecycle
   transitions (In Progress verification, In Review, Done) should each be
   trackable todos so they are not forgotten after compaction.
4. **Implement** the plan.
5. **Write tests and commit.** Write tests per the plan's Coverage Matrix, then
   run `just fix` and commit to the task branch inside the worktree, through
   `direnv exec .`. The commit triggers the lefthook pre-commit hook, which runs
   the full project test suite (`just test` on non-main branches: unit +
   integration, no live providers) plus `just fix`, `just build`, and `just
   machete`. This is the test validation — do not manually run `just test-unit`,
   `just test-integration`, or `just test-all`; the hook is the test runner. If
   the hook fails, fix the issue and re-commit. For each behavior row in the
   Coverage Matrix, update your working notes with the actual test file(s) and
   function names you wrote. Follow these enforcement rules for which tests to
   WRITE:
   - Pure logic requires unit coverage in crate-local `#[cfg(test)]` or nearby
     `tests/` modules. Integration or live-provider tests are not a substitute.
   - Provider-dependent behavior must be covered with provider-double-backed daemon
     or integration tests, not lower-level mocks. Use `HistoryContains` when the
     behavior depends on prior turns, tool results, notifications, reminders,
     compaction fenceposts, or other replayed history.
   - Full daemon-stack behavior must use the integration harness, normally with the project integration harness (real daemon + provider double),
     , and must exercise the relevant
     route/SSE/persistence/hook/process behavior rather than only internal
     helpers.
   - Observable TUI changes require buffer/TestBackend or scenario-harness tests
     for visible text, style, layout, wrapping, scrollbars, hit testing,
     modal/focus behavior, prompt/history navigation, mouse interaction,
     terminal events, or rendered runtime hydration as applicable. If the
     feature-gated TUI scenario harness is required, run the build-system target named
     in `rs/<app-crate>/src/tui/AGENTS.md`.
   - Do not silently skip or downgrade an applicable tier. If a relevant tier
     cannot be run because of credentials, feature gating, missing fixtures,
     infrastructure failure, or time, stop and report the blocker to the
     operator unless the plan already marks that tier N/A with a concrete reason
     that still applies.
   - A skipped test is not a pass. Record the exact skip reason and whether it is
     an expected project gate (for example live-provider credentials) or a
     blocker that needs operator input.
   - **Pre-existing tests passing is not coverage for new behavior.** The
     pre-commit hook running green does not mean your new feature is tested —
     it means the pre-existing tests pass. You must have written new tests for
     each acceptance criterion before claiming coverage. Do not report "N
     integration tests pass" unless N includes the new tests you wrote for this
     work. This is the single most common test-reporting failure: the suite is
     green, the new feature is untested, and the agent reports success.
   The pre-commit hook validates the full suite on every commit. When the
   review loop (step 7) finds issues, fix them and commit again — the hook
   re-validates each time.
6. **Test sufficiency gate (mandatory, before implementation review).** Before
   spawning the implementation review subagents, run a dedicated test-sufficiency
   audit. This gate exists because agents repeatedly commit and advance to In
   Review with acceptance criteria that have no test coverage.

   Spawn a `general-purpose` subagent with `model_override` `@mg:review` and
   give it:
   - The full list of acceptance criteria from the plan (AC.1, AC.2, …).
   - The Coverage Matrix from the plan.
   - The list of test files you have written, their locations, and the test
     function names.
   - The test files you wrote and their function names, plus the pre-commit
     hook result from your commit (pass/fail, which tests failed if any).

   The subagent must determine, for **every** acceptance criterion, whether a
   test exists that exercises it. It must return a per-criterion verdict
   (covered / not covered) and, for any not-covered criterion, name the specific
   test that should be written and where it should live. It must explicitly check
   for the false-green trap: are the tests that pass actually new tests for this
   feature, or are they pre-existing tests that pass regardless of whether the
   feature exists?

   **This gate loops.** If the subagent identifies any uncovered acceptance
   criterion, you must write the missing tests, re-run them, and re-spawn the
   subagent with the updated test inventory. Repeat until the subagent confirms
   every acceptance criterion has adequate test coverage. Do not proceed to the
   implementation review loop (step 7) until the test-sufficiency subagent
   returns a clean bill of coverage for every acceptance criterion.

   If a pinned `model_override` does not resolve at runtime, stop and ask the
   operator; do not silently substitute a weaker model and weaken the test gate.

7. **Implementation review loop.** Spawn three focused `general-purpose`
   reviewers, each with a distinct lens. **Fix or explicitly rebut every
   finding at every severity — critical, high, medium, and low.** There is no
   "follow-up" tier: any finding you do not fix in this commit will never be
   captured or tracked, so it is effectively dropped. Do not report findings as
   "can be addressed later" or "non-blocking follow-ups." Either fix the code
   now, or rebut the finding with a specific technical justification in your
   commit message and report to the operator. Re-run all three reviewers while
   any critical or high finding remains unfixed; medium and low findings must
   also be fixed or rebutted before you report completion to the operator.
   Treat the codebase's own review guidance as authoritative where it exists.
   If a pinned `model_override` does not resolve at runtime, stop and ask the
   operator; do not silently substitute a weaker model and weaken the review
   gate.

   | Reviewer | model_override | Focus |
   |---|---|---|
   | Architecture & approach | `@mg:arch` | Is the right approach taken? Replace-vs-edit: should any changed code have been replaced wholesale? Overengineering, unnecessary complexity, scope creep, dead code, abstraction level appropriateness. |
   | Correctness & contracts | `@mg:workhorse` | Mechanical correctness: edge cases, error handling paths, type safety, off-by-one, missing implementations, contract conformance. Review the production code only. |
   | Test quality | `@mg:workhorse` | False-green detection: are assertions meaningful (not tautological)? Do tests exercise the new behavior, not just pass by coincidence? Do tests assert on real behavior rather than mock returns? Are there tests that would pass regardless of whether the feature exists? Review the test code only. |

   Each reviewer gets a focused mandate — do not ask one reviewer to cover
   another's lens. The test sufficiency gate (step 6) already owns test coverage
   existence and AC mapping; these reviewers own code quality, production-code
   correctness, and test correctness respectively.

   **Reviewer-suggested tests are mandatory, not optional.** If any reviewer —
   the test-sufficiency subagent or an implementation reviewer — suggests adding a
   test, and that test aligns with an acceptance criterion or covers behavior
   within the plan's scope, you **MUST** add it. You may not skip or rebut it by
   claiming it is low-severity or non-blocking. A reviewer flagging a missing
   test at any severity is a signal that coverage is incomplete. The only valid
   reason to skip a reviewer-suggested test is if it is explicitly out of scope
   per the plan's acceptance criteria — and even then, you should add it and note
   the scope question for the operator. When in doubt, add the test. The cost of
   an extra test is negligible compared to the cost of shipping an untested
   acceptance criterion.

8. **Commit review fixes.** If the test sufficiency gate or review loop required
   changes, commit those fixes. The initial commit already happened in step 5;
   this step covers any additional commits from the review loop. Every finding
   must be resolved — fixed or explicitly rebutted — before you reach step 9.

9. **Move to In Review and complete the goal.** `transitionJiraIssue` `<IN_REVIEW_ID>`.
   Prompt the operator to review the work. Reference the ticket by key. State
   explicitly in your message that the ticket is now In Review and that the
   next step (on operator acceptance) is merge to main followed by transition
   to Done.

   **If operating under a saved-session goal, call `complete_goal` HERE —
   not after the merge.** The goal covers implementation, testing, review, and
   reaching In Review. The merge to main (step 10) is operator-gated and
   outside the goal's scope. Do NOT merge autonomously because the goal is
   "active" — an active goal means "do the work," not "ship to main without
   a human looking at it." If `ask_user_question` is suppressed by the active
   goal, that means you should NOT be asking the operator — it does NOT mean
   you should auto-accept on their behalf and merge. The merge gate requires
   explicit operator acceptance, period.

10. **Merge gate (operator acceptance only).** On explicit operator acceptance,
    hold the lock for the whole finalization so no other agent touches `main`
    mid-sequence. **Acquire the lock BEFORE touching `main`.** If the main tree is
    dirty, that means another agent holds the lock and is mid-merge — wait for
    the lock and retry; do NOT bail, stash, reset, or "fix" the dirty tree. A dirty
    main tree is normal during a merge (see AGENTS.md "Merge Lock"); the lock is
    the gate, not the tree state. First `popd` to return to the project root:
    you `pushd`'d into the worktree in step 2 and the stack survives compaction,
    so you are still pushed unless a `/clear` reset it (in which case you are
    already at the project root and `popd` errors at the floor — skip it). With
    the main tree as your cwd, the main-tree steps below need no `cd`; target the
    worktree with `git -C`.
    - Acquire `.merge-lock` atomically per the AGENTS.md "Merge Lock" section
      (contents are your ticket key + timestamp).
    - Bring `main` up to date: `direnv exec . git fetch`, then `direnv exec . git
      checkout main && direnv exec . git merge --ff-only @{u}`. If `main` has no
      upstream configured, fast-forward to `origin/main` instead; if `--ff-only`
      fails, stop and surface it.
    - Rebase the worktree branch: `direnv exec . git -C .worktrees/<branch>
      rebase main`. Resolve any conflicts; the branch must be clean before merging.
    - With `main` checked out and clean in the project root, run `direnv exec .
      git merge --squash <branch>` then `direnv exec . git commit` so the
      `test-all` pre-commit gate has its credentials.
    - Release the lock (owner-checked against your ticket key), then
      `transitionJiraIssue` `<DONE_ID>` (Done). **Do not skip the Done transition.**
      This is the single most common Jira lifecycle failure — agents merge,
      release the lock, remove the worktree, and report completion without ever
      transitioning the ticket to Done. After releasing the lock, before any
      other cleanup, call `transitionJiraIssue` with transition `<DONE_ID>`.
    - Remove the worktree: `direnv exec . just worktree-remove <branch>`. Run
      this only after the merge has landed and the lock has been released, so the
      branch is fully merged before its worktree is torn down.
    If the operator rejects, address feedback and return to step 6.

11. **Report and prime the CLI.** Before telling the operator you are done, run
    `direnv exec . just run-cli --help` to prime the CLI cache so the human can
    immediately verify the executable's behavior. Then report to the operator:
    restate the ticket (key and summary), confirm the ticket is now in Done,
    summarize what you changed, and **provide a full test inventory.**

    ### Test inventory (mandatory, abort if inadequate)

    Your report must include a **Test Inventory** section that lists, by tier,
    every test you wrote for this work:

    - **Unit tests:** every new unit test file and test function name, grouped by
      crate. State which acceptance criterion each covers.
    - **Integration tests:** every new integration test, with the test file path
      and test function name. Name the provider-double
      rules or harness setup each test uses. State which acceptance criterion
      each covers. This is the tier most commonly skipped — do not omit it.
    - **TUI tests:** every new TUI render or scenario test, with the test file
      path, test function name, and which observable behavior it asserts (visible
      text, style, layout, scroll, focus, etc.). State which acceptance criterion
      each covers.
    - **Live-provider tests** (if applicable): test names and what they exercise.

    **Abort if inadequate.** If the test inventory does not include at least one
    test for every acceptance criterion — or if any tier required by the Coverage
    Matrix has no new tests — **you must abort the report and go back to step 4
    to implement the missing tests.** Do not report completion with missing
    coverage. The operator should never have to ask "did you write tests for
    this?" — if they do, the gate has failed. Re-run the test sufficiency gate
    (step 6) after adding the missing tests.

    Call out any skips/blockers explicitly. Give concrete advice on how to test
    the change (commands to run, behavior to observe).

## Self-verification of observable behavior

When the change has observable prompt/template behavior — a new template
variable, a skill or facet rendering path, frontmatter handling, or anything
else that shapes what the model actually sees — **verify it yourself instead
of leaving that verification to the human.** Unit tests cover the code path;
they do not prove the variable shows up in a live session. Do the live check
before you report and prompt the human to review.

The technique is a throwaway probe under `.polytoken`, run through the
just-built binary, then removed:

1. Add a temporary artifact under `.polytoken` that exercises the new
   behavior. The most common form is a throwaway skill whose body renders the
   new template variable conditionally, e.g. a body containing
   `{% if source_control == "git" %}<secret phrase>{% endif %}` with
   `polytoken: true` frontmatter. Put a unique, unguessable literal (a "secret
   phrase") inside the branch so the only way it appears in the output is if
   the variable resolved to the expected value. The directory name is the skill
   name (`.polytoken/skills/<name>/SKILL.md`).
2. Build and run one non-interactive prompt that loads the probe and repeats
   its contents back:
   `printf '%s' '<prompt telling the model to invoke the skill and echo the phrase>' | direnv exec . just run-cli exec --max-tool-turns 5 --print-session-logs`.
   Pass the multi-word prompt via stdin. The `just run-cli` recipe forwards
   positional arguments in a way that drops shell quotes, so a positional prompt
   gets word-split.
3. Confirm the secret phrase appears in the rendered output. The strongest
   evidence is in the session log: `grep -rl "<secret phrase>"
   ~/.local/share/polytoken/sessions/` finds the exec session's `log.jsonl`,
   where the rendered skill body (the `skill` tool result) shows the phrase.
   MiniJinja runs in `UndefinedBehavior::Strict`, so an unwired variable
   errors the render; a wrong value hits a different branch. Either way the
   secret phrase only appears if the variable resolved correctly.
4. **Delete the probe artifact.** It must not be committed or merged. After
   removal, `git status` under `.polytoken` should be clean.

This costs one real provider call, so use it for behavior changes with a
template/prompt surface, not for pure internal refactors. The worktree's
`.git` (a gitdir pointer) is enough for git-targeting probes; for non-git
values run the probe from a directory without VCS markers.

## Notes

- **Goals complete before merge, not after.** When a saved-session goal is
  active, call `complete_goal` at step 9 (In Review). The merge to main
  (step 10) is operator-gated and outside the goal. An active goal
  suppresses `ask_user_question`; it does NOT authorize autonomous merges.
- Committing to the task branch triggers the lefthook pre-commit gate (`just fix`,
  `just build`, `just test`, `just machete`). Squash-merging to `main` triggers
  the `just test-all` gate instead, which needs the direnv-loaded credentials.
  Commit and merge from a shell where direnv is active, or the commit hook fails
  for want of credentials.
- If the operator cancels mid-execute, leave the ticket In Progress and ask
  whether to restore it to To Do (`<TO_DO_ID>`).
- **⚠️ You MUST operate inside the worktree for every file operation, shell
  command, and subagent spawn.** The worktree is created with `direnv exec .
  just worktree-create <branch>` and entered with `pushd .worktrees/<branch>`.
  If you have not run `just worktree-create` and `pushd`, you are in the wrong
  tree — stop and create the worktree before proceeding. No exceptions.
  Use absolute paths to describe the files you are editing.
