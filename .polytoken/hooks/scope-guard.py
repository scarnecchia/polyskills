#!/usr/bin/env python3
"""Polytoken pre_tool_use hook: enforce the session's declared scope roots.

The execute-facet autonomy contract writes a scope declaration before the
first edit of the session. This guard denies file-edit tool calls whose
target falls outside the declared roots (and secret-named files unless the
declaration opts in). It fails open: no declaration, malformed declarations
or events, or a guard error must never block edits.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

HOOK_NAME = "scope-guard"

# Matched against the lowercased basename: intentional widening so real-world
# shapes like PRIVATE.PEM or ID_RSA are also caught on case-sensitive systems.
SECRET_PATTERNS = [
    ".env",
    ".env.*",
    ".envrc",
    "*.pem",
    "id_rsa*",
    "*.key",
    "credentials*",
    ".git-credentials",
    ".netrc",
]


def read_event() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def scope_path() -> Path:
    # `or` (not a default argument) so an exported-empty XDG_STATE_HOME also
    # falls back — matching the writer-side ${XDG_STATE_HOME:-…} idiom.
    state_home = Path(
        os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    )
    scope_dir = state_home / "polytoken" / "hooks" / HOOK_NAME

    session_id = os.environ.get("POLYTOKEN_SESSION_ID")
    if session_id:
        identity = session_id
    else:
        project = os.environ.get("POLYTOKEN_PROJECT_PATH", "unknown-project")
        identity = "project-" + hashlib.sha256(project.encode()).hexdigest()

    safe_identity = re.sub(r"[^A-Za-z0-9._-]", "_", identity)
    return scope_dir / f"{safe_identity}.json"


def read_scope(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def emit(outcome: str, reason: str | None = None) -> None:
    payload: dict[str, Any] = {"outcome": outcome}
    if reason is not None:
        payload["reason"] = reason
    print(json.dumps(payload))


def target_from_event(event: dict[str, Any]) -> str | None:
    tool_input = event.get("input")
    if not isinstance(tool_input, dict):
        return None
    for key in ("path", "file_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def project_root() -> str:
    for key in ("POLYTOKEN_PROJECT_DIR", "POLYTOKEN_PROJECT_PATH"):
        value = os.environ.get(key)
        if value:
            return value
    return os.getcwd()


def resolve_against_project(raw: str) -> str:
    if os.path.isabs(raw):
        return raw
    return os.path.join(project_root(), raw)


def is_within(path: str, root: str) -> bool:
    if root == os.sep:
        return path.startswith(os.sep)
    root = root.rstrip(os.sep)
    return path == root or path.startswith(root + os.sep)


def secret_pattern(name: str) -> str | None:
    lowered = name.lower()
    for pattern in SECRET_PATTERNS:
        if fnmatch.fnmatch(lowered, pattern):
            return pattern
    return None


def run() -> None:
    event = read_event()
    raw_target = target_from_event(event)
    if raw_target is None:
        emit("allow")
        return
    scope_file = scope_path()
    if not scope_file.exists():
        # No declaration: the guard is inert.
        emit("allow")
        return
    scope = read_scope(scope_file)
    if scope is None:
        # Malformed declaration: fail open.
        emit("allow")
        return
    roots_raw = scope.get("roots")
    if not isinstance(roots_raw, list):
        emit("allow")
        return
    # Malformed entries fail open too: a typo'd roots list degrades the
    # guard to inert rather than deny-all.
    roots = [root for root in roots_raw if isinstance(root, str) and root]
    if not roots:
        emit("allow")
        return
    allow_secrets = scope.get("allow_secrets") is True

    target_real = os.path.realpath(resolve_against_project(raw_target))

    if not allow_secrets:
        matched = secret_pattern(os.path.basename(target_real))
        if matched:
            emit(
                "deny",
                f"Target {raw_target} matches secret-file pattern '{matched}'. "
                'Set "allow_secrets": true in the session scope file or confirm '
                "with the operator before touching it.",
            )
            return

    for root in roots:
        root_real = os.path.realpath(resolve_against_project(root))
        if is_within(target_real, root_real):
            emit("allow")
            return

    emit(
        "deny",
        f"Target {raw_target} is outside the declared scope roots. Update the "
        "session scope file or confirm the scope change with the operator.",
    )


def main() -> int:
    try:
        run()
    except Exception:  # noqa: BLE001 - a buggy guard must never block edits
        try:
            emit("allow")
        except Exception:  # noqa: BLE001 - double fault: nothing left to do
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
