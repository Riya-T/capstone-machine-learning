"""Hidden tests for the c_groups change (client groups). Never shown to the
writer or the editor.

Usage (with gateway.py importable, e.g. in the sandbox):
    python -m pytest changes/c_groups/private/test_groups_new.py
"""

import pytest
from gateway import AccessDenied, ClientBanned, Gateway, GatewayError


@pytest.fixture
def gateway():
    gw = Gateway()
    for name in ["alpha", "bravo", "charlie", "delta"]:
        gw.register(name)
    gw.create_group("staff")
    gw.create_group("guests")
    gw.assign_group("charlie", "staff")
    gw.assign_group("alpha", "staff")
    return gw


def state(gw):
    return (
        gw.get_allowed(),
        gw.get_banned(),
        {c: (gw.get_group(c), gw.get_messages(c)) for c in gw.get_clients()},
    )


def test_groups_are_listed_in_creation_order(gateway):
    gateway.create_group("admins")
    assert gateway.get_groups() == ["staff", "guests", "admins"]
    assert Gateway().get_groups() == []


def test_invalid_group_names_are_rejected(gateway):
    with pytest.raises(ValueError):
        gateway.create_group("")
    with pytest.raises(GatewayError):
        gateway.create_group("staff")
    assert gateway.get_groups() == ["staff", "guests"]
    assert gateway.get_members("staff") == ["alpha", "charlie"]


def test_members_are_listed_in_registration_order(gateway):
    gateway.assign_group("delta", "staff")
    gateway.assign_group("bravo", "staff")
    assert gateway.get_members("staff") == ["alpha", "bravo", "charlie", "delta"]
    assert gateway.get_members("guests") == []


def test_clients_start_in_no_group(gateway):
    assert gateway.get_group("bravo") is None
    assert gateway.get_group("delta") is None
    assert gateway.get_group("alpha") == "staff"


def test_assigning_again_moves_the_client(gateway):
    gateway.assign_group("alpha", "guests")
    assert gateway.get_group("alpha") == "guests"
    assert gateway.get_members("staff") == ["charlie"]
    assert gateway.get_members("guests") == ["alpha"]
    gateway.assign_group("alpha", "guests")
    assert gateway.get_members("guests") == ["alpha"]


def test_allow_group_allows_every_member_and_nobody_else(gateway):
    gateway.allow_group("staff")
    assert gateway.get_allowed() == ["alpha", "charlie"]
    gateway.send("charlie", "hello")
    with pytest.raises(AccessDenied):
        gateway.send("bravo", "hello")


def test_late_members_are_not_allowed_automatically(gateway):
    gateway.allow_group("staff")
    gateway.assign_group("bravo", "staff")
    assert gateway.get_allowed() == ["alpha", "charlie"]
    with pytest.raises(AccessDenied):
        gateway.send("bravo", "hello")


def test_revoke_group_revokes_only_the_members(gateway):
    for name in ["alpha", "bravo", "charlie", "delta"]:
        gateway.allow(name)
    gateway.revoke_group("staff")
    assert gateway.get_allowed() == ["bravo", "delta"]
    gateway.revoke_group("staff")
    assert gateway.get_allowed() == ["bravo", "delta"]


def test_a_banned_member_blocks_the_whole_group(gateway):
    gateway.ban("charlie")
    before = state(gateway)
    with pytest.raises(ClientBanned):
        gateway.allow_group("staff")
    assert state(gateway) == before
    assert gateway.get_allowed() == []


def test_an_empty_group_can_be_allowed_and_revoked(gateway):
    gateway.allow("alpha")
    gateway.allow_group("guests")
    gateway.revoke_group("guests")
    assert gateway.get_allowed() == ["alpha"]


@pytest.mark.parametrize(
    "call",
    [
        lambda gw: gw.assign_group("alpha", "admins"),
        lambda gw: gw.get_members("admins"),
        lambda gw: gw.allow_group("admins"),
        lambda gw: gw.revoke_group("admins"),
        lambda gw: gw.get_members(None),
    ],
)
def test_groups_that_do_not_exist_raise_key_error(gateway, call):
    before = state(gateway)
    with pytest.raises(KeyError):
        call(gateway)
    assert state(gateway) == before


@pytest.mark.parametrize("bad", ["echo", None, 1])
def test_group_methods_raise_key_error_for_unknown_clients(gateway, bad):
    with pytest.raises(KeyError):
        gateway.assign_group(bad, "staff")
    with pytest.raises(KeyError):
        gateway.get_group(bad)
    with pytest.raises(KeyError):
        gateway.assign_group(bad, "admins")
    assert gateway.get_members("staff") == ["alpha", "charlie"]


def test_group_membership_changes_nothing_else(gateway):
    with pytest.raises(AccessDenied):
        gateway.send("alpha", "hello")
    gateway.allow("alpha")
    gateway.send("alpha", "hello")
    gateway.ban("alpha")
    assert gateway.get_group("alpha") == "staff"
    assert gateway.get_members("staff") == ["alpha", "charlie"]
    assert gateway.get_messages("alpha") == ["hello"]
