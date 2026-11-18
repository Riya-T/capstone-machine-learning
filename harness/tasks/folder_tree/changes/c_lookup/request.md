Add two ways to look things up in `folders.py`: every file below a folder,
and the folder a file is in.

- Add `FolderTree.get_all_files(folder) -> list[str]`, which returns every
  file in the folder and in all the folders inside it, at any depth: first
  the folder's own files in their order, then, for each of its subfolders in
  order, all the files of that subfolder by the same rule. It raises
  `KeyError` for a folder that is not in the tree.
- Add `FolderTree.get_folder_of(file) -> str`, which returns the name of the
  folder that holds the file directly. It raises `KeyError` if no file has
  that name.
- Both always reflect the tree as it is now, after every earlier call that
  added, moved, removed or deleted something. Neither changes anything.

All existing behavior must keep working.
