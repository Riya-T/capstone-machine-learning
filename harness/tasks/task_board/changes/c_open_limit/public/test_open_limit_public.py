"""Public checks for the c_open_limit change (adjustable open-task limits).
Shown to the editor, never to the writer.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_open_limit/public/test_open_limit_public.py
"""

import pytest
from board import Board, BoardError


def test_open_limit_set_for_the_whole_board():
    b = Board(open_limit=2)
    b.add_project("web")
    b.add_task("web", "home", 1)
    b.add_task("web", "about", 1)
    with pytest.raises(BoardError):
        b.add_task("web", "blog", 1)
    assert b.get_open_limit("web") == 2


def test_open_limit_of_one_project_overrides_the_board():
    b = Board()
    b.add_project("big", open_limit=7)
    b.add_project("web")
    ids = [b.add_task("big", f"task {n}", 1) for n in range(7)]
    assert b.get_open_tasks("big") == ids
    assert b.get_open_limit("web") == 5
