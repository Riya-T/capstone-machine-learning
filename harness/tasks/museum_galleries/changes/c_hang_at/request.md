Make the place where new artworks go adjustable in `museum.py`: some
museums hang new arrivals at the front of a gallery, where visitors see them
first.

- `Museum` takes a new keyword argument `hang_at="end"`. It must be
  `"end"` or `"start"`; anything else raises `ValueError`.
- Add `Museum.set_hang_at(gallery, where)` and
  `Museum.get_hang_at(gallery) -> str`. Both raise `KeyError` for a gallery
  that is not in use, and `set_hang_at` raises `ValueError` when `where` is
  not `"end"` or `"start"` (which of the two is raised when both are wrong
  is unspecified; in each case nothing changes). `set_hang_at` changes only
  that gallery's setting.
- Every gallery starts with the museum's `hang_at` value when it is added.
  That includes a gallery added again under the name of a closed one: it
  does not keep the closed gallery's setting.
- In a gallery set to `"end"` everything works as before. In a gallery set
  to `"start"`, the calls that put artworks into it put them before its
  other artworks instead of after them:
  - `hang` and `move_artwork` put the artwork first;
  - `close_gallery(name, into)` puts the moved artworks, still in their
    order, before the artworks `into` already has;
  - any other method that puts artworks into a gallery follows the same
    rule.
- `take_down` and `swap_artworks` are not affected, and changing a setting
  does not rearrange the artworks a gallery already has.
- Locks work as before: a locked gallery still takes no artworks, whatever
  its setting. `set_hang_at` and `get_hang_at` work on a locked gallery.
- `undo` still restores the exact earlier state, now including every
  gallery's setting: `set_hang_at` is a recorded call like the others, so
  `undo` reverses it, and an artwork hung while a gallery was set to
  `"start"` is still taken out of the right place.

All existing behavior must keep working.
