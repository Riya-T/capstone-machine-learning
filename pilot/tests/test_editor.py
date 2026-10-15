"""Unit tests for pipeline.editor, the provisional editor turn loop, with the
deterministic mock backend: applying edits, running public checks, every
budget limit, wasted turns (bad format, files outside the allowlist,
cut-off replies), infrastructure errors, replay from the call cache, that no
prompt ever contains private tests or later changes, and that prompts stay
bounded over many turns. Most tests use a stub evaluator; the `docker` test
runs the real sandbox on record_store.

Usage:
    uv run pytest tests/test_editor.py -rs
"""

import ast
import dataclasses
import itertools
import uuid
from pathlib import Path

import pytest
import yaml

from pipeline.backends import CachedBackend, InMemoryCallCache, MockBackend
from pipeline.config import BackendConfig, ConfigError, load_config
from pipeline.editor import (
    CUT_OFF,
    FIRST_FEEDBACK,
    Editor,
    _truncate_middle,
    diff_lines,
)
from pipeline.evaluator import CaseResult, CategoryResult, Evaluator
from pipeline.parser import render_program
from pipeline.registry import load_tasks
from pipeline.runner import SandboxRunner

PILOT = Path(__file__).resolve().parents[1]
CFG = load_config(PILOT / "configs" / "pilot_mock.yaml")
TASK = load_tasks(CFG.tasks)["record_store"]
STEP = TASK.sequence("s1").steps[0]  # c_conflict; c_txn comes later
V0 = TASK.reference
CONFLICT = STEP.reference
FIRST = "Nothing yet: this is your first turn"


def editor_cfg(**budget):
    values = {"max_turns": 6, "max_total_tokens": 100_000, "wall_time_s": 600.0, **budget}
    return dataclasses.replace(CFG.editor, budget=dataclasses.replace(CFG.editor.budget, **values))


class StubEvaluator:
    """Stands in for the sandbox: records what it was asked to check and
    returns a fixed public-check result."""

    def __init__(self, status="passed", passed=4, total=5, output="1 failed, 4 passed", cause=""):
        failing = (CaseResult("public/test_public.py::test_records_survive_reopening", "failed"),)
        self.result = CategoryResult(
            "public", status, passed, total, failing if passed < total else (), "ok",
            detail="sandbox down" if status == "infra_error" else "",
            infra_cause=cause, output=output,
        )  # fmt: skip
        self.calls = []

    def run_category(self, program, checks, category):
        self.calls.append((dict(program), checks, category))
        return self.result


def mock(tmp_path, rules, seed=0) -> MockBackend:
    """A MockBackend from (regex, reply) rules; a reply may be (text,
    finish_reason)."""
    fixture = {"rules": []}
    for pattern, replies in rules:
        responses = []
        for reply in replies if isinstance(replies, list) else [replies]:
            text, reason = reply if isinstance(reply, tuple) else (reply, "stop")
            responses.append({"text": text, "finish_reason": reason})
        fixture["rules"].append({"match": pattern, "responses": responses})
    path = tmp_path / f"editor-{uuid.uuid4().hex[:6]}.yaml"
    path.write_text(yaml.safe_dump(fixture, sort_keys=False))
    cfg = BackendConfig(kind="mock", model="m", temperature=0.7, max_tokens=3072, fixtures=path)
    return MockBackend(cfg, seed)


def files_reply(program, command="RUN_CHECKS") -> str:
    return f"Here is the change.\n\n{render_program(dict(program))}\n{command}\n"


# --- the happy path ---------------------------------------------------------


