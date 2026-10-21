"""Music library where songs can be removed and durations are summed up.

Planted bug (after c_remove and c_duration): the durations were added
correctly, but play_next was rewritten to record the time played and now
returns None on an empty queue instead of raising QueueEmpty. Never shown to
the writer or the editor; validate-tasks checks that the tests catch it.

Usage:
    from playlist import MusicLibrary
    library = MusicLibrary()
    library.add_song("Blue", "Nina", 200)
    library.enqueue("Blue")
    library.play_next()
    library.get_time_played()
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
        self._played = []  # (title, duration) of every song play_next returned

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
        if title in self._playlists[name]:
            raise LibraryError(f"{title!r} is already in playlist {name!r}")
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

    def get_playlist_duration(self, name):
        self._require_playlist(name)
        return self._total(self._playlists[name])

    def enqueue(self, title):
        self._require_song(title)
        self._queue.append(title)

    def play_next(self):
        if not self._queue:
            return None
        title = self._queue.pop(0)
        self._played.append((title, self._songs[title][1]))
        return title

    def get_queue(self):
        return list(self._queue)

    def get_queue_duration(self):
        return self._total(self._queue)

    def get_time_played(self):
        return sum(duration for _, duration in self._played)

    def _total(self, titles):
        return sum(self._songs[title][1] for title in titles)

    def _require_song(self, title):
        # Non-str titles are never stored, so they count as unknown too.
        if not isinstance(title, str) or title not in self._songs:
            raise KeyError(title)

    def _require_playlist(self, name):
        if not isinstance(name, str) or name not in self._playlists:
            raise KeyError(name)
