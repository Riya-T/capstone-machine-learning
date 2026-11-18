Add an undo to `folders.py`, so a mistake in sorting the folders can be
taken back.

- Add `FolderTree.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the methods that change the tree:
  `add_folder`, `add_file`, `remove_file`, `move_folder` and
  `delete_folder`, and any other method of the class that changes folders
  or files. Each further `undo` goes one call further back.
- Undoing a call puts the whole tree back exactly as it was just before
  that call: every folder with the same parent, the same files and the same
  subfolders, in the same order. A call that changed several things is
  undone as a whole by one `undo`:
  - an undone `delete_folder` brings the deleted folder back, at its old
    place among its parent's subfolders, with its files in their old order,
    and also reverses whatever the delete did with those files; the
    folder's name is in use again;
  - an undone `move_folder` puts the folder, with everything inside it,
    back at its old place among its old parent's subfolders;
  - an undone `remove_file` puts the file back at its old place among the
    files of its folder;
  - an undone `add_folder` or `add_file` removes the folder or file, and
    its name may then be added again.
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods, and to `undo` itself, are not recorded either and are
  never undone. There is no redo.
- With nothing left to undo, `undo` raises `FolderError` and changes
  nothing.

All existing behavior must keep working.
