"""Foresight: showing the writer a task's later change requests.

A design hint (config.WriterConfig.design_hints) may contain the placeholder
$later_changes. For each task it is replaced by that task's change requests,
so the writer sees what will be asked of its program later. Candidates and
pairs still carry the plain prompt (collect._write_samples), so a writer
trained on them has to write the same way without seeing the future: a form
of context distillation (Askell et al., 2021; Snell et al., 2022).

A writer told about later changes may implement some of them early, and the
editor would then find those changes easy for the wrong reason. A program
implements a later change early, by this module's rule, when it defines a
public method, function, class or keyword parameter that only a later
change's request asks for: a name in the request's code spans that the
task's reference solution does not define. A change written under another
name is not caught.

The 7B writer does implement them early when told not to, so the fallback
asks for the final version first, with every change implemented, and then
deletes from that program what only the changes need, keeping the
structure that supports them. Two ways to delete:
- the writer does it (config.WriterConfig.prune_prompt): a second call
  with the program;
- prune_program does it (config.WriterConfig.prune_names): it deletes every
  function, method and class named only by a later change, and every
  one-line guard that raises one of those classes, by removing their lines,
  so the rest of the source stays as the writer wrote it.
Either way the rule above still drops a program if a name survives.

Usage:
    from harness.foresight import fill_hint, implements_later_change, prune_program
    sent = add_design_hint(prompt, fill_hint(hint, task))
    sent = add_design_hint(prompt, fill_hint(prune_prompt, task, program))
    first_version = prune_program(final_version, task)
    early = implements_later_change(program, task)
"""

import ast
import builtins
import keyword
import re

from .models.parser import render_program
from .registry import Program, Task

LATER_CHANGES = "$later_changes"
PROGRAM = "$program"

_CODE_SPAN = re.compile(r"`([^`\n]+)`")
_CALLED = re.compile(r"(\w+)\s*\(")
_CLASS = re.compile(r"\bclass\s+(\w+)")
_KEYWORD = re.compile(r"(?:^|[(,\s])(\w+)\s*=(?!=)")
_PYTHON = frozenset(dir(builtins)) | frozenset(keyword.kwlist)


def later_changes_text(task: Task) -> str:
    """The task's change requests, in manifest order, as numbered sections."""
    return "\n\n".join(
        f"### Change {n}\n\n{change.request.strip()}"
        for n, change in enumerate(task.changes.values(), start=1)
    )


def fill_hint(hint: str, task: Task, program: Program | None = None) -> str:
    """`hint` with $later_changes replaced by the task's change requests and,
    given a program, $program by its files in the writer's output format."""
    if LATER_CHANGES in hint:
        hint = hint.replace(LATER_CHANGES, later_changes_text(task))
    if program is not None and PROGRAM in hint:
        hint = hint.replace(PROGRAM, render_program(program).rstrip())
    return hint


def requested_names(request: str) -> set[str]:
    """Public names a request's code spans call, define as a class, or pass
    as a keyword, leaving out Python's own: `Ledger.freeze(account_id)` gives
    freeze, `class AccountFrozen(LedgerError)` gives AccountFrozen, `fee=0`
    gives fee, `sorted(x)` nothing."""
    names = set()
    for span in _CODE_SPAN.findall(request):
        for pattern in (_CALLED, _CLASS, _KEYWORD):
            names.update(pattern.findall(span))
    return {n for n in names if not n.startswith("_") and not n[0].isdigit()} - _PYTHON


def defined_names(program: Program) -> set[str]:
    """Every function, method and class a program defines, and every
    parameter name of its functions. Files that don't parse add nothing."""
    names = set()
    for path, data in program.items():
        if not path.endswith(".py"):
            continue
        try:
            tree = ast.parse(data.decode("utf-8"))
        except (SyntaxError, UnicodeDecodeError, ValueError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                names.add(node.name)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                args = node.args
                for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs):
                    names.add(arg.arg)
    return names


