Let setlists in `setlists.py` be locked, for example once a setlist has been
printed for the stage, so that nothing changes it by mistake.

- Add `Setlists.lock(setlist)` and `Setlists.unlock(setlist)`. Both raise
  `KeyError` for a setlist that is not in use. New setlists are not
  locked. Locking a locked setlist, or unlocking one that is not locked,
  does nothing.
- Add `Setlists.get_locked() -> list[str]`, which returns the names of the
  locked setlists, in the order of `get_setlists()`.
- Add `class SetlistLocked(SetlistError)` to `setlists.py`.
- The songs of a locked setlist cannot change. `add_song`, `remove_song`,
  `move_song`, `merge_setlists`, and every other method that changes the
  songs of a setlist, including methods added by other changes, raise
  `SetlistLocked` and change nothing when a setlist they would change is
  locked:
  - for `move_song` and `merge_setlists` that is either of the two
    setlists (a locked `source` cannot be merged away);
  - `drop_song_everywhere` raises `SetlistLocked` when any setlist that
    holds the title is locked, and then removes the title from no setlist.
    Locked setlists that do not hold the title do not matter.
- When a call would also raise another error, which error is raised is
  unspecified.
- The `get_` methods work as before on locked setlists, and `unlock` lifts
  the lock.
- `lock` and `unlock` are recorded like the other calls that change the
  setlists, so `undo` reverses them too, and `undo` still restores the
  exact earlier state.

All existing behavior must keep working.
