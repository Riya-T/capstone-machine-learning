"""Observed checkpoint summaries retain weak seeds and use families as the resampling unit.

Usage:
    uv run pytest tests/evaluation/test_seeds.py
"""

import json

import pytest

from harness.evaluation.analysis import compare
from harness.evaluation.integrity import verify_report
from harness.evaluation.records import EvaluationError
from harness.evaluation.report import write_report
from harness.evaluation.seeds import run_seed_summary, summarize_seeds

from .test_analysis import example


def seed_data():
    data = [example()]
    for number in (11, 22, 33):
        record = example("seed" + str(number))
        record.update(
            method_group="trained", training_seed=number, writer_identity=f"{number:064x}"
        )
        if number in (22, 33):
            for trial in record["samples"][0]["trials"]:
                if number == 22:
                    trial["steps"][-1]["status"] = "fail_new"
                else:
                    trial["steps"] = [{**trial["steps"][0], "status": "fail_new"}]
        data.append(record)
    return data


def test_fixed_checkpoint_summary_matches_hand_calculation_and_keeps_tie():
    result = summarize_seeds(compare(seed_data(), bootstrap_samples=30))
    group = result["groups"]["trained"]
    metric = group["metrics"]["change_completion"]
    assert metric["estimate"] == 0.5
    assert metric["checkpoint_min"] == 0.25 and metric["checkpoint_max"] == 0.75
    assert metric["contributing_families"] == 2
    assert metric["observed_checkpoints"] == 3
    assert group["completion_directions_vs_reference_group"] == dict(
        advantage=2, tie=1, disadvantage=0, unknown=0
    )
    pair = next(p for p in result["comparisons"] if p["metric"] == "change_completion")
    assert pair["difference"] == 0.25 and pair["paired_families"] == 2
    assert result["bootstrap"]["conditioned_on_observed_checkpoints"]
    assert len(result["seeds"]) == 28


def test_unresolved_seed_blocks_primary_group_estimate_instead_of_being_dropped():
    data = seed_data()
    data[2]["samples"][0]["trials"][0]["steps"] = []
    group = summarize_seeds(compare(data, bootstrap_samples=20))["groups"]["trained"]
    assert group["metrics"]["change_completion"]["estimate"] is None
    assert group["metrics"]["change_completion"]["interval"] is None
    assert group["metrics"]["change_completion"]["unknown_checkpoint_estimates"] == 1
    assert group["completion_directions_vs_reference_group"]["unknown"] == 1
    assert len(group["members"]) == 3


@pytest.mark.parametrize("field", ["training_seed", "writer_identity"])
def test_declared_replicates_cannot_duplicate_or_omit_identity(field):
    data = seed_data()
    data[2][field] = data[1][field]
    with pytest.raises(EvaluationError):
        summarize_seeds(compare(data, bootstrap_samples=20))


def test_more_seeds_and_repetitions_do_not_create_more_bootstrap_families():
    data = seed_data()
    for record in data:
        for task in record["tasks"]:
            task["family"] = "one_family"
    metric = summarize_seeds(compare(data, bootstrap_samples=20))["groups"]["trained"]["metrics"][
        "change_completion"
    ]
    assert metric["contributing_families"] == 1 and metric["interval"] is None


def test_seed_report_is_immutable_replayable_and_keeps_source_hash(tmp_path):
    result = compare(seed_data(), bootstrap_samples=20)
    primary = tmp_path / "primary"
    source = write_report(result, primary)["comparison.json"].read_bytes()
    paths = run_seed_summary(primary, tmp_path / "seeds")
    assert run_seed_summary(primary, tmp_path / "seeds") == paths
    assert (primary / "comparison.json").read_bytes() == source
    summary = json.loads((tmp_path / "seeds/analysis.json").read_text())
    assert summary["source_report_sha256"]
    assert not verify_report(tmp_path / "seeds")["analysis_recomputed"]
