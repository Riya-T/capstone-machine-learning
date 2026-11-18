Let a curator rehang several artworks in one go in `museum.py`, so that a
rehang either happens completely or not at all.

- Add `Museum.move_many(moves) -> None`. `moves` is a list of
  `(artwork, gallery)` pairs. They are applied in the order given, each
  exactly as `move_artwork(artwork, gallery)` would apply it to the museum
  as the pairs before it left it: the artwork is taken out of its current
  gallery and hung at the end of `gallery`. So a later pair may move an
  artwork that an earlier pair already moved.
- If any pair would make `move_artwork` raise at that point (an artwork
  that does not hang, a gallery that is not in use, or an artwork moved to
  the gallery it is in at that point), `move_many` raises that same kind of
  error and changes nothing: every artwork stays where it was, at its old
  position, including the artworks of the pairs before it.
- Values of `moves` that are not a list of pairs are unspecified.

All existing behavior must keep working.
