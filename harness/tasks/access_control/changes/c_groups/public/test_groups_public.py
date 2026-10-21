"""Public checks for the c_groups change (client groups). Shown to the
editor, never to the writer.

Usage (with gateway.py importable, e.g. in the sandbox):
    python -m pytest changes/c_groups/public/test_groups_public.py
"""

import pytest
from gateway import Gateway


def test_a_group_can_be_allowed_at_once():
    gw = Gateway()
    for name in ["alpha", "bravo", "charlie"]:
        gw.register(name)
    gw.create_group("staff")
    gw.assign_group("charlie", "staff")
    gw.assign_group("alpha", "staff")
    assert gw.get_groups() == ["staff"]
    assert gw.get_members("staff") == ["alpha", "charlie"]
    assert gw.get_group("alpha") == "staff"
    assert gw.get_group("bravo") is None
    gw.allow_group("staff")
    assert gw.get_allowed() == ["alpha", "charlie"]
    gw.revoke_group("staff")
    assert gw.get_allowed() == []


def test_a_client_is_in_at_most_one_group():
    gw = Gateway()
    gw.register("alpha")
    gw.create_group("staff")
    gw.create_group("guests")
    gw.assign_group("alpha", "staff")
    gw.assign_group("alpha", "guests")
    assert gw.get_group("alpha") == "guests"
    assert gw.get_members("staff") == []
    assert gw.get_members("guests") == ["alpha"]
    with pytest.raises(KeyError):
        gw.get_members("admins")
