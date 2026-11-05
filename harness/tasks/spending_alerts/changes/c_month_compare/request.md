Compare each month's spending in `spending.py` with the month before, to
spot categories that suddenly cost a lot more.

- Add `SpendingTracker.get_month_change(account_id, month, category) -> int`:
  the account's total for that category in `month` minus its total in
  `month - 1`. It can be negative. For month 1 the previous total is 0.
- Add `SpendingTracker.get_unusual_categories(account_id, month)
  -> list[str]`: the categories whose total in `month` is at least one and
  a half times their total in `month - 1`, counting only categories whose
  previous total is more than 0. Use whole numbers: a category is unusual
  when `current * 2 >= previous * 3`. The list is in the order of each
  category's first payment in `month`. In month 1 nothing is unusual.
- Being unusual does not depend on the alert limit: small amounts can be
  unusual, and the alerts stay as they are.
- Months and categories are checked like in the other queries: a month
  below 1, or (for `get_month_change`) an empty string or `None` as the
  category, raises `ValueError`. A month or a category with no payments is
  not an error: its total is 0, in `month` and in `month - 1` alike. For
  example, if `"alice"` paid only in month 4, 900 for `"food"`,
  `get_month_change("alice", 5, "food")` is -900,
  `get_month_change("alice", 6, "food")` is 0, and
  `get_unusual_categories("alice", 6)` is `[]`.
- Both methods raise `KeyError` for an unknown account. Which error is
  raised when the account and the month or category are both wrong is
  unspecified, and so are months that are not `int`s (such as `1.5`, `"3"`
  or `None`), as in the rest of `spending.py`. Both methods change nothing.

All existing behavior must keep working.
