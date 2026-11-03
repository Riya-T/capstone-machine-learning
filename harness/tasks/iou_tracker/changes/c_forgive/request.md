Let a lender forgive an IOU in `ious.py`, so a mistaken or waived IOU can be
taken back.

- Add `IouTracker.forgive_last(lender, borrower) -> int`: cancels the most
  recent IOU recorded from `lender` to `borrower` and returns its amount.
- A cancelled IOU is treated as if it had never been recorded: it is
  removed from the history of both users, and `get_owed(lender, borrower)`,
  `get_total_lent(lender)` and `get_total_borrowed(borrower)` all fall by
  its amount. A debt that falls to 0 is no longer listed by `get_debts`.
  Earlier IOUs between the two stay in force, so calling `forgive_last`
  again cancels the next most recent one.
- IOUs in the other direction (from `borrower` to `lender`) are never
  touched.
- Only existing IOUs can be cancelled: when no IOU from `lender` to
  `borrower` remains, raise `IouError`.

When a call has several problems, nothing changes. `KeyError` for a name
that is not a user and `ValueError` when lender and borrower have the same
name both come before `IouError`; if both apply, either may be raised.

All existing behavior must keep working.
