"""Demonstrate the workbench using explicitly synthetic native-store records.

Usage (from harness/):
    uv run python examples/collection_workbench.py --out runs/collection-demo
No model, Docker daemon, training or network connection is used.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

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
from harness.workbench.analysis import compare_collections
from harness.workbench.export import export_collection
from harness.workbench.report import encoded, safe_destination, verify_report, write_report

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "sha256:" + "1" * 64


def saved_fixture(root, method, *, interrupted=False):
    cfg = load_config(ROOT / "configs/mock.yaml")
    cfg = replace(
        cfg,
        runs_dir=root / method,
        writer=replace(cfg.writer, samples_per_task=6),
        tasks=replace(cfg.tasks, max_programs=2),
        editor=replace(cfg.editor, reps=2),
    )
    task = load_tasks(cfg.tasks)["record_store"]
    pv = prompt_version(
        build_writer_prompt(task.writer_view(), load_template(cfg.writer.prompt_template))
    )
    with Store(cfg.runs_dir) as store:
        run = store.start_run(cfg)
        parents = [
            store.put_blob(
                {
                    name: source + f"\n# Synthetic {i}\n".encode()
                    for name, source in task.reference.items()
                }
            )
            for i in range(4)
        ]
        slots = [parents[0], parents[0], parents[1], None, parents[2], parents[3]]
        for sample, cid in enumerate(slots):
            store.record_candidate(
                Candidate(
                    CandidateKey(task.id, pv, writer_cfg_hash(cfg), sample),
                    cid,
                    "malformed/no_code: SYNTHETIC" if cid is None else None,
                    10,
                    20,
                    1.0,
                    run,
                )
            )
        for index, cid in enumerate(parents):
            store.record_initial_check(
                InitialCheck(
                    task.id,
                    task.task_version,
                    cid,
                    sandbox_cfg_hash(cfg, IMAGE),
                    index != 1,
                    {"synthetic_fixture_only": True},
                    run,
                )
            )
            if index == 1:
                continue
            for sequence in task.sequences:
                for rep in range(2):
                    # These statuses are authored controls, not executed outcomes.
                    statuses = ["success"] * len(sequence.steps)
                    if index == 2:
                        statuses = ["fail_new"] if method == "base" else ["success", "fail_new"]
                    if interrupted and rep == 0:
                        statuses = []
                    for number, status in enumerate(statuses, 1):
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
                                number,
                                sequence.steps[number - 1].change.id,
                                status,
                                cid,
                                tokens_in=2,
                                tokens_out=3,
                                n_calls=1,
                                wall_s=0.25,
                                run_id=run,
                                end_reason="SYNTHETIC_FIXTURE",
                            )
                        )
    return export_collection(cfg, IMAGE, method=method, purpose="fixture")


def run(out):
    out = Path(out)
    safe_destination(out)
    if out.exists():
        raise ValueError("Use a new demonstration directory; no existing evidence is replaced")
    out.mkdir(parents=True)
    data = [saved_fixture(out / "stores", method) for method in ("base", "candidate")]
    for dataset in data:
        (out / (dataset["method"] + ".json")).write_bytes(encoded(dataset))
    result = compare_collections(data, reference="base", bootstrap_samples=100)
    write_report(result, out / "report")
    verify_report(out / "report")
    unfinished = saved_fixture(out / "unfinished-store", "interrupted", interrupted=True)
    receipt = write_report(
        compare_collections([unfinished], bootstrap_samples=100), out / "unfinished-report"
    )
    assert not receipt["collection_complete"]
    verify_report(out / "unfinished-report")
    return {
        "purpose": "SYNTHETIC FIXTURE — not experimental evidence",
        "report": str(out / "report/report.html"),
        "incomplete_report": str(out / "unfinished-report/report.html"),
        "model_calls": 0,
        "training_labels_created": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(encoded(run(args.out)).decode(), end="")
