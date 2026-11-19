"""Publish and verify portable collection comparison bundles without overwrite.

Usage: write_report(compare_collections(exports), Path("runs/collection-comparison"))
HTML is self-contained; generated programs and raw model replies are never embedded.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import stat
from pathlib import Path

from ..evaluation.records import EvaluationError, read_json, trajectory
from ..evaluation.storage import check_existing, publish_new
from .analysis import METRICS, compare_collections

FILES = {
    "comparison.json",
    "report.md",
    "report.html",
    "tasks.csv",
    "samples.csv",
    "trajectories.csv",
    "checkpoints.csv",
    "resources.csv",
    "comparisons.csv",
}


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def table_csv(rows, fields):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    # Keep user-controlled strings inert when a CSV is opened in a spreadsheet.
    # Numeric differences remain numeric, including legitimate negative values.
    def cell(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    writer.writerows({k: cell(v) for k, v in row.items()} for row in rows)
    return output.getvalue().encode()


def display(value, percent=False):
    return "unavailable" if value is None else f"{value:.1%}" if percent else f"{value:.3f}"


def render_markdown(result):
    title = (
        "SYNTHETIC FIXTURE — software demonstration"
        if result["purpose"] == "fixture"
        else (f"{result['purpose'].capitalize()} collection comparison")
    )
    lines = [
        f"# {title}",
        "",
        f"Reference: {result['reference']}.",
        "",
        "Every planned family is retained. Unknown outcomes are not code failures.",
        "",
        "## Initial correctness over all planned tasks",
        "",
        "| Checkpoint | Initial pass rate | Samples | Selected parents | Resolved / planned |",
        "|---|---:|---:|---:|---:|",
    ]
    for method, summary in result["methods"].items():
        counts = summary["observed_counts"]
        rate = summary["all_planned_tasks"]["initial_pass_rate"]["estimate"]
        lines.append(
            f"| {method} | {display(rate, True)} | {counts['samples_planned']} | "
            f"{counts['selected_programs']} | {counts['selected_trials_resolved']} / "
            f"{counts['selected_trials_planned']} |"
        )
    cohort = result["common_selected_tasks"]
    lines += [
        "",
        "## Editing on the common selected-parent cohort",
        "",
        f"Tasks ({len(cohort)}): {', '.join(cohort) or 'none'}.",
        "",
        "This conditions on each writer's own selected passing programs, not identical parents.",
        "Every method must have complete selected trajectories for a task to enter this cohort.",
        "",
        "| Checkpoint | Changes before failure | Fraction completed | First works | Whole works |",
        "|---|---:|---:|---:|---:|",
    ]
    for method, summary in result["methods"].items():
        m = summary["common_selected_cohort"]
        lines.append(
            f"| {method} | {display(m['selected_prefix']['estimate'])} | "
            f"{display(m['selected_completion']['estimate'], True)} | "
            f"{display(m['selected_first_success']['estimate'], True)} | "
            f"{display(m['selected_whole_success']['estimate'], True)} |"
        )
    lines += ["", "### Cohort exclusions", ""]
    lines += [
        f"- {r['task']}: " + "; ".join(f"{m}: {v}" for m, v in r["reasons"].items())
        for r in result["cohort_exclusions"]
    ] or ["None."]
    lines += [
        "",
        "## Paired differences on that same cohort",
        "",
        "Other minus reference, averaging tasks within family and then families equally.",
        "",
        "| Checkpoint | Metric | Difference | Exploratory interval | Families |",
        "|---|---|---:|---|---:|",
    ]
    for comparison in result["comparisons"]:
        for metric, value in comparison["metrics"].items():
            bounds = value["interval"]
            ci = "unavailable" if bounds is None else f"{bounds[0]:+.3f} to {bounds[1]:+.3f}"
            lines.append(
                f"| {comparison['method']} | {metric} | {display(value['estimate'])} | "
                f"{ci} | {value['families']} |"
            )
    lines += [
        "",
        "## Per-sample outcomes and selection",
        "",
        "Initial failures contribute zero completed changes, without inventing editing attempts.",
        "Duplicates reuse one saved parent trajectory; they are not independent editor runs.",
        "Unedited over-cap parents and unresolved work remain unknown. Bounds vary every",
        "unknown normalized outcome from 0 to 1. These are identification bounds,",
        "not confidence intervals.",
        "The pass-rate-times-selected-score product is a descriptive proxy. Selection caps and",
        "duplicate frequencies can make it differ from observed per-sample performance.",
        "",
        "| Checkpoint | Task | Exact sample score | Bounds | Unknown slots | Proxy |",
        "|---|---|---:|---|---:|---:|",
    ]
    for method, rows in result["task_summaries"].items():
        for row in rows:
            bounds = row["all_sample_bounds"]
            lines.append(
                f"| {method} | {row['task']} | {display(row['all_sample_completion'], True)} | "
                f"{display(bounds['lower'], True)} to {display(bounds['upper'], True)} | "
                f"{bounds['unknown']} | "
                f"{display(row['pass_rate_times_selected_completion_proxy'], True)} |"
            )
    lines += [
        "",
        "### All planned families: per-sample completion bounds",
        "",
        "| Checkpoint | Lower | Upper | Unknown slots | Families |",
        "|---|---:|---:|---:|---:|",
    ]
    for method, summary in result["methods"].items():
        bounds = summary["all_sample_identification"]
        lines.append(
            f"| {method} | {display(bounds['lower'], True)} | "
            f"{display(bounds['upper'], True)} | {bounds['unknown_slots']} | "
            f"{bounds['families']} |"
        )
    lines += [
        "",
        "## Interpretation and costs",
        "",
        "- No training labels are produced. Passing tests is not proof of general maintainability.",
        "- Intervals condition on supplied checkpoints; training-seed uncertainty is absent.",
        "- Selected editing cannot replace all-sample correctness. Empty cohorts have no estimate.",
        "- Resources separate writer answers and unique-parent edits. Missing usage stays missing.",
        "- Tokens may be estimated. Times include checks and scheduling, not only GPU work.",
        "- Calls count saved answers/editor counts, not transport retries.",
        "- Methods may share cache records; summing costs does not measure incremental spending.",
        "- Model tags/configured identities do not attest immutable weight files.",
        "- This post-hoc report leaves historical scores unchanged.",
        "- `comparison.json` includes leave-one-family-out sensitivity and every source export.",
        "- Integrity checks detect changed files; they do not attest external model outcomes.",
        "",
        "Verify hashes and recompute the bundle:",
        "`python -m harness collection-workbench verify --report THIS_DIRECTORY`.",
        "",
    ]
    return "\n".join(lines)


def ledgers(result):
    samples, trajectories, checkpoints, costs = [], [], [], []
    for data in result["source_datasets"]:
        method = data["method"]
        for task in data["tasks"]:
            task_id = task["definition"]["id"]
            for sample in task["samples"]:
                samples.append(
                    {
                        "method": method,
                        "task": task_id,
                        **{
                            k: sample[k]
                            for k in (
                                "sample_idx",
                                "candidate_id",
                                "initial_status",
                                "parse_category",
                            )
                        },
                    }
                )
            seqs = {s["id"]: s["changes"] for s in task["definition"]["sequences"]}
            for parent in task["programs"]:
                if parent["selection"] != "selected":
                    continue
                for trial in parent["trials"]:
                    base = {
                        "method": method,
                        "task": task_id,
                        "candidate_id": parent["candidate_id"],
                        "sequence": trial["sequence"],
                        "rep": trial["rep"],
                    }
                    outcome = trajectory(
                        {"initial_status": "pass"}, trial, len(seqs[trial["sequence"]])
                    )
                    trajectories.append({**base, **outcome})
                    actual = {s["step"]: s for s in trial["steps"]}
                    stopped = False
                    for number, change in enumerate(seqs[trial["sequence"]], 1):
                        saved = actual.get(number)
                        status = (
                            "not_reached" if stopped else saved["status"] if saved else "missing"
                        )
                        checkpoints.append(
                            {
                                **base,
                                "step": number,
                                "change_id": change,
                                "status": status,
                                "recorded": saved is not None,
                                "end_reason": saved.get("end_reason") if saved else None,
                                "infra_cause": saved.get("infra_cause") if saved else None,
                            }
                        )
                        stopped |= saved is not None and saved["status"] != "success"
        for row in result["task_summaries"][method]:
            for phase in ("writer", "editor"):
                for measure, receipt in row[phase + "_resources"].items():
                    costs.append(
                        {
                            "method": method,
                            "task": row["task"],
                            "phase": phase,
                            "measure": measure,
                            **receipt,
                        }
                    )
    return samples, trajectories, checkpoints, costs


def render_html(result):
    """Escape every stored value; no external assets, requests or source execution."""
    task_rows = []
    for method, rows in result["task_summaries"].items():
        for row in rows:
            values = [
                method,
                row["task"],
                display(row["initial_pass_rate"], True),
                display(row["selected_completion"], True),
                display(row["all_sample_completion"], True),
                row["over_cap_programs"],
                row["selected_trials_planned"] - row["selected_trials_resolved"],
            ]
            task_rows.append(
                "<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in values) + "</tr>"
            )
    notice = (
        "SYNTHETIC FIXTURE — not experimental evidence"
        if result["purpose"] == "fixture"
        else (f"{result['purpose'].capitalize()} saved collection evidence")
    )
    return (
        """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy"
 content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
