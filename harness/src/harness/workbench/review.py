"""Prepare human investigation cases for native multi-sample collection failures.

Usage: make_pack(report_directory, output_directory, stores={})
Missing work is listed separately; no cause or preference is inferred.
"""

from __future__ import annotations

import base64
import hashlib
import html
from pathlib import Path

from ..evaluation.artifacts import purpose_label
from ..evaluation.records import EvaluationError, read_json
from ..evaluation.review import (
    CASE_FIELDS,
    CATEGORIES,
    _preview,
    review_pack_files,
    review_summary_files,
    summarize_annotations,
)
from .derived import checked_files, publish, read_primary, verify
from .presentation import document, render_report_text
from .report import encoded, table_csv

EXTRA_FIELDS = ("candidate_id", "sample_indices", "change_kind", "end_reason", "infra_cause")
MISSING_FIELDS = (
    "method",
    "task",
    "candidate_id",
    "sample_idx",
    "stage",
    "sequence",
    "rep",
    "reason",
)


def cases_for(source, source_hash):
    cases, missing = [], []
    for data in source["source_datasets"]:
        for task in data["tasks"]:
            meta = task["definition"]
            base = {
                "method": data["method"],
                "generation_seed": data["generation_seed"],
                "task": meta["id"],
                "family": meta["family"],
            }

            def add(
                parent, *, stage, status, trial=None, step=None, sample=None, base=base, meta=meta
            ):
                row = {
                    **base,
                    "stage": stage,
                    "status": status,
                    "candidate_id": None if parent is None else parent["candidate_id"],
                    "sample_indices": [sample] if parent is None else parent["sample_indices"],
                    "sequence": None if trial is None else trial["sequence"],
                    "rep": None if trial is None else trial["rep"],
                    "step": None if step is None else step["step"],
                    "change_id": None if step is None else step["change_id"],
                    "change_kind": None
                    if step is None
                    else meta.get("change_kinds", {}).get(step["change_id"]),
                    "end_reason": None if step is None else step.get("end_reason"),
                    "infra_cause": None if step is None else step.get("infra_cause"),
                    "input_source_hash": None,
                    "output_source_hash": None,
                    "new_pass": None if step is None else step.get("new_pass"),
                    "new_total": None if step is None else step.get("new_total"),
                    "existing_pass": None if step is None else step.get("existing_pass"),
                    "existing_total": None if step is None else step.get("existing_total"),
                }
                if stage == "initial":
                    row["output_source_hash"] = row["candidate_id"]
                else:
                    before = parent["candidate_id"]
                    for prior in trial["steps"]:
                        if prior["step"] < step["step"]:
                            before = prior.get("output_blob")
                    row.update(input_source_hash=before, output_source_hash=step.get("output_blob"))
                row["case_id"] = hashlib.sha256(
                    encoded({"source": source_hash, "case": row})
                ).hexdigest()
                cases.append(row)

            def absent(reason, *, parent=None, sample=None, trial=None, stage="initial", base=base):
                missing.append(
                    {
                        "method": base["method"],
                        "task": base["task"],
                        "candidate_id": None if parent is None else parent["candidate_id"],
                        "sample_idx": sample,
                        "stage": stage,
                        "sequence": None if trial is None else trial["sequence"],
                        "rep": None if trial is None else trial["rep"],
                        "reason": reason,
                    }
                )

            for sample in task["samples"]:
                if sample["candidate_id"] is not None:
                    continue
                if sample["initial_status"] == "parse_failure":
                    add(
                        None,
                        stage="initial",
                        status="initial_parse_failure",
                        sample=sample["sample_idx"],
                    )
                else:
                    absent("writer_answer_missing", sample=sample["sample_idx"])
            lengths = {s["id"]: len(s["changes"]) for s in meta["sequences"]}
            for parent in task["programs"]:
                status = parent["initial_status"]
                if status in ("fail", "infra_error"):
                    add(parent, stage="initial", status="initial_" + status)
                elif status == "unresolved":
                    absent("initial_check_missing", parent=parent)
                elif parent["selection"] != "selected":
                    absent("not_scheduled_" + parent["selection"], parent=parent, stage="edit")
                else:
                    for trial in parent["trials"]:
                        steps = trial["steps"]
                        if steps and steps[-1]["status"] != "success":
                            add(
                                parent,
                                stage="edit",
                                status=steps[-1]["status"],
                                trial=trial,
                                step=steps[-1],
                            )
                        elif len(steps) < lengths[trial["sequence"]]:
                            absent("editing_not_finished", parent=parent, trial=trial, stage="edit")
    return {
        "schema_version": 1,
        "kind": "collection_review_cases",
        "purpose": source["purpose"],
        "source_report_sha256": source_hash,
        "categories": CATEGORIES,
        "cases": cases,
        "missing_work": missing,
        "training_labels": None,
    }


def validate_cases(source, raw_source, payload):
    expected = cases_for(source, hashlib.sha256(raw_source).hexdigest())
    plain = {
        **payload,
        "cases": [
            {k: v for k, v in c.items() if k not in ("before_preview", "after_preview")}
            for c in payload["cases"]
        ],
    }
    # JSON turns the shared category tuple into a list; normalize through encoding.
    if encoded(plain) != encoded(expected):
        raise EvaluationError(
            "Review case identities or recorded outcomes disagree with the source"
        )
    for case in payload["cases"]:
        for label in ("before_preview", "after_preview"):
            preview = case[label]
            if (
                not isinstance(preview, dict)
                or not isinstance(preview.get("files"), list)
                or preview.get("state")
                not in {
                    "no_saved_source_hash",
                    "store_not_provided",
                    "blob_missing",
                    "preview_size_limit",
                    "available",
                }
            ):
                raise EvaluationError("Malformed review preview")
            total = 0
            seen = set()
            for file in preview["files"]:
                if (
                    not isinstance(file, dict)
                    or not isinstance(file.get("path"), str)
                    or not isinstance(file.get("text"), str)
                    or type(file.get("truncated")) is not bool
                ):
                    raise EvaluationError("Malformed source preview file")
                if file["path"] in seen:
                    raise EvaluationError("Duplicate source preview path")
                seen.add(file["path"])
                total += len(file["text"].encode())
            if total > 512 * 1024:
                raise EvaluationError("Source preview exceeds the display limit")


