Add overdraft limits to `ledger.py`, so an account's balance can go below
zero, down to a limit set for that account.

- `open_account` takes a new keyword argument `overdraft_limit=0`. It must
  be an `int` that is 0 or more; anything else raises
  `ValueError` and no account is opened.
- A withdrawal or outgoing transfer may take the balance down to minus the
  account's overdraft limit, but no lower. One that would go lower raises
  `InsufficientFunds` and changes nothing. `get_balance` can now be negative.
- Add `Ledger.get_overdraft_limit(account_id) -> int`, which returns the
  account's current limit.
- Add `Ledger.set_overdraft_limit(account_id, limit)`, which replaces the
  limit. It raises `KeyError` for an account that is not open,
  `ValueError` for an invalid limit, and `LedgerError` if the limit is
  valid but the balance is already below minus it. In each case nothing
  changes.
- `get_overdraft_limit` raises `KeyError` for an account that is not open.

Which error is raised when one call has several of these problems (for
example an account that is not open and an invalid limit) is unspecified.
All existing behavior must keep working.
