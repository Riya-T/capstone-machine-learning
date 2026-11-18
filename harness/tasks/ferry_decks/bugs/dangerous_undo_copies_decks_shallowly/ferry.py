"""Ferry decks with undo, and dangerous goods kept on open-air decks.

Planted bug (after c_undo and c_dangerous): dangerous goods were added
correctly, but _save, rewritten to also save the open-air decks and the
dangerous vehicles, copies the decks dict without copying each deck's
list, so calls that change a list in place (board, leave, move_vehicle,
move_deck) change the saved copy too and undo no longer restores them.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from ferry import Ferry
    ferry = Ferry()
    ferry.add_deck("upper", open_air=True)
    ferry.board("tanker", "upper", dangerous=True)
    ferry.undo()  # the tanker is off the ferry again
"""


class FerryError(Exception):
    pass


class NotAllowed(FerryError):
    pass


class Ferry:
    def __init__(self):
        self._decks = {}  # deck name -> vehicle names, in the order they came on
        self._where = {}  # vehicle name -> deck name, for every vehicle aboard
        self._open_air = {}  # deck name -> whether it is open-air
        self._dangerous = set()  # names of the dangerous vehicles aboard
        self._undo_stack = []  # copies of the state as it was before each call

    def add_deck(self, name, open_air=False):
        if not isinstance(name, str) or not name:
            raise ValueError("deck name must be a non-empty str")
        if name in self._decks:
            raise FerryError(f"deck name {name!r} is already used")
        self._save()
        self._decks[name] = []
        self._open_air[name] = bool(open_air)

    def board(self, vehicle, deck, dangerous=False):
        self._require_deck(deck)
        if not isinstance(vehicle, str) or not vehicle:
            raise ValueError("vehicle name must be a non-empty str")
        if vehicle in self._where:
            raise FerryError(f"vehicle {vehicle!r} is already aboard")
        if dangerous and not self._open_air[deck]:
            raise NotAllowed(f"dangerous vehicle {vehicle!r} may not go on deck {deck!r}")
        self._save()
        self._decks[deck].append(vehicle)
        self._where[vehicle] = deck
        if dangerous:
            self._dangerous.add(vehicle)

    def leave(self, vehicle):
        self._require_vehicle(vehicle)
        self._save()
        deck = self._where.pop(vehicle)
        self._decks[deck].remove(vehicle)
        self._dangerous.discard(vehicle)

    def move_vehicle(self, vehicle, deck):
        self._require_vehicle(vehicle)
        self._require_deck(deck)
        old = self._where[vehicle]
        if old == deck:
            raise ValueError(f"vehicle {vehicle!r} is already on deck {deck!r}")
        self._require_allowed([vehicle], deck)
        self._save()
        self._decks[old].remove(vehicle)
        self._decks[deck].append(vehicle)
        self._where[vehicle] = deck

    def move_deck(self, from_deck, to_deck):
        self._require_deck(from_deck)
        self._require_deck(to_deck)
        if from_deck == to_deck:
            raise ValueError("cannot move a deck's vehicles onto the same deck")
        self._require_allowed(self._decks[from_deck], to_deck)
        self._save()
        moving = self._decks[from_deck]
        self._decks[from_deck] = []
        self._decks[to_deck].extend(moving)
        for vehicle in moving:
            self._where[vehicle] = to_deck
        return len(moving)

    def unload_deck(self, deck):
        self._require_deck(deck)
        self._save()
        unloaded = self._decks[deck]
        self._decks[deck] = []
        for vehicle in unloaded:
            del self._where[vehicle]
            self._dangerous.discard(vehicle)
        return list(unloaded)

    def undo(self):
        if not self._undo_stack:
            raise FerryError("nothing to undo")
        self._decks, self._where, self._open_air, self._dangerous = self._undo_stack.pop()

    def get_vehicles(self, deck):
        self._require_deck(deck)
        return list(self._decks[deck])

    def get_dangerous(self, deck):
        self._require_deck(deck)
        return [v for v in self._decks[deck] if v in self._dangerous]

    def get_deck_of(self, vehicle):
        self._require_vehicle(vehicle)
        return self._where[vehicle]

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        decks = dict(self._decks)
        self._undo_stack.append(
            (decks, dict(self._where), dict(self._open_air), set(self._dangerous))
        )

    def _require_allowed(self, vehicles, deck):
        # Every vehicle that would move is checked before any of them moves.
        if self._open_air[deck]:
            return
        for vehicle in vehicles:
            if vehicle in self._dangerous:
                raise NotAllowed(f"dangerous vehicle {vehicle!r} may not go on deck {deck!r}")

    def _require_deck(self, deck):
        # Non-str names are never stored, so they count as "never added" too.
        if not isinstance(deck, str) or deck not in self._decks:
            raise KeyError(deck)

    def _require_vehicle(self, vehicle):
        if not isinstance(vehicle, str) or vehicle not in self._where:
            raise KeyError(vehicle)
