Give vaults in `vaults.py` an optional capacity, the most coins they may
hold, for example a small till that must be emptied often.

- `add_vault` takes a new keyword argument `capacity=None`: the most coins,
  of all denominations together, the vault may hold. `None` means no
  limit. Anything else must be an `int` greater than 0; otherwise
  `add_vault` raises `ValueError` and adds no vault.
- Add `Vaults.get_capacity(vault) -> int | None`, which returns the vault's
  capacity. It raises `KeyError` for a vault that is not in use.
- Add `class VaultFull(VaultError)` to `vaults.py`.
- Every call that puts coins into a vault checks that vault's capacity:
  `deposit`, the receiving vault of `consolidate` (`to_vault`) and of
  `close_vault` (`into`), and every other method that moves coins into a
  vault, including methods added by other changes. When the receiving
  vault would then hold more coins in total than its capacity, the call
  raises `VaultFull` and changes nothing: no coin moves, and `close_vault`
  does not close the vault. Holding exactly the capacity is allowed.
- Only the receiving vault is checked: the vault the coins leave is not,
  and `withdraw` never raises `VaultFull`.
- When a call would also raise another error, which error is raised is
  unspecified.
- `undo` still restores the exact earlier state: a vault brought back by
  undoing `close_vault` has its capacity again.

All existing behavior must keep working.
