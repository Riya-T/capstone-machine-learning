"""Tests for harness.collection.view (the comment ablation): which comments
and docstrings go, that the rest of the code is untouched, that every task's
reference and planted-bug programs strip cleanly, that the editor sees the
stripped program for the whole sequence, and that the ablation gets its own
editor key. Then the readability control ("obscure"): which names change,
that a program does the same afterwards, and that every task program keeps
its public interface.

Usage:
    uv run pytest tests/collection/test_view.py
"""

import ast
import dataclasses
from pathlib import Path

import pytest
import yaml

from harness.collection.collect import CollectStats, Keys, _run_trial
from harness.collection.editor import Editor
from harness.collection.view import make_view, obscure, strip_comments, strip_source
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


_INVENTORY = (
    '"""Inventory."""\n'
    "import math\n"
    "\n"
    "LIMIT = 10  # most per item\n"
    "_UNIT = 2\n"
    "\n"
    "\n"
    "class Inventory:\n"
    "    def __init__(self, name):\n"
    "        self.name = name\n"
    "        self._counts = {}\n"
    "        self.history = []\n"
    "\n"
    "    def add(self, item, quantity=1):\n"
    '        """Add some."""\n'
    "        self._check(quantity)\n"
    "        total = self._counts.get(item, 0) + quantity\n"
    "        if total > LIMIT:\n"
    "            raise ValueError(f'too many {item}: {total}')\n"
    "        self._counts[item] = total\n"
    "        self.history.append((item, quantity))\n"
    "        return total\n"
    "\n"
    "    def _check(self, quantity):\n"
    "        if quantity <= 0:\n"
    "            raise ValueError('quantity must be positive')\n"
    "\n"
    "    def report(self):\n"
    "        lines = [f'{key}={count * _UNIT}' for key, count in sorted(self._counts.items())]\n"
    "        try:\n"
    "            first = lines[0]\n"
    "        except IndexError as error:\n"
    "            first = str(math.floor(0)) + type(error).__name__\n"
    "        return first, len(lines), len(self.history)\n"
)


def _use_inventory(code: str) -> list:
    namespace = {}
    exec(compile(code, "inventory.py", "exec"), namespace)
    inventory = namespace["Inventory"]("shop")
    out = [inventory.report(), inventory.add("b", 3), inventory.add(item="a", quantity=2)]
    out += [inventory.report(), inventory.name]
    for bad in ({"item": "a", "quantity": 0}, {"item": "a", "quantity": 9}):
        with pytest.raises(ValueError) as caught:
            inventory.add(**bad)
        out.append(str(caught.value))
    return out


def test_obscure_renames_private_names_attributes_and_locals_and_keeps_the_behavior():
    shown = obscure({"inventory.py": _INVENTORY.encode(), "notes.txt": b"_counts\n"})
    code = shown["inventory.py"].decode()

    gone = ["_counts", "_check", "_UNIT", "history", "total", "lines", "first", "error", "key"]
    assert [name for name in gone if name in code] == []
    assert "count" not in code.replace("ValueError", "")
    assert '"""' not in code and "#" not in code
    kept = ["Inventory", "add", "report", "self.name = name", "item", "quantity", "LIMIT", "math"]
    assert [name for name in kept if name not in code] == []
    assert shown["notes.txt"] == b"_counts\n"
    assert _use_inventory(code) == _use_inventory(_INVENTORY)


def test_obscure_renames_a_private_name_alike_in_every_file_and_keeps_imported_ones():
    program = {
        "store.py": b"def _load(path):\n    return path\n\ndef _keep(x):\n    return x\n",
        "app.py": b"import store\nfrom store import _keep\n\ndef run(p):\n"
        b"    return store._load(p) + _keep(p)\n",
    }

    shown = {path: data.decode() for path, data in obscure(program).items()}

    assert "_load" not in shown["store.py"] + shown["app.py"]
    assert "def _x1(path)" in shown["store.py"] and "store._x1(p)" in shown["app.py"]
    assert "def _keep(x)" in shown["store.py"] and "from store import _keep" in shown["app.py"]


