Add an undo to `ferry.py`, so a mistake in loading the ferry can be taken
back.

- Add `Ferry.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among the methods that change the ferry:
  `add_deck`, `board`, `leave`, `move_vehicle`, `move_deck` and
  `unload_deck`, and any other method of the class that changes which
  vehicles are aboard or where they are. Each further `undo` goes one call
  further back.
- Undoing a call puts every deck back exactly as it was just before that
  call: the same vehicles, in the same order. A call that changed several
  things is undone as a whole by one `undo`:
  - an undone `leave` puts the vehicle back aboard, at its old place among
    the vehicles of its deck;
  - an undone `move_vehicle` puts the vehicle back at its old place on its
    old deck;
  - an undone `move_deck` puts every moved vehicle back on `from_deck` in
    its old order, and `to_deck` holds exactly what it held before;
  - an undone `unload_deck` brings every unloaded vehicle back aboard, on
    that deck in its old order, so their names are aboard again;
  - an undone `board` takes the vehicle off the ferry, so it may board
    again;
  - an undone `add_deck` removes the deck, and its name may then be added
    again.
- A `move_deck` that moved no vehicles, or an `unload_deck` of an empty
  deck, is still a call: `undo` reverses it like any other.
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods, and to `undo` itself, are not recorded either and are
  never undone. There is no redo.
- With nothing left to undo, `undo` raises `FerryError` and changes nothing.

All existing behavior must keep working.
