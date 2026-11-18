Add an undo to `vaults.py`, so that a mistake, such as consolidating into
the wrong vault, can be taken back.

- Add `Vaults.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among the calls that change the vaults:
  `add_vault`, `deposit`, `withdraw`, `consolidate`, `close_vault`, and
  every other method that changes the vaults or their coins, including
  methods added by other changes. Each further `undo` goes one call further
  back.
- Undoing a call puts every count, and the list of vaults in its order,
  back to exactly what they were just before that call. A call that moved
  the coins of several denominations is undone as a whole by one `undo`:
  - an undone `consolidate` puts every coin it moved back into the vault
    it came from;
  - an undone `close_vault` brings the closed vault back, with all its
    coins and at its original position in `get_vaults()`, and takes those
    coins out of the vault they were moved into; its name is in use again;
  - an undone `add_vault` removes the vault, and its name may then be added
    again.
- A `consolidate` or `close_vault` that moved 0 coins is still a call:
  `undo` reverses it like any other (an undone `close_vault` of an empty
  vault brings the vault back).
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `VaultError` and changes
  nothing.

All existing behavior must keep working.
