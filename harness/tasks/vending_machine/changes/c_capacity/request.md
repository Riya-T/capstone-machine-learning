Give the slots in `vending.py` a capacity, so a slot can never hold more
items than fit in it.

- `add_slot` takes a new keyword argument `capacity=None`. `None` means the
  slot has no limit. Otherwise it must be an `int` greater than 0 (not a
  `bool`); anything else raises `ValueError` and no slot is added. Like a
  bad price, a bad capacity is reported before the check that the slot
  already exists.
- Add `class SlotFull(VendingError)` to `vending.py`.
- `restock` raises `SlotFull` and changes nothing when the count would take
  the slot's stock above its capacity. Filling a slot exactly to its
  capacity is allowed. `SlotFull` is checked after `KeyError` and
  `ValueError`.
- Add `VendingMachine.get_capacity(slot_id) -> int | None`, which returns the
  slot's capacity, or `None` when it has no limit.
- Add `VendingMachine.set_capacity(slot_id, capacity)`, which replaces the
  capacity; `None` removes the limit. It raises `KeyError` for a slot that
  does not exist, then `ValueError` for an invalid capacity, then
  `VendingError` if the slot already holds more items than the new capacity.
  In each case nothing changes. A capacity equal to the current stock is
  fine.
- `get_capacity` raises `KeyError` for a slot that does not exist.

All existing behavior must keep working.
