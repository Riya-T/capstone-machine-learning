"""Adventuring party where characters can be stunned or petrified.

Correct solution for party_inventory after c_status.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from party import Party
    party = Party()
    party.add_character("ana", 100)
    party.apply_effect("ana", "stunned")
    party.get_effects("ana")
"""


class PartyError(Exception):
    pass


class Incapacitated(PartyError):
    pass


EFFECTS = ("stunned", "petrified")


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


def check_effect(effect):
    if effect not in EFFECTS:
        raise ValueError(f"unknown effect {effect!r}")


class Party:
    def __init__(self):
        self._strengths = {}  # character name -> strength
        self._weights = {}  # item -> weight
        self._bags = {}  # character name -> items held, in the order given
        self._equipped = {}  # character name -> items equipped, in order
        self._effects = {}  # character name -> effects, in the order applied

    def add_character(self, name, strength):
        check_name(name, "character name")
        check_positive(strength, "strength")
        if name in self._strengths:
            raise PartyError(f"character {name!r} is already in the party")
        self._strengths[name] = strength
        self._bags[name] = []
        self._equipped[name] = []
        self._effects[name] = []

    def define_item(self, item, weight):
        check_name(item, "item name")
        check_positive(weight, "weight")
        if item in self._weights:
            raise PartyError(f"item {item!r} is already defined")
        self._weights[item] = weight

    def give_item(self, name, item):
        self._require_character(name)
        self._require_item(item)
        if "petrified" in self._effects[name]:
            raise Incapacitated(f"{name!r} is petrified")
        if item in self._bags[name]:
            raise PartyError(f"{name!r} already holds {item!r}")
        self._bags[name].append(item)

    def equip(self, name, item):
        self._require_character(name)
        self._require_item(item)
        self._require_able(name)
        if item not in self._bags[name]:
            raise PartyError(f"{name!r} does not hold {item!r}")
        if item in self._equipped[name]:
            raise PartyError(f"{name!r} already equipped {item!r}")
        self._equipped[name].append(item)

    def unequip(self, name, item):
        self._require_character(name)
        self._require_item(item)
        self._require_able(name)
        if item not in self._equipped[name]:
            raise PartyError(f"{name!r} has not equipped {item!r}")
        self._equipped[name].remove(item)

    def get_bag(self, name):
        self._require_character(name)
        return list(self._bags[name])

    def get_equipped(self, name):
        self._require_character(name)
        return list(self._equipped[name])

    def apply_effect(self, name, effect):
        self._require_character(name)
        check_effect(effect)
        if effect not in self._effects[name]:
            self._effects[name].append(effect)

    def remove_effect(self, name, effect):
        self._require_character(name)
        check_effect(effect)
        if effect in self._effects[name]:
            self._effects[name].remove(effect)

    def get_effects(self, name):
        self._require_character(name)
        return list(self._effects[name])

    def _require_character(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._strengths:
            raise KeyError(name)

    def _require_item(self, item):
        if not isinstance(item, str) or item not in self._weights:
            raise KeyError(item)

    def _require_able(self, name):
        if self._effects[name]:
            raise Incapacitated(f"{name!r} is {' and '.join(self._effects[name])}")
