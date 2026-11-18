Sorting photos one at a time is slow. Add a way to move several photos in
one call that moves either all of them or none.

- Add `PhotoLibrary.move_photos(photos: list[str], to_album: str) -> None`.
  It moves every photo in the list `photos` to the end of `to_album`, in
  the order of the list. The photos may come from different albums
  (including `"Unsorted"`), and the other photos of every album keep their
  order.
- The call succeeds or fails as a whole. It checks every photo before it
  moves any, and if any check fails it raises and moves no photo at all:
  - `KeyError` if `to_album` is not in use, or if any photo in the list is
    not in the library;
  - `ValueError` if any photo in the list is already in `to_album`, or if
    the same photo is in the list more than once.
- Which error is raised when a call has several problems is unspecified,
  and so is what an empty list does.
- After a successful call the photos are where `move_photo` would have put
  them one at a time, in the order of the list: they are still in the
  library and can be moved or removed again like any other photo.

All existing behavior must keep working.
