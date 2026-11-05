"""Publish derived evaluation artifacts without replacing original evidence.

Usage:
    publish_bundle("review_summary", files, output_directory)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

from .records import EvaluationError, read_json
from .storage import check_existing, publish_new

WORKFLOW_FILES = {
    "joint_pass": {"analysis.json", "parent_pairs.csv", "metrics.csv", "report.md"},
    "seed_summary": {"analysis.json", "seeds.csv", "groups.csv", "comparisons.csv", "report.md"},
    "size_match_empty": {"analysis.json", "matching.csv", "report.md"},
    "review_pack": {
        "cases.json",
        "cases.csv",
        "annotations.template.csv",
        "review.html",
        "report.md",
    },
    "review_summary": {"analysis.json", "annotations.csv", "report.md"},
    "figures": {
        "figure_data.json",
        "outcomes.png",
        "outcomes.svg",
        "differences.png",
        "differences.svg",
        "resources.png",
        "resources.svg",
        "report.md",
    },
}


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf8")


def csv_bytes(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    # Text written by a reviewer must not become an executable spreadsheet formula.
    # Numeric measurements stay numeric; JSON always retains the exact original text.
    for row in rows:
        writer.writerow(
            {
                k: "'" + v
                if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@"))
                else v
                for k, v in row.items()
            }
        )
    return stream.getvalue().encode("utf8")


def publish_bundle(kind, files, directory, *, source_hash=None):
    if kind not in WORKFLOW_FILES or set(files) != WORKFLOW_FILES[kind]:
        raise EvaluationError("Unknown derived bundle or unsupported artifact names")
    directory = Path(directory)
    outputs = dict(files)
    outputs["manifest.json"] = encoded(
        dict(
            schema_version=1,
            complete=True,
            kind=kind,
            source_report_sha256=source_hash,
            files={name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
        )
    )
    # Precheck the entire bundle before publishing its first file. The manifest is last.
    for name, data in outputs.items():
        check_existing(directory / name, data)
    for name, data in outputs.items():
        publish_new(directory / name, data)
    return {name: str(directory / name) for name in outputs}


def read_comparison(directory):
    # Import here so checksum verification can also recognize derived bundles.
    from .integrity import verify_report

    directory = Path(directory)
    receipt = verify_report(directory)
    if not receipt["analysis_recomputed"]:
        raise EvaluationError("This command requires an original comparison report")
    raw = (directory / "comparison.json").read_bytes()
    return read_json(raw), hashlib.sha256(raw).hexdigest()


def purpose_label(result):
    return {
        "fixture": "SYNTHETIC FIXTURE — not experimental evidence",
        "development": "Development data — not held-out evidence",
        "heldout": "Held-out saved outcomes",
    }[result["purpose"]]
