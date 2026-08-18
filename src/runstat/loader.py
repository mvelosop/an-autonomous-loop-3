"""Strict loader for a run directory: sessions/*.json and iterations.jsonl.

A malformed file is a hard error, not a silent skip -- undercounting a run's
telemetry silently is worse than refusing loudly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class RunError(Exception):
    """Raised when a run directory is missing or contains malformed input."""


@dataclass(frozen=True)
class Session:
    phase: str
    iteration: int
    total_cost_usd: float
    num_turns: int
    duration_ms: int
    is_error: bool
    permission_denials: list
    path: Path


@dataclass(frozen=True)
class Verdict:
    iteration: int
    task: str
    verdict: str
    criteria: list
    findings: list
    path: Path


@dataclass(frozen=True)
class Run:
    run_id: str
    sessions: list
    iterations: list
    verdicts: list


_VERDICT_REQUIRED_KEYS = ("task", "verdict", "criteria", "findings")


def load_run(path: Path) -> Run:
    path = Path(path)
    if not path.is_dir():
        raise RunError(f"run directory not found: {path}")

    sessions = []
    sessions_dir = path / "sessions"
    if sessions_dir.is_dir():
        for session_path in sorted(sessions_dir.glob("*.json")):
            try:
                data = json.loads(session_path.read_text())
            except json.JSONDecodeError as exc:
                raise RunError(f"malformed session file: {session_path.name}") from exc
            sessions.append(
                Session(
                    phase=data["phase"],
                    iteration=data["iteration"],
                    total_cost_usd=data["total_cost_usd"],
                    num_turns=data["num_turns"],
                    duration_ms=data["duration_ms"],
                    is_error=data["is_error"],
                    permission_denials=data["permission_denials"],
                    path=session_path,
                )
            )

    iterations = []
    iterations_path = path / "iterations.jsonl"
    if iterations_path.is_file():
        for line in iterations_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                iterations.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RunError(
                    f"malformed record in iterations.jsonl: {line!r}"
                ) from exc

    verdicts = []
    reports_dir = path / "reports"
    if reports_dir.is_dir():
        for verdict_path in sorted(reports_dir.glob("*-verdict.json")):
            try:
                data = json.loads(verdict_path.read_text())
            except json.JSONDecodeError as exc:
                raise RunError(f"malformed verdict file: {verdict_path.name}") from exc
            missing = [key for key in _VERDICT_REQUIRED_KEYS if key not in data]
            if missing:
                raise RunError(
                    f"malformed verdict file: {verdict_path.name} (missing {', '.join(missing)})"
                )
            verdicts.append(
                Verdict(
                    iteration=int(verdict_path.name.split("-", 1)[0]),
                    task=data["task"],
                    verdict=data["verdict"],
                    criteria=data["criteria"],
                    findings=data["findings"],
                    path=verdict_path,
                )
            )

    return Run(run_id=path.name, sessions=sessions, iterations=iterations, verdicts=verdicts)
