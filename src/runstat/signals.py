"""The ``runstat signals`` command: the eight run-level signals from brief 0002.

Derivations must match the loop driver's inline computation exactly (brief
0002 acceptance item 6), so this module is the single source of truth that
``compare`` (T6) also reuses.
"""


def compute_signals(sessions, iterations):
    """Return the eight signals as raw values, keyed by their brief-defined labels.

    Values are left unformatted (ints, floats, ``None`` for n/a, or an
    already-composed "x/y" string for tasks closed) so callers can both render
    them for display and use them numerically for a delta.
    """
    n_iterations = len(iterations)
    if iterations:
        last = iterations[-1]
        tasks_done = last["tasks_done"]
        tasks_total = last["tasks_total"]
    else:
        tasks_done = 0
        tasks_total = 0

    gate_failures = sum(1 for record in iterations if record["outcome"] == "gate_fail")
    review_rejections = sum(1 for record in iterations if record["outcome"] == "review_fail")
    attempts_burned = sum(1 for record in iterations if record["outcome"] != "done")

    iterations_per_closed = round(n_iterations / tasks_done, 2) if tasks_done else None

    estimated_spend = sum(session["total_cost_usd"] for session in sessions)

    return {
        "iterations": n_iterations,
        "tasks closed": f"{tasks_done}/{tasks_total}",
        "iterations per closed": iterations_per_closed,
        "gate failures": gate_failures,
        "review rejections": review_rejections,
        "attempts burned": attempts_burned,
        "no-progress streak": _trailing_no_progress_streak(iterations),
        "estimated spend": estimated_spend,
    }


def _trailing_no_progress_streak(iterations):
    """Count trailing records whose ``tasks_done`` did not increase over the previous one.

    The record before the first one is treated as a baseline of 0, so a first
    record with any progress breaks the streak rather than starting it.
    """
    streak = 0
    for i in range(len(iterations) - 1, -1, -1):
        current = iterations[i]["tasks_done"]
        baseline = iterations[i - 1]["tasks_done"] if i > 0 else 0
        if current > baseline:
            break
        streak += 1
    return streak


def format_value(label, value):
    """Render one signal's raw value the way ``signals`` and ``compare`` print it."""
    if label == "iterations per closed":
        return "n/a" if value is None else f"{value:.2f}"
    if label == "estimated spend":
        return f"${value:.2f}"
    if label == "tasks closed":
        return value
    return str(value)


def format_signals(signals):
    """Render the eight signals as ``label: value`` lines, in brief-defined order."""
    return "\n".join(f"{label}: {format_value(label, value)}" for label, value in signals.items())
