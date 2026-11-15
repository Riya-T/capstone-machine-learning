Give each freezer in `freezers.py` a capacity: the most samples it may
hold.

- Add `Freezers.set_capacity(freezer_id, samples)` and
  `Freezers.get_capacity(freezer_id) -> int | None`. Both raise `KeyError`
  for a freezer id that is not in use. Every freezer starts with a capacity
  of `None`, which means no limit.
- A capacity must be an `int` that is 0 or more, or `None`; anything else
  raises `ValueError` and changes nothing. `set_capacity` checks the
  freezer id before the capacity. Whether `True` and `False` count as an
  `int` is unspecified.
- A capacity may be set below the number of samples the freezer holds
  already. Those samples stay where they are, but no more can go in until
  enough have left.
- Add `class Full(FreezerError)` to `freezers.py`.
- Every call that puts samples into a freezer raises `Full`, and changes
  nothing, if that freezer would then hold more samples than its capacity.
  This applies to `store`, and to the receiving freezer of `move`,
  `move_all` and `remove_freezer`. Only the receiving freezer's capacity
  counts; samples may always leave a freezer.
- `move_all` and `remove_freezer` move all the samples or none: if not all
  of them fit, they raise `Full` and move nothing, and `remove_freezer`
  does not remove the freezer.
- Moving 0 samples never raises `Full`, even into a freezer that is over
  its capacity.
- `Full` is checked after every check that already exists: when a call also
  has one of those problems (a freezer id that is not in use, a sample id
  that is not stored, a move to the freezer the sample is already in, the
  same freezer given twice, or a sample id that is stored already), that
  error is raised instead.
- No other method checks capacities, and setting a capacity moves no
  samples.

All existing behavior must keep working.
