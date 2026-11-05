"""Compute family-weighted evaluation metrics and paired exploratory intervals.

Usage:
    result = compare(datasets, reference="original", bootstrap_samples=2000)
"""

from __future__ import annotations

import itertools
import random
import statistics
from collections import Counter, defaultdict

from .records import EvaluationError, integer, trajectory, validate_dataset

METRICS = (
    "initial_correctness",
    "change_completion",
    "change_completion_initially_correct",
    "whole_sequence_success",
    "whole_sequence_success_initially_correct",
    "regression_rate_reached",
    "new_feature_failure_rate_reached",
)
BEHAVIORAL = {"success", "fail_new", "fail_existing", "fail_both"}


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    left = int(position)
    right = min(left + 1, len(ordered) - 1)
    return ordered[left] + (ordered[right] - ordered[left]) * (position - left)


def interval(values: list[float], samples: int, seed: int, confidence: float):
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    draws = [statistics.mean(rng.choices(values, k=len(values))) for _ in range(samples)]
    tail = (1 - confidence) / 2
    return [percentile(draws, tail), percentile(draws, 1 - tail)]


def _task_signature(data):
    return {t["id"]: t for t in data["tasks"]}


def _cells(data):
    tasks = {t["id"]: t for t in data["tasks"]}
    cells = []
    for sample in data["samples"]:
        task = tasks[sample["task"]]
        lengths = {s["id"]: len(s["changes"]) for s in task["sequences"]}
        results = [
            {
                **trajectory(sample, t, lengths[t["sequence"]]),
                "length": lengths[t["sequence"]],
                "sequence": t["sequence"],
                "rep": t["rep"],
                "steps": t["steps"],
            }
            for t in sample["trials"]
        ]
        cells.append(
            dict(
                method=data["method"],
                seed=data["generation_seed"],
                task=task["id"],
                family=task["family"],
                sample=sample,
                trials=results,
            )
        )
    return cells


def _mean(values):
    return statistics.mean(values) if values else None


def _family_metrics(cells):
    unresolved_initial = any(c["sample"]["initial_status"] == "unresolved" for c in cells)
    known_initial = [
        c["sample"]["initial_status"] == "pass"
        for c in cells
        if c["sample"]["initial_status"] != "unresolved"
    ]
    result = {
        "initial_correctness": dict(
            value=None if unresolved_initial else _mean(known_initial),
            unresolved=unresolved_initial,
        )
    }
    for conditional, suffix in [(False, ""), (True, "_initially_correct")]:
        trials = [
            t
            for c in cells
            if not conditional or c["sample"]["initial_status"] == "pass"
            for t in c["trials"]
        ]
        unresolved = (conditional and unresolved_initial) or any(t["score"] is None for t in trials)
        for name, values in [
            (
                "change_completion",
                [t["score"] / t["length"] for t in trials if t["score"] is not None],
            ),
            (
                "whole_sequence_success",
                [float(t["score"] == t["length"]) for t in trials if t["score"] is not None],
            ),
        ]:
            result[name + suffix] = dict(
                value=None if unresolved else _mean(values),
                unresolved=unresolved,
            )
    reached = [
        s for c in cells for t in c["trials"] for s in t["steps"] if s["status"] in BEHAVIORAL
    ]
    for name, failures in [
        ("regression_rate_reached", {"fail_existing", "fail_both"}),
        ("new_feature_failure_rate_reached", {"fail_new", "fail_both"}),
    ]:
        result[name] = dict(
            value=_mean([s["status"] in failures for s in reached]),
            unresolved=False,
        )
    return result


def _summarize_families(families, metric, samples, seed, confidence):
    values = [f[metric]["value"] for f in families.values() if f[metric]["value"] is not None]
    unresolved = any(f[metric]["unresolved"] for f in families.values())
    return dict(
        estimate=None if unresolved else _mean(values),
        interval=None if unresolved else interval(values, samples, seed, confidence),
        contributing_families=len(values),
        planned_families=len(families),
        coverage_complete=not unresolved,
        complete_case_diagnostic=_mean(values) if unresolved else None,
    )


def _counts(cells):
    counts = Counter()
    costs = {
        k: dict(known_total=0, missing_records=0) for k in ("tokens_in", "tokens_out", "wall_s")
    }
    for c in cells:
        initial = c["sample"]["initial_status"]
        counts["initial_planned"] += 1
        counts["initial_" + initial] += 1
        records = [c["sample"]["writer_cost"]]
        for t in c["trials"]:
            counts["trajectories_planned"] += 1
            counts["trajectory_" + t["status"]] += 1
            counts["trajectories_resolved"] += t["score"] is not None
            for step in t["steps"]:
                records.append(step)
                counts["steps_recorded"] += 1
                if step["status"] in BEHAVIORAL:
                    counts["steps_behaviorally_evaluated"] += 1
                    counts["regressions"] += step["status"] in ("fail_existing", "fail_both")
                    counts["new_feature_failures"] += step["status"] in ("fail_new", "fail_both")
        for record in records:
            for k, summary in costs.items():
                if record[k] is None:
                    summary["missing_records"] += 1
                else:
                    summary["known_total"] += record[k]
    return dict(counts), costs


