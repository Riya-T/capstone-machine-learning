"""Hidden tests for the c_status change (status effects). Never shown to the
writer or the editor.

Usage (with party.py importable, e.g. in the sandbox):
    python -m pytest changes/c_status/private/test_status_new.py
"""

import pytest
from party import Incapacitated, Party, PartyError

NAMES = ["ana", "bo"]


@pytest.fixture
def party():
    p = Party()
    p.add_character("ana", 100)
    p.add_character("bo", 100)
    p.define_item("sword", 30)
    p.define_item("shield", 25)
    p.define_item("rope", 5)
    p.give_item("ana", "sword")
    p.give_item("ana", "shield")
    p.equip("ana", "sword")
    return p


def state(p):
    return {n: (p.get_bag(n), p.get_equipped(n), p.get_effects(n)) for n in NAMES}


def test_characters_start_without_effects(party):
    assert party.get_effects("ana") == []
    assert party.get_effects("bo") == []


def test_effects_are_listed_in_the_order_applied(party):
    party.apply_effect("ana", "petrified")
    party.apply_effect("ana", "stunned")
    assert party.get_effects("ana") == ["petrified", "stunned"]
    assert party.get_effects("bo") == []


def test_applying_or_removing_twice_is_harmless(party):
    party.apply_effect("ana", "stunned")
    party.apply_effect("ana", "stunned")
    assert party.get_effects("ana") == ["stunned"]
    party.remove_effect("ana", "stunned")
    party.remove_effect("ana", "stunned")
    party.remove_effect("bo", "petrified")
    assert party.get_effects("ana") == []
    assert party.get_effects("bo") == []


@pytest.mark.parametrize("effect", ["", "asleep", "Stunned", None, 1])
def test_unknown_effects_are_rejected(party, effect):
    before = state(party)
    with pytest.raises(ValueError):
        party.apply_effect("ana", effect)
    with pytest.raises(ValueError):
        party.remove_effect("ana", effect)
    assert state(party) == before


@pytest.mark.parametrize("method", ["apply_effect", "remove_effect"])
@pytest.mark.parametrize("name", ["cy", None, 2])
def test_effects_on_unknown_characters_raise_key_error(party, method, name):
    with pytest.raises(KeyError):
        getattr(party, method)(name, "stunned")
    with pytest.raises(KeyError):
        getattr(party, method)(name, "asleep")
    with pytest.raises(KeyError):
        party.get_effects(name)


def test_a_stunned_character_cannot_equip_or_unequip(party):
    party.apply_effect("ana", "stunned")
    before = state(party)
    with pytest.raises(Incapacitated):
        party.equip("ana", "shield")
    with pytest.raises(Incapacitated):
        party.unequip("ana", "sword")
    assert state(party) == before


def test_a_petrified_character_cannot_equip_unequip_or_receive(party):
    party.apply_effect("ana", "petrified")
    before = state(party)
    with pytest.raises(Incapacitated):
        party.equip("ana", "shield")
    with pytest.raises(Incapacitated):
        party.unequip("ana", "sword")
    with pytest.raises(Incapacitated):
        party.give_item("ana", "rope")
    assert state(party) == before


def test_effects_change_nothing_else_and_can_be_removed(party):
    party.apply_effect("ana", "stunned")
    party.apply_effect("ana", "petrified")
    assert party.get_bag("ana") == ["sword", "shield"]
    assert party.get_equipped("ana") == ["sword"]
    party.remove_effect("ana", "petrified")
    party.give_item("ana", "rope")
    with pytest.raises(Incapacitated):
        party.equip("ana", "rope")
    party.remove_effect("ana", "stunned")
    party.equip("ana", "rope")
    assert party.get_equipped("ana") == ["sword", "rope"]


def test_incapacitation_is_checked_before_other_party_errors(party):
    party.apply_effect("ana", "petrified")
    with pytest.raises(Incapacitated):
        party.equip("ana", "rope")  # not held
    with pytest.raises(Incapacitated):
        party.equip("ana", "sword")  # already equipped
    with pytest.raises(Incapacitated):
        party.unequip("ana", "shield")  # not equipped
    with pytest.raises(Incapacitated):
        party.give_item("ana", "sword")  # already held


def test_bad_input_is_reported_before_incapacitation(party):
    party.apply_effect("ana", "petrified")
    with pytest.raises(KeyError):
        party.equip("ana", "anvil")
    with pytest.raises(KeyError):
        party.give_item("ana", None)
    with pytest.raises(KeyError):
        party.equip("cy", "sword")


def test_other_characters_are_unaffected(party):
    party.apply_effect("ana", "petrified")
    party.give_item("bo", "rope")
    party.equip("bo", "rope")
    party.unequip("bo", "rope")
    assert party.get_bag("bo") == ["rope"]
    assert party.get_effects("bo") == []


def test_incapacitated_is_a_party_error():
    assert issubclass(Incapacitated, PartyError)
