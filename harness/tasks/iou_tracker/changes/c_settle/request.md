Let a user pay back several lenders at once in `ious.py`, all or nothing.

- Add `IouTracker.settle(borrower, payments)`, where `payments` is a list
  of `(lender, amount)` tuples. Each payment reduces what `borrower` owes
  that lender, `get_owed(lender, borrower)`, by `amount`. A debt paid down
  to 0 is no longer listed by `get_debts`.
- The totals follow the debts, not the history: each payment also lowers
  `get_total_lent(lender)` and `get_total_borrowed(borrower)` by its
  amount. `get_total_lent(name)` stays the sum of `get_owed(name, other)`
  over the other users, and `get_total_borrowed(name)` the sum of
  `get_owed(other, name)`. So once something has been paid back, the
  totals are less than what the IOUs in the history add up to.
- A payment may not be more than what `borrower` currently owes that
  lender. If any payment in the list is too large, raise `IouError` and
  apply none of the payments.
- `borrower` and each lender must be users (`KeyError`), each amount must
  be greater than 0 (`ValueError`), a user cannot pay themselves
  (`ValueError`), and a lender may appear only once in the list
  (`ValueError`). An empty list is allowed and does nothing.
- Payments are not IOUs: `settle` adds nothing to any history, and the IOUs
  that were paid off stay in the history.

When a call has several problems, nothing changes, and every `KeyError` or
`ValueError` above comes before the `IouError` for a payment that is too
large, wherever the payments are in the list. If there are several
`KeyError` or `ValueError` problems, any one of them may be raised.

All existing behavior must keep working.
