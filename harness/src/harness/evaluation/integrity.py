"""Verify saved report checksums and recompute analysis without inference or writes.

Usage:
    receipt = verify_report(Path("runs/comparison"))
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .analysis import compare
from .artifacts import WORKFLOW_FILES
from .records import HASH, EvaluationError, read_json
from .report import OPTIONAL_OUTPUT_NAMES, OUTPUT_NAMES

REQUIRED = {"comparison.json", "summary.csv", "trajectories.csv", "report.md"}


def _regular(path):
    if path.is_symlink() or not path.is_file():
        raise EvaluationError(f"Missing, non-file or linked report artifact: {path.name}")
    # Includes Windows reparse points that are not exposed as ordinary symlinks.
    if getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
        raise EvaluationError(f"Reparse point in report artifacts: {path.name}")
    return path.read_bytes()


def verify_report(directory: Path, *, recompute: bool = True) -> dict:
    """Check the declared bundle; checksums establish integrity, not authenticity.

    Legacy manifest-bearing bundles can omit newly added outputs. Analysis checks
    recompute scores from the embedded outcome records, never rerunning private
    tests or establishing that recorded model outcomes are true.
    """
    directory = Path(directory)
    manifest = read_json(_regular(directory / "manifest.json"))
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
        or manifest.get("complete") is not True
    ):
        raise EvaluationError("Invalid or incomplete report manifest")
    files = manifest.get("files")
    kind = manifest.get("kind")
    if kind is not None and (not isinstance(kind, str) or kind not in WORKFLOW_FILES):
        raise EvaluationError("Unknown derived report kind")
    required = WORKFLOW_FILES[kind] if kind else REQUIRED
    if not isinstance(files, dict) or not files.keys() >= required:
        raise EvaluationError("Manifest omits required report files")
    allowed = (
        WORKFLOW_FILES[kind]
        if kind
        else (set(OUTPUT_NAMES) | OPTIONAL_OUTPUT_NAMES) - {"manifest.json"}
    )
    blobs = {}
    for name, digest in files.items():
        if name not in allowed:
            raise EvaluationError(f"Unsafe or unsupported report filename: {name}")
        if not isinstance(digest, str) or not HASH.fullmatch(digest):
            raise EvaluationError(f"Invalid checksum for {name}")
        blobs[name] = _regular(directory / name)
        if hashlib.sha256(blobs[name]).hexdigest() != digest:
            raise EvaluationError(f"Checksum mismatch: {name}")
    if recompute and not kind:
        _analysis_matches(read_json(blobs["comparison.json"]))
    return dict(
        complete=True,
        checksums_valid=True,
        files_verified=sorted(files),
        analysis_recomputed=recompute and not kind,
        kind=kind or "comparison",
        note=(
            "Derived artifacts: checksums only; reproduce the analysis with its saved rule."
            if kind
            else "Local consistency only; does not authenticate results or rerun behavioral tests."
        ),
    )


def _analysis_matches(saved):
    try:
        options = saved["bootstrap"]
        expected = compare(
            saved["source_datasets"],
            reference=saved["reference"],
            bootstrap_samples=options["samples"],
            bootstrap_seed=options["seed"],
            confidence=options["confidence"],
        )
        for key in (
            "schema_version",
            "purpose",
            "reference",
            "bootstrap",
            "comparisons",
            "trajectories",
        ):
            if saved[key] != expected[key]:
                raise EvaluationError(f"Recomputed analysis differs: {key}")
        if set(saved["methods"]) != set(expected["methods"]):
            raise EvaluationError("Recomputed analysis differs: methods")
        for method, values in expected["methods"].items():
            for key in ("metrics", "families", "counts", "costs", "initial_source_descriptives"):
                if key == "initial_source_descriptives" and key not in saved["methods"][method]:
                    continue  # Added after the first report version.
                if saved["methods"][method][key] != values[key]:
                    raise EvaluationError(f"Recomputed analysis differs: {method}/{key}")
            for key in (
                "all_generated_source_descriptives",
                "resource_breakdown",
                "method_group",
                "training_seed",
                "writer_model",
                "writer_identity",
            ):
                if key in saved["methods"][method] and saved["methods"][method][key] != values[key]:
                    raise EvaluationError(f"Recomputed analysis differs: {method}/{key}")
    except (KeyError, TypeError, AttributeError) as exc:
        raise EvaluationError(f"Malformed saved analysis: {exc}") from exc
