"""Publish and recompute separate investigation bundles from saved comparisons.

Usage: source, raw = read_primary(Path("runs/comparison"))
Snapshots make derived artifacts independently verifiable without the source store.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..evaluation.records import HASH, EvaluationError, read_json
from ..evaluation.storage import check_existing
from .analysis import compare_collections
from .report import encoded, safe_destination
from .storage import publish_new

KINDS = {
    "collection_review_pack": {
        "source.comparison.json",
        "cases.json",
        "cases.csv",
        "missing.csv",
        "annotations.template.csv",
        "review.html",
        "report.md",
    },
    "collection_review_summary": {
        "source.comparison.json",
        "source.cases.json",
        "annotation_inputs.json",
        "analysis.json",
        "annotations.csv",
        "report.md",
        "report.html",
    },
    "collection_checkpoint_summary": {
        "source.comparison.json",
        "options.json",
        "analysis.json",
        "checkpoints.csv",
        "groups.csv",
        "comparisons.csv",
        "report.md",
        "report.html",
    },
}


def snapshot(raw):
    """Recompute the original comparison, not just a hash of claimed scores."""
    source = read_json(raw)
    result = compare_collections(
        source["source_datasets"],
        reference=source["reference"],
        **{
            key: source["analysis"][key]
            for key in ("bootstrap_samples", "bootstrap_seed", "confidence")
        },
    )
    if encoded(result) != raw:
        raise EvaluationError("Source comparison snapshot does not recompute")
    return source


def read_primary(directory):
    from .report import verify_report

    directory = Path(directory)
    safe_destination(directory)
    safe_destination(directory / "manifest.json")
    manifest = read_json((directory / "manifest.json").read_bytes())
    if not isinstance(manifest, dict) or manifest.get("kind") != "collection_report_manifest":
        raise EvaluationError("This operation needs an original collection comparison")
    verify_report(directory)
    if not (directory / "comparison.json").is_file():
        raise EvaluationError("This operation needs an original collection comparison")
    raw = (directory / "comparison.json").read_bytes()
    return read_json(raw), raw


def publish(kind, files, output):
    if kind not in KINDS or set(files) != KINDS[kind]:
        raise EvaluationError("Unsupported collection investigation artifact set")
    output = Path(output)
    safe_destination(output)
    payload = dict(files)
    payload["manifest.json"] = encoded(
        {
            "schema_version": 1,
            "kind": kind,
            "source_report_sha256": hashlib.sha256(files["source.comparison.json"]).hexdigest(),
            "files": {name: hashlib.sha256(body).hexdigest() for name, body in files.items()},
        }
    )
    for name, body in payload.items():
        safe_destination(output / name)
        check_existing(output / name, body)
    for name, body in payload.items():
        publish_new(output / name, body)
    return {
        "kind": kind,
        "output_files": sorted(payload),
        "model_calls": 0,
        "training_labels_created": 0,
    }


def checked_files(directory):
    directory = Path(directory)
    safe_destination(directory)
    safe_destination(directory / "manifest.json")
    manifest = read_json((directory / "manifest.json").read_bytes())
    if not isinstance(manifest, dict):
        raise EvaluationError("Expected an investigation manifest object")
    kind = manifest.get("kind")
    if (
        type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
        or not isinstance(kind, str)
        or kind not in KINDS
        or not isinstance(manifest.get("files"), dict)
        or set(manifest["files"]) != KINDS[kind]
    ):
        raise EvaluationError("Invalid collection investigation manifest")
    files = {}
    for name, digest in manifest["files"].items():
        if not isinstance(digest, str) or not HASH.fullmatch(digest):
            raise EvaluationError("Invalid artifact digest")
        safe_destination(directory / name)
        raw = (directory / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise EvaluationError(f"Investigation checksum mismatch: {name}")
        files[name] = raw
    if hashlib.sha256(files["source.comparison.json"]).hexdigest() != manifest.get(
        "source_report_sha256"
    ):
        raise EvaluationError("Investigation source identity disagrees")
    return kind, files


def verify(directory):
    kind, files = checked_files(directory)
    source = snapshot(files["source.comparison.json"])
    if kind == "collection_checkpoint_summary":
        from .checkpoints import summary_files

        rebuilt = summary_files(
            source, files["source.comparison.json"], read_json(files["options.json"])
        )
    else:
        from .review import replay_files

        rebuilt = replay_files(kind, source, files)
    if set(rebuilt) != set(files) or any(files[name] != raw for name, raw in rebuilt.items()):
        raise EvaluationError("Investigation artifacts do not recompute")
    return {
        "verified": True,
        "kind": kind,
        "analysis_recomputed": True,
        "files": len(files),
        "model_calls": 0,
    }
