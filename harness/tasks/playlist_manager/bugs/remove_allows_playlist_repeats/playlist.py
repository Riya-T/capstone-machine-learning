"""Music library that can be searched by artist and where songs can be removed.

Planted bug (after c_by_artist and c_remove): removal was added correctly,
but add_to_playlist no longer refuses a song that is already in the
playlist. Never shown to the writer or the editor; validate-tasks checks
that the tests catch it.

Usage:
    from playlist import MusicLibrary
    library = MusicLibrary()
    library.add_song("Blue", "Nina", 200)
    library.remove_song("Blue")
    library.get_artists()
"""


class LibraryError(Exception):
    pass


class QueueEmpty(LibraryError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_duration(duration):
    if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0:
        raise ValueError(f"duration must be a positive int, got {duration!r}")


class MusicLibrary:
    def __init__(self):
        self._songs = {}  # title -> (artist, duration), in the order added
        self._playlists = {}  # name -> list of titles, in creation order
        self._queue = []  # titles, next to play first

    def add_song(self, title, artist, duration):
        check_name(title, "title")
        check_name(artist, "artist")
        check_duration(duration)
        if title in self._songs:
            raise LibraryError(f"song {title!r} was already added")
        self._songs[title] = (artist, duration)

    def remove_song(self, title):
        self._require_song(title)
        del self._songs[title]
        for titles in self._playlists.values():
            if title in titles:
                titles.remove(title)
        self._queue = [t for t in self._queue if t != title]

    def create_playlist(self, name):
        check_name(name, "playlist name")
        if name in self._playlists:
            raise LibraryError(f"playlist {name!r} already exists")
        self._playlists[name] = []

    def add_to_playlist(self, name, title):
        self._require_playlist(name)
        self._require_song(title)
        self._playlists[name].append(title)

    def remove_from_playlist(self, name, title):
        self._require_playlist(name)
        self._require_song(title)
        if title not in self._playlists[name]:
            raise LibraryError(f"{title!r} is not in playlist {name!r}")
        self._playlists[name].remove(title)

    def get_playlist(self, name):
        self._require_playlist(name)
        return list(self._playlists[name])

    def get_playlist_by_artist(self, name, artist):
        self._require_playlist(name)
        return [t for t in self._playlists[name] if self._songs[t][0] == artist]

    def get_songs_by_artist(self, artist):
        return [t for t, (a, _) in self._songs.items() if a == artist]

    def get_artists(self):
        artists = []
        for artist, _ in self._songs.values():
            if artist not in artists:
                artists.append(artist)
        return artists

    def enqueue(self, title):
        self._require_song(title)
        self._queue.append(title)

    def play_next(self):
        if not self._queue:
            raise QueueEmpty("nothing is queued")
        return self._queue.pop(0)

    def get_queue(self):
        return list(self._queue)

    def _require_song(self, title):
        # Non-str titles are never stored, so they count as unknown too.
        if not isinstance(title, str) or title not in self._songs:
            raise KeyError(title)

    def _require_playlist(self, name):
        if not isinstance(name, str) or name not in self._playlists:
            raise KeyError(name)
