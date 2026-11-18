# Folder tree

Write a module `folders.py` that keeps track of a tree of folders holding
files: which folders are inside which, and which files each folder holds,
in order, as folders and files are added, moved and removed.

## Interface

```python
class FolderError(Exception): ...


class FolderTree:
    def __init__(self): ...
    def add_folder(self, name: str, parent: str) -> None: ...
    def add_file(self, folder: str, file: str) -> None: ...
    def remove_file(self, file: str) -> None: ...
    def move_folder(self, name: str, new_parent: str) -> None: ...
    def delete_folder(self, name: str) -> None: ...
    def get_files(self, folder: str) -> list[str]: ...
    def get_subfolders(self, folder: str) -> list[str]: ...
    def get_parent(self, folder: str) -> str | None: ...
```

Folder names and file names are non-empty strings.

## Folders

- A new tree holds a single empty folder named `"root"`, which has no
  parent. The root folder is always there: it can be neither moved nor
  deleted.
- `add_folder(name, parent)` adds an empty folder inside folder `parent`.
  Folder names are unique in the tree: a name already used by a folder
  (including `"root"`) raises `FolderError`.
- Every method that takes a folder name raises `KeyError` for a folder that
  is not in the tree: one that was never added, or one that was deleted.
- `get_subfolders(folder)` returns the names of the folders directly inside
  the folder, in the order they came there: by being added there or moved
  there.
- `get_parent(folder)` returns the name of the folder directly containing
  the folder, or `None` for `"root"`.

## Files

- `add_file(folder, file)` adds a file named `file` to the folder, after its
  other files. Every file in the tree has its own name: callers never add a
  file under a name that a file in the tree already has.
- `remove_file(file)` removes the file from the tree, wherever it is. It
  raises `KeyError` if no file has that name.
- `get_files(folder)` returns the names of the files directly in the
  folder, in the order they came there.

## Moving and deleting folders

- `move_folder(name, new_parent)` moves the folder, with everything inside
  it, out of its parent and puts it after the other subfolders of
  `new_parent`. It raises `ValueError` if `name` is `"root"` or if
  `new_parent` is the folder itself.
- `delete_folder(name)` deletes a folder that has no subfolders: the folder
  is removed from the tree and from its parent's subfolders. What happens
  to the files that were in it is up to you (for example, they may be
  removed from the tree, or moved to the parent folder). It raises
  `ValueError` if `name` is `"root"`.

## Errors

A failed call has no effect: if a method raises, every folder keeps the
same parent, files and subfolders, in the same order. When a call has more
than one problem, which of the errors is raised is unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes folder or file names that are not non-empty strings (such as `""`,
`None` or `1`), wherever they are passed. It also includes which error is
raised when a call has several problems, adding a file under a name that a
file in the tree already has, deleting a folder that still has subfolders,
what happens to the files of a deleted folder,
moving a folder into a folder inside it or into the folder it is already
in, adding a folder or file again under the name of one that was deleted or
removed, whether a file and a folder may have the same name, what happens
if a returned list is changed, the text of error messages, saving the tree
to a file, and use from several threads.
