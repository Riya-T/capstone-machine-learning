Add an undo to `setlists.py`, so that a mistake, such as merging the wrong
two setlists, can be taken back.

- Add `Setlists.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the calls that change the
  setlists: `create_setlist`, `add_song`, `remove_song`, `move_song`,
  `merge_setlists`, `drop_song_everywhere`, and every other method that
  changes the setlists, including methods added by other changes. Each
  further `undo` goes one call further back.
- Undoing a call puts every setlist, with its songs in their order, and the
  list of setlists in its order, back to exactly what they were just before
  that call. A call that changed several setlists is undone as a whole by
  one `undo`:
  - an undone `remove_song` puts the title back at its old position;
  - an undone `move_song` puts the title back at its old position in
    `from_setlist` and takes it out of `to_setlist`;
  - an undone `merge_setlists` brings `source` back, with its songs in
    their order and at its original position in `get_setlists()`, and
    takes the songs it appended out of `into` again (titles that were
    skipped stay where they are); the name of `source` is in use again;
  - an undone `drop_song_everywhere` puts the title back into every
    setlist it was removed from, each time at its old position;
  - an undone `create_setlist` removes the setlist, and its name may then
    be created again.
- A `merge_setlists` that appended 0 songs, or a `drop_song_everywhere`
  that removed the title from no setlist, is still a call: `undo` reverses
  it like any other (an undone merge of an empty setlist brings that
  setlist back).
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `SetlistError` and changes
  nothing.

All existing behavior must keep working.
