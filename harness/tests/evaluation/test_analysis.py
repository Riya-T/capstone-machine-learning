"""Hand-calculated metrics, family uncertainty, abstention, and safe report output.

Usage:
    uv run pytest tests/evaluation/test_analysis.py
"""

import copy
import csv
import hashlib
import json

import pytest

from harness.evaluation.analysis import compare
from harness.evaluation.records import EvaluationError
from harness.evaluation.report import write_report


def example(method="original"):
    """Synthetic outcome fixture: not a trained model or an experimental run."""
    tasks = [
        dict(
            id=name,
            family="family_" + name,
            split="eval",
            version=digit * 64,
            sequences=[dict(id="s1", changes=["a", "b"]), dict(id="s2", changes=["c", "a"])],
        )
        for name, digit in [("one", "1"), ("two", "2")]
    ]
    samples = []
    for task in tasks:
        initial = "fail" if method == "original" and task["id"] == "two" else "pass"
        second = (
            "fail_existing"
            if method == "original"
            else "success"
            if task["id"] == "one"
            else "fail_new"
        )
        trials = []
        for seq in task["sequences"]:
            for rep in range(3):
                steps = (
                    [
                        dict(
                            step=i,
                            change_id=change,
                            status="success" if i == 1 else second,
                            tokens_in=10,
                            tokens_out=20,
                            wall_s=0.5,
                        )
                        for i, change in enumerate(seq["changes"], 1)
                    ]
                    if initial == "pass"
                    else []
                )
                trials.append(dict(sequence=seq["id"], rep=rep, steps=steps))
        samples.append(
            dict(
                task=task["id"],
                candidate_id="a" * 64,
                initial_status=initial,
                writer_cost=dict(tokens_in=100, tokens_out=200, wall_s=1),
                trials=trials,
            )
        )
    return dict(
        schema_version=1,
        method=method,
        purpose="fixture",
        generation_seed=1,
        editor_reps=3,
        contract={"same_fixed_editor": "fixture-only"},
        tasks=tasks,
        samples=samples,
        provenance={"synthetic": True},
    )


def test_hand_calculated_population_and_conditional_scores():
    result = compare([example(), example("trained")], bootstrap_samples=200)
    original, trained = [result["methods"][x] for x in ("original", "trained")]
    assert original["metrics"]["initial_correctness"]["estimate"] == 0.5
    assert trained["metrics"]["initial_correctness"]["estimate"] == 1
    assert original["metrics"]["change_completion"]["estimate"] == 0.25
    assert trained["metrics"]["change_completion"]["estimate"] == 0.75
    assert original["metrics"]["change_completion_initially_correct"]["estimate"] == 0.5
    assert original["metrics"]["whole_sequence_success"]["estimate"] == 0
    assert trained["metrics"]["whole_sequence_success"]["estimate"] == 0.5
    assert original["metrics"]["regression_rate_reached"]["estimate"] == 0.5
    assert trained["metrics"]["regression_rate_reached"]["estimate"] == 0
    pair = result["comparisons"][0]["metrics"]["change_completion"]
    assert pair["difference"] == 0.5 and pair["interval"] == [0.5, 0.5]
    # Conditional paired comparison has only the one common passing family.
    conditional = result["comparisons"][0]["metrics"]["change_completion_initially_correct"]
    assert conditional["paired_families"] == 1 and conditional["interval"] is None
    assert original["counts"]["initial_fail"] == 1
    assert original["counts"]["regressions"] == 6
    assert original["counts"]["steps_behaviorally_evaluated"] == 12
    assert original["costs"]["tokens_in"]["known_total"] == 320


@pytest.mark.parametrize("state", ["missing", "infra_error"])
def test_unresolved_work_abstains_instead_of_becoming_a_zero(state):
    original = example()
    trial = original["samples"][0]["trials"][0]
    trial["steps"] = [] if state == "missing" else [{**trial["steps"][0], "status": "infra_error"}]
    result = compare([original, example("trained")], bootstrap_samples=100)
    metric = result["methods"]["original"]["metrics"]["change_completion"]
    assert metric["estimate"] is None and metric["interval"] is None
    assert not metric["coverage_complete"] and metric["complete_case_diagnostic"] == 0
    assert result["comparisons"][0]["metrics"]["change_completion"]["difference"] is None


