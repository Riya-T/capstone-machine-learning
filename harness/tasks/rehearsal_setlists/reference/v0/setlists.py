"""Rehearsal setlists: ordered lists of song titles.

Correct solution for the initial rehearsal_setlists spec.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.
"""


class SetlistError(Exception):
    pass


def check_name(name):
    if not isinstance(name, str) or not name:
        raise ValueError("setlist name must be a non-empty str")


def check_title(title):
    if not isinstance(title, str) or not title:
        raise ValueError("title must be a non-empty str")


def check_different(first, second):
    if first == second:
        raise ValueError("the two setlists must be different")


class Setlists:
    def __init__(self):
        # setlist name -> list of titles, in the order the setlists were created
        self._setlists = {}

    def create_setlist(self, name):
        check_name(name)
        if name in self._setlists:
            raise SetlistError(f"setlist name {name!r} is already used")
        self._setlists[name] = []

    def add_song(self, setlist, title):
        self._require(setlist)
        check_title(title)
        if self._find(setlist, title) is not None:
            raise SetlistError(f"{title!r} is already in setlist {setlist!r}")
        self._setlists[setlist].append(title)

    def remove_song(self, setlist, title):
        self._require(setlist)
        index = self._index(setlist, title)
        del self._setlists[setlist][index]

    def move_song(self, title, from_setlist, to_setlist):
        self._require(from_setlist)
        self._require(to_setlist)
        check_different(from_setlist, to_setlist)
        index = self._index(from_setlist, title)
        if self._find(to_setlist, title) is not None:
            raise SetlistError(f"{title!r} is already in setlist {to_setlist!r}")
        song = self._setlists[from_setlist].pop(index)
        self._setlists[to_setlist].append(song)

    def merge_setlists(self, source, into):
        self._require(source)
        self._require(into)
        check_different(source, into)
        appended = 0
        for song in self._setlists[source]:
            if self._find(into, song) is None:
                self._setlists[into].append(song)
                appended += 1
        del self._setlists[source]
        return appended

    def drop_song_everywhere(self, title):
        check_title(title)
        holders = []
        for name in self._setlists:
            index = self._find(name, title)
            if index is not None:
                holders.append((name, index))
        for name, index in holders:
            del self._setlists[name][index]
        return len(holders)

    def get_songs(self, setlist):
        self._require(setlist)
        return list(self._setlists[setlist])

    def get_setlists(self):
        return list(self._setlists)

    def _find(self, setlist, title):
        """Position of the title in the setlist, or None."""
        songs = self._setlists[setlist]
        if title in songs:
            return songs.index(title)
        return None

    def _index(self, setlist, title):
        index = self._find(setlist, title)
        if index is None:
            raise KeyError(title)
        return index

    def _require(self, setlist):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(setlist, str) or setlist not in self._setlists:
            raise KeyError(setlist)
