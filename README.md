# polyskills

This is my personal configuration template with skills I use regularly, including
a generalized Jira workflow pack. It also contains two facets, one subagent,
portable hooks, example configuration, and toolchain starters. I maintain it for
my own projects. If you use these skills, use them with
[Polytoken](https://polytoken.dev/).

## Using it

This repository is a configuration template, not an application. It has no
build or run command. You need Git and Polytoken. The hook scripts also need
Python 3.

1. Open a terminal in the folder where you keep your projects.
2. Clone this repository:

   ```sh
   git clone https://github.com/scarnecchia/polyskills.git
   ```

3. Open the cloned `polyskills` folder in your editor.
4. Modify the skills to match your projects.
5. Remove any skills that you do not need.
6. Ask your agent in Polytoken to use the installation guidance:

   > Reference the `polytoken:modifying-polytoken` skill to add these skills to my projects.

The installation uses file copies and configuration changes, not a package
installer. Use these steps with your agent:

1. Copy `.polytoken/` into your project root, or selected skills into `~/.config/polytoken/skills/` for global use.
2. Replace the applicable placeholders in [Customizing the Jira pack](#customizing-the-jira-pack). Each Jira skill's `Constants` block lists its requirements.
3. If you have no user configuration, copy `config.yaml` to `~/.config/polytoken/config.yaml`. Otherwise, use it as a reference.
4. Set the three model groups to models your providers authorize. You can use equivalent groups if you update their references.
5. Register the hook scripts as described in [Hooks](#hooks).
6. Write your project's `AGENTS.md` with an **environment facts** section. This section covers repository layout, test commands, allowed fetch protocols, and service endpoints.
7. Start a planning session in the `plan-dev` facet.

Most tool errors come from unknown environment details, not model failures.
The environment facts help the agent use your project's tools correctly.
The `plan-dev` facet passes its plan to `dev` through `handoff_plan` for
whole-plan approval. This approval request is the expected next step, not an
application launch.

## Developer setup

Use the clone from [Using it](#using-it) to edit the skills and configuration.
This repository has no build, test, or development run command. The example
recipes are placeholders for your project's commands, not tests for this
repository. Python 3 is required only for the hook scripts.

For a project's toolchain, adapt the optional [Project toolchain
starters](#project-toolchain-starters). Their versions are starting points, not
requirements for editing this template.

## What is in it

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

This pack comes from a working setup with placeholders instead of project keys,
cloud IDs, Confluence pages, and raw model names. The portable parts are the
workflows: claim-before-research double-grab, review panels, skeptic gates,
merge gates, and ticket-lifecycle checkpoints.

## Project toolchain starters

These files are optional starting points for the project that uses your skills:

- `mise.toml.example` — starting tool versions (direnv, just, lefthook, uv,
  ruff, shellcheck).
- `justfile.example` — starter recipes with the names the Jira workflow skills
  call (`build`, `test`, `fix`, `worktree-create`, `worktree-remove`).
- `.envrc.example` — starter direnv configuration. The skills use
  `direnv exec .` to run commands in the project environment.

1. Copy the example files you need into your project without the `.example` suffix.
2. Pin the tool versions in `mise.toml` to match your project.
3. Replace the starter recipes in `justfile` with your project's commands.
4. Adapt `.envrc` to your project environment.
5. Keep secrets in a git-ignored `.env.local`, never in `.envrc`.
6. If you use `.envrc`, run `direnv allow` from your project folder.

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

Polytoken does not run these hooks until you register them. To activate them globally:

1. Copy the scripts to `~/.config/polytoken/hooks/`.
2. Merge the entries from `hooks.json.example` into `~/.config/polytoken/hooks.json`.

This repository deliberately excludes other hooks, such as host banners and
private-environment loaders.

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

These are skills I use regularly, largely adapted from the work of others.
Credit goes to [haileyok](https://github.com/haileyok),
[ed3dai](https://github.com/ed3dai), and
[sjennings](https://github.com/sjennings).

The delivery/coding/writing skills are synced copies from a live Polytoken
install. The Jira pack was generalized from a single-project Atlassian setup.
`mise.toml.example` comes from the same source project; `justfile.example` and
`.envrc.example` are fresh starters (the upstream example files were empty).
`config.yaml` is an example, not a requirement — the skills work with any
config that defines the three model groups (or equivalent).

## Deliberately excluded

Domain-specific skills, machine-specific skills, machine-specific hooks (host
banners, private-environment loaders), and secrets.
