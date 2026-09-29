#!/usr/bin/env python3
"""Polytoken stop hook: mechanical completion proof for the delivery loop.

The delivery-loop skill writes a marker file when delivery starts. While
unpushed commits remain and the nudge budget is not exhausted, this hook
emits a `continue` outcome so the model finishes push + verify instead of
handing back early. The marker is the sole opt-in gate: sessions that never
ran the delivery loop have no marker and are never nudged.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback: unserialized nudges
    fcntl = None

HOOK_NAME = "completion-proof"
DEFAULT_BUDGET = 3
GIT_TIMEOUT_SECONDS = 5


def read_event() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def marker_path() -> Path:
    # `or` (not a default argument) so an exported-empty XDG_STATE_HOME also
    # falls back — matching the writer-side ${XDG_STATE_HOME:-…} idiom.
    state_home = Path(
        os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    )
    marker_dir = state_home / "polytoken" / "hooks" / HOOK_NAME

    session_id = os.environ.get("POLYTOKEN_SESSION_ID")
    if session_id:
        identity = session_id
    else:
        project = os.environ.get("POLYTOKEN_PROJECT_PATH", "unknown-project")
        identity = "project-" + hashlib.sha256(project.encode()).hexdigest()

    safe_identity = re.sub(r"[^A-Za-z0-9._-]", "_", identity)
    return marker_dir / f"{safe_identity}.json"


def read_marker(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _read_fd(fd: int) -> str:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8", "replace")


def record_nudge(path: Path, budget: int) -> int | None:
    """Consume one nudge from the marker, serialized by an exclusive lock.

    Re-reads the marker while holding the lock so concurrent stop events
    cannot lose increments (last-writer-wins), and re-checks the budget
    under the lock so a racing wave cannot exceed it. Returns the new
    nudges count, or None when the budget is exhausted or the marker
    became unreadable — either way the caller must stop.
    """
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    try:
        fd = os.open(path, os.O_RDWR)
    except FileNotFoundError:
        # The marker vanished between the opt-in check and now (a concurrent
        # stop event cleared it, or the skill did): do not resurrect it.
        return None
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        raw = _read_fd(fd)
        try:
            marker = json.loads(raw) if raw.strip() else {}
        except ValueError:
            return None
        if not isinstance(marker, dict):
            return None
        try:
            nudges = int(marker.get("nudges", 0))
        except (TypeError, ValueError):
            nudges = 0
        if nudges >= budget:
            return None
        marker["nudges"] = nudges + 1
        payload = json.dumps(marker).encode("utf-8")
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, payload)
        os.ftruncate(fd, len(payload))
        return nudges + 1
    finally:
        if fcntl is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(fd)


def resolve_repo(event: dict[str, Any]) -> str:
    cwd = event.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    for key in ("POLYTOKEN_PROJECT_DIR", "POLYTOKEN_PROJECT_PATH"):
        value = os.environ.get(key)
        if value:
            return value
    return os.getcwd()


def git(repo: str, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def inside_work_tree(repo: str) -> bool:
    return git(repo, "rev-parse", "--is-inside-work-tree") == "true"


def unpushed_count(repo: str) -> int:
    """Count commits on HEAD missing from upstream.

    A missing upstream (never pushed) or any git failure counts as
    unpushed > 0: the delivery has not been verified.
    """
    upstream = git(
        repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"
    )
    if upstream is None:
        return 1
    count = git(repo, "rev-list", "--count", f"{upstream}..HEAD")
    if count is None or not count.isdigit():
        return 1
    return int(count)


def emit(outcome: str, reason: str | None = None) -> None:
    payload: dict[str, Any] = {"outcome": outcome}
    if reason is not None:
        payload["reason"] = reason
    print(json.dumps(payload))


def run() -> None:
    event = read_event()
    marker_file = marker_path()
    if not marker_file.exists():
        emit("stop")
        return
    marker = read_marker(marker_file)
    if marker is None:
        # Corrupt marker: leave the file for the skill to clean up, never loop.
        emit("stop")
        return
    if marker.get("paused") is True:
        # Intentional operator handback: no budget consumed, marker kept.
        emit("stop")
        return
    repo = resolve_repo(event)
    if not inside_work_tree(repo):
        emit("stop")
        return
    unpushed = unpushed_count(repo)
    if unpushed == 0:
        try:
            marker_file.unlink()
        except OSError:
            pass
        emit("stop")
        return
    try:
        budget = int(marker.get("budget", DEFAULT_BUDGET))
    except (TypeError, ValueError):
        budget = DEFAULT_BUDGET
    # The authoritative budget check + increment happens under the lock.
    new_nudges = record_nudge(marker_file, budget)
    if new_nudges is None:
        # Budget exhausted (including a racing wave) or marker unreadable:
        # never trap the loop.
        emit("stop")
        return
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD") or "unknown branch"
    emit(
        "continue",
        f"Completion proof pending: {unpushed} unpushed commit(s) on {branch}. "
        "Push and verify the remote head, or clear the delivery marker if "
        "delivery is not actually in progress.",
    )


def main() -> int:
    try:
        run()
    except Exception:  # noqa: BLE001 - the loop must never hang on a buggy hook
        try:
            emit("stop")
        except Exception:  # noqa: BLE001 - double fault: nothing left to do
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
