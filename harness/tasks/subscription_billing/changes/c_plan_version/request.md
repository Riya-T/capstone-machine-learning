Two support agents sometimes change the same customer's subscription in
`billing.py` at once, and one silently undoes the other. Give each
subscription a version number so a change can say which state it was based
on.

- Add `class VersionConflict(BillingError)` to `billing.py`.
- Add `BillingSystem.get_version(customer) -> int`. A subscription has
  version 1 when it starts, and its version goes up by 1 with every
  successful `change_plan`, `pause` and `resume`. Billing cycles, failed
  calls and calls that only read leave it unchanged. A customer who cancels
  and subscribes again starts a new subscription at version 1.
- `get_version` raises `KeyError` for a customer who has never subscribed
  and `BillingError` for a customer who has cancelled and not subscribed
  again.
- `change_plan`, `pause`, `resume` and `cancel` take a new keyword argument
  `expected_version=None`. When it is `None` they work as before. Otherwise,
  if it is not equal to the subscription's current version,
  `VersionConflict` is raised and nothing changes.
- `VersionConflict` is checked after every `KeyError` check and after the
  check for a cancelled customer, and before every other error.
- Each customer has their own version: changing one subscription does not
  change the version of any other.

All existing behavior must keep working.
