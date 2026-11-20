"""Tests for harness.foresight: filling $later_changes with a task's change
requests, spotting programs that implement a later change early, and
cutting what only the later changes name out of a final version.

Usage:
    uv run pytest tests/test_foresight.py
"""

import dataclasses
from pathlib import Path

from harness.config import load_config
from harness.foresight import (
    defined_names,
    fill_hint,
    implements_later_change,
    later_change_names,
    prune_program,
    requested_names,
)
from harness.registry import load_tasks

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "configs" / "base.yaml")
TASKS = load_tasks(dataclasses.replace(CFG.tasks, include=("mail_bins", "bank_ledger")))
MAIL = TASKS["mail_bins"]
BANK = TASKS["bank_ledger"]


def test_hint_without_the_placeholder_is_unchanged():
    assert fill_hint("Keep a log.", MAIL) == "Keep a log."


def test_placeholder_becomes_every_change_request_in_manifest_order():
    filled = fill_hint("Later:\n\n$later_changes", MAIL)
    assert "$later_changes" not in filled
    positions = [filled.index(c.request.strip()) for c in MAIL.changes.values()]
    assert positions == sorted(positions) and len(positions) == 3
    assert filled.startswith("Later:\n\n### Change 1\n\n")


def test_program_placeholder_becomes_the_program_in_the_output_format():
    program = {"m.py": b"x = 1\n"}
    filled = fill_hint("Pare down:\n\n$program\n\n$later_changes", MAIL, program)
    assert filled.startswith("Pare down:\n\n```python file=m.py\nx = 1\n```\n\n### Change 1")
    assert fill_hint("Pare down: $program", MAIL) == "Pare down: $program"


def test_requested_names_come_from_code_spans_only():
    request = (
        "Add `Ledger.freeze(account_id)` and `class AccountFrozen(LedgerError)`. "
        "`Ledger` takes a new keyword argument `fee=0`; freeze(x) in prose is "
        "ignored, and so are `sorted(x)` and `a == b`."
    )
    assert requested_names(request) == {"freeze", "AccountFrozen", "fee"}


def test_defined_names_include_methods_classes_and_parameters():
    program = {
        "m.py": b"class A:\n    def f(self, x, *, fee=0):\n        pass\n",
        "notes.txt": b"def g(): pass\n",
        "bad.py": b"def (:\n",
    }
    assert defined_names(program) == {"A", "f", "self", "x", "fee"}


def test_later_change_names_leave_out_what_the_initial_reference_defines():
    names = later_change_names(MAIL)
    assert {"undo", "set_accepts", "get_accepts", "NotAccepted", "get_bin_of"} <= names
    assert not names & defined_names(MAIL.reference)
    assert {"freeze", "AccountFrozen", "fee", "overdraft_limit"} <= later_change_names(BANK)


def test_a_program_with_an_undo_method_implements_a_later_change_early():
    assert not implements_later_change(MAIL.reference, MAIL)
    (path, source), *_ = MAIL.reference.items()
    early = {path: source + b"\n\ndef undo():\n    pass\n"}
    assert implements_later_change(early, MAIL)


FINAL = b"""\
class SortingError(Exception):
    pass


class NotAccepted(SortingError):
    pass


class Sorter:
    def __init__(self):
        self._bins = {}
        self._history = []  # kept for undo

    def drop(self, bin_name, item):
        if item in self._refused:
            raise NotAccepted(item)
        self._bins[bin_name].append(item)
        self._history.append(("drop", bin_name, item))

    @staticmethod
    def get_accepts():
        return []

    def undo(self):
        kind, *args = self._history.pop()

    def count(self):
        return len(self._bins)
"""

FIRST = b"""\
class SortingError(Exception):
    pass


class Sorter:
    def __init__(self):
        self._bins = {}
        self._history = []  # kept for undo

    def drop(self, bin_name, item):
        self._bins[bin_name].append(item)
        self._history.append(("drop", bin_name, item))

    def count(self):
        return len(self._bins)
"""


def test_pruning_cuts_what_only_later_changes_name_and_keeps_the_rest_as_written():
    # The history stays; undo, get_accepts, NotAccepted and its guard go.
    pruned = prune_program({"sorting.py": FINAL, "notes.txt": b"def undo(): pass\n"}, MAIL)
    assert pruned == {"sorting.py": FIRST, "notes.txt": b"def undo(): pass\n"}
    assert not implements_later_change(pruned, MAIL)
    assert prune_program({"sorting.py": FIRST}, MAIL) == {"sorting.py": FIRST}


def test_a_body_left_empty_gets_pass():
    source = b"def check(item):\n    if item in REFUSED:\n        raise NotAccepted(item)\n"
    assert prune_program({"m.py": source}, MAIL) == {"m.py": b"def check(item):\n    pass\n"}


def test_guards_that_do_more_than_raise_and_elifs_stay():
    source = b"""\
def f(x):
    if x == 0:
        log(x)
        raise NotAccepted(x)
    if x == 1:
        raise NotAccepted(x)
    else:
        return 1
    if x == 2:
        return 2
    elif x == 3:
        raise NotAccepted(x)
    return 0
"""
    assert prune_program({"m.py": source}, MAIL) == {"m.py": source}


def test_a_file_that_does_not_parse_is_left_as_it_was():
    assert prune_program({"m.py": b"def undo(:\n"}, MAIL) == {"m.py": b"def undo(:\n"}
