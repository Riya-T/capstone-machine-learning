"""Public checks for the c_carry_limit change (strength limits the load).
Shown to the editor, never to the writer.

Usage (with party.py importable, e.g. in the sandbox):
    python -m pytest changes/c_carry_limit/public/test_carry_limit_public.py
"""

import pytest
from party import Party, TooHeavy


def test_a_character_cannot_carry_more_than_their_strength():
    party = Party()
    party.add_character("ana", 40)
    party.define_item("sword", 30)
    party.define_item("shield", 25)
    party.give_item("ana", "sword")
    with pytest.raises(TooHeavy):
        party.give_item("ana", "shield")
    assert party.get_bag("ana") == ["sword"]
    assert party.get_carry_weight("ana") == 30


def test_strength_can_be_raised_to_make_room():
    party = Party()
    party.add_character("ana", 40)
    party.define_item("sword", 30)
    party.define_item("shield", 25)
    party.give_item("ana", "sword")
    party.set_strength("ana", 55)
    assert party.get_strength("ana") == 55
    party.give_item("ana", "shield")
    assert party.get_carry_weight("ana") == 55
