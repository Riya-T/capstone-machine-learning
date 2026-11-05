"""Exercise the saved-only extension commands through the public harness CLI.

Usage:
    uv run pytest tests/evaluation/test_extension_cli.py
"""

import json

import pytest

from harness.__main__ import main
from harness.evaluation.analysis import compare
from harness.evaluation.report import write_report

from .test_plan import forbidden
from .test_seeds import seed_data


def test_saved_only_commands_interoperate_without_models_or_containers(tmp_path, monkeypatch):
    data = seed_data()
    for dataset in data:
        for sample in dataset["samples"]:
            sample["source_metrics"] = dict(python_lines=40, source_lines=40)
    primary = tmp_path / "primary"
    write_report(compare(data, bootstrap_samples=20), primary)
    before = (primary / "comparison.json").read_bytes()
    monkeypatch.setattr("harness.evaluation.plan.make_runner", forbidden)
    monkeypatch.setattr("harness.evaluation.plan.collect", forbidden)
    assert (
        main(["evaluation-seeds", "--report", str(primary), "--out", str(tmp_path / "seeds")]) == 0
    )
    assert (
        main(
            [
                "evaluation-size-match",
                "--report",
                str(primary),
                "--method",
                "seed11",
                "--relative-tolerance",
                "0.2",
                "--out",
                str(tmp_path / "matched"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "evaluation-review",
                "init",
                "--report",
                str(primary),
                "--out",
                str(tmp_path / "review"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "evaluation-review",
                "compile",
                "--pack",
                str(tmp_path / "review"),
                "--annotations",
                str(tmp_path / "review/annotations.template.csv"),
                "--out",
                str(tmp_path / "review-summary"),
            ]
        )
        == 0
    )
    for name in ("seeds", "matched", "review", "review-summary"):
        assert main(["evaluation-verify", "--report", str(tmp_path / name)]) == 0
    assert before == (primary / "comparison.json").read_bytes()
    summary = json.loads((tmp_path / "review-summary/analysis.json").read_text())
    assert summary["training_labels"] is None
    assert summary["case_counts"].get("reviewed", 0) == 0


def test_plot_command_is_offline_and_preserves_primary(tmp_path, monkeypatch):
    pytest.importorskip("matplotlib")
    primary = tmp_path / "primary"
    write_report(compare(seed_data(), bootstrap_samples=20), primary)
    before = (primary / "comparison.json").read_bytes()
    monkeypatch.setattr("harness.evaluation.plan.make_runner", forbidden)
    monkeypatch.setattr("harness.evaluation.plan.collect", forbidden)
    assert (
        main(["evaluation-plots", "--report", str(primary), "--out", str(tmp_path / "plots")]) == 0
    )
    assert before == (primary / "comparison.json").read_bytes()
    assert main(["evaluation-verify", "--report", str(tmp_path / "plots")]) == 0