def compare(
    datasets: list[dict],
    *,
    reference: str | None = None,
    bootstrap_samples: int = 2000,
    bootstrap_seed: int = 20261105,
    confidence: float = 0.95,
) -> dict:
    """Each family is one resampling unit; unknown trajectories block primary scores."""
    if not datasets:
        raise EvaluationError("No evaluation datasets supplied")
    integer(bootstrap_samples, "bootstrap_samples", 1)
    if bootstrap_samples > 20000:
        raise EvaluationError("bootstrap_samples must be <= 20000")
    integer(bootstrap_seed, "bootstrap_seed")
    if type(confidence) not in (int, float) or not 0 < confidence < 1:
        raise EvaluationError("confidence must be between 0 and 1")
    methods = defaultdict(list)
    seen = set()
    first = validate_dataset(datasets[0])
    for data in datasets:
        validate_dataset(data)
        key = data["method"], data["generation_seed"]
        if key in seen:
            raise EvaluationError("Duplicate method/generation-seed dataset")
        seen.add(key)
        if (
            data["purpose"] != first["purpose"]
            or data["contract"] != first["contract"]
            or data["editor_reps"] != first["editor_reps"]
            or _task_signature(data) != _task_signature(first)
        ):
            raise EvaluationError("Unmatched task versions, editor, budget, sandbox, or purpose")
        methods[data["method"]].append(data)
    seed_sets = [{d["generation_seed"] for d in group} for group in methods.values()]
    if any(s != seed_sets[0] for s in seed_sets):
        raise EvaluationError("Methods must have matching generation-seed sets")
    reference = reference or first["method"]
    if reference not in methods:
        raise EvaluationError("Reference method is absent")
    output = dict(
        schema_version=1,
        purpose=first["purpose"],
        reference=reference,
        bootstrap=dict(
            samples=bootstrap_samples,
            seed=bootstrap_seed,
            confidence=confidence,
            unit="task_family",
            paired=True,
        ),
        methods={},
        comparisons=[],
        trajectories=[],
        source_datasets=datasets,
        notes=[
            "Families are equally weighted; repetition counts are not independent evidence.",
            "Initial failures score zero for all-generated completion and sequence success.",
            "Conditional scores use initially correct programs; populations can differ.",
            "Missing/infra work blocks primary estimates; complete-case values are diagnostics.",
            "Reached-step regression rates exclude budget stops without private evaluation.",
            "Intervals are exploratory percentile family bootstraps; one family has no interval.",
            "Recorded costs can include estimated tokens and historical wall/latency effects.",
            "Training seeds/checkpoints remain separate method rows; no hierarchical pooling.",
        ],
    )
    family_scores = {}
    for method in sorted(methods):
        cells = list(itertools.chain.from_iterable(_cells(d) for d in methods[method]))
        families = defaultdict(list)
        for cell in cells:
            families[cell["family"]].append(cell)
            for trial in cell["trials"]:
                output["trajectories"].append(
                    dict(
                        method=method,
                        generation_seed=cell["seed"],
                        task=cell["task"],
                        family=cell["family"],
                        candidate_id=cell["sample"]["candidate_id"],
                        initial_status=cell["sample"]["initial_status"],
                        sequence=trial["sequence"],
                        rep=trial["rep"],
                        length=trial["length"],
                        score=trial["score"],
                        status=trial["status"],
                        completed_prefix=trial["completed_prefix"],
                        recorded_steps=len(trial["steps"]),
                    )
                )
        f = {name: _family_metrics(group) for name, group in sorted(families.items())}
        family_scores[method] = f
        counts, costs = _counts(cells)
        output["methods"][method] = dict(
            metrics={
                m: _summarize_families(f, m, bootstrap_samples, bootstrap_seed, confidence)
                for m in METRICS
            },
            families=f,
            counts=counts,
            costs=costs,
        )
    for method in sorted(methods):
        if method == reference:
            continue
        metrics = {}
        for metric in METRICS:
            a, b = family_scores[method], family_scores[reference]
            unresolved = any(a[k][metric]["unresolved"] or b[k][metric]["unresolved"] for k in a)
            differences = [
                a[k][metric]["value"] - b[k][metric]["value"]
                for k in a
                if a[k][metric]["value"] is not None and b[k][metric]["value"] is not None
            ]
            metrics[metric] = dict(
                difference=None if unresolved else _mean(differences),
                interval=None
                if unresolved
                else interval(differences, bootstrap_samples, bootstrap_seed, confidence),
                paired_families=len(differences),
                coverage_complete=not unresolved,
            )
        output["comparisons"].append(dict(method=method, reference=reference, metrics=metrics))
    return output
