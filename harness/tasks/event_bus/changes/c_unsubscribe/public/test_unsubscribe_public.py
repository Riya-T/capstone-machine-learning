"""Public checks for the c_unsubscribe change (subscribers leaving topics).
Shown to the editor, never to the writer.

Usage (with bus.py importable, e.g. in the sandbox):
    python -m pytest changes/c_unsubscribe/public/test_unsubscribe_public.py
"""

import pytest
from bus import BusError, EventBus


def test_a_subscriber_that_left_gets_nothing_more():
    bus = EventBus()
    bus.add_topic("orders")
    bus.subscribe("orders", "billing")
    bus.publish("orders", "first")
    bus.unsubscribe("orders", "billing")
    assert bus.publish("orders", "second") == 0
    assert bus.get_subscribers("orders") == []
    assert bus.get_deliveries("billing") == [("orders", "first")]


def test_leaving_a_topic_not_subscribed_to_raises():
    bus = EventBus()
    bus.add_topic("orders")
    with pytest.raises(BusError):
        bus.unsubscribe("orders", "billing")


def test_leaving_every_topic_reports_how_many():
    bus = EventBus()
    bus.add_topic("orders")
    bus.add_topic("alerts")
    bus.subscribe("orders", "billing")
    bus.subscribe("alerts", "billing")
    assert bus.unsubscribe_all("billing") == 2
    assert bus.unsubscribe_all("billing") == 0
