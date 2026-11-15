Let freezers in `freezers.py` be locked, for example while one is being
defrosted, so that no sample can go into it or come out of it.

- Add `Freezers.lock(freezer_id)` and `Freezers.unlock(freezer_id)`. Both
  raise `KeyError` for a freezer id that is not in use. Freezers start
  unlocked. Locking a locked freezer, or unlocking one that is not locked,
  does nothing.
- Add `class Locked(FreezerError)` to `freezers.py`.
- A call that would take a sample out of a locked freezer, or put one into
  it, raises `Locked` and changes nothing. That means:
  - `store` into a locked freezer;
  - `discard` of a sample whose freezer is locked;
  - `move` when the sample's freezer or `to_freezer` is locked;
  - `move_all` and `remove_freezer` when either of their two freezers is
    locked, even if there are no samples to move.
- Order of errors: `Locked` is checked after the `KeyError` and
  `ValueError` checks and before every other error. So a call with a
  `KeyError` or `ValueError` problem raises that error, not `Locked`; and
  a call into or out of a locked freezer raises `Locked`, not
  `FreezerError` for a sample id that is stored already, and not `Full`.
- Locks change nothing else: `add_freezer`, `find`, `set_capacity`,
  `get_capacity`, `get_samples` and `get_freezers` work as before on locked
  freezers, locking and unlocking move no samples, and capacities apply as
  before to calls that involve no locked freezer.

All existing behavior must keep working.
