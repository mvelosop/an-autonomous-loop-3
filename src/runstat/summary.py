"""The ``runstat summary`` command: a per-phase rollup of a run's telemetry."""

PHASE_ORDER = ["plan", "work", "review"]


def compute_rollup(sessions):
    """Group sessions by phase, summing session count, cost, turns and wall time."""
    rows = {}
    for session in sessions:
        row = rows.setdefault(
            session["phase"], {"sessions": 0, "cost": 0.0, "turns": 0, "wall_ms": 0}
        )
        row["sessions"] += 1
        row["cost"] += session["total_cost_usd"]
        row["turns"] += session["num_turns"]
        row["wall_ms"] += session["duration_ms"]
    return rows


def _format_row(label, row):
    wall_s = round(row["wall_ms"] / 1000)
    return f"{label:<8}{row['sessions']:>3}  ${row['cost']:.2f}  {row['turns']:>4}  {wall_s}s"


def _format_call_outs(sessions):
    """Name sessions that reported an error or a permission denial."""
    lines = []
    for session in sessions:
        if session.get("is_error"):
            lines.append(f"error: {session['file']} reported is_error")
    for session in sessions:
        denials = session.get("permission_denials")
        if denials:
            lines.append(
                f"permission denials: {session['file']} — {', '.join(denials)}"
            )
    return lines


def format_summary(sessions):
    """Render the per-phase rollup plus a total row, as the brief's table."""
    rows = compute_rollup(sessions)
    phases = [phase for phase in PHASE_ORDER if phase in rows]
    phases += [phase for phase in rows if phase not in PHASE_ORDER]

    lines = []
    total = {"sessions": 0, "cost": 0.0, "turns": 0, "wall_ms": 0}
    for phase in phases:
        row = rows[phase]
        lines.append(_format_row(phase, row))
        total["sessions"] += row["sessions"]
        total["cost"] += row["cost"]
        total["turns"] += row["turns"]
        total["wall_ms"] += row["wall_ms"]
    lines.append(_format_row("total", total))
    lines.append("")
    lines.append("Dollar figures are an estimate, not a bill.")

    call_outs = _format_call_outs(sessions)
    if call_outs:
        lines.append("")
        lines.extend(call_outs)
    return "\n".join(lines)
