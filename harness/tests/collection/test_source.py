"""Tests for collection/source.py: which config changes change a pair's
settings_hash (an experiment setting) and which don't (a machine detail).

Usage:
    uv run pytest tests/collection/test_source.py
"""

import pytest

from harness.collection.collect import Keys
from harness.collection.source import pair_source, run_source, settings, settings_hash
from harness.config import load_config

from ..helpers import minimal, write


def _hash(tmp_path, change=None, name="exp.yaml"):
    data = minimal()
    if change:
        change(data)
    return settings_hash(settings(load_config(write(tmp_path, data, name))))


def _set(*path_and_value):
    *path, value = path_and_value

    def change(data):
        section = data
        for key in path[:-1]:
            section = section[key]
        section[path[-1]] = value

    return change


@pytest.mark.parametrize(
    "change",
    [
        _set("seed", 2),
        _set("name", "other"),
        _set("runs_dir", "runs_karin"),
        _set("tasks", "include", ["a", "b"]),
        _set("writer", "samples_per_task", 8),
        _set("writer", "backend", "request_timeout_s", 30),
        _set("editor", "backend", "max_retries", 5),
        _set("sandbox", "image", "harness-sandbox:apptainer"),
        _set("execution", {"sandbox_runtime": "apptainer", "apptainer_image": "img.sif"}),
    ],
    ids=["seed", "name", "runs_dir", "tasks", "samples", "timeout", "retries", "image", "runtime"],
)
def test_machine_details_and_task_choice_leave_the_settings_alone(tmp_path, change):
    assert _hash(tmp_path / "a") == _hash(tmp_path / "b", change)


@pytest.mark.parametrize(
    "change",
    [
        _set("writer", "backend", "model", "other-writer"),
        _set("writer", "backend", "temperature", 0.9),
        _set("editor", "backend", "model", "other-editor"),
        _set("editor", "reps", 2),
        _set("editor", "view_transform", "strip_comments"),
        _set("editor", "budget", "max_turns", 5),
        _set("sandbox", "timeout_s", 50),
        _set("scorer", "rule", "strict"),
        _set("scorer", "per_task_cap", 8),
        _set("tasks", "sequences_per_task", 1),
    ],
    ids=[
        "writer-model",
        "writer-temperature",
        "editor-model",
        "reps",
        "view",
        "budget",
        "sandbox-timeout",
        "rule",
        "cap",
        "sequences",
    ],
)
def test_experiment_settings_change_the_hash(tmp_path, change):
    assert _hash(tmp_path / "a") != _hash(tmp_path / "b", change)


def test_a_prompt_template_counts_by_content_not_path(tmp_path):
    before = _hash(tmp_path / "a")
    folder = tmp_path / "b"
    write(folder, minimal())
    (folder / "writer.md").write_text("$entry_files $spec $public_checks\nBe tidy.")
    assert settings_hash(settings(load_config(folder / "exp.yaml"))) != before


def test_the_source_block_has_no_absolute_paths(tmp_path):
    cfg = load_config(write(tmp_path, minimal()))
    base = run_source(cfg, Keys("w", "e", "s"), run_id="r1")

    assert (base["run_id"], base["store"], base["config"]) == ("r1", "runs", "t")
    assert (base["writer_key"], base["editor_key"], base["sandbox_key"]) == ("w", "e", "s")
    assert base["sandbox_runtime"] == "docker"
    assert base["settings_hash"] == settings_hash(base["settings"])
    assert str(tmp_path) not in repr(base)


def test_pair_source_adds_the_task_and_prompt_versions():
    class FakeTask:
        task_version = "tv1"

    source = pair_source({"run_id": "r1"}, FakeTask(), "write a program")
    assert source["run_id"] == "r1" and source["task_version"] == "tv1"
    assert len(source["prompt_version"]) > 0
