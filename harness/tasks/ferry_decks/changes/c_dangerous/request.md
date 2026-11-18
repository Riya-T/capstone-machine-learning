Let `ferry.py` keep vehicles that carry dangerous goods on open-air decks
only.

- `add_deck` takes a new keyword argument: `add_deck(name,
  open_air=False)`. A deck added with `open_air=True` is an open-air deck.
- `board` takes a new keyword argument: `board(vehicle, deck,
  dangerous=False)`. A vehicle boarded with `dangerous=True` carries
  dangerous goods. It stays dangerous while it is aboard, wherever it is
  moved. A vehicle that leaves (or is unloaded) and boards again is
  dangerous only if that new `board` call says so.
- Add `Ferry.get_dangerous(deck) -> list[str]`, which returns the names of
  the dangerous vehicles on the deck, in the deck's order. It raises
  `KeyError` for a deck that was never added.
- Add `class NotAllowed(FerryError)` to `ferry.py`.
- A dangerous vehicle may only be on an open-air deck. Every call that puts
  vehicles onto a deck checks this: `board`, `move_vehicle`, and
  `move_deck` for `to_deck`. If a dangerous vehicle would end up on a deck
  that is not open-air, the call raises `NotAllowed` and changes nothing.
- `move_deck` moves all of the vehicles or none of them: if even one of the
  vehicles it would move is dangerous and `to_deck` is not open-air, no
  vehicle moves. Vehicles that are not dangerous may go on any deck.
- `leave` and `unload_deck` never raise `NotAllowed`.
- When a call would raise `NotAllowed` and another error too, which of them
  is raised is unspecified.
- `undo` keeps working as before: it puts back exactly the state from just
  before the undone call, and a vehicle that an undo brings back aboard is
  dangerous again if it was dangerous before.

All existing behavior must keep working.
