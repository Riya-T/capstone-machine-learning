"""Write JSON, CSV, and a readable comparison report without overwriting evidence.

Usage:
    write_report(compare(datasets), Path("runs/comparison-001"))
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from .analysis import METRICS
from .records import EvaluationError


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
        "| Method | Initial correct | Changes completed, all | Initially correct subset | "
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
        text = "unavailable" if ci is None else f"[{ci[0]:.1%}, {ci[1]:.1%}]"
        lines.append(
            f"| {pair['method']} vs {pair['reference']} | "
            f"{_percent(m['difference'])} | {text} ({level:.0%}) | "
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
    for name, text in outputs.items():
        path = directory / name
        if path.exists() and path.read_bytes() != text.encode("utf8"):
            raise EvaluationError(f"Refusing to overwrite {path}; use a new report directory")
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in outputs.items():
        path = directory / name
        if not path.exists():
            path.write_bytes(text.encode("utf8"))
    return {name: directory / name for name in outputs}
