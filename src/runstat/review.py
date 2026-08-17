"""Per-iteration table and totals for the `review` command.

compute_review aggregates run.verdicts into rows and totals so format_review
has nothing left to derive -- it only renders. The findings section (brief
0004 task T4) and the coherence checks (task T5) build on this module later.
"""

from __future__ import annotations


def _row(verdict) -> dict:
    not_met = sum(1 for c in verdict.criteria if not c["met"])
    evidence = sum(1 for c in verdict.criteria if str(c["evidence"]).strip())
    return {
        "iteration": verdict.iteration,
        "task": verdict.task,
        "verdict": verdict.verdict,
        "criteria": len(verdict.criteria),
        "not_met": not_met,
        "findings": len(verdict.findings),
        "evidence": evidence,
    }


def compute_review(run) -> dict:
    rows = [_row(v) for v in run.verdicts]

    criteria_ruled = sum(r["criteria"] for r in rows)

    totals = {
        "reviews": len(rows),
        "passed": sum(1 for r in rows if r["verdict"] == "PASS"),
        "failed": sum(1 for r in rows if r["verdict"] == "FAIL"),
        "criteria_ruled": criteria_ruled,
        "criteria_not_met": sum(r["not_met"] for r in rows),
        "findings": sum(r["findings"] for r in rows),
        "evidence_cited": sum(r["evidence"] for r in rows),
        "evidence_total": criteria_ruled,
    }

    return {"rows": rows, "totals": totals}


def format_review(review: dict) -> list:
    lines = [
        f"{'iteration':>9} {'task':<6} {'verdict':<7} "
        f"{'criteria':>8} {'not met':>7} {'findings':>8} {'evidence':>8}"
    ]
    for row in review["rows"]:
        evidence_display = f"{row['evidence']}/{row['criteria']}"
        lines.append(
            f"{row['iteration']:>9} {row['task']:<6} {row['verdict']:<7} "
            f"{row['criteria']:>8} {row['not_met']:>7} {row['findings']:>8} "
            f"{evidence_display:>8}"
        )

    totals = review["totals"]
    lines.append("")
    lines.append(f"reviews: {totals['reviews']}")
    lines.append(f"passed: {totals['passed']}")
    lines.append(f"failed: {totals['failed']}")
    lines.append(f"criteria ruled: {totals['criteria_ruled']}")
    lines.append(f"criteria not met: {totals['criteria_not_met']}")
    lines.append(f"findings: {totals['findings']}")
    lines.append(f"evidence cited: {totals['evidence_cited']}/{totals['evidence_total']}")

    return lines
