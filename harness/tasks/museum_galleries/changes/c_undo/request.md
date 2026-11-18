Add an undo to `museum.py`, so a curator's mistake in rearranging the
galleries can be taken back.

- Add `Museum.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among `add_gallery`, `hang`, `take_down`,
  `move_artwork`, `swap_artworks` and `close_gallery`, and any other method
  that changes the galleries or their artworks (including methods added
  later). Each further `undo` goes one call further back.
- Undoing a call puts the list of galleries, and every gallery's artworks
  in their order, back exactly as they were just before that call:
  - an undone `take_down` hangs the artwork again at its old position in
    its old gallery, and its name is in use again;
  - an undone `move_artwork` or `swap_artworks` puts the artworks back at
    their old positions in their old galleries;
  - an undone `close_gallery` takes the closed gallery's artworks out of
    `into` and brings the closed gallery back, with its artworks in their
    order and at its old position in `get_galleries()`; its name is in use
    again;
  - an undone `add_gallery` removes the gallery, and an undone `hang`
    takes the artwork down; the name is then free again.
- A call that changes several things at once is one call: one `undo`
  reverses all of it. A `close_gallery` that moved 0 artworks is still a
  call: `undo` brings the empty gallery back.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `MuseumError` and changes
  nothing.

All existing behavior must keep working.
