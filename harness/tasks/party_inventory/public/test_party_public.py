"""Public checks for party.py.

Usage (with party.py importable, e.g. in the sandbox):
    python -m pytest public/test_party_public.py
"""

import pytest
from party import Party, PartyError


@pytest.fixture
def party():
    p = Party()
    p.add_character("ana", 100)
    p.add_character("bo", 100)
    p.define_item("sword", 30)
    p.define_item("shield", 25)
    p.define_item("rope", 5)
    return p


def test_items_are_held_in_the_order_given(party):
    party.give_item("ana", "rope")
    party.give_item("ana", "sword")
    assert party.get_bag("ana") == ["rope", "sword"]
    assert party.get_bag("bo") == []


def test_equipping_keeps_the_item_in_the_bag(party):
    party.give_item("ana", "sword")
    party.give_item("ana", "shield")
    party.equip("ana", "shield")
    assert party.get_equipped("ana") == ["shield"]
    assert party.get_bag("ana") == ["sword", "shield"]


def test_unequipping_takes_the_item_off_but_keeps_it(party):
    party.give_item("ana", "sword")
    party.equip("ana", "sword")
    party.unequip("ana", "sword")
    assert party.get_equipped("ana") == []
    assert party.get_bag("ana") == ["sword"]


def test_an_item_must_be_held_to_be_equipped(party):
    with pytest.raises(PartyError):
        party.equip("ana", "sword")
    assert party.get_equipped("ana") == []


def test_strengths_and_weights_must_be_positive(party):
    with pytest.raises(ValueError):
        party.add_character("cy", 0)
    with pytest.raises(ValueError):
        party.define_item("feather", -1)


def test_unknown_characters_and_items_raise_key_error(party):
    with pytest.raises(KeyError):
        party.get_bag("cy")
    with pytest.raises(KeyError):
        party.give_item("ana", "lamp")
