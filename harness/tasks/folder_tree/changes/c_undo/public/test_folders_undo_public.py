"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with folders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_folders_undo_public.py
"""

import pytest
from folders import FolderError, FolderTree


@pytest.fixture
def tree():
    t = FolderTree()
    t.add_folder("docs", "root")
    t.add_folder("music", "root")
    return t


def test_undo_takes_back_the_last_file_added(tree):
    tree.add_file("docs", "plan.txt")
    tree.add_file("docs", "budget.xls")
    tree.undo()
    assert tree.get_files("docs") == ["plan.txt"]
    tree.undo()
    assert tree.get_files("docs") == []


def test_undo_takes_back_a_move_of_an_empty_folder(tree):
    tree.add_folder("work", "docs")
    tree.move_folder("work", "music")
    tree.undo()
    assert tree.get_subfolders("docs") == ["work"]
    assert tree.get_subfolders("music") == []
    assert tree.get_parent("work") == "docs"


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(FolderError):
        FolderTree().undo()
