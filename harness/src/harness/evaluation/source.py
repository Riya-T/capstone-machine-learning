"""Describe saved Python source without executing or transforming it.

Usage:
    metrics = describe_source({"main.py": b"# example\nx = 1\n"})
"""

from __future__ import annotations

import ast
import io
import tokenize


def describe_source(files: dict[str, bytes]) -> dict:
    """Count physical Python lines; documentation is the union of comment/docstring lines.

    Inline comments count their physical line. Only actual module/class/function
    docstrings count. A syntax/encoding/tokenization error makes documentation
    measures unavailable for the whole program rather than partially estimating them.
    These are descriptive measures, never maintainability scores.
    """
    python = {name: data for name, data in files.items() if name.endswith(".py")}
    result = dict(
        source_files=len(files),
        source_lines=sum(len(data.splitlines()) for data in files.values()),
        python_files=len(python),
        python_lines=sum(len(data.splitlines()) for data in python.values()),
        python_syntax_valid=None if not python else True,
        python_comment_lines=None,
        python_docstring_lines=None,
        python_documentation_lines=None,
        python_documentation_density=None,
    )
    if not python:
        return result
    comments, docstrings = set(), set()
    try:
        for name, data in python.items():
            tree = ast.parse(data, filename=name)
            for token in tokenize.tokenize(io.BytesIO(data).readline):
                if token.type == tokenize.COMMENT:
                    comments.add((name, token.start[0]))
            for node in ast.walk(tree):
                if (
                    not isinstance(
                        node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                    )
                    or not node.body
                ):
                    continue
                first = node.body[0]
                if (
                    isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)
                ):
                    docstrings.update(
                        (name, line) for line in range(first.lineno, first.end_lineno + 1)
                    )
    except (SyntaxError, UnicodeError, LookupError, tokenize.TokenError):
        result["python_syntax_valid"] = False
        return result
    result.update(
        python_comment_lines=len(comments),
        python_docstring_lines=len(docstrings),
        python_documentation_lines=len(comments | docstrings),
        python_documentation_density=(
            len(comments | docstrings) / result["python_lines"] if result["python_lines"] else None
        ),
    )
    return result
