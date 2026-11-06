"""Matching uses initial correctness and size, never later editing outcomes.

Usage:
    uv run pytest tests/evaluation/test_matching.py
"""

import copy
import json

import pytest

from harness.evaluation.analysis import compare
from harness.evaluation.integrity import verify_report
from harness.evaluation.matching import run_size_match, select_families
from harness.evaluation.records import EvaluationError
from harness.evaluation.report import write_report

from .test_analysis import example


def datasets():
    original, other = example(), example("candidate")
    for data, sizes in ((original, (40, 30)), (other, (50, 33))):
        for sample, size in zip(data["samples"], sizes, strict=True):
            sample["source_metrics"] = {"python_lines": size, "source_lines": size}
    return [original, other]


def test_threshold_and_initial_correctness_select_a_declared_family_subset():
    selection = select_families(
        compare(datasets(), bootstrap_samples=20), "candidate", tolerance=0.2
    )
    assert selection["selected_families"] == ["family_one"]
    assert selection["excluded_families"] == ["family_two"]
    assert selection["membership"][0]["relative_difference"] == 0.2
    assert "reference_initial_not_pass" in selection["membership"][1]["reason"]


def test_editing_failures_do_not_change_membership_or_rule_hash():
    data = datasets()
    before = select_families(compare(data, bootstrap_samples=20), "candidate", tolerance=0.2)
    for sample in data[1]["samples"]:
        for trial in sample["trials"]:
            trial["steps"] = [{**trial["steps"][0], "status": "fail_both"}]
    after = select_families(compare(data, bootstrap_samples=20), "candidate", tolerance=0.2)
    assert before == after


def test_one_ineligible_pair_excludes_its_entire_family():
    data = datasets()
    for record in data:
        for task in record["tasks"]:
            task["family"] = "shared"
    selection = select_families(compare(data, bootstrap_samples=20), "candidate", tolerance=0.2)
    assert selection["selected_families"] == []
    assert selection["membership"][0]["reason"] == "another_pair_in_family_excluded"


def test_every_generation_seed_must_satisfy_matching():
    data = datasets()
    second = copy.deepcopy(data)
    for record in second:
        record["generation_seed"] = 2
    second[1]["samples"][0]["source_metrics"]["python_lines"] = 100
    selection = select_families(
        compare(data + second, bootstrap_samples=20), "candidate", tolerance=0.2
    )
    assert not selection["selected_families"]


@pytest.mark.parametrize("value", [-1, 1.1, float("nan"), True])
def test_invalid_calipers_rejected(value):
    with pytest.raises(EvaluationError):
        select_families(compare(datasets(), bootstrap_samples=20), "candidate", tolerance=value)


def test_sensitivity_report_is_separate_labeled_verifiable_and_replayable(tmp_path):
    result = compare(datasets(), bootstrap_samples=20)
    primary = tmp_path / "primary"
    paths = write_report(result, primary)
    before = {k: p.read_bytes() for k, p in paths.items()}
    target = tmp_path / "matched"
    receipt = run_size_match(primary, "candidate", target, tolerance=0.2)
    assert receipt["status"] == "complete"
    assert verify_report(target)["analysis_recomputed"]
    assert "Size-matched sensitivity" in (target / "report.md").read_text(encoding="utf8")
    assert json.loads((target / "comparison.json").read_text())["size_matched_sensitivity"]
    assert run_size_match(primary, "candidate", target, tolerance=0.2) == receipt
    assert before == {k: p.read_bytes() for k, p in paths.items()}


def test_unknown_sizes_produce_abstention_not_a_zero_score(tmp_path):
    primary = tmp_path / "primary"
    write_report(compare([example(), example("candidate")], bootstrap_samples=20), primary)
    target = tmp_path / "empty"
    result = run_size_match(primary, "candidate", target, tolerance=0.1)
    assert result["status"] == "no_eligible_families"
    assert not (target / "comparison.json").exists()
    assert not verify_report(target)["analysis_recomputed"]
