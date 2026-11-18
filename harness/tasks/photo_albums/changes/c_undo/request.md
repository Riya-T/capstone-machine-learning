Add an undo to `albums.py`, so a slip while sorting photos can be taken
back.

- Add `PhotoLibrary.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the methods that change albums or
  photos: `create_album`, `add_photo`, `move_photo`, `remove_photo`,
  `merge_albums` and `delete_album`, and any other method that changes
  albums or photos. Each further `undo` goes one call further back.
- Undoing a call puts every album's photos, in their order, and the list of
  albums, in its order, back to exactly what they were just before that
  call. One `undo` always takes back a whole call, however many photos it
  moved:
  - an undone `move_photo` puts the photo back at its old position in the
    album it came from;
  - an undone `remove_photo` puts the photo back at its old position in its
    album, and its name is in the library again;
  - an undone `merge_albums` or `delete_album` brings the removed album back
    with its photos in their order, at its old position in `get_albums()`,
    and takes those photos out of the album they were moved to; its name is
    in use again;
  - an undone `create_album` removes the album, and an undone `add_photo`
    removes the photo; the name may then be used again.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `AlbumError` and changes nothing.

All existing behavior must keep working.
