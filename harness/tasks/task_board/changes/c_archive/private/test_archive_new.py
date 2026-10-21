"""Hidden tests for the c_archive change (archiving and restoring tasks).
Never shown to the writer or the editor.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_archive/private/test_archive_new.py
"""

import pytest
from board import Board, BoardError, VersionConflict


@pytest.fixture
def board():
    b = Board()
    b.add_project("web")
    b.add_project("app")
    b.add_task("web", "home", 2)
    b.add_task("web", "about", 4)
    b.add_task("app", "login", 1)
    return b


def state(b):
    tasks, task_id = [], 1
    while True:
        try:
            tasks.append((b.get_task(task_id), b.get_version(task_id), b.is_archived(task_id)))
        except KeyError:
            break
        task_id += 1
    projects = b.get_projects()
    return {p: (b.get_open_tasks(p), b.get_archived(p)) for p in projects}, tasks


def test_archive_nothing_is_archived_at_first(board):
    assert not board.is_archived(1)
    assert board.get_archived("web") == []


def test_archive_keeps_the_task_readable(board):
    board.archive(1)
    assert board.get_task(1) == ("web", "home", 2, False)
    assert board.get_open_tasks("web") == [2]
    assert board.get_archived("app") == []


def test_archive_frees_a_place_under_the_limit(board):
    for n in range(3):
        board.add_task("web", f"more {n}", 1)
    board.archive(2)
    assert board.add_task("web", "fits now", 1) == 7
    assert board.get_open_tasks("web") == [1, 4, 5, 6, 7]


def test_archive_and_restore_a_done_task(board):
    board.complete(2)
    board.archive(2)
    assert board.get_archived("web") == [2]
    assert board.get_open_tasks("web") == [1]
    board.restore(2)
    assert board.get_task(2) == ("web", "about", 4, True)
    assert board.get_open_tasks("web") == [1]


def test_archive_lists_tasks_in_archiving_order(board):
    board.archive(2)
    board.archive(1)
    assert board.get_archived("web") == [2, 1]
    board.restore(2)
    assert board.get_archived("web") == [1]


def test_archive_twice_or_restore_unarchived_is_rejected(board):
    board.archive(1)
    before = state(board)
    with pytest.raises(BoardError):
        board.archive(1)
    with pytest.raises(BoardError):
        board.restore(2)
    assert state(board) == before


def test_archive_restore_into_a_full_project_is_rejected(board):
    board.archive(1)
    for n in range(4):
        board.add_task("web", f"more {n}", 1)
    before = state(board)
    with pytest.raises(BoardError):
        board.restore(1)
    assert state(board) == before
    assert board.is_archived(1)


def test_archive_restore_uses_the_projects_own_limit():
    b = Board()
    b.add_project("tiny", open_limit=1)
    b.add_task("tiny", "first", 1)
    b.archive(1)
    b.add_task("tiny", "second", 1)
    with pytest.raises(BoardError):
        b.restore(1)
    b.complete(2)
    b.restore(1)
    assert b.get_open_tasks("tiny") == [1]


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.complete(1),
        lambda b: b.move_task(1, "app"),
        lambda b: b.rename_task(1, "new"),
        lambda b: b.set_due_day(1, 9),
    ],
    ids=["complete", "move_task", "rename_task", "set_due_day"],
)
def test_archive_blocks_changes_to_the_task(board, call):
    board.archive(1)
    before = state(board)
    with pytest.raises(BoardError):
        call(board)
    assert state(board) == before


def test_archive_check_comes_after_key_and_version_errors(board):
    board.archive(1)
    with pytest.raises(KeyError):
        board.move_task(1, "ops")
    with pytest.raises(VersionConflict):
        board.complete(1, expected_version=1)
    with pytest.raises(VersionConflict):
        board.archive(1, expected_version=1)


def test_archive_check_comes_before_value_errors(board):
    board.archive(1)
    for call in (
        lambda: board.rename_task(1, ""),
        lambda: board.set_due_day(1, -1),
        lambda: board.move_task(1, "web"),
    ):
        with pytest.raises(BoardError):
            call()


def test_archive_and_restore_count_as_changes(board):
    board.archive(1, expected_version=1)
    board.restore(1, expected_version=2)
    assert board.get_version(1) == 3
    before = state(board)
    with pytest.raises(VersionConflict):
        board.archive(1, expected_version=2)
    board.archive(1)
    with pytest.raises(VersionConflict):
        board.restore(1, expected_version=3)
    assert board.is_archived(1)
    assert board.get_version(1) == 4
    assert before[1][0][1] == 3


def test_archive_unknown_tasks_and_projects_raise_key_error(board):
    for call in (
        lambda: board.archive(99),
        lambda: board.restore(99),
        lambda: board.is_archived(99),
        lambda: board.archive(None),
        lambda: board.get_archived("ops"),
        lambda: board.restore(99, expected_version=1),
    ):
        with pytest.raises(KeyError):
            call()


def test_archive_a_restored_task_can_be_changed_again(board):
    board.archive(3)
    board.restore(3)
    board.move_task(3, "web")
    board.complete(3)
    assert board.get_task(3) == ("web", "login", 1, True)
    assert board.get_version(3) == 5
