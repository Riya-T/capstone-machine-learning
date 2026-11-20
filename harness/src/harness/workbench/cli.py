"""Offline commands for exporting, comparing and verifying native collections.

Usage: python -m harness collection-workbench --help
No command here invokes inference, Docker, training or generated code.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from ..config import ConfigError, load_config
from ..evaluation.records import EvaluationError, read_json
from .analysis import compare_collections
from .export import export_collection
from .report import encoded, safe_destination, verify_report, write_report
from .storage import publish_new


def build(manifest_path, out):
    """A post-hoc input manifest describes saved evidence, not preregistration."""
    manifest_path = Path(manifest_path)
    manifest = read_json(manifest_path.read_bytes())
    if not isinstance(manifest, dict):
        raise EvaluationError("Expected a collection manifest object")
    if set(manifest) - {
        "schema_version",
        "purpose",
        "image_id",
        "reference",
        "methods",
        "analysis",
    }:
        raise EvaluationError("Unknown collection manifest field")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise EvaluationError("Unsupported collection manifest")
    analysis = manifest.get("analysis", {})
    if not isinstance(analysis, dict) or set(analysis) - {
        "bootstrap_samples",
        "bootstrap_seed",
        "confidence",
    }:
        raise EvaluationError("Expected a supported collection analysis options object")
    methods = manifest["methods"]
    if not isinstance(methods, list) or not 1 <= len(methods) <= 32:
        raise EvaluationError("Manifest requires 1 to 32 checkpoints")
    datasets = []
    for method in methods:
        if not isinstance(method, dict):
            raise EvaluationError("Expected a checkpoint object")
        if set(method) - {"id", "config", "store", "method_group", "training_seed"}:
            raise EvaluationError("Unknown checkpoint field")
        cfg = load_config(manifest_path.parent / method["config"])
        if method.get("store") is not None:
            cfg = replace(cfg, runs_dir=(manifest_path.parent / method["store"]).resolve())
        if Path(out).resolve().is_relative_to(cfg.runs_dir.resolve()):
            raise EvaluationError("Report output must be outside every source store")
        datasets.append(
            export_collection(
                cfg,
                manifest["image_id"],
                method=method["id"],
                purpose=manifest["purpose"],
                method_group=method.get("method_group"),
                training_seed=method.get("training_seed"),
            )
        )
    result = compare_collections(
        datasets, reference=manifest.get("reference"), **analysis
    )
    return write_report(result, out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="Read a native SQLite store into portable JSON")
    export.add_argument("--config", type=Path, required=True)
    export.add_argument(
        "--store", type=Path, help="Override the saved store root, without changing cache keys"
    )
    export.add_argument(
        "--image-id", required=True, help="Recorded content ID; no Docker lookup is performed"
    )
    export.add_argument("--method", required=True)
    export.add_argument("--method-group")
    export.add_argument("--training-seed", type=int)
    export.add_argument(
        "--purpose", choices=("heldout", "development", "training", "fixture"), default="heldout"
    )
    export.add_argument("--out", type=Path, required=True)
    compare = commands.add_parser("compare", help="Build a report from portable collection exports")
    compare.add_argument("--input", type=Path, nargs="+", required=True)
    compare.add_argument("--reference")
    compare.add_argument("--out", type=Path, required=True)
    compare.add_argument("--bootstrap-samples", type=int, default=2000)
    compare.add_argument("--bootstrap-seed", type=int, default=20261119)
    compare.add_argument("--confidence", type=float, default=0.95)
    bundle = commands.add_parser(
        "build", help="Read configured saved runs and publish one comparison"
    )
    bundle.add_argument("--manifest", type=Path, required=True)
    bundle.add_argument("--out", type=Path, required=True)
    verify = commands.add_parser("verify", help="Check hashes and recompute a published report")
    verify.add_argument("--report", type=Path, required=True)
    checkpoints = commands.add_parser("checkpoints", help="Compare observed training checkpoints")
    checkpoints.add_argument("--report", type=Path, required=True)
    checkpoints.add_argument("--out", type=Path, required=True)
    checkpoints.add_argument(
        "--population", choices=("common-selected", "all-planned"), default="common-selected"
    )
    checkpoints.add_argument("--expect-seeds", action="append", default=[], metavar="GROUP=42,43")
    review = commands.add_parser("review", help="Prepare or compile human failure investigation")
    actions = review.add_subparsers(dest="review_action", required=True)
    prepare_review = actions.add_parser("init")
    prepare_review.add_argument("--report", type=Path, required=True)
    prepare_review.add_argument("--out", type=Path, required=True)
    prepare_review.add_argument("--store", action="append", default=[], metavar="METHOD=STORE")
    compile_review = actions.add_parser("compile")
    compile_review.add_argument("--pack", type=Path, required=True)
    compile_review.add_argument("--annotations", type=Path, nargs="+", required=True)
    compile_review.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "checkpoints":
            from .checkpoints import run_summary

            expected = {}
            for value in args.expect_seeds:
                group, separator, seeds = value.partition("=")
                if not separator or group in expected:
                    raise EvaluationError("Use unique GROUP=42,43 expected-seed declarations")
                expected[group] = [int(seed.strip()) for seed in seeds.split(",")]
            result = run_summary(
                args.report, args.out, population=args.population, expected_seeds=expected
            )
        elif args.command == "review":
            from .review import compile_pack, make_pack

            if args.review_action == "compile":
                result = compile_pack(args.pack, args.annotations, args.out)
            else:
                stores = {}
                for value in args.store:
                    method, separator, path = value.partition("=")
                    if not separator or method in stores or not Path(path).is_dir():
                        raise EvaluationError("Use unique METHOD=existing_store_root mappings")
                    stores[method] = Path(path)
                result = make_pack(args.report, args.out, stores=stores)
        elif args.command == "export":
            cfg = load_config(args.config)
            if args.store is not None:
                cfg = replace(cfg, runs_dir=args.store.resolve())
            if args.out.resolve().is_relative_to(cfg.runs_dir.resolve()):
                raise EvaluationError("Export output must be outside the source store")
            data = export_collection(
                cfg,
                args.image_id,
                method=args.method,
                purpose=args.purpose,
                method_group=args.method_group,
                training_seed=args.training_seed,
            )
            safe_destination(args.out)
            publish_new(args.out, encoded(data))
            result = {
                "exported_tasks": len(data["tasks"]),
                "model_calls": 0,
                "source_store_present": data["provenance"]["source_store_present"],
                "lookup": data["provenance"]["lookup"],
                "warnings": data["provenance"]["warnings"],
            }
        elif args.command == "compare":
            result = write_report(
                compare_collections(
                    [read_json(path.read_bytes()) for path in args.input],
                    reference=args.reference,
                    bootstrap_samples=args.bootstrap_samples,
                    bootstrap_seed=args.bootstrap_seed,
                    confidence=args.confidence,
                ),
                args.out,
            )
        elif args.command == "build":
            result = build(args.manifest, args.out)
        else:
            result = verify_report(args.report)
        print(encoded(result).decode(), end="")
        return (
            3
            if (
                result.get("collection_complete") is False
                or result.get("analysis_complete") is False
            )
            else 0
        )
    except (ConfigError, OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Collection workbench: {exc}", file=sys.stderr)
        return 2
