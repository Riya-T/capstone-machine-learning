# IOU tracker

Write a module `ious.py` that keeps track of who owes money to whom in a
group of users.

## Interface

```python
class IouError(Exception): ...


class IouTracker:
    def __init__(self): ...
    def add_user(self, name: str) -> None: ...
    def record_iou(self, lender: str, borrower: str, amount: int) -> None: ...
    def get_owed_to(self, name: str) -> list[tuple[str, int]]: ...
    def get_owed_by(self, name: str) -> list[tuple[str, int]]: ...
    def get_balance(self, name: str) -> int: ...
    def get_history(self, name: str) -> list[tuple[str, str, int]]: ...
    def get_users(self) -> list[str]: ...
```

All amounts are whole cents, as `int`.

## Users

- `add_user(name)` adds a user who owes nothing and is owed nothing. An
  empty name raises `ValueError`, and adding a name that is already a user
  raises `IouError`.
- `get_users()` returns the names of all users, in the order they were added.
- Every other method raises `KeyError` when given a name that is not a user,
  including values that are not strings at all, such as `None` or `1`.

## IOUs

- `record_iou(lender, borrower, amount)` records that `borrower` now owes
  `lender` another `amount`. The amount must be an `int` greater than 0, or
  `ValueError` is raised. A user cannot owe themselves: the same name for
  lender and borrower raises `ValueError`.
- What a user owes another user is the sum of the IOUs between them in that
  direction. Debts in the two directions are kept apart: if alice lends bob
  1000 and bob lends alice 400, then bob owes alice 1000 and alice owes
  bob 400.
- `get_owed_to(name)` returns one `(borrower, amount)` tuple for every user
  who owes `name` something, largest amount first. Users with equal amounts
  come in the order they were added, so sorting with `reverse=True` is
  wrong (it reverses the ties too). For example, if carol and then bob
  were added before alice, and each borrows 100 from alice, then
  `get_owed_to("alice")` is `[("carol", 100), ("bob", 100)]`.
- `get_owed_by(name)` returns one `(lender, amount)` tuple for every user
  that `name` owes something, largest amount first, with the same tie rule.
- `get_balance(name)` returns everything owed to `name` minus everything
  `name` owes. It is negative when `name` owes more than they are owed.

When a call has several problems, the first of these is raised:

1. `KeyError` for a name that is not a user (for `record_iou`, the lender is
   checked before the borrower);
2. `ValueError` for an invalid amount;
3. `ValueError` for a lender and borrower with the same name.

## History

`get_history(name)` returns every IOU in which `name` is the lender or the
borrower, oldest first, as `(lender, borrower, amount)` tuples. IOUs between
two other users are not included.

A failed call has no effect: if a method raises, every debt and every
history is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_user`, `bool` amounts,
what happens if a returned list is changed, the text of error messages,
saving the tracker to a file, and use from several threads.
