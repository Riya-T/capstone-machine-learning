"""Test helpers for building small valid config files.

Usage:
    from .helpers import minimal, write
    path = write(tmp_path, minimal())   # a config file plus the files it names
"""

from pathlib import Path

import yaml


def minimal() -> dict:
    """A small valid config; tests copy and mutate it."""
    backend = {
        "kind": "mock",
        "model": "m",
        "temperature": 0.5,
        "max_tokens": 100,
        "fixtures": "mock.yaml",
    }
    return {
        "schema_version": 1,
        "name": "t",
        "seed": 1,
        "allow_dirty": False,
        "runs_dir": "runs",
        "tasks": {
            "dir": "tasks",
            "include": ["a"],
            "sequence_length": {"train": 2, "dev": 2, "eval": 3},
            "sequences_per_task": 2,
        },
        "writer": {
            "backend": dict(backend),
            "samples_per_task": 2,
            "prompt_template": "writer.md",
        },
        "editor": {
            "backend": dict(backend),
            "scaffold": "turn_loop",
            "budget": {"max_turns": 2, "max_total_tokens": 1000, "wall_time_s": 10},
            "reps": 3,
            "prompt_template": "editor.md",
            "max_prompt_chars": 16000,
            "max_check_output_chars": 2000,
        },
        "sandbox": {
            "image": "img",
            "timeout_s": 5,
            "memory": "256m",
            "cpus": 1,
            "pids_limit": 64,
            "tmpfs_size": "16m",
            "output_cap_bytes": 1000,
        },
        "scorer": {"rule": "weak_dominance", "pairing_mode": "best_vs_worst"},
    }


def write(directory: Path, data: dict, name: str = "exp.yaml") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "tasks").mkdir(exist_ok=True)
    (directory / "writer.md").write_text("$entry_files $spec $public_checks")
    (directory / "editor.md").write_text(
        "$request $files $feedback $history $allowed_files $turns_left"
    )
    (directory / "mock.yaml").write_text("rules: []\n")
    path = directory / name
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path
