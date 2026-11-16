"""Outline view and function-level edits (editor.edit_format: functions).

The editor first sees each file as an outline: imports, module-level
statements and class attributes in full, but every function and method as
its signature and docstring with the body hidden. It opens the ones it
needs with a command on a line of its own,

    SHOW Ledger.withdraw, Ledger._require

and changes the program by sending complete definitions of the functions,
methods and classes it changes or adds, in fenced python blocks:

    ```python file=ledger.py
    class Ledger:
        def withdraw(self, account_id, amount):
            ...complete new body...
    ```

A top-level def replaces the function of that name, or is added at the end
of the file. A class block whose class exists replaces or adds the methods
and the class-level assignments it holds and leaves the class's other
members as they are; a new class is added after the last top-level
statement that defines a name its bases or decorators use, or after the
imports. Imports are added when missing, after the existing ones, and an
assignment to a name replaces the assignment to that name or is added after
the imports (at the top of the class, for a class attribute). Nothing is
ever removed. A sent function whose body is only `...` (the outline's
placeholder, copied back) is skipped, never applied: it would wipe out code.
So is one that would replace a function whose body is hidden and that the
editor has not opened: the 14B editor otherwise rewrites whole classes from
the outline, guessing every hidden body.
Other statements (an if block, a bare expression) are skipped too, and the
rest of the block still applies. A method sent without its class (a
top-level def whose first parameter is self) goes to the one class that has
a method of that name, or to the only class.

Large programs are where maintainability shows: no maintainer reads all of
them before each change. A 50-line program fits in the editor's prompt, so
with whole files the editor rewrites whatever it likes and the program's
design cannot matter (results/diagnostics.md). Here the editor has to find
its way by names and docstrings and change the program within its
structure.

Usage:
    text = outline_program(files, opened)               # the prompt's program
    names = resolve_names(files, ["withdraw"])          # (found, unknown)
    files, changed, skipped = apply_blocks(files, blocks, allowed)  # FunctionEditError
"""

from __future__ import annotations

import ast
import contextlib
import re
import textwrap
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

# Part of the editor key when edit_format is functions (store.py): raise it
# whenever a change here alters what the editor sees or which edits apply.
# 2: a sent def that replaces a hidden one the editor never opened is skipped.
# 3: SHOW lines count inside code blocks too, and are taken out of the code.
# 4: an indented block is dedented; backslashes in SHOW names are dropped.
PROTOCOL_VERSION = 4

HIDDEN = "...  # body hidden (SHOW {name})"
_SHOW = re.compile(r"^\**SHOW\**\b[:\s]*(.*)$")
_NOT_OPENED = "{name} (not opened yet: send SHOW {name}, then change it)"
_ONLY = "only functions, methods, classes, imports and assignments to a name can be sent"


class FunctionEditError(ValueError):
    """A reply block that can't be applied; the message is for the editor."""


@dataclass(frozen=True)
class _Def:
    qualname: str  # "func" or "Class.method"
    start: int  # first line, decorators included (0-based)
    end: int  # one past the last line
    keep: int  # lines before this are shown when hidden: signature and docstring
    indent: str  # the body's indentation


def function_defs(source: str) -> list[_Def]:
    """Top-level functions and the methods of top-level classes, in order."""
    out = []
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(_def(node, ""))
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.append(_def(sub, node.name + "."))
    return out


def _def(node: ast.FunctionDef | ast.AsyncFunctionDef, prefix: str) -> _Def:
    first = node.body[0]
    keep = first.end_lineno if _is_docstring(first) else first.lineno - 1
    if first.lineno == node.lineno or keep >= node.end_lineno:
        keep = node.end_lineno  # a one-line def, or only a docstring: nothing to hide
    return _Def(
        qualname=prefix + node.name,
        start=_start(node) - 1,
        end=node.end_lineno,
        keep=keep,
        indent=" " * first.col_offset,
    )


