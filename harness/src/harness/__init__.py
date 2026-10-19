"""The harness: builds preference data for training a code writer, by testing
how easily an editor model can change the writer's programs later.

Shared modules: config (settings), registry (tasks), store (results).
Subpackages: models (model calls), sandbox (running code), collection
(editing trials and scoring). The README at the repository root explains
how it all fits together.

Usage (from harness/):
    uv run python -m harness collect --config configs/mock.yaml
    from harness.config import load_config
"""
