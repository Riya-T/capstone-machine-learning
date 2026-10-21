"""Adventuring party where a character's strength limits what they carry.

Correct solution for party_inventory after c_carry_limit.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from party import Party
    party = Party()
    party.add_character("ana", 40)
    party.define_item("sword", 30)
    party.give_item("ana", "sword")
    party.get_carry_weight("ana")
"""


class PartyError(Exception):
    pass


class TooHeavy(PartyError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


class Party:
    def __init__(self):
        self._strengths = {}  # character name -> strength
        self._weights = {}  # item -> weight
        self._bags = {}  # character name -> items held, in the order given
        self._equipped = {}  # character name -> items equipped, in order

    def add_character(self, name, strength):
        check_name(name, "character name")
        check_positive(strength, "strength")
        if name in self._strengths:
            raise PartyError(f"character {name!r} is already in the party")
        self._strengths[name] = strength
        self._bags[name] = []
        self._equipped[name] = []

    def define_item(self, item, weight):
        check_name(item, "item name")
        check_positive(weight, "weight")
        if item in self._weights:
            raise PartyError(f"item {item!r} is already defined")
        self._weights[item] = weight

    def give_item(self, name, item):
        self._require_character(name)
        self._require_item(item)
        if item in self._bags[name]:
            raise PartyError(f"{name!r} already holds {item!r}")
        self._require_can_carry(name, self.get_carry_weight(name) + self._weights[item])
        self._bags[name].append(item)

    def equip(self, name, item):
        self._require_character(name)
        self._require_item(item)
        if item not in self._bags[name]:
            raise PartyError(f"{name!r} does not hold {item!r}")
        if item in self._equipped[name]:
            raise PartyError(f"{name!r} already equipped {item!r}")
        self._equipped[name].append(item)

    def unequip(self, name, item):
        self._require_character(name)
        self._require_item(item)
        if item not in self._equipped[name]:
            raise PartyError(f"{name!r} has not equipped {item!r}")
        self._equipped[name].remove(item)

    def get_bag(self, name):
        self._require_character(name)
        return list(self._bags[name])

    def get_equipped(self, name):
        self._require_character(name)
        return list(self._equipped[name])

    def get_carry_weight(self, name):
        self._require_character(name)
        return sum(self._weights[item] for item in self._bags[name])

    def get_strength(self, name):
        self._require_character(name)
        return self._strengths[name]

    def set_strength(self, name, strength):
        self._require_character(name)
        check_positive(strength, "strength")
        if self.get_carry_weight(name) > strength:
            raise PartyError(f"{name!r} already carries more than {strength}")
        self._strengths[name] = strength

    def _require_character(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._strengths:
            raise KeyError(name)

    def _require_item(self, item):
        if not isinstance(item, str) or item not in self._weights:
            raise KeyError(item)

    def _require_can_carry(self, name, weight):
        if weight > self._strengths[name]:
            raise TooHeavy(f"{name!r} cannot carry {weight}")