def outline_program(files: dict[str, bytes], opened: Iterable[str]) -> str:
    """The program as the editor sees it: fenced blocks like render_program,
    with the bodies of functions not in `opened` replaced by a placeholder.
    A file that doesn't parse is shown whole."""
    opened = set(opened)
    parts = []
    for path in sorted(files):
        source = files[path].decode("utf-8")
        try:
            defs = function_defs(source)
        except SyntaxError:
            defs = []
        lines = source.split("\n")
        for d in sorted(defs, key=lambda d: -d.start):  # bottom up keeps line numbers valid
            if d.qualname in opened or d.keep >= d.end:
                continue
            lines[d.keep : d.end] = [d.indent + HIDDEN.format(name=d.qualname)]
        text = "\n".join(lines)
        if text and not text.endswith("\n"):
            text += "\n"
        parts.append(f"```python file={path}\n{text}```\n")
    return "\n".join(parts)


def all_names(files: dict[str, bytes]) -> list[str]:
    names = []
    for path in sorted(files):
        with contextlib.suppress(SyntaxError):
            names += [d.qualname for d in function_defs(files[path].decode("utf-8"))]
    return names


def show_requests(lines: Sequence[str]) -> list[str]:
    """The names asked for on SHOW lines, as written (backticks, "self." and
    "()" dropped). The 14B editor often puts its SHOW line in a code block,
    so pass every line of the reply."""
    names = []
    for line in lines:
        match = _SHOW.match(line.strip())
        if match:
            for raw in re.split(r"[,\s]+", match.group(1)):
                name = raw.replace("\\", "")  # markdown escapes: Ledger.\_\_init\_\_
                name = name.strip("`'\"*:;.").removeprefix("self.").removesuffix("()")
                if name:
                    names.append(name)
    return names


def without_show_lines(code: str) -> str:
    """A code block with its SHOW lines taken out ("" if nothing else)."""
    kept = [line for line in code.split("\n") if not _SHOW.match(line.strip())]
    return "\n".join(kept) if any(line.strip() for line in kept) else ""


def resolve_names(files: dict[str, bytes], requested: Sequence[str]) -> tuple[list[str], list[str]]:
    """(qualified names found, names not found). A bare method name counts
    when exactly one class has it; a file prefix ("ledger.py:" or "ledger.")
    is ignored."""
    names = all_names(files)
    found, unknown = [], []
    for name in requested:
        bare = re.sub(r"^\w+\.py[:.]", "", name)
        if bare in names:
            match = bare
        else:
            tails = [n for n in names if n.rsplit(".", 1)[-1] == bare.rsplit(".", 1)[-1]]
            match = tails[0] if len(tails) == 1 else None
        if match is None:
            unknown.append(name)
        elif match not in found:
            found.append(match)
    return found, unknown


def apply_blocks(
    files: dict[str, bytes],
    blocks: Sequence[tuple[str, str]],
    allowed: Sequence[str],
    opened: Iterable[str] | None = None,
) -> tuple[dict[str, bytes], list[str], list[str]]:
    """Apply (info string, code) blocks: (new files, qualified names changed
    or added, what was skipped and why: a def whose body was only `...`, a
    def replacing a hidden one not in `opened` (None: no such check), or a
    statement other than a def, class, import or assignment to a name).
    Raises FunctionEditError, with nothing applied, for a block that names a
    file it may not change or isn't valid Python."""
    opened = None if opened is None else set(opened)
    out = dict(files)
    changed: list[str] = []
    skipped: list[str] = []
    for info, code in blocks:
        path = _block_path(info, allowed)
        source = out.get(path, b"").decode("utf-8")
        source, names, empty = _apply(source, code, opened)
        out[path] = source.encode("utf-8")
        changed += [n for n in names if n not in changed]
        skipped += empty
    return out, changed, skipped


def _block_path(info: str, allowed: Sequence[str]) -> str:
    match = re.search(r"\bfile=(\S+)", info)
    if match:
        path = match.group(1)
        if path not in allowed:
            raise FunctionEditError(f"you may not change {path!r}; you may change {list(allowed)}")
        return path
    if len(allowed) == 1:
        return allowed[0]
    raise FunctionEditError("a code block must name its file: ```python file=<path>")


