---
title: %INCLUDE vs %MACRO vs SET - when to use which
description: "deciding between file inclusion (`%INCLUDE`) and parameterized reuse (`%MACRO`); confusion between DATA-step `SET` and code-level inclusion; autoexec / libname / format-catalog config."
---

## Critical Rules

### Rule 8: Use `%INCLUDE` for file-level composition, `%MACRO` for call-site reuse, and `SET` for dataset input

`%INCLUDE` inlines the contents of a file into the current program at parse
time. Every `%let`, `%macro`, `libname`, and global statement in that file
runs in the including program context. Use it for shared config such as
autoexec fragments, libname blocks, format catalogs, and common option
settings.

Do not use `%INCLUDE` as a substitute for `%MACRO`. A call-site include has
no parameter list, no local macro scope, and re-parses the file every time.
For reusable logic that needs parameters, define a macro once and call it
with explicit arguments.

`SET` is a DATA-step statement for reading or stacking datasets. It is not a
code-inclusion mechanism.

```sas
/* CORRECT - %INCLUDE for one-time config at program head */
%include "/projects/study_2024/config/libnames.sas";
%include "/projects/study_2024/config/formats.sas";

/* CORRECT - %MACRO for parameterized reuse */
%macro build_cohort(year=, dx_filter=);
  data work.cohort_&year;
    set raw.claims;
    where year(service_dt) = &year and diagnosis_code = "&dx_filter";
  run;
%mend build_cohort;

%build_cohort(year=2023, dx_filter=E11)
%build_cohort(year=2024, dx_filter=E11)
```

```sas
/* WRONG - %INCLUDE used as pseudo-macro; no params, no local scope */
%include "/projects/study_2024/steps/build_cohort.sas";
%include "/projects/study_2024/steps/build_cohort.sas";
```

### Decision summary

| Need | Use | Why |
|------|-----|-----|
| Load shared libname, format, or option block once at program head | `%INCLUDE` | File-level composition; executes in caller context at parse time. |
| Reusable logic with parameters such as year, cohort, or filter | `%MACRO ... %MEND` | Parameter list and local macro scope. |
| Stack or read observations from datasets | DATA-step `SET` | Dataset input, not code composition. |

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `%include` | `%include "path/file.sas";` | Inline a SAS program file at parse time | Using in place of `%macro` for parameterized reuse |
| `%macro` / `%mend` | `%macro name(...); ... %mend name;` | Parameterized, scoped reuse | Substituting `%include` and losing parameters plus scope |
| `SET` | `set lib.ds1 lib.ds2;` | Stack or read rows from datasets | Confusing with code inclusion |

## Silent Pitfalls

- **`%INCLUDE` used as a pseudo-macro** — it has no parameters and no local macro scope.
- **`%INCLUDE` of a file that contains `%let` or `libname` statements** — those statements run in the caller context.
- **Relative paths in `%INCLUDE`** — resolution depends on the SAS working directory at submit time.
- **`SET` confused with include** — `SET lib.ds;` reads rows into the PDV; it does not execute .sas code.

## Anti-patterns (STOP signs)

- Repeating `%include` on the same step file expecting a fresh parameterized call.
- Including a file that hard-codes a year when the caller needs different years.
- Using `SET` for code inclusion.

Cross-ref: `../data-step/file-hygiene.md` covers hygiene for program-head config fragments.
