Make the way `setlists.py` compares song titles adjustable, because band
members type the same title with different capital letters.

- `Setlists` takes a new keyword argument `ignore_case=False`. With
  `False`, titles are compared exactly, as until now. With `True`, two
  titles count as the same song when they are equal after `.lower()`, for
  example `"Hey Jude"` and `"hey JUDE"`. Any value other than `True` or
  `False` raises `ValueError`.
- Add `Setlists.get_ignore_case() -> bool`, which returns the setting.
- With `ignore_case=True` the setting applies wherever titles are compared:
  - `add_song` raises `SetlistError` when the setlist already holds the
    title in any capitals;
  - `remove_song`, `move_song` and `drop_song_everywhere` find the title in
    any capitals, and `move_song` raises `SetlistError` when `to_setlist`
    already holds it in any capitals;
  - `merge_setlists` skips the songs of `source` that `into` already holds
    in any capitals;
  - and so does every other method that compares titles.
- A song keeps the spelling it was added with: `get_songs` returns every
  title exactly as it was added, also after `move_song` or
  `merge_setlists` moved it, whatever capitals the call used.
- Each `Setlists` object has its own setting. Every other rule stays as it
  is, and `undo` still restores the exact earlier state.

All existing behavior must keep working.
