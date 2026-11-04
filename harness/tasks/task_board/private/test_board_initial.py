"""Hidden tests for the initial task_board spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest private/test_board_initial.py
"""

import pytest
from board import Board, BoardError


@pytest.fixture
def board():
    b = Board()
    b.add_project("web")
    b.add_project("app")
    return b


def state(b):
    """Every project's open tasks and every task, to check that a failed call changed nothing."""
    tasks = []
    for task_id in range(1, 100):
        try:
            tasks.append(b.get_task(task_id))
        except KeyError:
            break
    return b.get_projects(), {p: b.get_open_tasks(p) for p in b.get_projects()}, tasks


def fill(b, project, count, day=1):
    return [b.add_task(project, f"{project} {n}", day) for n in range(count)]


# --- projects ---------------------------------------------------------------


def test_projects_are_listed_in_the_order_added():
    b = Board()
    for name in ["ops", "app", "web"]:
        b.add_project(name)
    assert b.get_projects() == ["ops", "app", "web"]
    assert b.get_open_tasks("ops") == []


def test_an_empty_project_name_is_rejected():
    b = Board()
    with pytest.raises(ValueError):
        b.add_project("")
    assert b.get_projects() == []


def test_adding_an_existing_project_is_rejected(board):
    board.add_task("web", "home", 2)
    before = state(board)
    with pytest.raises(BoardError):
        board.add_project("web")
    assert state(board) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.add_task("ops", "deploy", 1),
        lambda b: b.get_open_tasks("ops"),
        lambda b: b.get_open_tasks(None),
        lambda b: b.add_task(1, "deploy", 1),
    ],
)
def test_projects_that_do_not_exist_raise_key_error(board, call):
    board.add_task("web", "home", 2)
    before = state(board)
    with pytest.raises(KeyError):
        call(board)
    assert state(board) == before


# --- tasks ------------------------------------------------------------------


def test_a_new_task_is_open(board):
    task_id = board.add_task("app", "sign in", 0)
    assert task_id == 1
    assert board.get_task(task_id) == ("sign in", 0)
    assert board.get_open_tasks("app") == [1]
    assert board.get_open_tasks("web") == []


def test_ids_are_shared_by_all_projects(board):
    ids = [board.add_task(p, "t", 1) for p in ["web", "app", "app", "web"]]
    assert ids == [1, 2, 3, 4]
    assert board.get_open_tasks("web") == [1, 4]
    assert board.get_open_tasks("app") == [2, 3]


def test_an_empty_title_is_rejected(board):
    before = state(board)
    with pytest.raises(ValueError):
        board.add_task("web", "", 1)
    assert state(board) == before


@pytest.mark.parametrize("day", [-1, -7])
def test_due_days_below_zero_are_rejected(board, day):
    before = state(board)
    with pytest.raises(ValueError):
        board.add_task("web", "home", day)
    assert state(board) == before


def test_a_failed_add_uses_up_no_id(board):
    with pytest.raises(ValueError):
        board.add_task("web", "home", -1)
    with pytest.raises(KeyError):
        board.add_task("ops", "home", 1)
    assert board.add_task("web", "home", 1) == 1


@pytest.mark.parametrize("task_id", [0, 2, -1, None, "1"])
@pytest.mark.parametrize(
    "call",
    [
        lambda b, t: b.complete(t),
        lambda b, t: b.get_task(t),
        lambda b, t: b.move_task(t, "app"),
    ],
    ids=["complete", "get_task", "move_task"],
)
def test_tasks_that_do_not_exist_raise_key_error(board, call, task_id):
    board.add_task("web", "home", 2)
    before = state(board)
    with pytest.raises(KeyError):
        call(board, task_id)
    assert state(board) == before


def test_open_tasks_keep_their_order_when_one_is_done(board):
    fill(board, "web", 4)
    board.complete(2)
    board.complete(4)
    assert board.get_open_tasks("web") == [1, 3]
    assert board.get_task(2) == ("web 1", 1)
    assert board.get_task(3) == ("web 2", 1)


# --- full projects ----------------------------------------------------------


def test_the_sixth_open_task_is_rejected_and_changes_nothing(board):
    fill(board, "web", 5)
    before = state(board)
    with pytest.raises(BoardError):
        board.add_task("web", "extra", 1)
    assert state(board) == before
    assert board.add_task("app", "elsewhere", 1) == 6


def test_projects_fill_up_separately(board):
    fill(board, "web", 4)
    fill(board, "app", 5)
    assert board.add_task("web", "fifth", 1) == 10
    with pytest.raises(BoardError):
        board.add_task("web", "sixth", 1)
    assert board.get_open_tasks("web") == [1, 2, 3, 4, 10]


def test_moving_frees_a_place_in_the_old_project(board):
    fill(board, "web", 5)
    board.move_task(3, "app")
    assert board.add_task("web", "new", 1) == 6
    assert board.get_open_tasks("web") == [1, 2, 4, 5, 6]
    with pytest.raises(BoardError):
        board.add_task("web", "one more", 1)


# --- moving -----------------------------------------------------------------


def test_moving_takes_a_task_out_of_its_old_project(board):
    fill(board, "web", 3)
    board.add_task("app", "a", 1)
    board.move_task(2, "app")
    assert board.get_open_tasks("web") == [1, 3]
    assert board.get_open_tasks("app") == [4, 2]
    assert board.get_task(2) == ("web 1", 1)


def test_a_task_can_move_back(board):
    fill(board, "web", 3)
    board.move_task(1, "app")
    board.move_task(1, "web")
    assert board.get_open_tasks("web") == [2, 3, 1]
    assert board.get_open_tasks("app") == []


def test_boards_do_not_share_projects_or_ids():
    first, second = Board(), Board()
    first.add_project("web")
    first.add_task("web", "home", 1)
    assert second.get_projects() == []
    second.add_project("web")
    assert second.add_task("web", "home", 1) == 1
    assert second.get_open_tasks("web") == [1]
