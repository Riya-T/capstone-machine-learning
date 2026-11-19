"""Check population denominators, unknowns and family-level comparisons by hand.

Usage: python -m pytest tests/workbench/test_analysis.py
Fixtures intentionally distinguish exact sample performance from a selection proxy.
"""

import copy

import pytest

from harness.evaluation.records import EvaluationError
from harness.workbench.analysis import compare_collections, task_summary
from harness.workbench.records import validate_collection
from tests.workbench.helpers import fixture


def test_cap_gives_identification_bounds_not_a_fabricated_sample_score(tmp_path):
    _, data = fixture(tmp_path)
    row = task_summary(data, data["tasks"][0])
    assert row["initial_pass_rate"] == pytest.approx(4 / 6)
    assert row["selected_completion"] == 0.5
    assert row["selected_prefix"] == 1
    assert row["selected_trials_planned"] == 8
    assert row["selected_trials_resolved"] == 8
    assert row["all_sample_completion"] is None
    assert row["all_sample_bounds"]["lower"] == pytest.approx(2 / 6)
    assert row["all_sample_bounds"]["upper"] == pytest.approx(3 / 6)
    assert row["all_sample_bounds"]["unknown"] == 4
    assert row["pass_rate_times_selected_completion_proxy"] == pytest.approx(1 / 3)


def test_duplicate_frequencies_make_exact_score_differ_from_proxy(tmp_path):
    _, data = fixture(tmp_path, cap=3)
    row = task_summary(data, data["tasks"][0])
    assert row["all_sample_completion"] == 0.5
    assert row["pass_rate_times_selected_completion_proxy"] == pytest.approx(4 / 9)
    # Each saved writer answer costs once, while duplicates share editing work.
    assert row["writer_resources"]["tokens_in"]["total"] == 60
    assert row["editor_resources"]["tokens_in"]["total"] == 40


def test_missing_trials_and_infrastructure_are_not_zeros_or_complete_cases(tmp_path):
    _, data = fixture(tmp_path, infra=True)
    row = task_summary(data, data["tasks"][0])
    assert row["selected_completion"] is None
    assert row["selected_trials_resolved"] == 6
    assert row["observed_step_endings"]["infra_error"] == 2
    result = compare_collections([data], bootstrap_samples=20)
    assert result["common_selected_tasks"] == []
    assert result["methods"]["base"]["all_planned_tasks"]["initial_pass_rate"][
        "estimate"
    ] == pytest.approx(4 / 6)
    assert result["cohort_exclusions"][0]["reasons"]["base"] == "unresolved_selection_or_trials"


def test_missing_early_writer_slot_can_make_later_selection_unknown(tmp_path):
    _, data = fixture(tmp_path, missing=(0, 1))
    task = data["tasks"][0]
    assert [p["selection"] for p in task["programs"]] == [
        "initial_failure",
        "unresolved",
        "unresolved",
    ]
    assert task_summary(data, task)["initial_pass_rate"] is None


def test_initial_failures_give_zero_without_inventing_editor_steps(tmp_path):
    _, data = fixture(tmp_path)
    task = data["tasks"][0]
    for parent in task["programs"]:
        parent["initial_status"] = "fail"
        parent["selection"] = "initial_failure"
        for trial in parent["trials"]:
            trial["steps"] = []
    for sample in task["samples"]:
        if sample["candidate_id"]:
            sample["initial_status"] = "fail"
    validate_collection(data)
    row = task_summary(data, task)
    assert row["all_sample_completion"] == 0
    assert row["selected_completion"] is None
    assert row["selected_trials_planned"] == 0
    assert row["editor_resources"]["wall_s"]["total"] == 0


def test_one_family_cannot_produce_an_uncertainty_interval(tmp_path):
    _, data = fixture(tmp_path)
    result = compare_collections([data], bootstrap_samples=20)
    metric = result["methods"]["base"]["common_selected_cohort"]["selected_completion"]
    assert metric == {"estimate": 0.5, "interval": None, "families": 1}


