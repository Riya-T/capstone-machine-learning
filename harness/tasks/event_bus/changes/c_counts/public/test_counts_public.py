"""Public checks for the c_counts change (delivery statistics). Shown to the
editor, never to the writer.

Usage (with bus.py importable, e.g. in the sandbox):
    python -m pytest changes/c_counts/public/test_counts_public.py
"""

from bus import EventBus


def test_counts_follow_publishes_and_deliveries():
    bus = EventBus()
    bus.add_topic("orders")
    bus.subscribe("orders", "billing")
    bus.subscribe("orders", "shipping")
    bus.publish("orders", "a")
    bus.publish("orders", "b")
    assert bus.get_publish_count("orders") == 2
    assert bus.get_topic_delivery_count("orders") == 4
    assert bus.get_delivery_count("billing") == 2
    assert bus.get_delivery_count("nobody") == 0


def test_publishing_to_nobody_still_counts_as_a_publish():
    bus = EventBus()
    bus.add_topic("alerts")
    bus.publish("alerts", "disk full")
    assert bus.get_publish_count("alerts") == 1
    assert bus.get_topic_delivery_count("alerts") == 0


def test_topics_are_ranked_by_deliveries():
    bus = EventBus()
    bus.add_topic("quiet")
    bus.add_topic("busy")
    bus.subscribe("busy", "billing")
    bus.publish("busy", "x")
    assert bus.get_topics_by_deliveries() == ["busy", "quiet"]
