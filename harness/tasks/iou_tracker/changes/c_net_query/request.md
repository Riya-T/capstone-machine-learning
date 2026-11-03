Add net views of the debts to `ious.py`, where the two directions between
a pair of users cancel each other out.

- Add `IouTracker.get_net_owed(lender, borrower) -> int`:
  `get_owed(lender, borrower)` minus `get_owed(borrower, lender)`. It is
  negative when `get_owed(borrower, lender)` is the larger of the two, and
  0 when they are equal. It raises `KeyError` for a name that is not a user
  and `ValueError` when both names are the same.
- Add `IouTracker.get_net_debts() -> list[tuple[str, str, int]]`: one
  `(lender, borrower, net)` tuple for each pair of users whose two
  directions do not cancel out exactly, with the two names in the order
  that makes `net = get_net_owed(lender, borrower)` above 0. Largest first;
  pairs with equal amounts may come in any order, as in `get_debts`.
- A user's net position is `get_total_lent(name)` minus
  `get_total_borrowed(name)`.
- Add `IouTracker.get_creditors() -> list[str]`: the names of all users
  whose net position is above 0, the largest net position first. Users
  with equal net positions come in the order they were added.
- Add `IouTracker.get_debtors() -> list[str]`: the names of all users whose
  net position is below 0, the most negative first, with the same tie rule.

`get_owed`, `get_debts`, `get_total_lent` and `get_total_borrowed` keep
counting each direction on its own, exactly as before. All existing
behavior must keep working.
