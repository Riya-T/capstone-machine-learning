# Order workflow

Write a module `workflow.py` that tracks orders as they move through a fixed
set of states, and only lets them move along the allowed paths.

## Interface

```python
class WorkflowError(Exception): ...


class InvalidTransition(WorkflowError): ...


class OrderWorkflow:
    def __init__(self): ...
    def create_order(self, order_id: str, total: int) -> None: ...
    def move(self, order_id: str, state: str) -> None: ...
    def get_state(self, order_id: str) -> str: ...
    def get_total(self, order_id: str) -> int: ...
    def get_orders(self) -> list[str]: ...
    def get_orders_in(self, state: str) -> list[str]: ...
```

Totals are whole cents, as `int`.

## States

The five states are the strings `"new"`, `"paid"`, `"shipped"`,
`"delivered"` and `"cancelled"`. An order may move only along these paths:

- `"new"` to `"paid"`;
- `"paid"` to `"shipped"`;
- `"shipped"` to `"delivered"`;
- `"new"` to `"cancelled"`;
- `"paid"` to `"cancelled"`.

`"delivered"` and `"cancelled"` are final: an order in one of them cannot
move anywhere. Moving an order to the state it is already in is not
allowed either.

## Orders

- `create_order(order_id, total)` creates an order in state `"new"`. An
  empty id raises `ValueError`; a `total` that is not an `int` greater than
  0 raises `ValueError`; an id that already exists raises `WorkflowError`.
  The `ValueError` checks come before the `WorkflowError` check.
- `get_orders()` returns the ids of all orders, in the order they were
  created.
- `get_state(order_id)` returns the order's current state and
  `get_total(order_id)` its total.
- Every method that takes an order id raises `KeyError` when the id does
  not exist, including values that are not strings at all, such as `None`
  or `1`.

## Moving

- `move(order_id, state)` moves the order to `state`.
- A `state` that is not one of the five state names raises `ValueError`.
- A move that is not on one of the allowed paths raises
  `InvalidTransition`.
- `get_orders_in(state)` returns the ids of the orders currently in
  `state`, in the order they were created. A `state` that is not one of
  the five state names raises `ValueError`.

When a call has several problems, the first of these is raised:

1. `KeyError` for an order that does not exist;
2. `ValueError` for a state name that is not one of the five;
3. `InvalidTransition`.

A failed call has no effect: if a method raises, every order's state and
total is unchanged and no order is created.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `create_order`, `bool` totals,
what happens if a returned list is changed, the text of error messages,
saving the orders to a file, and use from several threads.
