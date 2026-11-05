"""Checkpoint accounting keeps observed, missing and not-reached outcomes distinct.

Usage:
    uv run pytest tests/evaluation/test_diagnostics.py
"""

import csv

import pytest

from harness.evaluation.analysis import compare
from harness.evaluation.diagnostics import diagnostic_rows
from harness.evaluation.report import write_report

from .test_analysis import example


def test_every_planned_checkpoint_has_one_row_without_counting_unreached_as_failures():
    result = compare([example(), example("candidate")], bootstrap_samples=20)
    rows, failures = diagnostic_rows(result)
    assert len(rows) == 48
    assert sum(r["recorded"] for r in rows) == 36
    assert sum(r["status"] == "not_reached_initial_failure" for r in rows) == 12
    initial = [r for r in failures if r["stage"] == "initial"]
    assert len(initial) == 1 and initial[0]["status"] == "initial_fail"
    assert initial[0]["sequence"] is None
    assert sum(r["status"] == "fail_existing" for r in failures) == 6
    assert sum(r["status"] == "fail_new" for r in failures) == 6
    assert sum(r["preserved_behavior_failure"] is True for r in rows) == 6
    assert all(r["preserved_behavior_failure"] is None for r in rows if not r["recorded"])


@pytest.mark.parametrize(
    "status,later",
    [
        ("missing", "not_reached_after_missing"),
        ("infra_error", "not_reached_after_infra_error"),
        ("budget_exhausted", "not_reached_after_failure"),
        ("fail_both", "not_reached_after_failure"),
    ],
)
def test_first_stop_is_preserved_and_later_changes_are_not_fabricated(status, later):
    data = example("candidate")
    trial = data["samples"][0]["trials"][0]
    trial["steps"] = (
        []
        if status == "missing"
        else [
            {
                **trial["steps"][0],
                "status": status,
                "end_reason": "fixture_stop",
                "infra_cause": "fixture_infra" if status == "infra_error" else None,
            }
        ]
    )
    rows, failures = diagnostic_rows(compare([data], bootstrap_samples=20))
    first, second = rows[:2]
    assert first["status"] == status and second["status"] == later
    assert not second["recorded"]
    assert second["output_source_hash"] is None
    assert first["recorded"] is (status != "missing")
    assert failures[0]["status"] == status
    assert failures[0]["step"] == 1
    if status != "fail_both":
        assert first["new_feature_failure"] is None
    else:
        assert first["new_feature_failure"] is True
        assert first["preserved_behavior_failure"] is True


def test_source_lineage_is_reported_only_when_saved():
    data = example("candidate")
    trial = data["samples"][0]["trials"][0]
    trial["steps"][0]["output_blob"] = "b" * 64
    trial["steps"][1]["output_blob"] = "c" * 64
    rows, _ = diagnostic_rows(compare([data], bootstrap_samples=20))
    assert rows[0]["input_source_hash"] == "a" * 64
    assert rows[1]["input_source_hash"] == "b" * 64
    assert rows[1]["output_source_hash"] == "c" * 64
    assert rows[2]["input_source_hash"] == "a" * 64
    assert rows[3]["input_source_hash"] is None


def test_unresolved_initial_is_not_a_code_failure():
    data = example()
    data["samples"][1]["initial_status"] = "unresolved"
    rows, failures = diagnostic_rows(compare([data], bootstrap_samples=20))
    assert rows[-1]["status"] == "not_reached_initial_unresolved"
    assert failures[-1]["status"] == "initial_unresolved"


def test_exports_include_complete_ledger_and_header_only_failure_table(tmp_path):
    data = example("candidate")
    for sample in data["samples"]:
        for trial in sample["trials"]:
            for step in trial["steps"]:
                step["status"] = "success"
    result = compare([data], bootstrap_samples=20)
    paths = write_report(result, tmp_path)
    with paths["checkpoints.csv"].open(newline="") as stream:
        assert len(list(csv.DictReader(stream))) == 24
    with paths["failures.csv"].open(newline="") as stream:
        assert list(csv.DictReader(stream)) == []
    assert result["methods"]["candidate"]["metrics"]["change_completion"]["estimate"] == 1
