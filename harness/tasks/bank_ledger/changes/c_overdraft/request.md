Add overdraft limits to `ledger.py`, so an account's balance can go below
zero, down to a limit set for that account.

- `open_account` takes a new keyword argument `overdraft_limit=0`. It must
  be an `int` that is 0 or more (not a `bool`); anything else raises
  `ValueError` and no account is opened.
- A withdrawal or outgoing transfer may take the balance down to minus the
  account's overdraft limit, but no lower. One that would go lower raises
  `InsufficientFunds` and changes nothing. `get_balance` can now be negative.
- Add `Ledger.get_overdraft_limit(account_id) -> int`, which returns the
  account's current limit.
- Add `Ledger.set_overdraft_limit(account_id, limit)`, which replaces the
  limit. It raises `KeyError` for an account that is not open, then
  `ValueError` for an invalid limit, then `LedgerError` if the balance is
  already below minus the new limit. In each case nothing changes.
- `get_overdraft_limit` raises `KeyError` for an account that is not open.

If both the account id and the limit passed to `open_account` are invalid,
either `ValueError` may come first. All existing behavior must keep working.
