"""Filter the scorer's preference pairs into a DPO training file.

Keeps a pair only if:

- the chosen program beats the rejected one in at least --min-rep-wins of
  the repetitions (each repetition's scores summed over the sequences), so
  a pair won on one lucky repetition is dropped;
- with --drop-cosmetic, the two programs differ in more than string
  literals, docstrings, local names and type annotations: programs that are
  the same code apart from those have the same design, so their pair can
  only be luck;
- its task is not in --drop-tasks.

Usage (from harness/):
    python scripts/filter_pairs.py runs/rtx5070_pc/dpo/pairs_cap8_all.jsonl \
        runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl --min-rep-wins 2 --drop-cosmetic
"""

import argparse
import ast
import builtins
import json
import re
from collections import Counter
from pathlib import Path

BLOCK = re.compile(r"```python file=\S+\n(.*?)```", re.S)
BUILTINS = set(dir(builtins))


def source(reply: str) -> str:
    return "\n".join(BLOCK.findall(reply))


class _StripStrings(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None  # docstring
        return self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            return ast.copy_location(ast.Constant(""), node)
        return node

    def visit_JoinedStr(self, node):
        return ast.copy_location(ast.Constant(""), node)


class _Rename(ast.NodeTransformer):
    """Rename every name that is not a def/class/import name or a builtin."""

    def __init__(self, keep: set[str]):
        self.keep, self.names = keep, {}

    def _name(self, name: str) -> str:
        if name in self.keep or name in BUILTINS or name == "self":
            return name
        return self.names.setdefault(name, f"v{len(self.names)}")

    def visit_Name(self, node):
        node.id = self._name(node.id)
        return node

    def visit_arg(self, node):
        node.arg, node.annotation = self._name(node.arg), None
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        node.attr = self._name(node.attr)
        return node


def shape(code: str) -> str:
    tree = _StripStrings().visit(ast.parse(code))
    keep = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            keep.add(node.name)
            if not isinstance(node, ast.ClassDef):
                node.returns = None
        elif isinstance(node, ast.Import | ast.ImportFrom):
            keep.update(alias.asname or alias.name for alias in node.names)
    return ast.dump(_Rename(keep).visit(tree), annotate_fields=False)


def rep_wins(row: dict) -> int:
    chosen, rejected = row["chosen_scores"], row["rejected_scores"]  # [sequence][repetition]
    reps = len(chosen[0])
    return sum(sum(seq[i] for seq in chosen) > sum(seq[i] for seq in rejected) for i in range(reps))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--min-rep-wins", type=int, default=2)
    parser.add_argument("--drop-cosmetic", action="store_true")
    parser.add_argument("--drop-tasks", default="", help="comma-separated task ids")
    args = parser.parse_args()
    drop_tasks = {t for t in args.drop_tasks.split(",") if t}
    kept, dropped = [], Counter()
    for line in args.source.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["task_id"] in drop_tasks:
            dropped["task dropped"] += 1
        elif rep_wins(row) < args.min_rep_wins:
            dropped["too few repetition wins"] += 1
        elif args.drop_cosmetic and shape(source(row["chosen"])) == shape(source(row["rejected"])):
            dropped["cosmetic"] += 1
        else:
            kept.append(row)
    args.out.write_text("".join(json.dumps(r) + "\n" for r in kept), encoding="utf-8")
    tasks = Counter(r["task_id"] for r in kept)
    print(f"kept {len(kept)} pairs from {len(tasks)} tasks; dropped: {dict(dropped)} -> {args.out}")


if __name__ == "__main__":
    main()