def test_obscure_leaves_a_function_that_defines_a_class_its_names():
    source = (
        "def make(n):\n    size = n * 2\n    class Box:\n        width = size\n    return Box\n"
    )

    code = obscure({"m.py": source.encode()})["m.py"].decode()

    assert "size = n * 2" in code and "width = size" in code


def _signatures(program):
    """(path, qualified name, parameters) of every public function, class
    and method at module or class level."""
    out = set()
    for path, data in program.items():
        for node in ast.parse(data).body:
            members = node.body if isinstance(node, ast.ClassDef) else [node]
            prefix = f"{node.name}." if isinstance(node, ast.ClassDef) else ""
            if isinstance(node, ast.ClassDef):
                out.add((path, node.name, ()))
            for sub in members:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    params = tuple(a.arg for a in sub.args.args + sub.args.kwonlyargs)
                    out.add((path, prefix + sub.name, params))
    return {
        s
        for s in out
        if not any(part.startswith("_") and not part.startswith("__") for part in s[1].split("."))
    }


@pytest.mark.parametrize("program", list(_task_programs()))
def test_every_task_program_obscures_to_python_with_the_same_public_interface(program):
    shown = obscure(program)

    for data in shown.values():
        compile(data, "shown.py", "exec")
    assert _signatures(shown) == _signatures(program)
    assert describe_source(shown)["python_documentation_lines"] == 0


def test_the_readability_control_has_its_own_editor_key():
    control = dataclasses.replace(
        CFG, editor=dataclasses.replace(CFG.editor, view_transform="obscure")
    )

    assert make_view("obscure") is obscure
    assert editor_cfg_hash(control, "img") != editor_cfg_hash(CFG, "img")
    assert writer_cfg_hash(control) == writer_cfg_hash(CFG)


def test_obscure_renames_a_private_slot_and_keeps_attributes_a_library_type_or_module_has():
    source = (
        "import time\n"
        "\n"
        "class Clock:\n"
        '    __slots__ = ("_ticks", "label", "items", "time", "speed")\n'
        "\n"
        "    def __init__(self, label):\n"
        "        self._ticks = 0\n"
        "        self.label = label\n"
        "        self.items = {}\n"
        "        self.time = time.time()\n"
        "        self.speed = 1\n"
        "\n"
        "    def tick(self, other):\n"
        "        self._ticks += self.speed\n"
        "        return list(self.items.items()), other.speed\n"
    )

    code = obscure({"clock.py": source.encode()})["clock.py"].decode()

    assert "'_x1'" in code and "self._x1 += self.speed" in code
    assert "self.items = {}" in code and "self.items.items()" in code
    assert "self.time = time.time()" in code and "other.speed" in code


def test_obscure_renames_a_data_attribute_on_every_object_and_keeps_methods_and_fields():
    source = (
        "from dataclasses import dataclass\n"
        "\n"
        "@dataclass\n"
        "class Point:\n"
        "    x: int\n"
        "\n"
        "class Path:\n"
        "    unit = 'm'\n"
        "\n"
        "    def __init__(self):\n"
        "        self.points = []\n"
        "\n"
        "    @property\n"
        "    def length(self):\n"
        "        return len(self.points)\n"
        "\n"
        "    def join(self, other):\n"
        "        self.points = self.points + other.points + [Point(x=self.length)]\n"
        "        self.unit = other.unit\n"
        "        return self\n"
    )

    code = obscure({"path.py": source.encode()})["path.py"].decode()

    assert "points" not in code
    assert "self.a1 = self.a1 + other.a1 + [Point(x=self.length)]" in code
    assert "self.unit = other.unit" in code and "x: int" in code
    namespace = {}
    exec(compile(code, "path.py", "exec"), namespace)
    joined = namespace["Path"]().join(namespace["Path"]().join(namespace["Path"]()))
    assert joined.length == 2 and joined.unit == "m"
