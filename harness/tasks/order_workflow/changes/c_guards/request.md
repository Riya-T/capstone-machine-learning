Add transition guards to `workflow.py`: an order may only be paid once the
money is in, and only be shipped once it has an address.

- Add `class GuardFailed(WorkflowError)` to `workflow.py`.
- Add `OrderWorkflow.set_address(order_id, address)`: records the delivery
  address, replacing any earlier one. `address` must be a non-empty `str`,
  or `ValueError` is raised. It is only allowed while the order is `"new"`
  or `"paid"`; in any other state it raises `WorkflowError`. Errors are
  checked in the order `KeyError`, `ValueError`, `WorkflowError`, and a call
  that raises changes nothing.
- Add `OrderWorkflow.get_address(order_id) -> str`: the recorded address,
  or `""` when none has been set.
- Add `OrderWorkflow.record_payment(order_id, amount)`: records a payment
  of `amount` cents towards the order. `amount` must be an `int` greater
  than 0 (not a `bool`), or `ValueError` is raised. The payments on an order
  may add up to exactly its total but never more; a payment that would go
  over the total raises `ValueError` and is not recorded. `KeyError` is
  checked before `ValueError`. Payments may be recorded in any state.
- Add `OrderWorkflow.get_paid(order_id) -> int`: the sum of the payments
  recorded on the order, 0 for a new order.
- `OrderWorkflow` takes a new keyword argument `guarded=False`. With
  `guarded=True`, moving an order to `"paid"` requires its payments to add
  up to its total, and moving it to `"shipped"` requires an address;
  otherwise `move` raises `GuardFailed`. No other move is guarded:
  cancelling needs neither payment nor address. With `guarded=False` no move
  is guarded, but addresses and payments are still recorded and checked as
  above.
- `GuardFailed` is checked after `KeyError`, `ValueError` and
  `InvalidTransition`. A move refused by a guard changes nothing.
- All four new methods raise `KeyError` for an order that does not exist.

All existing behavior must keep working.
