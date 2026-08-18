"""Per-iteration table, totals, findings and coherence for the `review` command.

compute_review aggregates run.verdicts (and run.iterations, for the coherence
checks) into rows, totals and violations so format_review has nothing left to
derive -- it only renders.
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
        "finding_texts": list(verdict.findings),
        "evidence": evidence,
    }


def _task_by_iteration(run) -> dict:
    tasks = {}
    for record in run.iterations:
        iteration = record.get("iteration")
        if iteration is not None:
            tasks[iteration] = record.get("task")
    return tasks


def _violations(run) -> list:
    expected_task = _task_by_iteration(run)
    violations = []
    for v in run.verdicts:
        not_met = [c for c in v.criteria if not c["met"]]
        if v.verdict == "PASS" and not_met:
            violations.append((1, v.iteration, v.task))
        if v.verdict == "PASS" and v.findings:
            violations.append((2, v.iteration, v.task))
        if v.verdict == "FAIL" and not not_met and not v.findings:
            violations.append((3, v.iteration, v.task))
        if any(not str(c["evidence"]).strip() for c in v.criteria):
            violations.append((4, v.iteration, v.task))
        want = expected_task.get(v.iteration)
        if want is not None and want != v.task:
            violations.append((5, v.iteration, v.task, want))
    return violations


def compute_review(run) -> dict:
    rows = [_row(v) for v in run.verdicts]

    criteria_ruled = sum(r["criteria"] for r in rows)
    violations = _violations(run)

    totals = {
        "reviews": len(rows),
        "passed": sum(1 for r in rows if r["verdict"] == "PASS"),
        "failed": sum(1 for r in rows if r["verdict"] == "FAIL"),
        "criteria_ruled": criteria_ruled,
        "criteria_not_met": sum(r["not_met"] for r in rows),
        "findings": sum(r["findings"] for r in rows),
        "evidence_cited": sum(r["evidence"] for r in rows),
        "evidence_total": criteria_ruled,
        "coherence": "ok" if not violations else f"{len(violations)} violation(s)",
    }

    return {"rows": rows, "totals": totals, "violations": violations}


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
    lines.append(f"coherence: {totals['coherence']}")

    lines.append("")
    if totals["findings"] == 0:
        lines.append("no findings recorded")
    else:
        for row in review["rows"]:
            if not row["finding_texts"]:
                continue
            lines.append(f"iteration {row['iteration']} ({row['task']}):")
            for text in row["finding_texts"]:
                lines.append(f"  {text}")

    lines.append("")
    violations = review["violations"]
    if not violations:
        lines.append("coherence checks: no violations")
    else:
        for violation in violations:
            if len(violation) == 4:
                check, iteration, task, want = violation
                lines.append(
                    f"check {check}: iteration {iteration} task {task} "
                    f"(iterations.jsonl names {want})"
                )
            else:
                check, iteration, task = violation
                lines.append(f"check {check}: iteration {iteration} task {task}")

    return lines
