"""Test-run options and skips for the marked test layers.

- `docker` tests run only when a Docker daemon answers.
- `local_model` tests call a real model server, so they are slow and need
  hardware; they run only with `pytest --local-model`.

Usage (from pilot/):
    uv run pytest -rs                   # -rs lists every skipped test and why
    uv run pytest --local-model
"""

import functools
import shutil
import subprocess

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--local-model",
        action="store_true",
        help="run tests marked local_model against the server in configs/pilot_local.yaml",
    )


@functools.cache
def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def pytest_collection_modifyitems(config, items):
    run_local = config.getoption("--local-model")
    for item in items:
        if "local_model" in item.keywords and not run_local:
            item.add_marker(pytest.mark.skip(reason="needs --local-model"))
        if "docker" in item.keywords and not docker_available():
            item.add_marker(pytest.mark.skip(reason="no Docker daemon available"))
