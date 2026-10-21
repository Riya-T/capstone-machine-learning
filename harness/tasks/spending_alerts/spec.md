# Spending alerts

Write a module `spending.py` that records what people spend, by account,
month and category, and warns when a category gets too expensive in a month.

## Interface

```python
class SpendingError(Exception): ...


class SpendingTracker:
    def __init__(self): ...
    def add_account(self, account_id: str) -> None: ...
    def get_accounts(self) -> list[str]: ...
    def record_payment(self, account_id: str, month: int, category: str, amount: int) -> int: ...
    def get_total(self, account_id: str, month: int) -> int: ...
    def get_category_total(self, account_id: str, month: int, category: str) -> int: ...
    def get_alerts(self, account_id: str, month: int) -> list[str]: ...
    def get_alert_months(self, account_id: str, category: str) -> list[int]: ...
```

All amounts are whole cents, as `int`. A month is a month number: an `int`
that is 1 or more (1 is the first month, 2 the next, and so on, with no
upper limit).

## Accounts

- `add_account(account_id)` adds an account with no payments. The id must
  be a non-empty string, or `ValueError` is raised. Adding an id that is
  already there raises `SpendingError`.
- `get_accounts()` returns the ids of all accounts, in the order they were
  added.
- Every other method that takes an `account_id` raises `KeyError` when the
  account was never added, including values that are not strings at all,
  such as `None` or `1`.

## Payments

- `record_payment(account_id, month, category, amount)` records one payment
  and returns its id. Ids are `int`s: the first payment recorded by a
  tracker gets 1, the next gets 2, and so on, counting over all accounts.
- The month must be a valid month number, the category a non-empty string
  and the amount an `int` greater than 0. Anything else raises
  `ValueError`.
- `get_total(account_id, month)` returns the sum of all the account's
  payments in that month, over all categories.
- `get_category_total(account_id, month, category)` returns the sum of the
  account's payments in that month and category.
- Both return 0 when nothing matches.

## Alerts

A category is **over the limit** for an account in a month when the
account's total for that category in that month is more than 50000
(500.00). A total of exactly 50000 is not over the limit.

- `get_alerts(account_id, month)` returns the categories that are over the
  limit in that month, in the order of each category's first payment in
  that month.
- `get_alert_months(account_id, category)` returns the months in which that
  category is over the limit, smallest month first. It returns `[]` for a
  category with no payments.

## Errors

The query methods check their arguments the same way as `record_payment`:
a month that is not a valid month number, or a category that is not a
non-empty string, raises `ValueError`.

When a call has several problems, `KeyError` for an unknown account comes
before any `ValueError`.

A failed call has no effect: if a method raises, no payment is recorded, no
payment id is used up and every total is unchanged. Trackers do not share
accounts or payments.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` values passed as months or amounts, what happens if a
returned list is changed, the text of error messages, saving the tracker to
a file, and use from several threads.
