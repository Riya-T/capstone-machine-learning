"""Validate exported evaluation records and interpret stopped trajectories.

Usage:
    validate_dataset(dataset)
    outcome = trajectory(sample, trial, sequence_length)
"""

from __future__ import annotations

import math
import re
from typing import Any

from ..collection.scorer import trial_score
from ..config import ConfigError
from ..store import FAILED

VERSION = 1
PURPOSES = {"heldout", "development", "fixture"}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
HASH = re.compile(r"[0-9a-f]{64}")
STATUSES = FAILED | {"success", "infra_error"}


class EvaluationError(ConfigError):
    """An invalid evaluation plan, record, or comparison."""


def identifier(value: Any, where: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise EvaluationError(f"{where}: expected a simple identifier, not a path")
    return value


def integer(value: Any, where: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise EvaluationError(f"{where}: expected an integer >= {minimum}")
    return value


def cost(value: Any, where: str, *, integral: bool = False) -> None:
    if value is None:
        return
    if (
        type(value) not in (int, float)
        or not math.isfinite(value)
        or value < 0
        or (integral and type(value) is not int)
    ):
        raise EvaluationError(f"{where}: expected a finite nonnegative number or null")


def trajectory(sample: dict, trial: dict, length: int) -> dict:
    """Use the existing consecutive-change scorer; never award partial tests."""
    initial = sample["initial_status"]
    steps = trial["steps"]
    if initial != "pass":
        if steps:
            raise EvaluationError("An initially failing/unresolved program has editing steps")
        return dict(
            score=0 if initial in ("fail", "parse_failure") else None,
            status="not_reached_initial_failure" if initial != "unresolved" else "unresolved",
            completed_prefix=0,
        )
    score = trial_score({s["step"]: s["status"] for s in steps}, length)
    prefix = sum(s["status"] == "success" for s in steps)
    if isinstance(score, int):
        return dict(
            score=score,
            status="success" if score == length else steps[-1]["status"],
            completed_prefix=prefix,
        )
    return dict(score=None, status=score, completed_prefix=prefix)


def validate_dataset(data: dict) -> dict:
    """Fail closed on corrupt/ambiguous data instead of silently changing scores."""
    try:
        return _validate(data)
    except (KeyError, TypeError, AttributeError) as exc:
        raise EvaluationError(f"Malformed evaluation record: {exc}") from exc


def _validate(data: dict) -> dict:
    if data["schema_version"] != VERSION:
        raise EvaluationError("Unsupported evaluation record schema")
    identifier(data["method"], "method")
    integer(data["generation_seed"], "generation_seed")
    if data["purpose"] not in PURPOSES:
        raise EvaluationError("Unknown evaluation purpose")
    integer(data["editor_reps"], "editor_reps", 1)
    if not isinstance(data["contract"], dict) or not data["contract"]:
        raise EvaluationError("Missing comparison contract")
    tasks = {}
    for task in data["tasks"]:
        identifier(task["id"], "task id")
        identifier(task["family"], "family")
        if task["id"] in tasks or not HASH.fullmatch(task["version"]):
            raise EvaluationError("Duplicate task or invalid task version")
        expected_split = {"heldout": "eval", "development": "dev"}.get(data["purpose"])
        if expected_split and task["split"] != expected_split:
            raise EvaluationError("Task split does not match evaluation purpose")
        sequences = {}
        for seq in task["sequences"]:
            identifier(seq["id"], "sequence")
            if seq["id"] in sequences or not seq["changes"]:
                raise EvaluationError("Duplicate or empty sequence")
            if len(set(seq["changes"])) != len(seq["changes"]):
                raise EvaluationError("A sequence repeats a change")
            sequences[seq["id"]] = seq["changes"]
        if not sequences:
            raise EvaluationError("Task has no sequences")
        tasks[task["id"]] = sequences
    if not tasks:
        raise EvaluationError("Evaluation has no tasks")
    samples = set()
    for sample in data["samples"]:
        task_id = sample["task"]
        if task_id not in tasks or task_id in samples:
            raise EvaluationError("Unknown task or duplicate initial sample")
        samples.add(task_id)
        if sample["initial_status"] not in ("pass", "fail", "parse_failure", "unresolved"):
            raise EvaluationError("Unknown initial status")
        cid = sample["candidate_id"]
        if cid is not None and not HASH.fullmatch(cid):
            raise EvaluationError("Invalid candidate source hash")
        if sample["initial_status"] in ("pass", "fail") and cid is None:
            raise EvaluationError("Evaluated initial program has no source hash")
        for name in ("tokens_in", "tokens_out", "wall_s"):
            cost(sample["writer_cost"][name], name, integral=name != "wall_s")
        seen = set()
        for trial in sample["trials"]:
            key = (trial["sequence"], trial["rep"])
            integer(trial["rep"], "rep")
            if key in seen or key[0] not in tasks[task_id] or trial["rep"] >= data["editor_reps"]:
                raise EvaluationError("Duplicate, unexpected, or out-of-range trajectory")
            seen.add(key)
            changes = tasks[task_id][key[0]]
            stopped = False
            for number, step in enumerate(trial["steps"], 1):
                if (
                    stopped
                    or step["step"] != number
                    or number > len(changes)
                    or step["change_id"] != changes[number - 1]
                ):
                    raise EvaluationError("Editing steps are out of order or follow a failure")
                if step["status"] not in STATUSES:
                    raise EvaluationError("Unknown editing status")
                stopped = step["status"] != "success"
                for name in ("tokens_in", "tokens_out", "wall_s"):
                    cost(step[name], name, integral=name != "wall_s")
            trajectory(sample, trial, len(changes))
        expected = {(seq, rep) for seq in tasks[task_id] for rep in range(data["editor_reps"])}
        if seen != expected:
            raise EvaluationError(
                "Record must represent every scheduled trajectory, even if missing"
            )
    if samples != set(tasks):
        raise EvaluationError("Record must represent every scheduled initial sample")
    return data
