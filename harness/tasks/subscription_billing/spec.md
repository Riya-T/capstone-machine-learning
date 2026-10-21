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
    def get_plan(self, customer: str) -> str | None: ...
    def get_charges(self, customer: str) -> list[int]: ...
```

All prices and charges are whole cents, as `int`.

## Plans

`add_plan(plan_id, price)` adds a plan. The id must be a non-empty string
and the price an `int` greater than 0; otherwise `ValueError` is raised.
Adding an id that was already added raises `BillingError`. `ValueError` is
checked first. Any method below that is given a `plan_id` that was never
added raises `KeyError`.

## Customers

- `subscribe(customer, plan_id)` puts the customer on the plan. The
  customer must be a non-empty string, or `ValueError` is raised. A customer
  who is already subscribed raises `BillingError`. Subscribing charges
  nothing; the first charge comes with the next billing cycle. Errors are
  checked in this order: `ValueError`, then `KeyError` for the plan, then
  `BillingError`.
- `cancel(customer)` ends the customer's subscription. Nothing is refunded.
  A customer who has cancelled may subscribe again later, to any plan.
- `get_plan(customer)` returns the id of the customer's current plan, or
  `None` if they have cancelled.
- `change_plan`, `cancel`, `get_plan` and `get_charges` raise `KeyError` for
  a customer who has never subscribed, including values that are not
  strings, such as `None` or `1`. This is checked before anything else.
- `change_plan` and `cancel` raise `BillingError` for a customer who has
  cancelled and not subscribed again.

## Changing plans

`change_plan(customer, plan_id)` moves a subscribed customer to another
plan straight away.

- Moving to a plan with a higher price charges the customer the difference
  between the two prices at once. For example, moving from a plan costing
  900 to one costing 1500 charges 600.
- Moving to a plan with the same or a lower price charges nothing.
- Moving to the plan the customer is already on raises `BillingError`.

Errors are checked in this order: `KeyError` for the customer, `KeyError`
for the plan, then `BillingError`.

## Billing cycles

- `run_cycle()` charges every subscribed customer the price of the plan
  they are on at that moment, and returns the total charged by this cycle
  (0 if nobody is subscribed). Customers who have cancelled are not charged.
- `get_charges(customer)` returns every charge made to the customer, oldest
  first: one per billing cycle they were charged in, plus one for each move
  to a higher-priced plan. Charges stay after a customer cancels.

A failed call has no effect: if a method raises, every plan, subscription
and charge is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_plan`, `bool` prices,
the order in which a cycle charges customers, what happens if a returned
list is changed, the text of error messages, saving the system to a file,
and use from several threads.
