"""Photo albums with moving several photos at once.

Correct solution for photo_albums after c_move_many.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from albums import PhotoLibrary
    library = PhotoLibrary()
    library.create_album("Holiday")
    library.add_photo("Holiday", "beach.jpg")
"""

UNSORTED = "Unsorted"


class AlbumError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class PhotoLibrary:
    def __init__(self):
        # album name -> list of its photos in order; the dict keeps the
        # albums in the order they were created.
        self._albums = {UNSORTED: []}

    def create_album(self, name):
        check_name(name, "album name")
        if name in self._albums:
            raise AlbumError(f"album {name!r} already exists")
        self._albums[name] = []

    def add_photo(self, album, photo):
        photos = self._require_album(album)
        check_name(photo, "photo name")
        if self._album_of(photo) is not None:
            raise AlbumError(f"photo {photo!r} is already in the library")
        photos.append(photo)

    def move_photo(self, photo, to_album):
        source = self._require_photo(photo)
        target = self._require_album(to_album)
        if source == to_album:
            raise ValueError(f"photo {photo!r} is already in album {to_album!r}")
        self._albums[source].remove(photo)
        target.append(photo)

    def move_photos(self, photos, to_album):
        target = self._require_album(to_album)
        if not isinstance(photos, list):
            raise ValueError("photos must be a list of photo names")
        # Every check runs before any photo moves, so a failed call moves none.
        sources = [self._require_photo(photo) for photo in photos]
        if len(set(photos)) != len(photos):
            raise ValueError("a photo is named more than once")
        if to_album in sources:
            raise ValueError(f"a photo is already in album {to_album!r}")
        for photo, source in zip(photos, sources):
            self._albums[source].remove(photo)
            target.append(photo)

    def remove_photo(self, photo):
        source = self._require_photo(photo)
        self._albums[source].remove(photo)

    def merge_albums(self, source, into):
        self._require_album(source)
        self._require_album(into)
        if source == into:
            raise ValueError("cannot merge an album into itself")
        if source == UNSORTED:
            raise AlbumError("the Unsorted album cannot be removed")
        return self._empty_into(source, into)

    def delete_album(self, name):
        self._require_album(name)
        if name == UNSORTED:
            raise AlbumError("the Unsorted album cannot be removed")
        return self._empty_into(name, UNSORTED)

    def get_photos(self, album):
        return list(self._require_album(album))

    def get_albums(self):
        return list(self._albums)

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
