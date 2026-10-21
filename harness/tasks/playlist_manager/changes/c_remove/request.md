Let songs be taken out again in `playlist.py`, both from a single playlist
and from the whole library.

- Add `MusicLibrary.remove_from_playlist(name, title)`. It takes the song
  out of that playlist; the other songs keep their order. It raises
  `KeyError` for a playlist that does not exist, then `KeyError` for a song
  that was never added, then `LibraryError` if the song is not in that
  playlist. The song stays in the library, in every other playlist and in
  the queue.
- Add `MusicLibrary.remove_song(title)`. It removes the song from the
  library, from every playlist it is in, and drops every copy of it from
  the queue, leaving everything else in order. It raises `KeyError` for a
  song that was never added or was already removed.
- Once removed, the title counts as unknown everywhere: `enqueue`,
  `add_to_playlist` and `remove_from_playlist` raise `KeyError` for it. The
  same title may then be added again with `add_song`, with any artist and
  duration, as a fresh song that is in no playlist.
- In each error case nothing changes.

All existing behavior must keep working.
