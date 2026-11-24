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
    .venv/bin/python -m harness.datasets validate --legacy-config configs/rtx5070_train.yaml ...
    .venv/bin/python -m harness.datasets merge --out runs/combined.jsonl ...
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

from .collection.source import settings as config_settings
from .collection.source import settings_hash

HARNESS = Path(__file__).resolve().parents[2]
DATA_DIR = HARNESS / "data"
MANIFEST = "MANIFEST.json"
_NAME = re.compile(r"[a-z0-9][a-z0-9._-]*")
MAX_BYTES = 50 * 2**20  # GitHub warns about files above 50 MB
MAX_VALIDATION_ERRORS = 20


class DatasetError(ValueError):
    pass


@dataclass(frozen=True)
class PairValidation:
    pair_count: int
    per_task: dict[str, int]
    settings_hash: str
    legacy_rows: int


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


def validate_pairs(
    files: list[Path],
    *,
    legacy_settings_hash: str | None = None,
    per_task_cap: int | None = 8,
) -> PairValidation:
    """Validate scorer-generated preference files before joining them."""
    summary, _ = _validated_pair_lines(
        files,
        legacy_settings_hash=legacy_settings_hash,
        per_task_cap=per_task_cap,
    )
    return summary


def merge_pairs(
    files: list[Path],
    out: Path,
    *,
    legacy_settings_hash: str | None = None,
    per_task_cap: int | None = 8,
) -> PairValidation:
    """Validate and join preference JSONL files without deduplicating or capping."""
    resolved_out = out.resolve()
    if any(path.resolve() == resolved_out for path in files):
        raise DatasetError(f"output {out} is also one of the input files")
    if resolved_out.is_relative_to(DATA_DIR.resolve()):
        raise DatasetError(
            "merge output must stay outside harness/data; use a scratch path in runs/"
        )
    summary, lines = _validated_pair_lines(
        files,
        legacy_settings_hash=legacy_settings_hash,
        per_task_cap=per_task_cap,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    _write_atomic(out, ("\n".join(lines) + "\n").encode("utf-8"))
    return summary


def _validated_pair_lines(
    files: list[Path],
    *,
    legacy_settings_hash: str | None,
    per_task_cap: int | None,
) -> tuple[PairValidation, list[str]]:
    if not files:
        raise DatasetError("give at least one preference JSONL file")
    if per_task_cap is not None and per_task_cap < 1:
        raise DatasetError("per-task cap must be at least 1")
    if legacy_settings_hash is not None and not re.fullmatch(r"[0-9a-f]{64}", legacy_settings_hash):
        raise DatasetError("legacy settings hash must be a 64-character lowercase SHA-256")

    problems = []
    lines = []
    hashes = set()
    per_task: Counter[str] = Counter()
    task_versions = {}
    seen_pairs = {}
    legacy_rows = 0

    for path in files:
        try:
            source_lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            problems.append(f"{path}: cannot read UTF-8 input: {exc}")
            continue
        for line_number, raw in enumerate(source_lines, start=1):
            if not raw.strip():
                continue
            location = f"{path}:{line_number}"
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                problems.append(f"{location}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(row, dict):
                problems.append(f"{location}: pair must be a JSON object")
                continue

            required_strings = (
                "task_id",
                "prompt",
                "chosen_id",
                "rejected_id",
                "chosen",
                "rejected",
            )
            invalid = [
                key for key in required_strings
                if not isinstance(row.get(key), str) or not row[key].strip()
            ]
            if invalid:
                problems.append(
                    f"{location}: missing non-empty string fields: {', '.join(invalid)}"
                )
                continue

            task_id = row["task_id"]
            chosen_id, rejected_id = row["chosen_id"], row["rejected_id"]
            if chosen_id == rejected_id:
                problems.append(f"{location}: chosen_id and rejected_id are identical")
            per_task[task_id] += 1
            pair_key = (task_id, *sorted((chosen_id, rejected_id)))
            direction = (chosen_id, rejected_id)
            previous = seen_pairs.get(pair_key)
            if previous is not None:
                kind = (
                    "duplicate pair"
                    if previous[0] == direction
                    else "conflicting pair direction"
                )
                problems.append(f"{location}: {kind}; first seen at {previous[1]}")
            else:
                seen_pairs[pair_key] = (direction, location)

            if "source" not in row:
                if legacy_settings_hash is None:
                    problems.append(
                        f"{location}: missing source.settings_hash; pass --legacy-config "
                        "to verify legacy pairs"
                    )
                else:
                    hashes.add(legacy_settings_hash)
                    legacy_rows += 1
            else:
                source = row["source"]
                if not isinstance(source, dict):
                    problems.append(f"{location}: source must be a JSON object")
                else:
                    row_hash = source.get("settings_hash")
                    if not isinstance(row_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", row_hash):
                        problems.append(f"{location}: source.settings_hash must be a SHA-256 hash")
                    else:
                        hashes.add(row_hash)
                        source_settings = source.get("settings")
                        if not isinstance(source_settings, dict):
                            problems.append(f"{location}: source.settings must be a JSON object")
                        elif settings_hash(source_settings) != row_hash:
                            problems.append(
                                f"{location}: source.settings_hash does not match "
                                "source.settings"
                            )

                    task_version = source.get("task_version")
                    prompt_version = source.get("prompt_version")
                    if not all(
                        isinstance(value, str) and value
                        for value in (task_version, prompt_version)
                    ):
                        problems.append(
                            f"{location}: source task_version and prompt_version must "
                            "both be non-empty strings"
                        )
                    else:
                        version = (task_version, prompt_version)
                        previous_version = task_versions.get(task_id)
                        if previous_version is not None and previous_version[0] != version:
                            problems.append(
                                f"{location}: task/prompt version for {task_id!r} differs "
                                f"from {previous_version[1]}"
                            )
                        else:
                            task_versions[task_id] = (version, location)
            lines.append(raw.strip())

    if not lines:
        problems.append("no preference pairs found")
    if len(hashes) > 1:
        problems.append(
            "incompatible settings_hash values: " + ", ".join(sorted(hashes))
        )
    if per_task_cap is not None:
        for task_id, count in sorted(per_task.items()):
            if count > per_task_cap:
                problems.append(
                    f"task {task_id!r} has {count} pairs, above the per-task cap {per_task_cap}"
                )
    if problems:
        if len(problems) > MAX_VALIDATION_ERRORS:
            omitted = len(problems) - MAX_VALIDATION_ERRORS
            problems = problems[:MAX_VALIDATION_ERRORS] + [
                f"... {omitted} additional validation errors omitted"
            ]
        raise DatasetError("\n".join(problems))

    return (
        PairValidation(
            pair_count=len(lines),
            per_task=dict(sorted(per_task.items())),
            settings_hash=next(iter(hashes)),
            legacy_rows=legacy_rows,
        ),
        lines,
    )


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

    parser = argparse.ArgumentParser(
        prog="python -m harness.datasets", description=__doc__.split("\n\n")[0]
    )
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="add existing files to a dataset under their own names")
    add.add_argument("dataset")
    add.add_argument("files", nargs="+", type=Path)
    sub.add_parser("verify", help="check every dataset against its manifest")
    validate = sub.add_parser("validate", help="validate preference JSONL files before joining")
    validate.add_argument("files", nargs="+", type=Path)
    _add_pair_validation_options(validate)
    merge = sub.add_parser("merge", help="validate and join compatible preference JSONL files")
    merge.add_argument("--out", required=True, type=Path, help="scratch JSONL output path")
    merge.add_argument("files", nargs="+", type=Path)
    _add_pair_validation_options(merge)
    args = parser.parse_args(argv)
    if args.command == "add":
        try:
            for path in args.files:
                add_file(args.dataset, path.name, path.read_bytes())
        except (DatasetError, OSError) as exc:
            parser.error(str(exc))
        return 0
    if args.command in ("validate", "merge"):
        legacy_hash, cap = _pair_validation_options(args, parser)
        try:
            if args.command == "validate":
                summary = validate_pairs(
                    args.files, legacy_settings_hash=legacy_hash, per_task_cap=cap
                )
            else:
                summary = merge_pairs(
                    args.files,
                    args.out,
                    legacy_settings_hash=legacy_hash,
                    per_task_cap=cap,
                )
        except (DatasetError, OSError) as exc:
            parser.error(str(exc))
        max_task = max(summary.per_task.values())
        print(
            f"{summary.pair_count} pairs from {len(summary.per_task)} tasks; "
            f"max/task {max_task}; settings {summary.settings_hash}"
            + (f"; {summary.legacy_rows} legacy rows mapped" if summary.legacy_rows else "")
            + (f" -> {args.out}" if args.command == "merge" else "")
        )
        return 0
    problems = [problem for folder in datasets() for problem in verify(folder)]
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(datasets())} datasets, {len(problems)} problems")
    return 1 if problems else 0


def _add_pair_validation_options(parser) -> None:
    parser.add_argument(
        "--legacy-config",
        type=Path,
        help="config used for preference rows without a source block",
    )
    cap = parser.add_mutually_exclusive_group()
    cap.add_argument(
        "--per-task-cap", type=int, default=8, help="maximum pairs per task (default: 8)"
    )
    cap.add_argument(
        "--no-per-task-cap", action="store_true", help="disable the per-task pair limit"
    )


def _pair_validation_options(args, parser) -> tuple[str | None, int | None]:
    from .config import load_config

    legacy_hash = None
    if args.legacy_config is not None:
        try:
            legacy_hash = settings_hash(config_settings(load_config(args.legacy_config)))
        except (OSError, ValueError, yaml.YAMLError) as exc:
            parser.error(f"--legacy-config: {exc}")
    cap = None if args.no_per_task_cap else args.per_task_cap
    if cap is not None and cap < 1:
        parser.error("--per-task-cap must be at least 1")
    return legacy_hash, cap


if __name__ == "__main__":
    raise SystemExit(main())
