"""Ferry decks: which vehicles are on each deck, in the order they came on.

Correct solution for ferry_decks before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ferry import Ferry
    ferry = Ferry()
    ferry.add_deck("upper")
    ferry.board("van", "upper")
"""


class FerryError(Exception):
    pass


class Ferry:
    def __init__(self):
        self._decks = {}  # deck name -> vehicle names, in the order they came on
        self._where = {}  # vehicle name -> deck name, for every vehicle aboard

    def add_deck(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("deck name must be a non-empty str")
        if name in self._decks:
            raise FerryError(f"deck name {name!r} is already used")
        self._decks[name] = []

    def board(self, vehicle, deck):
        self._require_deck(deck)
        if not isinstance(vehicle, str) or not vehicle:
            raise ValueError("vehicle name must be a non-empty str")
        if vehicle in self._where:
            raise FerryError(f"vehicle {vehicle!r} is already aboard")
        self._decks[deck].append(vehicle)
        self._where[vehicle] = deck

    def leave(self, vehicle):
        self._require_vehicle(vehicle)
        deck = self._where.pop(vehicle)
        self._decks[deck].remove(vehicle)

    def move_vehicle(self, vehicle, deck):
        self._require_vehicle(vehicle)
        self._require_deck(deck)
        old = self._where[vehicle]
        if old == deck:
            raise ValueError(f"vehicle {vehicle!r} is already on deck {deck!r}")
        self._decks[old].remove(vehicle)
        self._decks[deck].append(vehicle)
        self._where[vehicle] = deck

    def move_deck(self, from_deck, to_deck):
        self._require_deck(from_deck)
        self._require_deck(to_deck)
        if from_deck == to_deck:
            raise ValueError("cannot move a deck's vehicles onto the same deck")
        moving = self._decks[from_deck]
        self._decks[from_deck] = []
        self._decks[to_deck].extend(moving)
        for vehicle in moving:
            self._where[vehicle] = to_deck
        return len(moving)

    def unload_deck(self, deck):
        self._require_deck(deck)
        unloaded = self._decks[deck]
        self._decks[deck] = []
        for vehicle in unloaded:
            del self._where[vehicle]
        return unloaded

    def get_vehicles(self, deck):
        self._require_deck(deck)
        return list(self._decks[deck])

    def get_deck_of(self, vehicle):
        self._require_vehicle(vehicle)
        return self._where[vehicle]

    def _require_deck(self, deck):
        # Non-str names are never stored, so they count as "never added" too.
        if not isinstance(deck, str) or deck not in self._decks:
            raise KeyError(deck)

    def _require_vehicle(self, vehicle):
        if not isinstance(vehicle, str) or vehicle not in self._where:
            raise KeyError(vehicle)
