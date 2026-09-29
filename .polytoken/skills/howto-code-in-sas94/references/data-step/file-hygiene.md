---
title: SAS source hygiene for .sas files
description: "linting, indentation, line length, tabs vs spaces, trailing whitespace, invisible or non-printing characters, encoded password {SAS001} / {SAS002} / {SASENC}."
---

Source hygiene rules do not change DATA-step semantics, but they make SAS
programs easier to review and reduce invisible-byte failures. Apply these
checks when writing or reviewing any shared .sas program.

## Critical Rules

### Hygiene 1: Use consistent space indentation

Pick a project indentation width, commonly two spaces, and apply it
consistently inside DATA steps, PROC blocks, and macro control flow.

```sas
/* CORRECT - consistent two-space indentation */
data out;
  set in;
  if x > 0 then y = log(x);
run;
```

```sas
/* WRONG - mixed one-space and four-space indentation */
data out;
 set in;
    if x > 0 then y = log(x);
run;
```

### Hygiene 2: Keep lines reviewable

Use practical line wrapping for long variable lists, WHERE clauses, and
macro calls. Long lines hide logic in horizontal scroll and make diffs hard
to review.

```sas
/* CORRECT - wrap after logical operators */
data claims_2023;
  set raw.claims;
  where service_dt between "01JAN2023"d and "31DEC2023"d
    and paid_amt > 0
    and not missing(member_id);
run;
```

```sas
/* WRONG - all conditions forced onto one long line */
data claims_2023; set raw.claims; where service_dt between "01JAN2023"d and "31DEC2023"d and paid_amt > 0 and not missing(member_id) and provider_npi ne "" and diagnosis_code in ("E11.9","I10","N18.3","J44.9"); run;
```

### Hygiene 3: Use spaces, not tabs

Tab rendering depends on editor settings. What looks aligned in one editor
may be ragged in another and noisy in diffs.

```sas
/* CORRECT - spaces */
data out;
  set in;
run;
```

```sas
/* WRONG - leading tab before SET */
data out;
<TAB>set in;
run;
```

### Hygiene 4: Strip trailing whitespace

Remove spaces before the newline on every line. Trailing whitespace causes
spurious merge conflicts and diff churn.

```sas
/* CORRECT - no trailing blanks */
data out;
  set in;
run;
```

```sas
/* WRONG - imagine extra blanks after each semicolon */
%put NOTE: hello;
%put NOTE: world;
```

### Hygiene 5: Remove invisible or non-printing characters

A byte-order mark, non-breaking space, or other invisible character inside a
string literal can make equality comparisons fail without an obvious log
message.

```sas
/* CORRECT - plain visible characters */
data out;
  set in;
  where member_id = "A12345";
run;
```

```sas
/* WRONG - invisible bytes may be present inside the literal */
data out;
  set in;
  where member_id = "A<U+FEFF>12345";
run;
```

### Hygiene 6: Never commit encoded-password literals

SAS encoded password markers such as {SAS001}, {SAS002}, and {SASENC} are
reversible obfuscation, not encryption. Treat them as plaintext secrets.

```sas
/* CORRECT - read credentials from the run environment */
libname db oracle user=svc password="&env_db_pw" path=prod;
```

```sas
/* WRONG - committed credential-like literal */
libname db oracle user=svc password="{SAS002}D41D8CD98F00B204E9800998ECF8427E" path=prod;
```

## Silent Pitfalls

- **Trailing spaces, tabs, and invisible bytes** can break string compares
  or flood code review with whitespace-only diffs.
- **Encoded password markers in committed code** should trigger credential
  rotation and replacement with environment, authinfo, or scheduler-managed
  secret handling.

## Anti-patterns (STOP signs)

- Mixed tab and space indentation in the same file.
- Committing any {SAS001}, {SAS002}, or {SASENC} literal.
- Copying code from office documents or spreadsheets without checking for
  non-printing characters.
