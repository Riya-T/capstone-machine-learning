Give the slots in `vending.py` a capacity, so a slot can never hold more
items than fit in it.

- `add_slot` takes a new keyword argument `capacity=None`. `None` means the
  slot has no limit. Otherwise it must be an `int` greater than 0; anything
  else raises `ValueError` and no slot is added.
- Add `class SlotFull(VendingError)` to `vending.py`.
- `restock` raises `SlotFull` and changes nothing when the count would take
  the slot's stock above its capacity. Filling a slot exactly to its
  capacity is allowed.
- Add `VendingMachine.get_capacity(slot_id) -> int | None`, which returns the
  slot's capacity, or `None` when it has no limit.
- Add `VendingMachine.set_capacity(slot_id, capacity)`, which replaces the
  capacity; `None` removes the limit. It raises `KeyError` for a slot that
  does not exist, `ValueError` for an invalid capacity, and `VendingError`
  if the new capacity is valid but the slot already holds more items than
  it. In each case nothing changes. A capacity equal to the current stock
  is fine.
- `get_capacity` raises `KeyError` for a slot that does not exist.
- Which error is raised when one call has several of these problems (for
  example a bad capacity for a slot id that already exists) is unspecified.

All existing behavior must keep working.
