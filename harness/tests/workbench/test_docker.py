"""Run the actual mock collector and privately score its artifacts in Docker.

Usage: python -m pytest tests/workbench/test_docker.py --slow -rs
This is a software smoke, never experimental model evidence.
"""

from dataclasses import replace

import pytest

from harness.collection.collect import collect, sandbox_owner
from harness.config import load_config
from harness.sandbox.runner import make_runner
from harness.workbench.analysis import compare_collections, task_summary
from harness.workbench.export import export_collection
from harness.workbench.report import verify_report, write_report
from tests.evaluation.helpers import ROOT
from tests.workbench.test_export import hashes

pytestmark = [pytest.mark.docker, pytest.mark.slow]


def test_actual_mock_collection_export_private_scoring_and_zero_inference_resume(tmp_path):
    cfg = load_config(ROOT / "configs/mock.yaml")
    cfg = replace(
        cfg, runs_dir=tmp_path / "store", execution=replace(cfg.execution, sandbox_workers=1)
    )
    runner = make_runner(cfg, owner=sandbox_owner(cfg))
    image_id = runner.existing_image_id()
    if image_id is None:
        pytest.skip("Build the normal harness sandbox image before this smoke")
    first = collect(cfg)
    assert first.model_calls > 0  # Deterministic mock responses, no external inference.
    before = hashes(cfg.runs_dir)
    data = export_collection(cfg, image_id, method="mock", purpose="fixture")
    after = hashes(cfg.runs_dir)
    # SQLite can create lock bookkeeping even for a mode=ro WAL reader.
    # Require every durable database/blob/run file to remain byte-identical.
    transient = {"harness.sqlite-wal", "harness.sqlite-shm"}
    assert {k: v for k, v in before.items() if k not in transient} == {
        k: v for k, v in after.items() if k not in transient
    }
    assert (cfg.runs_dir / "harness.sqlite-wal").stat().st_size == 0
    row = task_summary(data, data["tasks"][0])
    assert row["initial_pass_rate"] == 1
    assert row["selected_programs"] == 1
    assert row["duplicate_samples"] == 2
    assert row["selected_completion"] == 0
    assert row["all_sample_completion"] == 0
    write_report(compare_collections([data], bootstrap_samples=20), tmp_path / "report")
    assert verify_report(tmp_path / "report")["verified"]
    second = collect(cfg)
    assert second.model_calls == 0
