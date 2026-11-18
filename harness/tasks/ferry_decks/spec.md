# Ferry decks

Write a module `ferry.py` that keeps track of the vehicles on a ferry: which
vehicles are on each deck, in the order they came onto it, as vehicles
board, leave and are moved from one deck to another.

## Interface

```python
class FerryError(Exception): ...


class Ferry:
    def __init__(self): ...
    def add_deck(self, name: str) -> None: ...
    def board(self, vehicle: str, deck: str) -> None: ...
    def leave(self, vehicle: str) -> None: ...
    def move_vehicle(self, vehicle: str, deck: str) -> None: ...
    def move_deck(self, from_deck: str, to_deck: str) -> int: ...
    def unload_deck(self, deck: str) -> list[str]: ...
    def get_vehicles(self, deck: str) -> list[str]: ...
    def get_deck_of(self, vehicle: str) -> str: ...
```

Deck names and vehicle names are non-empty strings.

## Decks

- `add_deck(name)` adds an empty deck. A name that is already in use raises
  `FerryError`.
- Every method that takes a deck name raises `KeyError` when given a name
  that was never added.

## Vehicles

- A vehicle is aboard from the time it boards until it leaves or its deck is
  unloaded. A vehicle name is aboard at most once: boarding a vehicle that is
  already aboard, on any deck, raises `FerryError`. A vehicle that is no
  longer aboard may board again later.
- Every method that takes a vehicle name, except `board`, raises `KeyError`
  for a vehicle that is not aboard.
- `board(vehicle, deck)` puts the vehicle on the deck, after the vehicles
  already there.
- `leave(vehicle)` takes the vehicle off the ferry. The other vehicles on
  its deck keep their order.
- `move_vehicle(vehicle, deck)` moves the vehicle from its deck to the end of
  `deck`. It raises `ValueError` if the vehicle is already on `deck`.
- `move_deck(from_deck, to_deck)` moves every vehicle on `from_deck`, keeping
  their order, to the end of `to_deck`, and returns how many vehicles it
  moved. Afterwards `from_deck` is empty but still in use. If `from_deck` is
  empty, nothing changes and it returns 0. It raises `ValueError` when both
  names are the same deck.
- `unload_deck(deck)` takes every vehicle on the deck off the ferry and
  returns their names in the deck's order (an empty list if the deck was
  empty). The deck stays in use, empty.
- `get_vehicles(deck)` returns the names of the vehicles on the deck, in the
  order they came onto it, by boarding or by being moved there.
- `get_deck_of(vehicle)` returns the name of the deck the vehicle is on.

## Errors

A failed call has no effect: if a method raises, every deck holds the same
vehicles in the same order as before. When a call has more than one
problem, which of the errors is raised is unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes deck or vehicle names that are not non-empty strings (such as `""`,
`None` or `1`), wherever they are passed. It also includes which error is
raised when a call has several problems, what happens if a returned list is
changed, the text of error messages, saving the ferry to a file, and use
from several threads.
