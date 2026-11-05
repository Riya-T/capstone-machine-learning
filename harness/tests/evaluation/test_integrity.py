"""Saved-report verification detects damage and inconsistent claimed scores offline.

Usage:
    uv run pytest tests/evaluation/test_integrity.py
"""

import hashlib
import json
from pathlib import Path

import pytest

from harness.__main__ import main
from harness.evaluation.analysis import compare
from harness.evaluation.integrity import verify_report
from harness.evaluation.records import EvaluationError
from harness.evaluation.report import write_report

from .test_analysis import example
from .test_plan import forbidden


def bundle(path):
    return write_report(compare([example(), example("candidate")], bootstrap_samples=20), path)


def update_checksum(path, name):
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][name] = hashlib.sha256((path / name).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))


def test_verify_is_read_only_and_makes_no_model_or_container_calls(tmp_path, monkeypatch, capsys):
    paths = bundle(tmp_path)
    before = {k: p.read_bytes() for k, p in paths.items()}
    monkeypatch.setattr("harness.evaluation.plan.make_runner", forbidden)
    monkeypatch.setattr("harness.evaluation.plan.collect", forbidden)
    assert main(["evaluation-verify", "--report", str(tmp_path)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["checksums_valid"] and receipt["analysis_recomputed"]
    assert set(receipt["files_verified"]) == set(paths) - {"manifest.json"}
    assert before == {k: p.read_bytes() for k, p in paths.items()}


@pytest.mark.parametrize("mode", ["changed", "missing"])
def test_damage_is_reported_without_repair(tmp_path, mode):
    paths = bundle(tmp_path)
    if mode == "changed":
        paths["summary.csv"].write_bytes(b"changed")
    else:
        paths["summary.csv"].unlink()
    with pytest.raises(EvaluationError, match="summary.csv"):
        verify_report(tmp_path)
    assert (
        (paths["summary.csv"].read_bytes() == b"changed")
        if mode == "changed"
        else (not paths["summary.csv"].exists())
    )


def test_rehashed_wrong_scores_still_fail_analysis_recomputation(tmp_path):
    paths = bundle(tmp_path)
    saved = json.loads(paths["comparison.json"].read_text())
    saved["methods"]["original"]["metrics"]["change_completion"]["estimate"] = 0.99
    paths["comparison.json"].write_text(json.dumps(saved))
    update_checksum(tmp_path, "comparison.json")
    with pytest.raises(EvaluationError, match="Recomputed analysis differs"):
        verify_report(tmp_path)
    receipt = verify_report(tmp_path, recompute=False)
    assert receipt["checksums_valid"] and not receipt["analysis_recomputed"]


@pytest.mark.parametrize("name", ["../outside.json", "C:\\secret.json", "manifest.json", "odd.txt"])
def test_manifest_cannot_read_paths_or_unknown_files(tmp_path, name):
    paths = bundle(tmp_path)
    manifest = json.loads(paths["manifest.json"].read_text())
    manifest["files"][name] = "a" * 64
    paths["manifest.json"].write_text(json.dumps(manifest))
    with pytest.raises(EvaluationError, match="Unsafe or unsupported"):
        verify_report(tmp_path)


@pytest.mark.parametrize(
    "manifest",
    [
        [],
        {},
        {"schema_version": True, "complete": True},
        {"schema_version": 1, "complete": False},
        {"schema_version": 1, "complete": True, "files": {}},
    ],
)
def test_invalid_manifest_is_not_a_complete_report(tmp_path, manifest):
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(EvaluationError):
        verify_report(tmp_path)


def test_legacy_manifest_bundle_without_new_outputs_still_verifies(tmp_path):
    paths = bundle(tmp_path)
    legacy_names = {"comparison.json", "summary.csv", "trajectories.csv", "report.md"}
    manifest = json.loads(paths["manifest.json"].read_text())
    manifest["files"] = {
        name: digest for name, digest in manifest["files"].items() if name in legacy_names
    }
    paths["manifest.json"].write_text(json.dumps(manifest))
    assert set(verify_report(tmp_path)["files_verified"]) == legacy_names


def test_linked_artifact_rejected_without_needing_symlink_privilege(tmp_path, monkeypatch):
    bundle(tmp_path)
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda p: p.name == "comparison.json" or original(p))
    with pytest.raises(EvaluationError, match="linked report"):
        verify_report(tmp_path)


def test_cli_missing_manifest_returns_error_not_traceback(tmp_path, capsys):
    assert main(["evaluation-verify", "--report", str(tmp_path)]) == 2
    assert "manifest.json" in capsys.readouterr().err
