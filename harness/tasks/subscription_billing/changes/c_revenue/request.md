Add revenue reports to `billing.py`, so we can see how much each plan has
brought in.

- Add `BillingSystem.get_revenue(plan_id) -> int`: the sum of every charge
  made for the plan so far. A billing cycle's charge to a customer counts
  for the plan the customer was on in that cycle. A charge for moving to a
  higher-priced plan counts for the plan the customer moved **to**.
- Charges keep counting for their plan after the customer moves to another
  plan or cancels: revenue never goes down.
- A plan nobody has been charged for has a revenue of 0. `get_revenue`
  raises `KeyError` for a plan that was never added.
- Add `BillingSystem.get_total_revenue() -> int`: the sum of every charge
  made to every customer so far.
- Add `BillingSystem.get_plans_by_revenue() -> list[str]`: the ids of all
  plans, highest revenue first. Plans with the same revenue keep the order
  in which they were added.

All existing behavior must keep working.
