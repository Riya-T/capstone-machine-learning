"""Separate correctness, selected-parent editing, and identifiable per-sample yield.

Usage: result = compare_collections(exports, reference="base")
Families, not individual edits or tests, are the uncertainty units.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict

from ..evaluation.analysis import interval
from ..evaluation.records import EvaluationError, integer, trajectory
from .records import validate_collection

BEHAVIORAL = {"success", "fail_new", "fail_existing", "fail_both"}
METRICS = (
    "initial_pass_rate",
    "selected_prefix",
    "selected_completion",
    "selected_first_success",
    "selected_whole_success",
    "all_sample_completion",
    "pass_rate_times_selected_completion_proxy",
)


def mean(values):
    return statistics.fmean(values) if values else None


def bounded(values):
    known = [v for v in values if v is not None]
    unknown = len(values) - len(known)
    return {
        "estimate": mean(known) if not unknown else None,
        "lower": sum(known) / len(values) if values else None,
        "upper": (sum(known) + unknown) / len(values) if values else None,
        "known": len(known),
        "unknown": unknown,
        "planned": len(values),
    }


def resources(items):
    """A known subtotal and its missing count are not a complete usage total."""
    rows = list(items)
    return {
        key: {
            "known_subtotal": sum(r[key] for r in rows if r.get(key) is not None),
            "known_records": sum(r.get(key) is not None for r in rows),
            "missing_records": sum(r.get(key) is None for r in rows),
            "total": None if any(r.get(key) is None for r in rows) else sum(r[key] for r in rows),
        }
        for key in ("tokens_in", "tokens_out", "wall_s", "n_calls")
    }


def _parent_scores(parent, lengths):
    result = []
    for trial in parent["trials"]:
        outcome = trajectory({"initial_status": "pass"}, trial, lengths[trial["sequence"]])
        score, length = outcome["score"], lengths[trial["sequence"]]
        result.append(
            {
                "sequence": trial["sequence"],
                "rep": trial["rep"],
                "status": outcome["status"],
                "score": score,
                "completion": None if score is None else score / length,
                "first": None if score is None else float(score > 0),
                "whole": None if score is None else float(score == length),
            }
        )
    return result


def task_summary(data, task):
    lengths = {s["id"]: len(s["changes"]) for s in task["definition"]["sequences"]}
    parents = {p["candidate_id"]: p for p in task["programs"]}
    selected = [p for p in parents.values() if p["selection"] == "selected"]
    scores = {p["candidate_id"]: _parent_scores(p, lengths) for p in selected}
    trials = [r for rows in scores.values() for r in rows]
    unknown_eligibility = any(
        s["initial_status"] in ("unresolved", "infra_error") for s in task["samples"]
    )
    cap = data["contract"]["max_programs"]
    # Once the definitely selected set fills the cap, later missing answers
    # cannot change it. They still block all-sample correctness estimates.
    selection_unknown = unknown_eligibility and (cap is None or len(selected) < cap)
    complete = (
        bool(trials) and not selection_unknown and all(t["score"] is not None for t in trials)
    )
    initial = bounded(
        [
            float(s["initial_status"] == "pass")
            if s["initial_status"] in ("pass", "fail", "parse_failure")
            else None
            for s in task["samples"]
        ]
    )
    all_sample = []
    for sample in task["samples"]:
        if sample["initial_status"] in ("fail", "parse_failure"):
            all_sample.extend([0.0] * (len(lengths) * data["contract"]["editor_reps"]))
        elif sample["candidate_id"] in scores:
            all_sample.extend(row["completion"] for row in scores[sample["candidate_id"]])
        else:
            all_sample.extend([None] * (len(lengths) * data["contract"]["editor_reps"]))
    per_sample = bounded(all_sample)
    selected_completion = mean([t["completion"] for t in trials]) if complete else None
    steps = [step for p in selected for t in p["trials"] for step in t["steps"]]
    endings = Counter(step["status"] for step in steps)
    return {
        "task": task["definition"]["id"],
        "family": task["definition"]["family"],
        "samples_planned": len(task["samples"]),
        "initial_counts": dict(Counter(s["initial_status"] for s in task["samples"])),
        "parsed_unique_programs": len(parents),
        "duplicate_samples": sum(max(len(p["sample_indices"]) - 1, 0) for p in parents.values()),
        "selected_programs": len(selected),
        "over_cap_programs": sum(p["selection"] == "over_cap" for p in parents.values()),
        "selection_unresolved": selection_unknown,
        "selected_trials_planned": len(trials),
        "selected_trials_resolved": sum(t["score"] is not None for t in trials),
        "selected_trials_complete": complete,
        "initial_pass_rate": initial["estimate"],
        "initial_bounds": initial,
        "selected_prefix": mean([t["score"] for t in trials]) if complete else None,
        "selected_completion": selected_completion,
        "selected_first_success": mean([t["first"] for t in trials]) if complete else None,
        "selected_whole_success": mean([t["whole"] for t in trials]) if complete else None,
        "all_sample_completion": per_sample["estimate"],
        "all_sample_bounds": per_sample,
        "pass_rate_times_selected_completion_proxy": (
            initial["estimate"] * selected_completion
            if initial["estimate"] is not None and selected_completion is not None
            else None
        ),
        "observed_step_endings": dict(endings),
        "observed_regressions": sum(endings[s] for s in ("fail_existing", "fail_both")),
        "behaviorally_evaluated_steps": sum(endings[s] for s in BEHAVIORAL),
        "writer_resources": resources(s["writer_cost"] for s in task["samples"]),
        "editor_resources": resources(steps),
    }


def _family_values(rows, metric):
    groups = defaultdict(list)
    for row in rows:
        groups[row["family"]].append(row[metric])
    return {
        family: mean(values) if all(v is not None for v in values) else None
        for family, values in sorted(groups.items())
    }


def _estimate(values, count, seed, confidence):
    if not values or any(v is None for v in values):
        return {"estimate": None, "interval": None, "families": len(values)}
    return {
        "estimate": mean(values),
        "interval": interval(values, count, seed, confidence),
        "families": len(values),
    }


def identification(rows, field):
    families = defaultdict(list)
    for row in rows:
        families[row["family"]].append(row[field])
    return {
        "lower": mean([mean([r["lower"] for r in group]) for group in families.values()]),
        "upper": mean([mean([r["upper"] for r in group]) for group in families.values()]),
        "unknown_slots": sum(r[field]["unknown"] for r in rows),
        "families": len(families),
        "interpretation": "identification bounds, not confidence intervals",
    }


def compare_collections(
    datasets, *, reference=None, bootstrap_samples=2000, bootstrap_seed=20261119, confidence=0.95
):
    integer(bootstrap_samples, "bootstrap samples", 1)
    integer(bootstrap_seed, "bootstrap seed")
    if (
        type(confidence) not in (int, float)
        or not math.isfinite(confidence)
        or not 0 < confidence < 1
    ):
        raise EvaluationError("Confidence must be between zero and one")
    if not datasets:
        raise EvaluationError("No collection exports")
    datasets = [validate_collection(d) for d in datasets]
    first = datasets[0]
    methods = [d["method"] for d in datasets]
    if len(set(methods)) != len(methods):
        raise EvaluationError(
            "Give each checkpoint a distinct method ID; do not pool training seeds"
        )
    reference = reference or methods[0]
    if reference not in methods:
        raise EvaluationError("Unknown reference method")

    def signature(data):
        return {t["definition"]["id"]: t["definition"] for t in data["tasks"]}

    for data in datasets[1:]:
        if data["purpose"] != first["purpose"] or data["contract"] != first["contract"]:
            raise EvaluationError(
                "Collection purposes, editor, image or per-call/selection budgets differ"
            )
        if (
            signature(data) != signature(first)
            or data["generation_seed"] != first["generation_seed"]
        ):
            raise EvaluationError("Task roster, versions, sequences or generation seed differ")
    rows = {d["method"]: [task_summary(d, t) for t in d["tasks"]] for d in datasets}
    indexed = {method: {r["task"]: r for r in values} for method, values in rows.items()}
    cohort, exclusions = [], []
    for task_id in sorted(signature(first)):
        reasons = {
            method: (
                "no_selected_passing_parent"
                if row["selected_programs"] == 0
                else "unresolved_selection_or_trials"
                if not row["selected_trials_complete"]
                else None
            )
            for method in methods
            for row in [indexed[method][task_id]]
        }
        reasons = {m: why for m, why in reasons.items() if why is not None}
        if reasons:
            exclusions.append({"task": task_id, "reasons": reasons})
        else:
            cohort.append(task_id)
    summaries = {}
    for method, values in rows.items():
        common = [indexed[method][t] for t in cohort]
        summaries[method] = {
            "all_sample_identification": identification(values, "all_sample_bounds"),
            "initial_identification": identification(values, "initial_bounds"),
            "all_planned_tasks": {
                m: _estimate(
                    list(_family_values(values, m).values()),
                    bootstrap_samples,
                    bootstrap_seed,
                    confidence,
                )
                for m in METRICS
            },
            "common_selected_cohort": {
                m: _estimate(
                    list(_family_values(common, m).values()),
                    bootstrap_samples,
                    bootstrap_seed,
                    confidence,
                )
                for m in METRICS
            },
            "observed_counts": {
                "samples_planned": sum(r["samples_planned"] for r in values),
                "selected_programs": sum(r["selected_programs"] for r in values),
                "selected_trials_planned": sum(r["selected_trials_planned"] for r in values),
                "selected_trials_resolved": sum(r["selected_trials_resolved"] for r in values),
                "regressions": sum(r["observed_regressions"] for r in values),
                "behaviorally_evaluated_steps": sum(
                    r["behaviorally_evaluated_steps"] for r in values
                ),
            },
        }
    comparisons = []
    for method in methods:
        if method == reference:
            continue
        paired = []
        for task_id in cohort:
            b, o = indexed[reference][task_id], indexed[method][task_id]
            paired.append(
                {
                    "family": b["family"],
                    **{m: None if b[m] is None or o[m] is None else o[m] - b[m] for m in METRICS},
                }
            )
        metrics = {
            m: _estimate(
                list(_family_values(paired, m).values()),
                bootstrap_samples,
                bootstrap_seed,
                confidence,
            )
            for m in METRICS
        }
        leave_one_out = []
        for excluded in sorted({r["family"] for r in paired}):
            rest = [r for r in paired if r["family"] != excluded]
            leave_one_out.append(
                {
                    "excluded_family": excluded,
                    "selected_completion_difference": mean(
                        list(_family_values(rest, "selected_completion").values())
                    ),
                }
            )
        comparisons.append(
            {
                "reference": reference,
                "method": method,
                "metrics": metrics,
                "leave_one_family_out": leave_one_out,
                "all_planned_sample_difference_bounds": {
                    "lower": summaries[method]["all_sample_identification"]["lower"]
                    - summaries[reference]["all_sample_identification"]["upper"],
                    "upper": summaries[method]["all_sample_identification"]["upper"]
                    - summaries[reference]["all_sample_identification"]["lower"],
                    "interpretation": "full-roster identification bounds, not confidence intervals",
                },
            }
        )
    return {
        "schema_version": 1,
        "kind": "collection_comparison",
        "purpose": first["purpose"],
        "reference": reference,
        "analysis": {
            "bootstrap_samples": bootstrap_samples,
            "bootstrap_seed": bootstrap_seed,
            "confidence": confidence,
            "uncertainty_unit": "family",
            "training_seed_uncertainty_included": False,
        },
        "common_selected_tasks": cohort,
        "cohort_exclusions": exclusions,
        "task_summaries": rows,
        "methods": summaries,
        "comparisons": comparisons,
        "source_datasets": datasets,
        "training_labels_created": 0,
    }
