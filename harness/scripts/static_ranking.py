"""Build DPO preferences by ranking passing writer programs with Radon MI.

Usage (from harness/):
    uv run python scripts/static_ranking.py --config configs/rtx5070_train.yaml
    uv run python scripts/static_ranking.py --config configs/rtx5070_train.yaml \
        --out runs/static-ranking/preferences.jsonl
    uv run python scripts/static_ranking.py --config configs/rtx5070_train.yaml \
        --dataset train-v2   # into harness/data/train-v2/ (harness/data/README.md)

This reads the existing collection store and runs no models or sandboxes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

from radon.metrics import mi_visit
from radon.raw import analyze

from harness.collection.collect import Keys, sandbox_owner
from harness.config import ExperimentConfig, load_config
from harness.datasets import add_file
from harness.models.parser import render_program
from harness.registry import build_writer_prompt, load_tasks, load_template, prompt_version
from harness.sandbox.runner import make_runner
from harness.store import Store


@dataclass(frozen=True)
class RankedProgram:
    candidate_id: str
    files: dict[str, bytes]
    score: float
    call_keys: tuple[str, ...]


def maintainability_score(files: dict[str, bytes]) -> float:
    """Return a LOC-weighted average Radon Maintainability Index (0–100)."""
    weighted_scores = []
    for path, content in sorted(files.items()):
        try:
            source = content.decode("utf-8")
            score = mi_visit(source, multi=True)
            lines = analyze(source).loc
        except (SyntaxError, UnicodeDecodeError) as exc:
            raise ValueError(f"{path}: cannot calculate Radon MI: {exc}") from exc
        weighted_scores.append((score, max(lines, 1)))
    if not weighted_scores:
        raise ValueError("cannot score a program with no files")
    total_lines = sum(lines for _, lines in weighted_scores)
    return round(sum(score * lines for score, lines in weighted_scores) / total_lines, 4)


def make_preferences(
    task_id: str,
    prompt: str,
    programs: list[RankedProgram],
    per_task_cap: int | None,
) -> tuple[list[dict[str, Any]], Counter[str]]:
    """Pair higher-MI programs against lower-MI programs within one task."""
    pairs = []
    tied = 0
    for left, right in combinations(programs, 2):
        if left.score == right.score:
            tied += 1
            continue
        chosen, rejected = (left, right) if left.score > right.score else (right, left)
        pairs.append(
            {
                "task_id": task_id,
                "prompt": prompt,
                "chosen": render_program(chosen.files),
                "rejected": render_program(rejected.files),
                "chosen_id": chosen.candidate_id,
                "rejected_id": rejected.candidate_id,
                "rule": "radon_mi",
                "pairing_mode": "all_pairs",
                "chosen_scores": [chosen.score],
                "rejected_scores": [rejected.score],
                "margin": round(chosen.score - rejected.score, 4),
                "chosen_call_keys": list(chosen.call_keys),
                "rejected_call_keys": list(rejected.call_keys),
            }
        )
    pairs.sort(key=lambda pair: (-pair["margin"], pair["chosen_id"], pair["rejected_id"]))
    capped = 0
    if per_task_cap is not None and len(pairs) > per_task_cap:
        capped = len(pairs) - per_task_cap
        pairs = pairs[:per_task_cap]
    return pairs, Counter(
        programs=len(programs),
        comparisons=len(programs) * (len(programs) - 1) // 2,
        ties=tied,
        pairs=len(pairs),
        capped=capped,
    )


def build_preferences(cfg: ExperimentConfig, image_id: str) -> tuple[list[dict], dict]:
    """Read passing writer samples from the collection store and rank them."""
    keys = Keys.of(cfg, image_id)
    template = load_template(cfg.writer.prompt_template)
    tasks = load_tasks(cfg.tasks)
    all_pairs = []
    totals: Counter[str] = Counter()
    task_reports = {}

    with Store(cfg.runs_dir) as store:
        for task_id, task in tasks.items():
            prompt = build_writer_prompt(task.writer_view(), template)
            samples = store.candidates(task.id, prompt_version(prompt), keys.writer)
            if not samples:
                raise RuntimeError(
                    f"{task.id}: no writer samples in {cfg.runs_dir}; "
                    "collect the train tasks through the initial-check stage first"
                )

            programs = []
            seen = set()
            for sample in samples:
                candidate_id = sample.candidate_id
                if candidate_id is None or candidate_id in seen:
                    continue
                seen.add(candidate_id)
                check = store.get_initial_check(
                    task.id, task.task_version, candidate_id, keys.sandbox
                )
                if check is None:
                    raise RuntimeError(
                        f"{task.id}: initial check missing for candidate {candidate_id}; "
                        "finish initial checks before building static-ranking preferences"
                    )
                if not check.passed:
                    continue
                if len(programs) >= cfg.tasks.max_programs:
                    continue
                files = store.get_blob(candidate_id)
                programs.append(
                    RankedProgram(
                        candidate_id,
                        files,
                        maintainability_score(files),
                        tuple(
                            row.call_key
                            for row in samples
                            if row.candidate_id == candidate_id and row.call_key
                        ),
                    )
                )

            pairs, stats = make_preferences(task_id, prompt, programs, cfg.scorer.per_task_cap)
            all_pairs.extend(pairs)
            totals.update(stats)
            task_reports[task_id] = dict(stats)

    report = {
        "metric": "Radon Maintainability Index, LOC-weighted across program files",
        "direction": "higher is preferred",
        "pairing": "all unequal-score pairs within each task; largest MI margins kept per-task",
        "per_task_cap": cfg.scorer.per_task_cap,
        "totals": dict(totals),
        "tasks": task_reports,
    }
    return all_pairs, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--out",
        type=Path,
        help="preference JSONL output (default: <runs_dir>/static_ranking/preferences.jsonl)",
    )
    parser.add_argument(
        "--dataset",
        help="write to harness/data/DATASET/ as radon_all.jsonl and radon_all_report.json",
    )
    args = parser.parse_args()
    if args.out and args.dataset:
        parser.error("give --out or --dataset, not both")
    cfg = load_config(args.config)
    runner = make_runner(cfg, owner=sandbox_owner(cfg))
    image_id = runner.existing_image_id()
    if image_id is None:
        raise SystemExit("sandbox image not found; initial checks are keyed by its id")

    pairs, report = build_preferences(cfg, image_id)
    if args.dataset:
        text = "".join(json.dumps(pair, ensure_ascii=False) + "\n" for pair in pairs)
        output = add_file(args.dataset, "radon_all.jsonl", text.encode("utf-8"))
        report_text = json.dumps(report, indent=2) + "\n"
        add_file(args.dataset, "radon_all_report.json", report_text.encode("utf-8"))
        print(f"Wrote {len(pairs)} static-ranking preference pairs to {output}")
        return
    output = args.out or cfg.runs_dir / "static_ranking" / "preferences.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for pair in pairs:
            file.write(json.dumps(pair, ensure_ascii=False) + "\n")
    report_path = output.with_name("preferences_report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(pairs)} static-ranking preference pairs to {output}")
    print(f"Wrote pair counts to {report_path}")


if __name__ == "__main__":
    main()
