"""Public checks for the c_archive change (archiving and restoring tasks).
Shown to the editor, never to the writer.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_archive/public/test_archive_public.py
"""

from board import Board


def test_archive_takes_a_task_off_the_board():
    b = Board()
    b.add_project("web")
    first = b.add_task("web", "home", 2)
    second = b.add_task("web", "about", 3)
    b.archive(first)
    assert b.is_archived(first)
    assert b.get_open_tasks("web") == [second]
    assert b.get_archived("web") == [first]
    assert b.get_version(first) == 2


def test_archive_restore_puts_the_task_back_at_the_end():
    b = Board()
    b.add_project("web")
    first = b.add_task("web", "home", 2)
    second = b.add_task("web", "about", 3)
    b.archive(first)
    b.restore(first)
    assert not b.is_archived(first)
    assert b.get_open_tasks("web") == [second, first]
    assert b.get_archived("web") == []
