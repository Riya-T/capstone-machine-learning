Add two ways to look songs up across the setlists in `setlists.py`, to plan
which songs to rehearse.

- Add `Setlists.get_setlists_with(title) -> list[str]`, which returns the
  names of the setlists that hold the title, in the order of
  `get_setlists()`. A title that no setlist holds gives `[]`.
- Add `Setlists.get_common_songs(first, second) -> list[str]`, which
  returns the titles that are in both setlists, in their order in `first`.
  It raises `KeyError` when either setlist is not in use. When `first` and
  `second` are the same setlist, it returns all of that setlist's songs.
- Titles are compared exactly, as everywhere else. Neither method changes
  anything.

All existing behavior must keep working.
