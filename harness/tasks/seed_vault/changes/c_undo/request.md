Add an undo to `vault.py`, so a mistake in sorting the seeds can be taken
back.

- Add `SeedVault.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the calls that change the vault:
  `add_drawer`, `deposit`, `transfer`, `transfer_all` and `retire_drawer`,
  and every other method of `SeedVault` that changes the vault, whether it
  exists now or is added later. Each further `undo` goes one call further
  back.
- Undoing a call puts the vault back exactly as it was just before that
  call: every count in every drawer, and the list of drawers in its order.
  One `undo` takes back the whole call, even when the call moved several
  varieties:
  - an undone `transfer` or `transfer_all` takes the packets out of the
    receiving drawer and back to the drawer they came from, so both drawers
    hold exactly what they held before;
  - an undone `retire_drawer` brings the retired drawer back, with all its
    packets, at its original position in `get_drawers()` (not at the end),
    and takes those packets out of the drawer they were moved into; its
    name is in use again;
  - an undone `add_drawer` removes the drawer, and its name may then be
    added again.
- A `transfer_all` or `retire_drawer` that moved 0 packets is still a call:
  `undo` reverses it like any other (an undone `retire_drawer` of an empty
  drawer brings the drawer back).
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `VaultError` and changes
  nothing.

All existing behavior must keep working.
