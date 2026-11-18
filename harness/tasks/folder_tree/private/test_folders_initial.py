"""Hidden tests for the initial folder_tree spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with folders.py importable, e.g. in the sandbox):
    python -m pytest private/test_folders_initial.py
"""

import pytest
from folders import FolderError, FolderTree


@pytest.fixture
def tree():
    # root: notes.txt, [docs, music]; docs: readme.txt, [work, home];
    # work: plan.txt, budget.xls
    t = FolderTree()
    t.add_folder("docs", "root")
    t.add_folder("music", "root")
    t.add_folder("work", "docs")
    t.add_folder("home", "docs")
    t.add_file("docs", "readme.txt")
    t.add_file("work", "plan.txt")
    t.add_file("work", "budget.xls")
    t.add_file("root", "notes.txt")
    return t


def state(t):
    """Every folder, from the root down, with its parent, files and
    subfolders, to check that a failed call changed nothing."""
    out, todo = [], ["root"]
    while todo:
        name = todo.pop(0)
        subfolders = t.get_subfolders(name)
        out.append((name, t.get_parent(name), t.get_files(name), subfolders))
        todo.extend(subfolders)
    return out


# --- folders --------------------------------------------------------------------


def test_folders_and_files_are_listed_in_the_order_they_came(tree):
    assert state(tree) == [
        ("root", None, ["notes.txt"], ["docs", "music"]),
        ("docs", "root", ["readme.txt"], ["work", "home"]),
        ("music", "root", [], []),
        ("work", "docs", ["plan.txt", "budget.xls"], []),
        ("home", "docs", [], []),
    ]


@pytest.mark.parametrize("name", ["docs", "work", "root"])
def test_adding_a_folder_name_in_use_is_rejected(tree, name):
    before = state(tree)
    with pytest.raises(FolderError):
        tree.add_folder(name, "music")
    assert state(tree) == before


FOLDER_CALLS = [
    lambda t, x: t.add_folder("pics", x),
    lambda t, x: t.add_file(x, "photo.jpg"),
    lambda t, x: t.move_folder(x, "music"),
    lambda t, x: t.move_folder("work", x),
    lambda t, x: t.delete_folder(x),
    lambda t, x: t.get_files(x),
    lambda t, x: t.get_subfolders(x),
    lambda t, x: t.get_parent(x),
]


@pytest.mark.parametrize("call", FOLDER_CALLS)
def test_folders_never_added_raise_key_error(tree, call):
    before = state(tree)
    with pytest.raises(KeyError):
        call(tree, "attic")
    assert state(tree) == before


@pytest.mark.parametrize("call", FOLDER_CALLS)
def test_a_deleted_folder_is_not_in_the_tree(tree, call):
    tree.delete_folder("home")
    before = state(tree)
    with pytest.raises(KeyError):
        call(tree, "home")
    assert state(tree) == before


# --- files ----------------------------------------------------------------------


def test_add_file_puts_it_after_the_folders_other_files(tree):
    tree.add_file("work", "memo.txt")
    tree.add_file("music", "song.mp3")
    assert tree.get_files("work") == ["plan.txt", "budget.xls", "memo.txt"]
    assert tree.get_files("music") == ["song.mp3"]


def test_remove_file_keeps_the_order_of_the_others(tree):
    tree.add_file("work", "memo.txt")
    tree.remove_file("budget.xls")
    assert tree.get_files("work") == ["plan.txt", "memo.txt"]
    tree.remove_file("notes.txt")
    assert tree.get_files("root") == []


def test_removing_a_file_that_is_not_there_raises_key_error(tree):
    tree.remove_file("plan.txt")
    before = state(tree)
    with pytest.raises(KeyError):
        tree.remove_file("plan.txt")
    with pytest.raises(KeyError):
        tree.remove_file("photo.jpg")
    assert state(tree) == before


# --- move_folder ----------------------------------------------------------------


def test_move_folder_goes_after_the_other_subfolders(tree):
    tree.move_folder("music", "docs")
    assert tree.get_subfolders("root") == ["docs"]
    assert tree.get_subfolders("docs") == ["work", "home", "music"]
    assert tree.get_parent("music") == "docs"


