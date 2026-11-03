Let a lender forgive an IOU in `ious.py`, so a mistaken or waived IOU can be
taken back.

- Add `IouTracker.forgive_last(lender, borrower) -> int`: cancels the most
  recent IOU from `lender` to `borrower` that is still in `get_ious()`, and
  returns its amount.
- A cancelled IOU is treated as if it had never been recorded: it is
  removed from `get_ious()`, where the other IOUs keep their order, and
  `get_owed(lender, borrower)` falls by its amount. Earlier IOUs between
  the two stay, so calling `forgive_last` again cancels the next most
  recent one.
- IOUs in the other direction (from `borrower` to `lender`) and IOUs
  between other users are never touched.
- When no IOU from `lender` to `borrower` is left in `get_ious()`, raise
  `IouError`. A name that is not a user raises `KeyError`, as everywhere
  else.

A call that raises changes nothing. When a call has several problems (such
as a name that is not a user, who has no IOUs either), which of the errors
is raised is unspecified.

For example:

```python
tracker.record_iou("alice", "bob", 400)
tracker.record_iou("bob", "alice", 50)
tracker.record_iou("alice", "bob", 150)
tracker.forgive_last("alice", "bob")  # 150
tracker.get_ious()  # [("alice", "bob", 400), ("bob", "alice", 50)]
tracker.get_owed("alice", "bob")      # 400
tracker.forgive_last("alice", "bob")  # 400
tracker.forgive_last("alice", "bob")  # raises IouError: none left
tracker.get_owed("bob", "alice")      # 50: never touched
```

All existing behavior must keep working.
