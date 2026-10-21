Let a waiting passenger in `elevators.py` cancel their call, for example
when they decide to take the stairs.

- Add `Building.cancel_call(passenger_id)`. The passenger stops waiting: they
  leave their floor's waiting list, the others on that floor keep their
  order, and no car picks the passenger up.
- It raises `KeyError` for an id that has no call: one that was never used,
  or whose call was already cancelled. It raises `ElevatorError` for a
  passenger who already got into a car, whether still riding or arrived. In
  each case nothing changes. `KeyError` is checked first.
- After a cancel the id is free again: a new `call` with it is accepted, on
  any floor, and joins the end of that floor's waiting list.
- A cancelled call never appears in `get_delivered`.
- Add `Building.get_cancelled() -> list[str]`: the ids of every cancelled
  call, oldest first. An id that was called, cancelled, called again and
  cancelled again appears twice.

All existing behavior must keep working.
