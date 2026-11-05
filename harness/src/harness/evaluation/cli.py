"""Evaluation CLI: safe dry-run by default, explicit execution, offline comparison.

Usage:
    python -m harness evaluate --plan configs/evaluation.example.yaml
    python -m harness evaluation-report --input original.json trained.json --out runs/comparison
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..config import ConfigError
from ..sandbox.runner import SandboxError
from ..store import StoreError
from .analysis import compare
from .integrity import verify_report
from .plan import execute, prepare, preview
from .records import read_json
from .report import OUTPUT_NAMES, write_report


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Matched writer evaluation and saved-only reporting"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser(
        "evaluate", help="Preview or explicitly run a matched evaluation plan"
    )
    evaluate.add_argument("--plan", type=Path, required=True)
    mode = evaluate.add_mutually_exclusive_group()
    mode.add_argument("--run", action="store_true", help="Call configured local models and sandbox")
    mode.add_argument("--dry-run", action="store_true", help="Preview only (the default)")
    mode.add_argument(
        "--export-only", action="store_true", help="Read saved stores; no inference/container"
    )
    report = sub.add_parser(
        "evaluation-report", help="Compare exported records without models or Docker"
    )
    report.add_argument("--input", type=Path, nargs="+", required=True)
    report.add_argument("--out", type=Path, required=True)
    report.add_argument("--reference")
    report.add_argument("--bootstrap-samples", type=int, default=2000)
    report.add_argument("--bootstrap-seed", type=int, default=20261105)
    report.add_argument("--confidence", type=float, default=0.95)
    verify = sub.add_parser("evaluation-verify", help="Verify a saved report without inference")
    verify.add_argument("--report", type=Path, required=True)
    verify.add_argument(
        "--checksums-only",
        action="store_true",
        help="Skip analysis recomputation (e.g. for a historical analysis version)",
    )
    preflight = sub.add_parser(
        "evaluation-preflight", help="Read-only checks before live evaluation"
    )
    preflight.add_argument("--plan", required=True, type=Path)
    preflight.add_argument(
        "--probe", action="store_true", help="Inspect Docker and GET local model lists"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "evaluation-preflight":
            from .preflight import check_preflight

            result = check_preflight(prepare(args.plan), probe=args.probe)
            print(json.dumps(result, indent=2, allow_nan=False))
            return 0 if result["ready"] else 3
        if args.command == "evaluation-verify":
            print(
                json.dumps(verify_report(args.report, recompute=not args.checksums_only), indent=2)
            )
            return 0
        if args.command == "evaluate":
            prepared = prepare(args.plan)
            result = (
                execute(prepared, export_only=args.export_only)
                if (args.run or args.export_only)
                else preview(prepared)
            )
            print(json.dumps(result, indent=2, allow_nan=False))
            return 0 if result.get("complete", True) else 3
        datasets = [read_json(p.read_text(encoding="utf8")) for p in args.input]
        targets = {args.out / name for name in OUTPUT_NAMES}
        if {p.resolve() for p in args.input} & {p.resolve() for p in targets}:
            raise ConfigError("Report output would overwrite an input dataset")
        result = compare(
            datasets,
            reference=args.reference,
            bootstrap_samples=args.bootstrap_samples,
            bootstrap_seed=args.bootstrap_seed,
            confidence=args.confidence,
        )
        print(json.dumps({k: str(v) for k, v in write_report(result, args.out).items()}, indent=2))
        return 0
    except (ConfigError, OSError, ValueError, SandboxError, StoreError) as exc:
        print(f"Evaluation error: {exc}", file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
