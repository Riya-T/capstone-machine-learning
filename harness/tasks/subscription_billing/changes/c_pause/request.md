Let customers in `billing.py` pause their subscription, for example while
they are away, and resume it later on the same plan.

- Add `class SubscriptionPaused(BillingError)` to `billing.py`.
- Add `BillingSystem.pause(customer)`, `BillingSystem.resume(customer)` and
  `BillingSystem.is_paused(customer) -> bool`.
- All three raise `KeyError` for a customer who has never subscribed.
  What they do for a customer who has cancelled is unspecified.
- Pausing a paused subscription raises `SubscriptionPaused`. Resuming a
  subscription that is not paused raises `BillingError` (not
  `SubscriptionPaused`).
- New subscriptions are not paused. A paused subscription keeps its plan:
  `get_plan` still returns it.
- `run_cycle` does not charge paused customers, and their charges are not
  part of the total it returns. After `resume`, the next cycle charges them
  again as usual. Pausing and resuming charge nothing.
- While a customer is paused, `change_plan` and `get_upgrade_charge` raise
  `SubscriptionPaused` and change nothing. When such a call also has
  another problem (a plan that was never added, or a move to the plan the
  customer is already on), which error is raised is unspecified.
- A paused customer may cancel, and is then not charged by later cycles,
  as with any cancel.

All existing behavior must keep working.
