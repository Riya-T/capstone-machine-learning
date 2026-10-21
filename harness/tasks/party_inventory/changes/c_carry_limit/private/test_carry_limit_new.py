"""Hidden tests for the c_carry_limit change (strength limits the load).
Never shown to the writer or the editor.

Usage (with party.py importable, e.g. in the sandbox):
    python -m pytest changes/c_carry_limit/private/test_carry_limit_new.py
"""

import pytest
from party import Party, PartyError, TooHeavy

BAD_STRENGTHS = [0, -5, 1.5, "10", None]
NAMES = ["ana", "bo"]


@pytest.fixture
def party():
    p = Party()
    p.add_character("ana", 40)
    p.add_character("bo", 10)
    p.define_item("sword", 30)
    p.define_item("shield", 25)
    p.define_item("rope", 5)
    p.define_item("lamp", 10)
    return p


def state(p):
    return {n: (p.get_bag(n), p.get_equipped(n), p.get_carry_weight(n)) for n in NAMES}


def test_carry_weight_sums_the_whole_bag(party):
    assert party.get_carry_weight("ana") == 0
    party.give_item("ana", "sword")
    party.give_item("ana", "rope")
    party.equip("ana", "sword")
    assert party.get_carry_weight("ana") == 35
    assert party.get_carry_weight("bo") == 0


def test_a_load_of_exactly_the_strength_is_allowed(party):
    party.give_item("ana", "sword")
    party.give_item("ana", "lamp")
    assert party.get_carry_weight("ana") == 40
    party.give_item("bo", "lamp")
    assert party.get_carry_weight("bo") == 10


def test_an_item_that_would_overload_is_refused_and_nothing_changes(party):
    party.give_item("ana", "sword")
    party.give_item("ana", "rope")
    before = state(party)
    with pytest.raises(TooHeavy):
        party.give_item("ana", "lamp")
    with pytest.raises(TooHeavy):
        party.give_item("bo", "shield")
    assert state(party) == before
    party.give_item("bo", "rope")
    assert party.get_bag("bo") == ["rope"]


def test_too_heavy_is_a_party_error():
    assert issubclass(TooHeavy, PartyError)


def test_too_heavy_comes_after_the_other_checks(party):
    party.give_item("bo", "lamp")
    with pytest.raises(KeyError):
        party.give_item("cy", "sword")
    with pytest.raises(KeyError):
        party.give_item("bo", "anvil")
    with pytest.raises(PartyError) as excinfo:
        party.give_item("bo", "lamp")
    assert not isinstance(excinfo.value, TooHeavy)


def test_strength_is_reported_as_given(party):
    assert party.get_strength("ana") == 40
    assert party.get_strength("bo") == 10
    party.add_character("cy", 7)
    assert party.get_strength("cy") == 7


def test_lowering_strength_down_to_the_load_is_allowed(party):
    party.give_item("ana", "sword")
    party.set_strength("ana", 30)
    assert party.get_strength("ana") == 30
    with pytest.raises(TooHeavy):
        party.give_item("ana", "rope")
    assert party.get_bag("ana") == ["sword"]


def test_lowering_strength_below_the_load_is_refused(party):
    party.give_item("ana", "sword")
    party.give_item("ana", "rope")
    before = state(party)
    with pytest.raises(PartyError):
        party.set_strength("ana", 34)
    assert party.get_strength("ana") == 40
    assert state(party) == before


@pytest.mark.parametrize("strength", BAD_STRENGTHS)
def test_invalid_new_strengths_are_refused(party, strength):
    with pytest.raises(ValueError):
        party.set_strength("ana", strength)
    assert party.get_strength("ana") == 40


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.get_carry_weight("cy"),
        lambda p: p.get_strength("cy"),
        lambda p: p.set_strength("cy", 10),
        lambda p: p.get_carry_weight(None),
        lambda p: p.get_strength(3),
    ],
)
def test_strength_calls_for_unknown_characters_raise_key_error(party, call):
    with pytest.raises(KeyError):
        call(party)


def test_set_strength_reports_errors_in_order(party):
    party.give_item("ana", "sword")
    with pytest.raises(KeyError):
        party.set_strength("cy", -1)
    with pytest.raises(ValueError):
        party.set_strength("ana", -1)
    assert party.get_strength("ana") == 40


def test_raising_strength_lets_a_refused_item_be_given(party):
    party.give_item("bo", "lamp")
    with pytest.raises(TooHeavy):
        party.give_item("bo", "rope")
    party.set_strength("bo", 15)
    party.give_item("bo", "rope")
    assert party.get_bag("bo") == ["lamp", "rope"]
    assert party.get_carry_weight("bo") == 15
