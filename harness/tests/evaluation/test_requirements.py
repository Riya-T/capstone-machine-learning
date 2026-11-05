"""Proposal metric controls: populations, phase costs and checkpoint declarations.

Usage:
    uv run pytest tests/evaluation/test_requirements.py
"""

import csv

from harness.evaluation.analysis import compare
from harness.evaluation.report import write_report

from .helpers import saved
from .test_analysis import example


def test_failed_initial_source_is_in_all_generated_comment_measurements():
    data = example()
    data["samples"][0]["source_metrics"] = dict(
        source_lines=10,
        python_documentation_density=0.2,
        python_comment_lines=2,
        python_docstring_lines=0,
    )
    data["samples"][1]["source_metrics"] = dict(
        source_lines=30,
        python_documentation_density=0.8,
        python_comment_lines=24,
        python_docstring_lines=0,
    )
    row = compare([data], bootstrap_samples=20)["methods"]["original"]
    all_fields = row["all_generated_source_descriptives"]["fields"]
    passing = row["initial_source_descriptives"]["fields"]
    assert all_fields["source_lines"]["family_weighted_known_mean"] == 20
    assert all_fields["python_documentation_density"]["family_weighted_known_mean"] == 0.5
    assert passing["python_documentation_density"]["family_weighted_known_mean"] == 0.2
    assert row["metrics"]["change_completion"]["estimate"] == 0.25


def test_phase_costs_add_up_and_initial_failures_do_not_get_editing_cost():
    row = compare([example()], bootstrap_samples=20)["methods"]["original"]
    phases = row["resource_breakdown"]["all_generated"]["phases"]
    passing = row["resource_breakdown"]["initially_correct"]["phases"]
    assert phases["writing"]["costs"]["tokens_in"]["known_total"] == 200
    assert phases["editing"]["costs"]["tokens_in"]["known_total"] == 120
    assert passing["writing"]["costs"]["tokens_in"]["known_total"] == 100
    assert passing["editing"] == phases["editing"]
    for key in ("tokens_in", "tokens_out", "wall_s"):
        assert (
            sum(p["costs"][key]["known_total"] for p in phases.values())
            == (row["costs"][key]["known_total"])
        )


def test_unknown_costs_and_parse_failure_source_are_not_invented():
    data = example()
    data["samples"][1].update(initial_status="parse_failure", candidate_id=None)
    data["samples"][0]["writer_cost"]["tokens_in"] = None
    data["samples"][0]["trials"][0]["steps"] = []
    row = compare([data], bootstrap_samples=20)["methods"]["original"]
    all_costs = row["resource_breakdown"]["all_generated"]
    assert all_costs["unresolved_trajectories"] == 1
    assert all_costs["phases"]["writing"]["costs"]["tokens_in"]["missing_records"] == 1
    assert (
        row["all_generated_source_descriptives"]["fields"]["source_lines"]["missing_samples"] == 2
    )


def test_population_and_phase_exports_match_analysis(tmp_path):
    result = compare([example()], bootstrap_samples=20)
    paths = write_report(result, tmp_path)
    with paths["resources.csv"].open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 12
    assert {r["population"] for r in rows} == {"all_generated", "initially_correct"}
    with paths["source_descriptives.csv"].open(newline="") as stream:
        assert len(list(csv.DictReader(stream))) == 6
    report = paths["report.md"].read_text(encoding="utf8")
    assert "original / all generated" in report and "original / initially correct" in report


def test_edit_size_is_exported_from_verified_blobs_without_affecting_scores(tmp_path):
    _, data = saved(tmp_path)
    assert data["samples"][0]["trials"][0]["steps"][0]["change_size"]["files_changed"] == 0
    result = compare([data], bootstrap_samples=20)
    paths = write_report(result, tmp_path / "report")
    with paths["checkpoints.csv"].open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert all(row["files_changed"] == row["python_lines_added"] == "0" for row in rows)
    assert result["methods"]["original"]["metrics"]["change_completion"]["estimate"] == 1
