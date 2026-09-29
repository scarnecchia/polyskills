---
title: RETAIN accumulators and PDV initialization
description: "retain, PDV, accumulator, carry-forward across rows, cumulative sum, running total, cum = cum + x, PDV-state-across-iterations, row-count sanity check."
---

## Critical Rules

### Rule 6: Retain accumulators and PDV carry-forward variables, or they reset each iteration

A DATA step reinitializes every non-RETAINed PDV slot to missing on each
iteration. An accumulator of the form `cum = cum + x;` therefore computes
missing plus x equals missing every row unless `cum` is retained with an
explicit initial value. The same rule applies to variables that carry state
across BY-group rows.

```sas
/* CORRECT - retain the accumulator with an explicit initial value */
data claims_running;
  set claims;
  by member_id;
  retain cum_paid 0;
  if first.member_id then cum_paid = 0;
  cum_paid = cum_paid + paid_amt;
run;
```

```sas
/* WRONG - cum_paid is not retained */
data claims_running;
  set claims;
  cum_paid = cum_paid + paid_amt;
run;
```

## Canonical Idioms

### Idiom: Row-count sanity check with PROC SQL

Use a quick count after important filters or joins to catch accidental empty
outputs before downstream code runs.

```sas
proc sql noprint;
  select count(*) into :n_claims_clean trimmed
  from work.claims_clean;
quit;

%if %sysevalf(&n_claims_clean = 0) %then %do;
  %put ERROR: claims_clean is empty, stopping pipeline.;
  %abort cancel;
%end;
```

### Idiom: Carry state within a BY group

Retain the previous value when comparing the current row with prior rows in
the same BY group, and reset on `first.group`.

```sas
data claims_gap;
  set claims;
  by member_id service_dt;
  retain prev_service_dt;
  if first.member_id then prev_service_dt = .;
  gap_days = service_dt - prev_service_dt;
  prev_service_dt = service_dt;
run;
```

## Silent Pitfalls

- **`retain` forgotten for accumulator** — `data out; set in; cum = cum + x; run;` without `retain cum 0;` resets `cum` to missing each row.
- **Retain without BY-group reset** — an accumulator retained across the whole step keeps growing past group boundaries. Pair `retain` with `if first.group then acc = 0;`.
- **Length defaulted from first assignment** — the first assignment to a character variable sets its length. Declare `length name $32;` up front or downstream values truncate silently.

## Anti-patterns (STOP signs)

- `data out; set in; cum = cum + x; run;` with no `retain cum 0;`.
- Assigning a character variable for the first time in the middle of a step with no prior `length` declaration.

## Related

Queue-based cross-row state uses a different mechanism: `lag.md`. Compile vs
execute-time filtering relative to the PDV: `where-vs-if.md`.
