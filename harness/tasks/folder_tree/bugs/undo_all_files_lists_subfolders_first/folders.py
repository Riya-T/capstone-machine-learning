"""Folder tree with lookups of every file below a folder and of a file's
folder, and undo.

Planted bug (after c_lookup and c_undo): undo was added correctly, but
get_all_files, rewritten while the storage was reworked, collects the files
of a folder's subfolders before the folder's own files.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from folders import FolderTree
    tree = FolderTree()
    tree.add_folder("docs", "root")
    tree.add_file("docs", "plan.txt")
    tree.undo()  # docs is empty again
"""

import copy

ROOT = "root"


class FolderError(Exception):
    pass


def check_name(name, what):
    if not isinstance(name, str) or not name:
        raise ValueError(f"{what} name must be a non-empty str, got {name!r}")


class FolderTree:
    def __init__(self):
        # folder name -> {"parent": name or None, "files": [...], "subfolders": [...]}
        self._folders = {ROOT: {"parent": None, "files": [], "subfolders": []}}
        self._file_folder = {}  # file name -> name of the folder holding it
        self._undo_stack = []  # copies of the state as it was before each call

    def add_folder(self, name, parent):
        self._require_folder(parent)
        check_name(name, "folder")
        if name in self._folders:
            raise FolderError(f"folder name {name!r} is already used")
        self._save()
        self._folders[name] = {"parent": parent, "files": [], "subfolders": []}
        self._folders[parent]["subfolders"].append(name)

    def add_file(self, folder, file):
        self._require_folder(folder)
        check_name(file, "file")
        if file in self._file_folder:
            raise FolderError(f"file name {file!r} is already used")
        self._save()
        self._folders[folder]["files"].append(file)
        self._file_folder[file] = folder

    def remove_file(self, file):
        if not isinstance(file, str) or file not in self._file_folder:
            raise KeyError(file)
        self._save()
        folder = self._file_folder.pop(file)
        self._folders[folder]["files"].remove(file)

    def move_folder(self, name, new_parent):
        self._require_folder(name)
        self._require_folder(new_parent)
        if name == ROOT:
            raise ValueError("the root folder cannot be moved")
        if self._is_inside(new_parent, name):
            raise ValueError(f"cannot move folder {name!r} into itself or a folder inside it")
        self._save()
        old_parent = self._folders[name]["parent"]
        self._folders[old_parent]["subfolders"].remove(name)
        self._folders[new_parent]["subfolders"].append(name)
        self._folders[name]["parent"] = new_parent

    def delete_folder(self, name):
        self._require_folder(name)
        if name == ROOT:
            raise ValueError("the root folder cannot be deleted")
        self._save()
        folder = self._folders.pop(name)
        parent = self._folders[folder["parent"]]
        parent["subfolders"].remove(name)
        parent["files"].extend(folder["files"])
        for file in folder["files"]:
            self._file_folder[file] = folder["parent"]
        parent["subfolders"].extend(folder["subfolders"])
        for sub in folder["subfolders"]:
            self._folders[sub]["parent"] = folder["parent"]

    def undo(self):
        if not self._undo_stack:
            raise FolderError("nothing to undo")
        self._folders, self._file_folder = self._undo_stack.pop()

    def get_files(self, folder):
        self._require_folder(folder)
        return list(self._folders[folder]["files"])

    def get_subfolders(self, folder):
        self._require_folder(folder)
        return list(self._folders[folder]["subfolders"])

    def get_parent(self, folder):
        self._require_folder(folder)
        return self._folders[folder]["parent"]

    def get_all_files(self, folder):
        self._require_folder(folder)
        files = []
        for sub in self._folders[folder]["subfolders"]:
            files.extend(self.get_all_files(sub))
        files.extend(self._folders[folder]["files"])
        return files

    def get_folder_of(self, file):
        if not isinstance(file, str) or file not in self._file_folder:
            raise KeyError(file)
        return self._file_folder[file]

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append(copy.deepcopy((self._folders, self._file_folder)))

    def _is_inside(self, folder, ancestor):
        # True if `folder` is `ancestor` or somewhere below it.
        while folder is not None:
            if folder == ancestor:
                return True
            folder = self._folders[folder]["parent"]
        return False

    def _require_folder(self, folder):
        # Non-str names are never stored, so they count as "not in the tree" too.
        if not isinstance(folder, str) or folder not in self._folders:
            raise KeyError(folder)
