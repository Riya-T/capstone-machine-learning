"""Read-only export, exact keys, initial failures, and record validation.

Usage:
    uv run pytest tests/evaluation/test_export.py
"""

import copy
import hashlib
from dataclasses import replace

import pytest

from harness.evaluation.export import export_dataset
from harness.evaluation.records import EvaluationError, trajectory, validate_dataset
from harness.registry import load_tasks
from harness.store import Store

from .helpers import IMAGE, config, saved


def test_export_matches_source_scores_and_does_not_change_store(tmp_path):
    cfg, data = saved(tmp_path, statuses={("s1", 0): ["success", "fail_existing"]})
    before = {
        p.relative_to(cfg.runs_dir): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in cfg.runs_dir.rglob("*")
        if p.is_file()
    }
    again = export_dataset(cfg, IMAGE, method="original", purpose="fixture")
    after = {
        p.relative_to(cfg.runs_dir): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in cfg.runs_dir.rglob("*")
        if p.is_file()
    }
    assert again == data and after == before
    sample = data["samples"][0]
    assert sample["initial_status"] == "pass"
    assert trajectory(sample, sample["trials"][0], 2)["score"] == 1
    assert data["provenance"]["runs"][0]["git_commit"]
    assert data["provenance"]["cost_note"].startswith("Recorded editor token")


@pytest.mark.parametrize("initial", [False, "parse"])
def test_initial_failure_remains_in_population_without_fake_edit_steps(tmp_path, initial):
    _, data = saved(tmp_path, initial=initial)
    sample = data["samples"][0]
    assert sample["initial_status"] == ("fail" if initial is False else "parse_failure")
    assert all(
        t["steps"] == [] and trajectory(sample, t, 2)["score"] == 0 for t in sample["trials"]
    )


def test_missing_store_stays_missing_and_unresolved(tmp_path):
    cfg = config(tmp_path)
    data = export_dataset(cfg, IMAGE, method="original", purpose="fixture")
    assert not cfg.runs_dir.exists()
    sample = data["samples"][0]
    assert sample["initial_status"] == "unresolved"
    assert all(trajectory(sample, t, 2)["score"] is None for t in sample["trials"])


def test_snapshot_reads_committed_wal_without_writable_store_initialization(tmp_path):
    cfg, _ = saved(tmp_path)
    with Store(cfg.runs_dir) as writer:
        # A writer connection remains open while the read-only backup is taken.
        before = list(writer.all_checkpoints())
        result = export_dataset(cfg, IMAGE, method="original", purpose="fixture")
        assert list(writer.all_checkpoints()) == before
        assert result["samples"][0]["initial_status"] == "pass"


def test_changed_task_or_model_keys_do_not_load_stale_scores(tmp_path):
    cfg, _ = saved(tmp_path)
    changed = replace(
        cfg, editor=replace(cfg.editor, backend=replace(cfg.editor.backend, model="other"))
    )
    data = export_dataset(changed, IMAGE, method="original", purpose="fixture")
    assert data["samples"][0]["initial_status"] == "pass"
    assert all(not t["steps"] for t in data["samples"][0]["trials"])
    changed = replace(
        cfg, writer=replace(cfg.writer, backend=replace(cfg.writer.backend, model="other"))
    )
    assert (
        export_dataset(changed, IMAGE, method="original", purpose="fixture")["samples"][0][
            "initial_status"
        ]
        == "unresolved"
    )


def test_corrupt_source_hash_is_rejected(tmp_path):
    cfg, data = saved(tmp_path)
    (cfg.runs_dir / "blobs" / (data["samples"][0]["candidate_id"] + ".json")).write_bytes(b"{}")
    with pytest.raises(EvaluationError, match="Corrupt"):
        export_dataset(cfg, IMAGE, method="original", purpose="fixture")


def test_multi_sample_collection_cannot_be_mislabeled_as_unselected_evaluation(tmp_path):
    cfg = config(tmp_path)
    with pytest.raises(EvaluationError, match="one writer sample"):
        export_dataset(
            replace(cfg, writer=replace(cfg.writer, samples_per_task=16)),
            IMAGE,
            method="original",
            purpose="fixture",
        )


def test_heldout_purpose_rejects_training_task(tmp_path):
    cfg = config(tmp_path)
    with pytest.raises(EvaluationError, match="split"):
        export_dataset(cfg, IMAGE, method="original")


@pytest.mark.parametrize("status", ["infra_error", "budget_exhausted", "fail_new", "fail_both"])
def test_failure_categories_remain_distinct(tmp_path, status):
    _, data = saved(tmp_path, statuses={("s1", 0): [status]})
    sample = data["samples"][0]
    outcome = trajectory(sample, sample["trials"][0], 2)
    assert outcome["status"] == status
    assert outcome["score"] == (None if status == "infra_error" else 0)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["samples"].append(copy.deepcopy(d["samples"][0])),
        lambda d: d["samples"][0]["trials"].append(copy.deepcopy(d["samples"][0]["trials"][0])),
        lambda d: d["samples"][0]["trials"][0]["steps"][0].update(status="maybe"),
        lambda d: d["samples"][0]["trials"][0]["steps"][0].update(tokens_in=-1),
        lambda d: d["samples"][0]["writer_cost"].update(wall_s=float("nan")),
        lambda d: d.update(method="../escape"),
        lambda d: d.update(schema_version=True),
        lambda d: d["samples"][0]["trials"][0]["steps"][0].update(step=True),
        lambda d: d["samples"][0]["trials"][0]["steps"][0].update(status="fail_new"),
        lambda d: d["samples"][0].update(initial_status="fail"),
    ],
)
def test_invalid_records_fail_closed(tmp_path, mutate):
    _, data = saved(tmp_path)
    mutate(data)
    with pytest.raises(EvaluationError):
        validate_dataset(data)


def test_fixture_export_contains_all_original_sequences_and_versions(tmp_path):
    cfg, data = saved(tmp_path)
    task = load_tasks(cfg.tasks)["record_store"]
    assert data["tasks"][0]["version"] == task.task_version
    assert len(data["samples"][0]["trials"]) == 6
