"""Public checks for board.py.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest public/test_board_public.py
"""

import pytest
from board import Board, BoardError


@pytest.fixture
def board():
    b = Board()
    b.add_project("website")
    b.add_project("mobile")
    return b


def test_task_ids_count_up_over_all_projects(board):
    assert board.add_task("website", "landing page", 3) == 1
    assert board.add_task("mobile", "login screen", 5) == 2
    assert board.add_task("website", "contact form", 4) == 3
    assert board.get_task(2) == ("mobile", "login screen", 5, False)


def test_completing_a_task_marks_it_done(board):
    task_id = board.add_task("website", "landing page", 3)
    board.complete(task_id)
    assert board.get_task(task_id) == ("website", "landing page", 3, True)
    assert board.get_open_tasks("website") == []


def test_a_project_holds_at_most_five_open_tasks(board):
    for day in range(5):
        board.add_task("website", f"task {day}", day)
    with pytest.raises(BoardError):
        board.add_task("website", "one too many", 9)
    assert board.get_open_tasks("website") == [1, 2, 3, 4, 5]


def test_done_tasks_free_a_place(board):
    for day in range(5):
        board.add_task("website", f"task {day}", day)
    board.complete(2)
    assert board.add_task("website", "next one", 7) == 6
    assert board.get_open_tasks("website") == [1, 3, 4, 5, 6]


def test_a_moved_task_joins_the_end_of_its_new_project(board):
    board.add_task("mobile", "login screen", 5)
    board.add_task("website", "landing page", 3)
    board.move_task(2, "mobile")
    assert board.get_open_tasks("mobile") == [1, 2]
    assert board.get_task(2)[0] == "mobile"


def test_unknown_project_raises_key_error(board):
    with pytest.raises(KeyError):
        board.add_task("backend", "api", 1)
    assert board.get_projects() == ["website", "mobile"]
