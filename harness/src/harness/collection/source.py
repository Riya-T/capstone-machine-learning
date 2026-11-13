"""Where a preference pair came from, recorded on every row of preferences.jsonl.

Pairs collected by different people, in different stores, are later joined
into one training set (harness/data/README.md). Each row therefore carries a
`source` block: the run and store that made it, the commit, the result keys,
the task and prompt versions, and `settings`, the parts of the config that
change which pairs come out.

`settings` leaves out what only differs between machines: server addresses,
timeouts and retries, the sandbox runtime and the image's tag and content id
(a Docker image and an Apptainer SIF of the same Dockerfile have different
ids), runs_dir, which tasks were included, samples_per_task and the seed.
Docker and Apptainer runs may therefore be joined, as the team decided: their
limits differ only for programs near the memory limit or the timeout
(sandbox/apptainer.py). `sandbox_runtime` is recorded so a merge can count
the pairs from each. Two people with the
same `settings_hash` ran the same experiment, so their pairs can be joined;
`harness.datasets merge` refuses to join rows whose settings differ.

Usage:
    base = run_source(cfg, keys, run_id="20261112T034705Z-5facee")
    pair["source"] = pair_source(base, task, pair["prompt"])
    settings(cfg)  # the compared settings, as plain JSON
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..config import BackendConfig, ExperimentConfig, canonical
from ..registry import Task
from ..registry import prompt_version as prompt_version_of
from .editor import PROTOCOL_VERSION as EDITOR_PROTOCOL_VERSION

if TYPE_CHECKING:
    from .collect import Keys

# Backend fields that differ between machines but not between experiments.
_MACHINE_ONLY = ("base_url", "request_timeout_s", "max_retries", "retry_backoff_s", "fixtures")


def _file_sha256(path: Path | None) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else None


def _backend(backend: BackendConfig, base_dir: Path) -> dict[str, Any]:
    section = canonical(backend, base_dir)
    out = {k: v for k, v in section.items() if k not in _MACHINE_ONLY}
    if backend.fixtures is not None:  # mock backends: the answers are the model
        out["fixtures_sha256"] = _file_sha256(backend.fixtures)
    return out


def settings(cfg: ExperimentConfig) -> dict[str, Any]:
    """The settings that decide which pairs a run makes, without paths or
    machine-specific values. Prompt templates count by content."""
    base = cfg.base_dir
    editor = canonical(cfg.editor, base)
    editor.update(
        backend=_backend(cfg.editor.backend, base),
        prompt_template=_file_sha256(cfg.editor.prompt_template),
        protocol=EDITOR_PROTOCOL_VERSION,
    )
    sandbox = canonical(cfg.sandbox, base)
    tasks = canonical(cfg.tasks, base)
    return {
        "writer": {
            "backend": _backend(cfg.writer.backend, base),
            "prompt_template": _file_sha256(cfg.writer.prompt_template),
        },
        "editor": editor,
        "sandbox": {k: v for k, v in sandbox.items() if k not in ("image", "build_context")},
        "scorer": canonical(cfg.scorer, base),
        "tasks": {k: v for k, v in tasks.items() if k not in ("dir", "include")},
    }


def settings_hash(value: dict[str, Any]) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_source(cfg: ExperimentConfig, keys: Keys, *, run_id: str | None) -> dict[str, Any]:
    """The part of `source` shared by every pair of one scoring run."""
    from ..store import git_state

    commit, dirty = git_state(Path(__file__).resolve().parent)
    compared = settings(cfg)
    return {
        "run_id": run_id,
        "store": cfg.runs_dir.name,  # e.g. nexus_karin: whose collection this is
        "config": cfg.name,
        "seed": cfg.seed,
        "git_commit": commit,
        "git_dirty": dirty,
        "writer_key": keys.writer,
        "editor_key": keys.editor,
        "sandbox_key": keys.sandbox,
        # Recorded but not compared: Docker and Apptainer pairs may be joined,
        # though their limits differ a little (sandbox/apptainer.py).
        "sandbox_runtime": cfg.execution.sandbox_runtime,
        "settings_hash": settings_hash(compared),
        "settings": compared,
    }


def pair_source(base: dict[str, Any], task: Task, prompt: str) -> dict[str, Any]:
    """`base` plus what is specific to the pair's task."""
    return {**base, "task_version": task.task_version, "prompt_version": prompt_version_of(prompt)}
