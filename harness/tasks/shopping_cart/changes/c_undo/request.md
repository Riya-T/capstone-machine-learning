Add `undo() -> bool` to `ShoppingCart`.

- Undo reverts the most recent successful `add_item` or `remove_item`
  operation to the exact cart contents from before that operation.
- Successful operations can be undone one at a time, in last-in-first-out
  order.
- Invalid operations and removing an unknown item do not create an undo
  entry.
- `undo()` returns `True` when it restores a prior cart state and `False`
  when there is no operation left to undo.

All existing behavior must keep working.
