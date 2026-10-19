"""Tests for the harness package.

Usage (from harness/):
    uv run pytest -rs                  # everything; Docker tests run if Docker is up
    uv run pytest -m "not docker"      # skip the Docker tests
"""
