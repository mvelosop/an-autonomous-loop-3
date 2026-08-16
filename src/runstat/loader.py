"""Loading of session telemetry from a run directory.

Shared by every command: each reads the same ``sessions/*.json`` layout
described in docs/briefs/0003-runstat-cli.md.
"""

import json
from pathlib import Path


class RunDirNotFound(Exception):
    """The given run directory does not exist. Exit code 2."""

    def __init__(self, run_dir):
        self.run_dir = run_dir
        super().__init__(f"no such run directory: {run_dir}")


class MalformedInput(Exception):
    """A session file or iterations.jsonl line could not be parsed. Exit code 2."""

    def __init__(self, path):
        self.path = path
        super().__init__(f"malformed input: {path}")


class NoSessions(Exception):
    """The run directory exists but holds no session files. Exit code 1."""

    def __init__(self, run_dir):
        self.run_dir = run_dir
        super().__init__(f"run directory has no sessions: {run_dir}")


def _require_run_dir(run_dir):
    if not Path(run_dir).is_dir():
        raise RunDirNotFound(run_dir)


def load_sessions(run_dir):
    """Return one dict per session file under ``<run_dir>/sessions/``.

    Files are read in name-sortable order, per the brief's input format.
    """
    _require_run_dir(run_dir)
    sessions_dir = Path(run_dir) / "sessions"
    sessions = []
    for path in sorted(sessions_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise MalformedInput(str(path)) from exc
        sessions.append(
            {
                "file": path.name,
                "phase": data["phase"],
                "iteration": data.get("iteration"),
                "total_cost_usd": data.get("total_cost_usd", 0.0),
                "num_turns": data.get("num_turns", 0),
                "duration_ms": data.get("duration_ms", 0),
                "is_error": data.get("is_error", False),
                "permission_denials": data.get("permission_denials", []),
            }
        )
    if not sessions:
        raise NoSessions(run_dir)
    return sessions


def load_iterations(run_dir):
    """Return one dict per line of ``<run_dir>/iterations.jsonl``, in file order."""
    _require_run_dir(run_dir)
    path = Path(run_dir) / "iterations.jsonl"
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise MalformedInput(str(path)) from exc
    return records
