"""Tests that the evaluation export measures the first edit of a comment
ablation trial from the stripped program the editor saw, not from the
writer's original, while the writer's own source description stays on the
original.

Usage:
    uv run pytest tests/evaluation/test_export_view.py
"""

from dataclasses import replace

import pytest

from harness.collection.view import strip_comments
from harness.evaluation.export import export_dataset
from harness.registry import build_writer_prompt, load_tasks, load_template, prompt_version
from harness.store import (
    Candidate,
    CandidateKey,
    Checkpoint,
    InitialCheck,
    Store,
    TrialKey,
    editor_cfg_hash,
    sandbox_cfg_hash,
    writer_cfg_hash,
)

from .helpers import IMAGE, config


def _saved_with_comments(tmp_path, view_transform):
    """One commented program whose first edit changes nothing beyond what the
    editor was shown, and whose second edit adds one line."""
    base = config(tmp_path, method=view_transform)
    cfg = replace(base, editor=replace(base.editor, view_transform=view_transform))
    task = load_tasks(cfg.tasks)["record_store"]
    written = {path: b"# a note\n" + data for path, data in task.reference.items()}
    shown = strip_comments(written) if view_transform == "strip_comments" else dict(written)
    path = sorted(p for p in shown if p.endswith(".py"))[0]
    second = {**shown, path: shown[path] + b"EXTRA = 1\n"}
    pv = prompt_version(
        build_writer_prompt(task.writer_view(), load_template(cfg.writer.prompt_template))
    )
    with Store(cfg.runs_dir) as store:
        run = store.start_run(cfg)
        cid = store.put_blob(written)
        outputs = [store.put_blob(shown), store.put_blob(second)]
        store.record_candidate(
            Candidate(CandidateKey(task.id, pv, writer_cfg_hash(cfg), 0), cid, None, 1, 2, 1.0, run)
        )
        store.record_initial_check(
            InitialCheck(
                task.id, task.task_version, cid, sandbox_cfg_hash(cfg, IMAGE), True, {}, run
            )
        )
        for seq in task.sequences:
            for rep in range(cfg.editor.reps):
                key = TrialKey(
                    task.id, task.task_version, cid, seq.id, rep, editor_cfg_hash(cfg, IMAGE)
                )
                for step, blob in enumerate(outputs, 1):
                    store.record_checkpoint(
                        Checkpoint(
                            key,
                            step,
                            seq.steps[step - 1].change.id,
                            "success",
                            blob,
                            run_id=run,
                            end_reason="fixture",
                        )
                    )
    data = export_dataset(cfg, IMAGE, method=view_transform, purpose="fixture")
    return data["samples"][0], written


@pytest.mark.parametrize("view_transform", ["none", "strip_comments"])
def test_first_edit_is_measured_from_what_the_editor_saw(tmp_path, view_transform):
    sample, _ = _saved_with_comments(tmp_path, view_transform)

    for trial in sample["trials"]:
        first, second = (step["change_size"] for step in trial["steps"])
        # The editor's first output is exactly what it was shown: no edit.
        assert first["files_changed"] == 0
        assert (second["python_lines_added"], second["python_lines_removed"]) == (1, 0)


def test_ablation_keeps_describing_the_writers_original_program(tmp_path):
    sample, written = _saved_with_comments(tmp_path, "strip_comments")

    assert sample["source_metrics"]["python_comment_lines"] >= len(
        [p for p in written if p.endswith(".py")]
    )
    assert sample["source_lines"] == sum(len(d.splitlines()) for d in written.values())
