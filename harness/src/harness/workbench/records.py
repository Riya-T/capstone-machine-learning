"""Validate portable multi-sample evidence and derive selection from sample order.

Usage: validate_collection(read_json(path.read_bytes()))
The one-sample evaluation schema remains unchanged.
"""

from __future__ import annotations

from collections import Counter

from ..evaluation.records import (
    HASH,
    EvaluationError,
    cost,
    identifier,
    integer,
    validate_dataset,
)

VERSION = 1
KIND = "saved_collection"
PURPOSES = {"training": "train", "development": "dev", "heldout": "eval", "fixture": None}
INITIAL = {"pass", "fail", "parse_failure", "unresolved", "infra_error"}
SELECTION = {"selected", "over_cap", "unresolved", "initial_failure"}


def selection(task, cap):
    """Do not assume an earlier missing answer would fail or duplicate another.

    A later parent is definitely selected only when every possible outcome of
    the earlier unresolved slots leaves room for it. Complete collections use
    exactly the collector's first-distinct-passing selection rule.
    """
    known = unknown = 0
    seen, result = set(), {}
    parents = {p["candidate_id"]: p for p in task["programs"]}
    for sample in task["samples"]:
        cid = sample["candidate_id"]
        if cid is None:
            unknown += sample["initial_status"] == "unresolved"
            continue
        if cid in seen:
            continue
        seen.add(cid)
        status = parents[cid]["initial_status"]
        if status == "pass":
            if cap is None or known + unknown < cap:
                result[cid] = "selected"
            elif known >= cap:
                result[cid] = "over_cap"
            else:
                result[cid] = "unresolved"
            known += 1
        elif status in ("unresolved", "infra_error"):
            result[cid] = "unresolved"
            unknown += 1
        else:
            result[cid] = "initial_failure"
    return result


def validate_collection(data):
    """Reject corrupt evidence instead of rewriting it to fit the comparison."""
    try:
        return _validate(data)
    except (KeyError, TypeError, AttributeError) as exc:
        raise EvaluationError(f"Malformed collection export: {exc}") from exc


def _validate(data):
    if data["schema_version"] != VERSION or type(data["schema_version"]) is not int:
        raise EvaluationError("Unsupported collection schema")
    if data["kind"] != KIND or data["purpose"] not in PURPOSES:
        raise EvaluationError("Expected a saved-collection export with a known purpose")
    identifier(data["method"], "method")
    identifier(data["method_group"], "method group")
    integer(data["generation_seed"], "generation seed")
    if data["training_seed"] is not None:
        integer(data["training_seed"], "training seed")
    for field in ("writer_identity", "editor_identity"):
        if not isinstance(data[field], str) or not HASH.fullmatch(data[field]):
            raise EvaluationError(f"Invalid {field}")
    provenance = data.get("provenance", {})
    if not isinstance(provenance, dict) or not isinstance(provenance.get("warnings", []), list):
        raise EvaluationError("Malformed source provenance")
    for warning in provenance.get("warnings", []):
        identifier(warning, "source lookup warning")
    contract = data["contract"]
    for field in ("samples_per_task", "editor_reps"):
        integer(contract[field], field, 1)
    if contract["max_programs"] is not None:
        integer(contract["max_programs"], "max_programs", 1)
    for field in ("editor_hash", "sandbox_hash"):
        if not isinstance(contract[field], str) or not HASH.fullmatch(contract[field]):
            raise EvaluationError(f"Invalid contract {field}")
    if not isinstance(contract["image_id"], str) or not contract["image_id"]:
        raise EvaluationError("Missing sandbox image identity")
    if not isinstance(data["tasks"], list) or not data["tasks"]:
        raise EvaluationError("No task roster")
    ids = set()
    for task in data["tasks"]:
        meta = task["definition"]
        task_id = identifier(meta["id"], "task")
        if task_id in ids:
            raise EvaluationError("Duplicate task")
        ids.add(task_id)
        expected_split = PURPOSES[data["purpose"]]
        if expected_split is not None and meta["split"] != expected_split:
            raise EvaluationError("Task split disagrees with collection purpose")
        if not isinstance(task["samples"], list) or not isinstance(task["programs"], list):
            raise EvaluationError("Expected sample and program arrays")
        if [s["sample_idx"] for s in task["samples"]] != list(range(contract["samples_per_task"])):
            raise EvaluationError("Every planned sample must occur exactly once, in order")
        parents = {}
        for parent in task["programs"]:
            cid = parent["candidate_id"]
            if not isinstance(cid, str) or not HASH.fullmatch(cid) or cid in parents:
                raise EvaluationError("Duplicate or invalid parent hash")
            parents[cid] = parent
        occurrences = Counter()
        for sample in task["samples"]:
            integer(sample["sample_idx"], "sample index")
            status, cid = sample["initial_status"], sample["candidate_id"]
            if status not in INITIAL:
                raise EvaluationError("Unknown initial status")
            if cid is None:
                if status not in ("unresolved", "parse_failure"):
                    raise EvaluationError("Evaluated sample has no source")
            elif cid not in parents or status != parents[cid]["initial_status"]:
                raise EvaluationError("Sample and parent identity/status disagree")
            else:
                occurrences[cid] += 1
            for field in ("tokens_in", "tokens_out", "wall_s"):
                cost(sample["writer_cost"][field], field, integral=field != "wall_s")
            cost(sample["writer_cost"].get("n_calls"), "writer n_calls", integral=True)
        if set(occurrences) != set(parents):
            raise EvaluationError("Unreferenced parent or missing sample")
        expected = selection(task, contract["max_programs"])
        for cid, parent in parents.items():
            indices = [s["sample_idx"] for s in task["samples"] if s["candidate_id"] == cid]
            if parent["sample_indices"] != indices:
                raise EvaluationError("Parent sample membership disagrees")
            if parent["selection"] not in SELECTION or parent["selection"] != expected[cid]:
                raise EvaluationError("Selection disagrees with first-passing order")
            # Reuse the established stop-order and private-count validation.
            # Infra at the initial stage is unresolved eligibility, not a code failure.
            legacy_status = (
                "unresolved"
                if parent["initial_status"] == "infra_error"
                else parent["initial_status"]
            )
            sample = {
                "task": task_id,
                "candidate_id": cid,
                "initial_status": legacy_status,
                "writer_cost": {"tokens_in": None, "tokens_out": None, "wall_s": None},
                "trials": parent["trials"],
                "source_metrics": parent.get("source_metrics"),
            }
            validate_dataset(
                {
                    "schema_version": 1,
                    "method": data["method"],
                    "generation_seed": data["generation_seed"],
                    "purpose": "fixture" if data["purpose"] == "training" else data["purpose"],
                    "contract": contract,
                    "editor_reps": contract["editor_reps"],
                    "tasks": [meta],
                    "samples": [sample],
                }
            )
        # Empty/missing collections must still validate their task definitions.
        if not parents:
            validate_dataset(
                {
                    "schema_version": 1,
                    "method": data["method"],
                    "generation_seed": data["generation_seed"],
                    "purpose": "fixture",
                    "contract": contract,
                    "editor_reps": contract["editor_reps"],
                    "tasks": [meta],
                    "samples": [
                        {
                            "task": task_id,
                            "candidate_id": None,
                            "initial_status": "unresolved",
                            "writer_cost": {"tokens_in": None, "tokens_out": None, "wall_s": None},
                            "trials": [
                                {"sequence": seq["id"], "rep": rep, "steps": []}
                                for seq in meta["sequences"]
                                for rep in range(contract["editor_reps"])
                            ],
                        }
                    ],
                }
            )
    return data
