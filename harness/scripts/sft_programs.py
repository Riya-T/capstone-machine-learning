"""Write the correctness-only baseline's training file: passing writer programs.

For each train task this takes the writer's programs that pass the initial
checks, the first --max-programs in sample order (the programs the editor
worked on and the preference pairs were built from), and writes one
{"task_id", "candidate_id", "prompt", "completion"} row per program, the
completion rendered as in the preference pairs. With --tasks-from, only the
tasks of that pairs file are used, so the baseline sees the same tasks and
programs as our writer but no editing outcomes.

This reads the existing collection store only; it runs no models or sandboxes.

Usage (from harness/):
    uv run python scripts/sft_programs.py --config configs/rtx5070_train.yaml \
        --tasks-from runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl \
        --out runs/rtx5070_pc/dpo/sft_programs.jsonl
    # or into a tracked dataset (harness/data/README.md):
    uv run python scripts/sft_programs.py --config configs/rtx5070_train.yaml \
        --tasks-from data/train-v2/pairs.jsonl --dataset train-v2
"""

import argparse
import json
from pathlib import Path

from harness.collection.collect import Keys, sandbox_owner
from harness.config import load_config
from harness.datasets import save_output
from harness.models.parser import render_program
from harness.registry import build_writer_prompt, load_tasks, load_template, prompt_version
from harness.sandbox.runner import make_runner
from harness.store import Store


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="output file (or use --dataset)")
    parser.add_argument(
        "--dataset", help="write to harness/data/DATASET/sft_programs.jsonl instead"
    )
    parser.add_argument("--tasks-from", type=Path, help="pairs JSONL whose tasks to keep")
    args = parser.parse_args()
    if (args.out is None) == (args.dataset is None):
        parser.error("give --out or --dataset, not both")
    cfg = load_config(args.config)
    image_id = make_runner(cfg, owner=sandbox_owner(cfg)).existing_image_id()
    if image_id is None:
        raise SystemExit("sandbox image not found; initial checks are keyed by its id")
    keys = Keys.of(cfg, image_id)
    template = load_template(cfg.writer.prompt_template)
    tasks = load_tasks(cfg.tasks)
    if args.tasks_from:
        lines = args.tasks_from.read_text(encoding="utf-8").splitlines()
        wanted = {json.loads(line)["task_id"] for line in lines}
        tasks = {task_id: task for task_id, task in tasks.items() if task_id in wanted}

    rows = []
    with Store(cfg.runs_dir) as store:
        for task in tasks.values():
            prompt = build_writer_prompt(task.writer_view(), template)
            seen, kept = set(), 0
            for sample in store.candidates(task.id, prompt_version(prompt), keys.writer):
                candidate_id = sample.candidate_id
                if candidate_id is None or candidate_id in seen:
                    continue
                seen.add(candidate_id)
                check = store.get_initial_check(
                    task.id, task.task_version, candidate_id, keys.sandbox
                )
                if check is None:
                    raise SystemExit(f"{task.id}: initial check missing for {candidate_id}")
                if not check.passed or kept >= cfg.tasks.max_programs:
                    continue
                kept += 1
                completion = render_program(store.get_blob(candidate_id))
                rows.append(
                    {
                        "task_id": task.id,
                        "candidate_id": candidate_id,
                        "prompt": prompt,
                        "completion": completion,
                    }
                )
    text = "".join(json.dumps(r) + "\n" for r in rows)
    out = save_output(text, out=args.out, dataset=args.dataset, filename="sft_programs.jsonl")
    print(f"wrote {len(rows)} programs from {len({r['task_id'] for r in rows})} tasks -> {out}")


if __name__ == "__main__":
    main()