def test_move_folder_takes_everything_inside_along(tree):
    tree.add_folder("2024", "work")
    tree.add_file("2024", "march.txt")
    tree.move_folder("work", "music")
    assert state(tree) == [
        ("root", None, ["notes.txt"], ["docs", "music"]),
        ("docs", "root", ["readme.txt"], ["home"]),
        ("music", "root", [], ["work"]),
        ("home", "docs", [], []),
        ("work", "music", ["plan.txt", "budget.xls"], ["2024"]),
        ("2024", "work", ["march.txt"], []),
    ]


def test_a_moved_folder_can_move_again(tree):
    tree.move_folder("work", "root")
    tree.move_folder("home", "work")
    tree.move_folder("work", "music")
    assert tree.get_subfolders("root") == ["docs", "music"]
    assert tree.get_subfolders("music") == ["work"]
    assert tree.get_subfolders("work") == ["home"]
    assert tree.get_subfolders("docs") == []


@pytest.mark.parametrize(
    "name, new_parent", [("docs", "docs"), ("work", "work"), ("root", "music"), ("root", "root")]
)
def test_moving_root_or_into_itself_is_rejected(tree, name, new_parent):
    before = state(tree)
    with pytest.raises(ValueError):
        tree.move_folder(name, new_parent)
    assert state(tree) == before


# --- delete_folder --------------------------------------------------------------
# What happens to the files of a deleted folder is unspecified, so these tests
# never look at the deleted folder's files or at its parent's files after a
# delete of a folder that held files.


def test_delete_folder_removes_the_folder_from_the_tree(tree):
    tree.delete_folder("work")
    assert tree.get_subfolders("docs") == ["home"]
    assert tree.get_subfolders("root") == ["docs", "music"]
    assert tree.get_files("root") == ["notes.txt"]
    assert tree.get_files("home") == []
    assert tree.get_parent("home") == "docs"


def test_delete_folder_of_an_empty_folder(tree):
    tree.delete_folder("home")
    assert state(tree) == [
        ("root", None, ["notes.txt"], ["docs", "music"]),
        ("docs", "root", ["readme.txt"], ["work"]),
        ("music", "root", [], []),
        ("work", "docs", ["plan.txt", "budget.xls"], []),
    ]


def test_the_parents_other_subfolders_keep_their_order_after_a_delete(tree):
    tree.add_folder("pics", "root")
    tree.add_folder("films", "root")
    tree.delete_folder("pics")
    assert tree.get_subfolders("root") == ["docs", "music", "films"]
    tree.delete_folder("music")
    assert tree.get_subfolders("root") == ["docs", "films"]


def test_a_tree_can_be_emptied_by_deletes(tree):
    tree.delete_folder("work")
    tree.delete_folder("home")
    tree.delete_folder("docs")
    tree.delete_folder("music")
    assert tree.get_subfolders("root") == []
    tree.add_folder("pics", "root")
    tree.add_file("pics", "photo.jpg")
    assert tree.get_subfolders("root") == ["pics"]
    assert tree.get_files("pics") == ["photo.jpg"]


def test_folders_and_files_elsewhere_keep_working_after_a_delete(tree):
    tree.delete_folder("work")
    tree.add_file("home", "todo.txt")
    tree.move_folder("home", "music")
    tree.remove_file("notes.txt")
    assert tree.get_files("home") == ["todo.txt"]
    assert tree.get_subfolders("music") == ["home"]
    assert tree.get_files("root") == []


def test_the_root_cannot_be_deleted(tree):
    before = state(tree)
    with pytest.raises(ValueError):
        tree.delete_folder("root")
    assert state(tree) == before


# --- general --------------------------------------------------------------------


def test_trees_do_not_share_folders():
    first, second = FolderTree(), FolderTree()
    first.add_folder("docs", "root")
    first.add_file("root", "notes.txt")
    assert second.get_subfolders("root") == []
    second.add_folder("docs", "root")
    second.add_file("root", "notes.txt")
    assert first.get_files("root") == ["notes.txt"]
