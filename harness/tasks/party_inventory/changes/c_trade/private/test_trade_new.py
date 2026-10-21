"""Hidden tests for the c_trade change (swapping items). Never shown to the
writer or the editor.

Usage (with party.py importable, e.g. in the sandbox):
    python -m pytest changes/c_trade/private/test_trade_new.py
"""

import pytest
from party import Party, PartyError, TooHeavy

NAMES = ["ana", "bo", "cy"]


@pytest.fixture
def party():
    p = Party()
    p.add_character("ana", 40)
    p.add_character("bo", 40)
    p.add_character("cy", 100)
    p.define_item("sword", 30)
    p.define_item("shield", 25)
    p.define_item("rope", 5)
    p.define_item("lamp", 10)
    p.give_item("ana", "sword")
    p.give_item("ana", "rope")
    p.give_item("bo", "shield")
    p.give_item("bo", "lamp")
    return p


def state(p):
    return {n: (p.get_bag(n), p.get_equipped(n), p.get_carry_weight(n)) for n in NAMES}


def test_traded_items_go_to_the_end_of_each_bag(party):
    party.trade("ana", "sword", "bo", "shield")
    assert party.get_bag("ana") == ["rope", "shield"]
    assert party.get_bag("bo") == ["lamp", "sword"]
    assert party.get_carry_weight("ana") == 30
    assert party.get_carry_weight("bo") == 40


def test_equipment_is_untouched_by_a_trade(party):
    party.equip("ana", "rope")
    party.equip("bo", "lamp")
    party.trade("ana", "sword", "bo", "shield")
    assert party.get_equipped("ana") == ["rope"]
    assert party.get_equipped("bo") == ["lamp"]


def test_a_traded_item_can_be_equipped_by_its_new_holder(party):
    party.trade("ana", "sword", "bo", "shield")
    party.equip("bo", "sword")
    assert party.get_equipped("bo") == ["sword"]
    with pytest.raises(PartyError):
        party.equip("ana", "sword")


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.trade("dee", "sword", "bo", "shield"),
        lambda p: p.trade("ana", "sword", "dee", "shield"),
        lambda p: p.trade(None, "sword", "bo", "shield"),
        lambda p: p.trade("ana", "anvil", "bo", "shield"),
        lambda p: p.trade("ana", "sword", "bo", "anvil"),
        lambda p: p.trade("ana", "sword", "bo", None),
    ],
)
def test_trades_with_unknown_names_raise_key_error_and_move_nothing(party, call):
    before = state(party)
    with pytest.raises(KeyError):
        call(party)
    assert state(party) == before


def test_a_character_cannot_trade_with_themselves(party):
    before = state(party)
    with pytest.raises(ValueError):
        party.trade("ana", "sword", "ana", "rope")
    assert state(party) == before


def test_an_item_cannot_be_traded_for_itself(party):
    party.give_item("cy", "sword")
    before = state(party)
    with pytest.raises(ValueError):
        party.trade("ana", "sword", "cy", "sword")
    assert state(party) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.trade("ana", "shield", "bo", "lamp"),  # ana does not hold shield
        lambda p: p.trade("ana", "sword", "bo", "rope"),  # bo does not hold rope
        lambda p: p.trade("ana", "sword", "cy", "lamp"),  # cy holds nothing
    ],
)
def test_both_sides_must_hold_what_they_give(party, call):
    before = state(party)
    with pytest.raises(PartyError) as excinfo:
        call(party)
    assert not isinstance(excinfo.value, TooHeavy)
    assert state(party) == before


def test_equipped_items_cannot_be_traded(party):
    party.equip("bo", "shield")
    before = state(party)
    with pytest.raises(PartyError) as excinfo:
        party.trade("ana", "sword", "bo", "shield")
    assert not isinstance(excinfo.value, TooHeavy)
    with pytest.raises(PartyError):
        party.trade("bo", "shield", "ana", "sword")
    assert state(party) == before
    party.unequip("bo", "shield")
    party.trade("ana", "sword", "bo", "shield")
    assert party.get_bag("bo") == ["lamp", "sword"]


def test_a_character_cannot_receive_an_item_they_already_hold(party):
    party.give_item("cy", "rope")
    party.give_item("cy", "shield")
    before = state(party)
    with pytest.raises(PartyError) as excinfo:
        party.trade("ana", "rope", "cy", "shield")
    assert not isinstance(excinfo.value, TooHeavy)
    assert state(party) == before


def test_a_trade_that_would_overload_either_side_moves_nothing(party):
    # ana carries 35 of 40; taking the shield (25) for the rope (5) would make 55.
    before = state(party)
    with pytest.raises(TooHeavy):
        party.trade("ana", "rope", "bo", "shield")
    # bo carries 35 of 40; taking the sword (30) for the lamp (10) would make 55.
    with pytest.raises(TooHeavy):
        party.trade("ana", "sword", "bo", "lamp")
    assert state(party) == before


def test_a_trade_is_judged_on_the_weight_after_the_swap(party):
    # cy has lots of room; ana gives rope (5) and gets lamp (10): 35 -> 40.
    party.give_item("cy", "lamp")
    party.trade("ana", "rope", "cy", "lamp")
    assert party.get_carry_weight("ana") == 40
    assert party.get_bag("ana") == ["sword", "lamp"]
    assert party.get_bag("cy") == ["rope"]


def test_errors_are_reported_in_order(party):
    party.equip("bo", "shield")
    with pytest.raises(KeyError):
        party.trade("dee", "anvil", "dee", "anvil")
    with pytest.raises(KeyError):
        party.trade("ana", "anvil", "ana", "anvil")
    with pytest.raises(ValueError):
        party.trade("ana", "shield", "ana", "shield")
    with pytest.raises(PartyError) as excinfo:
        party.trade("ana", "rope", "bo", "shield")  # equipped, and too heavy for ana
    assert not isinstance(excinfo.value, TooHeavy)
