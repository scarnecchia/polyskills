---
name: howto-code-in-python
description: Use when writing, reviewing, or modifying Python code - covers Python 3.11+ typing, functional core/imperative shell structure, uv/ruff/mypy/pytest/hypothesis tooling, structured JSON logging, error classification, and src/ project layout
---

# Writing Python

## Overview

Python house style. Applies whenever writing, reviewing, or modifying Python code.

Opinionated by design: fewer choices means less time debating style and more time solving problems. The core idea: small, pure functions that transform data; thin orchestration layers that handle I/O.

Python 3.11 is the floor, not the target. It is the oldest version that provides modern type hint syntax (`str | None`, `list[str]`) without `from __future__ import annotations`, plus `tomllib`, `ExceptionGroup`, and `TaskGroup` in the standard library. Use a higher version when the project already does or when its features are useful -- just never lower the floor:

```toml
[project]
requires-python = ">=3.11"
```

## Toolchain

| Tool | Purpose | Replaces |
|------|---------|----------|
| `uv` | Package, environment, and project management | `pip`, `venv`, `pip-tools`, `pipx` |
| `ruff` | Linting and formatting | `black`, `isort`, `flake8` |
| `pytest` | Test runner and fixtures | `unittest` |
| `hypothesis` | Property-based testing | Manual edge-case enumeration |
| `mypy --strict` | Static type checking (run in CI) | Runtime type errors |
| `logging` (stdlib) | Structured logging | `print` statements |
| `polars` | DataFrame operations (preferred) | `pandas` for new code |

Prefer `uv` over `pip` for installing dependencies, creating environments, and running tools (`uv add`, `uv sync`, `uv run`), unless the user directs otherwise or the project is already committed to another workflow.

Configure ruff in `pyproject.toml`, with `target-version` matching the project's actual floor:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "TCH"]
```

Run `ruff format` and do not hand-format. `pyproject.toml` only -- no `setup.py`, no `setup.cfg`.

## Functional core / imperative shell

Follow ed3d-house-style:howto-functional-vs-imperative. Python-specific rules:

- Label every source file with a `# pattern:` comment on line 1: `# pattern: Functional Core`, `# pattern: Imperative Shell`, or `# pattern: Mixed (unavoidable) -- [justification]`. If you cannot justify the mix, split the file.
- **Data flows into the core; I/O handles stay in the shell.** Passing a DataFrame into a core function is correct. Passing a database connection or HTTP client into a core function is a red flag.
- Core functions may accept an optional `logger: logging.Logger | None = None` parameter for diagnostics. Diagnostic logging is a deliberate part of the design, not an exception to purity.
- The core never imports the shell. Dependencies flow inward.
- **If you cannot describe what a function does without the word "and", split it.** This applies to computation, not wiring -- a shell function's job is to sequence I/O around core calls.
- Inject shell dependencies as keyword arguments with real defaults. Tests pass fakes; no mocking framework needed:

```python
def convert_one(
    run_id: str,
    api_url: str,
    *,
    http_module=converter_http,
    convert_fn=convert_sas_to_parquet,
) -> ConversionResult:
    ...
```

## Type annotations

- **All function signatures get annotations** -- parameters and return type, no exceptions. The signature is the documentation.
- Enforce with `mypy --strict` in CI. Annotations without a checker are documentation that silently rots.
- Modern syntax only: `str | None`, not `Optional[str]`; `list[str]`, not `List[str]`. This works natively on 3.11+, so never add `from __future__ import annotations`.
- Use `Literal` for constrained string values so typos fail at edit time, not in production:

```python
ErrorClass = Literal["source_missing", "source_permission", "parse_error", "unknown"]
```

- Use frozen dataclasses for structured data, never bare tuples or dicts. Raw deserialized input at a boundary may be typed as a `TypedDict` until it is converted; data you construct gets a dataclass. Use `tuple` rather than `list` for collection fields -- a frozen dataclass still allows `.append()` on a `list` field:

```python
@dataclass(frozen=True)
class ConversionResult:
    outcome: Literal["success", "failure", "skipped"]
    table: str
    warnings: tuple[SchemaWarning, ...] = ()
    error: str | None = None
```

- **Always specify explicit dtypes for columns holding identifiers, counts, or monetary values.** DataFrame libraries may infer `int32`/`float32` from observed values, and truncation bugs are silent. Use `Int64` and `schema_overrides` when reading external files. The cost of the wider type is negligible; the bugs are not.

## Error handling

Two tiers:

