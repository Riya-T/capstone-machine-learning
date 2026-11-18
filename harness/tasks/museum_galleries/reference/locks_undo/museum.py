"""Museum galleries with undo and locked galleries.

Correct solution for museum_galleries after c_undo and c_locks.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from museum import Museum
    museum = Museum()
    museum.add_gallery("east")
    museum.lock_gallery("east")
    museum.undo()  # east is unlocked again
"""


class MuseumError(Exception):
    pass


class GalleryLocked(MuseumError):
    pass


class Museum:
    def __init__(self):
        # gallery name -> artwork names in hanging order; the galleries are
        # kept in the order they were added.
        self._galleries = {}
        self._locked = set()
        self._history = []  # snapshots of the state just before each recorded call

    def add_gallery(self, name):
        if name in self._galleries:
            raise MuseumError(f"gallery name {name!r} is already used")
        self._save()
        self._galleries[name] = []

    def hang(self, artwork, gallery):
        self._require_gallery(gallery)
        if self._find(artwork) is not None:
            raise MuseumError(f"{artwork!r} already hangs in the museum")
        self._require_unlocked(gallery)
        self._save()
        self._galleries[gallery].append(artwork)

    def take_down(self, artwork):
        gallery, index = self._locate(artwork)
        self._require_unlocked(gallery)
        self._save()
        del self._galleries[gallery][index]

    def move_artwork(self, artwork, gallery):
        source, index = self._check_move(artwork, gallery)
        self._save()
        del self._galleries[source][index]
        self._galleries[gallery].append(artwork)

    def swap_artworks(self, first, second):
        first_gallery, first_index = self._locate(first)
        second_gallery, second_index = self._locate(second)
        if first == second:
            raise ValueError("cannot swap an artwork with itself")
        self._require_unlocked(first_gallery, second_gallery)
        self._save()
        self._galleries[first_gallery][first_index] = second
        self._galleries[second_gallery][second_index] = first

    def close_gallery(self, name, into):
        self._require_gallery(name)
        self._require_gallery(into)
        if name == into:
            raise ValueError("cannot close a gallery into itself")
        self._require_unlocked(name, into)
        self._save()
        moved = self._galleries.pop(name)
        self._galleries[into].extend(moved)
        return len(moved)

    def lock_gallery(self, name):
        self._require_gallery(name)
        self._save()
        self._locked.add(name)

    def unlock_gallery(self, name):
        self._require_gallery(name)
        self._save()
        self._locked.discard(name)

    def is_locked(self, name):
        self._require_gallery(name)
        return name in self._locked

    def undo(self):
        if not self._history:
            raise MuseumError("nothing to undo")
        self._restore(self._history.pop())

    def get_artworks(self, gallery):
        self._require_gallery(gallery)
        return list(self._galleries[gallery])

    def get_galleries(self):
        return list(self._galleries)

    def _snapshot(self):
        galleries = {name: list(artworks) for name, artworks in self._galleries.items()}
        return galleries, set(self._locked)

    def _restore(self, snapshot):
        self._galleries, self._locked = snapshot

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._history.append(self._snapshot())

    def _check_move(self, artwork, gallery):
        source, index = self._locate(artwork)
        self._require_gallery(gallery)
        if source == gallery:
            raise ValueError(f"{artwork!r} already hangs in {gallery!r}")
        self._require_unlocked(source, gallery)
        return source, index

    def _require_unlocked(self, *galleries):
        for gallery in galleries:
            if gallery in self._locked:
                raise GalleryLocked(f"gallery {gallery!r} is locked")

    def _require_gallery(self, gallery):
        if not isinstance(gallery, str) or gallery not in self._galleries:
            raise KeyError(gallery)

    def _find(self, artwork):
        for gallery, artworks in self._galleries.items():
            if artwork in artworks:
                return gallery, artworks.index(artwork)
        return None

    def _locate(self, artwork):
        found = self._find(artwork)
        if found is None:
            raise KeyError(artwork)
        return found