def test_applies_edits_runs_public_checks_and_finishes(tmp_path):
    evaluator = StubEvaluator()
    backend = mock(tmp_path, [(FIRST, files_reply(CONFLICT)), ("Public checks:", "DONE")])
    out = Editor(editor_cfg(), evaluator).edit(backend, V0, STEP)

    assert (out.status, out.reason) == ("done", "done")
    assert out.program == CONFLICT
    assert (out.turns, out.wasted_turns, out.model_calls) == (2, 0, 2)
    assert out.tokens_in > 0 and out.tokens_out > 0
    assert out.diff_lines == diff_lines(V0, CONFLICT) > 0
    # One check run, on the edited program, with the cumulative public checks.
    ((checked, checks, category),) = evaluator.calls
    assert checked == CONFLICT and category == "public"
    assert checks == STEP.tests.public
    assert [f.path for f in checks.files] == [
        "public/test_public.py",
        "changes/c_conflict/public/test_conflict_public.py",
    ]
    # The second prompt shows the check results.
    assert "Public checks: 4 of 5 passed." in backend.prompts[1]
    assert "test_records_survive_reopening: failed" in backend.prompts[1]


def test_files_with_done_are_applied_then_the_step_ends_without_checks(tmp_path):
    evaluator = StubEvaluator()
    backend = mock(tmp_path, [(FIRST, files_reply(CONFLICT, "DONE"))])
    out = Editor(editor_cfg(), evaluator).edit(backend, V0, STEP)
    assert (out.status, out.program, out.turns) == ("done", CONFLICT, 1)
    assert evaluator.calls == []


def test_files_without_a_command_are_applied_and_the_loop_continues(tmp_path):
    backend = mock(tmp_path, [(FIRST, files_reply(CONFLICT, "")), ("were applied", "DONE")])
    out = Editor(editor_cfg(), StubEvaluator()).edit(backend, V0, STEP)
    assert (out.status, out.program, out.turns, out.wasted_turns) == ("done", CONFLICT, 2, 0)


# --- wasted turns -----------------------------------------------------------


@pytest.mark.parametrize(
    ("bad_reply", "feedback"),
    [
        # A file outside the original program's allowlist.
        (
            "```python file=evil.py\nimport os\n```\nDONE\n",
            "'evil.py' is not one of ['records.py']",
        ),
        ("```python file=../records.py\nx = 1\n```\nDONE\n", "unsafe or non-normalized path"),
        ("```python\nx = 1\n```\nDONE\n", "block has no file= label"),
        ("```python file=records.py\nx = 1\n", "block is never closed"),
        ("I would add a version field to each record.", "no files and no command"),
        # Commands count only alone on a line, outside code blocks.
        ("I am DONE now.", "no files and no command"),
        ("```python file=records.py\nDONE\n```\n", None),  # a file, not a command
    ],
)
def test_bad_replies_are_wasted_turns_and_apply_nothing(tmp_path, bad_reply, feedback):
    backend = mock(tmp_path, [(FIRST, bad_reply), ("", "DONE")])
    out = Editor(editor_cfg(), StubEvaluator()).edit(backend, V0, STEP)
    assert out.status == "done"
    if feedback is None:
        # The block is a valid one-line file; applied, then the editor continues.
        assert out.program == {"records.py": b"DONE\n"}
        return
    assert out.program == V0  # nothing applied, and no extra file appeared
    assert (out.turns, out.wasted_turns) == (2, 1)
    assert feedback in backend.prompts[1]


def test_cut_off_reply_is_never_applied(tmp_path):
    # Looks complete, but the backend says it stopped at max_tokens.
    backend = mock(tmp_path, [(FIRST, (files_reply(CONFLICT, "DONE"), "length")), ("", "DONE")])
    out = Editor(editor_cfg(), StubEvaluator()).edit(backend, V0, STEP)
    assert (out.status, out.program, out.wasted_turns) == ("done", V0, 1)
    assert CUT_OFF in backend.prompts[1]


# --- budgets ----------------------------------------------------------------


def test_max_turns_ends_the_step_as_budget_exhausted(tmp_path):
    evaluator = StubEvaluator()
    backend = mock(tmp_path, [("", "RUN_CHECKS")])
    out = Editor(editor_cfg(max_turns=3), evaluator).edit(backend, V0, STEP)
    assert (out.status, out.reason, out.turns) == ("budget_exhausted", "max_turns", 3)
    assert len(evaluator.calls) == 3


