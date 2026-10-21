"""Hidden tests for the c_versions change (versioned task updates).
Never shown to the writer or the editor.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/private/test_versions_new.py
"""

import pytest
from board import Board, BoardError, VersionConflict

EDITS = {
    "complete": lambda b, t, **kw: b.complete(t, **kw),
    "move_task": lambda b, t, **kw: b.move_task(t, "app", **kw),
    "rename_task": lambda b, t, **kw: b.rename_task(t, "renamed", **kw),
    "set_due_day": lambda b, t, **kw: b.set_due_day(t, 9, **kw),
}


@pytest.fixture
def board():
    b = Board()
    b.add_project("web")
    b.add_project("app")
    b.add_task("web", "home", 2)
    b.add_task("web", "about", 4)
    return b


def state(b):
    tasks, task_id = [], 1
    while True:
        try:
            tasks.append((b.get_task(task_id), b.get_version(task_id)))
        except KeyError:
            break
        task_id += 1
    return {p: b.get_open_tasks(p) for p in b.get_projects()}, tasks


def test_versions_unknown_tasks_raise_key_error(board):
    for call in (
        lambda: board.get_version(99),
        lambda: board.get_version(None),
        lambda: board.rename_task(99, "x"),
        lambda: board.set_due_day(99, 1),
    ):
        with pytest.raises(KeyError):
            call()


@pytest.mark.parametrize("edit", sorted(EDITS))
def test_versions_each_change_adds_one(board, edit):
    EDITS[edit](board, 1)
    assert board.get_version(1) == 2
    assert board.get_version(2) == 1


def test_versions_count_every_change_in_turn(board):
    board.rename_task(1, "start")
    board.set_due_day(1, 3)
    board.move_task(1, "app")
    board.complete(1)
    board.move_task(1, "web")
    assert board.get_version(1) == 6
    assert board.get_task(1) == ("web", "start", 3, True)


def test_versions_setting_the_same_value_still_counts(board):
    board.rename_task(1, "home")
    board.set_due_day(1, 2)
    assert board.get_version(1) == 3
    assert board.get_task(1) == ("web", "home", 2, False)


def test_versions_done_tasks_can_be_renamed_and_rescheduled(board):
    board.complete(2)
    board.rename_task(2, "about us")
    board.set_due_day(2, 7)
    assert board.get_task(2) == ("web", "about us", 7, True)
    assert board.get_version(2) == 4


@pytest.mark.parametrize("edit", sorted(EDITS))
def test_versions_a_wrong_expected_version_changes_nothing(board, edit):
    board.rename_task(1, "home page")
    before = state(board)
    for stale in (1, 3, 0):
        with pytest.raises(VersionConflict):
            EDITS[edit](board, 1, expected_version=stale)
    assert state(board) == before


@pytest.mark.parametrize("edit", sorted(EDITS))
def test_versions_the_current_version_is_accepted(board, edit):
    board.set_due_day(1, 3)
    EDITS[edit](board, 1, expected_version=2)
    assert board.get_version(1) == 3


def test_versions_failed_calls_keep_the_version(board):
    board.complete(2)
    for call, error in [
        (lambda: board.complete(2), BoardError),
        (lambda: board.move_task(1, "web"), ValueError),
        (lambda: board.rename_task(1, ""), ValueError),
        (lambda: board.set_due_day(1, -1), ValueError),
    ]:
        with pytest.raises(error):
            call()
    assert board.get_version(1) == 1
    assert board.get_version(2) == 2


@pytest.mark.parametrize("day", [-1, 1.5, "3", None, True])
def test_versions_invalid_due_days_are_rejected(board, day):
    before = state(board)
    with pytest.raises(ValueError):
        board.set_due_day(1, day)
    assert state(board) == before


def test_versions_key_errors_come_before_a_conflict(board):
    with pytest.raises(KeyError):
        board.complete(99, expected_version=5)
    with pytest.raises(KeyError):
        board.move_task(1, "ops", expected_version=5)
    with pytest.raises(KeyError):
        board.rename_task(99, "x", expected_version=5)


def test_versions_a_conflict_comes_before_other_errors(board):
    for _ in range(4):
        board.add_task("app", "filler", 1)
    board.add_task("app", "last", 1)  # app is now full
    board.complete(2)
    for call in (
        lambda: board.complete(2, expected_version=1),
        lambda: board.move_task(1, "web", expected_version=7),
        lambda: board.move_task(1, "app", expected_version=7),
        lambda: board.rename_task(1, "", expected_version=7),
        lambda: board.set_due_day(1, -1, expected_version=7),
    ):
        with pytest.raises(VersionConflict):
            call()


def test_versions_other_tasks_are_not_touched(board):
    board.move_task(1, "app")
    board.add_task("app", "new", 1)
    assert [board.get_version(t) for t in (1, 2, 3)] == [2, 1, 1]


def test_versions_conflict_is_a_board_error():
    assert issubclass(VersionConflict, BoardError)
