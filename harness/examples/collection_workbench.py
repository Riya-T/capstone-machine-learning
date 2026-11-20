"""Demonstrate the workbench using explicitly synthetic native-store records.

Usage (from harness/):
    uv run python examples/collection_workbench.py --out runs/collection-demo
No model, Docker daemon, training or network connection is used.
"""

from __future__ import annotations

import argparse
import csv
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


def saved_fixture(root, method, *, interrupted=False, training_seed=None):
    cfg = load_config(ROOT / "configs/mock.yaml")
    cfg = replace(
        cfg,
        runs_dir=root / method,
        writer=replace(cfg.writer, samples_per_task=6),
        tasks=replace(cfg.tasks, max_programs=2),
        editor=replace(cfg.editor, reps=2),
    )
    if training_seed is not None:
        cfg = replace(
            cfg,
            writer=replace(
                cfg.writer, backend=replace(cfg.writer.backend, model="synthetic-writer-" + method)
            ),
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
    return export_collection(
        cfg,
        IMAGE,
        method=method,
        purpose="fixture",
        method_group="candidate" if training_seed is not None else None,
        training_seed=training_seed,
    )


def run(out, *, investigate=False):
    out = Path(out)
    safe_destination(out)
    if out.exists():
        raise ValueError("Use a new demonstration directory; no existing evidence is replaced")
    out.mkdir(parents=True)
    data = [saved_fixture(out / "stores", "base")]
    if investigate:
        from harness.evaluation.records import read_json
        from harness.evaluation.review import ANNOTATION_FIELDS

        data.extend(
            saved_fixture(out / "stores", f"candidate_s{seed}", training_seed=seed)
            for seed in (42, 43)
        )
    else:
        data.append(saved_fixture(out / "stores", "candidate"))
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
    receipt = {
        "purpose": "SYNTHETIC FIXTURE — not experimental evidence",
        "report": str(out / "report/report.html"),
        "incomplete_report": str(out / "unfinished-report/report.html"),
        "model_calls": 0,
        "training_labels_created": 0,
    }
    if investigate:
        from harness.workbench.checkpoints import run_summary
        from harness.workbench.review import compile_pack, make_pack

        run_summary(out / "report", out / "checkpoints", expected_seeds={"candidate": [42, 43]})
        make_pack(
            out / "report",
            out / "review",
            stores={d["method"]: out / "stores" / d["method"] for d in data},
        )
        compile_pack(out / "review", [out / "review/annotations.template.csv"], out / "unreviewed")
        for directory in ("checkpoints", "review", "unreviewed"):
            verify_report(out / directory)
        # These explicitly hypothetical reviewers demonstrate disagreement handling.
        case = next(
            c
            for c in read_json((out / "review/cases.json").read_bytes())["cases"]
            if c["stage"] == "edit"
        )
        annotations = []
        for name, category in (("demo_reviewer_a", "edit_bug"), ("demo_reviewer_b", "uncertain")):
            path = out / (name + ".csv")
            with path.open("w", newline="", encoding="utf8") as stream:
                writer = csv.DictWriter(stream, fieldnames=ANNOTATION_FIELDS)
                writer.writeheader()
                writer.writerow(
                    dict(
                        case_id=case["case_id"],
                        reviewer=name,
                        category=category,
                        confidence="hypothesis",
                        evidence="",
                        notes="Synthetic demonstration annotation, not a finding.",
                    )
                )
            annotations.append(path)
        compile_pack(out / "review", annotations, out / "disagreement-demo")
        verify_report(out / "disagreement-demo")
        receipt.update(
            checkpoints=str(out / "checkpoints/report.html"),
            review=str(out / "review/review.html"),
            unreviewed_summary=str(out / "unreviewed/report.html"),
            disagreement_demo=str(out / "disagreement-demo/report.html"),
        )
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--investigate",
        action="store_true",
        help="Also demonstrate synthetic checkpoint and failure-review workflows",
    )
    args = parser.parse_args()
    print(encoded(run(args.out, investigate=args.investigate)).decode(), end="")