def test_max_total_tokens_ends_the_step(tmp_path):
    backend = mock(tmp_path, [("", "RUN_CHECKS")])
    out = Editor(editor_cfg(max_total_tokens=50), StubEvaluator()).edit(backend, V0, STEP)
    # The first prompt alone is far over 50 (mock) tokens; the reply is
    # processed, then the budget stops the next call.
    assert (out.status, out.reason, out.turns) == ("budget_exhausted", "max_total_tokens", 1)
    assert out.tokens_in > 50


def test_wall_time_ends_the_step(tmp_path):
    ticks = itertools.count(start=0, step=100)  # every clock reading is 100 s later
    editor = Editor(editor_cfg(wall_time_s=250), StubEvaluator(), clock=lambda: next(ticks))
    out = editor.edit(mock(tmp_path, [("", "RUN_CHECKS")]), V0, STEP)
    # Readings: start 0; before call 1: 100; before call 2: 200; before
    # call 3: 300 >= 250, so the step stops after two turns.
    assert (out.status, out.reason, out.turns) == ("budget_exhausted", "wall_time", 2)


def test_program_too_large_for_the_prompt_is_budget_exhausted(tmp_path):
    huge = {"records.py": b"x = 1\n" * 5000}
    backend = mock(tmp_path, [("", "DONE")])
    out = Editor(editor_cfg(), StubEvaluator()).edit(backend, huge, STEP)
    assert (out.status, out.reason, out.model_calls) == ("budget_exhausted", "prompt_too_large", 0)
    assert backend.prompts == []


# --- infrastructure ---------------------------------------------------------


def test_backend_failure_is_an_infra_error(tmp_path):
    backend = mock(tmp_path, [("this never matches", "DONE")])  # the mock raises BackendError
    out = Editor(editor_cfg(), StubEvaluator()).edit(backend, V0, STEP)
    assert (out.status, out.infra_cause) == ("infra_error", "backend_error")


def test_sandbox_failure_during_checks_is_an_infra_error(tmp_path):
    evaluator = StubEvaluator(status="infra_error", passed=0, total=0, cause="docker_create")
    backend = mock(tmp_path, [(FIRST, files_reply(CONFLICT))])
    out = Editor(editor_cfg(), evaluator).edit(backend, V0, STEP)
    assert (out.status, out.infra_cause, out.reason) == (
        "infra_error",
        "docker_create",
        "sandbox down",
    )
    assert out.program == CONFLICT  # what was applied before the failure is kept


# --- what the editor sees ---------------------------------------------------


def _test_names(source: bytes) -> set[str]:
    """Test function names (fixtures such as `store` are ordinary words)."""
    tree = ast.parse(source)
    return {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
    }


def test_no_prompt_contains_private_tests_or_later_changes(tmp_path):
    rules = [
        (FIRST, files_reply(V0, "RUN_CHECKS")),
        ("Public checks: 4", "```python file=nope.py\nx\n```\nRUN_CHECKS"),
        ("is not one of", ("cut", "length")),
        ("cut off", "DONE"),
    ]
    backend = mock(tmp_path, rules)
    Editor(editor_cfg(), StubEvaluator()).edit(backend, V0, STEP)
    assert len(backend.prompts) == 4

    private = [*TASK.private_tests, *STEP.change.new_feature_tests]
    later = [c for c in TASK.changes.values() if c.id != STEP.change.id]
    for prompt in backend.prompts:
        assert STEP.change.request.strip() in prompt  # the current change, every turn
        for f in private:
            assert f.path not in prompt
            for name in _test_names(f.content):
                assert name not in prompt, name
        for change in later:
            assert change.id not in prompt
            for line in change.request.splitlines():
                # Boilerplate shared with the current request ("All existing
                # behavior must keep working.") is not a leak.
                if len(line.strip()) >= 25 and line.strip() not in STEP.change.request:
                    assert line.strip() not in prompt
            for f in change.public_checks + change.new_feature_tests:
                assert f.path not in prompt


