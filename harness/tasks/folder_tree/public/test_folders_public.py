"""Public checks for folders.py.

Usage (with folders.py importable, e.g. in the sandbox):
    python -m pytest public/test_folders_public.py
"""

import pytest
from folders import FolderError, FolderTree


@pytest.fixture
def tree():
    t = FolderTree()
    t.add_folder("docs", "root")
    t.add_folder("music", "root")
    return t


def test_a_new_tree_has_only_an_empty_root():
    t = FolderTree()
    assert t.get_subfolders("root") == []
    assert t.get_files("root") == []
    assert t.get_parent("root") is None


def test_folders_and_files_are_listed_in_the_order_added(tree):
    tree.add_folder("work", "docs")
    tree.add_file("docs", "plan.txt")
    tree.add_file("docs", "budget.xls")
    assert tree.get_subfolders("root") == ["docs", "music"]
    assert tree.get_subfolders("docs") == ["work"]
    assert tree.get_files("docs") == ["plan.txt", "budget.xls"]
    assert tree.get_parent("work") == "docs"


def test_a_folder_name_in_use_is_rejected(tree):
    with pytest.raises(FolderError):
        tree.add_folder("docs", "music")
    with pytest.raises(FolderError):
        tree.add_folder("root", "music")
    assert tree.get_subfolders("music") == []
    assert tree.get_subfolders("root") == ["docs", "music"]


def test_move_folder_takes_its_contents_along(tree):
    tree.add_folder("work", "docs")
    tree.add_file("work", "plan.txt")
    tree.move_folder("work", "music")
    assert tree.get_subfolders("docs") == []
    assert tree.get_subfolders("music") == ["work"]
    assert tree.get_parent("work") == "music"
    assert tree.get_files("work") == ["plan.txt"]
    with pytest.raises(ValueError):
        tree.move_folder("work", "work")


def test_delete_folder_removes_it_from_its_parent(tree):
    tree.add_folder("work", "docs")
    tree.add_folder("home", "docs")
    tree.add_folder("pics", "docs")
    tree.delete_folder("home")
    assert tree.get_subfolders("docs") == ["work", "pics"]
    assert tree.get_subfolders("root") == ["docs", "music"]
