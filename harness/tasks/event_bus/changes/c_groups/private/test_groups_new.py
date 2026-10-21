"""Hidden tests for the c_groups change (topic groups). Never shown to the
writer or the editor.

Usage (with bus.py importable, e.g. in the sandbox):
    python -m pytest changes/c_groups/private/test_groups_new.py
"""

import pytest
from bus import BusError, EventBus

NAMES = ["billing", "shipping", "audit"]


@pytest.fixture
def bus():
    b = EventBus()
    b.add_topic("orders")
    b.add_topic("refunds")
    b.add_topic("alerts")
    b.subscribe("orders", "billing")
    b.subscribe("orders", "shipping")
    b.subscribe("refunds", "audit")
    b.subscribe("refunds", "billing")
    b.add_group("money")
    b.add_to_group("money", "orders")
    b.add_to_group("money", "refunds")
    return b


def state(b):
    topics = {t: b.get_subscribers(t) for t in b.get_topics()}
    groups = {g: b.get_group_topics(g) for g in b.get_groups()}
    return topics, groups, {n: b.get_deliveries(n) for n in NAMES}


def test_a_fresh_group_is_empty_and_listed_in_creation_order(bus):
    bus.add_group("ops")
    bus.add_group("all")
    assert bus.get_groups() == ["money", "ops", "all"]
    assert bus.get_group_topics("ops") == []
    assert bus.get_group_subscribers("ops") == []
    assert bus.publish_group("ops", "hello") == 0


@pytest.mark.parametrize("bad", ["", None, 4])
def test_bad_group_names_are_rejected(bus, bad):
    with pytest.raises(ValueError):
        bus.add_group(bad)
    assert bus.get_groups() == ["money"]


def test_creating_a_group_twice_is_rejected(bus):
    before = state(bus)
    with pytest.raises(BusError):
        bus.add_group("money")
    assert state(bus) == before


def test_a_group_may_share_a_name_with_a_topic(bus):
    bus.add_group("orders")
    bus.add_to_group("orders", "alerts")
    assert bus.get_group_topics("orders") == ["alerts"]
    assert bus.get_topics() == ["orders", "refunds", "alerts"]
    assert bus.get_subscribers("orders") == ["billing", "shipping"]


def test_group_topics_keep_the_order_they_were_added(bus):
    bus.add_group("ops")
    bus.add_to_group("ops", "alerts")
    bus.add_to_group("ops", "orders")
    assert bus.get_group_topics("ops") == ["alerts", "orders"]


def test_a_topic_may_sit_in_several_groups(bus):
    bus.add_group("ops")
    bus.add_to_group("ops", "orders")
    assert bus.get_group_topics("money") == ["orders", "refunds"]
    assert bus.get_group_topics("ops") == ["orders"]


def test_adding_a_topic_to_a_group_twice_is_rejected(bus):
    before = state(bus)
    with pytest.raises(BusError):
        bus.add_to_group("money", "orders")
    assert state(bus) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.add_to_group("people", "orders"),
        lambda b: b.add_to_group("money", "payments"),
        lambda b: b.add_to_group(None, "orders"),
        lambda b: b.add_to_group("money", None),
        lambda b: b.get_group_topics("people"),
        lambda b: b.get_group_subscribers("people"),
        lambda b: b.publish_group("people", "hi"),
        lambda b: b.publish_group(2, "hi"),
    ],
)
def test_missing_groups_and_topics_raise_key_error(bus, call):
    before = state(bus)
    with pytest.raises(KeyError):
        call(bus)
    assert state(bus) == before


def test_group_publish_walks_topics_in_group_order(bus):
    assert bus.publish_group("money", "closing") == 4
    assert bus.get_deliveries("billing") == [("orders", "closing"), ("refunds", "closing")]
    assert bus.get_deliveries("shipping") == [("orders", "closing")]
    assert bus.get_deliveries("audit") == [("refunds", "closing")]


def test_group_publish_skips_topics_outside_the_group(bus):
    bus.subscribe("alerts", "audit")
    bus.publish_group("money", "closing")
    assert bus.get_deliveries("audit") == [("refunds", "closing")]


@pytest.mark.parametrize("bad", [None, 7, ["x"]])
def test_group_publish_rejects_bad_messages(bus, bad):
    before = state(bus)
    with pytest.raises(ValueError):
        bus.publish_group("money", bad)
    assert state(bus) == before
    with pytest.raises(KeyError):
        bus.publish_group("people", bad)  # the missing group wins


def test_group_subscribers_are_distinct_in_first_appearance_order(bus):
    assert bus.get_group_subscribers("money") == ["billing", "shipping", "audit"]
    bus.add_group("reverse")
    bus.add_to_group("reverse", "refunds")
    bus.add_to_group("reverse", "orders")
    assert bus.get_group_subscribers("reverse") == ["audit", "billing", "shipping"]


def test_group_subscribers_follow_later_subscriptions(bus):
    bus.subscribe("orders", "audit")
    bus.add_to_group("money", "alerts")
    bus.subscribe("alerts", "ops")
    assert bus.get_group_subscribers("money") == ["billing", "shipping", "audit", "ops"]
