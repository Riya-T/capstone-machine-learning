"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

What delete_folder does with the files of the deleted folder is up to the
program, so these tests only compare the tree before a delete with the tree
after it is undone, never the tree right after a delete.

Usage (with folders.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_folders_undo_new.py
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
    out, todo = [], ["root"]
    while todo:
        name = todo.pop(0)
        subfolders = t.get_subfolders(name)
        out.append((name, t.get_parent(name), t.get_files(name), subfolders))
        todo.extend(subfolders)
    return out


# --- each call can be undone ------------------------------------------------


def test_undo_of_add_file_removes_it_and_frees_the_name(tree):
    before = state(tree)
    tree.add_file("music", "song.mp3")
    tree.undo()
    assert state(tree) == before
    tree.add_file("docs", "song.mp3")
    assert tree.get_files("docs") == ["readme.txt", "song.mp3"]


def test_undo_of_add_folder_removes_it_and_frees_the_name(tree):
    before = state(tree)
    tree.add_folder("pics", "music")
    tree.undo()
    assert state(tree) == before
    with pytest.raises(KeyError):
        tree.get_files("pics")
    tree.add_folder("pics", "root")
    assert tree.get_subfolders("root") == ["docs", "music", "pics"]


@pytest.mark.parametrize("file", ["plan.txt", "budget.xls", "readme.txt"])
def test_undo_of_remove_file_puts_it_back_in_its_place(tree, file):
    before = state(tree)
    tree.remove_file(file)
    tree.undo()
    assert state(tree) == before
    tree.remove_file(file)
    tree.undo()
    assert state(tree) == before


def test_undo_of_move_folder_puts_it_back_in_its_old_place(tree):
    before = state(tree)
    tree.move_folder("work", "music")
    tree.undo()
    assert state(tree) == before
    assert tree.get_subfolders("docs") == ["work", "home"]


def test_undo_of_move_folder_brings_everything_inside_back(tree):
    tree.add_folder("2024", "work")
    tree.add_file("2024", "march.txt")
    before = state(tree)
    tree.move_folder("docs", "music")
    tree.undo()
    assert state(tree) == before
    assert tree.get_parent("docs") == "root"


def test_undo_of_delete_folder_brings_it_back_with_its_files(tree):
    before = state(tree)
    tree.delete_folder("work")
    tree.undo()
    assert state(tree) == before
    assert tree.get_subfolders("docs") == ["work", "home"]
    assert tree.get_files("work") == ["plan.txt", "budget.xls"]
    tree.remove_file("plan.txt")
    assert tree.get_files("work") == ["budget.xls"]


def test_undo_of_delete_folder_keeps_its_place_among_the_subfolders(tree):
    tree.add_folder("pics", "root")
    tree.add_file("music", "song.mp3")
    before = state(tree)
    tree.delete_folder("music")
    assert tree.get_subfolders("root") == ["docs", "pics"]
    tree.undo()
    assert tree.get_subfolders("root") == ["docs", "music", "pics"]
    assert state(tree) == before


def test_undo_makes_a_deleted_folder_usable_again(tree):
    tree.delete_folder("work")
    tree.undo()
    tree.add_file("work", "memo.txt")
    assert tree.get_files("work") == ["plan.txt", "budget.xls", "memo.txt"]
    with pytest.raises(FolderError):
        tree.add_folder("work", "music")
    tree.remove_file("plan.txt")
    assert tree.get_files("work") == ["budget.xls", "memo.txt"]
    assert tree.get_files("docs") == ["readme.txt"]
    tree.delete_folder("work")
    assert tree.get_subfolders("docs") == ["home"]


def test_undo_of_deleting_an_empty_folder(tree):
    before = state(tree)
    tree.delete_folder("home")
    tree.undo()
    assert state(tree) == before


def test_undo_of_a_move_then_a_delete(tree):
    tree.add_folder("pics", "root")
    before = state(tree)
    tree.move_folder("pics", "docs")
    tree.add_file("music", "song.mp3")
    middle = state(tree)
    tree.delete_folder("music")
    tree.undo()  # the delete: music is back, after docs
    assert state(tree) == middle
    assert tree.get_subfolders("root") == ["docs", "music"]
    tree.undo()  # the song
    tree.undo()  # the move: pics is back in root, last
    assert state(tree) == before
    assert tree.get_subfolders("docs") == ["work", "home"]


# --- what is and is not recorded --------------------------------------------


def test_undo_steps_back_one_call_at_a_time():
    t = FolderTree()
    calls = [
        lambda: t.add_folder("docs", "root"),
        lambda: t.add_folder("music", "root"),
        lambda: t.add_file("root", "notes.txt"),
        lambda: t.add_folder("work", "docs"),
        lambda: t.add_file("work", "plan.txt"),
        lambda: t.add_file("work", "budget.xls"),
        lambda: t.add_folder("home", "docs"),
        lambda: t.add_file("docs", "readme.txt"),
        lambda: t.move_folder("work", "music"),
        lambda: t.remove_file("plan.txt"),
        lambda: t.add_folder("2024", "home"),
        lambda: t.add_file("2024", "march.txt"),
        lambda: t.delete_folder("work"),
        lambda: t.move_folder("home", "music"),
        lambda: t.delete_folder("2024"),
        lambda: t.remove_file("notes.txt"),
        lambda: t.delete_folder("docs"),
    ]
    states = [state(t)]
    for call in calls:
        call()
        states.append(state(t))
    assert t.get_subfolders("root") == ["music"]
    assert t.get_subfolders("music") == ["home"]
    assert t.get_subfolders("home") == []
    for expected in reversed(states[:-1]):
        t.undo()
        assert state(t) == expected
    with pytest.raises(FolderError):
        t.undo()
    assert state(t) == [("root", None, [], [])]


def test_undo_skips_calls_that_raised(tree):
    tree.add_file("music", "song.mp3")
    for call in (
        lambda: tree.add_folder("docs", "music"),
        lambda: tree.add_folder("pics", "attic"),
        lambda: tree.add_file("attic", "photo.jpg"),
        lambda: tree.remove_file("photo.jpg"),
        lambda: tree.move_folder("docs", "docs"),
        lambda: tree.move_folder("root", "music"),
        lambda: tree.move_folder("attic", "music"),
        lambda: tree.delete_folder("root"),
        lambda: tree.delete_folder("attic"),
    ):
        with pytest.raises((ValueError, KeyError, FolderError)):
            call()
    tree.undo()  # the song
    assert tree.get_files("music") == []
    assert tree.get_files("root") == ["notes.txt"]


def test_undo_ignores_get_calls(tree):
    tree.add_file("music", "song.mp3")
    tree.get_files("music")
    tree.get_subfolders("music")
    tree.get_parent("music")
    tree.undo()
    assert tree.get_files("music") == []
    assert tree.get_files("root") == ["notes.txt"]


def test_undo_has_no_redo():
    t = FolderTree()
    t.add_folder("docs", "root")
    t.add_file("docs", "plan.txt")
    t.undo()
    t.undo()
    assert state(t) == [("root", None, [], [])]
    with pytest.raises(FolderError):
        t.undo()


def test_undo_after_new_calls_takes_back_the_new_calls_first(tree):
    tree.add_file("music", "song.mp3")
    tree.undo()
    tree.add_file("music", "tune.mp3")
    tree.undo()
    assert tree.get_files("music") == []
    tree.undo()  # notes.txt, the fixture's last call
    assert tree.get_files("root") == []
    assert tree.get_files("work") == ["plan.txt", "budget.xls"]


def test_undo_with_nothing_left_raises_and_changes_nothing():
    t = FolderTree()
    with pytest.raises(FolderError):
        t.undo()
    t.add_folder("docs", "root")
    t.undo()
    with pytest.raises(FolderError):
        t.undo()
    assert state(t) == [("root", None, [], [])]
    t.add_folder("docs", "root")
    t.add_file("docs", "plan.txt")
    assert t.get_files("docs") == ["plan.txt"]


def test_undo_of_the_whole_fixture(tree):
    for _ in range(8):
        tree.undo()
    assert state(tree) == [("root", None, [], [])]
    with pytest.raises(FolderError):
        tree.undo()


def test_undo_restores_the_parent_that_later_calls_use(tree):
    tree.move_folder("work", "music")
    tree.undo()
    assert tree.get_parent("work") == "docs"
    tree.delete_folder("work")
    assert tree.get_subfolders("docs") == ["home"]
    assert tree.get_subfolders("music") == []