def pack_files(source, raw_source, payload):
    validate_cases(source, raw_source, payload)
    files = review_pack_files(payload, case_fields=(*CASE_FIELDS, *EXTRA_FIELDS))
    files["source.comparison.json"] = raw_source
    files["missing.csv"] = table_csv(payload["missing_work"], MISSING_FIELDS)
    files["report.md"] += (
        b"\nThis native collection pack groups duplicate writer samples by parent. "
        b"Only actual terminal stops are review cases. Missing/over-cap work is in missing.csv. "
        b"Preview files can contain private source; review this bundle before sharing. "
        b"Preview checksums do not establish a causal failure explanation.\n"
        b"\nCompile a copied annotation CSV into a new directory:\n\n"
        b"`python -m harness collection-workbench review compile --pack PACK_DIRECTORY "
        b"--annotations YOUR_REVIEW.csv --out NEW_DIRECTORY`\n"
    )
    return files


def make_pack(directory, output, *, stores=None):
    source, raw = read_primary(directory)
    stores = stores or {}
    if not set(stores) <= set(source["methods"]):
        raise EvaluationError("Store mappings must name checkpoints in the source report")
    for root in stores.values():
        if Path(output).resolve().is_relative_to(Path(root).resolve()):
            raise EvaluationError("Review output must be outside source stores")
    payload = cases_for(source, hashlib.sha256(raw).hexdigest())
    cache = {}
    for case in payload["cases"]:
        for label, field in (("before", "input_source_hash"), ("after", "output_source_hash")):
            key = case["method"], case[field]
            if key not in cache:
                cache[key] = _preview(stores.get(case["method"]), case[field])
            case[label + "_preview"] = cache[key]
    return publish("collection_review_pack", pack_files(source, raw, payload), output)


def compiled_files(source, raw_source, cases_raw, annotation_raw):
    payload = read_json(cases_raw)
    validate_cases(source, raw_source, payload)
    inputs = read_json(annotation_raw)
    if not isinstance(inputs, list):
        raise EvaluationError("Malformed annotation input archive")
    decoded = []
    for record in inputs:
        if not isinstance(record, dict) or set(record) != {"sha256", "base64"}:
            raise EvaluationError("Malformed annotation input record")
        body = base64.b64decode(record["base64"], validate=True)
        if hashlib.sha256(body).hexdigest() != record["sha256"]:
            raise EvaluationError("Annotation input hash disagrees")
        decoded.append(body)
    result, reviews = summarize_annotations(payload, decoded)
    files = review_summary_files(result, reviews)
    files.update(
        {
            "source.comparison.json": raw_source,
            "source.cases.json": cases_raw,
            "annotation_inputs.json": annotation_raw,
        }
    )
    files["report.md"] = f"# {purpose_label(source)}\n\n".encode() + files["report.md"]
    rows = []
    for case in result["cases"]:
        for annotation in case["annotations"] or [{}]:
            values = [
                case["case_id"],
                case["status"],
                *(
                    annotation.get(field, "")
                    for field in ("reviewer", "category", "confidence", "evidence", "notes")
                ),
            ]
            rows.append(
                '<tr><td class="digest">'
                + html.escape(values[0])
                + "</td>"
                + "".join(f"<td>{html.escape(value)}</td>" for value in values[1:])
                + "</tr>"
            )
    detail = (
        '<p><a href="annotations.csv">All annotations</a> · '
        '<a href="analysis.json">Machine-readable review</a></p>'
        "<h2>Individual reviews and disagreements</h2><p>These are human assertions, "
        'not tool-verified causes. Every reviewer is retained.</p><div class="scroll">'
        "<table><thead><tr><th>Case ID</th><th>Status</th><th>Reviewer</th><th>Category</th>"
        "<th>Confidence</th><th>Evidence reference</th><th>Notes</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )
    files["report.html"] = document(
        "Human review summary", render_report_text(files["report.md"].decode()) + detail
    )
    return files


def compile_pack(directory, annotation_paths, output):
    receipt = verify(directory)
    if receipt["kind"] != "collection_review_pack":
        raise EvaluationError("Annotations require a native collection review pack")
    _, files = checked_files(directory)
    from .derived import snapshot

    source = snapshot(files["source.comparison.json"])
    inputs = []
    for path in annotation_paths:
        raw = Path(path).read_bytes()
        inputs.append(
            {"sha256": hashlib.sha256(raw).hexdigest(), "base64": base64.b64encode(raw).decode()}
        )
    derived = compiled_files(
        source, files["source.comparison.json"], files["cases.json"], encoded(inputs)
    )
    return publish("collection_review_summary", derived, output)


def replay_files(kind, source, files):
    if kind == "collection_review_pack":
        return pack_files(source, files["source.comparison.json"], read_json(files["cases.json"]))
    return compiled_files(
        source,
        files["source.comparison.json"],
        files["source.cases.json"],
        files["annotation_inputs.json"],
    )
