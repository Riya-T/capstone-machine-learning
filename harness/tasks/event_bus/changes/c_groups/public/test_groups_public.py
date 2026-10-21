"""Public checks for the c_groups change (topic groups). Shown to the
editor, never to the writer.

Usage (with bus.py importable, e.g. in the sandbox):
    python -m pytest changes/c_groups/public/test_groups_public.py
"""

import pytest
from bus import EventBus


@pytest.fixture
def bus():
    b = EventBus()
    b.add_topic("orders")
    b.add_topic("refunds")
    b.subscribe("orders", "billing")
    b.subscribe("refunds", "billing")
    b.subscribe("refunds", "audit")
    b.add_group("money")
    b.add_to_group("money", "orders")
    b.add_to_group("money", "refunds")
    return b


def test_a_group_message_reaches_every_topic(bus):
    assert bus.publish_group("money", "closing") == 3
    assert bus.get_deliveries("billing") == [("orders", "closing"), ("refunds", "closing")]
    assert bus.get_deliveries("audit") == [("refunds", "closing")]


def test_group_members_are_listed(bus):
    assert bus.get_groups() == ["money"]
    assert bus.get_group_topics("money") == ["orders", "refunds"]
    assert bus.get_group_subscribers("money") == ["billing", "audit"]


def test_a_group_that_does_not_exist_raises_key_error(bus):
    with pytest.raises(KeyError):
        bus.publish_group("people", "hi")
