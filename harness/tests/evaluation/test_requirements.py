"""Proposal metric controls: populations, phase costs and checkpoint declarations.

Usage:
    uv run pytest tests/evaluation/test_requirements.py
"""

import csv

import pytest

from harness.evaluation.analysis import compare
from harness.evaluation.plan import _job, prepare, preview
from harness.evaluation.records import EvaluationError
from harness.evaluation.report import write_report

from .helpers import ROOT, saved
from .test_analysis import example
from .test_plan import forbidden, write_plan


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


def test_full_proposal_plan_previews_five_conditions_and_three_trained_seeds(monkeypatch):
    monkeypatch.setattr("harness.evaluation.plan.make_runner", forbidden)
    prepared = prepare(ROOT / "configs/evaluation.proposal.example.yaml")
    result = preview(prepared)
    groups = {m["method_group"] for m in result["method_metadata"]}
    assert groups == {
        "original",
        "maintainability_prompt",
        "correctness_only",
        "static_ranking",
        "downstream_outcomes",
    }
    assert len(result["methods"]) == 11
    assert result["max_edit_checkpoints"] == 3168
    assert result["max_writer_generations"] == 176
    assert result["inference_performed"] is False
    for group in ("correctness_only", "static_ranking", "downstream_outcomes"):
        assert {
            m["training_seed"] for m in result["method_metadata"] if m["method_group"] == group
        } == {11, 22, 33}
    assert prepared.configs[0].writer.prompt_template != prepared.configs[1].writer.prompt_template


def test_declared_training_seed_does_not_change_generation_seed(tmp_path):
    def configure(p):
        p["methods"][1].update(
            writer_model="served-checkpoint", method_group="trained", training_seed=999
        )

    prepared = prepare(write_plan(tmp_path, configure))
    cfg = _job(prepared, 1, 11)
    assert cfg.seed == 11
    assert cfg.writer.backend.model == "served-checkpoint"
    assert preview(prepared)["method_metadata"][1]["training_seed"] == 999


@pytest.mark.parametrize("repeat_seed", [False, True])
def test_replicate_groups_reject_missing_or_duplicate_training_seeds(tmp_path, repeat_seed):
    def configure(p):
        for method in p["methods"]:
            method["method_group"] = "trained"
            if repeat_seed:
                method["training_seed"] = 123

    with pytest.raises(EvaluationError, match="training_seed"):
        prepare(write_plan(tmp_path, configure))


def test_checkpoint_exports_retain_declared_training_seed_and_change_kinds(tmp_path):
    from harness.evaluation.export import export_dataset

    from .helpers import IMAGE

    cfg, _ = saved(tmp_path)
    data = export_dataset(
        cfg, IMAGE, method="replica", purpose="fixture", method_group="trained", training_seed=55
    )
    result = compare([data], bootstrap_samples=20)
    row = result["methods"]["replica"]
    assert row["training_seed"] == 55 and row["method_group"] == "trained"
    paths = write_report(result, tmp_path / "report")
    with paths["checkpoints.csv"].open(newline="") as stream:
        assert all(row["change_kind"] for row in csv.DictReader(stream))
