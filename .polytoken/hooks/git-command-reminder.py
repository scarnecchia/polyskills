#!/usr/bin/env python3
"""Polytoken hook that reminds agents to maintain AGENTS.md before committing."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

GIT_COMMAND = re.compile(r"^git\s+(status|log(?!\s+--oneline\s+-\d+$))")
JJ_STATUS = re.compile(r"^jj\s+status(?:\s|$)")
JJ_LOG = re.compile(r"^jj\s+log(?:\s|$)")
JJ_QUICK_LOG = re.compile(r"^jj\s+log\s+(?:-n\s+\d+|--limit\s+\d+)\s*$")
REMINDER = (
    "Reminder: If you're about to commit changes that affect contracts, "
    "APIs, or domain structure, consider invoking `maintaining-project-context` "
    "to review and update `AGENTS.md` files before committing."
)


def read_event() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def marker_path() -> Path:
    state_home = Path(
        os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    )
    marker_dir = state_home / "polytoken" / "hooks" / "claudemd-reminder"

    session_id = os.environ.get("POLYTOKEN_SESSION_ID")
    if session_id:
        identity = session_id
    else:
        project = os.environ.get("POLYTOKEN_PROJECT_PATH", "unknown-project")
        identity = "project-" + hashlib.sha256(project.encode()).hexdigest()

    safe_identity = re.sub(r"[^A-Za-z0-9._-]", "_", identity)
    return marker_dir / f"{safe_identity}.pending"


def should_remind(command: str) -> bool:
    if GIT_COMMAND.match(command):
        return True
    if JJ_STATUS.match(command):
        return True
    return bool(JJ_LOG.match(command) and not JJ_QUICK_LOG.match(command))


def detect() -> int:
    event = read_event()
    if event.get("tool_name") != "shell_exec":
        return 0

    tool_input = event.get("input", {})
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not should_remind(command):
        return 0

    marker = marker_path()
    marker.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    marker.parent.chmod(0o700)
    descriptor = os.open(marker, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    os.close(descriptor)
    return 0


def inject() -> int:
    read_event()
    marker = marker_path()
    try:
        marker.unlink()
    except FileNotFoundError:
        print(json.dumps({"outcome": "proceed"}))
        return 0

    print(json.dumps({"outcome": "proceed", "additional_context": REMINDER}))
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"detect", "inject"}:
        print("usage: git-command-reminder.py detect|inject", file=sys.stderr)
        return 2
    return detect() if sys.argv[1] == "detect" else inject()


if __name__ == "__main__":
    raise SystemExit(main())
