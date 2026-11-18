Make the accepted denominations in `vaults.py` adjustable, so that the same
program can count the coins of another currency.

- `Vaults` takes a new keyword argument `denominations=None`. `None` keeps
  the denominations accepted until now: 1, 2, 5, 10, 20, 50, 100 and 200.
  Otherwise it must be a non-empty `list` of different `int`s, each greater
  than 0, in any order. Anything else, including an empty list or a list
  that repeats a value, raises `ValueError`.
- Add `Vaults.get_accepted() -> list[int]`, which returns the accepted
  denominations, smallest first.
- `deposit` accepts exactly these denominations; any other raises
  `ValueError` and changes nothing, as before.
- Each `Vaults` object has its own setting. Every other rule stays as it
  is, and `undo` still restores the exact earlier state.

All existing behavior must keep working.
