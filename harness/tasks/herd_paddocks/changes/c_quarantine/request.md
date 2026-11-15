Let paddocks in `farm.py` be put in quarantine, for example while a sick
animal is being checked. No animal may enter or leave a quarantined
paddock.

- Add `Farm.quarantine(paddock)` and `Farm.release(paddock)`. Both raise
  `KeyError` for a paddock that is not in use. New paddocks are not
  quarantined. Quarantining a quarantined paddock, or releasing one that
  is not quarantined, does nothing.
- Add `class Quarantined(FarmError)` to `farm.py`.
- `arrive`, `depart`, `move`, `move_all` and `close_paddock` raise
  `Quarantined` and change nothing when any paddock named in the call is
  quarantined, whether animals would leave it or enter it. This holds even
  when no animal would actually move, for example `move_all` from an empty
  paddock, or closing an empty quarantined paddock.
- Order of errors: `Quarantined` is checked after the `KeyError` and
  `ValueError` checks and before every other check. So a paddock that is
  not in use, a count of 0 or less, or the same paddock on both sides is
  reported first; but when a call would also raise
  `NotEnoughAnimals` or `NotAllowed`, it raises `Quarantined` instead.
- Calls that move no animals work as before on a quarantined paddock:
  `set_allowed`, `get_allowed`, `get_count`, `get_species` and
  `get_paddocks`.
- `release` lifts the quarantine: the paddock works as before, including
  its allowed species.

All existing behavior must keep working.
