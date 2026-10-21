Let a spot in `garage.py` be reserved for a vehicle before it arrives.

- Add `Garage.reserve(level_id, plate)`, which holds one free spot on the
  level for that plate. Errors, in this order: `KeyError` for a level that
  was not added; `ValueError` for a plate that is not a non-empty `str`;
  `GarageError` if the plate is parked or already has a reservation on any
  level; `GarageFull` if the level has no free spot. On error nothing
  changes.
- A reserved spot is not free: `get_free_spots` no longer counts it, and no
  other vehicle can take it. A level whose free spots are all reserved is
  full for every other vehicle, which goes on to the next level or gets
  `GarageFull` as usual.
- When the plate with the reservation enters, it parks on the reserved
  level, even when an earlier level has free spots, and the reservation
  ends. That entry does not change the level's free spot count, since the
  spot was already held.
- Add `Garage.cancel_reservation(plate)`, which ends the reservation and
  makes the spot free again. It raises `KeyError` when the plate has no
  reservation, including non-str values.
- Add `Garage.has_reservation(plate) -> bool`: `True` while the plate has a
  reservation, `False` otherwise, including for non-str values.
- Add `Garage.get_reserved(level_id) -> list[str]`: the plates with a
  reservation on the level, in the order the reservations were made. It
  raises `KeyError` for a level that was not added, including non-str
  values.
- A plate with a reservation is not parked: it does not appear in
  `get_vehicles`, and `get_level` and `leave` raise `KeyError` for it.
- Once the vehicle has entered and left again, it enters like any other
  vehicle the next time.

All existing behavior must keep working.
