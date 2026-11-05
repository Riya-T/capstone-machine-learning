"""Adversarial self-audit regressions for provenance, records and interrupted writes.

Usage:
    uv run pytest tests/evaluation/test_audit.py
"""

import copy
import hashlib
import json
from contextlib import suppress
from pathlib import Path

import pytest
import yaml

from harness.evaluation.analysis import compare
from harness.evaluation.export import export_dataset
from harness.evaluation.plan import _write_new, execute, prepare
from harness.evaluation.records import EvaluationError, identifier, read_json, validate_dataset
from harness.evaluation.storage import publish_new

from .helpers import IMAGE, saved
from .test_analysis import example
from .test_plan import forbidden, write_plan


def test_prepared_plan_rechecks_inputs_before_any_execution(tmp_path, monkeypatch):
    path = write_plan(tmp_path)
    prepared = prepare(path)
    config = tmp_path / "original.yaml"
    raw = yaml.safe_load(config.read_text())
    raw["writer"]["backend"]["temperature"] = 0.1
    config.write_text(yaml.safe_dump(raw))
    monkeypatch.setattr("harness.evaluation.plan.make_runner", forbidden)
    with pytest.raises(EvaluationError, match="changed since preparation"):
        execute(prepared)
    assert not prepared.root.exists()


def test_same_method_cannot_change_writer_across_generation_seeds():
    first = example()
    first["writer_model"] = "checkpoint-a"
    second = copy.deepcopy(first)
    second["generation_seed"] = 2
    second["writer_model"] = "checkpoint-b"
    with pytest.raises(EvaluationError, match="writer identity"):
        compare([first, second], bootstrap_samples=20)


def test_changes_must_be_an_array_not_a_string():
    data = example()
    data["tasks"][0]["sequences"][0]["changes"] = "ab"
    with pytest.raises(EvaluationError):
        validate_dataset(data)


def test_parse_failure_cannot_claim_a_parsed_source_hash():
    data = example()
    sample = data["samples"][1]
    sample["initial_status"] = "parse_failure"
    with pytest.raises(EvaluationError):
        validate_dataset(data)


def test_success_cannot_contradict_recorded_private_test_counts():
    data = example("candidate")
    data["samples"][0]["trials"][0]["steps"][0].update(
        new_pass=0,
        new_total=3,
        existing_pass=4,
        existing_total=4,
    )
    with pytest.raises(EvaluationError):
        validate_dataset(data)


def test_interrupted_evidence_write_never_leaves_a_truncated_final_file(tmp_path, monkeypatch):
    target = tmp_path / "lock.json"
    original_open = Path.open

    class Fault:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def write(self, data):
            self.stream.write(data[:4])
            self.stream.flush()
            raise OSError("simulated interruption")

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

    def inject(path, mode="r", *args, **kw):
        stream = original_open(path, mode, *args, **kw)
        return Fault(stream) if path == target and mode == "xb" else stream

    monkeypatch.setattr(Path, "open", inject)
    with suppress(OSError):
        _write_new(target, {"complete": True})
    assert not target.exists() or json.loads(target.read_text()) == {"complete": True}


def test_publication_failure_has_no_final_path_and_can_resume(tmp_path, monkeypatch):
    import os

    target = tmp_path / "snapshot.json"
    link = os.link

    def interrupted(*_):
        raise OSError("simulated failure before publication")

    monkeypatch.setattr("harness.evaluation.storage.os.link", interrupted)
    with pytest.raises(OSError, match="simulated"):
        _write_new(target, {"complete": True})
    assert not list(tmp_path.iterdir())
    monkeypatch.setattr("harness.evaluation.storage.os.link", link)
    _write_new(target, {"complete": True})
    assert read_json(target.read_text()) == {"complete": True}


def test_publication_race_preserves_competing_evidence(tmp_path, monkeypatch):
    target = tmp_path / "snapshot.json"

    def competitor(*_):
        target.write_bytes(b"another writer")
        raise FileExistsError("already exists")

    monkeypatch.setattr("harness.evaluation.storage.os.link", competitor)
    with pytest.raises(EvaluationError, match="overwrite"):
        publish_new(target, b"ours")
    assert target.read_bytes() == b"another writer"
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize(
    "text", ['{"method":"a","method":"b"}', '{"cost": NaN}', '{"cost": Infinity}']
)
def test_ambiguous_json_rejected(text):
    with pytest.raises(EvaluationError):
        read_json(text)


@pytest.mark.parametrize("name", ["con", "NUL", "COM1", "Lpt9"])
def test_portable_output_names_reject_windows_devices(name):
    with pytest.raises(EvaluationError):
        identifier(name, "method")


def test_test_counts_do_not_turn_runtime_failure_into_success():
    data = example("candidate")
    trial = data["samples"][0]["trials"][0]
    trial["steps"] = [
        {
            **trial["steps"][0],
            "status": "fail_both",
            "new_pass": 0,
            "new_total": 0,
            "existing_pass": 0,
            "existing_total": 0,
        }
    ]
    assert validate_dataset(data) is data
    assert (
        compare([data], bootstrap_samples=20)["methods"]["candidate"]["counts"][
            "trajectory_fail_both"
        ]
        == 1
    )


def test_edited_source_integrity_checked_even_when_initial_blob_is_intact(tmp_path):
    import sqlite3

    cfg, _ = saved(tmp_path)
    corrupt = b'{"edited.py":"incomplete base64"}'
    digest = hashlib.sha256(corrupt).hexdigest()
    (cfg.runs_dir / "blobs" / (digest + ".json")).write_bytes(corrupt)
    with sqlite3.connect(cfg.runs_dir / "harness.sqlite") as db:
        db.execute("UPDATE checkpoints SET output_blob=?", (digest,))
    with pytest.raises(EvaluationError, match="saved program"):
        export_dataset(cfg, IMAGE, method="original", purpose="fixture")


def test_writer_configuration_identity_not_just_model_tag():
    first = example()
    first["writer_identity"] = "1" * 64
    second = copy.deepcopy(first)
    second.update(generation_seed=2, writer_identity="2" * 64)
    with pytest.raises(EvaluationError, match="writer identity"):
        compare([first, second], bootstrap_samples=20)


def test_input_file_contents_change_fingerprint_before_generation(tmp_path):
    path = write_plan(tmp_path)
    config = tmp_path / "original.yaml"
    raw = yaml.safe_load(config.read_text())
    original = prepare(path).configs[0].writer.prompt_template
    template = tmp_path / "writer.txt"
    template.write_bytes(original.read_bytes())
    raw["writer"]["prompt_template"] = str(template)
    config.write_text(yaml.safe_dump(raw))
    before = prepare(path)
    template.write_bytes(template.read_bytes() + b"\nchanged")
    assert prepare(path).digest != before.digest
    with pytest.raises(EvaluationError, match="changed since preparation"):
        execute(before)
