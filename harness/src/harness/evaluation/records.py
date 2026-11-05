"""Validate exported evaluation records and interpret stopped trajectories.

Usage:
    validate_dataset(dataset)
    outcome = trajectory(sample, trial, sequence_length)
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

from ..collection.scorer import trial_score
from ..config import ConfigError
from ..store import FAILED

VERSION = 1
PURPOSES = {"heldout", "development", "fixture"}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}
HASH = re.compile(r"[0-9a-f]{64}")
STATUSES = FAILED | {"success", "infra_error"}


class EvaluationError(ConfigError):
    """An invalid evaluation plan, record, or comparison."""


def read_json(text: str | bytes):
    """Reject ambiguous keys and nonstandard numeric constants in saved evidence."""

    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise EvaluationError(f"Duplicate JSON key: {key}")
            out[key] = value
        return out

    def constant(value):
        raise EvaluationError(f"Nonstandard JSON constant: {value}")

    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise EvaluationError(f"Nonfinite JSON number: {value}")
        return result

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=number)


def identifier(value: Any, where: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value) or value.upper() in RESERVED:
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
    integer(data["schema_version"], "schema_version", 1)
    if data["schema_version"] != VERSION:
        raise EvaluationError("Unsupported evaluation record schema")
    identifier(data["method"], "method")
    integer(data["generation_seed"], "generation_seed")
    if data["purpose"] not in PURPOSES:
        raise EvaluationError("Unknown evaluation purpose")
    integer(data["editor_reps"], "editor_reps", 1)
    if not isinstance(data["contract"], dict) or not data["contract"]:
        raise EvaluationError("Missing comparison contract")
    for key in ("tasks", "samples"):
        if not isinstance(data[key], list):
            raise EvaluationError(f"{key}: expected an array")
    if "writer_identity" in data and not HASH.fullmatch(data["writer_identity"]):
        raise EvaluationError("Invalid writer identity hash")
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
        if not isinstance(task["sequences"], list):
            raise EvaluationError("sequences: expected an array")
        for seq in task["sequences"]:
            identifier(seq["id"], "sequence")
            if seq["id"] in sequences or not seq["changes"]:
                raise EvaluationError("Duplicate or empty sequence")
            if not isinstance(seq["changes"], list):
                raise EvaluationError("changes: expected an array")
            for change in seq["changes"]:
                identifier(change, "change")
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
        if sample["initial_status"] == "parse_failure" and cid is not None:
            raise EvaluationError("Parse failure cannot have a parsed source hash")
        for name in ("tokens_in", "tokens_out", "wall_s"):
            cost(sample["writer_cost"][name], name, integral=name != "wall_s")
        _source_metrics(sample.get("source_metrics"))
        seen = set()
        if not isinstance(sample["trials"], list):
            raise EvaluationError("trials: expected an array")
        for trial in sample["trials"]:
            key = (trial["sequence"], trial["rep"])
            integer(trial["rep"], "rep")
            if key in seen or key[0] not in tasks[task_id] or trial["rep"] >= data["editor_reps"]:
                raise EvaluationError("Duplicate, unexpected, or out-of-range trajectory")
            seen.add(key)
            changes = tasks[task_id][key[0]]
            stopped = False
            if not isinstance(trial["steps"], list):
                raise EvaluationError("steps: expected an array")
            for number, step in enumerate(trial["steps"], 1):
                integer(step["step"], "step", 1)
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
                if step.get("output_blob") is not None and not HASH.fullmatch(step["output_blob"]):
                    raise EvaluationError("Invalid edited source hash")
                if "n_calls" in step:
                    cost(step["n_calls"], "n_calls", integral=True)
                _test_counts(step)
                _source_metrics(step.get("source_metrics"))
                edit_size = step.get("change_size")
                if edit_size is not None:
                    if not isinstance(edit_size, dict):
                        raise EvaluationError("change_size: expected an object or null")
                    for key in (
                        "files_changed",
                        "files_added",
                        "files_removed",
                        "bytes_before",
                        "bytes_after",
                        "python_lines_added",
                        "python_lines_removed",
                    ):
                        cost(edit_size.get(key), key, integral=True)
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


def _source_metrics(value):
    if value is None:
        return
    if not isinstance(value, dict):
        raise EvaluationError("source_metrics: expected an object or null")
    for name in (
        "source_files",
        "source_lines",
        "python_files",
        "python_lines",
        "python_comment_lines",
        "python_docstring_lines",
        "python_documentation_lines",
    ):
        if name in value:
            cost(value[name], name, integral=True)
    density = value.get("python_documentation_density")
    cost(density, "python_documentation_density")
    if density is not None and density > 1:
        raise EvaluationError("Documentation density exceeds one")
    if (
        value.get("python_syntax_valid") is not None
        and type(value["python_syntax_valid"]) is not bool
    ):
        raise EvaluationError("python_syntax_valid: expected a boolean or null")


def _test_counts(step):
    """Check supplied evidence; legacy exports may have no test-count fields."""
    flags = {}
    for suite in ("new", "existing"):
        passed, total = step.get(suite + "_pass"), step.get(suite + "_total")
        if passed is None and total is None:
            continue
        integer(passed, suite + "_pass")
        integer(total, suite + "_total")
        if passed > total:
            raise EvaluationError("Passed tests exceed total tests")
        flags[suite] = passed == total
    expected = {
        "success": {"new": True, "existing": True},
        "fail_new": {"new": False, "existing": True},
        "fail_existing": {"new": True, "existing": False},
        "fail_both": {"new": False, "existing": False},
    }.get(step["status"], {})
    # A timeout/collection failure can have 0/0 (or even all cases passed).
    # Counts alone cannot certify a suite passed; they can contradict a claimed pass.
    if any(expected.get(k) is True and not value for k, value in flags.items()):
        raise EvaluationError("Editing status contradicts recorded private test counts")
