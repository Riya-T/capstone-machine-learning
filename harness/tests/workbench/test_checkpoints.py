"""Check observed-seed comparisons, coverage abstention and source-bound replay.

Usage: python -m pytest tests/workbench/test_checkpoints.py
All checkpoint outcomes here are authored software fixtures.
"""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from harness.evaluation.records import EvaluationError
from harness.workbench.analysis import compare_collections
from harness.workbench.checkpoints import options, run_summary, summarize
from harness.workbench.records import selection
from harness.workbench.report import encoded, verify_report, write_report
from tests.workbench.helpers import fixture


def example(tmp_path):
    _, base = fixture(tmp_path)
    datasets = [base]
    for seed, digit, score in ((42, "a", 1), (43, "b", 2)):
        data = copy.deepcopy(base)
        data.update(
            method=f"trained_{seed}",
            method_group="trained",
            training_seed=seed,
            writer_identity=digit * 64,
        )
        for trial in data["tasks"][0]["programs"][2]["trials"]:
            first = {**trial["steps"][0], "status": "success"}
            trial["steps"] = [
                first,
                {
                    **first,
                    "step": 2,
                    "change_id": next(
                        s["changes"][1]
                        for s in data["tasks"][0]["definition"]["sequences"]
                        if s["id"] == trial["sequence"]
                    ),
                    "status": "fail_new" if score == 1 else "success",
                },
            ]
        datasets.append(data)
    return compare_collections(datasets, reference="base", bootstrap_samples=30)


def test_group_summary_keeps_individual_checkpoints_and_does_not_inflate_family_count(tmp_path):
    result = summarize(example(tmp_path), options(expected_seeds={"trained": [42, 43]}))
    metric = result["groups"]["trained"]["metrics"]["selected_completion"]
    assert metric["estimate"] == 0.875
    assert metric["checkpoint_min"] == 0.75 and metric["checkpoint_max"] == 1
    assert metric["observed_checkpoints"] == 2
    assert metric["contributing_families"] == 1
    assert metric["interval"] is None
    assert result["training_labels"] is None
    assert not result["roster_verified"]  # A historical declaration is not preregistration.
    assert result["declared_roster_checked"] and result["declared_roster_complete"]


def test_a_worse_checkpoint_is_retained_instead_of_selecting_the_best_seed(tmp_path):
    source = example(tmp_path)
    raw = source["source_datasets"]
    for parent in raw[-1]["tasks"][0]["programs"]:
        if parent["selection"] == "selected":
            for trial in parent["trials"]:
                trial["steps"] = [{**trial["steps"][0], "status": "fail_new"}]
    result = summarize(compare_collections(raw, bootstrap_samples=30), options())
    trained = result["groups"]["trained"]
    assert trained["metrics"]["selected_completion"]["estimate"] == 0.375
    assert trained["completion_directions_vs_reference_group"] == {
        "advantage": 1,
        "disadvantage": 1,
        "tie": 0,
        "unknown": 0,
    }


def test_missing_declared_seed_blocks_group_and_pair_estimates_not_the_observed_rows(tmp_path):
    result = summarize(example(tmp_path), options(expected_seeds={"trained": [42, 43, 44]}))
    metric = result["groups"]["trained"]["metrics"]["selected_completion"]
    assert metric["estimate"] is None and metric["observed_only_estimate"] == 0.875
    assert result["declared_roster_coverage"][0]["missing"] == [44]
    pair = next(r for r in result["comparisons"] if r["metric"] == "selected_completion")
    assert pair["difference"] is None
    assert pair["observed_only_difference"] == 0.375
    assert len({r["method"] for r in result["seeds"]}) == 3


@pytest.mark.parametrize("problem", ["same_seed", "missing_seed", "same_writer_identity"])
def test_ambiguous_group_provenance_is_rejected(tmp_path, problem):
    source = example(tmp_path)
    data = source["source_datasets"]
    if problem == "same_seed":
        data[-1]["training_seed"] = 42
    elif problem == "missing_seed":
        data[-1]["training_seed"] = None
    else:
        data[-1]["writer_identity"] = data[-2]["writer_identity"]
    with pytest.raises(EvaluationError):
        summarize(compare_collections(data, bootstrap_samples=30), options())


@pytest.mark.parametrize(
    "roster",
    [
        {"trained": [42, 42]},
        {"trained": []},
        {"../path": [42]},
        {"trained": [True]},
        {"trained": [-1]},
    ],
)
def test_invalid_expected_seed_rosters_are_not_silently_normalized(roster):
    with pytest.raises(EvaluationError):
        options(expected_seeds=roster)


