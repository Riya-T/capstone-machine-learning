"""Export one evaluation seed from a consistent read-only SQLite snapshot.

Usage:
    dataset = export_dataset(cfg, image_id, method="original", purpose="heldout")
    # No model server, Docker daemon, Store initialization, or writes to source.
"""

from __future__ import annotations

import base64
import hashlib
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from ..collection.view import make_view
from ..config import ExperimentConfig
from ..registry import build_writer_prompt, load_tasks, load_template, prompt_version
from ..store import SCHEMA_VERSION, editor_cfg_hash, sandbox_cfg_hash, writer_cfg_hash
from .contract import UNRESOLVED_IMAGE
from .records import HASH, VERSION, EvaluationError, identifier, read_json, validate_dataset
from .source import describe_change, describe_source

COST_NOTE = (
    "Recorded editor token counts may include the collector's fallback estimates; "
    "they are not guaranteed provider-observed usage. Wall times are historical "
    "recorded attempt times, not fresh replay time or GPU-only inference time."
)


@contextmanager
def read_snapshot(path: Path):
    """Backup a read-only source connection into RAM, preserving WAL visibility."""
    if not path.is_file():
        yield None
        return
    try:
        source = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    except sqlite3.Error as exc:
        raise EvaluationError(f"Cannot open saved evaluation store: {exc}") from exc
    target = sqlite3.connect(":memory:")
    target.row_factory = sqlite3.Row
    started = time.monotonic()

    def progress(*_):
        if time.monotonic() - started > 15:
            raise EvaluationError("Timed out taking a consistent read-only database snapshot")

    try:
        source.backup(target, pages=256, progress=progress, sleep=0.01)
        version = target.execute("PRAGMA user_version").fetchone()[0]
        if version != SCHEMA_VERSION:
            raise EvaluationError(f"Store schema {version}, expected {SCHEMA_VERSION}")
        yield target
    except sqlite3.Error as exc:
        raise EvaluationError(f"Cannot read evaluation store {path}: {exc}") from exc
    finally:
        target.close()
        source.close()


def _blob(runs: Path, digest: str) -> dict[str, bytes]:
    if not HASH.fullmatch(digest):
        raise EvaluationError("Invalid saved source hash")
    path = runs / "blobs" / (digest + ".json")
    try:
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise EvaluationError(f"Corrupt source blob {digest}")
        return {p: base64.b64decode(s, validate=True) for p, s in read_json(data).items()}
    except (OSError, ValueError, AttributeError, TypeError) as exc:
        raise EvaluationError(f"Cannot read saved program {digest}: {exc}") from exc


def comparison_contract(cfg: ExperimentConfig, image_id: str) -> dict:
    """Writer identity/prompt may differ; editor and inference budgets must match."""
    return dict(
        editor_hash=editor_cfg_hash(cfg, image_id),
        sandbox_hash=sandbox_cfg_hash(cfg, image_id),
        image_id=image_id,
        writer_temperature=cfg.writer.backend.temperature,
        writer_max_tokens=cfg.writer.backend.max_tokens,
        writer_timeout_s=cfg.writer.backend.request_timeout_s,
        writer_max_retries=cfg.writer.backend.max_retries,
        editor_reps=cfg.editor.reps,
        sandbox_workers=cfg.execution.sandbox_workers,
        writer_samples_per_task=1,
        max_programs=1,
    )


