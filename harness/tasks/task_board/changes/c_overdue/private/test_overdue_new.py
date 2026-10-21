"""Hidden tests for the c_overdue change (due-day queries).
Never shown to the writer or the editor.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_overdue/private/test_overdue_new.py
"""

import pytest
from board import Board


@pytest.fixture
def board():
    b = Board()
    b.add_project("web")
    b.add_project("app")
    for project, day in [("web", 5), ("web", 2), ("web", 8), ("app", 2), ("app", 0), ("app", 5)]:
        b.add_task(project, f"{project} due {day}", day)
    return b


def test_overdue_sorts_by_due_day_then_id(board):
    assert board.get_overdue(6) == [5, 2, 4, 1, 6]
    assert board.get_overdue(100) == [5, 2, 4, 1, 6, 3]


def test_overdue_excludes_tasks_due_today(board):
    assert board.get_overdue(5) == [5, 2, 4]
    assert board.get_overdue(0) == []
    assert board.get_overdue(1) == [5]


def test_overdue_never_lists_done_tasks(board):
    board.complete(2)
    board.complete(6)
    assert board.get_overdue(6) == [5, 4, 1]
    assert board.get_due_on(2) == [4]
    assert board.get_due_on(5) == [1]


def test_overdue_can_be_limited_to_a_project(board):
    assert board.get_overdue(6, "web") == [2, 1]
    assert board.get_overdue(6, project="app") == [5, 4, 6]
    assert board.get_overdue(6, project=None) == [5, 2, 4, 1, 6]


def test_overdue_follows_tasks_that_moved(board):
    board.move_task(3, "app")
    assert board.get_overdue(9, "app") == [5, 4, 6, 3]
    assert board.get_overdue(9, "web") == [2, 1]
    assert board.get_due_on(8, "app") == [3]
    assert board.get_due_on(8, "web") == []


def test_overdue_due_on_lists_ids_in_order(board):
    assert board.get_due_on(5) == [1, 6]
    assert board.get_due_on(2) == [2, 4]
    assert board.get_due_on(2, "app") == [4]
    assert board.get_due_on(3) == []


def test_overdue_an_empty_board_has_nothing_due():
    b = Board()
    assert b.get_overdue(10) == []
    assert b.get_due_on(0) == []
    b.add_project("web")
    assert b.get_overdue(10, "web") == []


@pytest.mark.parametrize("day", [-1, 1.5, "3", None, True])
def test_overdue_invalid_days_are_rejected(board, day):
    with pytest.raises(ValueError):
        board.get_overdue(day)
    with pytest.raises(ValueError):
        board.get_due_on(day)
    with pytest.raises(ValueError):
        board.get_overdue(day, "web")


def test_overdue_unknown_projects_raise_key_error_first(board):
    for call in (
        lambda: board.get_overdue(5, "ops"),
        lambda: board.get_due_on(5, "ops"),
        lambda: board.get_overdue(-1, "ops"),
        lambda: board.get_due_on("x", project="ops"),
    ):
        with pytest.raises(KeyError):
            call()


def test_overdue_queries_change_nothing(board):
    board.get_overdue(6)
    board.get_due_on(2, "web")
    assert board.get_open_tasks("web") == [1, 2, 3]
    assert board.get_open_tasks("app") == [4, 5, 6]
    assert board.get_task(5) == ("app", "app due 0", 0, False)
