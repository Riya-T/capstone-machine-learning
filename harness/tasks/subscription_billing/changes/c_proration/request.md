Make the upgrade charge in `billing.py` adjustable. Today a customer who
moves to a higher-priced plan pays the whole price difference at once; we
want to charge only a share of it, set for the whole system or per plan.

- `BillingSystem` takes a new keyword argument `upgrade_percent=100`: the
  percentage of the price difference charged on a move to a higher-priced
  plan.
- `add_plan` takes a new keyword argument `upgrade_percent=None`. `None`
  means the plan uses the system's percentage; an `int` sets the plan's own.
  The percentage of the plan being moved **to** is the one that applies.
- A percentage (in either place) must be an `int` from 0 to 100 (not a
  `bool`); anything else raises `ValueError`. For `add_plan`, that check
  comes after the checks on the id and the price, and before the
  `BillingError` for an id that was already added. In every case no plan is
  added.
- The upgrade charge is the price difference times the percentage, divided
  by 100 and rounded down to a whole cent. For example, moving from 900 to
  1500 at 50% charges 300, and moving from 900 to 1000 at 33% charges 33.
- An upgrade charge that comes to 0 is not charged: `get_charges` gets no
  entry for it. Moves to a plan with the same or a lower price still charge
  nothing.
- Add `BillingSystem.get_upgrade_percent(plan_id) -> int`, which returns
  the percentage that applies to the plan, and raises `KeyError` for a plan
  that was never added.
- Add `BillingSystem.get_upgrade_charge(customer, plan_id) -> int`, which
  returns what `change_plan(customer, plan_id)` would charge right now,
  without changing anything. It raises the same errors as `change_plan`, in
  the same order.

All existing behavior must keep working.
