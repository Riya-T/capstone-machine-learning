"""Public checks for gateway.py.

Usage (with gateway.py importable, e.g. in the sandbox):
    python -m pytest public/test_gateway_public.py
"""

import pytest
from gateway import AccessDenied, Gateway


@pytest.fixture
def gateway():
    gw = Gateway()
    gw.register("alpha")
    gw.register("bravo")
    return gw


def test_clients_are_listed_in_registration_order(gateway):
    assert gateway.get_clients() == ["alpha", "bravo"]
    assert gateway.get_allowed() == []


def test_an_allowed_client_can_send(gateway):
    gateway.allow("alpha")
    gateway.send("alpha", "hello")
    gateway.send("alpha", "again")
    assert gateway.get_allowed() == ["alpha"]
    assert gateway.get_messages("alpha") == ["hello", "again"]
    assert gateway.get_messages("bravo") == []


def test_a_client_off_the_allow_list_is_denied(gateway):
    with pytest.raises(AccessDenied):
        gateway.send("bravo", "hello")


def test_revoking_takes_a_client_off_the_allow_list(gateway):
    gateway.allow("bravo")
    gateway.allow("alpha")
    assert gateway.get_allowed() == ["alpha", "bravo"]  # registration order
    gateway.revoke("alpha")
    assert gateway.get_allowed() == ["bravo"]
    with pytest.raises(AccessDenied):
        gateway.send("alpha", "hello")


def test_unknown_client_raises_key_error(gateway):
    with pytest.raises(KeyError):
        gateway.allow("charlie")
    with pytest.raises(KeyError):
        gateway.revoke("charlie")
    with pytest.raises(KeyError):
        gateway.get_messages("charlie")
