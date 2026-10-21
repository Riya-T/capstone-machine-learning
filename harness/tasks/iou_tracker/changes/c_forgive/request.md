Let a lender forgive an IOU in `ious.py`, so a mistaken or waived IOU can be
taken back.

- Add `IouTracker.forgive_last(lender, borrower) -> int`: cancels the most
  recent IOU recorded from `lender` to `borrower` and returns its amount.
- A cancelled IOU is treated as if it had never been recorded: it is
  removed from the history of both users, and what `borrower` owes `lender`
  falls by its amount. Earlier IOUs between the two stay in force, so
  calling `forgive_last` again cancels the next most recent one.
- IOUs in the other direction (from `borrower` to `lender`) are never
  touched.
- Only existing IOUs can be cancelled: when no IOU from `lender` to
  `borrower` remains, raise `IouError`. If cancelling the IOU would take the
  amount `borrower` owes `lender` below 0, also raise `IouError`.

When a call has several problems, the first of these is raised, and in
every case nothing changes:

1. `KeyError` for a name that is not a user (the lender is checked before
   the borrower);
2. `ValueError` when lender and borrower have the same name;
3. `IouError` as described above.

All existing behavior must keep working.
