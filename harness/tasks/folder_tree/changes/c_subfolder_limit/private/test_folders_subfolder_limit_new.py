"""Hidden tests for the c_subfolder_limit change (a limit on subfolders per
folder). Never shown to the writer or the editor.

Usage (with folders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_subfolder_limit/private/test_folders_subfolder_limit_new.py
"""

import pytest
from folders import FolderError, FolderFull, FolderTree


@pytest.fixture
def tree():
    # docs holds 2 subfolders of its 3, work (inside docs) 1 of its 1;
    # music, home, 2024 and root have no limit.
    t = FolderTree()
    t.add_folder("docs", "root", max_subfolders=3)
    t.add_folder("music", "root")
    t.add_folder("work", "docs", max_subfolders=1)
    t.add_folder("home", "docs")
    t.add_folder("2024", "work")
    t.add_file("work", "plan.txt")
    return t


def state(t):
    out, todo = [], ["root"]
    while todo:
        name = todo.pop(0)
        subfolders = t.get_subfolders(name)
        out.append((name, t.get_parent(name), t.get_files(name), subfolders))
        todo.extend(subfolders)
    return out


# --- the setting --------------------------------------------------------------


def test_limit_defaults_to_none(tree):
    tree.add_folder("pics", "root")
    assert tree.get_max_subfolders("pics") is None
    for i in range(12):
        tree.add_folder(f"album{i}", "pics")
    assert len(tree.get_subfolders("pics")) == 12


def test_limit_of_each_folder_is_its_own(tree):
    folders = ["root", "docs", "music", "work", "home", "2024"]
    assert [tree.get_max_subfolders(f) for f in folders] == [None, 3, None, 1, None, None]


@pytest.mark.parametrize("limit", [0, -2])
def test_limit_must_be_greater_than_0(tree, limit):
    before = state(tree)
    with pytest.raises(ValueError):
        tree.add_folder("pics", "music", max_subfolders=limit)
    assert state(tree) == before
    with pytest.raises(KeyError):
        tree.get_files("pics")


def test_limit_of_a_folder_not_in_the_tree_raises_key_error(tree):
    with pytest.raises(KeyError):
        tree.get_max_subfolders("attic")
    tree.delete_folder("2024")
    with pytest.raises(KeyError):
        tree.get_max_subfolders("2024")


def test_limit_error_is_a_folder_error():
    assert issubclass(FolderFull, FolderError)


# --- add_folder -----------------------------------------------------------------


def test_limit_can_be_filled_exactly(tree):
    tree.add_folder("pics", "docs")
    assert tree.get_subfolders("docs") == ["work", "home", "pics"]
    with pytest.raises(FolderFull):
        tree.add_folder("films", "docs")


def test_limit_refuses_a_folder_and_changes_nothing(tree):
    before = state(tree)
    with pytest.raises(FolderFull):
        tree.add_folder("2025", "work")
    assert state(tree) == before
    tree.add_folder("2025", "music")
    assert tree.get_subfolders("music") == ["2025"]


def test_limit_counts_only_folders_directly_inside(tree):
    tree.add_folder("pics", "home")
    tree.add_folder("films", "home")
    tree.add_folder("notes", "docs")  # docs: work, home, notes
    assert tree.get_subfolders("docs") == ["work", "home", "notes"]


def test_limit_frees_up_when_a_subfolder_is_deleted(tree):
    tree.delete_folder("2024")
    tree.add_folder("2025", "work")
    assert tree.get_subfolders("work") == ["2025"]


def test_limit_frees_up_when_a_subfolder_moves_out(tree):
    tree.move_folder("2024", "music")
    tree.add_folder("2025", "work")
    assert tree.get_subfolders("work") == ["2025"]
    assert tree.get_subfolders("music") == ["2024"]


def test_limit_never_applies_to_files(tree):
    for i in range(5):
        tree.add_file("work", f"memo{i}.txt")
    assert len(tree.get_files("work")) == 6


# --- move_folder ----------------------------------------------------------------


def test_limit_allows_a_move_that_fits(tree):
    tree.move_folder("music", "docs")
    assert tree.get_subfolders("docs") == ["work", "home", "music"]
    assert tree.get_subfolders("root") == ["docs"]


def test_limit_stops_a_move_into_a_full_folder(tree):
    before = state(tree)
    with pytest.raises(FolderFull):
        tree.move_folder("home", "work")
    assert state(tree) == before


def test_limit_stops_a_move_with_everything_inside_it(tree):
    tree.add_folder("albums", "music")
    tree.add_file("music", "song.mp3")
    tree.add_folder("pics", "docs")  # docs is full
    before = state(tree)
    with pytest.raises(FolderFull):
        tree.move_folder("music", "docs")
    assert state(tree) == before
    assert tree.get_parent("albums") == "music"


def test_limit_lets_a_refused_move_work_once_there_is_room(tree):
    with pytest.raises(FolderFull):
        tree.move_folder("home", "work")
    tree.delete_folder("2024")
    tree.move_folder("home", "work")
    assert tree.get_subfolders("work") == ["home"]
    assert tree.get_subfolders("docs") == ["work"]


def test_limit_moves_along_with_its_folder(tree):
    tree.move_folder("work", "music")
    assert tree.get_max_subfolders("work") == 1
    with pytest.raises(FolderFull):
        tree.add_folder("2025", "work")


def test_limit_is_not_checked_on_the_folder_a_subfolder_leaves(tree):
    tree.move_folder("2024", "root")
    assert tree.get_subfolders("root") == ["docs", "music", "2024"]
    assert tree.get_subfolders("work") == []


def test_limit_never_stops_delete_folder(tree):
    tree.add_folder("pics", "docs")  # docs is full
    tree.delete_folder("home")
    assert tree.get_subfolders("docs") == ["work", "pics"]
