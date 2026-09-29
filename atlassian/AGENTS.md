# Atlassian workflows

## Purpose

These skills connect Jira planning, implementation, review, and documentation
into one pipeline. They were written against one team's Jira site and project;
every site-specific value in them is a placeholder that must be replaced before
use. The README's customization table lists all placeholders and where they
appear.

## Contracts

- Keep planning and execution handoffs consistent when changing either side.
- Preserve shared runtime contracts across the `jira-epic-*` skills.
- Review state ownership and merge rules before changing `.current-epic` or
  `.current-gc` procedures.
- Keep operator approval gates for ticket decisions and external writes.

## Dependencies and adoption

These workflows need Atlassian access (the `acli` CLI or an Atlassian MCP
server), configured subagents, and project-specific Git procedures. Installing
the skills does not supply these services.

Before reuse, replace the values in each skill's Constants block: project keys,
Atlassian cloud ID, issue-type and transition IDs, Confluence containers and
page IDs, product-area names, Confluence labels, and model-group names.

`jira-ops` is the canonical Jira transport layer for the other Jira skills. It
defines the acli-first transport ladder with an Atlassian MCP fallback and
supplies per-operation recipes. Workflow skills reference it instead of
duplicating API mechanics.

`batch-fb-to-jira-tickets/fb-to-jira-ticket/` is a separate skill despite its
nested location.

Keep service credentials outside these files. Confirm the target site and
project before a workflow changes external records.
