"""Turns a model's text answer into program files.

The expected format (set by the writer prompt) is one fenced block per file:

    ```python file=records.py
    <file contents>
    ```

Prose outside fenced blocks is ignored. Everything about the blocks is
strict: every fence must be labelled `python file=<path>`, the path must be
one of the allowed files, no file may appear twice, and every allowed file
must appear. Anything else is a failure with a reason code, never a guess,
because a guessed program is not what the model wrote.

Failures fall into two categories reported separately:
- "truncated": the backend stopped at max_tokens (finish_reason "length"),
  so the answer is incomplete however it parses;
- "malformed": the model finished but the answer breaks the format.

Usage:
    result = parse_program(answer, task.entry_files, backend.last_usage.finish_reason)
    if result.ok:
        result.files                                 # {"records.py": b"..."}
    else:
        str(result.failure)                          # "malformed/unlabeled_block: line 40: ..."
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

Category = Literal["truncated", "malformed"]
Reason = Literal[
    "max_tokens",  # truncated
    "no_code",  # no fenced block at all
    "unclosed_block",  # a block is still open at the end of the answer
    "unlabeled_block",  # a fence without `file=` (e.g. ```python or ```)
    "bad_label",  # mentions file= but isn't exactly `python file=<path>`
    "bad_path",  # absolute, '..', backslash, quotes or not normalized
    "not_allowed",  # a path outside the allowed files
    "duplicate",  # the same path in two blocks
    "missing_file",  # an allowed file with no block
]

# An opening or closing fence: three or more backticks at the start of a line.
_FENCE = re.compile(r"^(`{3,})(.*)$")
_LABEL = re.compile(r"^python file=(\S+)$")


@dataclass(frozen=True)
class ParseFailure:
    category: Category
    reason: Reason
    detail: str

    def __str__(self) -> str:
        # The form stored in the candidates table's parse_error column.
        return f"{self.category}/{self.reason}: {self.detail}"


@dataclass(frozen=True)
class ParseResult:
    files: dict[str, bytes] | None  # set when parsing succeeded
    failure: ParseFailure | None  # set when it didn't

    @property
    def ok(self) -> bool:
        return self.failure is None


def parse_program(
    text: str, allowed_files: Sequence[str], finish_reason: str | None = None
) -> ParseResult:
    """Extract the allowed files from a model answer, preserving their exact
    contents as UTF-8 bytes."""
    if finish_reason == "length":
        return _fail("truncated", "max_tokens", "the backend stopped at max_tokens")
    try:
        blocks = _blocks(text)
        files: dict[str, bytes] = {}
        for line_no, label, content in blocks:
            path = _path_from_label(label, line_no)
            if path not in allowed_files:
                raise _Failure(
                    "not_allowed", f"line {line_no}: {path!r} is not one of {list(allowed_files)}"
                )
            if path in files:
                raise _Failure("duplicate", f"line {line_no}: {path!r} appears more than once")
            files[path] = content.encode("utf-8")
        if not blocks:
            raise _Failure("no_code", "the answer has no fenced code block")
        missing = [p for p in allowed_files if p not in files]
        if missing:
            raise _Failure("missing_file", f"no block for {missing}")
    except _Failure as exc:
        return _fail("malformed", exc.reason, exc.detail)
    return ParseResult(files, None)


def render_program(files: dict[str, bytes]) -> str:
    """The inverse of parse_program, in the format the writer prompt asks
    for. Used for prompts that show a program and for tests. Each file must
    be empty or end with a newline to survive the round trip."""
    parts = []
    for path in sorted(files):
        content = files[path].decode("utf-8")
        parts.append(f"```python file={path}\n{content}```\n")
    return "\n".join(parts)


class _Failure(Exception):
    def __init__(self, reason: Reason, detail: str) -> None:
        self.reason = reason
        self.detail = detail


def _fail(category: Category, reason: Reason, detail: str) -> ParseResult:
    return ParseResult(None, ParseFailure(category, reason, detail))


def _blocks(text: str) -> list[tuple[int, str, str]]:
    """(line number, info string, content) for every fenced block.

    Lines are split on "\\n" only. str.splitlines would also split on form
    feeds and Unicode line separators inside the code, changing its bytes.
    A trailing "\\r" is ignored when recognizing fences, so CRLF answers
    work, but kept in the content.
    """
    lines = text.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        opening = _FENCE.match(lines[i].rstrip("\r"))
        if opening is None:
            i += 1  # prose
            continue
        ticks, info = opening.group(1), opening.group(2).strip()
        start = i + 1
        # CommonMark: a block closes at a line of at least as many backticks
        # and nothing else. Longer fences let code contain ``` lines.
        close = re.compile(rf"^`{{{len(ticks)},}}\s*$")
        end = start
        while end < len(lines) and close.match(lines[end].rstrip("\r")) is None:
            end += 1
        if end == len(lines):
            raise _Failure("unclosed_block", f"line {i + 1}: block is never closed")
        content = "\n".join(lines[start:end])
        blocks.append((i + 1, info, content + "\n" if end > start else ""))
        i = end + 1
    return blocks


def _path_from_label(info: str, line_no: int) -> str:
    label = _LABEL.match(info)
    if label is None:
        if "file=" in info:
            raise _Failure(
                "bad_label", f"line {line_no}: expected `python file=<path>`, got {info!r}"
            )
        raise _Failure("unlabeled_block", f"line {line_no}: block has no file= label ({info!r})")
    path = label.group(1)
    p = PurePosixPath(path)
    if (
        p.is_absolute()
        or ".." in p.parts
        or "\\" in path
        or any(q in path for q in "\"'`")
        or str(p) != path
    ):
        raise _Failure("bad_path", f"line {line_no}: unsafe or non-normalized path {path!r}")
    return path
