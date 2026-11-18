"""Museum galleries with several moves as one call, and undo.

Correct solution for museum_galleries after c_move_many and c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from museum import Museum
    museum = Museum()
    museum.add_gallery("east")
    museum.add_gallery("west")
    museum.hang("water lilies", "east")
    museum.move_many([("water lilies", "west")])
    museum.undo()  # the water lilies hang in east again
"""


class MuseumError(Exception):
    pass


class Museum:
    def __init__(self):
        # gallery name -> artwork names in hanging order; the galleries are
        # kept in the order they were added.
        self._galleries = {}
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
        self._save()
        self._galleries[gallery].append(artwork)

    def take_down(self, artwork):
        gallery, index = self._locate(artwork)
        self._save()
        del self._galleries[gallery][index]

    def move_artwork(self, artwork, gallery):
        self.move_many([(artwork, gallery)])

    def move_many(self, moves):
        saved = self._snapshot()
        try:
            for artwork, gallery in moves:
                self._move(artwork, gallery)
        except Exception:
            self._restore(saved)
            raise
        self._history.append(saved)  # the whole call is one undo step

    def swap_artworks(self, first, second):
        first_gallery, first_index = self._locate(first)
        second_gallery, second_index = self._locate(second)
        if first == second:
            raise ValueError("cannot swap an artwork with itself")
        self._save()
        self._galleries[first_gallery][first_index] = second
        self._galleries[second_gallery][second_index] = first

    def close_gallery(self, name, into):
        self._require_gallery(name)
        self._require_gallery(into)
        if name == into:
            raise ValueError("cannot close a gallery into itself")
        self._save()
        moved = self._galleries.pop(name)
        self._galleries[into].extend(moved)
        return len(moved)

    def undo(self):
        if not self._history:
            raise MuseumError("nothing to undo")
        self._restore(self._history.pop())

    def get_artworks(self, gallery):
        self._require_gallery(gallery)
        return list(self._galleries[gallery])

    def get_galleries(self):
        return list(self._galleries)

    def _move(self, artwork, gallery):
        # Checks everything before changing anything; records nothing.
        source, index = self._locate(artwork)
        self._require_gallery(gallery)
        if source == gallery:
            raise ValueError(f"{artwork!r} already hangs in {gallery!r}")
        del self._galleries[source][index]
        self._galleries[gallery].append(artwork)

    def _snapshot(self):
        return {name: list(artworks) for name, artworks in self._galleries.items()}

    def _restore(self, snapshot):
        self._galleries = snapshot

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._history.append(self._snapshot())

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
