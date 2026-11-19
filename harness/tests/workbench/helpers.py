"""Build labeled native-store fixtures for duplicates, caps and editing failures.

Usage: cfg, data = fixture(tmp_path)
These records validate accounting software, not model performance.
"""

from dataclasses import replace

from harness.config import load_config
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
from harness.workbench.export import export_collection
from tests.evaluation.helpers import IMAGE, ROOT


def fixture(tmp_path, *, method="base", cap=2, missing=(), infra=False):
    cfg = load_config(ROOT / "configs/mock.yaml")
    cfg = replace(
        cfg,
        runs_dir=tmp_path / method,
        base_dir=tmp_path,
        writer=replace(cfg.writer, samples_per_task=6),
        tasks=replace(cfg.tasks, max_programs=cap),
        editor=replace(cfg.editor, reps=2),
    )
    task = load_tasks(cfg.tasks)["record_store"]
    pv = prompt_version(
        build_writer_prompt(task.writer_view(), load_template(cfg.writer.prompt_template))
    )
    with Store(cfg.runs_dir) as store:
        run_id = store.start_run(cfg)
        blobs = []
        for i in range(4):
            files = {
                name: data + f"\n# software fixture {i}\n".encode()
                for name, data in task.reference.items()
            }
            blobs.append(store.put_blob(files))
        for index, cid in enumerate([blobs[0], blobs[0], blobs[1], None, blobs[2], blobs[3]]):
            if index in missing:
                continue
            store.record_candidate(
                Candidate(
                    CandidateKey(task.id, pv, writer_cfg_hash(cfg), index),
                    cid,
                    "malformed/unlabeled_block: fixture only" if cid is None else None,
                    10,
                    20,
                    1.0,
                    run_id,
                )
            )
        for i, cid in enumerate(blobs):
            store.record_initial_check(
                InitialCheck(
                    task.id,
                    task.task_version,
                    cid,
                    sandbox_cfg_hash(cfg, IMAGE),
                    i != 1,
                    {"fixture_only": True},
                    run_id,
                )
            )
            if i == 1:
                continue
            for sequence in task.sequences:
                for rep in range(2):
                    statuses = ["success"] * len(sequence.steps) if i != 2 else ["fail_new"]
                    if infra and i == 0 and rep == 0:
                        statuses = ["infra_error"]
                    for step, status in enumerate(statuses, 1):
                        store.record_checkpoint(
                            Checkpoint(
                                TrialKey(
                                    task.id,
                                    task.task_version,
                                    cid,
                                    sequence.id,
                                    rep,
                                    editor_cfg_hash(cfg, IMAGE),
                                ),
                                step,
                                sequence.steps[step - 1].change.id,
                                status,
                                cid,
                                tokens_in=2,
                                tokens_out=3,
                                n_calls=1,
                                wall_s=0.25,
                                run_id=run_id,
                                infra_cause="fixture_runner" if status == "infra_error" else None,
                                end_reason="fixture",
                            )
                        )
    return cfg, export_collection(cfg, IMAGE, method=method, purpose="fixture")
