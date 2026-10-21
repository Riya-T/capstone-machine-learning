Let a move be undone in `workflow.py`, for example when an order was
cancelled by mistake.

- Add `OrderWorkflow.rollback(order_id)`: puts the order back in the state
  it was in just before its most recent move, undoing that move. Calling it
  again undoes the move before that, and so on, back to `"new"`.
- `rollback` raises `KeyError` for an order that does not exist;
  `InvalidTransition` when the order is `"delivered"`, because a delivery
  cannot be undone; and `WorkflowError` when the order has no move left to
  undo. Errors are checked in that order, and a call that raises changes
  nothing.
- After a rollback the order behaves as if the undone move had never been
  made: `get_state` and `get_orders_in` show the restored state, and the
  order may move again along any allowed path from there. An order that
  went `"new"`, `"paid"`, `"cancelled"` is in `"paid"` after one rollback
  and in `"new"` after a second.
- A rollback does not change the order's total.

All existing behavior must keep working.
