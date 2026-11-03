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
  that makes `net = get_net_owed(lender, borrower)` above 0. Largest net
  first; pairs with equal nets may come in any order.
- A user's net position is the sum of `get_net_owed(name, other)` over all
  the other users: what the others owe them, minus what they owe the
  others.
- Add `IouTracker.get_creditors() -> list[str]`: the names of all users
  whose net position is above 0, the largest net position first. Users
  with equal net positions come in the order they were added.
- Add `IouTracker.get_debtors() -> list[str]`: the names of all users whose
  net position is below 0, the most negative first, with the same tie rule.

For example, after alice lends bob 1000, bob lends alice 400 and carol
lends alice 100:

```python
tracker.get_owed("alice", "bob")      # 1000, as before
tracker.get_owed("bob", "alice")      # 400, as before
tracker.get_net_owed("alice", "bob")  # 600
tracker.get_net_owed("bob", "alice")  # -600
tracker.get_net_debts()  # [("alice", "bob", 600), ("carol", "alice", 100)]
# net positions: alice 600 - 100 = 500, bob -600, carol 100
tracker.get_creditors()  # ["alice", "carol"]
tracker.get_debtors()    # ["bob"]
```

`get_owed` and `get_ious` stay exactly as they are: `get_owed` keeps
counting each direction on its own. All existing behavior must keep
working.
