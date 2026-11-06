"""Freeze the expected evaluation roster before outcomes exist.

Usage:
    contract = freeze_contract(prepared)
    receipt = check_contract(contract, exported_datasets)
"""

from __future__ import annotations

import hashlib

from ..store import editor_cfg_hash
from .artifacts import encoded
from .records import HASH, PURPOSES, EvaluationError, identifier, integer, validate_dataset

UNRESOLVED_IMAGE = "image-resolved-at-execution"


def _digest(body):
    return hashlib.sha256(encoded(body)).hexdigest()


def freeze_contract(prepared):
    # Read the planned roster, never infer an expected population from observed results.
    signature = prepared.signature
    body = dict(
        schema_version=1,
        kind="evaluation_analysis_contract",
        plan_fingerprint=prepared.digest,
        purpose=prepared.plan.purpose,
        reference=prepared.plan.reference,
        bootstrap={**signature["bootstrap"], "unit": "task_family", "paired": True},
        generation_seeds=list(prepared.plan.generation_seeds),
        methods=[
            dict(
                method=row["method"],
                method_group=row["method_group"],
                training_seed=row["training_seed"],
                writer_model=cfg.writer.backend.model,
                writer_identity=row["writer_identity"],
                editor_identity=editor_cfg_hash(cfg, UNRESOLVED_IMAGE),
            )
            for row, cfg in zip(signature["methods"], prepared.configs, strict=True)
        ],
        tasks=signature["tasks"],
        comparison_contract=signature["comparison_contract"],
        note="Configured identities and planned coverage, not model-weight attestation. "
        "The actual sandbox image is locked separately at execution. Freeze before inference; "
        "this file alone cannot prove when it was created.",
    )
    return {**body, "contract_id": _digest(body)}


def validate_contract(contract):
    if not isinstance(contract, dict):
        raise EvaluationError("Analysis contract must be an object")
    body = {k: v for k, v in contract.items() if k != "contract_id"}
    required = {
        "schema_version",
        "kind",
        "plan_fingerprint",
        "purpose",
        "reference",
        "bootstrap",
        "generation_seeds",
        "methods",
        "tasks",
        "comparison_contract",
        "note",
    }
    if (
        set(body) != required
        or type(body["schema_version"]) is not int
        or body["schema_version"] != 1
        or body["kind"] != "evaluation_analysis_contract"
        or contract.get("contract_id") != _digest(body)
    ):
        raise EvaluationError("Malformed or changed analysis contract")
    # Explicit shape checks keep damaged JSON out of the CLI's indexing paths.
    if (
        not isinstance(body["methods"], list)
        or not body["methods"]
        or not isinstance(body["generation_seeds"], list)
        or not body["generation_seeds"]
        or not isinstance(body["tasks"], dict)
        or not body["tasks"]
        or not isinstance(body["comparison_contract"], dict)
        or not isinstance(body["bootstrap"], dict)
    ):
        raise EvaluationError("Malformed analysis contract roster")
    try:
        if body["purpose"] not in PURPOSES or not isinstance(body["note"], str):
            raise EvaluationError("Malformed contract purpose or note")
        if not HASH.fullmatch(body["plan_fingerprint"]):
            raise EvaluationError("Malformed plan fingerprint")
        options = body["bootstrap"]
        integer(options["samples"], "bootstrap samples", 1)
        integer(options["seed"], "bootstrap seed")
        if (
            set(options) != {"samples", "seed", "confidence", "unit", "paired"}
            or options["samples"] > 20000
            or not 0 < options["confidence"] < 1
            or options["unit"] != "task_family"
            or options["paired"] is not True
        ):
            raise EvaluationError("Invalid contract analysis settings")
        integer(body["comparison_contract"]["editor_reps"], "editor reps", 1)
        names = [row["method"] for row in body["methods"]]
        if len(set(names)) != len(names) or body["reference"] not in names:
            raise EvaluationError("Duplicate contract methods or absent reference")
        seeds = body["generation_seeds"]
        if any(type(s) is not int or s < 0 for s in seeds) or len(set(seeds)) != len(seeds):
            raise EvaluationError("Invalid contract generation seeds")
        for row in body["methods"]:
            if set(row) != {
                "method",
                "method_group",
                "training_seed",
                "writer_model",
                "writer_identity",
                "editor_identity",
            } or any(not isinstance(row[k], str) for k in row if k != "training_seed"):
                raise EvaluationError("Malformed contract method metadata")
            identifier(row["method"], "contract method")
            identifier(row["method_group"], "contract group")
            if row["training_seed"] is not None:
                integer(row["training_seed"], "training seed")
            for key in ("writer_identity", "editor_identity"):
                if not HASH.fullmatch(row[key]):
                    raise EvaluationError("Invalid contract identity")
        for name, row in body["tasks"].items():
            identifier(name, "contract task")
            if set(row) != {"version", "family", "split", "sequences"}:
                raise EvaluationError("Malformed contract task metadata")
            if not HASH.fullmatch(row["version"]):
                raise EvaluationError("Invalid contract task version")
            identifier(row["family"], "contract family")
            if row["split"] not in {"train", "dev", "eval"}:
                raise EvaluationError("Invalid contract task split")
            if not isinstance(row["sequences"], dict) or not row["sequences"]:
                raise EvaluationError("Invalid contract sequences")
            for sequence, changes in row["sequences"].items():
                identifier(sequence, "contract sequence")
                if not isinstance(changes, list) or not changes:
                    raise EvaluationError("Invalid contract changes")
                for change in changes:
                    identifier(change, "contract change")
                if len(set(changes)) != len(changes):
                    raise EvaluationError("Duplicate contract change")
    except (TypeError, KeyError, AttributeError) as exc:
        raise EvaluationError("Malformed analysis contract metadata") from exc
    return contract


