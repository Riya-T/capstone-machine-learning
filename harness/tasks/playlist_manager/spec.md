# Music library

Write a module `playlist.py` that keeps a collection of songs, named
playlists built from those songs, and a queue of songs waiting to be played.

## Interface

```python
class LibraryError(Exception): ...


class QueueEmpty(LibraryError): ...


class MusicLibrary:
    def __init__(self): ...
    def add_song(self, title: str, artist: str, duration: int) -> None: ...
    def create_playlist(self, name: str) -> None: ...
    def add_to_playlist(self, name: str, title: str) -> None: ...
    def get_playlist(self, name: str) -> list[str]: ...
    def enqueue(self, title: str) -> None: ...
    def play_next(self) -> str: ...
    def get_queue(self) -> list[str]: ...
```

All durations are whole seconds, as `int`.

## Songs

- `add_song(title, artist, duration)` adds a song. The title and the artist
  must be non-empty strings and the duration must be an `int` greater
  than 0, or `ValueError` is raised. A title that has already been added
  raises `LibraryError`. Songs are identified by their title.
- Every other method raises `KeyError` when given a title that has not been
  added, including values that are not strings at all, such as `None` or `1`.

## Playlists

- `create_playlist(name)` creates an empty playlist. An empty name raises
  `ValueError`, and a name that already exists raises `LibraryError`.
- `add_to_playlist(name, title)` appends the song to the end of the
  playlist. A song can be in a playlist only once: adding it again raises
  `LibraryError`. The same song may be in any number of playlists.
- `get_playlist(name)` returns the playlist's titles in the order they were
  added.
- `add_to_playlist` and `get_playlist` raise `KeyError` for a playlist name
  that does not exist, including values that are not strings.

## Queue

- `enqueue(title)` adds the song to the end of the queue. The same song may
  be queued any number of times.
- `play_next()` removes the song at the front of the queue and returns its
  title. When the queue is empty it raises `QueueEmpty`.
- `get_queue()` returns the queued titles, next to play first.

When a call has several problems, the first of these is raised:

1. `KeyError` for an unknown playlist (for `add_to_playlist`, the playlist is
   checked before the song);
2. `KeyError` for an unknown song;
3. `ValueError` for an invalid argument;
4. `LibraryError` for a song or playlist that is already there.

A failed call has no effect: if a method raises, every playlist and the
queue are unchanged, and no song is added.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names and titles that are not strings passed to `add_song` or
`create_playlist`, `bool` durations, two songs with the same artist and
duration, what happens if a returned list is changed, the text of error
messages, saving the library to a file, and use from several threads.
