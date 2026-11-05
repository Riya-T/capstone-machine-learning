"""Offline CLI replay, malformed inputs and protection of original input exports.

Usage:
    uv run pytest tests/evaluation/test_cli.py
"""

import json

from harness.__main__ import main

from .test_analysis import example
from .test_plan import forbidden


def test_report_command_uses_only_exported_json_and_replays_identically(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr("harness.evaluation.plan.make_runner", forbidden)
    monkeypatch.setattr("harness.evaluation.plan.collect", forbidden)
    sources = []
    for method in ("original", "candidate"):
        p = tmp_path / (method + ".json")
        p.write_text(json.dumps(example(method)), encoding="utf8")
        sources.append(p)
    before = [p.read_bytes() for p in sources]
    args = [
        "evaluation-report",
        "--input",
        *map(str, sources),
        "--reference",
        "original",
        "--bootstrap-samples",
        "100",
        "--out",
        str(tmp_path / "reports"),
    ]
    assert main(args) == 0
    paths = json.loads(capsys.readouterr().out)
    assert "SYNTHETIC FIXTURE" in (tmp_path / "reports/report.md").read_text(encoding="utf8")
    result = (tmp_path / "reports/comparison.json").read_bytes()
    assert main(args) == 0
    assert (tmp_path / "reports/comparison.json").read_bytes() == result
    assert [p.read_bytes() for p in sources] == before
    assert set(paths) == {"comparison.json", "summary.csv", "trajectories.csv", "report.md"}


def test_report_command_cannot_overwrite_its_input(tmp_path, capsys):
    source = tmp_path / "comparison.json"
    source.write_text(json.dumps(example()), encoding="utf8")
    before = source.read_bytes()
    assert main(["evaluation-report", "--input", str(source), "--out", str(tmp_path)]) == 2
    assert "overwrite" in capsys.readouterr().err
    assert source.read_bytes() == before


def test_malformed_export_gives_clear_error_without_partial_report(tmp_path, capsys):
    source = tmp_path / "broken.json"
    source.write_text("{not json", encoding="utf8")
    out = tmp_path / "reports"
    assert main(["evaluation-report", "--input", str(source), "--out", str(out)]) == 2
    assert "Evaluation error" in capsys.readouterr().err
    assert not out.exists()
