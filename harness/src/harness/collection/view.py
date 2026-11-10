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

Usage:
    view = make_view("strip_comments")
    shown = view(program)  # {path: bytes}, the same paths
"""

from __future__ import annotations

import ast
import io
import logging
import tokenize
from collections.abc import Callable

from ..registry import Program

log = logging.getLogger("harness")

View = Callable[[Program], Program]
_DOC_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def make_view(transform: str) -> View:
    """The function from a program to what the editor sees of it."""
    if transform == "none":
        return dict
    if transform == "strip_comments":
        return strip_comments
    raise ValueError(f"unknown view_transform {transform!r}")


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
