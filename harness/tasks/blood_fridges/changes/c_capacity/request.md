Give the fridges in `blood_bank.py` a capacity: the most units a fridge can
hold in total, counting every blood type together.

- `add_fridge` takes a new keyword argument: `add_fridge(name,
  capacity=None)`. `None`, the default, means the fridge has no limit.
  Otherwise the capacity must be an `int` greater than 0; anything else
  raises `ValueError` and adds no fridge.
- Add `BloodBank.get_capacity(fridge) -> int | None`, which returns the
  fridge's capacity (`None` for no limit). It raises `KeyError` for a fridge
  that is not in use.
- Add `class FridgeFull(BloodBankError)` to `blood_bank.py`.
- A fridge never holds more units in total than its capacity; holding
  exactly its capacity is fine. Every call that puts units into a fridge
  checks the receiving fridge: `store`, and the fridge the units go to in
  `transfer_all` (`to_fridge`) and `retire_fridge` (`into`). If the
  receiving fridge would end up holding more than its capacity, the call
  raises `FridgeFull` and changes nothing.
- `transfer_all` and `retire_fridge` move all of the units or none of them:
  when they raise `FridgeFull`, no unit moves, and `retire_fridge` does not
  retire the fridge.
- Taking units out of a fridge, or moving them out of it, never checks that
  fridge's capacity.
- When a call would raise `FridgeFull` and another error too, which of them
  is raised is unspecified.
- `undo` keeps working as before: it puts back exactly the state from just
  before the undone call, and a fridge brought back by an undone
  `retire_fridge` has its capacity again.

All existing behavior must keep working.
