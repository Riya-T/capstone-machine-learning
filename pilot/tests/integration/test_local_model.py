"""Integration against the real model server in configs/pilot_local.yaml.

Skipped unless pytest is run with --local-model. Slow (a full writer answer
takes tens of seconds on the laptop) and dependent on the model, so these
check the pipeline's contract with a real model, not the model's quality.
"""

import time
from pathlib import Path

import pytest

from pipeline.backends import derive_seed, make_backend
from pipeline.config import load_config
from pipeline.parser import parse_program
from pipeline.registry import build_writer_prompt, load_task, load_template

PILOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.local_model


def test_local_writer_answer_follows_the_output_format():
    cfg = load_config(PILOT / "configs" / "pilot_local.yaml")
    task = load_task(cfg.tasks.dir / "record_store", cfg.tasks)
    prompt = build_writer_prompt(task.writer_view(), load_template(cfg.writer.prompt_template))
    backend = make_backend(cfg.writer.backend, derive_seed(cfg.seed, "local-model-test", 0))

    start = time.monotonic()
    answer = backend.generate(prompt)
    wall = time.monotonic() - start

    usage = backend.last_usage
    result = parse_program(answer, task.entry_files, usage.finish_reason)
    print(f"\nwall {wall:.1f}s, usage {usage}, parse {result.failure or 'ok'}")
    assert usage.finish_reason == "stop", "raise max_tokens or the server's context length"
    assert result.ok, f"{result.failure}\n--- answer ---\n{answer}"
