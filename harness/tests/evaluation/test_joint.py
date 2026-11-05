"""Aligned pass cohorts, abstention, family weighting, and immutable saved-only replay.

Usage:
    uv run pytest tests/evaluation/test_joint.py
"""

import copy
import json

import pytest

from harness.__main__ import main
from harness.evaluation.analysis import compare
from harness.evaluation.integrity import verify_report
from harness.evaluation.joint import joint_pass, run_joint_pass
from harness.evaluation.records import EvaluationError
from harness.evaluation.report import write_report

from .test_analysis import example
from .test_plan import forbidden


def metric(summary, name="change_completion"):
    return next(row for row in summary["metrics"] if row["metric"] == name)


def change_initial(sample, status):
    sample["initial_status"] = status
    if status == "parse_failure":
        sample["candidate_id"] = None
    for trial in sample["trials"]:
        trial["steps"] = []


def test_joint_pass_uses_same_cells_not_separate_passing_populations():
    a, b = example(), example("candidate")
    for data in (a, b):
        for task in data["tasks"]:
            task["family"] = "common"
    primary = compare([a, b], bootstrap_samples=20)
    old = primary["methods"]
    assert old["candidate"]["metrics"]["change_completion_initially_correct"]["estimate"] == 0.75
    assert old["original"]["metrics"]["change_completion_initially_correct"]["estimate"] == 0.5
    before = copy.deepcopy(primary)
    summary = joint_pass(primary, "candidate")
    row = metric(summary)
    assert row["reference_estimate"] == 0.5 and row["method_estimate"] == 1
    assert row["difference"] == 0.5 and row["interval_low"] is None
    assert summary["counts"] == dict(
        planned_pairs=2,
        included_pairs=1,
        excluded_initial_failure=1,
        unknown_eligibility=0,
        included_families=1,
    )
    assert primary == before


def test_cohort_membership_does_not_depend_on_editing_outcomes():
    a, b = example(), example("candidate")
    before = joint_pass(compare([a, b], bootstrap_samples=20), "candidate")
    for trial in b["samples"][0]["trials"]:
        trial["steps"][0]["status"] = "fail_new"
        trial["steps"] = trial["steps"][:1]
    after = joint_pass(compare([a, b], bootstrap_samples=20), "candidate")
    assert before["parent_pairs"] == after["parent_pairs"]
    assert metric(after)["difference"] == -0.5


def test_unresolved_eligibility_blocks_estimates_even_with_observed_pairs():
    a, b = example(), example("candidate")
    change_initial(a["samples"][1], "unresolved")
    summary = joint_pass(compare([a, b], bootstrap_samples=20), "candidate")
    assert summary["status"] == "incomplete_eligibility"
    assert summary["counts"]["included_pairs"] == 1
    assert summary["counts"]["unknown_eligibility"] == 1
    assert all(
        row["difference"] is None and not row["coverage_complete"] for row in summary["metrics"]
    )


def test_known_failure_proves_exclusion_even_if_other_parent_is_unknown():
    a, b = example(), example("candidate")
    change_initial(b["samples"][1], "unresolved")
    summary = joint_pass(compare([a, b], bootstrap_samples=20), "candidate")
    assert summary["status"] == "complete"
    assert summary["counts"]["unknown_eligibility"] == 0
    assert summary["parent_pairs"][1]["eligibility"] == "excluded_initial_failure"


@pytest.mark.parametrize("kind", ["missing", "infra_error"])
def test_unresolved_edits_are_not_treated_as_zero_or_ignored(kind):
    a, b = example(), example("candidate")
    trial = b["samples"][0]["trials"][0]
    if kind == "missing":
        trial["steps"].pop()
    else:
        trial["steps"][-1]["status"] = kind
    summary = joint_pass(compare([a, b], bootstrap_samples=20), "candidate")
    assert summary["status"] == "incomplete_outcomes"
    assert all(row["difference"] is None for row in summary["metrics"])


def test_no_joint_parents_has_no_zero_score_and_keeps_missing_edits_missing():
    a, b = example(), example("candidate")
    change_initial(b["samples"][0], "fail")
    result = compare([a, b], bootstrap_samples=20)
    before = copy.deepcopy(result)
    summary = joint_pass(result, "candidate")
    assert summary["status"] == "no_jointly_correct_parents"
    assert summary["counts"]["included_pairs"] == 0
    assert all(row["difference"] is None for row in summary["metrics"])
    assert result == before


def test_multiple_generation_seeds_remain_inside_families():
    a, b = example(), example("candidate")
    second_a, second_b = copy.deepcopy(a), copy.deepcopy(b)
    second_a["generation_seed"] = second_b["generation_seed"] = 2
    summary = joint_pass(compare([a, b, second_a, second_b], bootstrap_samples=20), "candidate")
    assert summary["counts"]["included_pairs"] == 2
    assert metric(summary)["paired_families"] == 1
    assert metric(summary)["interval_low"] is None


