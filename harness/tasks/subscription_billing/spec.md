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

`add_plan(plan_id, price)` adds a plan. An empty id, or a price of 0 or
less, raises `ValueError`. Adding an id that was already added raises
`BillingError`. `ValueError` is checked first. Any method below that is
given a `plan_id` that was never added raises `KeyError`.

## Customers

A customer is known from their first `subscribe` on, and stays known for
good. A known customer is either **subscribed** (on a plan) or
**cancelled**. A cancelled customer keeps every charge made so far and may
subscribe again.

- `subscribe(customer, plan_id)` puts the customer on the plan. This works
  for a customer who has never subscribed and for one who has cancelled.
  Subscribing charges nothing; the first charge comes with the next billing
  cycle. It raises:
  - `ValueError` for an empty string or `None` as the customer;
  - `KeyError` for a plan that was never added;
  - `BillingError` for a customer who is subscribed right now.
- `cancel(customer)` ends the customer's subscription. Nothing is refunded.
  It raises:
  - `KeyError` for a customer who has never subscribed;
  - `BillingError` for a customer who is cancelled already.
- `get_plan(customer)` returns the id of the customer's current plan, or
  `None` if they are cancelled.
- `get_charges(customer)` returns the customer's charges (see "Billing
  cycles").
- `change_plan`, `cancel`, `get_plan` and `get_charges` raise `KeyError` for
  a customer who has never subscribed, including values that are not
  strings, such as `None` or `1`.

For example, with plans `"basic"` (price 900) and `"lite"` (price 400):

```python
billing.subscribe("alice", "basic")
billing.run_cycle()                   # returns 900
billing.cancel("alice")
billing.get_plan("alice")             # None
billing.get_charges("alice")          # [900]
billing.run_cycle()                   # returns 0: alice is not charged
billing.cancel("alice")               # raises BillingError
billing.change_plan("alice", "lite")  # raises BillingError
billing.subscribe("alice", "lite")
billing.get_plan("alice")             # "lite"
billing.run_cycle()                   # returns 400
billing.get_charges("alice")          # [900, 400]
```

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
- `BillingError` for a customer who is cancelled;
- `BillingError` for a move to the plan the customer is already on.

## Billing cycles

- `run_cycle()` charges every subscribed customer the price of the plan
  they are on at that moment, and returns the total charged by this cycle
  (0 if nobody is subscribed). Cancelled customers are not charged.
- `get_charges(customer)` returns every charge made to the customer, oldest
  first: one per billing cycle they were charged in, plus one for each move
  to a higher-priced plan. Charges stay after a customer cancels, and after
  they subscribe again.

A failed call has no effect: if a method raises, every plan, subscription
and charge is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when a call to `subscribe` or `change_plan`
has several problems (for example a cancelled customer and a plan that was
never added), prices that are not `int`s, such as `1.5`, `"900"` or
`None`, `bool` prices, ids that are not strings passed to `add_plan`,
values that are neither strings nor `None`, such as `7`, passed as the
customer to `subscribe`, the order in which a cycle charges customers, what
happens if a returned list is changed, the text of error messages, saving
the system to a file, and use from several threads.
