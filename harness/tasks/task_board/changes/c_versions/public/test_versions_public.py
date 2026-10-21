"""Public checks for the c_versions change (versioned task updates).
Shown to the editor, never to the writer.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/public/test_versions_public.py
"""

import pytest
from board import Board, VersionConflict


def test_versions_start_at_one_and_count_changes():
    b = Board()
    b.add_project("web")
    task_id = b.add_task("web", "home", 3)
    assert b.get_version(task_id) == 1
    b.rename_task(task_id, "home page")
    b.set_due_day(task_id, 4)
    assert b.get_version(task_id) == 3
    assert b.get_task(task_id) == ("web", "home page", 4, False)


def test_versions_a_stale_edit_is_refused():
    b = Board()
    b.add_project("web")
    task_id = b.add_task("web", "home", 3)
    b.rename_task(task_id, "home page", expected_version=1)
    with pytest.raises(VersionConflict):
        b.complete(task_id, expected_version=1)
    assert b.get_task(task_id)[3] is False
    b.complete(task_id, expected_version=2)
    assert b.get_version(task_id) == 3
