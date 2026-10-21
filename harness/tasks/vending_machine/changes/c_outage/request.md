Let slots in `vending.py` be taken out of order, for example while a jammed
spiral is being repaired.

- Add `VendingMachine.disable_slot(slot_id)`,
  `VendingMachine.enable_slot(slot_id)` and
  `VendingMachine.is_disabled(slot_id) -> bool`. All three raise `KeyError`
  for a slot that does not exist. New slots are enabled. Disabling a
  disabled slot, or enabling an enabled one, does nothing.
- Add `class SlotDisabled(VendingError)` to `vending.py`.
- While a slot is disabled, `buy` on it raises `SlotDisabled` and changes
  nothing. `SlotDisabled` is checked after `KeyError` and before `SoldOut`
  and `NotEnoughCredit`.
- `restock` and `get_stock` still work on a disabled slot, and `get_slots`
  still lists it.
- Add `VendingMachine.get_working_slots() -> list[str]`: the ids of the
  slots that are not disabled, in the order they were added.
- Disabling and enabling a slot does not change its stock or the credit.

All existing behavior must keep working.
