"""Photo albums with undo and at most 5 photos per album (Unsorted aside).

Correct solution for photo_albums after c_undo and c_album_limit.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from albums import PhotoLibrary
    library = PhotoLibrary()
    library.create_album("Holiday")
    library.add_photo("Holiday", "beach.jpg")
    library.undo()  # Holiday is empty again
"""

UNSORTED = "Unsorted"
MAX_PHOTOS = 5  # per album; Unsorted has no limit


class AlbumError(Exception):
    pass


class AlbumFull(AlbumError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class PhotoLibrary:
    def __init__(self):
        # album name -> list of its photos in order; the dict keeps the
        # albums in the order they were created.
        self._albums = {UNSORTED: []}
        self._undo_stack = []  # copies of the albums as they were before each call

    def create_album(self, name):
        check_name(name, "album name")
        if name in self._albums:
            raise AlbumError(f"album {name!r} already exists")
        self._save()
        self._albums[name] = []

    def add_photo(self, album, photo):
        photos = self._require_album(album)
        check_name(photo, "photo name")
        if self._album_of(photo) is not None:
            raise AlbumError(f"photo {photo!r} is already in the library")
        self._require_room(album, 1)
        self._save()
        photos.append(photo)

    def move_photo(self, photo, to_album):
        source = self._require_photo(photo)
        target = self._require_album(to_album)
        if source == to_album:
            raise ValueError(f"photo {photo!r} is already in album {to_album!r}")
        self._require_room(to_album, 1)
        self._save()
        self._albums[source].remove(photo)
        target.append(photo)

    def remove_photo(self, photo):
        source = self._require_photo(photo)
        self._save()
        self._albums[source].remove(photo)

    def merge_albums(self, source, into):
        self._require_album(source)
        self._require_album(into)
        if source == into:
            raise ValueError("cannot merge an album into itself")
        if source == UNSORTED:
            raise AlbumError("the Unsorted album cannot be removed")
        self._require_room(into, len(self._albums[source]))
        self._save()
        return self._empty_into(source, into)

    def delete_album(self, name):
        self._require_album(name)
        if name == UNSORTED:
            raise AlbumError("the Unsorted album cannot be removed")
        self._save()
        return self._empty_into(name, UNSORTED)

    def undo(self):
        if not self._undo_stack:
            raise AlbumError("nothing to undo")
        self._albums = self._undo_stack.pop()

    def get_photos(self, album):
        return list(self._require_album(album))

    def get_albums(self):
        return list(self._albums)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({name: list(photos) for name, photos in self._albums.items()})

    def _require_room(self, album, count):
        if album != UNSORTED and len(self._albums[album]) + count > MAX_PHOTOS:
            raise AlbumFull(f"album {album!r} would hold more than {MAX_PHOTOS} photos")

    def _empty_into(self, source, into):
        photos = self._albums.pop(source)
        self._albums[into].extend(photos)
        return len(photos)

    def _album_of(self, photo):
        for name, photos in self._albums.items():
            if photo in photos:
                return name
        return None

    def _require_album(self, album):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(album, str) or album not in self._albums:
            raise KeyError(album)
        return self._albums[album]

    def _require_photo(self, photo):
        album = self._album_of(photo)
        if album is None:
            raise KeyError(photo)
        return album
