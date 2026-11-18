Albums are printed as small photo books with 5 pages, so an album in
`albums.py` may hold at most 5 photos. `"Unsorted"` is never printed and
has no limit.

- Add `class AlbumFull(AlbumError)` to `albums.py`.
- Every call that puts photos into an album other than `"Unsorted"` checks
  the limit, and raises `AlbumFull` and changes nothing when the album
  would end up with more than 5 photos:
  - `add_photo` into an album that already has 5 photos;
  - `move_photo` into an album that already has 5 photos;
  - `merge_albums(source, into)` when `into` would end up with more than 5
    photos. It then moves no photo at all, and `source` is not removed.
- `"Unsorted"` takes any number of photos, so `delete_album` and a merge
  into `"Unsorted"` are never refused by the limit.
- Taking photos out of an album (`move_photo` out of it, `remove_photo`) is
  never refused by the limit, and a full album has room again once a photo
  has left it.
- When a call has another problem as well (an album or photo that is not in
  use, the same album twice, a photo name already in the library), which
  error is raised is unspecified, but the call still changes nothing.
- `undo` works as before: it restores exactly the state before the undone
  call, which always kept to the limit, so `undo` never raises `AlbumFull`.

All existing behavior must keep working.
