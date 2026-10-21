"""Event bus: topics, their subscribers, and a record of every delivery.

Planted bug (initial version): subscribing to the same topic twice is
accepted, so the subscriber is listed twice and receives every message twice.
The public checks never subscribe twice, so only the hidden initial tests
catch it. Never shown to the writer or the editor; validate-tasks checks
that the tests catch it.

Usage:
    from bus import EventBus
    bus = EventBus()
    bus.add_topic("orders")
    bus.subscribe("orders", "billing")
    bus.publish("orders", "order 17 placed")
"""


class BusError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_message(message):
    if not isinstance(message, str):
        raise ValueError(f"message must be a str, got {message!r}")


class EventBus:
    def __init__(self):
        self._subscribers = {}  # topic -> subscriber names in subscription order
        self._log = []  # (subscriber, topic, message), oldest first

    def add_topic(self, topic):
        check_name(topic, "topic")
        if topic in self._subscribers:
            raise BusError(f"topic {topic!r} already exists")
        self._subscribers[topic] = []

    def subscribe(self, topic, subscriber):
        self._require(topic)
        check_name(subscriber, "subscriber")
        self._subscribers[topic].append(subscriber)

    def publish(self, topic, message):
        self._require(topic)
        check_message(message)
        receivers = self._subscribers[topic]
        for subscriber in receivers:
            self._log.append((subscriber, topic, message))
        return len(receivers)

    def get_topics(self):
        return list(self._subscribers)

    def get_subscribers(self, topic):
        self._require(topic)
        return list(self._subscribers[topic])

    def get_deliveries(self, subscriber):
        return [(topic, message) for who, topic, message in self._log if who == subscriber]

    def _require(self, topic):
        # Non-str names are never stored, so they count as "does not exist" too.
        if not isinstance(topic, str) or topic not in self._subscribers:
            raise KeyError(topic)
