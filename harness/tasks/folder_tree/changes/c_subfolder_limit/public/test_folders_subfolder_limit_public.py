"""Public checks for the c_subfolder_limit change (a limit on subfolders per
folder). Shown to the editor, never to the writer.

Usage (with folders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_subfolder_limit/public/test_folders_subfolder_limit_public.py
"""

import pytest
from folders import FolderFull, FolderTree


@pytest.fixture
def tree():
    t = FolderTree()
    t.add_folder("docs", "root", max_subfolders=2)
    t.add_folder("music", "root")
    return t


def test_the_limit_is_reported(tree):
    assert tree.get_max_subfolders("docs") == 2
    assert tree.get_max_subfolders("music") is None
    assert tree.get_max_subfolders("root") is None


def test_adding_a_folder_past_the_limit_raises(tree):
    tree.add_folder("work", "docs")
    tree.add_folder("home", "docs")
    with pytest.raises(FolderFull):
        tree.add_folder("pics", "docs")
    assert tree.get_subfolders("docs") == ["work", "home"]
