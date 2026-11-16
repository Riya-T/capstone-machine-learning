"""What the editor sees of a program: editor.view_transform.

"strip_comments" (the comment ablation) removes every comment and every
module, class and function docstring from the program's Python files,
before the first step of a change sequence. The editor then edits the
stripped program for the whole sequence, so comments it writes itself stay.

Stripping keeps the layout of everything else: no reformatting, only the
comment text (and lines left empty by it) and the docstrings go. A body
that held only a docstring gets `pass`. Every stripped file is checked to
parse to the same syntax tree as the original without its docstrings, so
the program does the same thing (except for reading `__doc__`, which no
test does). A file that doesn't parse is left as it is; the program can
still pass its tests if nothing imports it.

"obscure" (the readability control) makes the program as hard to read as
it can without changing what it does: comments and docstrings go, every
private name (`_items`, `_check`, `_Node`: one leading underscore) becomes
`_x1`, `_x2`, ... across all files, every public data attribute (a name
only ever assigned as `self.accounts = ...`: not a method, class attribute,
parameter, import, string or attribute of a builtin type) becomes `a1`,
`a2`, ..., every local variable of a function or method becomes `v1`, `v2`,
..., and the code is printed back by `ast.unparse` (no blank lines inside
classes and functions). Public functions, classes and methods, parameters,
keyword arguments, imports and dunder names stay, so the change requests
still apply; a test that reads a data attribute directly would fail, which
`scripts/obscure_check.py` rules out for the programs of a run.

Usage:
    view = make_view("strip_comments")
    shown = view(program)  # {path: bytes}, the same paths
"""

from __future__ import annotations

import ast
import builtins
import collections
import datetime
import decimal
import enum
import fractions
import io
import logging
import re
import tokenize
from collections.abc import Callable, Iterator

from ..registry import Program

log = logging.getLogger("harness")

View = Callable[[Program], Program]
_DOC_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
_PRIVATE = re.compile(r"_[A-Za-z0-9]\w*\Z")  # one leading underscore, not `_` or dunder
# Attribute names of builtin and standard-library types, which `x.items()`
# or `when.year` may mean even where the program also sets `self.items`.
_LIBRARY_ATTRIBUTES = frozenset().union(
    *map(
        dir,
        (
            *(dict, list, set, frozenset, tuple, str, bytes, bytearray, int, float, complex),
            *(bool, object, BaseException, range, slice, memoryview, enum.Enum),
            *(collections.deque, collections.Counter, collections.OrderedDict),
            *(collections.defaultdict, datetime.date, datetime.datetime, datetime.time),
            *(datetime.timedelta, decimal.Decimal, fractions.Fraction),
        ),
    )
)


def make_view(transform: str) -> View:
    """The function from a program to what the editor sees of it."""
    if transform == "none":
        return dict
    if transform == "strip_comments":
        return strip_comments
    if transform == "obscure":
        return obscure
    raise ValueError(f"unknown view_transform {transform!r}")


def obscure(program: Program) -> Program:
    """The program without comments, docstrings, blank lines or meaningful
    private and local names. Files that aren't Python or don't parse are
    left as they are."""
    trees = {}
    for path, data in program.items():
        if path.endswith(".py"):
            try:
                trees[path] = ast.parse(data.decode("utf-8"))
            except (SyntaxError, UnicodeDecodeError) as exc:
                log.warning("obscure: %s left as it is (%s)", path, exc)
    for tree in trees.values():
        for owner, _ in _docstrings(tree):
            owner.body = owner.body[1:] or ([] if isinstance(owner, ast.Module) else [ast.Pass()])
    private = _private_names(trees.values())
    for tree in trees.values():
        _rename(tree, private)
    attributes = _attribute_names(trees.values())
    for tree in trees.values():
        _rename(tree, attributes, attributes_only=True)
        taken, fixed = _module_names(tree)
        for function in _outer_functions(tree):
            _rename(function, _local_names(function, taken, fixed), locals_only=True)
    return {
        path: (ast.unparse(trees[path]) + "\n").encode("utf-8") if path in trees else data
        for path, data in program.items()
    }


