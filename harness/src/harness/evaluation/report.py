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
from .storage import check_existing, publish_new

OUTPUT_NAMES = (
    "comparison.json",
    "summary.csv",
    "comparisons.csv",
    "families.csv",
    "trajectories.csv",
    "report.md",
    "manifest.json",
)


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
        "## Initial source descriptions",
        "",
        "Initially passing programs only. Known family-weighted means; missing samples "
        "remain disclosed. These measurements do not establish maintainability.",
        "",
        "| Method | Source lines | Python documentation-line density | "
        "Missing samples (lines / density) |",
        "|---|---:|---:|---:|",
    ]
    for name, method in result["methods"].items():
        fields = method["initial_source_descriptives"]["fields"]
        size, density = fields["source_lines"], fields["python_documentation_density"]
        size_text = size["family_weighted_known_mean"]
        lines.append(
            f"| {name} | {'unavailable' if size_text is None else f'{size_text:.1f}'} | "
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


def write_report(result: dict, directory: Path) -> dict[str, Path]:
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
