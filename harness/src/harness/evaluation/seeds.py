"""Summarize observed training checkpoints without treating them as independent tasks.

Usage:
    run_seed_summary(report_directory, output_directory)
"""

from __future__ import annotations

import statistics
from collections import defaultdict

from .analysis import METRICS, interval
from .artifacts import csv_bytes, encoded, publish_bundle, purpose_label, read_comparison
from .records import EvaluationError


def _mean(values):
    return statistics.mean(values) if values else None


def summarize_seeds(result):
    grouped = defaultdict(list)
    for name, row in result["methods"].items():
        grouped[row.get("method_group") or name].append(name)
    bootstrap = result["bootstrap"]
    groups, seeds = {}, []
    for group, members in sorted(grouped.items()):
        members = sorted(members)
        rows = [result["methods"][name] for name in members]
        if len(members) > 1:
            labels = [r.get("training_seed") for r in rows]
            identities = [r.get("writer_identity") for r in rows]
            if None in labels or len(set(labels)) != len(labels):
                raise EvaluationError(f"{group}: distinct declared training seeds are required")
            if None in identities or len(set(identities)) != len(identities):
                raise EvaluationError(f"{group}: distinct saved writer identities are required")
        families = {}
        for family in rows[0]["families"]:
            families[family] = {}
            for metric in METRICS:
                cells = [row["families"][family][metric] for row in rows]
                # Keep the same observed checkpoints for each included family.
                # An inapplicable seed is not silently replaced by a more favorable one.
                values = [c["value"] for c in cells]
                families[family][metric] = dict(
                    value=None if None in values else _mean(values),
                    unresolved=any(c["unresolved"] for c in cells),
                )
        metrics = {}
        for metric in METRICS:
            values = [
                f[metric]["value"] for f in families.values() if f[metric]["value"] is not None
            ]
            unknown = any(f[metric]["unresolved"] for f in families.values())
            estimates = [r["metrics"][metric]["estimate"] for r in rows]
            known = [v for v in estimates if v is not None]
            metrics[metric] = dict(
                estimate=None if unknown else _mean(values),
                interval=None
                if unknown
                else interval(
                    values, bootstrap["samples"], bootstrap["seed"], bootstrap["confidence"]
                ),
                contributing_families=len(values),
                planned_families=len(families),
                coverage_complete=not unknown,
                observed_checkpoints=len(members),
                unknown_checkpoint_estimates=len(estimates) - len(known),
                checkpoint_min=min(known) if known else None,
                checkpoint_max=max(known) if known else None,
            )
        groups[group] = dict(members=members, families=families, metrics=metrics)
        for name, row in zip(members, rows, strict=True):
            for metric in METRICS:
                m = row["metrics"][metric]
                seeds.append(
                    dict(
                        group=group,
                        method=name,
                        training_seed=row.get("training_seed"),
                        metric=metric,
                        estimate=m["estimate"],
                        interval_low=None if m["interval"] is None else m["interval"][0],
                        interval_high=None if m["interval"] is None else m["interval"][1],
                        contributing_families=m["contributing_families"],
                        coverage_complete=m["coverage_complete"],
                    )
                )
    reference = result["methods"][result["reference"]].get("method_group") or result["reference"]
    pairs = []
    for group, row in groups.items():
        if group == reference:
            continue
        for metric in METRICS:
            a, b = row["families"], groups[reference]["families"]
            unresolved = any(a[k][metric]["unresolved"] or b[k][metric]["unresolved"] for k in a)
            values = [
                a[k][metric]["value"] - b[k][metric]["value"]
                for k in a
                if a[k][metric]["value"] is not None and b[k][metric]["value"] is not None
            ]
            ci = (
                None
                if unresolved
                else interval(
                    values, bootstrap["samples"], bootstrap["seed"], bootstrap["confidence"]
                )
            )
            pairs.append(
                dict(
                    group=group,
                    reference=reference,
                    metric=metric,
                    difference=None if unresolved else _mean(values),
                    interval_low=None if ci is None else ci[0],
                    interval_high=None if ci is None else ci[1],
                    paired_families=len(values),
                    coverage_complete=not unresolved,
                )
            )
        baseline = groups[reference]["metrics"]["change_completion"]["estimate"]
        directions = dict(advantage=0, tie=0, disadvantage=0, unknown=0)
        for name in row["members"]:
            value = result["methods"][name]["metrics"]["change_completion"]["estimate"]
            label = (
                "unknown"
                if value is None or baseline is None
                else "advantage"
                if value > baseline
                else "disadvantage"
                if value < baseline
                else "tie"
            )
            directions[label] += 1
        row["completion_directions_vs_reference_group"] = directions
    return dict(
        schema_version=1,
        purpose=result["purpose"],
        reference_group=reference,
        bootstrap={**bootstrap, "conditioned_on_observed_checkpoints": True},
        groups=groups,
        seeds=seeds,
        comparisons=pairs,
        note="Task-family uncertainty with the observed checkpoint set fixed; not uncertainty "
        "over future training seeds. Conditional metrics use common applicable families. "
        "Checkpoint identities are declared provenance, not authenticated weight digests.",
    )


def run_seed_summary(directory, output):
    result, source_hash = read_comparison(directory)
    summary = summarize_seeds(result)
    summary["source_report_sha256"] = source_hash
    group_rows = []
    for name, row in summary["groups"].items():
        for metric, values in row["metrics"].items():
            values = dict(values)
            ci = values.pop("interval")
            group_rows.append(
                dict(
                    group=name,
                    metric=metric,
                    **values,
                    interval_low=None if ci is None else ci[0],
                    interval_high=None if ci is None else ci[1],
                )
            )
    lines = [
        f"# {purpose_label(result)}",
        "",
        "Observed training-checkpoint summary",
        "",
        summary["note"],
        "",
        "| Group | Checkpoints | Completion | Per-checkpoint range |",
        "|---|---:|---:|---|",
    ]
    for name, row in summary["groups"].items():
        m = row["metrics"]["change_completion"]
        value = "unavailable" if m["estimate"] is None else f"{m['estimate']:.1%}"
        limits = (
            "unavailable"
            if m["checkpoint_min"] is None
            else (f"{m['checkpoint_min']:.1%} to {m['checkpoint_max']:.1%}")
        )
        lines.append(f"| {name} | {len(row['members'])} | {value} | {limits} |")
    lines += [
        "",
        "Every checkpoint, including adverse and unresolved seeds, is retained in seeds.csv.",
        "Directions count checkpoint estimates against the same reference-group mean; "
        "they are not independent tests or automatically usable training labels.",
        "",
    ]
    files = {
        "analysis.json": encoded(summary),
        "seeds.csv": csv_bytes(summary["seeds"], list(summary["seeds"][0])),
        "groups.csv": csv_bytes(group_rows, list(group_rows[0])),
        "comparisons.csv": csv_bytes(
            summary["comparisons"],
            [
                "group",
                "reference",
                "metric",
                "difference",
                "interval_low",
                "interval_high",
                "paired_families",
                "coverage_complete",
            ],
        ),
        "report.md": "\n".join(lines).encode("utf8"),
    }
    return publish_bundle("seed_summary", files, output, source_hash=source_hash)
