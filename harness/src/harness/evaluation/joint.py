"""Compare editing on aligned parents that both passed initial correctness.

Usage:
    run_joint_pass(report_directory, "trained", output_directory)
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict

from .analysis import _cells, _family_metrics, interval
from .artifacts import csv_bytes, encoded, publish_bundle, purpose_label, read_comparison
from .records import EvaluationError

METRICS = (
    "change_completion",
    "whole_sequence_success",
    "regression_rate_reached",
    "new_feature_failure_rate_reached",
)
PAIR_FIELDS = (
    "task",
    "family",
    "generation_seed",
    "reference_candidate",
    "method_candidate",
    "reference_initial",
    "method_initial",
    "eligibility",
)
METRIC_FIELDS = (
    "metric",
    "reference_estimate",
    "method_estimate",
    "difference",
    "interval_low",
    "interval_high",
    "paired_families",
    "coverage_complete",
)


def _mean(values):
    return statistics.mean(values) if values else None


def joint_pass(result, method):
    reference = result["reference"]
    if method == reference or method not in result["methods"]:
        raise EvaluationError("Choose a non-reference method present in the report")
    if result.get("size_matched_sensitivity"):
        raise EvaluationError("Start from the primary report, not a size-matched subset")
    indexed = {name: {} for name in (reference, method)}
    for data in result["source_datasets"]:
        if data["method"] in indexed:
            for cell in _cells(data):
                indexed[data["method"]][cell["task"], cell["seed"]] = cell
    if set(indexed[reference]) != set(indexed[method]):
        raise EvaluationError("Joint comparison requires aligned task/seed pairs")

    rows, included = [], {name: [] for name in indexed}
    for key, left in sorted(indexed[reference].items()):
        right = indexed[method][key]
        a, b = left["sample"], right["sample"]
        statuses = a["initial_status"], b["initial_status"]
        # Downstream scores never enter the membership decision.
        eligibility = (
            "included"
            if statuses == ("pass", "pass")
            else "excluded_initial_failure"
            if any(s in {"fail", "parse_failure"} for s in statuses)
            else "unknown_eligibility"
        )
        rows.append(
            dict(
                task=key[0],
                family=left["family"],
                generation_seed=key[1],
                reference_candidate=a["candidate_id"],
                method_candidate=b["candidate_id"],
                reference_initial=statuses[0],
                method_initial=statuses[1],
                eligibility=eligibility,
            )
        )
        if eligibility == "included":
            included[reference].append(left)
            included[method].append(right)
    counts = Counter(row["eligibility"] for row in rows)
    unknown = counts["unknown_eligibility"] > 0
    incomplete = any(
        t["score"] is None for cells in included.values() for c in cells for t in c["trials"]
    )
    status = (
        "incomplete_eligibility"
        if unknown
        else "no_jointly_correct_parents"
        if not counts["included"]
        else "incomplete_outcomes"
        if incomplete
        else "complete"
    )
    families = {}
    for name, cells in included.items():
        grouped = defaultdict(list)
        for cell in cells:
            grouped[cell["family"]].append(cell)
        families[name] = {
            family: _family_metrics(group) for family, group in sorted(grouped.items())
        }
    bootstrap = result["bootstrap"]
    metrics = []
    for metric in METRICS:
        a, b = families[reference], families[method]
        # Unknown membership could change the cohort itself. Missing edits could
        # change its results. Neither earns a primary estimate from the known subset.
        complete = status == "complete"
        paired = [
            k for k in a if a[k][metric]["value"] is not None and b[k][metric]["value"] is not None
        ]
        av = [a[k][metric]["value"] for k in paired]
        bv = [b[k][metric]["value"] for k in paired]
        differences = [b[k][metric]["value"] - a[k][metric]["value"] for k in paired]
        ci = (
            interval(differences, bootstrap["samples"], bootstrap["seed"], bootstrap["confidence"])
            if complete
            else None
        )
        metrics.append(
            dict(
                metric=metric,
                reference_estimate=_mean(av) if complete else None,
                method_estimate=_mean(bv) if complete else None,
                difference=_mean(differences) if complete else None,
                interval_low=ci[0] if ci else None,
                interval_high=ci[1] if ci else None,
                paired_families=len(differences),
                coverage_complete=complete,
            )
        )
    return dict(
        schema_version=1,
        purpose=result["purpose"],
        status=status,
        reference=reference,
        method=method,
        bootstrap=bootstrap,
        parent_pairs=rows,
        metrics=metrics,
        families=families,
        counts=dict(
            planned_pairs=len(rows),
            included_pairs=counts["included"],
            excluded_initial_failure=counts["excluded_initial_failure"],
            unknown_eligibility=counts["unknown_eligibility"],
            included_families=len(families[reference]),
        ),
        roster_verified=bool(result.get("coverage_receipt", {}).get("matches")),
        notes=[
            "Secondary paired analysis: membership uses initial pass/fail only; "
            "the same task/generation-seed cells are retained for both writers.",
            "Initial correctness is one by selection and is not scored as an improvement. "
            "Primary all-generated and individually conditional scores remain unchanged.",
            "Average sequences/repetitions and generation seeds inside task families first. "
            "Intervals resample families; one family has no interval.",
            "Unknown eligibility or editing outcomes block primary cohort estimates. "
            "Reached-step failure rates condition on actually evaluated steps; budgets "
            "and early failure can give the two writers different reached denominators.",
            "This selected cohort does not estimate effects on all generated programs. "
            "Differences are descriptive, not causal or automatic preference labels.",
        ],
    )


def run_joint_pass(directory, method, output):
    result, source_hash = read_comparison(directory)
    summary = joint_pass(result, method)
    summary["source_report_sha256"] = source_hash
    lines = [
        f"# {purpose_label(result)}",
        "",
        "Joint initial-pass comparison",
        "",
        f"Status: {summary['status']}",
        "",
        f"Included {summary['counts']['included_pairs']} of "
        f"{summary['counts']['planned_pairs']} planned parent pairs across "
        f"{summary['counts']['included_families']} families.",
        "",
        *summary["notes"],
        "",
        "| Metric | Reference | Method | Difference | Paired families |",
        "|---|---:|---:|---:|---:|",
    ]

    def display(value):
        return "unavailable" if value is None else f"{value:.1%}"

    for row in summary["metrics"]:
        delta = "unavailable" if row["difference"] is None else f"{100 * row['difference']:+.1f} pp"
        lines.append(
            f"| {row['metric']} | {display(row['reference_estimate'])} | "
            f"{display(row['method_estimate'])} | {delta} | "
            f"{row['paired_families']} |"
        )
    lines += [
        "",
        "Differences are method minus reference, in percentage points. "
        "A negative failure-rate difference means fewer observed failures.",
        "",
        f"Source report SHA256: {source_hash}",
        "",
    ]
    files = {
        "analysis.json": encoded(summary),
        "parent_pairs.csv": csv_bytes(summary["parent_pairs"], PAIR_FIELDS),
        "metrics.csv": csv_bytes(summary["metrics"], METRIC_FIELDS),
        "report.md": "\n".join(lines).encode("utf8"),
    }
    paths = publish_bundle("joint_pass", files, output, source_hash=source_hash)
    return dict(status=summary["status"], counts=summary["counts"], outputs=paths)
