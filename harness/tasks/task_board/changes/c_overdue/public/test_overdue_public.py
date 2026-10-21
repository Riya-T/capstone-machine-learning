"""Public checks for the c_overdue change (due-day queries).
Shown to the editor, never to the writer.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_overdue/public/test_overdue_public.py
"""

from board import Board


def test_overdue_lists_open_tasks_due_before_today():
    b = Board()
    b.add_project("web")
    b.add_task("web", "home", 6)
    b.add_task("web", "about", 2)
    b.add_task("web", "blog", 9)
    assert b.get_overdue(7) == [2, 1]
    b.complete(2)
    assert b.get_overdue(7) == [1]


def test_overdue_due_on_one_day():
    b = Board()
    b.add_project("web")
    b.add_project("app")
    b.add_task("app", "login", 3)
    b.add_task("web", "home", 3)
    b.add_task("web", "about", 4)
    assert b.get_due_on(3) == [1, 2]
    assert b.get_due_on(3, project="web") == [2]
