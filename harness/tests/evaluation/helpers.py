"""Build isolated fixture stores using the team's existing schema and task.

Usage:
    cfg, dataset = saved(tmp_path, method="original")
"""

from dataclasses import replace
from pathlib import Path

from harness.config import load_config
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

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "sha256:" + "1" * 64


def config(tmp_path, method="original", seed=1):
    cfg = load_config(ROOT / "configs/mock.yaml")
    return replace(
        cfg,
        seed=seed,
        runs_dir=tmp_path / method,
        writer=replace(cfg.writer, samples_per_task=1),
        tasks=replace(cfg.tasks, max_programs=1),
        editor=replace(cfg.editor, reps=3),
    )


def saved(tmp_path, method="original", statuses=None, initial=True, seed=1):
    cfg = config(tmp_path, method, seed)
    task = load_tasks(cfg.tasks)["record_store"]
    pv = prompt_version(
        build_writer_prompt(task.writer_view(), load_template(cfg.writer.prompt_template))
    )
    with Store(cfg.runs_dir) as store:
        run = store.start_run(cfg)
        cid = store.put_blob(task.reference)
        store.record_candidate(
            Candidate(
                CandidateKey(task.id, pv, writer_cfg_hash(cfg), 0),
                cid if initial != "parse" else None,
                "malformed/no_code: fixture" if initial == "parse" else None,
                10,
                20,
                1.0,
                run,
            )
        )
        if initial != "parse":
            store.record_initial_check(
                InitialCheck(
                    task.id,
                    task.task_version,
                    cid,
                    sandbox_cfg_hash(cfg, IMAGE),
                    initial,
                    {"fixture_only": True},
                    run,
                )
            )
        if initial is True:
            for seq in task.sequences:
                for rep in range(3):
                    chosen = (statuses or {}).get((seq.id, rep), ["success", "success"])
                    key = TrialKey(
                        task.id, task.task_version, cid, seq.id, rep, editor_cfg_hash(cfg, IMAGE)
                    )
                    for i, status in enumerate(chosen, 1):
                        store.record_checkpoint(
                            Checkpoint(
                                key,
                                i,
                                seq.steps[i - 1].change.id,
                                status,
                                cid,
                                tokens_in=1,
                                tokens_out=2,
                                wall_s=0.5,
                                run_id=run,
                                end_reason="fixture",
                            )
                        )
    return cfg, export_dataset(cfg, IMAGE, method=method, purpose="fixture")