def later_change_names(task: Task) -> frozenset[str]:
    """Names only the task's later changes ask for: requested names that the
    reference solution of the initial specification does not define."""
    requested = set()
    for change in task.changes.values():
        requested |= requested_names(change.request)
    return frozenset(requested - defined_names(task.reference))


def implements_later_change(program: Program, task: Task) -> bool:
    """Whether the program defines a name only a later change asks for."""
    return bool(defined_names(program) & later_change_names(task))


def prune_program(program: Program, task: Task) -> Program:
    """The program without what only the task's later changes ask for: every
    function, method and class whose name only a later change asks for, and
    every `if` without an `else` whose whole body raises one of those
    classes. Their lines are removed and the rest is kept as written,
    including data the program keeps for the changes (a history, a set of
    sealed drawers). A body left empty gets `pass`. A file that doesn't
    parse, before or after, is left as it was."""
    names = later_change_names(task)
    return {
        path: _prune_source(data, names) if path.endswith(".py") else data
        for path, data in program.items()
    }


def _prune_source(data: bytes, names: frozenset[str]) -> bytes:
    try:
        source = data.decode("utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError, ValueError):
        return data
    lines = source.splitlines(keepends=True)
    replaced: dict[int, str] = {}  # 0-based line -> new text ("" deletes it)

    def first_line(stmt: ast.stmt) -> int:
        decorators = getattr(stmt, "decorator_list", [])
        return min([stmt.lineno, *(d.lineno for d in decorators)]) - 1

    def prune(body: list[ast.stmt]) -> None:
        doomed = [s for s in body if _only_for_later_changes(s, names)]
        for stmt in body:
            if stmt not in doomed:
                for child in _bodies(stmt, lines):
                    prune(child)
        for stmt in doomed:
            start, end = first_line(stmt), stmt.end_lineno
            # As many blank lines after it go as there are before it, so the
            # spacing between what is left stays as the writer had it.
            before = _blank_run(lines, start - 1, -1)
            end += min(before, _blank_run(lines, end, 1))
            for i in range(start, end):
                replaced[i] = ""
        if doomed and len(doomed) == len(body):
            indent = lines[doomed[0].lineno - 1][: doomed[0].col_offset]
            replaced[first_line(doomed[0])] = f"{indent}pass\n"

    prune(tree.body)
    if not replaced:
        return data
    pruned = "".join(replaced.get(i, line) for i, line in enumerate(lines))
    try:
        ast.parse(pruned)
    except SyntaxError:
        return data
    return pruned.encode("utf-8")


def _blank_run(lines: list[str], i: int, step: int) -> int:
    """How many blank lines there are from line i on, going by step."""
    n = 0
    while 0 <= i < len(lines) and not lines[i].strip():
        n += 1
        i += step
    return n


def _only_for_later_changes(stmt: ast.stmt, names: frozenset[str]) -> bool:
    if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return stmt.name in names
    if isinstance(stmt, ast.If) and not stmt.orelse and len(stmt.body) == 1:
        raised = stmt.body[0]
        if isinstance(raised, ast.Raise) and raised.exc is not None:
            exc = raised.exc.func if isinstance(raised.exc, ast.Call) else raised.exc
            return isinstance(exc, ast.Name) and exc.id in names
    return False


def _bodies(stmt: ast.stmt, lines: list[str]) -> list[list[ast.stmt]]:
    """The statement lists inside a compound statement. An `elif` is visited
    through its own bodies, so its line is never replaced by `pass`."""
    out = []
    for field in ("body", "orelse", "finalbody"):
        body = getattr(stmt, field, None)
        if not isinstance(body, list) or not body or not isinstance(body[0], ast.stmt):
            continue
        is_elif = (
            field == "orelse"
            and len(body) == 1
            and isinstance(body[0], ast.If)
            and lines[body[0].lineno - 1].lstrip().startswith("elif")
        )
        out.extend(_bodies(body[0], lines) if is_elif else [body])
    for handler in getattr(stmt, "handlers", []):
        out.append(handler.body)
    return out