def export_dataset(
    cfg: ExperimentConfig,
    image_id: str,
    *,
    method: str,
    purpose: str = "heldout",
    method_group: str | None = None,
    training_seed: int | None = None,
) -> dict:
    """Read exactly sample zero; never select a better initially passing sample."""
    identifier(method, "method")
    if cfg.writer.samples_per_task != 1 or cfg.tasks.max_programs != 1:
        raise EvaluationError("Evaluation requires one writer sample and max_programs=1")
    tasks = load_tasks(cfg.tasks)
    template = load_template(cfg.writer.prompt_template)
    view = make_view(cfg.editor.view_transform)
    writer_hash = writer_cfg_hash(cfg)
    sandbox_hash = sandbox_cfg_hash(cfg, image_id)
    editor_hash = editor_cfg_hash(cfg, image_id)
    data = dict(
        schema_version=VERSION,
        method=method,
        purpose=purpose,
        generation_seed=cfg.seed,
        editor_reps=cfg.editor.reps,
        writer_model=cfg.writer.backend.model,
        writer_identity=writer_hash,
        editor_identity=editor_cfg_hash(cfg, UNRESOLVED_IMAGE),
        method_group=method_group or method,
        training_seed=training_seed,
        contract=comparison_contract(cfg, image_id),
        provenance=dict(
            config=cfg.to_dict(),
            config_hash=cfg.config_hash,
            source_store=str(cfg.runs_dir / "harness.sqlite"),
            source_store_present=(cfg.runs_dir / "harness.sqlite").is_file(),
            source_run_ids=[],
            cost_note=COST_NOTE,
            backend_model_revision="Not resolved by the existing collector; model tag is recorded.",
        ),
        tasks=[],
        samples=[],
    )
    run_ids = set()
    with read_snapshot(cfg.runs_dir / "harness.sqlite") as db:
        for task in tasks.values():
            sequences = task.sequences[: cfg.tasks.max_sequences]
            data["tasks"].append(
                dict(
                    id=task.id,
                    family=task.family,
                    split=task.split,
                    version=task.task_version,
                    change_kinds={x.change.id: x.change.kind for s in sequences for x in s.steps},
                    sequences=[
                        dict(id=s.id, changes=[x.change.id for x in s.steps]) for s in sequences
                    ],
                )
            )
            prompt = build_writer_prompt(task.writer_view(), template)
            candidate = (
                None
                if db is None
                else db.execute(
                    "SELECT * FROM candidates WHERE task_id=? AND prompt_version=? "
                    "AND writer_cfg_hash=? AND sample_idx=0",
                    (task.id, prompt_version(prompt), writer_hash),
                ).fetchone()
            )
            initial_files = None
            sample = dict(
                task=task.id,
                candidate_id=None,
                initial_status="unresolved",
                parse_error=None,
                writer_cost=dict(tokens_in=None, tokens_out=None, wall_s=None),
                source_lines=None,
                source_metrics=None,
                trials=[],
            )
            if candidate is not None:
                # Preserve the first scheduled answer even if a later answer would pass more tests.
                run_ids.add(candidate["run_id"])
                cid = candidate["candidate_id"]
                sample.update(candidate_id=cid, parse_error=candidate["parse_error"])
                sample["writer_cost"] = {
                    k: candidate[k] for k in ("tokens_in", "tokens_out", "wall_s")
                }
                if cid is None:
                    sample["initial_status"] = "parse_failure"
                else:
                    files = _blob(cfg.runs_dir, cid)
                    initial_files = files
                    sample["source_lines"] = sum(len(s.splitlines()) for s in files.values())
                    sample["source_metrics"] = describe_source(files)
                    check = db.execute(
                        "SELECT * FROM initial_checks WHERE task_id=? AND task_version=? "
                        "AND candidate_id=? AND sandbox_cfg_hash=?",
                        (task.id, task.task_version, cid, sandbox_hash),
                    ).fetchone()
                    if check is not None:
                        run_ids.add(check["run_id"])
                        if check["passed"] not in (0, 1):
                            raise EvaluationError("Invalid saved initial-check boolean")
                        sample["initial_status"] = "pass" if check["passed"] else "fail"
            for seq in sequences:
                for rep in range(cfg.editor.reps):
                    rows = (
                        []
                        if db is None or sample["candidate_id"] is None
                        else db.execute(
                            "SELECT * FROM checkpoints WHERE task_id=? AND task_version=? "
                            "AND candidate_id=? AND sequence_id=? AND rep=? AND editor_cfg_hash=? "
                            "ORDER BY step",
                            (
                                task.id,
                                task.task_version,
                                sample["candidate_id"],
                                seq.id,
                                rep,
                                editor_hash,
                            ),
                        ).fetchall()
                    )
                    steps = []
                    # Every sequence/repetition starts from its own original
                    # parent, as the editor saw it: with editor.view_transform
                    # (the comment ablation), the stripped program, so removed
                    # comments don't count as part of the first edit.
                    previous_files = initial_files and view(initial_files)
                    for row in rows:
                        run_ids.add(row["run_id"])
                        source_metrics = None
                        edited_files = None
                        if row["output_blob"] is not None:
                            edited_files = _blob(cfg.runs_dir, row["output_blob"])
                            source_metrics = describe_source(edited_files)
                        steps.append(
                            {
                                k: row[k]
                                for k in (
                                    "step",
                                    "change_id",
                                    "status",
                                    "output_blob",
                                    "new_pass",
                                    "new_total",
                                    "existing_pass",
                                    "existing_total",
                                    "tokens_in",
                                    "tokens_out",
                                    "n_calls",
                                    "wall_s",
                                    "end_reason",
                                    "infra_cause",
                                )
                            }
                        )
                        steps[-1]["source_metrics"] = source_metrics
                        steps[-1]["change_size"] = describe_change(previous_files, edited_files)
                        previous_files = edited_files
                    sample["trials"].append(dict(sequence=seq.id, rep=rep, steps=steps))
            data["samples"].append(sample)
        if db is not None:
            # Original run metadata is evidence, not the current machine's state.
            data["provenance"]["runs"] = [
                dict(row)
                for run_id in sorted(run_ids)
                for row in db.execute(
                    "SELECT run_id, git_commit, git_dirty, config_hash, started_at "
                    "FROM runs WHERE run_id=?",
                    (run_id,),
                )
            ]
    data["provenance"]["source_run_ids"] = sorted(run_ids)
    return validate_dataset(data)