def test_prompt_size_stays_bounded_over_many_turns(tmp_path):
    flood = "E" * 200_000  # far more check output than the prompt can hold
    cfg = editor_cfg(max_turns=40)
    backend = mock(tmp_path, [("", "RUN_CHECKS")])
    out = Editor(cfg, StubEvaluator(output=flood)).edit(backend, V0, STEP)
    assert out.turns == 40
    sizes = [len(p) for p in backend.prompts]
    assert max(sizes) <= cfg.max_prompt_chars
    # Turns 2..40 differ only in the turns-left number: no transcript grows.
    assert max(sizes[1:]) - min(sizes[1:]) <= 2
    assert "output truncated" in backend.prompts[-1]


def test_first_prompt_shows_the_current_files_and_allowlist(tmp_path):
    backend = mock(tmp_path, [("", "DONE")])
    Editor(editor_cfg(), StubEvaluator()).edit(backend, V0, STEP)
    (prompt,) = backend.prompts
    assert render_program(dict(V0)).strip() in prompt
    assert "You may change only these files: records.py" in prompt
    assert FIRST_FEEDBACK in prompt
    assert "You have 6 turns left" in prompt


# --- replay -----------------------------------------------------------------


def test_rerunning_a_step_replays_every_turn_without_model_calls(tmp_path):
    rules = [(FIRST, files_reply(CONFLICT)), ("Public checks:", "DONE")]
    cache = InMemoryCallCache()
    editor = Editor(editor_cfg(), StubEvaluator())
    first = editor.edit(CachedBackend(mock(tmp_path, rules), cache), V0, STEP)

    replay_mock = mock(tmp_path, rules)
    replayed = CachedBackend(replay_mock, cache)
    second = editor.edit(replayed, V0, STEP)
    assert dataclasses.replace(second, wall_s=0) == dataclasses.replace(first, wall_s=0)
    assert replayed.model_calls == 0 and replay_mock.prompts == []


# --- helpers and configuration ----------------------------------------------


def test_diff_lines_counts_added_and_removed_lines():
    before = {"a.py": b"one\ntwo\nthree\n"}
    after = {"a.py": b"one\n2\nthree\nfour\n"}
    assert diff_lines(before, after) == 3  # -two, +2, +four
    assert diff_lines(before, before) == 0


def test_truncate_middle_keeps_both_ends_within_the_limit():
    text = "START" + "x" * 1000 + "END"
    cut = _truncate_middle(text, 100)
    assert len(cut) <= 100 and cut.startswith("START") and cut.endswith("END")
    assert _truncate_middle("short", 100) == "short"


def test_editor_template_must_use_exactly_its_placeholders(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("$request $files $feedback")
    cfg = dataclasses.replace(CFG.editor, prompt_template=bad)
    with pytest.raises(ConfigError, match="placeholders must be exactly"):
        Editor(cfg, StubEvaluator())


# --- with the real sandbox --------------------------------------------------


@pytest.mark.docker
def test_editing_record_store_with_real_public_checks(tmp_path):
    runner = SandboxRunner(CFG.sandbox, owner=f"pytest-editor-{uuid.uuid4().hex[:8]}")
    try:
        evaluator = Evaluator(runner, workers=2)
        backend = mock(tmp_path, [(FIRST, files_reply(CONFLICT)), ("Public checks:", "DONE")])
        out = Editor(editor_cfg(), evaluator).edit(backend, V0, STEP)
        assert (out.status, out.program) == ("done", CONFLICT)
        assert "Public checks: 5 of 5 passed." in backend.prompts[1]
        # The edited program then passes the hidden tests for this step.
        assert evaluator.check_step(out.program, STEP).status == "success"
    finally:
        runner.sweep()
