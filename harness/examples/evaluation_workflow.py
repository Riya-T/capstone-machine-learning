"""Demonstrate saved-only evaluation tools with explicitly synthetic outcomes and sizes.

Usage:
    uv run python examples/evaluation_workflow.py --out runs/evaluation-analysis-demo --plots
    # No model is trained, called or repaired. Every outcome/size here is a fixture.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from harness.evaluation.analysis import compare
from harness.evaluation.artifacts import encoded
from harness.evaluation.matching import run_size_match
from harness.evaluation.report import write_report
from harness.evaluation.review import compile_reviews, make_review_pack
from harness.evaluation.seeds import run_seed_summary
from harness.evaluation.storage import publish_new

ROOT = Path(__file__).resolve().parents[1]


def synthetic_datasets():
    original = json.loads((ROOT / "fixtures/evaluation/fixture_original.json").read_text())
    candidate = json.loads((ROOT / "fixtures/evaluation/fixture_candidate.json").read_text())
    data = [original]
    for number in (11, 22, 33):
        record = copy.deepcopy(candidate)
        record.update(
            method=f"fixture_trained_s{number}",
            method_group="fixture_trained",
            training_seed=number,
            writer_identity=hashlib.sha256(f"synthetic-checkpoint-{number}".encode()).hexdigest(),
            writer_model=f"SYNTHETIC_NOT_A_MODEL_{number}",
        )
        # These deliberately different fixture outcomes exercise weak/tied seed reporting.
        # They were not measured from any program or model.
        if number != 11:
            for trial in record["samples"][0]["trials"]:
                if number == 22:
                    trial["steps"][-1]["status"] = "fail_new"
                else:
                    trial["steps"] = [{**trial["steps"][0], "status": "fail_new"}]
        data.append(record)
    for number, record in enumerate(data):
        record["provenance"].update(
            synthetic=True,
            size_note="Synthetic line annotations for matching tests, not measured source.",
            seed_note="Seed labels represent fictitious checkpoints; no training took place.",
        )
        for index, sample in enumerate(record["samples"]):
            lines = (40 if number == 0 else 44) + index * 10
            sample["source_metrics"] = dict(
                source_lines=lines,
                python_lines=lines,
                python_comment_lines=2,
                python_docstring_lines=1,
                python_documentation_density=3 / lines,
            )
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("runs/evaluation-analysis-demo"))
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    data = synthetic_datasets()
    for record in data:
        publish_new(args.out / "inputs" / (record["method"] + ".json"), encoded(record))
    primary = args.out / "comparison"
    write_report(compare(data, reference="fixture_original", bootstrap_samples=200), primary)
    run_size_match(primary, "fixture_trained_s11", args.out / "size-matched", tolerance=0.2)
    run_seed_summary(primary, args.out / "seeds")
    make_review_pack(primary, args.out / "review")
    compile_reviews(
        args.out / "review",
        [args.out / "review/annotations.template.csv"],
        args.out / "unreviewed-summary",
    )
    if args.plots:
        from harness.evaluation.figures import export_figures

        export_figures(primary, args.out / "figures")
    print(
        json.dumps(
            dict(
                synthetic_only=True,
                primary_dashboard=str(primary / "report.html"),
                output=str(args.out),
                inference=False,
                training=False,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
