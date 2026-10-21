"""Hidden tests for the initial access_control spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with gateway.py importable, e.g. in the sandbox):
    python -m pytest private/test_gateway_initial.py
"""

import pytest
from gateway import AccessDenied, Gateway, GatewayError

BAD_MESSAGES = ["", None, 5, b"bytes", ["hello"]]


@pytest.fixture
def gateway():
    gw = Gateway()
    gw.register("alpha")
    gw.register("bravo")
    gw.register("charlie")
    gw.allow("alpha")
    return gw


def state(gw):
    """Allow list and every message list, to check that a failed call changed nothing."""
    return (gw.get_allowed(), {c: gw.get_messages(c) for c in gw.get_clients()})


# --- clients ----------------------------------------------------------------


def test_a_new_gateway_has_no_clients():
    gw = Gateway()
    assert gw.get_clients() == []
    assert gw.get_allowed() == []


def test_clients_are_listed_in_registration_order():
    gw = Gateway()
    for name in ["zulu", "alpha", "mike"]:
        gw.register(name)
    assert gw.get_clients() == ["zulu", "alpha", "mike"]


def test_a_new_client_is_not_allowed_and_has_no_messages(gateway):
    assert gateway.get_messages("bravo") == []
    assert gateway.get_allowed() == ["alpha"]
    with pytest.raises(AccessDenied):
        gateway.send("bravo", "hello")


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_client_ids_are_rejected(bad_id):
    gw = Gateway()
    with pytest.raises(ValueError):
        gw.register(bad_id)
    assert gw.get_clients() == []


def test_registering_a_registered_client_is_rejected(gateway):
    gateway.send("alpha", "hello")
    before = state(gateway)
    with pytest.raises(GatewayError):
        gateway.register("alpha")
    assert state(gateway) == before
    assert gateway.get_clients() == ["alpha", "bravo", "charlie"]


@pytest.mark.parametrize(
    "call",
    [
        lambda gw: gw.allow("delta"),
        lambda gw: gw.revoke("delta"),
        lambda gw: gw.send("delta", "hello"),
        lambda gw: gw.get_messages("delta"),
        lambda gw: gw.allow(None),
        lambda gw: gw.get_messages(1),
    ],
)
def test_clients_that_are_not_registered_raise_key_error(gateway, call):
    gateway.send("alpha", "hello")
    before = state(gateway)
    with pytest.raises(KeyError):
        call(gateway)
    assert state(gateway) == before


# --- allow list -------------------------------------------------------------


def test_allowed_clients_are_listed_in_registration_order(gateway):
    gateway.allow("charlie")
    gateway.allow("bravo")
    assert gateway.get_allowed() == ["alpha", "bravo", "charlie"]


def test_allowing_twice_is_harmless(gateway):
    gateway.allow("alpha")
    assert gateway.get_allowed() == ["alpha"]
    gateway.send("alpha", "hello")
    assert gateway.get_messages("alpha") == ["hello"]


def test_revoking_removes_only_that_client(gateway):
    gateway.allow("bravo")
    gateway.revoke("alpha")
    assert gateway.get_allowed() == ["bravo"]
    assert gateway.get_clients() == ["alpha", "bravo", "charlie"]


def test_revoking_a_client_that_is_not_allowed_is_harmless(gateway):
    gateway.revoke("bravo")
    gateway.revoke("bravo")
    assert gateway.get_allowed() == ["alpha"]


def test_a_revoked_client_can_be_allowed_again(gateway):
    gateway.revoke("alpha")
    with pytest.raises(AccessDenied):
        gateway.send("alpha", "hello")
    gateway.allow("alpha")
    gateway.send("alpha", "hello")
    assert gateway.get_allowed() == ["alpha"]
    assert gateway.get_messages("alpha") == ["hello"]


# --- messages ---------------------------------------------------------------


def test_messages_are_listed_oldest_first(gateway):
    for text in ["one", "two", "three"]:
        gateway.send("alpha", text)
    assert gateway.get_messages("alpha") == ["one", "two", "three"]


def test_messages_are_kept_per_client(gateway):
    gateway.allow("bravo")
    gateway.send("alpha", "from alpha")
    gateway.send("bravo", "from bravo")
    gateway.send("alpha", "alpha again")
    assert gateway.get_messages("alpha") == ["from alpha", "alpha again"]
    assert gateway.get_messages("bravo") == ["from bravo"]
    assert gateway.get_messages("charlie") == []


def test_the_same_text_may_be_sent_twice(gateway):
    gateway.send("alpha", "ping")
    gateway.send("alpha", "ping")
    assert gateway.get_messages("alpha") == ["ping", "ping"]


def test_a_denied_send_records_nothing(gateway):
    before = state(gateway)
    with pytest.raises(AccessDenied):
        gateway.send("bravo", "hello")
    assert state(gateway) == before


def test_revoking_keeps_earlier_messages(gateway):
    gateway.send("alpha", "hello")
    gateway.revoke("alpha")
    assert gateway.get_messages("alpha") == ["hello"]
    with pytest.raises(AccessDenied):
        gateway.send("alpha", "more")
    assert gateway.get_messages("alpha") == ["hello"]


@pytest.mark.parametrize("message", BAD_MESSAGES)
def test_invalid_messages_are_rejected(gateway, message):
    before = state(gateway)
    with pytest.raises(ValueError):
        gateway.send("alpha", message)
    assert state(gateway) == before


def test_an_unregistered_client_is_reported_before_a_bad_message(gateway):
    with pytest.raises(KeyError):
        gateway.send("delta", "")


def test_a_bad_message_is_reported_before_access_is_checked(gateway):
    with pytest.raises(ValueError):
        gateway.send("bravo", "")
    with pytest.raises(ValueError):
        gateway.send("bravo", None)


def test_access_denied_is_a_gateway_error():
    assert issubclass(AccessDenied, GatewayError)


def test_gateways_do_not_share_clients():
    first, second = Gateway(), Gateway()
    first.register("alpha")
    first.allow("alpha")
    first.send("alpha", "hello")
    assert second.get_clients() == []
    second.register("alpha")
    assert second.get_allowed() == []
    assert second.get_messages("alpha") == []