def _identifiers(tree: ast.AST) -> Iterator[tuple[str, bool]]:
    """(identifier, may be renamed) for every name in the tree. Parameters,
    keyword arguments, imports and global or nonlocal declarations are never
    renamed: callers and other modules use them by name."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            yield node.id, True
        elif isinstance(node, ast.Attribute):
            yield node.attr, True
        elif isinstance(node, (*_FUNCTIONS, ast.ClassDef, ast.ExceptHandler)):
            if node.name:
                yield node.name, True
        elif isinstance(node, (ast.arg, ast.keyword)):
            if node.arg:
                yield node.arg, False
        elif isinstance(node, ast.alias):
            for part in [*node.name.split("."), node.asname or ""]:
                yield part, False
        elif isinstance(node, ast.ImportFrom):
            for part in (node.module or "").split("."):
                yield part, False
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            for name in node.names:
                yield name, False
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            yield node.name, False
        elif isinstance(node, ast.MatchMapping) and node.rest:
            yield node.rest, False
        elif isinstance(node, ast.MatchClass):
            for name in node.kwd_attrs:
                yield name, False


def _fresh(prefix: str, taken: set[str]) -> Iterator[str]:
    i = 0
    while True:
        i += 1
        if f"{prefix}{i}" not in taken:
            yield f"{prefix}{i}"


def _private_names(trees) -> dict[str, str]:
    """Old -> new name of every private name, in order of first use."""
    seen, fixed = {}, set(dir(builtins))
    for tree in trees:
        for name, free in _identifiers(tree):
            seen.setdefault(name, None)
            if not free:
                fixed.add(name)
    new = _fresh("_x", set(seen))
    return {name: next(new) for name in seen if _PRIVATE.match(name) and name not in fixed}


def _attribute_names(trees) -> dict[str, str]:
    """Old -> new name of every public data attribute, in order of first
    assignment: a name set as `self.name = ...` that is nothing else in
    the program (not a method, property, class or module attribute,
    parameter, keyword, import or string, nor read from an imported module
    or an attribute of a builtin type)."""
    trees = list(trees)
    seen, fixed = set(), set(dir(builtins)) | _LIBRARY_ATTRIBUTES
    assigned = {}
    for tree in trees:
        imported = set()
        for name, free in _identifiers(tree):
            seen.add(name)
            if not free:
                fixed.add(name)
        for node in ast.walk(tree):
            if isinstance(node, ast.alias):
                imported.add((node.asname or node.name).split(".")[0])
        for node in tree.body:
            if not isinstance(node, (*_FUNCTIONS, ast.ClassDef)):
                fixed.update(n.id for n in ast.walk(node) if isinstance(n, ast.Name))
        for node in ast.walk(tree):
            if isinstance(node, (*_FUNCTIONS, ast.ClassDef)):
                fixed.add(node.name)
            if isinstance(node, ast.ClassDef):
                for statement in node.body:
                    if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                        fixed.update(n.id for n in ast.walk(statement) if isinstance(n, ast.Name))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                fixed.add(node.value)
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id in imported:
                    fixed.add(node.attr)
                elif node.value.id == "self" and isinstance(node.ctx, ast.Store):
                    assigned.setdefault(node.attr, None)
    new = _fresh("a", seen)
    return {
        name: next(new)
        for name in assigned
        if name not in fixed and not name.startswith("_") and name.isidentifier()
    }


def _outer_functions(tree: ast.AST) -> Iterator[ast.AST]:
    """Functions and methods not inside another function."""
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, _FUNCTIONS):
            yield node
        else:
            yield from _outer_functions(node)


def _function_nodes(function: ast.AST) -> Iterator[ast.AST]:
    """The nodes of a function, nested functions and comprehensions
    included, classes defined inside it left out (their assignments are
    class attributes)."""
    for node in ast.iter_child_nodes(function):
        if not isinstance(node, ast.ClassDef):
            yield node
            yield from _function_nodes(node)


def _module_names(module: ast.Module) -> tuple[set[str], set[str]]:
    """(every identifier in the module, the ones a local renaming must
    leave alone: parameters and the like, builtins, private names and names
    bound at module level)."""
    taken, fixed = set(), set(dir(builtins))
    for name, free in _identifiers(module):
        taken.add(name)
        if not free or _PRIVATE.match(name):
            fixed.add(name)
    for node in module.body:
        if isinstance(node, (*_FUNCTIONS, ast.ClassDef)):
            fixed.add(node.name)
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                fixed.add(sub.id)
    return taken, fixed


def _local_names(function: ast.AST, taken: set[str], fixed: set[str]) -> dict[str, str]:
    """Old -> new name of every variable the function (or a function or
    comprehension inside it) assigns, apart from the fixed names. None for
    a function that defines a class, whose body may read the function's
    variables."""
    if any(isinstance(node, ast.ClassDef) for node in ast.walk(function)):
        return {}
    assigned = {}
    for node in _function_nodes(function):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            assigned.setdefault(node.id, None)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            assigned.setdefault(node.name, None)
    new = _fresh("v", taken)
    return {name: next(new) for name in assigned if name not in fixed}


def _rename(
    tree: ast.AST,
    names: dict[str, str],
    locals_only: bool = False,
    attributes_only: bool = False,
) -> None:
    """Rename in place: private names everywhere (also as attribute names,
    definitions and strings equal to one, as in `__slots__`), with
    locals_only the variables of one function, with attributes_only the
    data attributes (`x.name`, whatever x is)."""
    if not names:
        return
    if attributes_only:
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in names:
                node.attr = names[node.attr]
        return
    nodes = _function_nodes(tree) if locals_only else ast.walk(tree)
    for node in nodes:
        if isinstance(node, ast.Name) and node.id in names:
            node.id = names[node.id]
        elif isinstance(node, ast.ExceptHandler) and node.name in names:
            node.name = names[node.name]
        elif locals_only:
            continue
        elif isinstance(node, ast.Attribute) and node.attr in names:
            node.attr = names[node.attr]
        elif isinstance(node, (*_FUNCTIONS, ast.ClassDef)) and node.name in names:
            node.name = names[node.name]
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in names:
            node.value = names[node.value]


def strip_comments(program: Program) -> Program:
    """The program with comments and docstrings removed from its .py files."""
    result = {}
    for path, data in program.items():
        if not path.endswith(".py"):
            result[path] = data
            continue
        try:
            result[path] = strip_source(data)
        except (SyntaxError, UnicodeDecodeError, tokenize.TokenError) as exc:
            log.warning("strip_comments: %s left as it is (%s)", path, exc)
            result[path] = data
    return result


def strip_source(data: bytes) -> bytes:
    """One Python file without comments and docstrings. Raises SyntaxError
    (or UnicodeDecodeError) if it doesn't parse."""
    text = data.decode("utf-8")
    original = ast.parse(text)
    stripped = _strip_comment_tokens(_strip_docstrings(text, original))
    if _shape(ast.parse(stripped)) != _shape(original):
        raise AssertionError("strip_comments changed the program's syntax tree")
    return stripped.encode("utf-8")


