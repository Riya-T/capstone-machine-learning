"""Size-matched sensitivity analysis selected without reading editing outcomes.

Usage:
    run_size_match(report_directory, "trained", output_directory, tolerance=0.2)
"""

from __future__ import annotations

import copy
import hashlib
import math
from collections import defaultdict

from .analysis import compare
from .artifacts import csv_bytes, encoded, publish_bundle, purpose_label, read_comparison
from .records import EvaluationError
from .report import json_text, write_report

FIELDS = (
    "family",
    "task",
    "generation_seed",
    "reference_size",
    "method_size",
    "relative_difference",
    "pair_eligible",
    "family_selected",
    "reason",
)


def select_families(result, method, *, tolerance, size_field="python_lines"):
    if result.get("size_matched_sensitivity"):
        raise EvaluationError("Start from the primary report, not another matched subset")
    if (
        type(tolerance) not in (float, int)
        or not math.isfinite(tolerance)
        or not 0 <= tolerance <= 1
    ):
        raise EvaluationError("Size tolerance must be finite and between zero and one")
    if size_field not in ("python_lines", "source_lines"):
        raise EvaluationError("Unsupported size field")
    reference = result["reference"]
    if method == reference or method not in result["methods"]:
        raise EvaluationError("Choose one non-reference method present in the report")
    indexed = {name: {} for name in (reference, method)}
    families = {}
    for data in result["source_datasets"]:
        if data["method"] not in indexed:
            continue
        families.update({t["id"]: t["family"] for t in data["tasks"]})
        for sample in data["samples"]:
            indexed[data["method"]][data["generation_seed"], sample["task"]] = sample

    rows, eligible = [], defaultdict(list)
    # Only initial statuses and source measurements enter the membership decision.
    # Editing scores are deliberately not inspected until this selection is locked.
    for key, parent in sorted(indexed[reference].items()):
        other = indexed[method][key]
        sizes = []
        reasons = []
        for name, sample in (("reference", parent), ("method", other)):
            size = (sample.get("source_metrics") or {}).get(size_field)
            if size is None and size_field == "source_lines":
                size = sample.get("source_lines")
            size = size if type(size) is int and size >= 0 else None
            sizes.append(size)
            if sample["initial_status"] != "pass":
                reasons.append(name + "_initial_not_pass")
            if size is None:
                reasons.append(name + "_size_unknown")
        gap = None if None in sizes else abs(sizes[0] - sizes[1]) / max(1, *sizes)
        if gap is not None and gap > tolerance:
            reasons.append("outside_size_tolerance")
        family = families[key[1]]
        eligible[family].append(not reasons)
        rows.append(
            dict(
                family=family,
                task=key[1],
                generation_seed=key[0],
                reference_size=sizes[0],
                method_size=sizes[1],
                relative_difference=gap,
                pair_eligible=not reasons,
                reason=";".join(reasons),
            )
        )
    selected = sorted(f for f, values in eligible.items() if all(values))
    for row in rows:
        row["family_selected"] = row["family"] in selected
        if row["pair_eligible"] and not row["family_selected"]:
            row["reason"] = "another_pair_in_family_excluded"
    rule = dict(
        version=1,
        method=method,
        reference=reference,
        size_field=size_field,
        relative_tolerance=tolerance,
        initially_passing_only=True,
        unit="whole_task_family",
        formula="abs(a-b)/max(1,a,b)",
    )
    return dict(
        rule=rule,
        rule_sha256=hashlib.sha256(encoded(rule)).hexdigest(),
        selected_families=selected,
        excluded_families=sorted(set(eligible) - set(selected)),
        membership=rows,
    )


def run_size_match(directory, method, output, *, tolerance, size_field="python_lines"):
    result, source_hash = read_comparison(directory)
    selection = select_families(result, method, tolerance=tolerance, size_field=size_field)
    selection.update(source_report_sha256=source_hash, purpose=result["purpose"])
    table = csv_bytes(selection["membership"], FIELDS)
    if not selection["selected_families"]:
        selection["status"] = "no_eligible_families"
        paths = publish_bundle(
            "size_match_empty",
            {
                "analysis.json": encoded(selection),
                "matching.csv": table,
                "report.md": (
                    f"# {purpose_label(result)}\n\nNo eligible size-matched families. "
                    "No subset score was invented; primary results are unchanged.\n"
                ).encode(),
            },
            output,
            source_hash=source_hash,
        )
        return dict(status=selection["status"], outputs=paths)

    datasets = []
    for data in result["source_datasets"]:
        if data["method"] not in (method, result["reference"]):
            continue
        data = copy.deepcopy(data)
        data["tasks"] = [t for t in data["tasks"] if t["family"] in selection["selected_families"]]
        ids = {t["id"] for t in data["tasks"]}
        data["samples"] = [s for s in data["samples"] if s["task"] in ids]
        datasets.append(data)
    bootstrap = result["bootstrap"]
    subset = compare(
        datasets,
        reference=result["reference"],
        bootstrap_samples=bootstrap["samples"],
        bootstrap_seed=bootstrap["seed"],
        confidence=bootstrap["confidence"],
    )
    subset["size_matched_sensitivity"] = True
    subset["notes"].insert(
        0,
        "Size-matched sensitivity subset: both parents initially pass; "
        "not a replacement for the primary all-generated comparison. "
        "Fix the tolerance before outcomes.",
    )
    paths = write_report(
        subset,
        output,
        supplemental={"matching.json": json_text(selection), "matching.csv": table.decode("utf8")},
    )
    return dict(
        status="complete",
        selected_families=selection["selected_families"],
        outputs={k: str(v) for k, v in paths.items()},
    )
