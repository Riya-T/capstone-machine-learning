# Photo albums

Write a module `albums.py` that keeps a photo library organised in albums.
Each album holds named photos in the order they were put into it. Photos can
be moved between albums or removed, and whole albums can be merged into
another album or deleted.

## Interface

```python
class AlbumError(Exception): ...


class PhotoLibrary:
    def __init__(self): ...
    def create_album(self, name: str) -> None: ...
    def add_photo(self, album: str, photo: str) -> None: ...
    def move_photo(self, photo: str, to_album: str) -> None: ...
    def remove_photo(self, photo: str) -> None: ...
    def merge_albums(self, source: str, into: str) -> int: ...
    def delete_album(self, name: str) -> int: ...
    def get_photos(self, album: str) -> list[str]: ...
    def get_albums(self) -> list[str]: ...
```

Album names and photo names are non-empty strings.

## Albums

- A new library has one album, named `"Unsorted"`, with no photos. It
  always exists: it can be used like any other album, but it can never be
  removed.
- `create_album(name)` adds an album with no photos. A name that is already
  in use (including `"Unsorted"`) raises `AlbumError`.
- `get_albums()` returns the names of the albums in use, in the order they
  were created, so `"Unsorted"` always comes first.
- Every other method that takes an album name raises `KeyError` when given
  an album name that is not in use: one that was never created, or one that
  was merged or deleted.

## Photos

- Each photo is in exactly one album, and a photo name is used at most once
  in the whole library.
- `add_photo(album, photo)` puts a new photo at the end of the album. A
  photo name that is already in the library (in any album) raises
  `AlbumError`.
- `move_photo(photo, to_album)` takes the photo out of its album and puts it
  at the end of `to_album`; the other photos keep their order. Moving a
  photo to the album it is already in raises `ValueError`.
- `remove_photo(photo)` takes the photo out of the library; the other photos
  keep their order.
- `move_photo` and `remove_photo` raise `KeyError` for a photo name that is
  not in the library.
- `get_photos(album)` returns the photos of the album, in order.

## Merging and deleting albums

- `merge_albums(source, into)` puts every photo of album `source` at the end
  of album `into`, in `source`'s order, then removes album `source`: it is
  no longer in `get_albums()`, and every method treats it as not in use. It
  returns how many photos it moved. Merging an album into itself raises
  `ValueError`, and `source` may not be `"Unsorted"` (`AlbumError`).
- `delete_album(name)` puts every photo of the album at the end of
  `"Unsorted"`, in their order, then removes the album the same way. It
  returns how many photos it moved. Deleting `"Unsorted"` raises
  `AlbumError`.

## Errors

A failed call has no effect: if a method raises, every album's photos and
the list of albums are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type, such as album or photo names that are not
non-empty strings (`""`, `None` or `1`), wherever they are passed. It also
includes which error is raised when a call has more than one problem (such
as `merge_albums("Unsorted", "Unsorted")`), whether a name that was used
before (an album that was merged or deleted, a photo that was removed) may
be used again, what happens if a returned list is changed, the text of error
messages, saving the library to a file, and use from several threads.
