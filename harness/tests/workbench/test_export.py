"""Exercise real SQLite exports without inference or generated-code execution.

Usage: python -m pytest tests/workbench/test_export.py
"""

import hashlib
import sqlite3
from dataclasses import replace

import pytest

from harness.evaluation.records import EvaluationError
from harness.store import Store
from harness.workbench.export import export_collection
from tests.evaluation.helpers import IMAGE
from tests.workbench.helpers import fixture


def hashes(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_reads_every_sample_and_unique_parent_without_touching_store(tmp_path, monkeypatch):
    cfg, _ = fixture(tmp_path)
    before = hashes(cfg.runs_dir)
    monkeypatch.setattr(Store, "__init__", lambda *_: pytest.fail("Store must not be initialized"))
    data = export_collection(cfg, IMAGE, method="base", purpose="fixture")
    task = data["tasks"][0]
    assert len(task["samples"]) == 6
    assert len(task["programs"]) == 4
    assert task["programs"][0]["sample_indices"] == [0, 1]
    assert [p["selection"] for p in task["programs"]] == [
        "selected",
        "initial_failure",
        "selected",
        "over_cap",
    ]
    assert before == hashes(cfg.runs_dir)
    assert "source_store" not in data["provenance"]
    assert "host" not in data["provenance"]["runs"][0]


def test_missing_store_and_writer_samples_stay_missing(tmp_path):
    cfg, _ = fixture(tmp_path)
    empty = replace(cfg, runs_dir=tmp_path / "does-not-exist")
    data = export_collection(empty, IMAGE, method="empty", purpose="fixture")
    assert not empty.runs_dir.exists()
    assert not data["provenance"]["source_store_present"]
    assert len(data["tasks"][0]["samples"]) == 6
    assert all(s["initial_status"] == "unresolved" for s in data["tasks"][0]["samples"])


def test_wrong_image_and_config_do_not_adopt_other_saved_checks(tmp_path):
    cfg, _ = fixture(tmp_path)
    other = export_collection(cfg, "sha256:" + "f" * 64, method="base", purpose="fixture")
    assert all(p["initial_status"] == "unresolved" for p in other["tasks"][0]["programs"])
    assert other["provenance"]["warnings"] == [
        "initial_checks_missing_check_task_version_and_image_id"
    ]
    changed = replace(
        cfg, writer=replace(cfg.writer, backend=replace(cfg.writer.backend, temperature=0.123))
    )
    missing = export_collection(changed, IMAGE, method="base", purpose="fixture")
    assert not missing["tasks"][0]["programs"]


def test_generation_seed_cannot_be_relabelled_by_a_different_config(tmp_path):
    cfg, _ = fixture(tmp_path)
    with pytest.raises(EvaluationError, match="generation seed"):
        export_collection(replace(cfg, seed=cfg.seed + 1), IMAGE, method="base", purpose="fixture")


def test_blob_integrity_is_required_and_generated_source_is_never_executed(tmp_path):
    cfg, _ = fixture(tmp_path)
    blob = next((cfg.runs_dir / "blobs").iterdir())
    blob.write_bytes(b"{}")
    with pytest.raises(EvaluationError, match="Corrupt source"):
        export_collection(cfg, IMAGE, method="base", purpose="fixture")


def test_read_only_snapshot_observes_committed_wal_records(tmp_path):
    cfg, _ = fixture(tmp_path)
    db = sqlite3.connect(cfg.runs_dir / "harness.sqlite")
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("UPDATE candidates SET tokens_in=77 WHERE sample_idx=0")
        db.commit()
        data = export_collection(cfg, IMAGE, method="base", purpose="fixture")
        assert data["tasks"][0]["samples"][0]["writer_cost"]["tokens_in"] == 77
        assert db.execute("SELECT tokens_in FROM candidates WHERE sample_idx=0").fetchone()[0] == 77
    finally:
        db.close()


@pytest.mark.parametrize("image", ["harness-sandbox:latest", "sha256:bad", "sha256:" + "z" * 64])
def test_requires_a_content_image_id(tmp_path, image):
    cfg, _ = fixture(tmp_path)
    with pytest.raises(EvaluationError):
        export_collection(cfg, image, method="base", purpose="fixture")


def test_initial_infrastructure_is_not_classified_as_incorrect_code(tmp_path):
    cfg, _ = fixture(tmp_path)
    with sqlite3.connect(cfg.runs_dir / "harness.sqlite") as db:
        db.execute(
            "UPDATE initial_checks SET passed=0, report_json=?",
            ('{"public":{"status":"infra_error"}}',),
        )
    data = export_collection(cfg, IMAGE, method="base", purpose="fixture")
    assert all(p["initial_status"] == "infra_error" for p in data["tasks"][0]["programs"])
    assert all(not t["steps"] for p in data["tasks"][0]["programs"] for t in p["trials"])


def test_wrong_task_version_remains_unresolved_instead_of_reusing_old_tests(tmp_path):
    cfg, _ = fixture(tmp_path)
    with sqlite3.connect(cfg.runs_dir / "harness.sqlite") as db:
        db.execute("UPDATE initial_checks SET task_version=?", ("e" * 64,))
    data = export_collection(cfg, IMAGE, method="base", purpose="fixture")
    assert all(p["initial_status"] == "unresolved" for p in data["tasks"][0]["programs"])


def test_source_is_described_without_running_top_level_code(tmp_path):
    cfg, data = fixture(tmp_path)
    marker = tmp_path / "must-not-be-created"
    source = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n".encode()
    with Store(cfg.runs_dir) as store:
        cid = store.put_blob({"evil.py": source})
    with sqlite3.connect(cfg.runs_dir / "harness.sqlite") as db:
        db.execute("UPDATE candidates SET candidate_id=? WHERE sample_idx=0", (cid,))
    exported = export_collection(cfg, IMAGE, method="base", purpose="fixture")
    assert exported["tasks"][0]["programs"][0]["source_metrics"]["python_syntax_valid"]
    assert not marker.exists()
