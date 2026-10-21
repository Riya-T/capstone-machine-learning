"""Public checks for the c_status change (status effects). Shown to the
editor, never to the writer.

Usage (with party.py importable, e.g. in the sandbox):
    python -m pytest changes/c_status/public/test_status_public.py
"""

import pytest
from party import Incapacitated, Party


def make_party():
    party = Party()
    party.add_character("ana", 100)
    party.define_item("sword", 30)
    party.give_item("ana", "sword")
    return party


def test_a_stunned_character_cannot_equip_until_the_effect_is_removed():
    party = make_party()
    party.apply_effect("ana", "stunned")
    assert party.get_effects("ana") == ["stunned"]
    with pytest.raises(Incapacitated):
        party.equip("ana", "sword")
    party.remove_effect("ana", "stunned")
    assert party.get_effects("ana") == []
    party.equip("ana", "sword")
    assert party.get_equipped("ana") == ["sword"]


def test_a_stunned_character_can_still_be_given_items():
    party = make_party()
    party.define_item("rope", 5)
    party.apply_effect("ana", "stunned")
    party.give_item("ana", "rope")
    assert party.get_bag("ana") == ["sword", "rope"]
