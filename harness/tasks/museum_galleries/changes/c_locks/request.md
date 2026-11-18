Let galleries in `museum.py` be locked, for example while an exhibition is
being photographed. No artwork may be hung in, taken down from, or moved
into or out of a locked gallery.

- Add `Museum.lock_gallery(name)`, `Museum.unlock_gallery(name)` and
  `Museum.is_locked(name) -> bool`. Each raises `KeyError` for a gallery
  that is not in use. New galleries are not locked. Locking a locked
  gallery, or unlocking one that is not locked, does nothing.
- Add `class GalleryLocked(MuseumError)` to `museum.py`.
- A call raises `GalleryLocked` and changes nothing when it would change a
  locked gallery:
  - `hang` into a locked gallery;
  - `take_down` of an artwork in a locked gallery;
  - `move_artwork` of an artwork in a locked gallery, or into a locked
    gallery;
  - `swap_artworks` when either artwork is in a locked gallery (also when
    both are in the same gallery);
  - `close_gallery` when gallery `name` or gallery `into` is locked, even
    when `name` has no artworks;
  - any other method that hangs, takes down or moves artworks, for every
    gallery it would change.
- When a call has another problem as well (a gallery or artwork that is
  not in use, the same name on both sides, a name already in use), which
  error is raised is unspecified.
- Calls that change no gallery work as before on a locked gallery:
  `add_gallery`, `get_artworks` and `get_galleries`, and of course calls
  on other galleries. `unlock_gallery` lifts the lock, and the gallery
  works as before.
- `undo` still restores the exact earlier state, now including which
  galleries are locked: `lock_gallery` and `unlock_gallery` are recorded
  calls like the others, so `undo` reverses them, and undoing any call puts
  every lock back as it was just before that call. `undo` itself is never
  blocked by a lock.

All existing behavior must keep working.
