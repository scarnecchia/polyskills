# polyskills

A portable Polytoken configuration template: curated skills, two facets, one
subagent, portable hooks, an example user config, project-toolchain starter
files, and a generalized Jira workflow pack. Copy what you need into a
project's `.polytoken/` directory or your global `~/.config/polytoken/`, then
fill in the marked placeholders.

## What's in it

```
.polytoken/
  facets/
    plan-dev.md   read-only code-planning facet (modeled on the plan facet)
    dev.md        approved-plan execution facet (modeled on the execute facet)
  subagents/
    project-context-librarian.md   delivery-loop docs loop; maintaining-project-context
  hooks/
    git-command-reminder.py   nags about AGENTS.md upkeep when git/jj is used
    completion-proof.py       stop hook that verifies pushes before handback
    scope-guard.py            fences file edits to the declared scope roots
  skills/
    # delivery loop
    delivery-loop/            push → PR → review → docs → completion proof
    create-pr/                draft PR creation (gh / atgc)
    code-review/              two-reviewer (standard + adversarial) diff review
    review/                   diff-since-X multi-lens review (+ companion docs)
    using-git-worktrees/      isolated workspace before implementation
    housekeeping/             out-of-scope findings → repo issue tracker
    # coding core
    coding-effectively/       umbrella; routes to language sub-skills
    howto-functional-vs-imperative/  FCIS — required by coding-effectively
    defense-in-depth/         validation layering for invalid-data bugs
    writing-good-tests/       test discipline
    # writing chain
    writing-agent-context-files/  AGENTS.md authoring/upkeep
    writing-agent-directives/     (+ graphviz-conventions.dot, long-running-state-patterns.md)
    prompt-security-hardening/
    writing-code-comments/
    ste-writing/
    writing-for-a-technical-audience/
    writing-good-readmes/
    maintaining-project-context/
    # Jira workflow pack (generic; see "Customizing the Jira pack")
    jira-ops/                 canonical Jira transport layer (constants + recipes)
    jira-epic-from-prd/       PRD → reviewed Epic + child issues
    jira-epic-run/            parent orchestrator for an Epic
    jira-epic-state/          .current-epic runtime contracts
    jira-epic-task-plan/      per-task plan authoring inside an Epic run
    jira-epic-task-execute/   per-task implementation inside an Epic run
    jira-epic-docs/           docs lanes for an Epic
    jira-epic-close/          review panel + docs closeout for an Epic
    jira-solo-tasker-plan/    claim and plan a standalone ticket
    jira-solo-tasker-execute/ implement, review, merge, close a standalone ticket
    batch-fb-to-jira-tickets/ batch Feedback→engineering triage (orchestrator)
      fb-to-jira-ticket/      single-ticket worker (a separate skill despite nesting)
    garbage-collection-plan/    plan a behavior-preserving cleanup pass
    garbage-collection-execute/ execute the cleanup pass
    # language packs (conditional refs of coding-effectively) + extras
    howto-code-in-python/       Python discipline (uv, ruff, pytest, typing)
    howto-code-in-rust/         Rust discipline (errors, cargo, testing)
    howto-code-in-typescript/   TypeScript discipline (+ typebox, type-fest)
    howto-develop-with-postgres/ TX-safe Postgres access (+ drizzle notes)
    programming-in-react/       React patterns (+ hooks deep-dive, testing)
    property-based-testing/     property catalogs and library reference
    howto-code-in-sas94/        SAS 9.4 discipline (+ large references tree)
    postmortem-review/          development-process postmortems
    typesafe-ai/                typed judgments and probabilities for LLM apps
    typography-designer/        interface typography (+ reference docs)
config.yaml                   example user config (model groups + playwright MCP)
hooks.json.example            hook registrations for the three portable hooks
mise.toml.example             starter tool versions (mise)
justfile.example              starter recipes matching the workflow skills
.envrc.example                starter direnv config (skills run via `direnv exec .`)
```

Language packs and extras (`howto-code-in-python`, `howto-code-in-rust`,
`howto-code-in-typescript`, `howto-develop-with-postgres`,
`programming-in-react`, `property-based-testing`, `howto-code-in-sas94`,
`postmortem-review`, `typesafe-ai`, `typography-designer`; plus `using-atgc`
for Tangled-hosted projects, if you use it) are conditional references of
`coding-effectively`. They are vendored here; re-sync them from your global
install when that set moves.

## Customizing the Jira pack

The Jira skills are workflow templates: every site-specific value is a
`<PLACEHOLDER>`, and each skill's `Constants` block says so at the top.
Replace these before first use:

