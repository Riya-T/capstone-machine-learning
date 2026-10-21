"""Hidden tests for the c_ban change (banned clients). Never shown to the
writer or the editor.

Usage (with gateway.py importable, e.g. in the sandbox):
    python -m pytest changes/c_ban/private/test_ban_new.py
"""

import pytest
from gateway import AccessDenied, ClientBanned, Gateway, GatewayError


@pytest.fixture
def gateway():
    gw = Gateway()
    gw.register("alpha")
    gw.register("bravo")
    gw.register("charlie")
    gw.allow("alpha")
    gw.allow("bravo")
    gw.send("alpha", "hello")
    return gw


def state(gw):
    return (gw.get_allowed(), {c: gw.get_messages(c) for c in gw.get_clients()})


def test_clients_start_unbanned(gateway):
    assert not gateway.is_banned("alpha")
    assert not gateway.is_banned("charlie")
    assert gateway.get_banned() == []


def test_banning_takes_the_client_off_the_allow_list(gateway):
    gateway.ban("alpha")
    assert gateway.is_banned("alpha")
    assert gateway.get_allowed() == ["bravo"]
    assert gateway.get_banned() == ["alpha"]


def test_a_banned_client_cannot_send(gateway):
    gateway.ban("alpha")
    before = state(gateway)
    with pytest.raises(ClientBanned):
        gateway.send("alpha", "more")
    assert state(gateway) == before


def test_a_banned_client_cannot_be_allowed(gateway):
    gateway.ban("charlie")
    before = state(gateway)
    with pytest.raises(ClientBanned):
        gateway.allow("charlie")
    assert state(gateway) == before
    assert gateway.get_allowed() == ["alpha", "bravo"]


def test_unbanning_leaves_the_client_off_the_allow_list(gateway):
    gateway.ban("bravo")
    gateway.unban("bravo")
    assert not gateway.is_banned("bravo")
    assert gateway.get_allowed() == ["alpha"]
    with pytest.raises(AccessDenied):
        gateway.send("bravo", "hello")
    gateway.allow("bravo")
    gateway.send("bravo", "hello")
    assert gateway.get_messages("bravo") == ["hello"]
    assert gateway.get_allowed() == ["alpha", "bravo"]


def test_banning_or_unbanning_twice_is_harmless(gateway):
    gateway.ban("alpha")
    gateway.ban("alpha")
    assert gateway.get_banned() == ["alpha"]
    gateway.unban("alpha")
    gateway.unban("alpha")
    assert gateway.get_banned() == []
    gateway.unban("charlie")
    assert not gateway.is_banned("charlie")


@pytest.mark.parametrize("method", ["ban", "unban", "is_banned"])
@pytest.mark.parametrize("bad", ["delta", None, 1])
def test_ban_methods_raise_key_error_for_unknown_clients(gateway, method, bad):
    before = state(gateway)
    with pytest.raises(KeyError):
        getattr(gateway, method)(bad)
    assert state(gateway) == before
    assert gateway.get_banned() == []


def test_banned_clients_are_listed_in_registration_order(gateway):
    gateway.ban("charlie")
    gateway.ban("alpha")
    assert gateway.get_banned() == ["alpha", "charlie"]
    assert gateway.get_clients() == ["alpha", "bravo", "charlie"]


def test_revoking_a_banned_client_is_harmless(gateway):
    gateway.ban("alpha")
    gateway.revoke("alpha")
    assert gateway.is_banned("alpha")
    assert gateway.get_allowed() == ["bravo"]


def test_banning_keeps_earlier_messages(gateway):
    gateway.ban("alpha")
    assert gateway.get_messages("alpha") == ["hello"]
    gateway.unban("alpha")
    assert gateway.get_messages("alpha") == ["hello"]


def test_bad_input_is_reported_before_the_ban(gateway):
    gateway.ban("alpha")
    with pytest.raises(KeyError):
        gateway.send("delta", "hello")
    with pytest.raises(KeyError):
        gateway.allow("delta")
    with pytest.raises(ValueError):
        gateway.send("alpha", "")
    with pytest.raises(ValueError):
        gateway.send("alpha", None)


def test_the_ban_is_reported_rather_than_access_denied(gateway):
    gateway.ban("charlie")
    with pytest.raises(ClientBanned):
        gateway.send("charlie", "hello")


def test_client_banned_is_a_gateway_error_but_not_access_denied():
    assert issubclass(ClientBanned, GatewayError)
    assert not issubclass(ClientBanned, AccessDenied)
    assert not issubclass(AccessDenied, ClientBanned)


def test_banning_one_client_does_not_affect_the_others(gateway):
    gateway.ban("alpha")
    gateway.send("bravo", "hello")
    assert gateway.get_messages("bravo") == ["hello"]
    assert not gateway.is_banned("bravo")
    gateway.allow("charlie")
    assert gateway.get_allowed() == ["bravo", "charlie"]