<title>Collection results workbench</title><style>
body{font:16px/1.55 system-ui,sans-serif;margin:2rem auto;padding:0 1.2rem;
max-width:1180px;color:#172b3a;background:#f5f8fb}
h1,h2{line-height:1.2}
main,section{background:white;padding:1.4rem;margin:1rem 0;
border:1px solid #d4e0e8;border-radius:10px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:.6rem;border-bottom:1px solid #d4e0e8}
th{background:#eaf2f8}input{font:inherit;padding:.55rem;width:min(90%,30rem)}
pre{white-space:pre-wrap;font:14px/1.6 ui-monospace,monospace}
.scroll{overflow-x:auto}.notice{color:#704108;background:#fff2d6;padding:.8rem}a{color:#075f97}
</style><header><h1>Collection results workbench</h1><p class="notice">"""
        + html.escape(notice)
        + """</p>
<p>Correctness and editing are different questions. Unknown is not failure.</p></header>
<main><h2>Task explorer</h2><label>Filter by checkpoint or task
<input id="filter" type="search" placeholder="e.g. recipe_binder"></label>
<p id="count" aria-live="polite"></p><div class="scroll"><table id="tasks"><thead><tr>
<th>Checkpoint</th><th>Task</th><th>Initial pass</th><th>Selected editing</th>
<th>Exact per-sample</th><th>Over cap</th><th>Unresolved trials</th>
</tr></thead><tbody>"""
        + "".join(task_rows)
        + """</tbody></table></div>
<p>Editing values here use each task's own selected parents.
Paired comparisons below use the disclosed common cohort.</p>
<p><a href="tasks.csv">Task CSV</a> · <a href="samples.csv">Every scheduled sample</a> ·
<a href="checkpoints.csv">Checkpoint ledger</a> ·
<a href="resources.csv">Resources</a> · <a href="comparison.json">Full evidence JSON</a></p></main>
<section><h2>Full report and limitations</h2><pre>"""
        + html.escape(render_markdown(result))
        + """</pre></section>
<script>
const input=document.getElementById('filter');
const rows=[...document.querySelectorAll('#tasks tbody tr')];
function filter(){let shown=0;for(const row of rows){
row.hidden=!row.textContent.toLowerCase().includes(input.value.toLowerCase());
shown+=!row.hidden;}
document.getElementById('count').textContent=shown+' of '+rows.length+' task/checkpoint rows';}
input.addEventListener('input',filter);filter();
</script></html>"""
    )


def artifacts(result):
    samples, trajectories, checkpoints, costs = ledgers(result)
    task_rows = [
        {
            "method": method,
            **{
                k: r[k]
                for k in (
                    "task",
                    "family",
                    "samples_planned",
                    "parsed_unique_programs",
                    "duplicate_samples",
                    "selected_programs",
                    "over_cap_programs",
                    "selected_trials_planned",
                    "selected_trials_resolved",
                    *METRICS,
                )
            },
        }
        for method, rows in result["task_summaries"].items()
        for r in rows
    ]
    differences = [
        {
            "method": c["method"],
            "reference": c["reference"],
            "metric": metric,
            "estimate": value["estimate"],
            "lower": None if value["interval"] is None else value["interval"][0],
            "upper": None if value["interval"] is None else value["interval"][1],
            "families": value["families"],
        }
        for c in result["comparisons"]
        for metric, value in c["metrics"].items()
    ]
    return {
        "comparison.json": encoded(result),
        "report.md": render_markdown(result).encode(),
        "report.html": render_html(result).encode(),
        "tasks.csv": table_csv(
            task_rows,
            [
                "method",
                "task",
                "family",
                "samples_planned",
                "parsed_unique_programs",
                "duplicate_samples",
                "selected_programs",
                "over_cap_programs",
                "selected_trials_planned",
                "selected_trials_resolved",
                *METRICS,
            ],
        ),
        "samples.csv": table_csv(
            samples,
            ["method", "task", "sample_idx", "candidate_id", "initial_status", "parse_category"],
        ),
        "trajectories.csv": table_csv(
            trajectories,
            [
                "method",
                "task",
                "candidate_id",
                "sequence",
                "rep",
                "score",
                "status",
                "completed_prefix",
            ],
        ),
        "checkpoints.csv": table_csv(
            checkpoints,
            [
                "method",
                "task",
                "candidate_id",
                "sequence",
                "rep",
                "step",
                "change_id",
                "status",
                "recorded",
                "end_reason",
                "infra_cause",
            ],
        ),
        "resources.csv": table_csv(
            costs,
            [
                "method",
                "task",
                "phase",
                "measure",
                "known_subtotal",
                "known_records",
                "missing_records",
                "total",
            ],
        ),
        "comparisons.csv": table_csv(
            differences, ["method", "reference", "metric", "estimate", "lower", "upper", "families"]
        ),
    }


def safe_destination(path):
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise EvaluationError("Refusing a symlinked output path")
        if ancestor.exists() and getattr(ancestor.stat(), "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
        ):
            raise EvaluationError("Refusing a reparse-point output path")


def write_report(result, out):
    out = Path(out)
    safe_destination(out)
    payload = artifacts(result)
    payload["manifest.json"] = encoded(
        {
            "schema_version": 1,
            "kind": "collection_report_manifest",
            "files": {name: hashlib.sha256(body).hexdigest() for name, body in payload.items()},
        }
    )
    # Check every target before publishing any file, including an existing manifest.
    for name, body in payload.items():
        check_existing(out / name, body)
    for name, body in payload.items():
        publish_new(out / name, body)
    complete = all(
        not row["selection_unresolved"]
        and not any(row["initial_counts"].get(s, 0) for s in ("unresolved", "infra_error"))
        and row["selected_trials_planned"] == row["selected_trials_resolved"]
        for rows in result["task_summaries"].values()
        for row in rows
    )
    return {
        "output_files": sorted(payload),
        "training_labels_created": 0,
        "collection_complete": complete,
        "common_selected_tasks": len(result["common_selected_tasks"]),
    }


def verify_report(out):
    out = Path(out)
    safe_destination(out)
    manifest = read_json((out / "manifest.json").read_bytes())
    if (
        manifest.get("schema_version") != 1
        or manifest.get("kind") != "collection_report_manifest"
        or set(manifest.get("files", {})) != FILES
    ):
        raise EvaluationError("Unexpected collection report manifest")
    for name, digest in manifest["files"].items():
        if (out / name).is_symlink() or hashlib.sha256(
            (out / name).read_bytes()
        ).hexdigest() != digest:
            raise EvaluationError(f"Report checksum mismatch: {name}")
    saved = read_json((out / "comparison.json").read_bytes())
    recomputed = compare_collections(
        saved["source_datasets"],
        reference=saved["reference"],
        **{k: saved["analysis"][k] for k in ("bootstrap_samples", "bootstrap_seed", "confidence")},
    )
    for name, body in artifacts(recomputed).items():
        if body != (out / name).read_bytes():
            raise EvaluationError(f"Saved analysis does not recompute: {name}")
    return {"verified": True, "analysis_recomputed": True, "files": len(FILES), "model_calls": 0}
