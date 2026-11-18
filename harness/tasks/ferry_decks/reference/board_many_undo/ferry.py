"""Ferry decks with groups of vehicles that board as a whole, and undo.

Correct solution for ferry_decks after c_board_many and c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ferry import Ferry
    ferry = Ferry()
    ferry.add_deck("upper")
    ferry.board_many([("van", "upper"), ("bus", "upper")])  # returns 2
    ferry.undo()  # both are off the ferry again
"""


class FerryError(Exception):
    pass


class Ferry:
    def __init__(self):
        self._decks = {}  # deck name -> vehicle names, in the order they came on
        self._where = {}  # vehicle name -> deck name, for every vehicle aboard
        self._undo_stack = []  # copies of the state as it was before each call

    def add_deck(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("deck name must be a non-empty str")
        if name in self._decks:
            raise FerryError(f"deck name {name!r} is already used")
        self._save()
        self._decks[name] = []

    def board(self, vehicle, deck):
        self._check_boarding(vehicle, deck, set())
        self._save()
        self._decks[deck].append(vehicle)
        self._where[vehicle] = deck

    def board_many(self, arrivals):
        # The whole group is checked, each tuple seeing the ones before it,
        # before any vehicle boards; then it is recorded as one call.
        boarding = set()
        for vehicle, deck in arrivals:
            self._check_boarding(vehicle, deck, boarding)
            boarding.add(vehicle)
        self._save()
        for vehicle, deck in arrivals:
            self._decks[deck].append(vehicle)
            self._where[vehicle] = deck
        return len(arrivals)

    def leave(self, vehicle):
        self._require_vehicle(vehicle)
        self._save()
        deck = self._where.pop(vehicle)
        self._decks[deck].remove(vehicle)

    def move_vehicle(self, vehicle, deck):
        self._require_vehicle(vehicle)
        self._require_deck(deck)
        old = self._where[vehicle]
        if old == deck:
            raise ValueError(f"vehicle {vehicle!r} is already on deck {deck!r}")
        self._save()
        self._decks[old].remove(vehicle)
        self._decks[deck].append(vehicle)
        self._where[vehicle] = deck

    def move_deck(self, from_deck, to_deck):
        self._require_deck(from_deck)
        self._require_deck(to_deck)
        if from_deck == to_deck:
            raise ValueError("cannot move a deck's vehicles onto the same deck")
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
        return list(unloaded)

    def undo(self):
        if not self._undo_stack:
            raise FerryError("nothing to undo")
        self._decks, self._where = self._undo_stack.pop()

    def get_vehicles(self, deck):
        self._require_deck(deck)
        return list(self._decks[deck])

    def get_deck_of(self, vehicle):
        self._require_vehicle(vehicle)
        return self._where[vehicle]

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        decks = {name: list(vehicles) for name, vehicles in self._decks.items()}
        self._undo_stack.append((decks, dict(self._where)))

    def _check_boarding(self, vehicle, deck, boarding):
        self._require_deck(deck)
        if not isinstance(vehicle, str) or not vehicle:
            raise ValueError("vehicle name must be a non-empty str")
        if vehicle in self._where or vehicle in boarding:
            raise FerryError(f"vehicle {vehicle!r} is already aboard")

    def _require_deck(self, deck):
        # Non-str names are never stored, so they count as "never added" too.
        if not isinstance(deck, str) or deck not in self._decks:
            raise KeyError(deck)

    def _require_vehicle(self, vehicle):
        if not isinstance(vehicle, str) or vehicle not in self._where:
            raise KeyError(vehicle)
