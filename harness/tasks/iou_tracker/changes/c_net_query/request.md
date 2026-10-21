Add net views of the debts to `ious.py`, where the two directions between
a pair of users cancel each other out.

- Add `IouTracker.get_net_owed(a, b) -> int`: what `b` owes `a` minus what
  `a` owes `b`. It is negative when `a` owes `b` more. It raises `KeyError`
  for a name that is not a user (`a` is checked before `b`), then
  `ValueError` when both names are the same.
- Add `IouTracker.get_net_owed_to(name) -> list[tuple[str, int]]`: one
  `(user, net)` tuple for every other user whose net debt to `name` is
  above 0, largest first. Users with equal amounts come in the order they
  were added. It raises `KeyError` for a name that is not a user.
- Add `IouTracker.get_debtors() -> list[str]`: the names of all users whose
  balance is below 0, the most negative balance first, with the same tie
  rule.
- Add `IouTracker.get_creditors() -> list[str]`: the names of all users
  whose balance is above 0, the largest balance first, with the same tie
  rule.

`get_owed_to` and `get_owed_by` keep returning the amounts in one direction
only, exactly as before. All existing behavior must keep working.
