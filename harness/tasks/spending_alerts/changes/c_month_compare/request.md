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
- Both methods raise `KeyError` for an unknown account, then `ValueError`
  for an invalid month or (for `get_month_change`) category. They change
  nothing.

All existing behavior must keep working.
