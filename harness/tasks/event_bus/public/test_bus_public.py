"""Public checks for bus.py.

Usage (with bus.py importable, e.g. in the sandbox):
    python -m pytest public/test_bus_public.py
"""

import pytest
from bus import EventBus


@pytest.fixture
def bus():
    b = EventBus()
    b.add_topic("orders")
    b.add_topic("alerts")
    return b


def test_a_subscriber_receives_published_messages(bus):
    bus.subscribe("orders", "billing")
    bus.publish("orders", "order 17 placed")
    assert bus.get_deliveries("billing") == [("orders", "order 17 placed")]


def test_publish_returns_how_many_deliveries_were_made(bus):
    bus.subscribe("orders", "billing")
    bus.subscribe("orders", "shipping")
    assert bus.publish("orders", "order 18 placed") == 2
    assert bus.publish("alerts", "disk full") == 0


def test_subscribers_are_listed_in_subscription_order(bus):
    bus.subscribe("orders", "shipping")
    bus.subscribe("orders", "billing")
    assert bus.get_subscribers("orders") == ["shipping", "billing"]


def test_topics_are_listed_in_creation_order(bus):
    assert bus.get_topics() == ["orders", "alerts"]


def test_a_topic_that_does_not_exist_raises_key_error(bus):
    with pytest.raises(KeyError):
        bus.publish("payments", "hello")
    with pytest.raises(KeyError):
        bus.get_subscribers("payments")


def test_a_name_that_received_nothing_gets_an_empty_list(bus):
    bus.subscribe("orders", "billing")
    assert bus.get_deliveries("billing") == []
    assert bus.get_deliveries("nobody") == []
