"""Checks the course rule that every source and test file starts with a
descriptive header that includes usage information.

A file passes if its module docstring exists and contains a "Usage" section.
Covers the package, the tests and the task files.

Usage:
    uv run pytest tests/test_headers.py
"""

import ast
from pathlib import Path

import pytest

PILOT = Path(__file__).resolve().parents[1]
FILES = sorted(
    p
    for folder in ("src", "tests", "tasks")
    for p in (PILOT / folder).rglob("*.py")
    if "__pycache__" not in p.parts
)


def test_files_were_found():
    assert len(FILES) > 30


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(PILOT)))
def test_file_has_a_header_with_usage(path):
    docstring = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    assert docstring, "missing module docstring"
    assert len(docstring.splitlines()[0]) > 10, "first line should describe the file"
    assert "Usage" in docstring, "header has no Usage section"
