"""The eight run-level signals from brief 0002 section 7.

compute_signals returns numbers (ints, floats, None) so that a command like
compare can do arithmetic on them directly. format_signals turns those numbers
into the (label, display) pairs every command prints, so the display form is
defined exactly once.
"""

from __future__ import annotations


def compute_signals(run) -> dict:
    iterations = len(run.iterations)

    if run.iterations:
        last = run.iterations[-1]
        tasks_done = last["tasks_done"]
        tasks_total = last["tasks_total"]
    else:
        tasks_done = 0
        tasks_total = 0

    iterations_per_closed = (iterations / tasks_done) if tasks_done else None

    gate_failures = sum(1 for rec in run.iterations if rec["outcome"] == "gate_fail")
    review_rejections = sum(1 for rec in run.iterations if rec["outcome"] == "review_fail")
    attempts_burned = sum(1 for rec in run.iterations if rec["outcome"] != "done")

    no_progress_streak = 0
    prev_tasks_done = 0
    increased_flags = []
    for rec in run.iterations:
        increased_flags.append(rec["tasks_done"] > prev_tasks_done)
        prev_tasks_done = rec["tasks_done"]
    for increased in reversed(increased_flags):
        if increased:
            break
        no_progress_streak += 1

    estimated_spend = sum(s.total_cost_usd for s in run.sessions)

    return {
        "iterations": iterations,
        "tasks_done": tasks_done,
        "tasks_total": tasks_total,
        "iterations_per_closed": iterations_per_closed,
        "gate_failures": gate_failures,
        "review_rejections": review_rejections,
        "attempts_burned": attempts_burned,
        "no_progress_streak": no_progress_streak,
        "estimated_spend": estimated_spend,
    }


def format_signals(signals: dict) -> list:
    per_closed = signals["iterations_per_closed"]
    per_closed_display = "n/a" if per_closed is None else f"{per_closed:.2f}"

    return [
        ("iterations", str(signals["iterations"])),
        ("tasks closed", f"{signals['tasks_done']}/{signals['tasks_total']}"),
        ("iterations per closed", per_closed_display),
        ("gate failures", str(signals["gate_failures"])),
        ("review rejections", str(signals["review_rejections"])),
        ("attempts burned", str(signals["attempts_burned"])),
        ("no-progress streak", str(signals["no_progress_streak"])),
        ("estimated spend", f"${signals['estimated_spend']:.2f}"),
    ]
