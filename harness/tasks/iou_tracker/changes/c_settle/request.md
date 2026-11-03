Let a user pay back several lenders at once in `ious.py`, all or nothing.

- Add `IouTracker.settle(borrower, payments)`, where `payments` is a list
  of `(lender, amount)` tuples. Each payment lowers what `borrower` owes
  that lender, `get_owed(lender, borrower)`, by `amount`.
- Payments are not IOUs: `settle` adds nothing to `get_ious()`, and the
  IOUs that were paid back stay in it. So `get_owed(lender, borrower)` is
  now the sum of the IOUs from `lender` to `borrower` in `get_ious()`, minus
  everything `borrower` has paid `lender`. A new IOU after a payment adds to
  what is still owed.
- A payment never changes what is owed in the other direction: when bob
  pays alice, `get_owed("bob", "alice")` stays the same.
- A payment may not be more than what `borrower` owes that lender when
  `settle` is called. If any payment in the list is too large, raise
  `IouError` and apply none of the payments.
- `settle` also raises:
  - `KeyError` if `borrower` or a lender is not a user;
  - `ValueError` if an amount is not greater than 0;
  - `ValueError` if the same lender appears more than once in the list.
- An empty list is allowed and does nothing.

A call that raises changes nothing. When a call has several problems (such
as a lender who is not a user, and so is owed nothing), which of the errors
is raised is unspecified.

For example:

```python
tracker.record_iou("alice", "bob", 600)
tracker.record_iou("carol", "bob", 250)
tracker.settle("bob", [("alice", 150), ("carol", 250)])
tracker.get_owed("alice", "bob")  # 450
tracker.get_owed("carol", "bob")  # 0
tracker.get_ious()  # [("alice", "bob", 600), ("carol", "bob", 250)]: unchanged
tracker.settle("bob", [("alice", 100), ("carol", 1)])  # raises IouError: bob owes carol 0
tracker.get_owed("alice", "bob")  # still 450: the payment to alice was not applied
tracker.record_iou("carol", "bob", 30)
tracker.get_owed("carol", "bob")  # 30
```

All existing behavior must keep working.
