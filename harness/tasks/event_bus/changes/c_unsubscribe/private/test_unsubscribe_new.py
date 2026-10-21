"""Hidden tests for the c_unsubscribe change (subscribers leaving topics).
Never shown to the writer or the editor.

Usage (with bus.py importable, e.g. in the sandbox):
    python -m pytest changes/c_unsubscribe/private/test_unsubscribe_new.py
"""

import pytest
from bus import BusError, EventBus

NAMES = ["billing", "shipping", "audit"]


@pytest.fixture
def bus():
    b = EventBus()
    b.add_topic("orders")
    b.add_topic("alerts")
    b.subscribe("orders", "billing")
    b.subscribe("orders", "shipping")
    b.subscribe("alerts", "billing")
    b.publish("orders", "order 1")
    return b


def state(b):
    topics = {t: b.get_subscribers(t) for t in b.get_topics()}
    return topics, {n: b.get_deliveries(n) for n in NAMES}


def test_leaving_stops_deliveries_and_keeps_old_ones(bus):
    bus.unsubscribe("orders", "billing")
    bus.publish("orders", "order 2")
    assert bus.get_deliveries("billing") == [("orders", "order 1")]
    assert bus.get_deliveries("shipping") == [("orders", "order 1"), ("orders", "order 2")]


def test_leaving_removes_the_name_from_the_list_and_the_count(bus):
    bus.unsubscribe("orders", "billing")
    assert bus.get_subscribers("orders") == ["shipping"]
    assert bus.publish("orders", "order 2") == 1


def test_leaving_one_topic_keeps_the_others(bus):
    bus.unsubscribe("orders", "billing")
    assert bus.get_subscribers("alerts") == ["billing"]
    bus.publish("alerts", "disk full")
    assert bus.get_deliveries("billing") == [("orders", "order 1"), ("alerts", "disk full")]


def test_rejoining_puts_the_subscriber_last(bus):
    bus.unsubscribe("orders", "billing")
    bus.subscribe("orders", "billing")
    assert bus.get_subscribers("orders") == ["shipping", "billing"]
    bus.publish("orders", "order 2")
    assert bus.get_deliveries("billing") == [("orders", "order 1"), ("orders", "order 2")]


@pytest.mark.parametrize("who", ["audit", "shipping"])
def test_leaving_without_a_subscription_raises_bus_error(bus, who):
    # "audit" never subscribed to alerts; "shipping" subscribes to orders only.
    before = state(bus)
    with pytest.raises(BusError):
        bus.unsubscribe("alerts", who)
    assert state(bus) == before


def test_leaving_twice_raises_the_second_time(bus):
    bus.unsubscribe("orders", "billing")
    before = state(bus)
    with pytest.raises(BusError):
        bus.unsubscribe("orders", "billing")
    assert state(bus) == before


@pytest.mark.parametrize("topic", ["payments", None, 1])
def test_leaving_a_missing_topic_raises_key_error_first(bus, topic):
    before = state(bus)
    with pytest.raises(KeyError):
        bus.unsubscribe(topic, "audit")  # not subscribed either: KeyError wins
    assert state(bus) == before


def test_leaving_everything_clears_every_topic(bus):
    assert bus.unsubscribe_all("billing") == 2
    assert bus.get_subscribers("orders") == ["shipping"]
    assert bus.get_subscribers("alerts") == []
    assert bus.publish("orders", "order 2") == 1
    assert bus.publish("alerts", "disk full") == 0


def test_leaving_everything_counts_only_current_subscriptions(bus):
    assert bus.unsubscribe_all("shipping") == 1
    assert bus.unsubscribe_all("shipping") == 0
    assert bus.unsubscribe_all("audit") == 0
    assert bus.unsubscribe_all(None) == 0


def test_leaving_everything_keeps_deliveries_and_other_subscribers(bus):
    bus.subscribe("orders", "audit")
    bus.unsubscribe_all("billing")
    assert bus.get_deliveries("billing") == [("orders", "order 1")]
    assert bus.get_subscribers("orders") == ["shipping", "audit"]
    assert bus.get_topics() == ["orders", "alerts"]
