"""Hidden tests for the c_lookup change (files below a folder, and the
folder of a file). Never shown to the writer or the editor.

Usage (with folders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lookup/private/test_folders_lookup_new.py
"""

import pytest
from folders import FolderTree


@pytest.fixture
def tree():
    # root: notes.txt, [docs, music]; docs: readme.txt, [work, home];
    # work: plan.txt, budget.xls; home: [], [2024]; 2024: march.txt;
    # music: song.mp3
    t = FolderTree()
    t.add_folder("docs", "root")
    t.add_folder("music", "root")
    t.add_folder("work", "docs")
    t.add_folder("home", "docs")
    t.add_folder("2024", "home")
    t.add_file("music", "song.mp3")
    t.add_file("docs", "readme.txt")
    t.add_file("work", "plan.txt")
    t.add_file("2024", "march.txt")
    t.add_file("work", "budget.xls")
    t.add_file("root", "notes.txt")
    return t


def state(t):
    out, todo = [], ["root"]
    while todo:
        name = todo.pop(0)
        subfolders = t.get_subfolders(name)
        out.append((name, t.get_parent(name), t.get_files(name), subfolders))
        todo.extend(subfolders)
    return out


ALL_FROM_ROOT = ["notes.txt", "readme.txt", "plan.txt", "budget.xls", "march.txt", "song.mp3"]


# --- get_all_files --------------------------------------------------------------


def test_lookup_all_files_from_the_root(tree):
    assert tree.get_all_files("root") == ALL_FROM_ROOT


@pytest.mark.parametrize(
    "folder, files",
    [
        ("docs", ["readme.txt", "plan.txt", "budget.xls", "march.txt"]),
        ("work", ["plan.txt", "budget.xls"]),
        ("home", ["march.txt"]),
        ("2024", ["march.txt"]),
        ("music", ["song.mp3"]),
    ],
)
def test_lookup_all_files_from_each_folder(tree, folder, files):
    assert tree.get_all_files(folder) == files


def test_lookup_all_files_of_an_empty_folder(tree):
    tree.add_folder("pics", "music")
    assert tree.get_all_files("pics") == []
    assert tree.get_all_files("root") == ALL_FROM_ROOT


def test_lookup_all_files_after_moves_and_deletes(tree):
    tree.move_folder("work", "music")
    assert tree.get_all_files("root") == [
        "notes.txt", "readme.txt", "march.txt", "song.mp3", "plan.txt", "budget.xls",
    ]  # fmt: skip
    tree.add_folder("pics", "docs")
    tree.delete_folder("pics")  # held no files
    assert tree.get_all_files("docs") == ["readme.txt", "march.txt"]
    tree.remove_file("plan.txt")
    tree.add_file("2024", "april.txt")
    assert tree.get_all_files("root") == [
        "notes.txt", "readme.txt", "march.txt", "april.txt", "song.mp3", "budget.xls",
    ]  # fmt: skip


@pytest.mark.parametrize("folder", ["attic", "2024"])
def test_lookup_all_files_of_a_folder_not_in_the_tree(tree, folder):
    tree.delete_folder("2024")
    with pytest.raises(KeyError):
        tree.get_all_files(folder)


# --- get_folder_of --------------------------------------------------------------


@pytest.mark.parametrize(
    "file, folder",
    [
        ("notes.txt", "root"),
        ("readme.txt", "docs"),
        ("plan.txt", "work"),
        ("budget.xls", "work"),
        ("march.txt", "2024"),
        ("song.mp3", "music"),
    ],
)
def test_lookup_folder_of_each_file(tree, file, folder):
    assert tree.get_folder_of(file) == folder


def test_lookup_folder_of_a_file_after_a_delete_elsewhere(tree):
    tree.delete_folder("2024")
    assert tree.get_folder_of("plan.txt") == "work"
    assert tree.get_folder_of("readme.txt") == "docs"
    assert tree.get_folder_of("song.mp3") == "music"
    tree.add_file("home", "april.txt")
    assert tree.get_folder_of("april.txt") == "home"


def test_lookup_folder_of_a_file_in_a_moved_folder(tree):
    tree.move_folder("home", "music")
    assert tree.get_folder_of("march.txt") == "2024"
    assert tree.get_folder_of("song.mp3") == "music"


def test_lookup_folder_of_a_file_that_is_not_there(tree):
    tree.remove_file("song.mp3")
    for file in ["song.mp3", "photo.jpg"]:
        with pytest.raises(KeyError):
            tree.get_folder_of(file)


def test_lookups_change_nothing(tree):
    before = state(tree)
    tree.get_all_files("root")
    tree.get_all_files("work")
    tree.get_folder_of("plan.txt")
    assert state(tree) == before
