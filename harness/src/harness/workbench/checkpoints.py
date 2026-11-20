"""Compare observed collection checkpoints with the existing seed-summary engine.

Usage: run_summary(report, output, population="common-selected", expected_seeds={})
An expected roster is a coverage declaration, not evidence of preregistration.
"""

from __future__ import annotations

from collections import defaultdict

from ..evaluation.artifacts import purpose_label
from ..evaluation.records import EvaluationError, identifier, integer, read_json
from ..evaluation.seeds import summarize_seeds
from .analysis import METRICS, _estimate, _family_values
from .derived import publish, read_primary
from .presentation import document, render_report_text
from .report import display, encoded, table_csv


def options(population="common-selected", expected_seeds=None):
    if population not in ("common-selected", "all-planned"):
        raise EvaluationError("Unknown checkpoint-summary population")
    expected_seeds = {} if expected_seeds is None else expected_seeds
    if not isinstance(expected_seeds, dict):
        raise EvaluationError("Expected seeds must map groups to seed lists")
    normalized = {}
    for group, values in expected_seeds.items():
        identifier(group, "checkpoint group")
        if not isinstance(values, list) or not values:
            raise EvaluationError("Each expected checkpoint group needs a nonempty seed list")
        for value in values:
            integer(value, "expected training seed")
        if len(set(values)) != len(values):
            raise EvaluationError("Duplicate expected training seed")
        normalized[group] = sorted(values)
    return {"population": population, "expected_seeds": dict(sorted(normalized.items()))}


def summarize(source, settings):
    if not isinstance(settings, dict) or set(settings) != {"population", "expected_seeds"}:
        raise EvaluationError("Invalid checkpoint-summary options")
    settings = options(**settings)
    analysis = source["analysis"]
    members = {}
    selected_tasks = set(source["common_selected_tasks"])
    for data in source["source_datasets"]:
        rows = source["task_summaries"][data["method"]]
        if settings["population"] == "common-selected":
            rows = [r for r in rows if r["task"] in selected_tasks]
        family_values = {m: _family_values(rows, m) for m in METRICS}
        families = sorted({r["family"] for r in rows})
        members[data["method"]] = {
            "method_group": data["method_group"],
            "training_seed": data["training_seed"],
            "writer_identity": data["writer_identity"],
            "families": {
                family: {
                    m: {
                        "value": family_values[m][family],
                        "unresolved": family_values[m][family] is None,
                    }
                    for m in METRICS
                }
                for family in families
            },
            "metrics": {
                m: {
                    **_estimate(
                        list(family_values[m].values()),
                        analysis["bootstrap_samples"],
                        analysis["bootstrap_seed"],
                        analysis["confidence"],
                    ),
                    "contributing_families": sum(v is not None for v in family_values[m].values()),
                    "coverage_complete": bool(families)
                    and all(v is not None for v in family_values[m].values()),
                }
                for m in METRICS
            },
        }
    # Both tools use the same implementation of grouping and family resampling.
    shared = summarize_seeds(
        {
            "methods": members,
            "reference": source["reference"],
            "purpose": source["purpose"],
            "bootstrap": {
                "samples": analysis["bootstrap_samples"],
                "seed": analysis["bootstrap_seed"],
                "confidence": analysis["confidence"],
            },
        },
        metric_names=METRICS,
        completion_metric="selected_completion",
    )
    for group in shared["groups"].values():
        if not group["families"]:
            for metric in group["metrics"].values():
                metric["coverage_complete"] = False
    for comparison in shared["comparisons"]:
        if comparison["paired_families"] == 0:
            comparison["coverage_complete"] = False
    actual = defaultdict(list)
    for member in members.values():
        actual[member["method_group"]].append(member["training_seed"])
    coverage = []
    blocked = set()
    for group, expected in settings["expected_seeds"].items():
        observed = actual.get(group, [])
        missing = sorted(set(expected) - set(observed))
        extra = sorted(
            set(observed) - set(expected), key=lambda value: -1 if value is None else value
        )
        coverage.append(
            {
                "group": group,
                "expected": expected,
                "observed": observed,
                "missing": missing,
                "extra": extra,
                "complete": not missing and not extra,
            }
        )
        if missing or extra:
            blocked.add(group)
    for group in blocked & shared["groups"].keys():
        for metric in shared["groups"][group]["metrics"].values():
            metric.update(
                observed_only_estimate=metric["estimate"],
                estimate=None,
                interval=None,
                coverage_complete=False,
            )
    for comparison in shared["comparisons"]:
        if comparison["group"] in blocked or comparison["reference"] in blocked:
            comparison.update(
                observed_only_difference=comparison["difference"],
                difference=None,
                interval_low=None,
                interval_high=None,
                coverage_complete=False,
            )
    for group, row in shared["groups"].items():
        if "completion_directions_vs_reference_group" in row and (
            group in blocked or shared["reference_group"] in blocked
        ):
            row["observed_only_completion_directions"] = row[
                "completion_directions_vs_reference_group"
            ]
            row["completion_directions_vs_reference_group"] = {
                "advantage": 0,
                "tie": 0,
                "disadvantage": 0,
                "unknown": len(row["members"]),
            }
    shared.update(
        kind="collection_checkpoint_analysis",
        population=settings["population"],
        declared_roster_checked=bool(settings["expected_seeds"]),
        declared_roster_complete=not blocked,
        declared_roster_coverage=coverage,
        groups_without_declared_seed_roster=sorted(set(actual) - set(settings["expected_seeds"])),
        population_tasks=sorted(selected_tasks)
        if settings["population"] == "common-selected"
        else sorted(row["task"] for row in source["task_summaries"][source["reference"]]),
        training_labels=None,
        roster_note="Expected seeds, when supplied, are a historical coverage declaration. "
        "No pre-inference roster is authenticated; missing seeds block group aggregates.",
    )
    return shared