def test_pairing_uses_common_task_cohort_and_preserves_exclusions(tmp_path):
    _, base = fixture(tmp_path / "a")
    other = copy.deepcopy(base)
    other["method"] = "trained"
    # A second task with no initially passing program on either method.
    for data in (base, other):
        extra = copy.deepcopy(data["tasks"][0])
        extra["definition"].update(id="empty_task", family="empty_family")
        for parent in extra["programs"]:
            parent["initial_status"] = "fail"
            parent["selection"] = "initial_failure"
            for trial in parent["trials"]:
                trial["steps"] = []
        for sample in extra["samples"]:
            if sample["candidate_id"]:
                sample["initial_status"] = "fail"
        data["tasks"].append(extra)
    result = compare_collections([base, other], bootstrap_samples=40)
    assert result["common_selected_tasks"] == ["record_store"]
    assert result["cohort_exclusions"][0]["task"] == "empty_task"
    assert result["methods"]["base"]["all_planned_tasks"]["initial_pass_rate"][
        "estimate"
    ] == pytest.approx(1 / 3)
    assert result["methods"]["base"]["common_selected_cohort"]["initial_pass_rate"][
        "estimate"
    ] == pytest.approx(2 / 3)
    assert result["comparisons"][0]["metrics"]["selected_completion"]["estimate"] == 0


def test_family_weighting_does_not_overweight_many_variants(tmp_path):
    _, data = fixture(tmp_path)
    extra = copy.deepcopy(data["tasks"][0])
    extra["definition"].update(id="same_family_variant")
    data["tasks"].append(extra)
    empty = copy.deepcopy(extra)
    empty["definition"].update(id="another_family", family="second_family")
    for parent in empty["programs"]:
        if parent["initial_status"] == "pass":
            for trial in parent["trials"]:
                trial["steps"] = [{**trial["steps"][0], "status": "fail_new"}]
    data["tasks"].append(empty)
    result = compare_collections([data], bootstrap_samples=100)
    metric = result["methods"]["base"]["common_selected_cohort"]["selected_completion"]
    assert metric["estimate"] == 0.25
    assert metric["families"] == 2
    assert metric["interval"] is not None


@pytest.mark.parametrize("change", ["contract", "version", "seed", "duplicate"])
def test_incomparable_or_duplicated_exports_are_rejected(tmp_path, change):
    _, data = fixture(tmp_path)
    other = copy.deepcopy(data)
    other["method"] = "other"
    if change == "contract":
        other["contract"]["writer_temperature"] = 0.111
    elif change == "version":
        other["tasks"][0]["definition"]["version"] = "f" * 64
    elif change == "seed":
        other["generation_seed"] += 1
    else:
        other["method"] = data["method"]
    with pytest.raises(EvaluationError):
        compare_collections([data, other], bootstrap_samples=20)


@pytest.mark.parametrize(
    "mutation",
    ["selection", "sample_order", "membership", "after_failure", "test_counts", "negative_cost"],
)
def test_contradictory_saved_evidence_is_not_repaired(tmp_path, mutation):
    _, data = fixture(tmp_path)
    task = data["tasks"][0]
    if mutation == "selection":
        task["programs"][-1]["selection"] = "selected"
    elif mutation == "sample_order":
        task["samples"].reverse()
    elif mutation == "membership":
        task["programs"][0]["sample_indices"] = [0]
    elif mutation == "after_failure":
        trial = task["programs"][2]["trials"][0]
        trial["steps"].append({**trial["steps"][0], "step": 2})
    elif mutation == "test_counts":
        task["programs"][0]["trials"][0]["steps"][0].update(new_pass=0, new_total=1)
    else:
        task["samples"][0]["writer_cost"]["tokens_in"] = -1
    with pytest.raises(EvaluationError):
        validate_collection(data)


def test_missing_usage_is_disclosed_instead_of_imputed(tmp_path):
    _, data = fixture(tmp_path)
    data["tasks"][0]["samples"][0]["writer_cost"]["tokens_in"] = None
    row = task_summary(data, data["tasks"][0])
    assert row["writer_resources"]["tokens_in"] == {
        "known_subtotal": 50,
        "known_records": 5,
        "missing_records": 1,
        "total": None,
    }


def test_unbounded_program_cap_retains_all_distinct_passes(tmp_path):
    _, data = fixture(tmp_path, cap=None)
    row = task_summary(data, data["tasks"][0])
    assert row["selected_programs"] == 3
    assert row["over_cap_programs"] == 0
    assert row["all_sample_completion"] == 0.5


def test_late_missing_writer_does_not_hide_a_fully_identified_selected_cohort(tmp_path):
    _, data = fixture(tmp_path, cap=2, missing=(5,))
    row = task_summary(data, data["tasks"][0])
    assert not row["selection_unresolved"]
    assert row["selected_completion"] == 0.5
    assert row["initial_pass_rate"] is None
    assert row["all_sample_completion"] is None
