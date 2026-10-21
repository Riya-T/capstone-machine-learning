"""Hidden tests for the c_open_limit change (adjustable open-task limits).
Never shown to the writer or the editor.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_open_limit/private/test_open_limit_new.py
"""

import pytest
from board import Board, BoardError

BAD_LIMITS = [0, -2, 2.5, "3", True]


@pytest.fixture
def board():
    b = Board()
    b.add_project("web")
    b.add_project("big", open_limit=8)
    return b


def state(b):
    tasks, task_id = [], 1
    while True:
        try:
            tasks.append(b.get_task(task_id))
        except KeyError:
            break
        task_id += 1
    projects = b.get_projects()
    return (
        projects,
        {p: (b.get_open_tasks(p), b.get_open_limit(p)) for p in projects},
        tasks,
    )


def fill(b, project, count, day=1):
    return [b.add_task(project, f"{project} {n}", day) for n in range(count)]


def test_open_limit_defaults_to_five_and_the_board_value():
    plain = Board()
    plain.add_project("web")
    assert plain.get_open_limit("web") == 5
    strict = Board(open_limit=3)
    strict.add_project("web")
    strict.add_project("big", open_limit=6)
    strict.add_project("auto", open_limit=None)
    assert [strict.get_open_limit(p) for p in ["web", "big", "auto"]] == [3, 6, 3]


def test_open_limit_adding_uses_each_projects_own_limit(board):
    fill(board, "big", 8)
    with pytest.raises(BoardError):
        board.add_task("big", "ninth", 1)
    fill(board, "web", 5)
    before = state(board)
    with pytest.raises(BoardError):
        board.add_task("web", "sixth", 1)
    assert state(board) == before


def test_open_limit_moving_uses_the_target_projects_limit():
    b = Board(open_limit=2)
    b.add_project("small")
    b.add_project("tiny", open_limit=1)
    b.add_project("big", open_limit=4)
    fill(b, "small", 2)
    b.add_task("tiny", "only", 1)
    before = state(b)
    with pytest.raises(BoardError):
        b.move_task(1, "tiny")
    assert state(b) == before
    b.move_task(3, "big")
    b.move_task(1, "big")
    assert b.get_open_tasks("big") == [3, 1]


@pytest.mark.parametrize("limit", BAD_LIMITS + [None])
def test_open_limit_invalid_board_limits_are_rejected(limit):
    with pytest.raises(ValueError):
        Board(open_limit=limit)


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_open_limit_invalid_project_limits_add_no_project(board, limit):
    before = state(board)
    with pytest.raises(ValueError):
        board.add_project("ops", open_limit=limit)
    assert state(board) == before


def test_open_limit_a_bad_limit_is_reported_before_an_existing_project(board):
    with pytest.raises(ValueError):
        board.add_project("web", open_limit=0)
    assert board.get_open_limit("web") == 5


def test_open_limit_unknown_projects_raise_key_error(board):
    with pytest.raises(KeyError):
        board.get_open_limit("ops")
    with pytest.raises(KeyError):
        board.set_open_limit("ops", 3)
    with pytest.raises(KeyError):
        board.set_open_limit("ops", 0)
    with pytest.raises(KeyError):
        board.get_open_limit(None)


def test_open_limit_can_be_replaced(board):
    board.set_open_limit("web", 2)
    assert board.get_open_limit("web") == 2
    fill(board, "web", 2)
    with pytest.raises(BoardError):
        board.add_task("web", "third", 1)
    assert board.get_open_limit("big") == 8


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_open_limit_invalid_values_are_rejected_when_setting(board, limit):
    before = state(board)
    with pytest.raises(ValueError):
        board.set_open_limit("web", limit)
    assert state(board) == before


def test_open_limit_below_the_open_tasks_is_rejected(board):
    fill(board, "web", 3)
    before = state(board)
    with pytest.raises(BoardError):
        board.set_open_limit("web", 2)
    assert state(board) == before
    board.set_open_limit("web", 3)  # exactly the open tasks
    assert board.get_open_limit("web") == 3


def test_open_limit_ignores_done_tasks_when_lowered(board):
    fill(board, "web", 3)
    board.complete(1)
    board.complete(2)
    board.set_open_limit("web", 1)
    with pytest.raises(BoardError):
        board.add_task("web", "more", 1)


def test_open_limit_a_bad_value_is_reported_before_the_open_count(board):
    fill(board, "web", 3)
    with pytest.raises(ValueError):
        board.set_open_limit("web", 0)


def test_open_limit_raised_limit_makes_room(board):
    fill(board, "web", 5)
    board.set_open_limit("web", 6)
    assert board.add_task("web", "sixth", 1) == 6
    assert len(board.get_open_tasks("web")) == 6
