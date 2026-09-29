---
title: Macro definition syntax and maintainable macro style
description: "authoring or editing a `%macro` definition, signature readability, `%mend` name, nesting, parameter names, local variables, or optional file headers."
---

## Critical Rules

### Rule 1: Prefer an explicit parameter list for shared macros

Bare `%macro name;` is legal SAS. For shared or long-lived code, prefer
`%macro name();` for a zero-argument macro and list parameters inside the
parentheses when present. The explicit form makes it obvious where the
signature ends and reduces review mistakes when parameters are added later.

```sas
/* CORRECT - explicit zero-argument signature */
%macro show_name();
  %put NOTE: &=sysmacroname;
%mend show_name;
```

```sas
/* DISCOURAGED IN SHARED CODE - legal SAS, but easier to misread */
%macro show_name;
  %put NOTE: &=sysmacroname;
%mend show_name;
```

### Rule 2: Close long or shared macros with the macro name

Bare `%mend;` is legal SAS. Named endings are easier to audit when files
contain multiple macros or long generated-code blocks.

```sas
/* CORRECT */
%macro summarize_claims(libds, outds=work.summary);
  proc means data=&libds n mean;
    output out=&outds n=n mean=mean_paid;
  run;
%mend summarize_claims;
```

```sas
/* DISCOURAGED IN SHARED CODE - the end marker is ambiguous */
%macro summarize_claims(libds, outds=work.summary);
  proc means data=&libds n mean;
    output out=&outds n=n mean=mean_paid;
  run;
%mend;
```

### Rule 3: Avoid nested `%macro` definitions unless there is a clear reason

A macro definition inside another macro is compiled each time the outer
macro executes. That is usually slower and harder to debug than defining
helper macros separately.

```sas
/* CORRECT - helper is defined separately */
%macro write_note(msg);
  %put NOTE: &msg;
%mend write_note;

%macro outer();
  %write_note(msg=outer is running)
%mend outer;
```

```sas
/* WRONG FOR ROUTINE CODE - helper is recompiled on every outer call */
%macro outer();
  %macro write_note(msg);
    %put NOTE: &msg;
  %mend write_note;
  %write_note(msg=outer is running)
%mend outer;
```

### Rule 4: Keep parameter names valid and option syntax ordinary

Parameter names cannot contain spaces. Use ordinary SAS macro-statement
syntax and keep option use minimal unless a project standard requires it.

```sas
/* CORRECT */
%macro filter_claims(libds, outds=work.filtered, min_paid=0);
  data &outds;
    set &libds;
    where paid_amt >= &min_paid;
  run;
%mend filter_claims;
```

```sas
/* WRONG - a parameter name cannot contain a blank */
%macro filter_claims(libds, out ds=work.filtered);
%mend filter_claims;
```

### Rule 5: Declare non-parameter macro variables with `%local`

Every macro variable created inside a macro should be declared local unless
the macro deliberately writes to a caller-visible variable and documents
that side effect.

```sas
/* CORRECT - working symbols are local */
%macro count_rows(libds, outvar=n_rows);
  %local dsid rc nobs;
  %let dsid = %sysfunc(open(&libds));
  %if &dsid %then %do;
    %let nobs = %sysfunc(attrn(&dsid, nlobs));
    %let rc = %sysfunc(close(&dsid));
  %end;
  %else %let nobs = .;
  %global &outvar;
  %let &outvar = &nobs;
%mend count_rows;
```

```sas
/* WRONG - DSID, RC, and NOBS may leak or overwrite caller variables */
%macro count_rows(libds, outvar=n_rows);
  %let dsid = %sysfunc(open(&libds));
  %let nobs = %sysfunc(attrn(&dsid, nlobs));
  %let rc = %sysfunc(close(&dsid));
  %global &outvar;
  %let &outvar = &nobs;
%mend count_rows;
```

### Rule 6: Use file headers when project style requires them

A short header can help reviewers understand purpose, parameters, outputs,
and side effects. Treat this as a project documentation convention, not as
a SAS language requirement.

```sas
/*
  Macro: require_dataset
  Purpose: Stop early when an expected input dataset is missing.
  Parameters:
    libds - two-level dataset name
*/
%macro require_dataset(libds);
  %if not %sysfunc(exist(&libds)) %then %do;
    %put ERROR: Required dataset &libds does not exist.;
    %abort cancel;
  %end;
%mend require_dataset;
```

## Canonical Idioms

### Idiom: Positional-required plus keyword-optional parameters

Keep required data inputs first and make optional behavior explicit with
keyword parameters and defaults.

```sas
%macro dataset_exists(libds, outvar=dataset_exists);
  %local exists;
  %let exists = %sysfunc(exist(&libds));
  %global &outvar;
  %let &outvar = &exists;
%mend dataset_exists;

%dataset_exists(sashelp.class, outvar=have_class)
%put NOTE: &=have_class;
```

### Idiom: Guarded execution parameter

When a macro has side effects, an optional predicate can let callers skip
work without wrapping the call in an outer `%if` block.

```sas
%macro build_cohort(year=, outds=work.cohort, iftrue=%str(1=1));
  %if not(%eval(%unquote(&iftrue))) %then %return;

  data &outds;
    set raw.claims;
    where year(service_dt) = &year;
  run;
%mend build_cohort;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `%macro` | `%macro name(pos, kw=default);` | Open a macro definition | Hiding required inputs in globals instead of parameters |
| `%mend` | `%mend name;` | Close a macro definition | Bare ending in a long file |
| `%let` | `%let var = value;` | Assign a macro variable | Forgetting scope and overwriting a caller variable |
| `%global` | `%global var1 var2;` | Declare a global macro variable | Using globals for ordinary working variables |
| `%local` | `%local var1 var2;` | Declare variables local to the current macro | Omitting it for temporary symbols |

## Silent Pitfalls

- **Nested macro definitions** are recompiled each time the outer macro runs.
- **Implicit macro variable scope** can overwrite a caller variable with no
  syntax error.
- **Bare `%mend;` in long files** makes it harder to verify which macro just
  ended.
- **Encoded-password literals in code** such as {SAS001}, {SAS002}, and
  {SASENC} should be removed and treated as exposed credentials.

## Anti-patterns (STOP signs)

- `%let x = &y;` inside a macro with no `%local x;`.
- `%macro ...; %macro ...; %mend; %mend;` in routine code.
- Parameter names with embedded blanks.
- Long shared macros that end with bare `%mend;`.