def _apply(source: str, code: str, opened: set[str] | None) -> tuple[str, list[str], list[str]]:
    code = textwrap.dedent(code)  # methods sent without their class, still indented
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise FunctionEditError(
            f"a code block is not valid Python (line {exc.lineno}: {exc.msg})"
        ) from None
    code_lines = code.split("\n")
    changed, skipped = [], []
    for node in tree.body:
        if _is_docstring(node) or isinstance(node, ast.Pass):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            owner = _method_owner(source, node)
            name = f"{owner}.{node.name}" if owner else node.name
            if _only_ellipsis(node):
                skipped.append(f"{name} (its body was only `...`)")
                continue
            if _unseen(source, name, opened):
                skipped.append(_NOT_OPENED.format(name=name))
                continue
            source = _put_member(source, owner, node, code_lines)
            changed.append(name)
        elif isinstance(node, ast.ClassDef):
            source, names, empty = _put_class(source, node, code_lines, opened)
            changed += names
            skipped += empty
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            source = _put_import(source, _segment(node, code_lines))
        elif _assigned_name(node):
            source = _put_member(source, None, node, code_lines)
        else:
            skipped.append(
                f"the {type(node).__name__} statement at line {node.lineno} (" + _ONLY + ")"
            )
    ast.parse(source)  # every insertion keeps the file valid; check anyway
    return source, changed, skipped


def _unseen(source: str, name: str, opened: set[str] | None) -> bool:
    """Whether `name` is a function whose body the outline hides and that
    the editor has not opened (one-line and docstring-only defs are shown
    whole, so they count as seen)."""
    if opened is None or name in opened:
        return False
    return any(d.qualname == name and d.keep < d.end for d in function_defs(source))


def _method_owner(source: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """The class a top-level def sent without its class belongs to: when its
    first parameter is self or cls, no top-level function has its name, and
    exactly one class has a method of that name (or there is one class)."""
    args = node.args.posonlyargs + node.args.args
    if not args or args[0].arg not in ("self", "cls"):
        return None
    tree = ast.parse(source)
    if any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == node.name
        for n in tree.body
    ):
        return None
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    having = [
        c.name
        for c in classes
        if any(
            isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == node.name
            for m in c.body
        )
    ]
    if len(having) == 1:
        return having[0]
    plain = [c.name for c in classes if not _is_exception(c)]
    return plain[0] if not having and len(plain) == 1 else None


def _is_exception(node: ast.ClassDef) -> bool:
    return any(
        isinstance(b, ast.Name) and (b.id.endswith(("Error", "Exception")) or b.id == "Warning")
        for b in node.bases
    )


def _put_class(source: str, node: ast.ClassDef, code_lines: list[str], opened: set[str] | None):
    tree = ast.parse(source)
    if not any(isinstance(n, ast.ClassDef) and n.name == node.name for n in tree.body):
        methods = [s for s in node.body if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]
        empty = [
            f"{node.name}.{m.name} (its body was only `...`)" for m in methods if _only_ellipsis(m)
        ]
        if empty and len(empty) == len(methods):
            return source, [], empty
        return _insert_class(source, node, code_lines), [node.name], []
    changed, skipped = [], []
    for sub in node.body:
        if _is_docstring(sub) or isinstance(sub, ast.Pass):
            continue
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = f"{node.name}.{sub.name}"
            if _only_ellipsis(sub):
                skipped.append(f"{name} (its body was only `...`)")
                continue
            if _unseen(source, name, opened):
                skipped.append(_NOT_OPENED.format(name=name))
                continue
            source = _put_member(source, node.name, sub, code_lines)
            changed.append(name)
        elif _assigned_name(sub):
            source = _put_member(source, node.name, sub, code_lines)
        else:
            skipped.append(
                f"the {type(sub).__name__} statement at line {sub.lineno} in class "
                f"{node.name} (" + _ONLY + ")"
            )
    return source, changed, skipped


