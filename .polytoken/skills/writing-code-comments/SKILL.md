---
name: writing-code-comments
description: Writing code comments that carry real information. Use when adding or changing code comments, when reviewing verbose or substance-free comments, or when the user says "yap".
---

# Writing Code Comments

A comment earns its place only by saying what the code cannot: the **non-obvious**. Words written to think out loud rather than to inform a reader are **yap** — verbose residue with no payload. Do not ship yap.

## Required Sub-Skills

**ALWAYS REQUIRED:**
- `ste-writing` - A style guide for writing in ASD-STE100 Simplified Technical English 

## What a good comment IS

A good comment is one of:

- **Why, not what.** The reasoning the code can't show: a constraint, a tradeoff, a workaround for a tool bug, why the obvious alternative was rejected.
- **A warning.** A gotcha a competent reader would otherwise trip on: "order matters here", "must run before X".
- **A contract.** A doc comment on a public API: what it does, what callers must guarantee, what it can throw.

And it is always:

- **Beside what it explains.** Details live next to the code they describe — not clumped in one block atop the file or function.
- **Short.** Every sentence survives only if a future reader acts on it.

## Yap red flags

| Pattern | Fix |
|---|---|
| Paraphrases the prompt or task ("This function parses the config as requested") | Delete. Describe the code, never the request. |
| Restates the adjacent code in prose (`i++ // increment i`) | Delete. |
| Narrates history ("We used to use X, now we use Y") | Delete the history; keep only why-now. Git holds the past. |
| Wall-of-text comment atop a file or big function | Break it up; move each part next to the code it explains. |
| Explains the obvious at length, skips the one hard part | Keep the hard part; delete the rest. |
| Right content, wrong spot (**misplaced yap**) | Move it closer to the code it explains. |

## The yap test

For every comment written, before finishing:

1. If a competent reader deleted this comment, would they lose anything the code doesn't already say? No → delete it.
2. Is this next to the code it explains? No → move it.
3. Would half the words say the same thing? Cut them.

Default is **no comment**. Silence beats yap.
