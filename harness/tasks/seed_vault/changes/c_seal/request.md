Let drawers in `vault.py` be sealed, for example while a sample of their
seeds is out for a germination test. No packet may go into or come out of a
sealed drawer.

- Add `SeedVault.seal(drawer)` and `SeedVault.unseal(drawer)`. Both raise
  `KeyError` for a drawer that is not in use. Sealing a sealed drawer, or
  unsealing one that is not sealed, does nothing.
- Add `SeedVault.get_sealed() -> list[str]`: the names of the sealed
  drawers, in the order `get_drawers()` lists them.
- New drawers are not sealed.
- Add `class DrawerSealed(VaultError)` to `vault.py`.
- `deposit`, `transfer`, `transfer_all` and `retire_drawer` raise
  `DrawerSealed` and change nothing when any drawer named in the call is
  sealed, whether packets would leave it or go into it. This holds even
  when no packet would actually move, for example `transfer_all` from an
  empty drawer, or retiring an empty sealed drawer.
- When a call would also raise `KeyError`, `ValueError` or
  `NotEnoughSeeds`, which error it raises is unspecified.
- The other methods work as before on sealed drawers: `add_drawer`,
  `get_count` and `get_drawers`.
- `unseal` lifts the seal: the drawer works as before.
- `undo` still puts the vault back exactly as it was before the call it
  reverses, including which drawers are sealed: `seal` and `unseal` change
  the vault, so they are recorded like the other such calls (even one that
  did nothing), and `undo` itself never raises `DrawerSealed`.

All existing behavior must keep working.
