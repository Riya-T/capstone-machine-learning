Allow payments in `spending.py` to be refunded, in full or in part.

- Add `SpendingTracker.refund(payment_id, amount=None) -> None`.
  `payment_id` is an id returned by `record_payment`. With `amount=None`
  the whole part of the payment that has not been refunded yet is
  refunded; otherwise `amount` must be an `int` greater than 0 and only
  that much is refunded.
- Refunded money no longer counts anywhere: every total, alert and list of
  alert months is computed as if the payment had been for its amount minus
  what was refunded from it. The payment keeps its month and category.
- A payment can be refunded several times, until nothing of it is left.
- Add `SpendingTracker.get_refunded(payment_id) -> int`: how much of the
  payment has been refunded so far (0 if none).
- Errors:
  - `KeyError` for a payment id that `record_payment` never returned
    (including values that are not `int`s);
  - `ValueError` for an invalid amount;
  - `SpendingError` when the amount is more than what is left of the
    payment, or when nothing is left of it (with `amount=None` too).

  Which one is raised when several apply is unspecified.
- `get_refunded` raises `KeyError` for an unknown payment id.
- A failed refund changes nothing. Refunds do not use up payment ids: the
  next payment gets the next id as before.

All existing behavior must keep working.