def _put_member(source: str, cls: str | None, node: ast.stmt, code_lines: list[str]) -> str:
    """Replace the def or assignment of the same name in the module (cls
    None) or in class `cls`, or insert it."""
    tree = ast.parse(source)
    lines = source.split("\n")
    body = tree.body
    container = None
    if cls is not None:
        container = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
        body = container.body
    name = _member_name(node)
    new = _segment(node, code_lines)
    for old in body:
        if _member_name(old) == name and type(old) in _same_kind(node):
            indent = " " * old.col_offset
            lines[_start(old) - 1 : old.end_lineno] = [_indent(x, indent) for x in new]
            return "\n".join(lines)
    if container is None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return _append(lines, new)
        return _insert_at(lines, _after_imports(tree), new, blank=False)
    indent = " " * container.body[0].col_offset
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        at = container.end_lineno
        return "\n".join(lines[:at] + [""] + [_indent(x, indent) for x in new] + lines[at:])
    first = container.body[0]
    at = first.end_lineno if _is_docstring(first) else first.lineno - 1
    return "\n".join(lines[:at] + [_indent(x, indent) for x in new] + lines[at:])


def _insert_class(source: str, node: ast.ClassDef, code_lines: list[str]) -> str:
    tree = ast.parse(source)
    lines = source.split("\n")
    needed = {
        n.id
        for e in [*node.bases, *node.decorator_list]
        for n in ast.walk(e)
        if isinstance(n, ast.Name)
    }
    at = _after_imports(tree)
    for top in tree.body:
        if _defined_names(top) & needed:
            at = top.end_lineno
    return _insert_at(lines, at, _segment(node, code_lines), blank=True)


def _put_import(source: str, new: list[str]) -> str:
    tree = ast.parse(source)
    present = {
        line.strip()
        for n in tree.body
        if isinstance(n, (ast.Import, ast.ImportFrom))
        for line in source.split("\n")[n.lineno - 1 : n.end_lineno]
    }
    if all(line.strip() in present for line in new if line.strip()):
        return source
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    at = imports[-1].end_lineno if imports else _docstring_end(tree)
    return _insert_at(source.split("\n"), at, new, blank=False)


def _insert_at(lines: list[str], at: int, new: list[str], *, blank: bool) -> str:
    pad = [""] if blank else []
    return "\n".join(lines[:at] + pad + new + pad + lines[at:])


def _append(lines: list[str], new: list[str]) -> str:
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return "\n".join([*lines, "", "", *new, ""])


def _after_imports(tree: ast.Module) -> int:
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    return imports[-1].end_lineno if imports else _docstring_end(tree)


def _docstring_end(tree: ast.Module) -> int:
    return tree.body[0].end_lineno if tree.body and _is_docstring(tree.body[0]) else 0


def _segment(node: ast.stmt, code_lines: list[str]) -> list[str]:
    text = "\n".join(code_lines[_start(node) - 1 : node.end_lineno])
    return textwrap.dedent(text).split("\n")


def _indent(line: str, indent: str) -> str:
    return indent + line if line.strip() else line


def _start(node: ast.stmt) -> int:
    decorators = getattr(node, "decorator_list", [])
    return min([node.lineno, *(d.lineno for d in decorators)])


def _is_docstring(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _only_ellipsis(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = [s for s in node.body if not _is_docstring(s)]
    return all(
        isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is ...
        for s in body
    )


def _assigned_name(node: ast.stmt) -> str | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        return target.id if isinstance(target, ast.Name) else None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def _member_name(node: ast.stmt) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    return _assigned_name(node)


def _same_kind(node: ast.stmt) -> tuple[type, ...]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return (ast.FunctionDef, ast.AsyncFunctionDef)
    return (ast.Assign, ast.AnnAssign)


def _defined_names(node: ast.stmt) -> set[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return {(a.asname or a.name).split(".")[0] for a in node.names}
    name = _assigned_name(node)
    return {name} if name else set()
