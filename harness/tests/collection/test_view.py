"""Tests for harness.collection.view (the comment ablation): which comments
and docstrings go, that the rest of the code is untouched, that every task's
reference and planted-bug programs strip cleanly, that the editor sees the
stripped program for the whole sequence, and that the ablation gets its own
editor key.

Usage:
    uv run pytest tests/collection/test_view.py
"""

import dataclasses
from pathlib import Path

import pytest
import yaml

from harness.collection.collect import CollectStats, Keys, _run_trial
from harness.collection.editor import Editor
from harness.collection.view import make_view, strip_comments, strip_source
from harness.config import BackendConfig, load_config
from harness.evaluation.source import describe_source
from harness.models.parser import render_program
from harness.registry import load_tasks
from harness.store import Store, TrialKey, editor_cfg_hash, writer_cfg_hash

ROOT = Path(__file__).resolve().parents[2]
CFG = load_config(ROOT / "configs" / "mock.yaml")


def strip(text: str) -> str:
    return strip_source(text.encode()).decode()


def test_removes_whole_line_and_inline_comments_and_keeps_the_layout():
    source = (
        "# header\n"
        "import os  # for paths\n"
        "\n"
        "\n"
        "def f(x):\n"
        "    # explain\n"
        "    y = [1,  # one\n"
        "         2]\n"
        "    return x + y[0]   # done\n"
    )

    assert strip(source) == (
        "import os\n\n\ndef f(x):\n    y = [1,\n         2]\n    return x + y[0]\n"
    )


def test_removes_module_class_and_function_docstrings():
    source = (
        '"""Module doc."""\n'
        "import os\n"
        "\n"
        "class A:\n"
        '    """Class doc,\n'
        '    over two lines."""\n'
        "    x = 1\n"
        "\n"
        "    def m(self):\n"
        "        '''Method doc.'''\n"
        "        return 2\n"
        "\n"
        "async def g():\n"
        '    """Async doc."""  # and a comment\n'
        "    return 3\n"
    )

    assert strip(source) == (
        "import os\n"
        "\n"
        "class A:\n"
        "    x = 1\n"
        "\n"
        "    def m(self):\n"
        "        return 2\n"
        "\n"
        "async def g():\n"
        "    return 3\n"
    )


def test_a_body_with_only_a_docstring_gets_pass():
    source = (
        "class Error(Exception):\n"
        '    """Raised when it fails."""\n'
        "\n"
        "def f():\n"
        '    """Two\n'
        '    lines."""\n'
        "\n"
        'def g(): "one line"\n'
    )

    assert strip(source) == (
        "class Error(Exception):\n    pass\n\ndef f():\n    pass\n\ndef g(): pass\n"
    )


def test_a_docstring_sharing_its_line_with_code_becomes_pass():
    assert strip('def f():\n    "doc"; return 1\n') == "def f():\n    pass; return 1\n"


def test_keeps_strings_that_are_not_docstrings():
    source = (
        "def f():\n"
        "    x = 1\n"
        '    """not first, so not a docstring"""\n'
        '    return "# not a comment" + x\n'
        'NAME = """# also kept"""\n'
    )

    assert strip(source) == source


def test_handles_non_ascii_text_before_a_docstring_and_windows_line_endings():
    source = 'def café():  # é\r\n    """Doc é."""\r\n    return "é"\r\n'

    assert strip(source) == 'def café():\r\n    return "é"\r\n'


def test_is_idempotent_and_leaves_comment_free_code_unchanged():
    source = 'def f():\n    """Doc."""\n    return 1  # one\n'

    once = strip(source)
    assert strip(once) == once == "def f():\n    return 1\n"


def test_program_keeps_its_paths_and_leaves_other_files_and_broken_python_alone():
    program = {
        "app.py": b"x = 1  # one\n",
        "README.md": b"# Title\n",
        "broken.py": b"def f(:  # not Python\n",
    }

    assert strip_comments(program) == {
        "app.py": b"x = 1\n",
        "README.md": b"# Title\n",
        "broken.py": b"def f(:  # not Python\n",
    }


def test_view_none_returns_an_equal_copy():
    program = {"app.py": b"x = 1  # one\n"}
    shown = make_view("none")(program)

    assert shown == program and shown is not program
    with pytest.raises(ValueError, match="unknown view_transform"):
        make_view("strip_tests")


def _task_programs():
    for path in sorted((ROOT / "tasks").glob("*/*/*")):
        if path.parent.name in ("reference", "bugs") and path.is_dir():
            files = {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*.py")}
            if files:
                yield pytest.param(files, id=f"{path.parts[-3]}/{path.parent.name}/{path.name}")


@pytest.mark.parametrize("program", list(_task_programs()))
def test_every_task_program_strips_to_the_same_code_with_no_documentation(program):
    # strip_source raises if the syntax tree changed, beyond docstrings.
    shown = {path: strip_source(data) for path, data in program.items()}

    metrics = describe_source(shown)
    assert metrics["python_syntax_valid"] is True
    assert metrics["python_documentation_lines"] == 0


class _RecordingEditor(Editor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = []

    def edit(self, backend, program, step):
        self.inputs.append(dict(program))
        return super().edit(backend, program, step)


class _PassingEvaluator:
    def run_category(self, program, checks, category_name):
        from harness.sandbox.evaluator import CategoryResult

        return CategoryResult("x", "passed", 1, 1, (), "ok")

    def check_step(self, program, step):
        from harness.sandbox.evaluator import CategoryResult, StepEvaluation

        ok = CategoryResult("x", "passed", 1, 1, (), "ok")
        return StepEvaluation(ok, ok)


def _commented(program):
    return {path: b"# a note\n" + data for path, data in program.items()}


def test_editor_sees_the_stripped_program_and_keeps_its_own_comments(tmp_path):
    task = load_tasks(CFG.tasks)["record_store"]
    s1 = task.sequence("s1")
    # The editor's reply adds a comment of its own; step 2 must still see it.
    reply = render_program(_commented(dict(s1.steps[0].reference))) + "\nRUN_CHECKS\n"
    fixtures = tmp_path / "editor.yaml"
    fixtures.write_text(yaml.safe_dump({"rules": [{"match": "", "responses": [{"text": reply}]}]}))
    backend = BackendConfig(
        kind="mock", model="m", temperature=0.7, max_tokens=99, fixtures=fixtures
    )
    cfg = dataclasses.replace(
        CFG,
        runs_dir=tmp_path / "runs",
        editor=dataclasses.replace(CFG.editor, backend=backend, view_transform="strip_comments"),
    )
    evaluator = _PassingEvaluator()
    editor = _RecordingEditor(cfg.editor, evaluator)
    written = _commented(dict(task.reference))
    with Store(cfg.runs_dir) as store:
        stats = CollectStats(run_id=store.start_run(cfg))
        cid = store.put_blob(written)
        _run_trial(cfg, store, editor, evaluator, task, cid, s1, 0, Keys("w", "e", "s"), stats)
        steps = store.trial_steps(TrialKey(task.id, task.task_version, cid, "s1", 0, "e"))

    assert [c.status for c in steps] == ["success", "success"]
    first, second = editor.inputs
    assert first == strip_comments(written) != written
    assert all(b"# a note" in data for data in second.values())


def test_the_ablation_has_its_own_editor_key_and_shares_the_writer_key():
    ablation = dataclasses.replace(
        CFG, editor=dataclasses.replace(CFG.editor, view_transform="strip_comments")
    )

    assert editor_cfg_hash(ablation, "img") != editor_cfg_hash(CFG, "img")
    assert writer_cfg_hash(ablation) == writer_cfg_hash(CFG)
