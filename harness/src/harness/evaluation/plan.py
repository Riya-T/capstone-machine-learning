"""Strict matched evaluation plans and explicit, isolated collection execution.

Usage:
    prepared = prepare(Path("configs/evaluation.example.yaml"))
    preview(prepared)          # no inference, containers, or store writes
    execute(prepared)          # only an explicit CLI --run calls this
"""

from __future__ import annotations

import dataclasses
import hashlib
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import yaml

from ..collection.collect import collect
from ..config import (
    ConfigError,
    ExperimentConfig,
    InputPath,
    OutputPath,
    load_config,
    parse_dataclass,
)
from ..registry import load_tasks
from ..sandbox.runner import make_runner
from ..store import writer_cfg_hash
from .analysis import compare
from .contract import attach_contract, freeze_contract
from .export import comparison_contract, export_dataset
from .records import EvaluationError, identifier, integer, read_json, trajectory
from .report import json_text, write_report
from .storage import publish_new


@dataclass(frozen=True)
class Method:
    id: str
    config: InputPath
    writer_model: str | None = None
    method_group: str | None = None
    training_seed: int | None = None


@dataclass(frozen=True)
class Plan:
    schema_version: int
    name: str
    output_dir: OutputPath
    methods: tuple[Method, ...]
    generation_seeds: tuple[int, ...]
    reference: str
    purpose: Literal["heldout", "development", "fixture"] = "heldout"
    bootstrap_samples: int = 2000
    bootstrap_seed: int = 20261105
    confidence: float = 0.95
    max_method_runs: int = 64
    max_edit_checkpoints: int = 4096


@dataclass(frozen=True)
class Prepared:
    plan: Plan
    configs: tuple[ExperimentConfig, ...]
    signature: dict
    digest: str
    root: Path
    source_path: Path


def _hash(value):
    return hashlib.sha256(json_text(value).encode()).hexdigest()


def _schedule(plan):
    """Rotate writer order between generation seeds; each job stays sequential."""
    count = len(plan.methods)
    return [
        dict(method=plan.methods[index].id, method_index=index, generation_seed=seed)
        for number, seed in enumerate(plan.generation_seeds)
        for index in [(offset + number) % count for offset in range(count)]
    ]


