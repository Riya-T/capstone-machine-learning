Let a user pay back several lenders at once in `ious.py`, all or nothing.

- Add `IouTracker.settle(borrower, payments)`, where `payments` is a list
  of `(lender, amount)` tuples. Each payment reduces what `borrower` owes
  that lender by `amount`. A debt paid down to 0 disappears from
  `get_owed_to` and `get_owed_by`.
- A payment may not be more than what `borrower` currently owes that
  lender. If any payment in the list is too large, raise `IouError` and
  apply none of the payments.
- Each lender must be a user, each amount must be an `int` greater than 0,
  a user cannot pay themselves, and a lender may appear only once in the
  list. An empty list is allowed and does nothing.
- Payments are not IOUs: `settle` adds nothing to any history, and the IOUs
  that were paid off stay in the history.

When a call has several problems, the first of these is raised, and in
every case nothing changes:

1. `KeyError` for a borrower that is not a user;
2. for each payment, in list order: `KeyError` for a lender that is not a
   user, then `ValueError` for an invalid amount, then `ValueError` for a
   lender with the same name as the borrower;
3. `ValueError` for a lender that appears twice;
4. `IouError` for a payment larger than the debt.

All existing behavior must keep working.
