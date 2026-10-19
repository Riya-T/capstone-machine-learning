"""Tests for harness.collection.editor with a scripted mock model: applying
edits, running checks, every budget limit, wasted turns, turn summaries,
infrastructure errors, cached replay, prompts that stay small and never
leak private tests or later changes. One docker test uses the real sandbox.

Usage:
    uv run pytest tests/collection/test_editor.py -rs
"""

import ast
import dataclasses
import itertools
import uuid
from pathlib import Path

import pytest
import yaml

from harness.collection.editor import (
    CUT_OFF,
    FIRST_FEEDBACK,
    NO_HISTORY,
    NOT_RERUN,
    UNCHANGED,
    Editor,
    _truncate_middle,
    diff_lines,
    normalize_output,
)
from harness.config import BackendConfig, ConfigError, load_config
from harness.models.backends import CachedBackend, InMemoryCallCache, MockBackend
from harness.models.parser import render_program
from harness.registry import load_tasks
from harness.sandbox.evaluator import CaseResult, CategoryResult, Evaluator
from harness.sandbox.runner import SandboxRunner

ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "mock.yaml")
TASK = load_tasks(CFG.tasks)["record_store"]
STEP = TASK.sequence("s1").steps[0]  # c_conflict; c_txn comes later
V0 = TASK.reference
CONFLICT = STEP.reference
FIRST = "Nothing yet: this is your first turn"


def editor_cfg(history_turns=3, **budget):
    values = {"max_turns": 6, "max_total_tokens": 100_000, "wall_time_s": 600.0, **budget}
    return dataclasses.replace(
        CFG.editor,
        budget=dataclasses.replace(CFG.editor.budget, **values),
        history_turns=history_turns,
    )


class StubEvaluator:
    """Stands in for the sandbox: records what it was asked to check and
    returns a fixed public-check result."""

    def __init__(self, status=None, passed=4, total=5, output="1 failed, 4 passed", cause=""):
        # By default the status follows the counts: all passing is "passed",
        # which makes the editor finish the step (auto-finish).
        status = status or ("passed" if total and passed == total else "failed")
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


def test_all_public_checks_passing_finishes_the_step(tmp_path):
    # The editor never sends DONE; a passing RUN_CHECKS ends the step anyway.
    evaluator = StubEvaluator(passed=5, total=5)
    backend = mock(tmp_path, [(FIRST, files_reply(CONFLICT)), ("", "RUN_CHECKS")])
    out = Editor(editor_cfg(), evaluator).edit(backend, V0, STEP)
    assert (out.status, out.reason, out.turns, out.program) == (
        "done",
        "checks_passed",
        1,
        CONFLICT,
    )
    assert len(evaluator.calls) == 1


def test_some_public_checks_failing_keeps_the_step_going(tmp_path):
    evaluator = StubEvaluator(passed=4, total=5)
    backend = mock(tmp_path, [("", "RUN_CHECKS")])
    out = Editor(editor_cfg(max_turns=3), evaluator).edit(backend, V0, STEP)
    assert (out.status, out.reason, out.turns) == ("budget_exhausted", "max_turns", 3)


def test_a_run_with_no_tests_is_not_a_pass(tmp_path):
    # 0 of 0 (e.g. the program fails to import) must never auto-finish.
    evaluator = StubEvaluator(status="failed", passed=0, total=0)
    backend = mock(tmp_path, [("", "RUN_CHECKS")])
    out = Editor(editor_cfg(max_turns=2), evaluator).edit(backend, V0, STEP)
    assert out.reason == "max_turns"


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
    # The code never changed, so only the first RUN_CHECKS ran the checks.
    assert (len(evaluator.calls), out.wasted_turns) == (1, 2)


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
    # Once the summaries hold history_turns lines, prompts differ only in
    # turn numbers: no transcript grows.
    settled = sizes[cfg.history_turns + 1 :]
    assert max(settled) - min(settled) <= 6
    assert "output truncated" in backend.prompts[-1]


def test_first_prompt_shows_the_current_files_and_allowlist(tmp_path):
    backend = mock(tmp_path, [("", "DONE")])
    Editor(editor_cfg(), StubEvaluator()).edit(backend, V0, STEP)
    (prompt,) = backend.prompts
    assert render_program(dict(V0)).strip() in prompt
    assert "You may change only these files: records.py" in prompt
    assert FIRST_FEEDBACK in prompt
    assert NO_HISTORY in prompt
    assert "You have 6 turns left" in prompt


# --- replies that change nothing ---------------------------------------------


