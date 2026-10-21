"""Public checks for the c_trade change (swapping items). Shown to the
editor, never to the writer.

Usage (with party.py importable, e.g. in the sandbox):
    python -m pytest changes/c_trade/public/test_trade_public.py
"""

import pytest
from party import Party, PartyError


def make_party():
    party = Party()
    party.add_character("ana", 100)
    party.add_character("bo", 100)
    party.define_item("sword", 30)
    party.define_item("shield", 25)
    party.define_item("rope", 5)
    party.give_item("ana", "sword")
    party.give_item("ana", "rope")
    party.give_item("bo", "shield")
    return party


def test_a_trade_swaps_the_two_items():
    party = make_party()
    party.trade("ana", "sword", "bo", "shield")
    assert party.get_bag("ana") == ["rope", "shield"]
    assert party.get_bag("bo") == ["sword"]


def test_an_item_that_is_not_held_cannot_be_traded():
    party = make_party()
    with pytest.raises(PartyError):
        party.trade("ana", "shield", "bo", "sword")
    assert party.get_bag("ana") == ["sword", "rope"]
    assert party.get_bag("bo") == ["shield"]
