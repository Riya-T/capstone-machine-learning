"""Collection: runs the whole pipeline for the tasks in a config.

For each task:
1. Writer samples: ask the writer for N programs (one seed each) and parse them.
2. Initial checks: run each distinct program against the public checks and
   the hidden initial tests.
3. Editing trials: take each passing program (the first tasks.max_programs
   of them) through every change sequence, editor.reps times. A trial stops
   at its first failed step.
4. Scoring: write preferences.jsonl and preferences_report.json to the
   run's directory.

Everything resumes: finished samples, checks and steps are skipped, a
half-done trial continues from its first unfinished step (replaying saved
model answers), and infrastructure errors are retried. A rerun of a
finished collection makes no model calls.

Usage:
    python -m harness collect --config configs/mock.yaml
    stats = collect(load_config("configs/mock.yaml"))
    stats.model_calls, stats.run_dir
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..config import ExperimentConfig
from ..models.backends import BackendError, CachedBackend, derive_seed, make_backend
from ..models.parser import parse_program
from ..registry import ChangeSequence, Program, Task, build_writer_prompt, load_tasks, load_template
from ..registry import prompt_version as prompt_version_of
from ..sandbox.evaluator import Evaluator
from ..sandbox.runner import SandboxError, make_runner
from ..store import (
    Candidate,
    CandidateKey,
    Checkpoint,
    InitialCheck,
    Store,
    TrialKey,
    editor_cfg_hash,
    resume_point,
    sandbox_cfg_hash,
    writer_cfg_hash,
)
from .editor import Editor
from .scorer import Scorer, ScoreResult, load_task_record, summary_table, write_outputs

log = logging.getLogger("harness")


@dataclass
class CollectStats:
    run_id: str = ""
    run_dir: Path = field(default_factory=Path)
    model_calls: int = 0  # calls that reached a model (cache misses)
    samples_recorded: int = 0
    initial_checks_recorded: int = 0
    steps_recorded: int = 0
    infra_errors: int = 0  # left unrecorded or recorded as infra_error; retried next run
    pairs: int = 0


@dataclass(frozen=True)
class Keys:
    """The configuration keys results are stored under."""

    writer: str
    editor: str
    sandbox: str

    @classmethod
    def of(cls, cfg: ExperimentConfig, image_id: str) -> Keys:
        return cls(
            writer_cfg_hash(cfg), editor_cfg_hash(cfg, image_id), sandbox_cfg_hash(cfg, image_id)
        )


def sandbox_owner(cfg: ExperimentConfig) -> str:
    """Container label for this store, so sweeping leftovers from a crashed
    run never touches another store's containers (Docker only)."""
    return f"collect-{cfg.component_hash(cfg.runs_dir)[:12]}"


STAGES = ("writer", "initial", "edit")


