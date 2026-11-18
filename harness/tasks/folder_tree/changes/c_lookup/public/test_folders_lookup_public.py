"""Public checks for the c_lookup change (files below a folder, and the
folder of a file). Shown to the editor, never to the writer.

Usage (with folders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lookup/public/test_folders_lookup_public.py
"""

import pytest
from folders import FolderTree


@pytest.fixture
def tree():
    t = FolderTree()
    t.add_folder("docs", "root")
    t.add_folder("work", "docs")
    t.add_file("work", "plan.txt")
    t.add_file("docs", "readme.txt")
    t.add_file("root", "notes.txt")
    return t


def test_all_files_lists_a_folders_own_files_first(tree):
    assert tree.get_all_files("root") == ["notes.txt", "readme.txt", "plan.txt"]
    assert tree.get_all_files("work") == ["plan.txt"]


def test_folder_of_a_file(tree):
    assert tree.get_folder_of("plan.txt") == "work"
    with pytest.raises(KeyError):
        tree.get_folder_of("photo.jpg")
