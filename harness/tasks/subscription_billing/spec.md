# Subscription billing

Write a module `billing.py` that bills customers for subscriptions: there
are plans with a price per billing cycle, customers subscribe to one plan at
a time, and each billing cycle charges every subscriber.

## Interface

```python
class BillingError(Exception): ...


class BillingSystem:
    def __init__(self): ...
    def add_plan(self, plan_id: str, price: int) -> None: ...
    def subscribe(self, customer: str, plan_id: str) -> None: ...
    def change_plan(self, customer: str, plan_id: str) -> None: ...
    def cancel(self, customer: str) -> None: ...
    def run_cycle(self) -> int: ...
    def get_plan(self, customer: str) -> str: ...
    def get_charges(self, customer: str) -> list[int]: ...
```

All prices and charges are whole cents, as `int`.

## Plans

`add_plan(plan_id, price)` adds a plan. It raises:

- `ValueError` for an empty id, or a price of 0 or less;
- `BillingError` for an id that was already added.

Any method below that is given a `plan_id` that was never added raises
`KeyError`.

## Customers

- `subscribe(customer, plan_id)` puts the customer on the plan. Subscribing
  charges nothing; the first charge comes with the next billing cycle. It
  raises:
  - `ValueError` for an empty string or `None` as the customer;
  - `KeyError` for a plan that was never added;
  - `BillingError` for a customer who is already subscribed.
- `cancel(customer)` ends the customer's subscription: billing cycles do not
  charge them any more. Nothing is refunded.
- `get_plan(customer)` returns the id of the customer's current plan.
- `change_plan`, `cancel`, `get_plan` and `get_charges` raise `KeyError` for
  a customer who has never subscribed, including values that are not
  strings, such as `None` or `1`.

## Changing plans

`change_plan(customer, plan_id)` moves a subscribed customer to another
plan straight away.

- Moving to a plan with a higher price charges the customer the difference
  between the two prices at once. For example, moving from a plan costing
  900 to one costing 1500 charges 600.
- Moving to a plan with the same or a lower price charges nothing.

It raises:

- `KeyError` for a customer who has never subscribed;
- `KeyError` for a plan that was never added;
- `BillingError` for a move to the plan the customer is already on.

## Billing cycles

- `run_cycle()` charges every subscribed customer the price of the plan
  they are on at that moment, and returns the total charged by this cycle
  (0 if nobody is subscribed).
- `get_charges(customer)` returns every charge made to the customer, oldest
  first: one per billing cycle they were charged in, plus one for each move
  to a higher-priced plan.

A failed call has no effect: if a method raises, every plan, subscription
and charge is unchanged.

## Example

```python
billing = BillingSystem()
billing.add_plan("basic", 900)
billing.add_plan("pro", 1500)
billing.subscribe("alice", "basic")
billing.subscribe("bob", "basic")
billing.get_charges("alice")         # []: subscribing charges nothing
billing.run_cycle()                  # 1800
billing.change_plan("alice", "pro")  # charges alice 600 at once
billing.cancel("bob")
billing.run_cycle()                  # 1500: bob is not charged any more
billing.get_charges("alice")         # [900, 600, 1500]
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes everything about a customer after they cancel other than that
billing cycles do not charge them (for example what `get_plan`,
`get_charges`, `change_plan` and `cancel` do for them, and whether they can
subscribe again), which error is raised when one call has several problems
(for example a price of 0 and an id that was already added), prices that
are not `int`s, such as `1.5`, `"900"` or `None`, `bool` prices, ids that
are not strings passed to `add_plan`, values that are neither strings nor
`None`, such as `7`, passed as the customer to `subscribe`, the order in
which a cycle charges customers, what happens if a returned list is
changed, the text of error messages, saving the system to a file, and use
from several threads.
