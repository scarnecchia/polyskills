---
title: macros topic index
description: '"%macro", "%let", "%sysfunc", quoting error, `&&var`, symget/symput, or any macro authoring/debugging task — load the specific reference file for the sub-topic.'
---

## Routing Table

The SAS macro language runs at compile time — it generates SAS code that
then executes. Most "macro errors" are actually *resolution-order* errors:
the macro processor resolved something too early, too late, or in the
wrong scope. This topic is split into five reference files; load only what the task
needs.

| Atom | Load when |
|------|-----------|
| [definition-syntax.md](definition-syntax.md) | Authoring a `%macro`; signature readability, named `%mend`, avoiding unnecessary nesting, parameter syntax, optional file headers, and `%local` discipline. |
| [scope-and-quoting.md](scope-and-quoting.md) | Scope leak (`%let` inside `%macro` without `%local`); quoting bugs (`%str`, `%nrstr`, `%bquote`, `%nrbquote`, `%superq`); `call symputx` / `symget` scope argument. |
| [debugging.md](debugging.md) | Macro returns wrong value, log too quiet, resolution-order suspected; toggling `MPRINT` / `MLOGIC` / `SYMBOLGEN`; `%PUT _USER_` / `%PUT _ALL_`; `OPTIONS OBS=0 NONOTES NOSOURCE` dry run. |
| [include-vs-macro.md](include-vs-macro.md) | Deciding between `%INCLUDE`, `%MACRO`, and DATA-step `SET`; file inclusion at parse time vs parameterized reuse. |
| [sysfunc-and-eval.md](sysfunc-and-eval.md) | Arithmetic inside macro code; calling DATA-step functions from macro context; `%eval` integer-only vs `%sysevalf` floating with `integer` / `ceil` / `floor` / `boolean` conversion. |

## Cross-topic siblings

- `../data-step/macro-quoting.md` — DATA-step-side of macro-generated code, `call symputx` / `symget`.
- `../data-step/file-hygiene.md` — program-head autoexec fragments that pair with `%INCLUDE`.
- `../base-procs/schema-utils.md` — `PROC SQL INTO :macvar` list pattern (loaded separately).
