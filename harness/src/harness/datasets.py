"""Datasets in harness/data/: final data files that git tracks.

harness/runs/ (stores, blobs, logs) stays out of git. The scripts that make
training files (filter_pairs, match_pairs, sft_programs, static_ranking)
take --dataset NAME and then write their output to harness/data/NAME/
instead of --out. Each file is recorded in the folder's MANIFEST.json with
its sha256, size and row count, the command that made it, the git commit
and the date. See harness/data/README.md.

A file in a dataset is never replaced: writing different content under a
name that exists is refused (a new version is a new dataset, such as
train-v2), and writing the same content again changes nothing, so a
rerun of the same command is safe. tests/test_datasets.py checks every
file still matches its manifest.

Usage:
    path = save_output(text, out=args.out, dataset=args.dataset, filename="pairs.jsonl")
    problems = verify(DATA_DIR / "train-v1")  # [] when every file matches

    # from harness/: add files made before --dataset existed, or check every dataset
    .venv/bin/python -m harness.datasets add train-v1 runs/rtx5070_pc/dpo/pairs_cap8_all.jsonl ...
    .venv/bin/python -m harness.datasets verify
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2]
DATA_DIR = HARNESS / "data"
MANIFEST = "MANIFEST.json"
_NAME = re.compile(r"[a-z0-9][a-z0-9._-]*")
MAX_BYTES = 50 * 2**20  # GitHub warns about files above 50 MB


class DatasetError(ValueError):
    pass


def save_output(
    text: str,
    *,
    out: Path | None,
    dataset: str | None,
    filename: str,
    data_dir: Path | None = None,
) -> Path:
    """Write a script's output to `out`, or into the dataset as `filename`.
    Exactly one of `out` and `dataset` must be given."""
    if (out is None) == (dataset is None):
        raise DatasetError("give an output path or --dataset, not both")
    if dataset is not None:
        return add_file(dataset, filename, text.encode("utf-8"), data_dir=data_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def add_file(
    dataset: str,
    filename: str,
    content: bytes,
    *,
    command: list[str] | None = None,
    data_dir: Path | None = None,
) -> Path:
    """Add one file to a dataset (created if new) and record it."""
    data_dir = DATA_DIR if data_dir is None else data_dir
    if not _NAME.fullmatch(dataset):
        raise DatasetError(f"dataset {dataset!r}: use lowercase letters, digits, '.', '_', '-'")
    if not _NAME.fullmatch(filename) or filename == MANIFEST:
        raise DatasetError(f"file name {filename!r}: use lowercase letters, digits, '.', '_', '-'")
    if len(content) > MAX_BYTES:
        raise DatasetError(f"{filename}: {len(content) / 2**20:.1f} MB is too big for git")
    folder = data_dir / dataset
    path = folder / filename
    manifest = _read_manifest(folder) if folder.exists() else {"dataset": dataset, "files": []}
    digest = hashlib.sha256(content).hexdigest()
    if path.exists():
        if path.read_bytes() == content:
            print(f"{dataset}/{filename}: unchanged")
            return path
        raise DatasetError(
            f"{dataset}/{filename} already exists with different content; files in a dataset "
            "are never replaced, so write to a new dataset (such as train-v2)"
        )
    rows = None
    if filename.endswith(".jsonl"):
        rows = sum(1 for line in content.decode("utf-8").splitlines() if line.strip())
    commit, dirty = _git()
    manifest["files"].append(
        dict(
            name=filename,
            sha256=digest,
            bytes=len(content),
            rows=rows,
            command=_shown(command if command is not None else sys.argv),
            git_commit=commit,
            git_dirty=dirty,
            created=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
    )
    folder.mkdir(parents=True, exist_ok=True)
    _write_atomic(path, content)
    _write_atomic(folder / MANIFEST, (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    print(
        f"{dataset}/{filename}: added ({len(content)} bytes"
        + ("" if rows is None else f", {rows} rows")
        + ")"
    )
    print(
        f"to share it: git add {path.relative_to(HARNESS.parent).as_posix()}"
        if path.is_relative_to(HARNESS.parent)
        else f"wrote {path}"
    )
    return path


def verify(folder: Path) -> list[str]:
    """Problems with one dataset: files missing, unlisted or changed."""
    try:
        manifest = _read_manifest(folder)
    except DatasetError as exc:
        return [str(exc)]
    listed = [entry["name"] for entry in manifest["files"]]
    present = {p.name for p in folder.iterdir() if p.is_file() and p.name != MANIFEST}
    problems = [
        f"{folder.name}/{name}: in the folder but not in {MANIFEST}"
        for name in sorted(present - set(listed))
    ]
    for entry in manifest["files"]:
        path = folder / entry["name"]
        if not path.is_file():
            problems.append(f"{folder.name}/{entry['name']}: missing")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            problems.append(f"{folder.name}/{entry['name']}: changed since it was added")
    return problems


def datasets(data_dir: Path | None = None) -> list[Path]:
    """Every dataset folder in data_dir (harness/data/ by default)."""
    data_dir = DATA_DIR if data_dir is None else data_dir
    if not data_dir.is_dir():
        return []
    return sorted(p for p in data_dir.iterdir() if p.is_dir() and not p.name.startswith("."))


def _read_manifest(folder: Path) -> dict:
    path = folder / MANIFEST
    if not path.is_file():
        raise DatasetError(f"{folder.name}: no {MANIFEST}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_atomic(path: Path, content: bytes) -> None:
    partial = path.with_name(f".{path.name}.partial")
    partial.write_bytes(content)
    os.replace(partial, path)


def _shown(argv: list[str]) -> str:
    """The command line, with paths inside the repository made relative and
    the home directory hidden, so no personal path ends up in git."""
    repo, home = str(HARNESS) + os.sep, str(Path.home()) + os.sep
    parts = []
    for arg in argv:
        arg = arg.replace(repo, "")
        parts.append(arg.replace(home, "~/"))
    if parts and parts[0].endswith(".py"):
        parts[0] = "python " + parts[0]
    return " ".join(parts)


def _git() -> tuple[str | None, bool | None]:
    """The checked-out commit, and whether tracked files had changes."""

    def run(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=HARNESS, capture_output=True, text=True, check=True
        ).stdout

    try:
        return run("rev-parse", "HEAD").strip(), bool(run("status", "--porcelain", "-uno").strip())
    except (OSError, subprocess.CalledProcessError):
        return None, None


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m harness.datasets", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="add existing files to a dataset under their own names")
    add.add_argument("dataset")
    add.add_argument("files", nargs="+", type=Path)
    sub.add_parser("verify", help="check every dataset against its manifest")
    args = parser.parse_args(argv)
    if args.command == "add":
        try:
            for path in args.files:
                add_file(args.dataset, path.name, path.read_bytes())
        except (DatasetError, OSError) as exc:
            parser.error(str(exc))
        return 0
    problems = [problem for folder in datasets() for problem in verify(folder)]
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(datasets())} datasets, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
