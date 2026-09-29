---
description: 'Canonical Jira operations for the project skills — constants, the transport ladder (acli CLI first, Atlassian MCP fallback), per-operation recipes, and ticket-discipline rules. Load via @skill: before any Jira API call.'
---

# Jira Operations

This skill is the single source of truth for how Polytoken skills talk to
Jira. Skills that perform Jira operations reference this skill
(`@skill:jira-ops`) instead of duplicating constants and API mechanics.
Workflow logic (when to claim, when to transition, what to write) stays in
the calling skill; the how lives here.

## Constants

All values in this block are site-specific placeholders — replace them with your own project values before first use.

- Atlassian cloudId: `<ATLASSIAN_CLOUD_ID>`
- Jira project: `<PROJECT_KEY>`
- Transitions: To Do `<TO_DO_ID>`, In Progress `<IN_PROGRESS_ID>`, In Review `<IN_REVIEW_ID>`, Done `<DONE_ID>`.
  These IDs are board-specific (verified 2026-06-18); re-verify with
  `getTransitionsForJiraIssue` (MCP `execute`) if the project board is
  reconfigured.
- Parent epic for housekeeping work: **<HOUSEKEEPING_EPIC_KEY>** (see the `housekeeping`
  skill for its filing rules).

## Transport ladder

Try transports in this order for every Jira operation:

1. **`acli` CLI** (mise shim; OAuth via `acli auth login`, check with
   `acli auth status`). It authenticates to the target cloud site directly and
   survives Atlassian MCP outages. Bulk operations accept comma-separated
   `--key "A,B,C"` lists and print one `✓` line per item — capture that
   output as the per-item evidence.
2. **Atlassian MCP tools** (`mcp__atlassian__*`: `getJiraIssue`,
   `searchJiraIssuesUsingJql`, `transitionJiraIssue`,
   `addOrEditJiraIssueComment`, `editJiraIssue`, `createJiraIssue`).
   These require the cloudId above.
3. If both transports fail, surface the outage and stop — do not guess at
   ticket state.

Do not switch transports in the middle of one logical operation. If an
operation's outcome is ambiguous (timeout, transport drop), re-fetch the
ticket state before retrying; a retried transition or comment can
double-apply.

## Operation recipes

Each row gives the `acli` form and the MCP equivalent. `KEY` is a ticket
key such as `ABC-1244`.

| Operation | acli | MCP |
|---|---|---|
| View fields/status | `acli jira workitem view KEY --fields labels --json` | `getJiraIssue` |
| Search | `acli jira workitem search --jql "<jql>" --json` | `searchJiraIssuesUsingJql` |
| Transition | `acli jira workitem transition --key "KEY" --status "Done" --yes` | `transitionJiraIssue` (transitionId `<DONE_ID>`) |
| Comment | `acli jira workitem comment create --key "KEY" --body-file comment.txt` | `addOrEditJiraIssueComment` |
| Labels | `acli jira workitem edit --key "KEY" --labels "a,b,c" --yes` | `editJiraIssue` (`labels`) |
| Create | `acli jira workitem create --project <PROJECT_KEY> --type Task --parent <HOUSEKEEPING_EPIC_KEY> --label "a,b" --summary "..." --description-file body.txt --json` | `createJiraIssue` |

Notes:

- **acli transitions take the status NAME** (`"In Review"`), not the
  transition id; MCP takes the numeric `transitionId`. The landed status
  is authoritative: MCP `transitionJiraIssue` returns it; with acli,
  re-view the ticket after transitioning.
- **Label edits replace the whole label set** on both transports. Fetch
  the current labels first and write back the union with your addition —
  never pass only the new label.
- `--body-file` / `--description-file` take plain text or ADF; keep
  multiline bodies in files, not shell strings.
- `acli ... --json` prints stable JSON for programmatic parsing
  (`fields.labels`, `fields.status.name`, `key`).
- Creation with `--parent` requires the parent key (`<HOUSEKEEPING_EPIC_KEY>` for
  housekeeping children) and produces the new key on stdout — capture it
  immediately; an interrupted creation must be looked up by summary+JQL,
  never recreated blind.

## Ticket discipline (carried by every consuming skill)

- **Carry the key everywhere.** Reference the ticket key in every API
  call, operator-facing status message, and todo title. Recover it from
  the plan or session state after compaction before doing anything else.
- **Advance the lifecycle at every checkpoint**: To Do → In Progress →
  In Review → Done. Do not skip checkpoints; the most common failure is
  reaching In Review and never advancing to Done after the merge.
- **Done is not optional.** After a verified merge, the Done transition
  is the final required Jira action before reporting completion.
- **Never abandon a ticket mid-lifecycle.** On interruption, re-read the
  actual status (transport-agnostic — see the ladder) and reconcile from
  what Jira says, never from what you remember.
- **Verify, never assume.** Statuses may have changed behind your back
  (another session, an interrupted call that actually landed). One cheap
  `view` beats a wrong transition.
