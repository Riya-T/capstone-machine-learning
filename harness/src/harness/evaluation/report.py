"""Write JSON, CSV, and a readable comparison report without overwriting evidence.

Usage:
    write_report(compare(datasets), Path("runs/comparison-001"))
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

from .analysis import METRICS
from .dashboard import render_dashboard
from .diagnostics import CHECKPOINT_FIELDS, FAILURE_FIELDS, diagnostic_rows
from .storage import check_existing, publish_new

OUTPUT_NAMES = (
    "comparison.json",
    "summary.csv",
    "comparisons.csv",
    "families.csv",
    "trajectories.csv",
    "checkpoints.csv",
    "failures.csv",
    "resources.csv",
    "source_descriptives.csv",
    "methods.csv",
    "report.md",
    "report.html",
    "manifest.json",
)
OPTIONAL_OUTPUT_NAMES = {"matching.json", "matching.csv"}


def json_text(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _csv(rows, fields):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def _percent(value):
    return "unavailable" if value is None else f"{value:.1%}"


def _points(value):
    return "unavailable" if value is None else f"{value * 100:+.1f} pp"


def render_markdown(result):
    title = {
        "fixture": "SYNTHETIC FIXTURE — not experimental evidence",
        "development": "Development comparison — not held-out evidence",
        "heldout": "Held-out writer comparison",
    }[result["purpose"]]
    if result.get("size_matched_sensitivity"):
        title = "Size-matched sensitivity analysis — " + title
    lines = [
        f"# {title}",
        "",
        f"Reference method: {result['reference']}.",
        "",
        "Family-weighted rates; unknown outcomes are not scored as failures.",
        "",
        "| Method | Initial tests passed | Changes completed, all | Initially passing subset | "
        "Whole sequences, all | Regressions / evaluated steps | Unresolved trials |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, method in result["methods"].items():
        m, c = method["metrics"], method["counts"]
        lines.append(
            f"| {name} | {_percent(m['initial_correctness']['estimate'])} | "
            f"{_percent(m['change_completion']['estimate'])} | "
            f"{_percent(m['change_completion_initially_correct']['estimate'])} | "
            f"{_percent(m['whole_sequence_success']['estimate'])} | "
            f"{c.get('regressions', 0)} / {c.get('steps_behaviorally_evaluated', 0)} | "
            f"{c['trajectories_planned'] - c.get('trajectories_resolved', 0)} |"
        )
    lines += [
        "",
        "## Paired completion differences",
        "",
        "Positive means more changes completed than the reference, not proven causation.",
        "",
        "| Method vs reference | Difference | Exploratory interval | Paired families |",
        "|---|---:|---|---:|",
    ]
    level = result["bootstrap"]["confidence"]
    for pair in result["comparisons"]:
        m = pair["metrics"]["change_completion"]
        ci = m["interval"]
        text = "unavailable" if ci is None else f"[{ci[0] * 100:+.1f}, {ci[1] * 100:+.1f}] pp"
        lines.append(
            f"| {pair['method']} vs {pair['reference']} | "
            f"{_points(m['difference'])} | {text} ({level:.0%}) | "
            f"{m['paired_families']} |"
        )
    lines += [
        "",
        "## Recorded resource use",
        "",
        "Known totals only. Missing records are explicit; tokens may include estimates.",
        "",
        "| Method | Input tokens | Output tokens | Wall seconds | Missing cost fields |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, method in result["methods"].items():
        c = method["costs"]
        lines.append(
            f"| {name} | {c['tokens_in']['known_total']} | {c['tokens_out']['known_total']} | "
            f"{c['wall_s']['known_total']:.3f} | "
            f"{sum(v['missing_records'] for v in c.values())} |"
        )
    lines += [
        "",
        "Writing and editing costs are separated in `resources.csv`, for all generated "
        "programs and the initially correct subset. Totals cover recorded attempts only; "
        "unstarted work is not measured cost.",
        "",
    ]
    lines += [
        "",
        "## Initial source descriptions",
        "",
        "Both all generated programs and the initially passing subset. "
        "Known family-weighted means; "
        "missing samples "
        "remain disclosed. These measurements do not establish maintainability.",
        "",
        "| Method / population | Source lines | Python documentation-line density | "
        "Missing samples (lines / density) |",
        "|---|---:|---:|---:|",
    ]
    for name, method in result["methods"].items():
        for population, key in (
            ("all generated", "all_generated_source_descriptives"),
            ("initially correct", "initial_source_descriptives"),
        ):
            fields = method[key]["fields"]
            size, density = fields["source_lines"], fields["python_documentation_density"]
            size_text = size["family_weighted_known_mean"]
            lines.append(
                f"| {name} / {population} | "
                f"{'unavailable' if size_text is None else f'{size_text:.1f}'} | "
                f"{_percent(density['family_weighted_known_mean'])} | "
                f"{size['missing_samples']} / {density['missing_samples']} |"
            )
    lines += ["", "## Interpretation and limits", ""]
    lines += [f"- {note}" for note in result["notes"]]
    lines += [
        "",
        "Full per-family estimates, all metrics/intervals, costs, individual trajectories,",
        "source configurations, task versions, model tags and run commits are in the JSON/CSV.",
        "The report does not assign preference labels or claim that training improved a model.",
    ]
    return "\n".join(lines) + "\n"


def write_report(result: dict, directory: Path, *, supplemental=None) -> dict[str, Path]:
    """Only create outputs, or accept identical prior outputs. Never clobber others."""
    directory = Path(directory)
    metric_rows = []
    for method, row in result["methods"].items():
        for name in METRICS:
            m = row["metrics"][name]
            metric_rows.append(
                dict(
                    method=method,
                    metric=name,
                    estimate=m["estimate"],
                    interval_low=None if m["interval"] is None else m["interval"][0],
                    interval_high=None if m["interval"] is None else m["interval"][1],
                    contributing_families=m["contributing_families"],
                    planned_families=m["planned_families"],
                    coverage_complete=m["coverage_complete"],
                )
            )
    outputs = {
        "comparison.json": json_text(result),
        "summary.csv": _csv(metric_rows, list(metric_rows[0])),
        "trajectories.csv": _csv(result["trajectories"], list(result["trajectories"][0])),
        "report.md": render_markdown(result),
        "report.html": render_dashboard(result),
    }
    pair_fields = [
        "method",
        "reference",
        "metric",
        "difference",
        "interval_low",
        "interval_high",
        "paired_families",
        "coverage_complete",
    ]
    pairs = []
    for pair in result["comparisons"]:
        for name, metric in pair["metrics"].items():
            pairs.append(
                dict(
                    method=pair["method"],
                    reference=pair["reference"],
                    metric=name,
                    difference=metric["difference"],
                    interval_low=None if metric["interval"] is None else metric["interval"][0],
                    interval_high=None if metric["interval"] is None else metric["interval"][1],
                    paired_families=metric["paired_families"],
                    coverage_complete=metric["coverage_complete"],
                )
            )
    outputs["comparisons.csv"] = _csv(pairs, pair_fields)
    families = [
        dict(method=method, family=family, metric=name, **metric)
        for method, row in result["methods"].items()
        for family, values in row["families"].items()
        for name, metric in values.items()
    ]
    outputs["families.csv"] = _csv(families, ["method", "family", "metric", "value", "unresolved"])
    checkpoints, failures = diagnostic_rows(result)
    outputs["checkpoints.csv"] = _csv(checkpoints, CHECKPOINT_FIELDS)
    outputs["failures.csv"] = _csv(failures, FAILURE_FIELDS)
    resources = [
        dict(
            method=method,
            population=population,
            phase=phase,
            measurement=key,
            **values,
            recorded_attempts=details["recorded_attempts"],
            unresolved_trajectories=group["unresolved_trajectories"],
        )
        for method, row in result["methods"].items()
        for population, group in row["resource_breakdown"].items()
        for phase, details in group["phases"].items()
        for key, values in details["costs"].items()
    ]
    outputs["resources.csv"] = _csv(
        resources,
        [
            "method",
            "population",
            "phase",
            "measurement",
            "known_total",
            "missing_records",
            "recorded_attempts",
            "unresolved_trajectories",
        ],
    )
    sources = [
        dict(method=method, population=population, measurement=key, **values)
        for method, row in result["methods"].items()
        for population, name in (
            ("all_generated", "all_generated_source_descriptives"),
            ("initially_correct", "initial_source_descriptives"),
        )
        for key, values in row[name]["fields"].items()
    ]
    outputs["source_descriptives.csv"] = _csv(
        sources,
        [
            "method",
            "population",
            "measurement",
            "family_weighted_known_mean",
            "contributing_families",
            "missing_samples",
        ],
    )
    method_rows = [
        dict(
            method=name,
            **{
                key: row[key]
                for key in ("method_group", "training_seed", "writer_model", "writer_identity")
            },
        )
        for name, row in result["methods"].items()
    ]
    outputs["methods.csv"] = _csv(
        method_rows, ["method", "method_group", "training_seed", "writer_model", "writer_identity"]
    )
    if supplemental:
        from .records import EvaluationError

        if not set(supplemental) <= OPTIONAL_OUTPUT_NAMES:
            raise EvaluationError("Unsupported supplementary report artifacts")
        outputs.update(supplemental)
    # Published last: absent manifest means a bundle is incomplete and safe to resume.
    outputs["manifest.json"] = json_text(
        dict(
            schema_version=1,
            complete=True,
            files={
                name: hashlib.sha256(text.encode("utf8")).hexdigest()
                for name, text in outputs.items()
            },
        )
    )
    for name, text in outputs.items():
        check_existing(directory / name, text.encode("utf8"))
    for name, text in outputs.items():
        publish_new(directory / name, text.encode("utf8"))
    return {name: directory / name for name in outputs}
