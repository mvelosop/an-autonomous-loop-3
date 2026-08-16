"""Side-by-side comparison of two runs' signals, for the `compare` command.

compute_compare reuses compute_signals for both runs rather than defining its
own derivations, then pairs each of the eight signals with a delta (run B
minus run A). Only signals whose display is a single number get a delta;
"tasks closed" is a pair (2/8) and subtracting it would be meaningless.
"""

from __future__ import annotations

from .signals import compute_signals


def _ratio_display(value) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _signed_int(delta: int) -> str:
    return f"{delta:+d}"


def _signed_ratio(delta: float) -> str:
    return f"{delta:+.2f}"


def _signed_money(delta: float) -> str:
    sign = "+" if delta >= 0 else "-"
    return f"{sign}${abs(delta):.2f}"


def compute_compare(run_a, run_b) -> dict:
    a = compute_signals(run_a)
    b = compute_signals(run_b)

    pc_a, pc_b = a["iterations_per_closed"], b["iterations_per_closed"]
    pc_delta = "" if pc_a is None or pc_b is None else _signed_ratio(pc_b - pc_a)

    rows = [
        (
            "iterations",
            str(a["iterations"]),
            str(b["iterations"]),
            _signed_int(b["iterations"] - a["iterations"]),
        ),
        (
            "tasks closed",
            f"{a['tasks_done']}/{a['tasks_total']}",
            f"{b['tasks_done']}/{b['tasks_total']}",
            "",
        ),
        ("iterations per closed", _ratio_display(pc_a), _ratio_display(pc_b), pc_delta),
        (
            "gate failures",
            str(a["gate_failures"]),
            str(b["gate_failures"]),
            _signed_int(b["gate_failures"] - a["gate_failures"]),
        ),
        (
            "review rejections",
            str(a["review_rejections"]),
            str(b["review_rejections"]),
            _signed_int(b["review_rejections"] - a["review_rejections"]),
        ),
        (
            "attempts burned",
            str(a["attempts_burned"]),
            str(b["attempts_burned"]),
            _signed_int(b["attempts_burned"] - a["attempts_burned"]),
        ),
        (
            "no-progress streak",
            str(a["no_progress_streak"]),
            str(b["no_progress_streak"]),
            _signed_int(b["no_progress_streak"] - a["no_progress_streak"]),
        ),
        (
            "estimated spend",
            f"${a['estimated_spend']:.2f}",
            f"${b['estimated_spend']:.2f}",
            _signed_money(b["estimated_spend"] - a["estimated_spend"]),
        ),
    ]

    return {"rows": rows}


def format_compare(compare: dict) -> list:
    lines = [f"{'signal':<22} {'run a':>10} {'run b':>10} {'delta':>10}"]
    for label, a_disp, b_disp, delta_disp in compare["rows"]:
        lines.append(f"{label:<22} {a_disp:>10} {b_disp:>10} {delta_disp:>10}")
    lines.append("")
    lines.append("Dollar figures are an estimate, not a bill.")
    return lines