def _docstrings(tree: ast.Module) -> list[tuple[ast.AST, ast.Expr]]:
    """(owner, docstring statement) for every module, class and function."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, _DOC_OWNERS) and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                found.append((node, first))
    return found


def _strip_docstrings(text: str, tree: ast.Module) -> str:
    # ast columns are UTF-8 byte offsets, so edit the lines as bytes.
    lines = [line.encode("utf-8") for line in text.splitlines(keepends=True)]
    # Bottom-up, so earlier positions stay valid as later lines change.
    for owner, doc in sorted(_docstrings(tree), key=lambda d: -d[1].lineno):
        first, last = doc.lineno - 1, doc.end_lineno - 1
        before = lines[first][: doc.col_offset]
        after = lines[last][doc.end_col_offset :]
        alone = len(owner.body) == 1 and not isinstance(owner, ast.Module)
        rest = after.strip()
        if not before.strip() and (not rest or rest.startswith(b"#")) and not alone:
            del lines[first : last + 1]  # the docstring has its lines to itself
        else:
            # Shares a line with other code (`def f(): "doc"`, `"doc"; x = 1`)
            # or is the whole body: put `pass` in its place.
            lines[first : last + 1] = [before + b"pass" + after]
    return b"".join(lines).decode("utf-8")


def _strip_comment_tokens(text: str) -> str:
    lines = text.splitlines(keepends=True)
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    comments = [t.start for t in tokens if t.type == tokenize.COMMENT]
    for row, col in reversed(comments):
        line = lines[row - 1]
        ending = line[len(line.rstrip("\r\n")) :]
        if not line[:col].strip():
            del lines[row - 1]  # a comment on a line of its own
        else:
            lines[row - 1] = line[:col].rstrip() + ending
    return "".join(lines)


def _shape(tree: ast.Module) -> str:
    """The syntax tree without docstrings, positions or `pass` statements
    that sit beside other statements, for comparing two versions of a
    file. A body with only a docstring compares as `pass`."""
    for owner, _ in _docstrings(tree):
        owner.body = owner.body[1:] or ([] if isinstance(owner, ast.Module) else [ast.Pass()])
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            body = getattr(node, field, None)
            if isinstance(body, list) and len(body) > 1:
                kept = [s for s in body if not isinstance(s, ast.Pass)]
                setattr(node, field, kept or body[:1])
    return ast.dump(tree, include_attributes=False)
