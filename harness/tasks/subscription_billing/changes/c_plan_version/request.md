Two support agents sometimes change the same customer's subscription in
`billing.py` at once, and one silently undoes the other. Give each
subscription a version number so a change can say which state it was based
on.

- Add `class VersionConflict(BillingError)` to `billing.py`.
- Add `BillingSystem.get_version(customer) -> int`. A subscription has
  version 1 when it starts, and its version goes up by 1 with every
  successful `change_plan`, `pause` and `resume`. Billing cycles, failed
  calls and calls that only read leave it unchanged.
- `get_version` raises `KeyError` for a customer who has never subscribed.
  What it does for a customer who has cancelled is unspecified.
- `change_plan`, `pause`, `resume` and `cancel` take a new keyword argument
  `expected_version=None`. When it is `None` they work as before. Otherwise,
  if it is not equal to the subscription's current version,
  `VersionConflict` is raised and nothing changes.
- When a call with a wrong `expected_version` also has another problem
  (for example a plan that was never added, a paused customer or a move
  to the current plan), which error is raised
  is unspecified.
- Each customer has their own version: changing one subscription does not
  change the version of any other.

All existing behavior must keep working.
