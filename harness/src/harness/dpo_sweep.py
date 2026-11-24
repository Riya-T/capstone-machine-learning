"""Prepare and track reproducible, dev-only history-suite DPO sweeps.

Run from ``harness/``:

    uv run python -m harness.dpo_sweep prepare \\
        --preferences runs/nexus_hist/pairs_coarse/preferences.jsonl \\
        --hf-revision <40-character-Hugging-Face-commit>
    bash runs/dpo_sweeps/hist2_beta_nll_dev/submit.sh

Usage:
    python -m harness.dpo_sweep {prepare,record-jobs} --help

Preparation does not submit jobs or run training. It hashes the pair file,
pins the base-model revision, writes one manifest and evaluation config per
seed, and creates a sequential Slurm submission script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from harness.config import ConfigError, load_config

HARNESS_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SPEC = HARNESS_DIR / "configs/dpo_sweeps/history_beta_nll.yaml"
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read YAML file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return value


def _finite_number(value: Any, label: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{label} must be finite and at least {minimum}")
    return float(value)


def load_spec(path: Path) -> dict[str, Any]:
    """Load and validate the fixed sweep definition."""
    spec = _read_yaml(path)
    required = {
        "name",
        "base_eval_config",
        "learning_rate",
        "epochs",
        "seeds",
        "base_dev_passing_programs",
        "candidate_settings",
    }
    if set(spec) != required:
        missing, extra = required - set(spec), set(spec) - required
        raise ValueError(f"invalid sweep keys; missing={sorted(missing)}, extra={sorted(extra)}")
    if not isinstance(spec["name"], str) or not NAME_PATTERN.fullmatch(spec["name"]):
        raise ValueError("sweep name may use letters, digits, _, . and - only")
    if (
        not isinstance(spec["base_eval_config"], str)
        or Path(spec["base_eval_config"]).name != spec["base_eval_config"]
    ):
        raise ValueError("base_eval_config must be a config filename")
    spec["learning_rate"] = _finite_number(spec["learning_rate"], "learning_rate", minimum=1e-12)
    spec["epochs"] = _finite_number(spec["epochs"], "epochs", minimum=1e-12)

    seeds = spec["seeds"]
    if (
        not isinstance(seeds, list)
        or not seeds
        or any(type(seed) is not int or seed < 0 for seed in seeds)
        or len(set(seeds)) != len(seeds)
    ):
        raise ValueError("seeds must be a non-empty list of unique non-negative integers")
    base_passes = spec["base_dev_passing_programs"]
    if type(base_passes) is not int or base_passes < 1:
        raise ValueError("base_dev_passing_programs must be a positive integer")

    settings = spec["candidate_settings"]
    if not isinstance(settings, list) or not settings:
        raise ValueError("candidate_settings must be a non-empty list")
    names: set[str] = set()
    combinations: set[tuple[float, float]] = set()
    for setting in settings:
        if not isinstance(setting, dict) or set(setting) != {"name", "beta", "nll_weight"}:
            raise ValueError("each candidate must contain exactly name, beta, and nll_weight")
        name = setting["name"]
        if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name) or name in names:
            raise ValueError(f"candidate name is invalid or duplicated: {name!r}")
        names.add(name)
        setting["beta"] = _finite_number(setting["beta"], f"{name}.beta", minimum=1e-12)
        setting["nll_weight"] = _finite_number(setting["nll_weight"], f"{name}.nll_weight")
        pair = setting["beta"], setting["nll_weight"]
        if pair in combinations:
            raise ValueError(f"duplicate beta/NLL combination: {pair}")
        combinations.add(pair)
    return spec


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as source:
        return sum(1 for _ in source)


def _git_state() -> tuple[str, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=HARNESS_DIR.parent,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=HARNESS_DIR.parent,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"cannot record the repository revision: {exc}") from exc
    return commit, dirty


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _run_id(sweep: str, setting: str, seed: int) -> str:
    return f"{sweep}_{setting}_s{seed}"


def _eval_config(
    *,
    config_dir: Path,
    sweep_name: str,
    run_id: str,
    base_eval_config: str,
) -> Path:
    filename = f"dpo-sweep-{sweep_name}-{run_id}.yaml"
    path = config_dir / filename
    if path.exists():
        raise ValueError(f"generated evaluation config already exists: {path}")
    config = {
        "extends": base_eval_config,
        "name": f"dpo-sweep-{run_id}",
        "runs_dir": f"../runs/dpo_sweeps/{sweep_name}/evaluation",
        "writer": {"backend": {"model": f"writer-{run_id}-ctx8k"}},
    }
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    try:
        load_config(path)
    except (ConfigError, OSError, yaml.YAMLError):
        path.unlink(missing_ok=True)
        raise
    return path


def _shell_script(
    *,
    harness_dir: Path,
    preferences: Path,
    output_dir: Path,
    config_dir: Path,
    hf_revision: str,
    runs: list[dict[str, Any]],
) -> str:
    relative_root = os.path.relpath(harness_dir, output_dir)
    lines = [
        "#!/usr/bin/env bash",
        "# Run from the Nexus submission node after collect_nexus has installed Ollama.",
        "set -euo pipefail",
        'SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)',
        f'cd "$(cd -- "$SCRIPT_DIR"/{shlex.quote(relative_root)} && pwd)"',
        "PREVIOUS_JOB=",
    ]
    for index, run in enumerate(runs):
        run_id = run["run_id"]
        training = run["training"]
        train_args = [
            "sbatch",
            "--parsable",
            f"--export=ALL,HF_REVISION={hf_revision}",
        ]
        if index:
            train_args.append('--dependency="afterok:${PREVIOUS_JOB}"')
        train_args.extend(
            [
                "scripts/train_nexus.sbatch",
                str(preferences),
                run_id,
                "--epochs",
                str(training["epochs"]),
                "--learning-rate",
                str(training["learning_rate"]),
                "--beta",
                str(training["beta"]),
                "--nll-weight",
                str(training["nll_weight"]),
                "--seed",
                str(training["seed"]),
            ]
        )
        train_cmd = " ".join(
            arg if arg.startswith("--dependency=") else shlex.quote(arg) for arg in train_args
        )
        eval_config = Path(os.path.relpath(config_dir, harness_dir)) / run["evaluation"]["config"]
        lines.extend(
            [
                f"TRAIN_JOB=$({train_cmd})",
                "TRAIN_JOB=${TRAIN_JOB%%;*}",
                "python -m harness.dpo_sweep record-jobs "
                f"--manifest {shlex.quote(str(output_dir / 'manifest.json'))} "
                f'--run-id {shlex.quote(run_id)} --train-job "$TRAIN_JOB"',
                f'EVAL_JOB=$(sbatch --parsable --dependency="afterok:${{TRAIN_JOB}}" '
                f"scripts/collect_nexus.sbatch {shlex.quote(str(eval_config))} --until initial)",
                "EVAL_JOB=${EVAL_JOB%%;*}",
                "python -m harness.dpo_sweep record-jobs "
                f"--manifest {shlex.quote(str(output_dir / 'manifest.json'))} "
                f'--run-id {shlex.quote(run_id)} --eval-job "$EVAL_JOB"',
                "PREVIOUS_JOB=$EVAL_JOB",
                f'echo "{run_id}: train=$TRAIN_JOB eval=$EVAL_JOB"',
            ]
        )
    return "\n".join(lines) + "\n"


def prepare(
    *,
    spec_path: Path,
    preferences: Path,
    hf_revision: str,
    output_dir: Path,
    config_dir: Path = HARNESS_DIR / "configs",
) -> Path:
    """Write all per-seed manifests, generated dev configs and submission commands."""
    spec_path = spec_path.resolve()
    preferences = preferences.resolve()
    output_dir = output_dir.resolve()
    config_dir = config_dir.resolve()
    if not preferences.is_file():
        raise ValueError(f"preferences file does not exist: {preferences}")
    if preferences.stat().st_size == 0:
        raise ValueError(f"preferences file is empty: {preferences}")
    if not SHA_PATTERN.fullmatch(hf_revision):
        raise ValueError("--hf-revision must be a full 40-character commit SHA")
    spec = load_spec(spec_path)
    if not (config_dir / spec["base_eval_config"]).is_file():
        raise ValueError(
            f"base evaluation config not found: {config_dir / spec['base_eval_config']}"
        )
    if output_dir.exists():
        raise ValueError(f"output directory already exists: {output_dir}")
    run_ids = [
        _run_id(spec["name"], setting["name"], seed)
        for setting in spec["candidate_settings"]
        for seed in spec["seeds"]
    ]
    existing_adapters = [
        HARNESS_DIR / "runs" / "writers" / run_id
        for run_id in run_ids
        if (HARNESS_DIR / "runs" / "writers" / run_id).exists()
    ]
    if existing_adapters:
        raise ValueError(
            "writer output already exists; choose a new sweep name: "
            + ", ".join(str(path) for path in existing_adapters)
        )
    commit, dirty = _git_state()
    pair_hash = _sha256(preferences)
    settings_hash = _sha256(spec_path)
    created_configs: list[Path] = []
    runs: dict[str, dict[str, Any]] = {}
    try:
        for setting in spec["candidate_settings"]:
            for seed in spec["seeds"]:
                run_id = _run_id(spec["name"], setting["name"], seed)
                config_path = _eval_config(
                    config_dir=config_dir,
                    sweep_name=spec["name"],
                    run_id=run_id,
                    base_eval_config=spec["base_eval_config"],
                )
                created_configs.append(config_path)
                runs[run_id] = {
                    "run_id": run_id,
                    "status": "planned",
                    "setting": setting["name"],
                    "training": {
                        "base_model": "Qwen/Qwen2.5-Coder-7B-Instruct",
                        "hf_revision": hf_revision.lower(),
                        "epochs": spec["epochs"],
                        "learning_rate": spec["learning_rate"],
                        "beta": setting["beta"],
                        "nll_weight": setting["nll_weight"],
                        "seed": seed,
                    },
                    "data": {
                        "preferences": str(preferences),
                        "sha256": pair_hash,
                        "line_count": _line_count(preferences),
                    },
                    "source": {"git_commit": commit, "dirty_worktree": dirty},
                    "evaluation": {
                        "config": config_path.name,
                        "until": "initial",
                        "run_dir": str(
                            HARNESS_DIR / "runs" / "dpo_sweeps" / spec["name"] / "evaluation"
                        ),
                        "dev_tasks": [
                            "seed_vault",
                            "choir_sections",
                            "tram_lines",
                            "photo_albums",
                        ],
                    },
                    "jobs": {"train": None, "evaluation": None},
                    "outcome": None,
                }

        output_dir.mkdir(parents=True, exist_ok=False)
        for run in runs.values():
            per_run_dir = output_dir / "runs" / run["run_id"]
            per_run_dir.mkdir(parents=True)
            _atomic_json(per_run_dir / "manifest.json", run)
        manifest = {
            "schema_version": 1,
            "sweep": spec["name"],
            "spec": str(spec_path),
            "spec_sha256": settings_hash,
            "hf_revision": hf_revision.lower(),
            "selection_rule": {
                "eligible_if_mean_passing_dev_programs_at_least": math.ceil(
                    2 * spec["base_dev_passing_programs"] / 3
                ),
                "maximize": "mean passing copy-design programs across seeds",
                "evaluation_stage": "initial checks only; no editing outcomes",
            },
            "runs": runs,
        }
        _atomic_json(output_dir / "manifest.json", manifest)
        script = _shell_script(
            harness_dir=HARNESS_DIR,
            preferences=preferences,
            output_dir=output_dir,
            config_dir=config_dir,
            hf_revision=hf_revision.lower(),
            runs=list(runs.values()),
        )
        submit_path = output_dir / "submit.sh"
        submit_path.write_text(script, encoding="utf-8")
        submit_path.chmod(0o755)
        return output_dir
    except Exception:
        for config_path in created_configs:
            config_path.unlink(missing_ok=True)
        if output_dir.exists():
            for path in sorted(output_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            output_dir.rmdir()
        raise


def record_jobs(
    manifest_path: Path, run_id: str, train_job: str | None, eval_job: str | None
) -> None:
    """Record Slurm job IDs in the sweep and matching per-seed manifest."""
    if not train_job and not eval_job:
        raise ValueError("provide --train-job or --eval-job")
    path = manifest_path.resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    run = manifest["runs"].get(run_id)
    if run is None:
        raise ValueError(f"unknown run id {run_id!r}")
    if train_job:
        run["jobs"]["train"] = train_job
    if eval_job:
        run["jobs"]["evaluation"] = eval_job
    run["status"] = (
        "submitted"
        if run["jobs"]["train"] is not None and run["jobs"]["evaluation"] is not None
        else "partially_submitted"
    )
    _atomic_json(path, manifest)
    _atomic_json(path.parent / "runs" / run_id / "manifest.json", run)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = result.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare", help="create configs and per-seed manifests")
    prepare_parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    prepare_parser.add_argument("--preferences", type=Path, required=True)
    prepare_parser.add_argument(
        "--hf-revision", required=True, help="full 40-character model commit"
    )
    prepare_parser.add_argument(
        "--output-dir", type=Path, help="defaults to runs/dpo_sweeps/<sweep name>"
    )
    jobs_parser = commands.add_parser("record-jobs", help="record submitted Slurm job IDs")
    jobs_parser.add_argument("--manifest", type=Path, required=True)
    jobs_parser.add_argument("--run-id", required=True)
    jobs_parser.add_argument("--train-job")
    jobs_parser.add_argument("--eval-job")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "prepare":
            spec = load_spec(args.spec.resolve())
            output = args.output_dir or Path("runs/dpo_sweeps") / spec["name"]
            result = prepare(
                spec_path=args.spec,
                preferences=args.preferences,
                hf_revision=args.hf_revision,
                output_dir=output,
            )
            count = len(spec["candidate_settings"]) * len(spec["seeds"])
            print(f"Prepared {count} runs in {result}")
            print(f"Submit sequentially with: bash {result / 'submit.sh'}")
        else:
            record_jobs(args.manifest, args.run_id, args.train_job, args.eval_job)
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"dpo_sweep: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