def collect(cfg: ExperimentConfig, until: str = "edit") -> CollectStats:
    """Run the stages up to and including `until` (writer, initial or edit),
    then write the preference files and summary for whatever is collected.
    Running again with a later stage continues from there."""
    if until not in STAGES:
        raise ValueError(f"until must be one of {STAGES}, got {until!r}")
    scorer = Scorer(cfg.scorer, cfg.editor.reps)  # fail on a bad scorer config before any work
    tasks = load_tasks(cfg.tasks)
    stats = CollectStats()
    runner = make_runner(cfg, owner=sandbox_owner(cfg))
    image_id = runner.ensure_image()
    removed = runner.sweep()
    if removed:
        log.info("removed %d sandbox containers left by an earlier run", removed)
    keys = Keys.of(cfg, image_id)
    evaluator = Evaluator(runner, workers=cfg.execution.sandbox_workers)
    editor = Editor(cfg.editor, evaluator)
    template = load_template(cfg.writer.prompt_template)

    with Store(cfg.runs_dir) as store:
        stats.run_id = store.start_run(cfg)
        stats.run_dir = store.runs_dir / stats.run_id
        log.info(
            "run %s: %d tasks, image %s, until %s", stats.run_id, len(tasks), image_id[:19], until
        )
        for task in tasks.values():
            prompt = build_writer_prompt(task.writer_view(), template)
            _write_samples(cfg, store, task, prompt, keys, stats)
            if until == "writer":
                continue
            programs = _distinct_programs(store, task, prompt, keys)
            passed = _initial_checks(store, evaluator, task, programs, keys, stats)
            log.info(
                "%s: %d distinct programs, %d passed initially", task.id, len(programs), len(passed)
            )
            if until == "initial":
                continue
            passed = passed[: cfg.tasks.max_programs]
            for n, cid in enumerate(passed, start=1):
                for sequence in task.sequences[: cfg.tasks.max_sequences]:
                    for rep in range(cfg.editor.reps):
                        _run_trial(
                            cfg, store, editor, evaluator, task, cid, sequence, rep, keys, stats
                        )
                log.info("%s: trials done for candidate %d/%d", task.id, n, len(passed))
        result = score(cfg, store, tasks, keys, stats.run_dir, scorer)
        stats.pairs = len(result.pairs)
    print(summary_table(result.report), flush=True)
    log.info(
        "run %s finished: %d model calls, %d samples, %d checks and %d steps recorded, "
        "%d infra errors, %d pairs",
        stats.run_id, stats.model_calls, stats.samples_recorded, stats.initial_checks_recorded,
        stats.steps_recorded, stats.infra_errors, stats.pairs,
    )  # fmt: skip
    return stats


def report(cfg: ExperimentConfig, out_dir: Path | None = None) -> ScoreResult:
    """Rebuild preferences.jsonl and preferences_report.json from the store.
    Builds no backend and runs no container; the sandbox image must exist
    (its id is part of the result keys)."""
    runner = make_runner(cfg, owner=sandbox_owner(cfg))
    image_id = runner.existing_image_id()
    if image_id is None:
        image = cfg.execution.apptainer_image or cfg.sandbox.image
        raise SandboxError(f"image {image} not found; results are keyed by its id")
    out = out_dir or cfg.runs_dir / "report"
    with Store(cfg.runs_dir) as store:
        result = score(cfg, store, load_tasks(cfg.tasks), Keys.of(cfg, image_id), out)
    log.info("report written to %s: %d pairs", out, len(result.pairs))
    print(summary_table(result.report), flush=True)
    return result


def score(cfg, store: Store, tasks: dict[str, Task], keys: Keys, out_dir: Path, scorer=None):
    scorer = scorer or Scorer(cfg.scorer, cfg.editor.reps)
    template = load_template(cfg.writer.prompt_template)
    records = [
        load_task_record(
            store,
            task,
            build_writer_prompt(task.writer_view(), template),
            writer_hash=keys.writer,
            sandbox_hash=keys.sandbox,
            editor_hash=keys.editor,
            editor_reps=cfg.editor.reps,
            max_sequences=cfg.tasks.max_sequences,
            max_programs=cfg.tasks.max_programs,
        )
        for task in tasks.values()
    ]
    result = scorer.build(records, store.get_blob)
    write_outputs(result, out_dir)
    return result


# --- stages -----------------------------------------------------------------


def _write_samples(cfg, store: Store, task: Task, prompt: str, keys: Keys, stats) -> None:
    pv = prompt_version_of(prompt)
    for i in range(cfg.writer.samples_per_task):
        key = CandidateKey(task.id, pv, keys.writer, i)
        if store.get_candidate(key) is not None:
            continue
        backend = CachedBackend(
            make_backend(cfg.writer.backend, derive_seed(cfg.seed, task.id, "writer", i)), store
        )
        start = time.monotonic()
        try:
            answer = backend.generate(prompt)
        except BackendError as exc:
            log.warning("%s sample %d: writer call failed (retried next run): %s", task.id, i, exc)
            stats.infra_errors += 1
            continue
        stats.model_calls += backend.model_calls
        usage = backend.last_usage
        parsed = parse_program(answer, task.entry_files, usage.finish_reason if usage else None)
        store.record_candidate(
            Candidate(
                key=key,
                candidate_id=store.put_blob(parsed.files) if parsed.ok else None,
                parse_error=None if parsed.ok else str(parsed.failure),
                tokens_in=usage.prompt_tokens if usage else None,
                tokens_out=usage.completion_tokens if usage else None,
                wall_s=time.monotonic() - start,
                run_id=stats.run_id,
                call_key=backend.last_key,
            )
        )
        stats.samples_recorded += 1
        log.info("%s sample %d: %s", task.id, i, "parsed" if parsed.ok else parsed.failure)


