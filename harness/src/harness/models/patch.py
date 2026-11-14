"""SEARCH/REPLACE edits: how the editor changes files without resending
them (editor.edit_format: search_replace).

An edit names a file, quotes lines of its current contents and gives the
lines to put in their place:

    records.py
    <<<<<<< SEARCH
        def get(self, key):
            return self._data[key]
    =======
        def get(self, key, default=None):
            return self._data.get(key, default)
    >>>>>>> REPLACE

The file name is the closest non-blank line above the SEARCH marker, or the
file= label of the fenced block the edit sits in; it may be left out when
only one file may change. Edits may sit inside or outside fenced blocks, and
a fence line copied into the SEARCH or REPLACE lines (the prompt shows the
program in fenced blocks) is dropped.

A reply's edits apply in order. The SEARCH lines must match exactly one
place in the file as it stands after the earlier edits, exactly or, failing
that, ignoring trailing whitespace; a guessed location is not what the
model wrote. An edit that doesn't match is skipped with an EditError whose
message tells the editor what to fix, and the other edits still apply: the
14B editor often sends a dozen edits, and in the first patch run one bad
edit wasted the whole turn every time. An edit that doesn't match but whose
REPLACE lines are already in the file (a repeat of an earlier edit) is
skipped silently, and so is one whose REPLACE lines equal its SEARCH lines;
neither counts as applied. A fenced file= block that holds code but no edit is an
error for the whole reply: whole files are not accepted in this format.

Usage:
    edits, outside = split_edits(reply, allowed_files)   # raises EditError
    result = apply_edits(files, edits)
    result.files, result.failures                        # [(edit number, EditError)]
    outside                                              # reply lines not in an edit
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

# Part of the editor key when edit_format is search_replace (store.py):
# raise it whenever a change here alters which edits apply. 1: all or
# nothing. 2: edits apply one by one, repeats and fence lines are dropped.
# 3: edits that change nothing don't count as applied, and SEARCH lines that
# start with a def or class missing from the file get their own message.
PROTOCOL_VERSION = 3

Reason = Literal[
    "unclosed_edit",  # no ======= or >>>>>>> REPLACE after a SEARCH marker
    "empty_search",  # an edit that quotes no lines
    "no_file",  # several files may change and the edit doesn't name one
    "not_allowed",  # names a file outside the allowed files
    "whole_file",  # a file= block with code but no edit
    "new_code",  # the SEARCH lines start with a def or class the file doesn't have
    "not_found",  # the SEARCH lines match nowhere
    "ambiguous",  # the SEARCH lines match more than one place
]

_SEARCH = re.compile(r"^\s*<{5,9} ?SEARCH\s*$")
_DIVIDER = re.compile(r"^\s*={5,9}\s*$")
_REPLACE = re.compile(r"^\s*>{5,9} ?REPLACE\s*$")
_FENCE = re.compile(r"^\s*(`{3,})(.*)$")
_FILE_LABEL = re.compile(r"\bfile=(\S+)")
_HEADER = re.compile(r"^\s*(?:async\s+)?(def|class)\s+(\w+)")


class EditError(ValueError):
    """An edit that cannot be read or applied. str() is for the editor."""

    def __init__(self, reason: Reason, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason


@dataclass(frozen=True)
class Edit:
    path: str
    search: tuple[str, ...]
    replace: tuple[str, ...]
    line_no: int  # of the SEARCH marker in the reply, from 1


@dataclass(frozen=True)
class Applied:
    files: dict[str, bytes]  # with every edit that matched applied
    failures: list[tuple[int, EditError]]  # (edit number from 1, why it was skipped)
    applied: int  # edits that changed a file
    repeated: int  # edits skipped because their REPLACE lines were already there
    unchanged: int  # edits skipped because their REPLACE lines equal their SEARCH lines


def split_edits(text: str, allowed_files: Sequence[str]) -> tuple[list[Edit], list[str]]:
    """The reply's edits, in order, and the reply's lines outside them
    (where commands such as RUN_CHECKS live)."""
    lines = [line.rstrip("\r") for line in text.split("\n")]
    edits: list[Edit] = []
    outside: list[str] = []
    fence_label = ""  # info string of the fenced block we are in, if any
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if _SEARCH.match(line):
            edit, i = _read_edit(lines, i, fence_label if in_fence else "", allowed_files)
            edits.append(edit)
            continue
        fence = _FENCE.match(line)
        if fence:
            if in_fence and not fence.group(2).strip():
                in_fence = False
            elif not in_fence:
                in_fence, fence_label = True, fence.group(2).strip()
        outside.append(line)
        i += 1
    whole = _whole_files(outside, allowed_files)
    if whole:
        raise EditError(
            "whole_file",
            f"a ```{whole[0]} block holds code but no <<<<<<< SEARCH edit; whole files "
            "are not accepted, send SEARCH/REPLACE edits instead",
        )
    return edits, outside


def apply_edits(files: dict[str, bytes], edits: Sequence[Edit]) -> Applied:
    """The files with the edits applied in order, each one that matches
    exactly one place; the others are listed in failures."""
    out = dict(files)
    failures: list[tuple[int, EditError]] = []
    applied = repeated = unchanged = 0
    for k, edit in enumerate(edits, 1):
        where = f"edit {k} ({edit.path}, line {edit.line_no} of your reply)"
        if edit.search == edit.replace:
            unchanged += 1
            continue
        text = out[edit.path].decode("utf-8")
        lines = text.split("\n")
        found = _matches(lines, edit.search, lambda a, b: a == b)
        if not found:
            found = _matches(lines, edit.search, lambda a, b: a.rstrip() == b.rstrip())
        if not found:
            if edit.replace and _matches(lines, edit.replace, lambda a, b: a == b):
                repeated += 1
                continue
            header = _missing_header(edit.search, lines)
            if header:
                failures.append((k, EditError(
                    "new_code",
                    f"{where}: the SEARCH lines start with `{header}`, which is not in "
                    "the current file yet. To add new code, quote the existing lines it "
                    "should follow and repeat them in REPLACE with the new code after them",
                )))  # fmt: skip
                continue
            failures.append((k, EditError(
                "not_found",
                f"{where}: the SEARCH lines are not in the current file. Copy them "
                "exactly from the current program, including indentation",
            )))  # fmt: skip
            continue
        if len(found) > 1:
            failures.append((k, EditError(
                "ambiguous",
                f"{where}: the SEARCH lines match {len(found)} places. Quote more of "
                "the lines around them so they match only one",
            )))  # fmt: skip
            continue
        start = found[0]
        lines[start : start + len(edit.search)] = edit.replace
        new = "\n".join(lines)
        if text.endswith("\n") and not new.endswith("\n"):
            new += "\n"
        out[edit.path] = new.encode("utf-8")
        applied += 1
    return Applied(out, failures, applied, repeated, unchanged)


def _missing_header(search: tuple[str, ...], lines: list[str]) -> str | None:
    """The def or class line the SEARCH lines start with, if the file has no
    def or class of that name (the editor quoted code it means to add)."""
    first = next((line for line in search if line.strip()), "")
    header = _HEADER.match(first)
    if header is None:
        return None
    name = re.compile(rf"^\s*(?:async\s+)?{header.group(1)}\s+{re.escape(header.group(2))}\b")
    if any(name.match(line) for line in lines):
        return None
    return first.strip()


def _read_edit(
    lines: list[str], start: int, fence_label: str, allowed_files: Sequence[str]
) -> tuple[Edit, int]:
    """The edit whose SEARCH marker is lines[start], and the index after its
    REPLACE marker."""
    line_no = start + 1
    path = _edit_path(lines, start, fence_label, allowed_files, line_no)
    divider = end = None
    for j in range(start + 1, len(lines)):
        if divider is None and _DIVIDER.match(lines[j]):
            divider = j
        elif divider is not None and _REPLACE.match(lines[j]):
            end = j
            break
        elif _SEARCH.match(lines[j]) or (divider is None and _REPLACE.match(lines[j])):
            break
    if divider is None or end is None:
        raise EditError(
            "unclosed_edit",
            f"the edit at line {line_no} of your reply needs a ======= line and then a "
            ">>>>>>> REPLACE line",
        )
    search = _unfenced(lines[start + 1 : divider])
    if not search:
        raise EditError(
            "empty_search",
            f"the edit at line {line_no} of your reply quotes no lines; put the lines "
            "to replace between <<<<<<< SEARCH and =======",
        )
    return Edit(path, search, _unfenced(lines[divider + 1 : end]), line_no), end + 1


def _unfenced(block: list[str]) -> tuple[str, ...]:
    """The lines without a fence line copied in at the start or end."""
    if block and _FENCE.match(block[0]):
        block = block[1:]
    if block and _FENCE.match(block[-1]):
        block = block[:-1]
    return tuple(block)


def _edit_path(
    lines: list[str], start: int, fence_label: str, allowed_files: Sequence[str], line_no: int
) -> str:
    """The file an edit names: the closest non-blank line above its SEARCH
    marker, or its fenced block's file= label, or the only allowed file."""
    named = None
    for j in range(start - 1, -1, -1):
        text = lines[j].strip()
        if not text:
            continue
        fence = _FENCE.match(text)
        if fence:
            label = _FILE_LABEL.search(fence.group(2))
            if label:
                named = label.group(1)
                break
            continue  # ```python: look above it
        candidate = text.strip("`*#:").strip()
        if candidate in allowed_files or (" " not in candidate and candidate.endswith(".py")):
            named = candidate
        break  # prose, or the end of an earlier edit: no name here
    if named is None:
        label = _FILE_LABEL.search(fence_label)
        named = label.group(1) if label else None
    if named is None:
        if len(allowed_files) == 1:
            return allowed_files[0]
        raise EditError(
            "no_file",
            f"the edit at line {line_no} of your reply names no file; put the file name "
            f"({', '.join(allowed_files)}) on the line above <<<<<<< SEARCH",
        )
    if named not in allowed_files:
        raise EditError(
            "not_allowed",
            f"the edit at line {line_no} of your reply changes {named!r}; you may change "
            f"only {', '.join(allowed_files)}",
        )
    return named


def _matches(lines: list[str], search: tuple[str, ...], same) -> list[int]:
    n = len(search)
    return [
        i
        for i in range(len(lines) - n + 1)
        if all(same(a, b) for a, b in zip(lines[i : i + n], search, strict=True))
    ]


def _whole_files(outside: list[str], allowed_files: Sequence[str]) -> list[str]:
    """Info strings of fenced file= blocks that still hold code once the
    edits are taken out (a file name on its own line doesn't count)."""
    found = []
    label = None
    body: list[str] = []
    for line in outside:
        fence = _FENCE.match(line)
        if label is None:
            if fence:
                label, body = fence.group(2).strip(), []
            continue
        if fence and not fence.group(2).strip():
            code = [x.strip() for x in body if x.strip() and x.strip() not in allowed_files]
            if _FILE_LABEL.search(label) and code:
                found.append(label)
            label = None
        else:
            body.append(line)
    return found
