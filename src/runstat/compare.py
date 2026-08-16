"""The ``runstat compare`` command: two runs' signals side by side, with a delta column."""

from runstat.signals import compute_signals, format_value


def _numeric_delta(label, value_a, value_b):
    """Return run B's value minus run A's for a signal with a comparable delta, else ``None``."""
    if label == "tasks closed":
        return None
    if isinstance(value_a, str) or isinstance(value_b, str):
        return None
    if value_a is None or value_b is None:
        return None
    delta = value_b - value_a
    return round(delta, 2) if isinstance(delta, float) else delta


def _format_delta(label, delta):
    """Render a delta at the same precision as the signal, with an explicit ``+`` when positive."""
    if delta is None:
        return ""
    if label == "iterations per closed":
        return f"{delta:+.2f}"
    if label == "estimated spend":
        sign = "-" if delta < 0 else "+" if delta > 0 else ""
        return f"{sign}${abs(delta):.2f}"
    if delta > 0:
        return f"+{delta}"
    if delta < 0:
        return f"{delta}"
    return "0"


def compute_comparison(sessions_a, iterations_a, sessions_b, iterations_b):
    """Return every ``signals`` label mapped to ``(value_a, value_b, delta)``."""
    signals_a = compute_signals(sessions_a, iterations_a)
    signals_b = compute_signals(sessions_b, iterations_b)
    rows = {}
    for label, value_a in signals_a.items():
        value_b = signals_b[label]
        rows[label] = (value_a, value_b, _numeric_delta(label, value_a, value_b))
    return rows


def format_comparison(rows):
    """Render the comparison table: label, run A's value, run B's value, delta."""
    lines = [f"{'signal':<22}{'run A':>10}{'run B':>10}  delta"]
    for label, (value_a, value_b, delta) in rows.items():
        a_text = format_value(label, value_a)
        b_text = format_value(label, value_b)
        delta_text = _format_delta(label, delta)
        lines.append(f"{label:<22}{a_text:>10}{b_text:>10}  {delta_text}")
    return "\n".join(lines)
