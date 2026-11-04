Let the library in `playlist.py` be searched by artist.

- Add `MusicLibrary.get_songs_by_artist(artist) -> list[str]`: the titles
  of every song by that artist, in the order the songs were added. An
  artist with no songs gives `[]`; no error is raised for it.
- Add `MusicLibrary.get_artists() -> list[str]`: every artist that has at
  least one song in the library, in the order their first songs were added.
  An artist with several songs is listed once, at the place of their first
  song. For example, after adding songs by `"Pia"`, `"Nina"`, `"Pia"`,
  `"Omar"` and `"Nina"`, in that order, `get_artists()` is
  `["Pia", "Nina", "Omar"]`.
- Add `MusicLibrary.get_playlist_by_artist(name, artist) -> list[str]`: the
  titles in that playlist by that artist, in playlist order. It raises
  `KeyError` for a playlist that does not exist; an artist with no songs in
  the playlist gives `[]`.
- Artists are compared exactly: `"Nina"` and `"nina"` are different
  artists.

All existing behavior must keep working.