| Placeholder | Where | Replace with |
|---|---|---|
| `<PROJECT_KEY>` | all `jira-*`, batch pack | your Jira project key (the feedback skills call the target project "DEV" in prose) |
| `<SD_PROJECT_KEY>` | batch pack | the Jira project key that receives feedback tickets (prose shorthand for its tickets: "SD") |
| `<ATLASSIAN_CLOUD_ID>` | `jira-ops`, `jira-epic-from-prd`, `jira-epic-run`, `jira-solo-tasker-*`, batch pack | your Atlassian cloud ID |
| `<TASK_TYPE_ID>`, `<BUG_TYPE_ID>`, `<SD_PROJECT_ID>`, `<SD_TASK_TYPE_ID>`, `<PROJECT_ID>` | batch pack, `jira-solo-tasker-plan`, `jira-epic-*` | your site's issue-type and project IDs (discover them; they differ per site) |
| `<TO_DO_ID>`, `<IN_PROGRESS_ID>`, `<IN_REVIEW_ID>`, `<DONE_ID>` | `jira-ops`, `jira-epic-run`, solo-tasker pair | your board's transition IDs — the skills also show dynamic discovery via `getTransitionsForJiraIssue`, which is the safer path |
| `<HOUSEKEEPING_EPIC_KEY>` | `jira-ops` create recipe | the parent epic for housekeeping tickets, if you use one |
| `<PRODUCT_AREA>`, `<PRD_CONTAINER>`, `<TD_CONTAINER>`, `<PRD_GUIDE>`, `<*_PAGE_ID>`, `<TD_LABEL>`, `<AREA_LABEL>`, `<STATUS_LIVE_LABEL>` | `jira-epic-from-prd` | your Confluence space's containers, page IDs, and label scheme |
| `<PROJECT>_TEST_*` | task-plan/solo-tasker test tiers | your test-harness env-var prefix |
| `@mg:workhorse`, `@mg:arch`, `@mg:review` | many skills + both facets | model-group names from `config.yaml` `modelgroups` — keep these three names or rename and update references |
| `<workhorse-model-*>`, `<arch-model-*>`, `<review-model-*>` | `config.yaml` | model references your providers authorize (format: `<provider>/<model>(<effort>)`) |
| `<project-prefix>-<number>_<short-description>` | solo-tasker pair | your worktree branch naming convention |
| `just build` / `just test` / `just fix`, `direnv exec .`, pre-commit hooks, `.worktrees/`, `.merge-lock`, single-`main` branch model | solo-tasker + epic skills | your project's real build/test/merge commands and branch model — the workflows assume a long-lived `main` with worktrees, but every command is named explicitly so you can swap it |

The pack was extracted from a working setup and de-personalized: project keys,
cloud IDs, Confluence pages, and raw model names were all replaced.
replaced. The workflow shapes (claim-before-research double-grab, review
panels, skeptic gates, merge gates, ticket-lifecycle checkpoints) are the
portable part.

## Project toolchain starters

- `mise.toml.example` — starting tool versions (direnv, just, lefthook, uv,
  ruff, shellcheck). Copy to `mise.toml` and pin what your project needs.
- `justfile.example` — starter recipes with the names the Jira workflow skills
  call (`build`, `test`, `fix`, `worktree-create`, `worktree-remove`).
- `.envrc.example` — starter direnv config; the skills run commands through
  `direnv exec .`, so this file is what loads the project environment. Copy to
  `.envrc`, adapt, then `direnv allow`. Keep secrets in a git-ignored
  `.env.local`, never in `.envrc`.

## Hooks

The three hook scripts under `.polytoken/hooks/` are portable and
machine-agnostic:

- `git-command-reminder.py` — reminds the agent to keep `AGENTS.md` files
  current when it runs git/jj commands (pairs with the
  `maintaining-project-context` skill).
- `completion-proof.py` — stop hook used by the `delivery-loop` skill to prove
  work was actually pushed before a session hands back.
- `scope-guard.py` — fences file edits to the scope roots declared for the
  session.

They do nothing until registered. To activate them globally, copy the scripts
to `~/.config/polytoken/hooks/` and merge the entries from
`hooks.json.example` into your `~/.config/polytoken/hooks.json`. Other hooks
you may run (host banners, private-environment loaders) are deliberately not
included.

## Using it

1. Copy `.polytoken/` into a new project root, or copy selected skills into
   `~/.config/polytoken/skills/` to make them global.
2. Work through the customization table above (each Jira skill's Constants
   block lists exactly what it needs).
3. Copy `config.yaml` to `~/.config/polytoken/config.yaml`, fill the model
   groups, and copy the hook scripts + register them per the Hooks section.
4. Start from the toolchain starters (`mise.toml`, `justfile`, `.envrc`) and
   adapt them to your stack.
5. Write the project's `AGENTS.md` with an **environment facts** section
   (repo layout, test command, allowed fetch protocols, service endpoints) —
   most tool errors come from environment unknowns, not model failures.
6. Start planning sessions in the `plan-dev` facet; they hand off to `dev`
   via `handoff_plan` for whole-plan approval.

## Design notes

- **Model references use model groups, never raw model names.** Groups are
  defined once in `config.yaml` and referenced as `@mg:<group>` everywhere, so
  swapping providers never touches the skills.
- **Scope-guard declarations are written with the file tool**, not shell
  redirection.
- `plan-dev`/`dev` carry the pre-authorization contract: every step enumerated
  in an approved plan is operator-confirmed; anything else stops and asks.
- The only subagent shipped here is `project-context-librarian`, because it is
  the only one the vendored skills dispatch by name. Harness-shipped subagents
  (`general-purpose`, `general-purpose-mini`, `researcher`, `plan-reviewer`)
  are assumed and deliberately not shadowed.

## Provenance

The delivery/coding/writing skills are synced copies from a live Polytoken
install. The Jira pack was generalized from a single-project Atlassian setup.
`mise.toml.example` comes from the same source project; `justfile.example` and
`.envrc.example` are fresh starters (the upstream example files were empty).
`config.yaml` is an example, not a requirement — the skills work with any
config that defines the three model groups (or equivalent).

## Deliberately excluded

Domain-specific skills, machine-specific skills, machine-specific hooks (host
banners, private-environment loaders), and secrets.
