"""Hidden tests for the c_counts change (delivery statistics). Never shown to
the writer or the editor.

Usage (with bus.py importable, e.g. in the sandbox):
    python -m pytest changes/c_counts/private/test_counts_new.py
"""

import pytest
from bus import BusError, EventBus


@pytest.fixture
def bus():
    b = EventBus()
    b.add_topic("orders")
    b.add_topic("alerts")
    b.add_topic("refunds")
    b.subscribe("orders", "billing")
    b.subscribe("orders", "shipping")
    b.subscribe("alerts", "billing")
    return b


def test_everything_starts_at_zero(bus):
    for topic in bus.get_topics():
        assert bus.get_publish_count(topic) == 0
        assert bus.get_topic_delivery_count(topic) == 0
    assert bus.get_delivery_count("billing") == 0
    assert bus.get_topics_by_deliveries() == ["orders", "alerts", "refunds"]


def test_subscriber_count_matches_its_deliveries(bus):
    bus.publish("orders", "a")
    bus.publish("alerts", "b")
    bus.publish("orders", "c")
    assert bus.get_delivery_count("billing") == 3 == len(bus.get_deliveries("billing"))
    assert bus.get_delivery_count("shipping") == 2
    assert bus.get_delivery_count("audit") == 0


def test_publish_count_includes_calls_that_reached_nobody(bus):
    bus.publish("refunds", "x")
    bus.publish("refunds", "y")
    assert bus.get_publish_count("refunds") == 2
    assert bus.get_topic_delivery_count("refunds") == 0


def test_failed_publishes_are_not_counted(bus):
    for bad in (None, 3):
        with pytest.raises(ValueError):
            bus.publish("orders", bad)
    with pytest.raises(KeyError):
        bus.publish("payments", "x")
    assert bus.get_publish_count("orders") == 0
    assert bus.get_topic_delivery_count("orders") == 0
    assert bus.get_delivery_count("billing") == 0


def test_topic_delivery_count_sums_over_subscribers(bus):
    bus.publish("orders", "a")
    bus.publish("orders", "b")
    bus.subscribe("orders", "audit")
    bus.publish("orders", "c")
    assert bus.get_publish_count("orders") == 3
    assert bus.get_topic_delivery_count("orders") == 7
    assert bus.get_topic_delivery_count("alerts") == 0


def test_the_empty_message_counts(bus):
    bus.publish("alerts", "")
    assert bus.get_publish_count("alerts") == 1
    assert bus.get_topic_delivery_count("alerts") == 1
    assert bus.get_delivery_count("billing") == 1


@pytest.mark.parametrize("method", ["get_publish_count", "get_topic_delivery_count"])
@pytest.mark.parametrize("topic", ["payments", None, 1])
def test_statistics_for_a_missing_topic_raise_key_error(bus, method, topic):
    with pytest.raises(KeyError):
        getattr(bus, method)(topic)


def test_ranking_puts_the_most_delivered_topic_first(bus):
    bus.publish("alerts", "a")  # 1 delivery
    bus.publish("orders", "b")  # 2 deliveries
    assert bus.get_topics_by_deliveries() == ["orders", "alerts", "refunds"]
    bus.publish("alerts", "c")
    bus.publish("alerts", "d")  # alerts now 3
    assert bus.get_topics_by_deliveries() == ["alerts", "orders", "refunds"]


def test_ranking_ties_keep_creation_order(bus):
    bus.subscribe("refunds", "audit")
    bus.publish("refunds", "r")
    bus.publish("alerts", "a")  # alerts and refunds both at 1, orders at 0
    assert bus.get_topics_by_deliveries() == ["alerts", "refunds", "orders"]


def test_ranking_counts_deliveries_not_publishes(bus):
    bus.publish("refunds", "x")
    bus.publish("refunds", "y")
    bus.publish("refunds", "z")  # three publishes, zero deliveries
    bus.publish("alerts", "a")  # one publish, one delivery
    assert bus.get_topics_by_deliveries() == ["alerts", "orders", "refunds"]


def test_rejected_subscriptions_change_no_counts(bus):
    with pytest.raises(BusError):
        bus.subscribe("orders", "billing")
    bus.publish("orders", "a")
    assert bus.get_delivery_count("billing") == 1
    assert bus.get_topic_delivery_count("orders") == 2
