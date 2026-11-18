# Coin vaults

Write a module `vaults.py` that keeps track of the coins kept in a set of
vaults: how many coins of each denomination each vault holds, as coins are
deposited, withdrawn and moved from one vault to another.

## Interface

```python
class VaultError(Exception): ...


class NotEnoughCoins(VaultError): ...


class Vaults:
    def __init__(self): ...
    def add_vault(self, name: str) -> None: ...
    def deposit(self, vault: str, denomination: int, count: int) -> None: ...
    def withdraw(self, vault: str, denomination: int, count: int) -> None: ...
    def consolidate(self, from_vault: str, to_vault: str) -> int: ...
    def close_vault(self, name: str, into: str) -> int: ...
    def get_count(self, vault: str, denomination: int) -> int: ...
    def get_denominations(self, vault: str) -> list[int]: ...
    def get_vaults(self) -> list[str]: ...
```

Vault names are non-empty strings; denominations and counts are `int`.

## Vaults

- `add_vault(name)` adds an empty vault. A name that is already in use
  raises `VaultError`.
- `get_vaults()` returns the names of the vaults in use, in the order they
  were added.
- Every other method raises `KeyError` when given a vault name that is not
  in use: one that was never added, or one that was closed.

## Coins

- A denomination is the value of a coin in cents. The accepted
  denominations are 1, 2, 5, 10, 20, 50, 100 and 200; `deposit` with any
  other denomination raises `ValueError`.
- A count must be greater than 0; otherwise `deposit` and `withdraw` raise
  `ValueError`.
- `deposit(vault, denomination, count)` adds `count` coins of that
  denomination to the vault. `withdraw(vault, denomination, count)` takes
  them out. Withdrawing more coins of a denomination than the vault holds
  (including a denomination it holds none of) raises `NotEnoughCoins`.
- `get_count(vault, denomination)` returns how many coins of that
  denomination the vault holds: 0 if it holds none.
- `get_denominations(vault)` returns the denominations the vault holds at
  least one coin of, smallest first. A denomination whose coins have all
  left the vault (by `withdraw`, `consolidate` or `close_vault`) is no
  longer listed.

## Moving every coin

- `consolidate(from_vault, to_vault)` moves every coin of every
  denomination from `from_vault` into `to_vault` and returns how many coins
  it moved in total. Afterwards `from_vault` is empty but still in use.
  Consolidating an empty vault is not an error: nothing changes and it
  returns 0.
- `close_vault(name, into)` moves every coin of every denomination from
  vault `name` into vault `into`, then closes vault `name`: it is no longer
  listed by `get_vaults()`, and every method treats it as not in use. It
  returns how many coins it moved in total (0 if the vault was empty). The
  other vaults keep their order.
- `consolidate` and `close_vault` raise `ValueError` when both names are
  the same.

```python
v = Vaults()
v.add_vault("till")
v.add_vault("safe")
v.deposit("till", 50, 4)
v.deposit("till", 10, 3)
v.deposit("safe", 50, 1)
v.consolidate("till", "safe")  # returns 7
v.get_count("safe", 50)        # 5
v.get_denominations("safe")    # [10, 50]
v.get_denominations("till")    # []
v.close_vault("till", "safe")  # returns 0
v.get_vaults()                 # ["safe"]
```

Python note: a `dict` must not gain or lose keys while a `for` loop runs
over it (Python raises `RuntimeError`); if a loop over a vault's coins can
add or remove entries, loop over a copy such as `list(coins.items())`.

## Errors

Which error is raised when a call has more than one problem (for example a
vault that is not in use and a count of 0) is unspecified.

A failed call has no effect: if a method raises, every count and the list
of vaults are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it.
This includes values of the wrong type (counts or denominations that are
not `int`, such as `1.5`, `"3"`, `True` or `None`, and vault names that are
not non-empty strings), which error is raised when a call has more than one
problem, `withdraw` and `get_count` with a denomination that is not
accepted, adding a vault under the name of a closed vault, what happens if
a returned list is changed, the text of error messages, saving the vaults
to a file, and use from several threads.
