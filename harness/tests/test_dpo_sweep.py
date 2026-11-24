"""Tests for preparing and tracking the history-suite DPO sweep.

Usage: uv run pytest tests/test_dpo_sweep.py
"""

import json
import subprocess
from pathlib import Path

import pytest

from harness.dpo_sweep import load_spec, prepare, record_jobs

SPEC = Path(__file__).parents[1] / "configs/dpo_sweeps/history_beta_nll.yaml"
CONFIG_DIR = Path(__file__).parents[1] / "configs"


def test_history_sweep_is_controlled_and_seeded():
    spec = load_spec(SPEC)

    assert spec["learning_rate"] == pytest.approx(3e-5)
    assert spec["epochs"] == 3
    assert spec["seeds"] == [42, 43, 44]
    assert len(spec["candidate_settings"]) == 5
    assert {(row["beta"], row["nll_weight"]) for row in spec["candidate_settings"]} == {
        (0.05, 1.0),
        (0.1, 0.0),
        (0.1, 1.0),
        (0.1, 2.0),
        (0.2, 1.0),
    }


def test_record_jobs_updates_both_manifests(tmp_path):
    run_id = "hist2_beta_nll_dev_beta005_nll1_s42"
    run = {"run_id": run_id, "status": "planned", "jobs": {"train": None, "evaluation": None}}
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps(run), encoding="utf-8")
    root = {"runs": {run_id: run}}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(root), encoding="utf-8")

    record_jobs(path, run_id, "1234", None)
    record_jobs(path, run_id, None, "1235")

    updated = json.loads(path.read_text(encoding="utf-8"))["runs"][run_id]
    per_seed = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert updated["status"] == "submitted"
    assert updated["jobs"] == {"train": "1234", "evaluation": "1235"}
    assert per_seed == updated


def test_prepare_writes_one_config_and_manifest_per_seed(tmp_path, monkeypatch):
    source = SPEC.read_text(encoding="utf-8").replace(
        "hist2_beta_nll_dev", f"pytest_{tmp_path.name.replace('-', '_')}"
    )
    spec_path = tmp_path / "sweep.yaml"
    spec_path.write_text(source, encoding="utf-8")
    preferences = tmp_path / "preferences.jsonl"
    preferences.write_text('{"prompt":"p","chosen":"a","rejected":"b"}\n', encoding="utf-8")
    monkeypatch.setattr("harness.dpo_sweep._git_state", lambda: ("a" * 40, False))

    sweep_name = load_spec(spec_path)["name"]
    try:
        output = prepare(
            spec_path=spec_path,
            preferences=preferences,
            hf_revision="b" * 40,
            output_dir=tmp_path / "output",
            config_dir=CONFIG_DIR,
        )
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        submit = (output / "submit.sh").read_text(encoding="utf-8")

        assert len(manifest["runs"]) == 15
        assert all(run["status"] == "planned" for run in manifest["runs"].values())
        assert all(run["data"]["sha256"] for run in manifest["runs"].values())
        assert "afterok:${PREVIOUS_JOB}" in submit
        assert "afterok:${TRAIN_JOB}" in submit
        subprocess.run(["bash", "-n", str(output / "submit.sh")], check=True)
    finally:
        for config in CONFIG_DIR.glob(f"dpo-sweep-{sweep_name}-*.yaml"):
            config.unlink()


def test_load_spec_rejects_duplicate_setting_names(tmp_path):
    content = SPEC.read_text(encoding="utf-8").replace("name: beta020_nll1", "name: beta005_nll1")
    path = tmp_path / "duplicate.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="invalid or duplicated"):
        load_spec(path)