def summary_files(source, raw_source, settings):
    result = summarize(source, settings)
    groups = []
    for group, values in result["groups"].items():
        for metric, row in values["metrics"].items():
            ci = row["interval"]
            groups.append(
                {
                    "group": group,
                    "metric": metric,
                    "estimate": row["estimate"],
                    "lower": None if ci is None else ci[0],
                    "upper": None if ci is None else ci[1],
                    "checkpoint_min": row["checkpoint_min"],
                    "checkpoint_max": row["checkpoint_max"],
                    "observed_checkpoints": row["observed_checkpoints"],
                    "coverage_complete": row["coverage_complete"],
                }
            )
    lines = [
        f"# {purpose_label(source)}",
        "",
        "Observed training-checkpoint summary",
        "",
        result["note"],
        "",
        result["roster_note"],
        "",
        f"Population: {result['population']}; "
        f"tasks: {', '.join(result['population_tasks']) or 'none'}.",
        "",
        "| Group | Checkpoints | Selected completion | Observed checkpoint range |",
        "|---|---:|---:|---|",
    ]
    for group, values in result["groups"].items():
        metric = values["metrics"]["selected_completion"]
        lines.append(
            f"| {group} | {len(values['members'])} | {display(metric['estimate'], True)} | "
            f"{display(metric['checkpoint_min'], True)} to "
            f"{display(metric['checkpoint_max'], True)} |"
        )
    lines += ["", "## Expected-seed coverage", ""]
    lines += [
        f"- {r['group']}: missing {r['missing']}; unexpected {r['extra']}."
        for r in result["declared_roster_coverage"]
    ] or ["No expected-seed roster supplied."]
    lines += [
        "",
        "Individual checkpoints, including worse and unresolved ones, remain in checkpoints.csv.",
        "Group means average checkpoints within each family. Two seeds are not two task samples.",
        "Intervals do not include future training-seed variation.",
        "Configured writer identities are distinct tags/configs, not verified weight digests.",
        "No winner or training label is assigned.",
        "",
    ]
    text = "\n".join(lines)
    seed_fields = [
        "group",
        "method",
        "training_seed",
        "metric",
        "estimate",
        "interval_low",
        "interval_high",
        "contributing_families",
        "coverage_complete",
    ]
    group_fields = [
        "group",
        "metric",
        "estimate",
        "lower",
        "upper",
        "checkpoint_min",
        "checkpoint_max",
        "observed_checkpoints",
        "coverage_complete",
    ]
    pair_fields = [
        "group",
        "reference",
        "metric",
        "difference",
        "interval_low",
        "interval_high",
        "paired_families",
        "coverage_complete",
        "observed_only_difference",
    ]
    comparisons = [{k: row.get(k) for k in pair_fields} for row in result["comparisons"]]
    return {
        "source.comparison.json": raw_source,
        "options.json": encoded(options(**settings)),
        "analysis.json": encoded(result),
        "checkpoints.csv": table_csv(result["seeds"], seed_fields),
        "groups.csv": table_csv(groups, group_fields),
        "comparisons.csv": table_csv(comparisons, pair_fields),
        "report.md": text.encode(),
        "report.html": document(
            "Observed checkpoints",
            '<p><a href="checkpoints.csv">Individual checkpoints</a> · '
            '<a href="comparisons.csv">Group differences</a> · '
            '<a href="analysis.json">Full analysis</a></p>' + render_report_text(text),
        ),
    }


def run_summary(directory, output, *, population="common-selected", expected_seeds=None):
    source, raw = read_primary(directory)
    settings = options(population, expected_seeds)
    files = summary_files(source, raw, settings)
    receipt = publish("collection_checkpoint_summary", files, output)
    result = read_json(files["analysis.json"])
    receipt["analysis_complete"] = (
        result["declared_roster_complete"]
        and bool(result["population_tasks"])
        and all(
            row["metrics"][metric]["coverage_complete"]
            for row in result["groups"].values()
            for metric in ("selected_completion", "initial_pass_rate")
        )
    )
    return receipt