def check_contract(contract, datasets):
    validate_contract(contract)
    methods = {row["method"]: row for row in contract["methods"]}
    expected = {(name, seed) for name in methods for seed in contract["generation_seeds"]}
    seen, issues = set(), []
    # These hashes include a runtime image. Their image-independent equivalent is
    # checked separately; actual image equality remains mandatory in compare().
    runtime_fields = {"image_id", "sandbox_hash", "editor_hash"}
    for data in datasets:
        validate_dataset(data)
        key = data["method"], data["generation_seed"]
        if key in seen:
            issues.append(f"Duplicate dataset: {key}")
        seen.add(key)
        if key not in expected:
            issues.append(f"Unexpected dataset: {key}")
            continue
        label = f"{key[0]}/{key[1]}"
        row = methods[key[0]]
        for field in ("writer_model", "writer_identity", "editor_identity", "training_seed"):
            if field not in data:
                issues.append(f"{label}: {field} unavailable; cannot verify")
            elif data[field] != row[field]:
                issues.append(f"{label}: {field} differs from frozen plan")
        if data.get("method_group", data["method"]) != row["method_group"]:
            issues.append(f"{label}: method_group differs from frozen plan")
        if data["purpose"] != contract["purpose"]:
            issues.append(f"{label}: purpose differs from frozen plan")
        planned = contract["comparison_contract"]
        if data["editor_reps"] != planned["editor_reps"] or {
            k: v for k, v in data["contract"].items() if k not in runtime_fields
        } != {k: v for k, v in planned.items() if k not in runtime_fields}:
            issues.append(f"{label}: inference budgets differ from frozen plan")
        tasks = {
            t["id"]: dict(
                version=t["version"],
                family=t["family"],
                split=t["split"],
                sequences={s["id"]: s["changes"] for s in t["sequences"]},
            )
            for t in data["tasks"]
        }
        if tasks != contract["tasks"]:
            issues.append(f"{label}: task versions or sequence roster differ from frozen plan")
    issues += [f"Missing dataset: {key}" for key in sorted(expected - seen)]
    return dict(
        contract_id=contract["contract_id"],
        matches=not issues,
        expected_datasets=len(expected),
        supplied_datasets=len(datasets),
        issues=issues,
        note="Coverage of planned records; unresolved outcomes remain unresolved. "
        "This does not authenticate recorded outcomes or checkpoint weights.",
    )


def attach_contract(result, contract):
    receipt = check_contract(contract, result["source_datasets"])
    if not receipt["matches"]:
        raise EvaluationError("Frozen coverage check failed: " + "; ".join(receipt["issues"]))
    if result["reference"] != contract["reference"] or result["bootstrap"] != contract["bootstrap"]:
        raise EvaluationError("Analysis settings differ from the frozen contract")
    result["analysis_contract"] = contract
    result["coverage_receipt"] = receipt
    result["notes"].append(
        "All planned datasets match the frozen analysis contract. This verifies the roster, "
        "not completeness of inference outcomes or the authenticity of model weights."
    )
    return receipt