def _distinct_programs(store: Store, task: Task, prompt: str, keys: Keys) -> list[str]:
    """Parsed candidate ids, each once, in order of first sample."""
    seen: list[str] = []
    for c in store.candidates(task.id, prompt_version_of(prompt), keys.writer):
        if c.candidate_id is not None and c.candidate_id not in seen:
            seen.append(c.candidate_id)
    return seen


def _initial_checks(store, evaluator, task, programs, keys, stats) -> list[str]:
    passed = []
    for cid in programs:
        check = store.get_initial_check(task.id, task.task_version, cid, keys.sandbox)
        if check is None:
            result = evaluator.check_initial(store.get_blob(cid), task)
            if result.status == "infra_error":
                log.warning("%s %s: initial check infra error (retried next run)", task.id, cid[:8])
                stats.infra_errors += 1
                continue
            check = InitialCheck(
                task.id,
                task.task_version,
                cid,
                keys.sandbox,
                result.passed,
                {"public": result.public.to_dict(), "initial": result.initial.to_dict()},
                stats.run_id,
            )
            store.record_initial_check(check)
            stats.initial_checks_recorded += 1
        if check.passed:
            passed.append(cid)
    return passed


def _run_trial(
    cfg: ExperimentConfig,
    store: Store,
    editor: Editor,
    evaluator: Evaluator,
    task: Task,
    cid: str,
    sequence: ChangeSequence,
    rep: int,
    keys: Keys,
    stats: CollectStats,
) -> None:
    trial = TrialKey(task.id, task.task_version, cid, sequence.id, rep, keys.editor)
    recorded = store.trial_steps(trial)
    point = resume_point(recorded, len(sequence.steps))
    if point.next_step is None:
        return
    # Calls made by the steps already done; the resumed step's calls start
    # there, so any it made before an interruption replay from the cache.
    start_index = sum(c.n_calls or 0 for c in recorded if c.step < point.next_step)
    seed = derive_seed(cfg.seed, task.id, cid, sequence.id, rep, "editor")
    backend = CachedBackend(make_backend(cfg.editor.backend, seed), store, start_index)
    program: Program = store.get_blob(point.input_blob or cid)

    statuses = []
    for step in sequence.steps[point.next_step - 1 :]:
        start = time.monotonic()
        outcome = editor.edit(backend, program, step)
        counts: dict = {}
        infra_cause = outcome.infra_cause or None
        if outcome.status == "done":
            evaluation = evaluator.check_step(outcome.program, step)
            status = evaluation.status
            infra_cause = evaluation.infra_cause or None
            counts = {
                "new_pass": evaluation.new_feature.passed,
                "new_total": evaluation.new_feature.total,
                "existing_pass": evaluation.existing.passed,
                "existing_total": evaluation.existing.total,
            }
        else:
            status = outcome.status  # budget_exhausted or infra_error
        store.record_checkpoint(
            Checkpoint(
                trial=trial,
                step=step.number,
                change_id=step.change.id,
                status=status,
                output_blob=store.put_blob(outcome.program),
                tokens_in=outcome.tokens_in,
                tokens_out=outcome.tokens_out,
                n_calls=outcome.model_calls,
                wall_s=time.monotonic() - start,
                diff_lines=outcome.diff_lines,
                run_id=stats.run_id,
                infra_cause=infra_cause if status == "infra_error" else None,
                end_reason=outcome.reason,
                **counts,
            )
        )
        stats.steps_recorded += 1
        statuses.append(status)
        if status == "infra_error":
            stats.infra_errors += 1
        if status != "success":
            break
        program = outcome.program
    stats.model_calls += backend.model_calls
    log.info("%s %s %s rep %d: %s", task.id, cid[:8], sequence.id, rep, ", ".join(statuses))
