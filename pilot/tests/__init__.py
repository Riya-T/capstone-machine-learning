"""Test suite for the pipeline package.

Usage (from pilot/):
    uv run pytest -rs                  # everything; Docker tests run if a daemon answers
    uv run pytest -m "not docker"      # skip the Docker tests
    uv run pytest --local-model        # also call the model server in configs/pilot_local.yaml
"""
