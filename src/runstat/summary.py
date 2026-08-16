"""Per-phase rollup for the `summary` command.

compute_summary aggregates run.sessions into rows so format_summary has
nothing left to derive -- it only renders.
"""

from __future__ import annotations

_PHASE_ORDER = ["plan", "work", "review"]


def _row(phase: str, sessions: list) -> dict:
    return {
        "phase": phase,
        "sessions": len(sessions),
        "cost": sum(s.total_cost_usd for s in sessions),
        "turns": sum(s.num_turns for s in sessions),
        "duration_s": round(sum(s.duration_ms for s in sessions) / 1000),
    }


def compute_summary(run) -> dict:
    by_phase: dict = {}
    for session in run.sessions:
        by_phase.setdefault(session.phase, []).append(session)

    known = [p for p in _PHASE_ORDER if p in by_phase]
    unknown = sorted(p for p in by_phase if p not in _PHASE_ORDER)
    rows = [_row(phase, by_phase[phase]) for phase in known + unknown]

    total = _row("total", run.sessions)

    flagged = [
        s for s in run.sessions if s.is_error or s.permission_denials
    ]

    return {"rows": rows, "total": total, "flagged": flagged}


def format_summary(summary: dict) -> list:
    lines = [
        f"{'phase':<8} {'sessions':>8} {'cost':>10} {'turns':>7} {'wall':>7}"
    ]
    for row in [*summary["rows"], summary["total"]]:
        lines.append(
            f"{row['phase']:<8} {row['sessions']:>8} "
            f"${row['cost']:>8.2f} {row['turns']:>7} {row['duration_s']:>6}s"
        )
    lines.append("")
    lines.append("Dollar figures are an estimate, not a bill.")

    if summary["flagged"]:
        lines.append("")
        lines.append("Flagged sessions:")
        for session in summary["flagged"]:
            reasons = []
            if session.is_error:
                reasons.append("is_error")
            if session.permission_denials:
                reasons.append(f"{len(session.permission_denials)} permission denial(s)")
            lines.append(f"  {session.path.name}: {', '.join(reasons)}")

    return lines
