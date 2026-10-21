"""Hidden tests for the initial party_inventory spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with party.py importable, e.g. in the sandbox):
    python -m pytest private/test_party_initial.py
"""

import pytest
from party import Party, PartyError

BAD_NUMBERS = [0, -5, 1.5, "10", None]
NAMES = ["ana", "bo"]


@pytest.fixture
def party():
    p = Party()
    p.add_character("ana", 100)
    p.add_character("bo", 100)
    p.define_item("sword", 30)
    p.define_item("shield", 25)
    p.define_item("rope", 5)
    p.define_item("lamp", 10)
    return p


def state(p):
    """Every bag and equipment list, to check that a failed call changed nothing."""
    return {n: (p.get_bag(n), p.get_equipped(n)) for n in NAMES}


# --- characters and items ---------------------------------------------------


def test_a_new_character_holds_and_equips_nothing(party):
    party.add_character("cy", 40)
    assert party.get_bag("cy") == []
    assert party.get_equipped("cy") == []


def test_adding_a_character_twice_is_rejected(party):
    party.give_item("ana", "rope")
    with pytest.raises(PartyError):
        party.add_character("ana", 50)
    assert party.get_bag("ana") == ["rope"]


def test_defining_an_item_twice_is_rejected(party):
    with pytest.raises(PartyError):
        party.define_item("sword", 1)
    party.give_item("ana", "sword")
    assert party.get_bag("ana") == ["sword"]


@pytest.mark.parametrize("name", [""])
def test_empty_names_are_rejected(party, name):
    with pytest.raises(ValueError):
        party.add_character(name, 10)
    with pytest.raises(ValueError):
        party.define_item(name, 10)
    with pytest.raises(KeyError):
        party.get_bag(name)
    with pytest.raises(KeyError):
        party.give_item("ana", name)


@pytest.mark.parametrize("strength", BAD_NUMBERS)
def test_invalid_strengths_are_rejected(party, strength):
    with pytest.raises(ValueError):
        party.add_character("cy", strength)
    with pytest.raises(KeyError):
        party.get_bag("cy")


@pytest.mark.parametrize("weight", BAD_NUMBERS)
def test_invalid_weights_are_rejected(party, weight):
    with pytest.raises(ValueError):
        party.define_item("feather", weight)
    with pytest.raises(KeyError):
        party.give_item("ana", "feather")


def test_a_bad_number_is_reported_before_a_repeated_name(party):
    with pytest.raises(ValueError):
        party.add_character("ana", -1)
    with pytest.raises(ValueError):
        party.define_item("sword", -1)


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.give_item("cy", "sword"),
        lambda p: p.equip("cy", "sword"),
        lambda p: p.unequip("cy", "sword"),
        lambda p: p.get_bag("cy"),
        lambda p: p.get_equipped("cy"),
        lambda p: p.get_bag(None),
        lambda p: p.get_bag(1),
        lambda p: p.give_item("ana", "feather"),
        lambda p: p.equip("ana", "feather"),
        lambda p: p.unequip("ana", "feather"),
        lambda p: p.give_item("ana", None),
        lambda p: p.equip("ana", 2),
    ],
)
def test_unknown_characters_and_items_raise_key_error_and_change_nothing(party, call):
    party.give_item("ana", "sword")
    party.equip("ana", "sword")
    before = state(party)
    with pytest.raises(KeyError):
        call(party)
    assert state(party) == before


def test_an_unknown_character_is_reported_before_an_unknown_item(party):
    # Either would be KeyError; combined with a bad item for a known
    # character the error is still KeyError, never PartyError.
    with pytest.raises(KeyError):
        party.give_item("cy", "feather")
    with pytest.raises(KeyError):
        party.equip("ana", "feather")


# --- bags -------------------------------------------------------------------


def test_bags_keep_items_in_the_order_given(party):
    for item in ["lamp", "sword", "rope"]:
        party.give_item("ana", item)
    assert party.get_bag("ana") == ["lamp", "sword", "rope"]
    assert party.get_bag("bo") == []


def test_the_same_item_can_be_held_by_several_characters(party):
    party.give_item("ana", "sword")
    party.give_item("bo", "sword")
    assert party.get_bag("ana") == ["sword"]
    assert party.get_bag("bo") == ["sword"]


def test_a_character_holds_at_most_one_of_each_item(party):
    party.give_item("ana", "sword")
    party.give_item("ana", "rope")
    before = state(party)
    with pytest.raises(PartyError):
        party.give_item("ana", "sword")
    assert state(party) == before


# --- equipment --------------------------------------------------------------


def test_equipped_items_are_listed_in_the_order_equipped(party):
    for item in ["sword", "shield", "lamp"]:
        party.give_item("ana", item)
    party.equip("ana", "lamp")
    party.equip("ana", "sword")
    assert party.get_equipped("ana") == ["lamp", "sword"]
    assert party.get_bag("ana") == ["sword", "shield", "lamp"]


def test_equipping_an_item_that_is_not_held_changes_nothing(party):
    party.give_item("ana", "sword")
    before = state(party)
    with pytest.raises(PartyError):
        party.equip("ana", "shield")
    assert state(party) == before


def test_equipping_the_same_item_twice_is_rejected(party):
    party.give_item("ana", "sword")
    party.equip("ana", "sword")
    before = state(party)
    with pytest.raises(PartyError):
        party.equip("ana", "sword")
    assert state(party) == before


def test_unequipping_keeps_the_item_and_the_rest_of_the_equipment(party):
    for item in ["sword", "shield", "lamp"]:
        party.give_item("ana", item)
        party.equip("ana", item)
    party.unequip("ana", "shield")
    assert party.get_equipped("ana") == ["sword", "lamp"]
    assert party.get_bag("ana") == ["sword", "shield", "lamp"]


def test_an_unequipped_item_can_be_equipped_again_at_the_end(party):
    party.give_item("ana", "sword")
    party.give_item("ana", "shield")
    party.equip("ana", "sword")
    party.equip("ana", "shield")
    party.unequip("ana", "sword")
    party.equip("ana", "sword")
    assert party.get_equipped("ana") == ["shield", "sword"]


@pytest.mark.parametrize("item", ["sword", "rope"])
def test_unequipping_an_item_that_is_not_equipped_is_rejected(party, item):
    # "sword" is held but not equipped; "rope" is not even held.
    party.give_item("ana", "sword")
    party.give_item("ana", "lamp")
    party.equip("ana", "lamp")
    before = state(party)
    with pytest.raises(PartyError):
        party.unequip("ana", item)
    assert state(party) == before


def test_equipment_is_kept_per_character(party):
    party.give_item("ana", "sword")
    party.give_item("bo", "sword")
    party.equip("ana", "sword")
    assert party.get_equipped("ana") == ["sword"]
    assert party.get_equipped("bo") == []
    with pytest.raises(PartyError):
        party.unequip("bo", "sword")


def test_parties_do_not_share_characters_or_items():
    first, second = Party(), Party()
    first.add_character("ana", 10)
    first.define_item("sword", 3)
    with pytest.raises(KeyError):
        second.get_bag("ana")
    second.add_character("ana", 20)
    with pytest.raises(KeyError):
        second.give_item("ana", "sword")
    assert second.get_bag("ana") == []
