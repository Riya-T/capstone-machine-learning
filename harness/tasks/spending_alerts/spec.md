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

- `add_account(account_id)` adds an account with no payments. An empty
  string or `None` as the id raises `ValueError`. Adding an id that is
  already there raises `SpendingError`.
- `get_accounts()` returns the ids of all accounts, in the order they were
  added.
- Every other method that takes an `account_id` raises `KeyError` when the
  account was never added.

## Payments

- `record_payment(account_id, month, category, amount)` records one payment
  and returns its id. Ids are `int`s: the first payment recorded by a
  tracker gets 1, the next gets 2, and so on, counting over all accounts.
- A month below 1, or an amount of 0 or less, raises `ValueError`. An
  empty string or `None` as the category raises `ValueError` too.
- `get_total(account_id, month)` returns the sum of all the account's
  payments in that month, over all categories.
- `get_category_total(account_id, month, category)` returns the sum of the
  account's payments in that month and category.
- Both return 0 when nothing matches: a month or a category with no
  payments is not an error.

## Alerts

A category is **over the limit** for an account in a month when the
account's total for that category in that month is more than 50000
(500.00). A total of exactly 50000 is not over the limit.

- `get_alerts(account_id, month)` returns the categories that are over the
  limit in that month, in the order of each category's first payment in
  that month.
- `get_alert_months(account_id, category)` returns the months in which that
  category is over the limit, each month once, in any order. It returns
  `[]` for a category with no payments.

## Checking the queries

`get_total`, `get_category_total`, `get_alerts` and `get_alert_months`
check their month and category like `record_payment` does, whether or not
the account has payments: a month below 1, or an empty string or `None`
as the category, raises `ValueError`. For example, if `"alice"` has no
payments in month 7:

- `get_total("alice", 7)` returns 0, and `get_total("alice", 0)` raises
  `ValueError`;
- `get_category_total("alice", 7, "food")` returns 0, and
  `get_category_total("alice", 7, "")` raises `ValueError`;
- `get_alerts("alice", 7)` returns `[]`, and `get_alerts("alice", 0)`
  raises `ValueError`;
- `get_alert_months("alice", "")` raises `ValueError`.

## Errors

A failed call has no effect: if a method raises, no payment is recorded, no
payment id is used up and every total is unchanged. Trackers do not share
accounts or payments.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when a call has several problems (for
example an account that was never added and an invalid month), values that
are neither strings nor `None`, such as `7`, passed as an account id or a
category, `None` as the account id of any method other than `add_account`,
the order of the months from `get_alert_months`, months and amounts that are not `int`s, such as `1.5`, `"3"` or `None`,
`bool` values passed as months or amounts, what happens if a returned list
is changed, the text of error messages, saving the tracker to a file, and
use from several threads.
