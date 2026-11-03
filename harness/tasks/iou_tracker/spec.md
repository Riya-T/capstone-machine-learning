# IOU tracker

Write a module `ious.py` that keeps track of money lent within a group of
users: the list of every IOU recorded between them, and how much each
borrower owes each lender.

## Interface

```python
class IouError(Exception): ...


class IouTracker:
    def __init__(self): ...
    def add_user(self, name: str) -> None: ...
    def get_users(self) -> list[str]: ...
    def record_iou(self, lender: str, borrower: str, amount: int) -> None: ...
    def get_ious(self) -> list[tuple[str, str, int]]: ...
    def get_owed(self, lender: str, borrower: str) -> int: ...
```

All amounts are whole cents, as `int`. A method that takes two names takes
the lender first and the borrower second, and every
`(lender, borrower, amount)` tuple has them in that order too.

## Users

`add_user(name)` adds a user. It raises:

- `ValueError` if `name` is an empty string;
- `IouError` if `name` is already a user.

`get_users()` returns the names of all users, in the order they were added.

`record_iou` and `get_owed` raise `KeyError` when they are given a name that
is not a user; `get_owed` does not return 0 for such a name. `None` counts
as a name that is not a user: `KeyError`, not `ValueError`.

## IOUs

`record_iou(lender, borrower, amount)` records one IOU: `lender` lent
`amount` to `borrower`. It raises:

- `KeyError` if `lender` or `borrower` is not a user;
- `ValueError` if `amount` is not greater than 0, such as `0` or `-5`;
- `ValueError` if `lender` and `borrower` are the same name.

`get_ious()` returns every IOU recorded so far, as
`(lender, borrower, amount)` tuples, oldest first. Each call to
`record_iou` adds one tuple at the end, even when the same lender has lent
to the same borrower before.

`get_owed(lender, borrower)` returns how much `borrower` owes `lender`: the
sum of the amounts of the tuples in `get_ious()` with this lender and this
borrower, or 0 if there are none. IOUs in the other direction do not count:
an IOU in which `borrower` lent to `lender` never changes
`get_owed(lender, borrower)`.

A failed call has no effect: if a method raises, `get_ious()` and every
`get_owed` are unchanged.

## Example

```python
tracker = IouTracker()
for name in ["alice", "bob", "carol"]:
    tracker.add_user(name)
tracker.record_iou("alice", "bob", 300)   # alice lends bob 300
tracker.record_iou("carol", "alice", 50)  # carol lends alice 50
tracker.record_iou("alice", "bob", 200)   # alice lends bob 200 more
tracker.record_iou("bob", "alice", 100)   # bob lends alice 100

tracker.get_ious()
# [("alice", "bob", 300), ("carol", "alice", 50), ("alice", "bob", 200), ("bob", "alice", 100)]
tracker.get_owed("alice", "bob")    # 500: 300 + 200
tracker.get_owed("bob", "alice")    # 100: only bob's IOU to alice
tracker.get_owed("carol", "alice")  # 50
tracker.get_owed("alice", "carol")  # 0: alice never lent to carol
tracker.get_owed("alice", "dave")   # raises KeyError: dave is not a user
tracker.record_iou("bob", "bob", 10)    # raises ValueError
tracker.record_iou("alice", "bob", 0)   # raises ValueError
tracker.get_ious()                  # the same 4 IOUs: failed calls add nothing
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when a call has several problems (such as a
name that is not a user and an amount of 0), `get_owed` with the same name
twice, amounts that are not `int`s, such as `1.5`, `"10"` or `None`, `bool`
amounts, names that are not strings passed to `add_user`, other values that
are not strings, such as `7`, passed as a name, what happens if a returned
list is changed, the text of error messages, saving the tracker to a file,
and use from several threads.
