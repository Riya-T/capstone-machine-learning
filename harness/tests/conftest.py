"""Pytest setup: decides which marked tests run.

- docker tests run only when Docker is up.
- apptainer tests run only where the apptainer CLI exists.
- slow tests (full collection, task validation, stress tests) run only
  with --slow.

Usage (from harness/):
    uv run pytest -rs                   # -rs lists every skipped test and why
    uv run pytest --slow                # also the slow tests
"""

import functools
import shutil
import subprocess

import pytest

# tests/data holds test inputs, including a task whose own test files only
# run inside the sandbox; pytest must not collect them directly.
collect_ignore_glob = ["data/*"]


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", help="run tests marked slow")


@functools.cache
def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def apptainer_available() -> bool:
    return shutil.which("apptainer") is not None


def pytest_collection_modifyitems(config, items):
    run_slow = config.getoption("--slow")
    for item in items:
        if "slow" in item.keywords and not run_slow:
            item.add_marker(pytest.mark.skip(reason="slow; run with --slow"))
        if "docker" in item.keywords and not docker_available():
            item.add_marker(pytest.mark.skip(reason="no Docker daemon available"))
        if "apptainer" in item.keywords and not apptainer_available():
            item.add_marker(pytest.mark.skip(reason="no apptainer CLI available"))
