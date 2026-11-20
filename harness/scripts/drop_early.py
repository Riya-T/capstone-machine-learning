"""Drop training rows whose program implements a later change early.

A writer shown a task's later change requests (foresight, see
src/harness/foresight.py) may implement some of them in its first version.
The editor would then find those changes easy for the wrong reason, so such
programs are kept out of training data. This reads a JSONL file of
preference pairs (chosen, rejected) or SFT rows (completion), drops every
row in which any program implements a later change of its task by
`implements_later_change`, and writes the rest. It reports how many rows
and distinct programs were dropped, per task.

Reads files only; it runs no models or sandboxes.

Usage (from harness/):
    uv run python scripts/drop_early.py --config configs/rtx5070_hist_train_foresight.yaml \
        --input runs/rtx5070_pc/dpo/hist_fs_all.jsonl --out runs/rtx5070_pc/dpo/hist_fs.jsonl
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from harness.config import load_config
from harness.foresight import implements_later_change
from harness.models.parser import code_blocks
from harness.registry import load_tasks

FIELDS = ("chosen", "rejected", "completion")


def program_of(text: str) -> dict[str, bytes]:
    """The fenced blocks of a rendered program, as files the rule can read."""
    return {
        f"block{i}.py": content.encode("utf-8") for i, (_, content) in enumerate(code_blocks(text))
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    tasks = load_tasks(load_config(args.config).tasks)
    kept, dropped, early_programs = [], Counter(), {}
    for line in args.input.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        task = tasks[row["task_id"]]
        early = False
        for field in FIELDS:
            if field in row:
                text = row[field]
                if text not in early_programs:
                    early_programs[text] = implements_later_change(program_of(text), task)
                early |= early_programs[text]
        if early:
            dropped[row["task_id"]] += 1
        else:
            kept.append(line)
    args.out.write_text("".join(f"{line}\n" for line in kept), encoding="utf-8")
    flagged = sum(early_programs.values())
    print(
        f"kept {len(kept)} of {len(kept) + sum(dropped.values())} rows; "
        f"{flagged} of {len(early_programs)} distinct programs implement a later change early"
    )
    for task_id, n in sorted(dropped.items()):
        print(f"  {task_id}: {n} rows dropped")


if __name__ == "__main__":
    main()
