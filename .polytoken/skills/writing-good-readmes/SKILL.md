---
description: "Use when creating, rewriting, or updating a project README, including installation instructions for users and development setup instructions."
---

# Writing good READMEs

Delegate all README writing and revisions to a `general-purpose` subagent
with `model_override: "@mg:review"`. The parent gathers evidence,
reviews the result, and requests corrections. The parent does not write
replacement README prose.

## Required writer setup

Before writing, the subagent must load these skills with the `skill` tool:

- `writing-for-a-technical-audience`
- `ste-writing`

Apply both skills. If their style rules conflict, follow `ste-writing`.
Use its strict mode for setup procedures and STE-flavored mode for descriptions.
Use sentence case for headings.

If the model, subagent, or either skill is unavailable, report the blocker.
Do not substitute another model or write the README in the parent session.

## Prepare the assignment

1. Identify the README path and applicable project instructions.
2. Inspect project manifests, setup scripts, command definitions, and existing documentation.
3. Identify the supported user installation method and the separate development workflow.
4. Record evidence for prerequisites, commands, configuration, and expected results.
5. Ask about missing facts only when they change the instructions.

Do not assume a package manager, release download, container, or hosted service exists.
For a library or template, describe its actual use instead of inventing an application launch command.
If no end-user installation exists, state this in the user section and link to developer setup.

## Delegate the writing

Call `subagent` with these arguments:

- `subagent_type`: `general-purpose`
- `model_override`: `@mg:review`
- `name`: `readme-writer`
- `cwd`: the project directory

Give the writer the exact README path, permitted edit scope, project instructions,
and verified source paths. Include the requirements below in its assignment.
Explicitly instruct it to load both required skills before writing.
Request the changed path, evidence for commands, checks performed, and unresolved questions.

Keep the writer's edits limited to the requested README files.
The assignment does not authorize dependency installation, service changes, commits, or publication.

## Required README content

Keep these sections in this order. Add other sections only when the project needs them.

### Project title

Use one level-one heading with the project's actual name.

### Short description

Explain what the project does and who can use it in one short paragraph.
Describe current behavior, not planned features or unsupported benefits.

### Install and run

Write this section for a relatively non-technical reader.

- Explain what the reader needs before starting, including supported operating systems and required accounts.
- Give the simplest supported installation method as numbered steps.
- If commands are necessary, explain how to open a terminal and which folder to use.
- Explain unfamiliar terms when they first appear.
- Separate commands from sample output so readers can copy commands safely.
- Explain how to start the project and complete one basic action.
- Describe the visible result that confirms success.
- Explain how to stop the project when applicable.

Keep development tools out of this section unless ordinary users need them.
Explain any required value that the reader must supply. Do not include credentials in examples.

### Developer setup

Write this section for someone who will change and test the project.

- List the supported toolchain and required versions from project evidence.
- Explain how to get the source and enter the project directory.
- Document dependency setup and local configuration.
- Document required services and database setup when applicable.
- Give the development run command and expected result.
- Include existing test, lint, and build commands relevant to development.

Distinguish required steps from optional tools.
If the repository has no test, build, or run command, say so instead of inventing one.
Reference secret managers or environment variables for credentials.
Document ignore rules and file permissions when local configuration contains secrets.

## Review and finish

1. Read the writer's README and check all four required sections.
2. Trace each command, version, path, and configuration claim to project evidence.
3. Check that user instructions require no unexplained development knowledge.
4. Check Markdown links and the expected results of setup steps.
5. Run safe checks available in the current environment.
6. Return defects to a subagent using the same required model and writing skills.
7. Report the changed files, completed checks, and any untested instructions.

Do not execute destructive commands or install software merely to validate prose.
Distinguish commands checked against source files from commands tested by execution.
Finish only when the README meets the requirements or a reported blocker prevents completion.