1. **Expected findings** (validation results): return them as data -- a list of warning dataclasses, not exceptions. When findings can be fatal, the caller decides severity through a policy object (e.g., a frozen dataclass with a `frozenset` of fatal check names), not ad-hoc `if` checks scattered through the shell.
2. **System errors** (unexpected, infrastructure): catch at the shell boundary, classify, log with context, and return a failure result value.

Rules:

- Never bare `except` without re-raising or classifying. Every caught exception is logged with context or re-raised.
- Create custom exceptions for domain concepts. `SchemaDriftError` tells you what went wrong; `ValueError` does not.
- Centralise exception classification in one function returning an `ErrorClass` literal, matching narrow types before broad ones (`PermissionError` before `OSError`).
- Error messages are lowercase sentence fragments that compose when chained: `"conversion failed: schema mismatch in column patid"`. No title case, no periods.

## Structured logging

- Use `logging`, never `print`. Configure handlers and a JSON-lines formatter once at the entry point; library code calls `logging.getLogger(__name__)` and nothing else.
- Emit one JSON object per event with semantic context via `extra` fields -- enough to answer: which run? which table? what happened?

```python
log.info("conversion complete", extra={
    "table": "enrollment", "run_id": "run-2024-0042",
    "rows_written": 84_210, "warnings": 3, "duration_seconds": 12.4,
})
```

- Structured business events belong in the shell; core functions log diagnostics only, through the optional logger parameter.
- **Never log row-level data.** Log counts, column names, and metadata -- never identifiers, dates of service, or other sensitive values.
- Log paths relative to the project or data root, not absolute paths, which can leak directory structure and server details.
- Design log fields (counts, durations, warning tallies) assuming they will eventually feed metrics dashboards.

## Testing

Follow ed3d-house-style:writing-good-tests and ed3d-house-style:property-based-testing. Python-specific rules:

- Unit tests exercise the core with fabricated data -- no files, no mocking, no setup. **If your test needs more setup than assertion, the function under test is doing too much.**
- Integration tests exercise the shell (real files, real wiring). Mark them so unit tests run alone for fast feedback:

```toml
[tool.pytest.ini_options]
markers = ["integration: tests that hit the filesystem or network"]
```

Run `pytest -m "not integration"` locally; run everything in CI.

- Shared fixtures live in `conftest.py`. **Fixtures share data, not state** -- use `scope="session"` only for immutable values; anything mutable (DataFrames, dicts, lists) stays at function scope.
- Bundle small representative sample files (100-1000 rows) in `tests/data/` for integration tests. Never include real production or patient records.
- Use `hypothesis` when you care about invariants rather than specific values: row counts preserved, outputs bounded, roundtrips lossless.

## Docstrings

Docstrings are not mandatory. A well-named function with typed parameters is often self-documenting, and a docstring that repeats the signature is noise.

Write one for public API functions, non-obvious behaviour (edge cases, side effects, preconditions), and modules whose purpose the filename does not convey. Use short Google-style prose; never `:param:`/`:returns:` blocks, and never repeat type information -- the signature is the source of truth. If removing the docstring would leave a reader confused, keep it; otherwise skip it.

## Project structure

Always use the `src/` layout:

```
my_project/
├── src/my_package/
│   ├── core/          # Functional core (pure transforms)
│   ├── io/            # Imperative shell (readers, writers, clients)
│   ├── resources/     # Bundled non-code files (lookup tables, schemas)
│   ├── cli.py         # Entry point
│   └── config.py      # Configuration dataclass
├── tests/             # conftest.py, unit tests, integration tests
├── pyproject.toml
└── README.md
```

- One repository, one installable package. Distinct tools get separate repositories; shared code becomes a separate library package.
- Entry points go in `[project.scripts]`.
- Bundled runtime files live in `resources/` and are accessed via `importlib.resources.files()`, so they work when the package is installed. User-provided inputs are passed via CLI arguments or config, never bundled.
- Configuration is a dataclass loaded from TOML or JSON at the shell boundary. No global config objects.

## Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | `snake_case.py`, named for contents | `validate.py`, `date_parsing.py` |
| Functions | Verbs describing the action | `validate_claims`, `scan_directory` |
| Classes | Reserved for dataclasses and containers | `SchemaWarning`, `ConversionResult` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_CHUNK_SIZE` |

- **If a class has one public method, it should be a function.** There is no `EnrollmentProcessor`; there is a `process_enrollment` function.
- **No catch-all modules.** Never create `utils.py`, `helpers.py`, or `common.py` -- they attract unrelated code without bound. A function that fits no existing module signals the need for a new, specifically named module.