def prepare(path: Path) -> Prepared:
    path = Path(path).resolve()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf8"))
    except (OSError, yaml.YAMLError) as exc:
        raise EvaluationError(f"Cannot read evaluation plan: {exc}") from exc
    plan = parse_dataclass(Plan, raw, base_dir=path.parent, where="evaluation")
    if plan.schema_version != 1:
        raise EvaluationError("Unsupported evaluation plan schema")
    identifier(plan.name, "plan name")
    ids = [identifier(m.id, "method") for m in plan.methods]
    if not ids or len(ids) != len({i.casefold() for i in ids}) or plan.reference not in ids:
        raise EvaluationError("Methods must be unique and include the reference")
    if not plan.generation_seeds or len(set(plan.generation_seeds)) != len(plan.generation_seeds):
        raise EvaluationError("Generation seeds must be nonempty and unique")
    for seed in plan.generation_seeds:
        integer(seed, "generation seed")
        if seed > 2147483647:
            raise EvaluationError("Generation seed must fit the existing 31-bit backend")
    for name in ("bootstrap_samples", "max_method_runs", "max_edit_checkpoints"):
        integer(getattr(plan, name), name, 1)
    integer(plan.bootstrap_seed, "bootstrap_seed")
    if plan.bootstrap_samples > 20000 or not 0 < plan.confidence < 1:
        raise EvaluationError("Invalid bootstrap count or confidence")
    if len(ids) * len(plan.generation_seeds) > plan.max_method_runs:
        raise EvaluationError("Plan exceeds max_method_runs")
    configs, descriptions = [], []
    contract = task_signature = runtime = None
    checkpoints = 0
    for method in plan.methods:
        original = load_config(method.config)
        if method.method_group is not None:
            identifier(method.method_group, "method_group")
        if method.training_seed is not None:
            integer(method.training_seed, "training_seed")
        if method.writer_model is not None:
            if not method.writer_model.strip() or "\x00" in method.writer_model:
                raise EvaluationError("writer_model must name a served checkpoint")
            original = dataclasses.replace(
                original,
                writer=dataclasses.replace(
                    original.writer,
                    backend=dataclasses.replace(original.writer.backend, model=method.writer_model),
                ),
            )
        cfg = dataclasses.replace(
            original,
            writer=dataclasses.replace(original.writer, samples_per_task=1),
            tasks=dataclasses.replace(original.tasks, max_programs=1),
        )
        tasks = load_tasks(cfg.tasks)
        expected = {"heldout": "eval", "development": "dev"}.get(plan.purpose)
        if expected and any(t.split != expected for t in tasks.values()):
            raise EvaluationError(f"{method.id}: {plan.purpose} requires {expected} tasks")
        if plan.purpose == "fixture" and any(
            b.kind != "mock" for b in (cfg.writer.backend, cfg.editor.backend)
        ):
            raise EvaluationError("Fixture plans require mock writer and editor")
        current_tasks = {
            t.id: dict(
                version=t.task_version,
                family=t.family,
                split=t.split,
                sequences={
                    s.id: [x.change.id for x in s.steps]
                    for s in t.sequences[: cfg.tasks.max_sequences]
                },
            )
            for t in tasks.values()
        }
        current_contract = comparison_contract(cfg, "image-resolved-at-execution")
        if contract is not None and (
            current_contract != contract
            or current_tasks != task_signature
            or cfg.execution.sandbox_runtime != runtime
        ):
            raise EvaluationError("Methods must use matched tasks, editor, budgets and sandbox")
        contract, task_signature, runtime = (
            current_contract,
            current_tasks,
            cfg.execution.sandbox_runtime,
        )
        out = plan.output_dir.resolve()
        if (
            out == original.runs_dir.resolve()
            or out.is_relative_to((original.runs_dir / "blobs").resolve())
            or out.is_relative_to(cfg.tasks.dir.resolve())
        ):
            raise EvaluationError(
                "Evaluation output must not replace an original store or task data"
            )
        steps = sum(
            len(s.steps) for t in tasks.values() for s in t.sequences[: cfg.tasks.max_sequences]
        )
        checkpoints += steps * cfg.editor.reps * len(plan.generation_seeds)
        configs.append(cfg)
        descriptions.append(
            dict(
                method=method.id,
                resolved_config=cfg.to_dict(),
                writer_identity=writer_cfg_hash(cfg),
                method_group=method.method_group or method.id,
                training_seed=method.training_seed,
            )
        )
    if checkpoints > plan.max_edit_checkpoints:
        raise EvaluationError("Plan exceeds max_edit_checkpoints")
    groups = {}
    for description in descriptions:
        groups.setdefault(description["method_group"], []).append(description)
    for name, members in groups.items():
        if len(members) < 2:
            continue
        seeds = [m["training_seed"] for m in members]
        if None in seeds or len(set(seeds)) != len(seeds):
            raise EvaluationError(
                f"{name}: replicate checkpoints need distinct training_seed values"
            )
        if len({m["writer_identity"] for m in members}) != len(members):
            raise EvaluationError(
                f"{name}: replicate checkpoints must have distinct writer identities"
            )
    source_root = Path(__file__).resolve().parents[1]
    sources = {
        p.relative_to(source_root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in source_root.rglob("*.py")
    }
    signature = dict(
        schema_version=1,
        name=plan.name,
        purpose=plan.purpose,
        reference=plan.reference,
        generation_seeds=list(plan.generation_seeds),
        methods=descriptions,
        schedule=_schedule(plan),
        tasks=task_signature,
        comparison_contract=contract,
        bootstrap=dict(
            samples=plan.bootstrap_samples, seed=plan.bootstrap_seed, confidence=plan.confidence
        ),
        source_hashes=sources,
        max_edit_checkpoints=plan.max_edit_checkpoints,
        max_method_runs=plan.max_method_runs,
    )
    digest = _hash(signature)
    return Prepared(
        plan, tuple(configs), signature, digest, plan.output_dir / plan.name / digest[:16], path
    )


def preview(prepared: Prepared) -> dict:
    p = prepared.plan
    writer_calls = edit_steps = turn_calls = output_tokens = 0
    for cfg in prepared.configs:
        tasks = load_tasks(cfg.tasks)
        writers = len(tasks) * len(p.generation_seeds)
        steps = sum(
            len(s.steps) for t in tasks.values() for s in t.sequences[: cfg.tasks.max_sequences]
        )
        steps *= cfg.editor.reps * len(p.generation_seeds)
        writer_calls += writers
        edit_steps += steps
        turns = steps * cfg.editor.budget.max_turns
        turn_calls += turns
        output_tokens += (
            writers * cfg.writer.backend.max_tokens + turns * cfg.editor.backend.max_tokens
        )
    return dict(
        mode="dry-run",
        purpose=p.purpose,
        fingerprint=prepared.digest,
        output_directory=str(prepared.root),
        reference=p.reference,
        methods=[m.id for m in p.methods],
        method_metadata=[
            dict(
                method=m.id,
                method_group=m.method_group or m.id,
                training_seed=m.training_seed,
                writer_model=cfg.writer.backend.model,
            )
            for m, cfg in zip(p.methods, prepared.configs, strict=True)
        ],
        generation_seeds=list(p.generation_seeds),
        schedule=prepared.signature["schedule"],
        task_ids=sorted(prepared.signature["tasks"]),
        writer_samples_per_task_seed=1,
        selection_of_passing_alternatives=False,
        max_writer_generations=writer_calls,
        max_edit_checkpoints=edit_steps,
        max_editor_generations=turn_calls,
        max_generated_tokens=output_tokens,
        inference_performed=False,
        source_stores_modified=False,
        note="Logical generation bounds exclude the backend's HTTP retries. --run is explicit.",
    )


def _job(prepared, index, seed):
    # Separate stores prevent the collector's sample cache from merging generation seeds.
    cfg = prepared.configs[index]
    return dataclasses.replace(
        cfg,
        name=f"evaluation-{prepared.plan.methods[index].id}-{seed}",
        seed=seed,
        runs_dir=prepared.root / "stores" / prepared.plan.methods[index].id / str(seed),
    )


def _local_only(cfg):
    # A preview or accidental configuration change must not turn into paid remote inference.
    for backend in (cfg.writer.backend, cfg.editor.backend):
        if backend.kind == "mock":
            continue
        url = urlparse(backend.base_url or "")
        if (
            url.scheme not in ("http", "https")
            or url.hostname not in ("localhost", "127.0.0.1", "::1")
            or url.username
            or url.password
        ):
            raise EvaluationError("Real execution supports local loopback endpoints only")
        if "REPLACE" in backend.model:
            raise EvaluationError("Configure a locally served trained writer before --run")
        if backend.model.casefold().endswith((":cloud", "-cloud")):
            raise EvaluationError("Cloud-routed model tags are not authorized for local evaluation")


@contextmanager
def _controller(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".controller.lock").open("a+b") as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if __import__("os").name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise EvaluationError(
                "Another evaluation controller owns this output directory"
            ) from exc
        try:
            yield
        finally:
            if __import__("os").name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _complete(dataset):
    lengths = {
        (task["id"], seq["id"]): len(seq["changes"])
        for task in dataset["tasks"]
        for seq in task["sequences"]
    }
    return all(
        trajectory(sample, trial, lengths[sample["task"], trial["sequence"]])["score"] is not None
        for sample in dataset["samples"]
        for trial in sample["trials"]
    )


def _write_new(path, value):
    publish_new(path, json_text(value).encode("utf8"))


def _assert_current(prepared):
    # Source files and prompts can change after preview, so freeze checks also run at execution.
    try:
        current = prepare(prepared.source_path)
    except (ConfigError, OSError) as exc:
        raise EvaluationError(f"Inputs changed since preparation: {exc}") from exc
    if current.signature != prepared.signature or current.root != prepared.root:
        raise EvaluationError(
            "Inputs changed since preparation; preserve this run and prepare again"
        )


def _metadata(path, fields):
    value = read_json(path.read_text(encoding="utf8"))
    if not isinstance(value, dict) or not fields <= value.keys():
        raise EvaluationError(f"Malformed evaluation metadata: {path.name}")
    return value


def execute(prepared: Prepared, *, export_only: bool = False) -> dict:
    """Run the existing collector sequentially in new stores, or export saved-only."""
    _assert_current(prepared)
    p, root = prepared.plan, prepared.root
    lock_path = root / "evaluation.lock.json"
    if export_only and not lock_path.exists():
        raise EvaluationError("No frozen evaluation here; --export-only never creates a run")
    if not export_only:
        for cfg in prepared.configs:
            _local_only(cfg)
    with _controller(root):
        if lock_path.exists():
            lock = _metadata(lock_path, {"signature", "image_id"})
            if (
                lock["signature"] != prepared.signature
                or not isinstance(lock["image_id"], str)
                or not lock["image_id"]
            ):
                raise EvaluationError("Evaluation lock does not match current inputs")
        else:
            if set(x.name for x in root.iterdir()) != {".controller.lock"}:
                raise EvaluationError("Refusing a nonempty, unowned output directory")
            runners = [make_runner(cfg, owner="evaluation-preflight") for cfg in prepared.configs]
            image_ids = [r.ensure_image() for r in runners]
            if len(set(image_ids)) != 1:
                raise EvaluationError("Methods resolved different sandbox images")
            lock = dict(signature=prepared.signature, image_id=image_ids[0])
            _write_new(lock_path, lock)
        analysis_contract = freeze_contract(prepared)
        _write_new(root / "analysis.contract.json", analysis_contract)
        datasets = []
        for job in prepared.signature["schedule"]:
            i, seed = job["method_index"], job["generation_seed"]
            method = p.methods[i]
            _assert_current(prepared)
            cfg = _job(prepared, i, seed)
            marker = cfg.runs_dir / "evaluation.completed.json"
            metadata = dict(
                method=method.id,
                purpose=p.purpose,
                method_group=method.method_group,
                training_seed=method.training_seed,
            )
            dataset = export_dataset(cfg, lock["image_id"], **metadata)
            if marker.exists():
                if _metadata(marker, {"dataset_hash"})["dataset_hash"] != _hash(dataset):
                    raise EvaluationError("Completed saved evaluation changed; refusing to rerun")
            elif not export_only:
                # Image verification happens before any model calls in this job.
                runner = make_runner(cfg, owner="evaluation-preflight")
                if runner.ensure_image() != lock["image_id"]:
                    raise EvaluationError("Sandbox image changed; existing scores are preserved")
                _assert_current(prepared)
                stats = collect(cfg)
                _assert_current(prepared)
                if runner.existing_image_id() != lock["image_id"]:
                    raise EvaluationError("Sandbox image changed during collection")
                dataset = export_dataset(cfg, lock["image_id"], **metadata)
                if _complete(dataset):
                    # Only resolved trials earn a completion marker.
                    # Normal code failures are terminal outcomes, not missing work.
                    _write_new(marker, dict(dataset_hash=_hash(dataset), run_id=stats.run_id))
            datasets.append(dataset)
            snapshot = root / "exports" / f"{method.id}-{seed}-{_hash(dataset)[:16]}.json"
            _write_new(snapshot, dataset)
        result = compare(
            datasets,
            reference=p.reference,
            bootstrap_samples=p.bootstrap_samples,
            bootstrap_seed=p.bootstrap_seed,
            confidence=p.confidence,
        )
        report_root = root / "reports" / _hash(datasets)[:16]
        attach_contract(result, analysis_contract)
        paths = write_report(result, report_root)
        return dict(
            complete=all(_complete(d) for d in datasets),
            report_directory=str(report_root),
            reports={k: str(v) for k, v in paths.items()},
            purpose=p.purpose,
            fingerprint=prepared.digest,
            inference_requested=not export_only,
        )
