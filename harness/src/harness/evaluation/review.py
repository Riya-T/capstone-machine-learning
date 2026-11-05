"""Prepare immutable failure cases and compile separate human review annotations.

Usage:
    make_review_pack(report_directory, output_directory, stores={})
    compile_reviews(pack_directory, annotation_paths, output_directory)
"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from html import escape
from pathlib import Path

from .artifacts import csv_bytes, encoded, publish_bundle, purpose_label, read_comparison
from .diagnostics import diagnostic_rows
from .export import _blob
from .integrity import verify_report
from .records import HASH, EvaluationError, read_json

CATEGORIES = (
    "unreviewed",
    "initial_bug",
    "edit_bug",
    "structure_interaction",
    "task_ambiguity",
    "test_defect",
    "task_difficulty",
    "infrastructure",
    "submission_problem",
    "uncertain",
)
ANNOTATION_FIELDS = ("case_id", "reviewer", "category", "confidence", "evidence", "notes")
CASE_FIELDS = (
    "case_id",
    "method",
    "generation_seed",
    "task",
    "family",
    "stage",
    "sequence",
    "rep",
    "step",
    "change_id",
    "status",
    "input_source_hash",
    "output_source_hash",
)


def _preview(root, digest):
    if digest is None:
        return dict(state="no_saved_source_hash", files=[])
    if root is None:
        return dict(state="store_not_provided", files=[])
    path = Path(root) / "blobs" / (digest + ".json")
    if not path.is_file():
        return dict(state="blob_missing", files=[])
    if path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
        raise EvaluationError("Linked source previews are not allowed")
    if path.stat().st_size > 2 * 1024 * 1024:
        return dict(state="preview_size_limit", files=[])
    files = _blob(Path(root), digest)
    remaining, previews = 128 * 1024, []
    for name, raw in sorted(files.items()):
        part = raw[:remaining]
        previews.append(
            dict(
                path=name,
                text=part.decode("utf8", errors="replace"),
                truncated=len(part) < len(raw),
            )
        )
        remaining -= len(part)
    return dict(
        state="available",
        files=previews,
        note="UTF-8 replacement decoding is for display only; original blob bytes stay unchanged.",
    )


def make_review_pack(directory, output, *, stores=None):
    result, source_hash = read_comparison(directory)
    stores = stores or {}
    if not set(stores) <= result["methods"].keys():
        raise EvaluationError("Store mappings must name methods in this report")
    samples = {
        (d["method"], d["generation_seed"], s["task"]): s
        for d in result["source_datasets"]
        for s in d["samples"]
    }
    _, failures = diagnostic_rows(result)
    cases, cache = [], {}
    for failure in failures:
        sample = samples[failure["method"], failure["generation_seed"], failure["task"]]
        before, after = None, sample["candidate_id"]
        if failure["stage"] == "edit":
            before, after = sample["candidate_id"], None
            trial = next(
                t
                for t in sample["trials"]
                if t["sequence"] == failure["sequence"] and t["rep"] == failure["rep"]
            )
            for step in trial["steps"]:
                if step["step"] < failure["step"]:
                    before = step.get("output_blob")
                elif step["step"] == failure["step"]:
                    after = step.get("output_blob")
        case = dict(**failure, input_source_hash=before, output_source_hash=after)
        # A case belongs to this exact saved report, not merely to a task name.
        case["case_id"] = hashlib.sha256(
            encoded(dict(source=source_hash, failure=failure))
        ).hexdigest()
        for label, digest in (("before", before), ("after", after)):
            key = failure["method"], digest
            if key not in cache:
                # Never trust a machine-local path embedded in somebody else's report.
                # Only a store root supplied explicitly on this command is opened.
                cache[key] = _preview(stores.get(failure["method"]), digest)
            case[label + "_preview"] = cache[key]
        cases.append(case)
    payload = dict(
        schema_version=1,
        purpose=result["purpose"],
        source_report_sha256=source_hash,
        categories=CATEGORIES,
        cases=cases,
        training_labels=None,
    )
    template = [
        dict(
            case_id=c["case_id"],
            reviewer="",
            category="unreviewed",
            confidence="unreviewed",
            evidence="",
            notes="",
        )
        for c in cases
    ]
    html = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Failure review</title>',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        "style-src 'unsafe-inline'; base-uri 'none'\">",
        "<style>body{font:16px/1.5 system-ui;max-width:1100px;margin:32px auto;padding:20px}"
        "pre{white-space:pre-wrap;background:#f1f4f8;padding:16px;overflow-wrap:anywhere}"
        "summary{font-weight:600;cursor:pointer}details{border-top:1px solid #bbb;padding:16px 0}"
        "code{overflow-wrap:anywhere}.notice{background:#fff0c2;padding:15px}</style>",
        f"<h1>{escape(purpose_label(result))}</h1><h2>Human failure review</h2>",
        '<p class="notice">Recorded outcomes are unchanged. Read the source previews, copy '
        "annotations.template.csv to your own CSV, and record your review there. "
        "The tool does not infer causes or assign training labels.</p>",
    ]
    for case in cases:
        title = (
            f"{case['method']} / {case['task']} / {case['sequence']} / "
            f"rep {case['rep']}: {case['status']}"
        )
        html += [
            f'<details id="case-{case["case_id"]}"><summary>{escape(title)}</summary>',
            f"<p>Case ID: <code>{case['case_id']}</code></p>",
        ]
        for label in ("before", "after"):
            preview = case[label + "_preview"]
            html.append(f"<h3>{label.title()} source: {escape(preview['state'])}</h3>")
            for file in preview["files"]:
                suffix = " (truncated preview)" if file["truncated"] else ""
                html.append(
                    f"<h4>{escape(file['path'])}{suffix}</h4><pre>{escape(file['text'])}</pre>"
                )
        html.append("</details>")
    html.append("</html>\n")
    instructions = (
        f"# {purpose_label(result)}\n\nReview {len(cases)} immutable cases in review.html.\n\n"
        "Copy annotations.template.csv to annotations.csv before editing; never edit pack files. "
        "Use one unique reviewer ID, a listed category, and confidence hypothesis or verified. "
        "A verified claim requires an evidence reference. Evidence paths are never executed/read. "
        "Verified means reviewer-asserted, not independently established by this tool. "
        "Multiple reviewers may disagree; compilation preserves those disagreements.\n"
    )
    files = {
        "cases.json": encoded(payload),
        "cases.csv": csv_bytes([{k: c[k] for k in CASE_FIELDS} for c in cases], CASE_FIELDS),
        "annotations.template.csv": csv_bytes(template, ANNOTATION_FIELDS),
        "review.html": "\n".join(html).encode("utf8"),
        "report.md": instructions.encode("utf8"),
    }
    return publish_bundle("review_pack", files, output, source_hash=source_hash)


def compile_reviews(directory, annotation_paths, output):
    receipt = verify_report(directory)
    if receipt["kind"] != "review_pack":
        raise EvaluationError("Annotations require an immutable review pack")
    payload = read_json((Path(directory) / "cases.json").read_bytes())
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("cases"), list)
        or not isinstance(payload.get("source_report_sha256"), str)
        or not HASH.fullmatch(payload["source_report_sha256"])
    ):
        raise EvaluationError("Malformed immutable review pack")
    for case in payload["cases"]:
        if (
            not isinstance(case, dict)
            or not isinstance(case.get("case_id"), str)
            or not HASH.fullmatch(case["case_id"])
            or case.get("stage") not in ("initial", "edit")
        ):
            raise EvaluationError("Malformed review case")
    known = {c["case_id"] for c in payload["cases"]}
    stages = {c["case_id"]: c["stage"] for c in payload["cases"]}
    if len(known) != len(payload["cases"]):
        raise EvaluationError("Duplicate review cases")
    reviews, seen, inputs = [], set(), []
    for path in annotation_paths:
        path = Path(path)
        inputs.append(hashlib.sha256(path.read_bytes()).hexdigest())
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if (
                reader.fieldnames is None
                or len(reader.fieldnames) != len(set(reader.fieldnames))
                or (set(reader.fieldnames) != set(ANNOTATION_FIELDS))
            ):
                raise EvaluationError("Annotation CSV has missing, duplicate or unknown columns")
            for row in reader:
                if None in row or None in row.values():
                    raise EvaluationError("Malformed annotation CSV row")
                case_id = row["case_id"]
                if case_id not in known or row["category"] not in CATEGORIES:
                    raise EvaluationError("Unknown case ID or review category")
                category, confidence = row["category"], row["confidence"]
                if stages[case_id] == "initial" and category in (
                    "edit_bug",
                    "structure_interaction",
                ):
                    raise EvaluationError("An initial-only case cannot assert a later edit defect")
                if category == "unreviewed":
                    if confidence != "unreviewed" or any(
                        row[k].strip() for k in ("reviewer", "evidence", "notes")
                    ):
                        raise EvaluationError(
                            "Unreviewed template rows must not contain review claims"
                        )
                    continue
                if confidence not in ("hypothesis", "verified") or not row["reviewer"].strip():
                    raise EvaluationError(
                        "Reviewed rows need reviewer and hypothesis/verified confidence"
                    )
                if not (row["notes"].strip() or row["evidence"].strip()):
                    raise EvaluationError("Explain a review with notes or evidence")
                if confidence == "verified" and not row["evidence"].strip():
                    raise EvaluationError(
                        "Reviewer-asserted verified causes need evidence references"
                    )
                key = case_id, row["reviewer"].strip().casefold()
                if key in seen:
                    raise EvaluationError("Duplicate reviewer/case annotation")
                seen.add(key)
                reviews.append(row)
    by_case = defaultdict(list)
    for row in reviews:
        by_case[row["case_id"]].append(row)
    counts = Counter()
    cases = []
    for case in payload["cases"]:
        annotations = by_case[case["case_id"]]
        categories = {a["category"] for a in annotations}
        status = (
            "unreviewed"
            if not annotations
            else "disagreement"
            if len(categories) > 1
            else "reviewed"
        )
        counts[status] += 1
        cases.append(dict(case_id=case["case_id"], status=status, annotations=annotations))
    result = dict(
        schema_version=1,
        purpose=payload["purpose"],
        source_report_sha256=payload["source_report_sha256"],
        annotation_input_hashes=inputs,
        cases=cases,
        case_counts=dict(counts),
        annotation_category_counts=dict(Counter(a["category"] for a in reviews)),
        training_labels=None,
        note="Human assertions only. Evidence references were not opened or executed. "
        "Disagreements remain unresolved; no majority label or causal proof is inferred.",
    )
    files = {
        "analysis.json": encoded(result),
        "annotations.csv": csv_bytes(reviews, ANNOTATION_FIELDS),
        "report.md": (
            f"# {payload['purpose']}: human review summary\n\n"
            f"{len(known)} cases; counts {dict(counts)}.\n\n{result['note']}\n"
        ).encode(),
    }
    return publish_bundle(
        "review_summary", files, output, source_hash=payload["source_report_sha256"]
    )
