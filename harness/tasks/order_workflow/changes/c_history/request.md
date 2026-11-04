Add a state history to `workflow.py`, so support staff can see where an
order has been.

- Add `OrderWorkflow.get_history(order_id) -> list[str]`: every state the
  order has been in, oldest first. It starts with `"new"` and its last
  entry is always the order's current state.
- Add `OrderWorkflow.get_move_count(order_id) -> int`: how many successful
  moves have been made on the order. A new order has 0.
- Add `OrderWorkflow.get_orders_that_passed(state) -> list[str]`: the ids
  of every order whose history contains `state`, whether or not it is still
  there, in the order the orders were created. It raises `ValueError` for
  an unknown state name, just like `get_orders_in`.
- `get_history` and `get_move_count` raise `KeyError` for an order that
  does not exist.
- A `move` call that raised adds nothing to the history and is not counted,
  whatever the reason it raised.
- If the workflow can already undo moves with `rollback`, a move that was
  rolled back counts as never made: it is taken out of the history, it is
  no longer counted in `get_move_count`, and `get_orders_that_passed` no
  longer lists the order for a state it only reached through that move. For
  example, an order that went `"new"`, `"paid"`, `"cancelled"` and was then
  rolled back once has the history `["new", "paid"]` and a move count of 1,
  and is not listed by `get_orders_that_passed("cancelled")`. A `rollback`
  call that raised changes none of these. This change does not add
  `rollback` to a workflow that does not have it.

All existing behavior must keep working.
