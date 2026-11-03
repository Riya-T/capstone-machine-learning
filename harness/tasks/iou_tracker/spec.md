# IOU tracker

Write a module `ious.py` that keeps track of money lent within a group of
users: every IOU recorded between them, how much each borrower has to pay
back to each lender, and how much each user has lent and borrowed in total.

## Interface

```python
class IouError(Exception): ...


class IouTracker:
    def __init__(self): ...
    def add_user(self, name: str) -> None: ...
    def record_iou(self, lender: str, borrower: str, amount: int) -> None: ...
    def get_owed(self, lender: str, borrower: str) -> int: ...
    def get_debts(self) -> list[tuple[str, str, int]]: ...
    def get_total_lent(self, name: str) -> int: ...
    def get_total_borrowed(self, name: str) -> int: ...
    def get_history(self, name: str) -> list[tuple[str, str, int]]: ...
    def get_users(self) -> list[str]: ...
```

All amounts are whole cents, as `int`. A method that takes two names takes
the lender first and the borrower second, and every
`(lender, borrower, amount)` tuple has them in that order too.

## Users

- `add_user(name)` adds a user with no IOUs. An empty name raises
  `ValueError`, and adding a name that is already a user raises `IouError`.
- `get_users()` returns the names of all users, in the order they were added.
- Every other method raises `KeyError` when given a name that is not a user.
  `None` counts as a name that is not a user: `KeyError`, not `ValueError`.
  This includes `get_owed`: when either name is not a user, it raises
  `KeyError` and does not return 0.

## IOUs and debts

- `record_iou(lender, borrower, amount)` records one IOU: `lender` lent
  `amount` to `borrower`. The amount must be greater than 0, or
  `ValueError` is raised. A user cannot lend to themselves: the same name
  for lender and borrower raises `ValueError`.
- `get_owed(lender, borrower)` returns how much `borrower` has to pay back
  to `lender`: the sum of every IOU recorded with `lender` as the lender
  and `borrower` as the borrower, or 0 if there is none.
- The two directions are kept apart, not netted: an IOU in which bob lent
  to alice never counts towards `get_owed("alice", "bob")`, only towards
  `get_owed("bob", "alice")`.
- `get_debts()` returns every debt in the group: one
  `(lender, borrower, amount)` tuple for each lender and borrower where
  `get_owed(lender, borrower)` is above 0, with that sum as the amount,
  largest amount first. Several IOUs from the same lender to the same
  borrower make a single debt: after IOUs of 300 and 200 from alice to
  bob, `get_debts()` is `[("alice", "bob", 500)]`, one tuple, not two.

## Totals

- `get_total_lent(name)` returns the sum of every IOU in which `name` is
  the lender. This is the same as the sum of `get_owed(name, other)` over
  all the other users.
- `get_total_borrowed(name)` returns the sum of every IOU in which `name`
  is the borrower. This is the same as the sum of `get_owed(other, name)`
  over all the other users.
- Both are 0 for a user with no IOUs. Each IOU adds its amount to its
  lender's total lent and to its borrower's total borrowed, and to no other
  total. A user who has lent and borrowed has two totals above 0: they are
  never netted against each other.

## History

`get_history(name)` returns every IOU in which `name` is the lender or the
borrower, as `(lender, borrower, amount)` tuples, in the order they were
recorded. So each IOU is in two histories: its lender's and its
borrower's. Each call to `record_iou` is one entry of its own, even when
the same lender and borrower already have a debt: the history is not
summed like `get_owed`. IOUs between two other users are not included.

A failed call has no effect: if a method raises, every debt, every total
and every history is unchanged.

## Example

```python
tracker = IouTracker()
for name in ["alice", "bob", "carol"]:
    tracker.add_user(name)
tracker.record_iou("alice", "bob", 300)   # alice lends bob 300
tracker.record_iou("carol", "alice", 50)  # carol lends alice 50
tracker.record_iou("alice", "bob", 200)   # alice lends bob 200 more
tracker.record_iou("bob", "alice", 100)   # bob lends alice 100

tracker.get_owed("alice", "bob")    # 500: 300 + 200
tracker.get_owed("bob", "alice")    # 100
tracker.get_owed("alice", "carol")  # 0: alice never lent to carol
tracker.get_debts()
# [("alice", "bob", 500), ("bob", "alice", 100), ("carol", "alice", 50)]

tracker.get_total_lent("alice")      # 500: 300 + 200 to bob
tracker.get_total_borrowed("alice")  # 150: 50 from carol + 100 from bob
tracker.get_total_lent("bob")        # 100: to alice
tracker.get_total_borrowed("bob")    # 500: from alice
tracker.get_total_lent("carol")      # 50: to alice
tracker.get_total_borrowed("carol")  # 0

tracker.get_history("alice")
# [("alice", "bob", 300), ("carol", "alice", 50), ("alice", "bob", 200), ("bob", "alice", 100)]
tracker.get_history("bob")
# [("alice", "bob", 300), ("alice", "bob", 200), ("bob", "alice", 100)]
tracker.get_history("carol")
# [("carol", "alice", 50)]
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which of `KeyError` and `ValueError` is raised when a call has
both problems, `get_owed` with the same name twice, the order of debts with
equal amounts in `get_debts`, amounts that are not `int`s, such as `1.5`,
`"10"` or `None`, `bool` amounts, names that are not strings passed to
`add_user`, other values that are not strings, such as `7`, passed as a
name, what happens if a returned list is changed, the text of error
messages, saving the tracker to a file, and use from several threads.