def test_budget_stop_is_failure_but_not_a_known_regression():
    data = example("trained")
    data["samples"][0]["trials"][0]["steps"] = [
        {**data["samples"][0]["trials"][0]["steps"][0], "status": "budget_exhausted"}
    ]
    result = compare([data], bootstrap_samples=50)["methods"]["trained"]
    assert result["counts"]["trajectory_budget_exhausted"] == 1
    assert result["counts"]["steps_behaviorally_evaluated"] == 22
    assert result["counts"].get("regressions", 0) == 0


def test_repetitions_and_related_tasks_do_not_inflate_bootstrap_family_count():
    original, trained = example(), example("trained")
    for data in (original, trained):
        for task in data["tasks"]:
            task["family"] = "one_family"
    result = compare([original, trained], bootstrap_samples=100)
    assert len(result["trajectories"]) == 24
    metric = result["comparisons"][0]["metrics"]["change_completion"]
    assert metric["paired_families"] == 1 and metric["interval"] is None


def test_all_initial_failures_have_zero_population_score_and_no_conditional_score():
    data = example()
    for sample in data["samples"]:
        sample["initial_status"] = "fail"
        for trial in sample["trials"]:
            trial["steps"] = []
    metrics = compare([data], bootstrap_samples=50)["methods"]["original"]["metrics"]
    assert metrics["change_completion"]["estimate"] == 0
    assert metrics["change_completion_initially_correct"]["estimate"] is None
    assert metrics["regression_rate_reached"]["estimate"] is None


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.update(generation_seed=2),
        lambda d: d["contract"].update(editor="different"),
        lambda d: d["tasks"][0].update(version="f" * 64),
        lambda d: d.update(purpose="heldout"),
    ],
)
def test_unmatched_comparisons_are_rejected(mutation):
    data = example("trained")
    mutation(data)
    with pytest.raises(EvaluationError):
        compare([example(), data], bootstrap_samples=50)


def test_duplicate_method_seed_is_rejected():
    with pytest.raises(EvaluationError, match="Duplicate"):
        compare([example(), example()], bootstrap_samples=50)


def test_paired_bootstrap_handles_opposite_family_effects_and_is_reproducible():
    original, trained = example("base"), example("trained")
    # Both initially pass. Family one's difference +0.5, family two's -0.5.
    for method, fixture in [("base", original), ("trained", trained)]:
        for n, sample in enumerate(fixture["samples"]):
            success = (method == "trained") == (n == 0)
            for trial in sample["trials"]:
                trial["steps"][-1]["status"] = "success" if success else "fail_new"
    a = compare([original, trained], bootstrap_samples=300, bootstrap_seed=17)
    b = compare([original, trained], bootstrap_samples=300, bootstrap_seed=17)
    m = a["comparisons"][0]["metrics"]["change_completion"]
    assert m["difference"] == 0 and m["interval"] == [-0.5, 0.5]
    assert a == b


def test_cost_unknowns_are_not_fabricated_as_complete_observed_totals():
    data = example()
    data["samples"][0]["writer_cost"]["tokens_in"] = None
    result = compare([data], bootstrap_samples=50)["methods"]["original"]["costs"]
    assert result["tokens_in"]["known_total"] == 220
    assert result["tokens_in"]["missing_records"] == 1


def test_reports_are_labeled_have_every_trajectory_and_never_clobber(tmp_path):
    result = compare([example(), example("trained")], bootstrap_samples=100)
    paths = write_report(result, tmp_path)
    assert "SYNTHETIC FIXTURE" in paths["report.md"].read_text(encoding="utf8")
    assert json.loads(paths["comparison.json"].read_text())["purpose"] == "fixture"
    with paths["trajectories.csv"].open(newline="") as f:
        assert len(list(csv.DictReader(f))) == 24
    before = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    assert write_report(result, tmp_path) == paths
    assert before == {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()
    }
    changed = copy.deepcopy(result)
    changed["notes"].append("different")
    with pytest.raises(EvaluationError, match="overwrite"):
        write_report(changed, tmp_path)
    assert before == {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bootstrap_samples": 0},
        {"bootstrap_samples": 20001},
        {"confidence": 0},
        {"confidence": 1},
        {"confidence": float("nan")},
        {"bootstrap_seed": -1},
        {"reference": "absent"},
    ],
)
def test_invalid_analysis_options(kwargs):
    with pytest.raises(EvaluationError):
        compare([example()], **kwargs)
