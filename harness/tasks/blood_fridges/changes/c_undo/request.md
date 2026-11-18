Add an undo to `blood_bank.py`, so a mistake in handling the blood can be
taken back.

- Add `BloodBank.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the methods that change the bank:
  `add_fridge`, `store`, `take`, `transfer_all` and `retire_fridge`, and any
  other method of the class that changes unit counts or the list of
  fridges. Each further `undo` goes one call further back.
- Undoing a call puts every unit count, and the list of fridges in its
  order, back exactly as they were just before that call. A call that
  changed several things is undone as a whole by one `undo`:
  - an undone `transfer_all` puts every unit back into the fridge it came
    from, and the receiving fridge holds what it held before;
  - an undone `retire_fridge` brings the retired fridge back, with its
    units and at its original position in `get_fridges()`, and takes those
    units out of the fridge they were moved into; its name is in use again;
  - an undone `add_fridge` removes the fridge, and its name may then be
    added again.
- A `transfer_all` or `retire_fridge` that moved 0 units is still a call:
  `undo` reverses it like any other (an undone `retire_fridge` of an empty
  fridge brings the fridge back).
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods, and to `undo` itself, are not recorded either and are
  never undone. There is no redo.
- With nothing left to undo, `undo` raises `BloodBankError` and changes
  nothing.

All existing behavior must keep working.
