"""Hidden tests for the initial event_bus spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with bus.py importable, e.g. in the sandbox):
    python -m pytest private/test_bus_initial.py
"""

import pytest
from bus import BusError, EventBus

BAD_NAMES = ["", None, 3]
BAD_MESSAGES = [None, 5, b"bytes", ["a list"]]
NAMES = ["billing", "shipping", "audit", "nobody"]


@pytest.fixture
def bus():
    b = EventBus()
    b.add_topic("orders")
    b.add_topic("alerts")
    b.subscribe("orders", "billing")
    return b


def state(b):
    """Every topic's subscribers and every known name's deliveries, to check
    that a failed call changed nothing."""
    topics = {t: b.get_subscribers(t) for t in b.get_topics()}
    deliveries = {n: b.get_deliveries(n) for n in NAMES}
    return topics, deliveries


# --- topics -----------------------------------------------------------------


def test_a_new_topic_has_no_subscribers(bus):
    assert bus.get_subscribers("alerts") == []


def test_topics_are_listed_in_creation_order():
    b = EventBus()
    for name in ["zeta", "alpha", "mid"]:
        b.add_topic(name)
    assert b.get_topics() == ["zeta", "alpha", "mid"]


@pytest.mark.parametrize("bad", [""])
def test_invalid_topic_names_are_rejected(bad):
    b = EventBus()
    with pytest.raises(ValueError):
        b.add_topic(bad)
    assert b.get_topics() == []


def test_adding_an_existing_topic_is_rejected(bus):
    before = state(bus)
    with pytest.raises(BusError):
        bus.add_topic("orders")
    assert state(bus) == before
    assert bus.get_topics() == ["orders", "alerts"]


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.subscribe("payments", "billing"),
        lambda b: b.publish("payments", "hello"),
        lambda b: b.get_subscribers("payments"),
        lambda b: b.subscribe(None, "billing"),
        lambda b: b.publish(1, "hello"),
        lambda b: b.get_subscribers(None),
    ],
)
def test_topics_that_do_not_exist_raise_key_error(bus, call):
    bus.publish("orders", "seed")
    before = state(bus)
    with pytest.raises(KeyError):
        call(bus)
    assert state(bus) == before


# --- subscribers ------------------------------------------------------------


def test_subscribers_keep_subscription_order(bus):
    bus.subscribe("orders", "shipping")
    bus.subscribe("orders", "audit")
    assert bus.get_subscribers("orders") == ["billing", "shipping", "audit"]


@pytest.mark.parametrize("bad", BAD_NAMES)
def test_invalid_subscriber_names_are_rejected(bus, bad):
    before = state(bus)
    with pytest.raises(ValueError):
        bus.subscribe("orders", bad)
    assert state(bus) == before


def test_subscribing_twice_to_one_topic_is_rejected(bus):
    before = state(bus)
    with pytest.raises(BusError):
        bus.subscribe("orders", "billing")
    assert state(bus) == before
    assert bus.publish("orders", "once") == 1
    assert bus.get_deliveries("billing") == [("orders", "once")]


def test_one_subscriber_can_follow_several_topics(bus):
    bus.subscribe("alerts", "billing")
    assert bus.get_subscribers("orders") == ["billing"]
    assert bus.get_subscribers("alerts") == ["billing"]
    bus.publish("alerts", "disk full")
    bus.publish("orders", "order 1")
    assert bus.get_deliveries("billing") == [("alerts", "disk full"), ("orders", "order 1")]


def test_subscribing_to_one_topic_does_not_touch_another(bus):
    bus.subscribe("alerts", "shipping")
    assert bus.get_subscribers("orders") == ["billing"]


# --- publishing -------------------------------------------------------------


def test_publish_reaches_every_subscriber(bus):
    bus.subscribe("orders", "shipping")
    bus.publish("orders", "order 1")
    assert bus.get_deliveries("billing") == [("orders", "order 1")]
    assert bus.get_deliveries("shipping") == [("orders", "order 1")]
    assert bus.get_deliveries("audit") == []


def test_publish_returns_the_number_of_deliveries(bus):
    assert bus.publish("orders", "a") == 1
    bus.subscribe("orders", "shipping")
    bus.subscribe("orders", "audit")
    assert bus.publish("orders", "b") == 3


def test_publishing_to_a_topic_without_subscribers_returns_zero(bus):
    assert bus.publish("alerts", "nobody home") == 0
    assert state(bus)[1] == {n: [] for n in NAMES}


@pytest.mark.parametrize("bad", BAD_MESSAGES)
def test_invalid_messages_are_rejected(bus, bad):
    before = state(bus)
    with pytest.raises(ValueError):
        bus.publish("orders", bad)
    assert state(bus) == before


def test_the_empty_message_is_delivered(bus):
    assert bus.publish("orders", "") == 1
    assert bus.get_deliveries("billing") == [("orders", "")]


def test_deliveries_are_oldest_first_across_topics(bus):
    bus.subscribe("alerts", "billing")
    bus.publish("orders", "first")
    bus.publish("alerts", "second")
    bus.publish("orders", "third")
    assert bus.get_deliveries("billing") == [
        ("orders", "first"),
        ("alerts", "second"),
        ("orders", "third"),
    ]


def test_the_same_message_twice_is_delivered_twice(bus):
    bus.publish("orders", "ping")
    bus.publish("orders", "ping")
    assert bus.get_deliveries("billing") == [("orders", "ping"), ("orders", "ping")]


def test_late_subscribers_miss_earlier_messages(bus):
    bus.publish("orders", "before")
    bus.subscribe("orders", "shipping")
    bus.publish("orders", "after")
    assert bus.get_deliveries("shipping") == [("orders", "after")]
    assert bus.get_deliveries("billing") == [("orders", "before"), ("orders", "after")]


def test_a_missing_topic_is_reported_before_a_bad_subscriber_or_message(bus):
    with pytest.raises(KeyError):
        bus.subscribe("payments", "")
    with pytest.raises(KeyError):
        bus.publish("payments", None)


def test_failed_calls_deliver_nothing(bus):
    for call in (
        lambda: bus.publish("orders", 7),
        lambda: bus.publish("payments", "x"),
        lambda: bus.subscribe("orders", "billing"),
        lambda: bus.subscribe("orders", ""),
    ):
        with pytest.raises((KeyError, ValueError, BusError)):
            call()
    assert bus.get_deliveries("billing") == []
    assert bus.get_subscribers("orders") == ["billing"]


def test_buses_do_not_share_topics():
    first, second = EventBus(), EventBus()
    first.add_topic("orders")
    first.subscribe("orders", "billing")
    first.publish("orders", "x")
    assert second.get_topics() == []
    assert second.get_deliveries("billing") == []
    second.add_topic("orders")
    assert second.get_subscribers("orders") == []
