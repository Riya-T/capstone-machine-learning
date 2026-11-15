Let each paddock in `farm.py` limit which species may be put into it, for
example a paddock with a low fence that only takes sheep.

- Add `Farm.set_allowed(paddock, species)` and
  `Farm.get_allowed(paddock) -> list[str] | None`. Both raise `KeyError`
  for a paddock that is not in use.
- The `species` argument of `set_allowed` is either `None`, meaning any
  species may enter, or a `list` of species, each a non-empty `str`.
  Duplicates in the list are allowed and ignored, and an empty list means
  no species may enter. Anything else, including a single `str`, raises
  `ValueError` (after the `KeyError` check) and changes nothing. Each call
  replaces the paddock's earlier setting.
- Every new paddock starts with `None`, so any species may enter it. That
  includes a paddock added again under the name of a closed one: it does
  not keep the closed paddock's setting.
- `get_allowed(paddock)` returns `None`, or the allowed species without
  duplicates in alphabetical order.
- Add `class NotAllowed(FarmError)` to `farm.py`.
- Every call that puts animals into a paddock checks that their species is
  allowed there: `arrive`, and the receiving paddock (`to_paddock`) of
  `move`, `move_all` and `close_paddock`. If a species is not allowed, the
  call raises `NotAllowed` and changes nothing.
- `move_all` and `close_paddock` check every species they would move
  before moving any animal: if even one of them is not allowed, nothing
  moves and `close_paddock` does not close the paddock. Only species with
  animals in the paddock are checked, so `move_all` or `close_paddock` from
  an empty paddock never raises `NotAllowed`.
- `NotAllowed` is checked after every other check: when a call would also
  raise `KeyError`, `ValueError` or `NotEnoughAnimals`, that error is
  raised instead.
- A setting does not affect animals already in the paddock: they stay,
  and can depart or be moved out as before. The setting of the paddock the
  animals leave is never checked.
- No other method checks the allowed species, and `set_allowed` changes no
  counts.

All existing behavior must keep working.
