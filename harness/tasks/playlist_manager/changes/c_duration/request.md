Report how long things take to play in `playlist.py`. All results are whole
seconds, as `int`.

- Add `MusicLibrary.get_playlist_duration(name) -> int`: the sum of the
  durations of the songs in that playlist. An empty playlist gives 0. It
  raises `KeyError` for a playlist that does not exist.
- Add `MusicLibrary.get_queue_duration() -> int`: the sum of the durations
  of everything in the queue, counting a song once for every copy of it
  that is queued. An empty queue gives 0.
- Add `MusicLibrary.get_time_played() -> int`: the total duration of every
  song that `play_next` has returned since the library was created. It
  starts at 0 and only grows. A song that is later removed with
  `remove_song` still counts, with the duration it had when it was played,
  even if a new song with the same title is added afterwards.
- Add `MusicLibrary.get_song_time_played(title) -> int`: how long that song
  has been played, that is its duration for every time `play_next` has
  returned it since the song was added. A song that has not been played
  gives 0. It raises `KeyError` for a title that is not in the library.
- A removed title that is added again is a fresh song: its own time played
  starts again from 0, while `get_time_played()` keeps every play. For
  example, if `"Blue"` (200 seconds) is played twice, removed, added again
  with 5 seconds and played once, `get_song_time_played("Blue")` is 5 and
  `get_time_played()` is 405.
- Failed calls change none of these values.

All existing behavior must keep working.