def test_rechecking_unchanged_code_is_a_wasted_turn_and_shows_the_last_result(tmp_path):
    evaluator = StubEvaluator(passed=4, total=5)
    backend = mock(
        tmp_path,
        [
            (FIRST, files_reply(CONFLICT)),
            ("were not run again", "DONE"),
            ("Public checks: 4", files_reply(CONFLICT)),  # the same files again
        ],
    )
    out = Editor(editor_cfg(), evaluator).edit(backend, V0, STEP)
    assert (out.status, out.turns, out.wasted_turns) == ("done", 3, 1)
    assert len(evaluator.calls) == 1  # the unchanged code was not checked twice
    third = backend.prompts[2]
    assert NOT_RERUN.split(";")[0] in third
    assert "Public checks: 4 of 5 passed." in third  # the earlier result, repeated
    assert "Turn 2: sent records.py (unchanged), then RUN_CHECKS on unchanged code" in third


def test_changed_code_is_checked_again(tmp_path):
    evaluator = StubEvaluator(passed=4, total=5)
    tweaked = {"records.py": CONFLICT["records.py"] + b"\n# tweak\n"}
    backend = mock(
        tmp_path,
        [
            (FIRST, files_reply(CONFLICT)),
            ("Turn 2", "DONE"),
            ("Public checks: 4", files_reply(tweaked)),
        ],
    )
    out = Editor(editor_cfg(), evaluator).edit(backend, V0, STEP)
    assert [checked for checked, _, _ in evaluator.calls] == [CONFLICT, tweaked]
    assert out.wasted_turns == 0


def test_files_identical_to_the_current_ones_without_a_command_are_wasted(tmp_path):
    backend = mock(tmp_path, [(FIRST, files_reply(V0, "")), ("nothing changed", "DONE")])
    out = Editor(editor_cfg(), StubEvaluator()).edit(backend, V0, STEP)
    assert (out.status, out.turns, out.wasted_turns) == ("done", 2, 1)
    assert UNCHANGED in backend.prompts[1]


# --- turn summaries ---------------------------------------------------------


def test_prompts_summarize_the_latest_turns(tmp_path):
    evaluator = StubEvaluator(passed=4, total=5)
    backend = mock(
        tmp_path,
        [
            (FIRST, files_reply(CONFLICT, "")),
            ("Turn 3", "DONE"),
            ("Turn 2", "no command here"),
            ("Turn 1", "RUN_CHECKS"),
        ],
    )
    Editor(editor_cfg(), evaluator).edit(backend, V0, STEP)
    changed = diff_lines(V0, CONFLICT)
    fourth = backend.prompts[3]
    assert f"- Turn 1: sent records.py ({changed} lines changed); applied, no checks run" in fourth
    assert (
        "- Turn 2: sent no files, then RUN_CHECKS; public checks 4 of 5 passed; "
        "failing: test_records_survive_reopening"
    ) in fourth
    assert "- Turn 3: reply had no files and no command; nothing applied" in fourth


def test_history_turns_limits_the_summaries(tmp_path):
    rules = [(FIRST, "nope"), ("Turn 1", "still nope"), ("Turn 2", "DONE")]
    one = mock(tmp_path, rules)
    Editor(editor_cfg(history_turns=1), StubEvaluator()).edit(one, V0, STEP)
    assert "Turn 2" in one.prompts[2] and "Turn 1" not in one.prompts[2]

    none = mock(tmp_path, [(FIRST, "nope"), ("", "DONE")])
    Editor(editor_cfg(history_turns=0), StubEvaluator()).edit(none, V0, STEP)
    assert NO_HISTORY in none.prompts[1] and "Turn 1" not in none.prompts[1]


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


def test_check_output_is_normalized_so_replayed_prompts_match():
    a = "1 failed, 4 passed in 0.31s\nE  <records.RecordStore object at 0x7f3a9c2b1d90>"
    b = "1 failed, 4 passed in 12.07s (0:00:12)\nE  <records.RecordStore object at 0x7f00aa11bb22>"
    assert normalize_output(a) == normalize_output(b)
    assert (
        normalize_output(a)
        == "1 failed, 4 passed in <time>\nE  <records.RecordStore object at 0x...>"
    )


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
        backend = mock(tmp_path, [(FIRST, files_reply(CONFLICT))])
        out = Editor(editor_cfg(), evaluator).edit(backend, V0, STEP)
        # Every real public check (initial plus c_conflict's) passed on the
        # first RUN_CHECKS, so the step ended there without a DONE.
        assert (out.status, out.reason, out.turns) == ("done", "checks_passed", 1)
        assert out.program == CONFLICT
        # The edited program then passes the hidden tests for this step.
        assert evaluator.check_step(out.program, STEP).status == "success"
    finally:
        runner.sweep()
