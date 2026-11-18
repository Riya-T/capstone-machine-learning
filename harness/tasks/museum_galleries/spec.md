# Museum galleries

Write a module `museum.py` that keeps track of which artworks hang in which
gallery of a museum, and in what order, as artworks are hung, taken down,
moved and swapped, and as galleries are closed.

## Interface

```python
class MuseumError(Exception): ...


class Museum:
    def __init__(self): ...
    def add_gallery(self, name: str) -> None: ...
    def hang(self, artwork: str, gallery: str) -> None: ...
    def take_down(self, artwork: str) -> None: ...
    def move_artwork(self, artwork: str, gallery: str) -> None: ...
    def swap_artworks(self, first: str, second: str) -> None: ...
    def close_gallery(self, name: str, into: str) -> int: ...
    def get_artworks(self, gallery: str) -> list[str]: ...
    def get_galleries(self) -> list[str]: ...
```

Gallery names and artwork names are non-empty strings.

## Galleries

- `add_gallery(name)` adds an empty gallery. A name that is already in use
  raises `MuseumError`.
- `get_galleries()` returns the names of the galleries in use, in the order
  they were added.
- Every other method that takes a gallery name raises `KeyError` when that
  name is not in use: one that was never added, or one that was closed.

## Artworks

- Each artwork hangs in exactly one gallery, and its name is unique in the
  whole museum.
- `get_artworks(gallery)` returns the names of the artworks in the gallery
  in hanging order, first one first. A new gallery has none.
- `hang(artwork, gallery)` hangs the artwork at the end of the gallery,
  after its other artworks. An artwork name that already hangs anywhere in
  the museum raises `MuseumError`.
- `take_down(artwork)` removes the artwork from its gallery. The other
  artworks keep their order. The name is then free: `hang` may hang it
  again later.
- `move_artwork(artwork, gallery)` takes the artwork out of its gallery and
  hangs it at the end of `gallery`. The artworks it leaves behind keep their
  order. Moving an artwork to the gallery it is already in raises
  `ValueError`.
- `swap_artworks(first, second)` makes the two artworks trade places: each
  ends up in the other's gallery, at the other's position. They may be in
  the same gallery or in different ones. Neither goes to the
  end of a gallery and no other artwork moves (see the example below).
- `take_down`, `move_artwork` and `swap_artworks` raise `KeyError` for an
  artwork that is not hanging in the museum: one that was never hung, or
  one that was taken down.

## Closing a gallery

- `close_gallery(name, into)` moves every artwork of gallery `name` to the
  end of gallery `into`, keeping their order, and then closes gallery
  `name`: it is removed from `get_galleries()`, and every method treats it
  as not in use. It returns how many artworks it moved (0 if the gallery
  was empty).
- The closed gallery's name is then free: `add_gallery` may add it again
  later, as a new empty gallery.
- `close_gallery` raises `ValueError` when `name` and `into` are the same.

```python
m = Museum()
m.add_gallery("east")
m.add_gallery("west")
for artwork in ["lilies", "harbor", "dancer"]:
    m.hang(artwork, "east")
m.hang("storm", "west")
m.swap_artworks("harbor", "storm")
m.get_artworks("east")           # ["lilies", "storm", "dancer"]
m.get_artworks("west")           # ["harbor"]
m.close_gallery("east", "west")  # returns 3
m.get_artworks("west")           # ["harbor", "lilies", "storm", "dancer"]
m.get_galleries()                # ["west"]
```

Python note: moving or taking down an artwork changes the list of the
gallery it leaves. If you loop over that very list and move artworks inside
the loop, Python skips some of them. Loop over a copy instead
(`for artwork in list(artworks):`), from the first artwork to the last
(looping backwards would reverse their order), and count how many there are
before you move anything.

## Errors

A failed call has no effect: if a method raises, every gallery and every
artwork stays where it was, in the same order.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when a call has more than one problem (for
example a gallery that is not in use and an artwork that does not hang),
swapping an artwork with itself, names that are not non-empty strings (such
as `""`, `None` or `1`), what happens if a returned list is changed, the text of error messages, saving the
museum to a file, and use from several threads.
