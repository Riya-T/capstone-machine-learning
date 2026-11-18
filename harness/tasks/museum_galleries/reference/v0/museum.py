"""Museum galleries: which artworks hang in which gallery, in what order.

Correct solution for museum_galleries before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from museum import Museum
    museum = Museum()
    museum.add_gallery("east")
    museum.hang("water lilies", "east")
"""


class MuseumError(Exception):
    pass


class Museum:
    def __init__(self):
        # gallery name -> artwork names in hanging order; the galleries are
        # kept in the order they were added.
        self._galleries = {}

    def add_gallery(self, name):
        if name in self._galleries:
            raise MuseumError(f"gallery name {name!r} is already used")
        self._galleries[name] = []

    def hang(self, artwork, gallery):
        self._require_gallery(gallery)
        if self._find(artwork) is not None:
            raise MuseumError(f"{artwork!r} already hangs in the museum")
        self._galleries[gallery].append(artwork)

    def take_down(self, artwork):
        gallery, index = self._locate(artwork)
        del self._galleries[gallery][index]

    def move_artwork(self, artwork, gallery):
        source, index = self._locate(artwork)
        self._require_gallery(gallery)
        if source == gallery:
            raise ValueError(f"{artwork!r} already hangs in {gallery!r}")
        del self._galleries[source][index]
        self._galleries[gallery].append(artwork)

    def swap_artworks(self, first, second):
        first_gallery, first_index = self._locate(first)
        second_gallery, second_index = self._locate(second)
        if first == second:
            raise ValueError("cannot swap an artwork with itself")
        self._galleries[first_gallery][first_index] = second
        self._galleries[second_gallery][second_index] = first

    def close_gallery(self, name, into):
        self._require_gallery(name)
        self._require_gallery(into)
        if name == into:
            raise ValueError("cannot close a gallery into itself")
        moved = self._galleries.pop(name)
        self._galleries[into].extend(moved)
        return len(moved)

    def get_artworks(self, gallery):
        self._require_gallery(gallery)
        return list(self._galleries[gallery])

    def get_galleries(self):
        return list(self._galleries)

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
