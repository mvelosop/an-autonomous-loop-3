"""Loading of session telemetry from a run directory.

Shared by every command: each reads the same ``sessions/*.json`` layout
described in docs/briefs/0003-runstat-cli.md.
"""

import json
from pathlib import Path


def load_sessions(run_dir):
    """Return one dict per session file under ``<run_dir>/sessions/``.

    Files are read in name-sortable order, per the brief's input format.
    """
    sessions_dir = Path(run_dir) / "sessions"
    sessions = []
    for path in sorted(sessions_dir.glob("*.json")):
        data = json.loads(path.read_text())
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
    return sessions
