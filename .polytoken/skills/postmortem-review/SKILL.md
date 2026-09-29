---
description: Prepare a parent-session evidence bundle and launch the postmortem-reviewer subagent to improve the development process rather than the product.
polytoken:
  disable_model_invocation: true
---

# Postmortem review

Use this skill only from the parent session. It prepares evidence for the
`postmortem-reviewer` subagent. The reviewer examines how the project was
developed and recommends systemic improvements to that development process. It
does not repair the product or continue the implementation.

## Decide whether to run the review

Run a postmortem review at a meaningful boundary, such as:

- completion of a substantial task or Epic;
- a blocked, abandoned, or non-convergent workflow;
- repeated repair or review rounds;
- a surprising failure, red herring, or long investigation;
- a process change that needs independent assessment.

Do not run the reviewer merely because a task was difficult. Run it when the
interaction contains evidence that can improve future work.

## Identify the parent session

Use the current Polytoken session ID from the runtime/session context when that
value is available. Do not invent a session ID. The durable parent transcript
normally lives at:

```text
$XDG_DATA_HOME/polytoken/sessions/<SESSION_ID>/log.jsonl
```

When `XDG_DATA_HOME` is unset, the default is:

```text
~/.local/share/polytoken/sessions/<SESSION_ID>/log.jsonl
```

The primary transcript is `log.jsonl`. Subagent transcripts and other workflow
artifacts can live beside it under the same session directory. The parent may
not know the session directory from its task prompt, so use the runtime session
ID or another observed session artifact. If the ID or path cannot be
established, state that the postmortem is blocked and ask for the path. Do not
search all session directories or guess from a nearby session name.

## Prepare a temporary evidence bundle

Create a temporary directory that the parent can grant to the child. Prefer a
session-specific temporary directory outside the project, for example:

```sh
bundle_dir="$(mktemp -d "${TMPDIR:-/tmp}/polytoken-postmortem.XXXXXX")"
```

Copy only the evidence needed for this review into the bundle. Include the
parent `log.jsonl` and, when available, relevant subagent logs, plans, review
findings, workflow state, test results, and operator-decision artifacts. Keep
the original filenames or add a short manifest so the reviewer can identify
which agent produced each record.

Do not give the reviewer unrestricted access to the raw session directory. Raw
logs can contain credentials, tokens, private prompts, unrelated paths, and
sensitive tool arguments. Before dispatch:

1. Copy the selected logs into the temporary directory.
2. Remove or redact credentials, bearer tokens, API keys, cookies, private
   personal data, and unrelated sensitive content.
3. Preserve timestamps, message order, tool names, error text, file paths needed
   to explain the workflow, and enough context to establish causation.
4. Add a `MANIFEST.md` describing the session ID, source files, redactions, and
   known evidence gaps. Do not put secrets in the manifest.
5. Verify that the bundle contains only intended files and is readable.
6. Add an explicit inventory to `MANIFEST.md` naming the parent log, every
   represented subagent log, and every omitted artifact with the reason it was
   omitted.
7. Run a post-redaction scan for credential markers and fail closed if the scan
   finds a suspected secret. Record the scan result in the manifest without
   recording secret values.

Use shell commands for copying and redaction only when the command is safe and
observable. Do not print the raw bundle or secrets into the conversation. When
the bundle contains a large transcript, tell the child to use targeted reads and
searches instead of loading every file at once.

The bundle is not complete until the manifest inventory is explicit. If a
represented subagent log or workflow artifact is unavailable, list it under
`Omitted` and mark the review scope as incomplete. Do not claim that every
represented agent was reviewed when the evidence bundle does not contain that
agent's record.

## Grant read access

The child needs a filesystem read grant for the temporary bundle. A path in the
spawn prompt does not grant access. Request or obtain a read-only directory
grant through the normal permission flow before launching the child. The parent
and subagents share the relevant permission infrastructure, so the resulting
grant can be used by the reviewer.

Grant the bundle directory, not the entire session-data tree. Do not grant write
access. If the grant cannot be obtained, do not launch the reviewer and report
the missing authorization as the blocker.

## Launch the reviewer

Use the `subagent` tool without `resume_from`. A fresh launch gives the reviewer
an independent conversational context. Use the configured
`postmortem-reviewer` subagent type. The reviewer is read-only and already has
its postmortem framing, evidence-handling rules, skill-versus-subagent guidance,
and structured exit schema.

Set `model_override` only when the review needs a deliberate model choice. The
configured definition supplies the normal model. Do not use `resume_from`: that
would seed another subagent's conversation history and defeat the independent
review.

The spawn prompt must include all of the following:

- the absolute path to the temporary evidence bundle;
- the parent session ID, if known;
- the intended outcome and scope of the development interaction;
- which logs and artifacts the bundle contains;
- important redactions or evidence gaps;
- an explicit instruction not to modify the project or continue implementation;
- the requested structured output and any deadline or prioritization need.

Use a prompt in this shape, replacing bracketed values:

```text
Review the read-only postmortem evidence bundle at:
[BUNDLE_DIR]

Parent session ID: [SESSION_ID or unknown]

The development interaction intended to:
[INTENDED OUTCOME]

The bundle contains:
[FILES AND ARTIFACTS]

Redactions and evidence gaps:
[REDACTIONS OR NONE]

Review the primary agent and every represented subagent. Focus on off-track work,
red herrings, repeated iterations, duplicated investigation, lost handoffs,
operator friction, and rules or gates that failed to help. Do not modify the
project and do not continue implementation.

Prefer systemic remedies over spot fixes. For each recommendation, explain
whether the right surface is an AGENTS.md file, skill, subagent, facet, tool,
test, lint, workflow gate, or removal of low-value ceremony. Include a future
validation scenario and rank recommendations by leverage and confidence.

Return the configured structured postmortem result. Cite bundle filenames and
record or line locations where possible.
```

## Interpret the result

Treat the reviewer output as a process-improvement proposal, not an automatic
change request. Check each recommendation against the evidence and distinguish:

- a one-off agent mistake;
- a recurring process weakness;
- a missing or contradictory instruction;
- a tool or permission limitation;
- unnecessary ceremony;
- a product defect that belongs in normal engineering work instead.

Prefer changes that prevent a class of future failures. Route concrete accepted
process changes through the normal planning and review workflow. A proposed
skill should explain its invocation point, scope, baseline behavior, and
validation scenarios. A proposed subagent should explain why the work needs
parallelization, a disposable context, or a fresh/blind independent view. A
nearby `AGENTS.md` change should belong to the directory whose ongoing work
needs the guidance.

Preserve the evidence bundle until the review result and any needed follow-up
are recorded. Remove the temporary bundle afterward when retention is no longer
needed. Do not delete the original session logs.
