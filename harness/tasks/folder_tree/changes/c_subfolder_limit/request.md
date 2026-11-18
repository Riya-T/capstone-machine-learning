Let folders in `folders.py` limit how many subfolders they hold, for example
a shared folder that may hold at most 10 folders.

- `add_folder` takes a new keyword argument: `add_folder(name, parent,
  max_subfolders=None)`. `None`, the default, means no limit. Otherwise the
  limit must be an `int` greater than 0; anything else raises `ValueError`
  and adds no folder. The root folder has no limit.
- Add `FolderTree.get_max_subfolders(folder) -> int | None`, which returns
  the folder's limit (`None` for no limit). It raises `KeyError` for a
  folder that is not in the tree.
- Add `class FolderFull(FolderError)` to `folders.py`.
- A folder never holds more subfolders directly than its limit; holding
  exactly its limit is fine. Folders further down do not count. Every call
  that puts a folder directly into another checks the receiving folder:
  `add_folder` (the `parent`) and `move_folder` (the `new_parent`). If the
  receiving folder would end up with more subfolders than its limit, the
  call raises `FolderFull` and changes nothing: a refused `move_folder`
  moves nothing, neither the folder nor anything inside it.
- A moved folder keeps its own limit. The limit of the folder that a moved
  folder leaves is not checked, and deleting or moving out a subfolder
  makes room for another. Files are never limited, and `delete_folder`
  never raises `FolderFull`.
- When a call would raise `FolderFull` and another error too, which of them
  is raised is unspecified.
- `undo` keeps working as before: it puts back exactly the state from just
  before the undone call, and a folder brought back by an undone
  `delete_folder` has its limit again.

All existing behavior must keep working.
