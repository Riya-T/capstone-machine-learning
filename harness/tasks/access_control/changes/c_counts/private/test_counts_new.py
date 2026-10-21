"""Hidden tests for the c_counts change (message statistics). Never shown to
the writer or the editor.

Usage (with gateway.py importable, e.g. in the sandbox):
    python -m pytest changes/c_counts/private/test_counts_new.py
"""

import pytest
from gateway import AccessDenied, Gateway


@pytest.fixture
def gateway():
    gw = Gateway()
    for name in ["alpha", "bravo", "charlie"]:
        gw.register(name)
    gw.allow("alpha")
    gw.allow("bravo")
    return gw


def test_a_new_client_has_zero_counts(gateway):
    assert gateway.get_message_count("charlie") == 0
    assert gateway.get_character_count("charlie") == 0
    assert gateway.get_total_messages() == 0
    assert Gateway().get_total_messages() == 0
    assert Gateway().get_ranking() == []


def test_counts_add_up_per_client(gateway):
    gateway.send("alpha", "abc")
    gateway.send("bravo", "de")
    gateway.send("alpha", "fghij")
    assert gateway.get_message_count("alpha") == 2
    assert gateway.get_character_count("alpha") == 8
    assert gateway.get_message_count("bravo") == 1
    assert gateway.get_character_count("bravo") == 2
    assert gateway.get_total_messages() == 3


def test_repeated_messages_count_every_time(gateway):
    for _ in range(3):
        gateway.send("alpha", "ping")
    assert gateway.get_message_count("alpha") == 3
    assert gateway.get_character_count("alpha") == 12


def test_ranking_is_most_messages_first(gateway):
    gateway.allow("charlie")
    gateway.send("charlie", "a")
    gateway.send("charlie", "b")
    gateway.send("charlie", "c")
    gateway.send("alpha", "a")
    gateway.send("bravo", "a")
    gateway.send("bravo", "b")
    assert gateway.get_ranking() == [("charlie", 3), ("bravo", 2), ("alpha", 1)]


def test_ranking_ties_keep_registration_order(gateway):
    gateway.allow("charlie")
    gateway.send("charlie", "x")
    gateway.send("alpha", "y")
    assert gateway.get_ranking() == [("alpha", 1), ("charlie", 1), ("bravo", 0)]


def test_ranking_counts_messages_not_characters(gateway):
    gateway.send("alpha", "a" * 50)
    gateway.send("bravo", "b")
    gateway.send("bravo", "c")
    assert gateway.get_ranking()[0] == ("bravo", 2)


def test_failed_sends_count_nothing(gateway):
    gateway.send("alpha", "ok")
    for call in (
        lambda: gateway.send("charlie", "denied"),
        lambda: gateway.send("alpha", ""),
        lambda: gateway.send("delta", "nobody"),
    ):
        with pytest.raises((AccessDenied, ValueError, KeyError)):
            call()
    assert gateway.get_total_messages() == 1
    assert gateway.get_message_count("charlie") == 0
    assert gateway.get_character_count("alpha") == 2


def test_revoking_keeps_the_counts(gateway):
    gateway.send("alpha", "hello")
    gateway.revoke("alpha")
    assert gateway.get_message_count("alpha") == 1
    assert gateway.get_character_count("alpha") == 5
    assert gateway.get_ranking()[0] == ("alpha", 1)


@pytest.mark.parametrize("bad", ["delta", None, 1])
def test_unknown_clients_raise_key_error(gateway, bad):
    with pytest.raises(KeyError):
        gateway.get_message_count(bad)
    with pytest.raises(KeyError):
        gateway.get_character_count(bad)


def test_statistics_change_nothing(gateway):
    gateway.send("alpha", "hello")
    gateway.get_ranking()
    gateway.get_total_messages()
    gateway.get_message_count("alpha")
    assert gateway.get_messages("alpha") == ["hello"]
    assert gateway.get_allowed() == ["alpha", "bravo"]
