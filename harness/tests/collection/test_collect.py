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

from harness.collection.collect import (
    CollectStats,
    Keys,
    _distinct_programs,
    _run_trial,
    _write_samples,
)
from harness.collection.editor import Editor
from harness.config import BackendConfig, load_config
from harness.models.parser import render_program
from harness.registry import build_writer_prompt, load_tasks, load_template
from harness.registry import prompt_version as prompt_version_of
from harness.sandbox.evaluator import CategoryResult, StepEvaluation
from harness.store import CandidateKey, Store, TrialKey

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


def test_design_hints_change_what_is_sent_but_not_the_candidate_key(tmp_path):
    # Sample i is sent hint i mod 2; the empty hint sends the plain prompt.
    plain = dict(TASK.reference)
    hinted = {path: text + b"# kept as a log\n" for path, text in plain.items()}
    fixtures = tmp_path / "writer.yaml"
    rules = [
        {"match": "## Design\n\nKeep a log", "responses": [{"text": render_program(hinted)}]},
        {"match": "", "responses": [{"text": render_program(plain)}]},
    ]
    fixtures.write_text(yaml.safe_dump({"rules": rules}))
    backend = BackendConfig(
        kind="mock", model="m", temperature=0.7, max_tokens=99, fixtures=fixtures
    )
    writer = dataclasses.replace(
        CFG.writer, backend=backend, samples_per_task=4, design_hints=("", "Keep a log.")
    )
    cfg = dataclasses.replace(CFG, runs_dir=tmp_path / "runs", writer=writer)
    prompt = build_writer_prompt(TASK.writer_view(), load_template(cfg.writer.prompt_template))
    keys = Keys("w", "e", "s")
    with Store(cfg.runs_dir) as store:
        stats = CollectStats(run_id=store.start_run(cfg))
        _write_samples(cfg, store, TASK, prompt, keys, stats)
        pv = prompt_version_of(prompt)
        ids = [
            store.get_candidate(CandidateKey(TASK.id, pv, "w", i)).candidate_id for i in range(4)
        ]
        assert ids == [store.put_blob(plain), store.put_blob(hinted)] * 2
        assert _distinct_programs(store, TASK, prompt, keys) == ids[:2]