def test_checkpoint_summary_verifies_without_the_original_report_directory(tmp_path, monkeypatch):
    source = example(tmp_path)
    write_report(source, tmp_path / "source")
    run_summary(tmp_path / "source", tmp_path / "summary", expected_seeds={"trained": [42, 43]})
    before = (tmp_path / "source/comparison.json").read_bytes()
    read_bytes = Path.read_bytes

    def local_only(path):
        if path.is_relative_to(tmp_path / "source"):
            pytest.fail("A derived bundle must not require its original report directory")
        return read_bytes(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", local_only)
        assert verify_report(tmp_path / "summary")["analysis_recomputed"]
    assert "SYNTHETIC FIXTURE" in (tmp_path / "summary/report.html").read_text()
    run_summary(tmp_path / "source", tmp_path / "summary", expected_seeds={"trained": [43, 42]})
    assert (tmp_path / "source/comparison.json").read_bytes() == before


def test_rehashed_false_group_result_cannot_pass_recomputation(tmp_path):
    write_report(example(tmp_path), tmp_path / "source")
    run_summary(tmp_path / "source", tmp_path / "summary")
    path = tmp_path / "summary/analysis.json"
    saved = json.loads(path.read_bytes())
    saved["groups"]["trained"]["metrics"]["selected_completion"]["estimate"] = 1
    path.write_bytes(encoded(saved))
    manifest = json.loads((tmp_path / "summary/manifest.json").read_bytes())
    manifest["files"]["analysis.json"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path / "summary/manifest.json").write_bytes(encoded(manifest))
    with pytest.raises(EvaluationError, match="recompute"):
        verify_report(tmp_path / "summary")


def test_missing_entire_expected_group_remains_a_coverage_failure(tmp_path):
    write_report(example(tmp_path), tmp_path / "source")
    receipt = run_summary(
        tmp_path / "source", tmp_path / "summary", expected_seeds={"absent": [99]}
    )
    assert not receipt["analysis_complete"]
    result = json.loads((tmp_path / "summary/analysis.json").read_bytes())
    assert "absent" not in result["groups"]
    assert result["declared_roster_coverage"][0]["missing"] == [99]


def test_an_unexpected_seed_cannot_be_dropped_to_improve_the_group(tmp_path):
    result = summarize(example(tmp_path), options(expected_seeds={"trained": [42]}))
    assert result["declared_roster_coverage"][0]["extra"] == [43]
    assert result["groups"]["trained"]["metrics"]["selected_completion"]["estimate"] is None
    assert {r["training_seed"] for r in result["seeds"] if r["group"] == "trained"} == {42, 43}


def test_wrong_roster_container_type_is_rejected_even_when_empty():
    with pytest.raises(EvaluationError):
        options(expected_seeds=[])


def test_multi_group_roster_round_trip_is_order_independent(tmp_path):
    write_report(example(tmp_path), tmp_path / "source")
    run_summary(
        tmp_path / "source",
        tmp_path / "summary",
        expected_seeds={"zz": [99], "trained": [43, 42], "aa": [1]},
    )
    assert verify_report(tmp_path / "summary")["verified"]
    run_summary(
        tmp_path / "source",
        tmp_path / "summary",
        expected_seeds={"aa": [1], "trained": [42, 43], "zz": [99]},
    )


def test_editing_gain_and_initial_correctness_loss_are_both_retained(tmp_path):
    _, base = fixture(tmp_path)
    trained = copy.deepcopy(base)
    trained.update(
        method="trained", method_group="trained", training_seed=42, writer_identity="a" * 64
    )
    task = trained["tasks"][0]
    rejected = task["programs"][2]
    rejected["initial_status"] = "fail"
    for trial in rejected["trials"]:
        trial["steps"] = []
    for sample in task["samples"]:
        if sample["candidate_id"] == rejected["candidate_id"]:
            sample["initial_status"] = "fail"
    states = selection(task, trained["contract"]["max_programs"])
    for parent in task["programs"]:
        parent["selection"] = states[parent["candidate_id"]]
    result = summarize(compare_collections([base, trained], bootstrap_samples=20), options())
    metrics = result["groups"]["trained"]["metrics"]
    assert metrics["selected_completion"]["estimate"] == 1
    assert metrics["initial_pass_rate"]["estimate"] == 0.5
    differences = {r["metric"]: r["difference"] for r in result["comparisons"]}
    assert differences["selected_completion"] == 0.5
    assert differences["initial_pass_rate"] == pytest.approx(-1 / 6)
