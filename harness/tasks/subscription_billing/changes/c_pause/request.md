Let customers in `billing.py` pause their subscription, for example while
they are away, and resume it later on the same plan.

- Add `class SubscriptionPaused(BillingError)` to `billing.py`.
- Add `BillingSystem.pause(customer)`, `BillingSystem.resume(customer)` and
  `BillingSystem.is_paused(customer) -> bool`.
- All three raise `KeyError` for a customer who has never subscribed, before
  any other error. `pause` and `resume` raise `BillingError` for a customer
  who has cancelled; `is_paused` returns `False` for them.
- Pausing a paused subscription raises `SubscriptionPaused`. Resuming a
  subscription that is not paused raises `BillingError` (not
  `SubscriptionPaused`).
- New subscriptions are not paused, and that includes a customer who
  subscribes again after cancelling. A paused subscription keeps its plan:
  `get_plan` still returns it.
- `run_cycle` does not charge paused customers, and their charges are not
  part of the total it returns. After `resume`, the next cycle charges them
  again as usual. Pausing and resuming charge nothing.
- While a customer is paused, `change_plan` and `get_upgrade_charge` raise
  `SubscriptionPaused` and change nothing. This is checked after both
  `KeyError` checks and the check for a cancelled customer, and before the
  `BillingError` for moving to the current plan.
- A paused customer may cancel.

All existing behavior must keep working.