def test_pair_specific_seed_subsets_are_aligned():
    a, b = example(), example("candidate")
    second_a, second_b = copy.deepcopy(a), copy.deepcopy(b)
    second_a["generation_seed"] = second_b["generation_seed"] = 2
    change_initial(second_b["samples"][0], "parse_failure")
    summary = joint_pass(compare([a, b, second_a, second_b], bootstrap_samples=20), "candidate")
    assert summary["counts"]["included_pairs"] == 1
    assert metric(summary)["difference"] == 0.5


def test_family_weighting_does_not_treat_related_tasks_as_independent():
    a, b = example(), example("candidate")
    a["samples"][1] = copy.deepcopy(b["samples"][1])
    for trial in a["samples"][1]["trials"]:
        trial["steps"][-1]["status"] = "success"
    # Family one favors the method by .5; family two favors reference by .5.
    for data in (a, b):
        extra_task = copy.deepcopy(data["tasks"][0])
        extra_task["id"] = "related"
        data["tasks"].append(extra_task)
        sample = copy.deepcopy(data["samples"][0])
        sample["task"] = "related"
        data["samples"].append(sample)
    summary = joint_pass(compare([a, b], bootstrap_samples=40), "candidate")
    assert summary["counts"]["included_pairs"] == 3
    assert metric(summary)["paired_families"] == 2
    assert metric(summary)["difference"] == 0


@pytest.mark.parametrize("method", ["original", "absent"])
def test_invalid_comparison_methods_are_rejected(method):
    with pytest.raises(EvaluationError, match="non-reference"):
        joint_pass(compare([example(), example("candidate")], bootstrap_samples=20), method)


def test_saved_cli_replays_identically_without_any_backend_or_source_write(tmp_path, monkeypatch):
    source = tmp_path / "primary"
    write_report(compare([example(), example("candidate")], bootstrap_samples=20), source)
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    monkeypatch.setattr("harness.evaluation.plan.collect", forbidden)
    monkeypatch.setattr("harness.evaluation.plan.make_runner", forbidden)
    output = tmp_path / "joint"
    args = [
        "evaluation-joint-pass",
        "--report",
        str(source),
        "--method",
        "candidate",
        "--out",
        str(output),
    ]
    assert main(args) == 0
    rendered = {p.name: p.read_bytes() for p in output.iterdir()}
    assert main(args) == 0
    assert rendered == {p.name: p.read_bytes() for p in output.iterdir()}
    assert before == {p.name: p.read_bytes() for p in source.iterdir()}
    receipt = verify_report(output)
    assert receipt["kind"] == "joint_pass" and not receipt["analysis_recomputed"]
    saved = json.loads((output / "analysis.json").read_bytes())
    assert saved["source_report_sha256"] and not saved["roster_verified"]
    assert "SYNTHETIC FIXTURE" in (output / "report.md").read_text(encoding="utf8")


def test_empty_cohort_cli_saves_abstention_and_exits_three(tmp_path):
    a, b = example(), example("candidate")
    change_initial(b["samples"][0], "fail")
    source, output = tmp_path / "primary", tmp_path / "abstention"
    write_report(compare([a, b], bootstrap_samples=20), source)
    assert (
        main(
            [
                "evaluation-joint-pass",
                "--report",
                str(source),
                "--method",
                "candidate",
                "--out",
                str(output),
            ]
        )
        == 3
    )
    saved = json.loads((output / "analysis.json").read_bytes())
    assert saved["status"] == "no_jointly_correct_parents"
    assert verify_report(output)["checksums_valid"]


def test_existing_source_bundle_cannot_be_overwritten(tmp_path):
    write_report(compare([example(), example("candidate")], bootstrap_samples=20), tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises(EvaluationError, match="overwrite"):
        run_joint_pass(tmp_path, "candidate", tmp_path)
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


def test_budget_stop_is_a_resolved_failure_without_fabricated_regressions():
    a, b = example(), example("candidate")
    for trial in b["samples"][0]["trials"]:
        trial["steps"] = [{**trial["steps"][0], "status": "budget_exhausted"}]
    summary = joint_pass(compare([a, b], bootstrap_samples=20), "candidate")
    assert summary["status"] == "complete"
    assert metric(summary)["method_estimate"] == 0
    rate = metric(summary, "regression_rate_reached")
    assert rate["method_estimate"] is None and rate["difference"] is None
    assert rate["paired_families"] == 0


def test_nested_size_matched_report_is_rejected():
    result = compare([example(), example("candidate")], bootstrap_samples=20)
    result["size_matched_sensitivity"] = True
    with pytest.raises(EvaluationError, match="primary report"):
        joint_pass(result, "candidate")
