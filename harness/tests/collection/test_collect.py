"""Tests for editing trials in harness.collection.collect, with a fake
evaluator instead of Docker: a step that finishes because all public checks
passed is still graded by the hidden tests.

Usage:
    uv run pytest tests/collection/test_collect.py
"""

import dataclasses
from pathlib import Path

import pytest
import yaml

from harness.collection.collect import CollectStats, Keys, _run_trial
from harness.collection.editor import Editor
from harness.config import BackendConfig, load_config
from harness.models.parser import render_program
from harness.registry import load_tasks
from harness.sandbox.evaluator import CategoryResult, StepEvaluation
from harness.store import Store, TrialKey

ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "mock.yaml")
TASK = load_tasks(CFG.tasks)["record_store"]
S1 = TASK.sequence("s1")


def category(status, passed, total):
    return CategoryResult("x", status, passed, total, (), "ok")


class StubEvaluator:
    """Public checks always pass (so the editor auto-finishes); the hidden
    step tests give whatever outcome the test chooses."""

    def __init__(self, hidden: str):
        self.hidden = hidden
        self.step_checks = 0

    def run_category(self, program, checks, category_name):
        return category("passed", 10, 10)

    def check_step(self, program, step):
        self.step_checks += 1
        if self.hidden == "success":
            return StepEvaluation(category("passed", 12, 12), category("passed", 40, 40))
        return StepEvaluation(category("failed", 3, 12), category("passed", 40, 40))


@pytest.mark.parametrize(("hidden", "status"), [("success", "success"), ("fail_new", "fail_new")])
def test_auto_finished_step_is_scored_by_the_hidden_tests(tmp_path, hidden, status):
    reply = render_program(dict(S1.steps[0].reference)) + "\nRUN_CHECKS\n"
    fixtures = tmp_path / "editor.yaml"
    fixtures.write_text(yaml.safe_dump({"rules": [{"match": "", "responses": [{"text": reply}]}]}))
    backend = BackendConfig(
        kind="mock", model="m", temperature=0.7, max_tokens=99, fixtures=fixtures
    )
    cfg = dataclasses.replace(
        CFG,
        runs_dir=tmp_path / "runs",
        editor=dataclasses.replace(CFG.editor, backend=backend),
        tasks=dataclasses.replace(CFG.tasks, max_sequences=1),
    )
    evaluator = StubEvaluator(hidden)
    keys = Keys("w", "e", "s")
    with Store(cfg.runs_dir) as store:
        stats = CollectStats(run_id=store.start_run(cfg))
        cid = store.put_blob(TASK.reference)
        editor = Editor(cfg.editor, evaluator)
        _run_trial(cfg, store, editor, evaluator, TASK, cid, S1, 0, keys, stats)
        steps = store.trial_steps(TrialKey(TASK.id, TASK.task_version, cid, "s1", 0, "e"))

    first = steps[0]
    assert (first.status, first.end_reason) == (status, "checks_passed")
    assert (first.new_pass, first.new_total) == ((12, 12) if hidden == "success" else (3, 12))
    # A success moves on to the next change; a failure ends the trial there.
    assert len(steps) == (2 if hidden == "success" else 1)
    assert evaluator.step_checks == len(steps)
