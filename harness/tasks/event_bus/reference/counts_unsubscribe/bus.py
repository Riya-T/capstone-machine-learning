"""Event bus with delivery statistics where subscribers can leave topics.

Correct solution for event_bus after c_counts and c_unsubscribe.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from bus import EventBus
    bus = EventBus()
    bus.add_topic("orders")
    bus.subscribe("orders", "billing")
    bus.unsubscribe("orders", "billing")
    bus.get_publish_count("orders")
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
        self._publishes = {}  # topic -> number of successful publish calls

    def add_topic(self, topic):
        check_name(topic, "topic")
        if topic in self._subscribers:
            raise BusError(f"topic {topic!r} already exists")
        self._subscribers[topic] = []
        self._publishes[topic] = 0

    def subscribe(self, topic, subscriber):
        self._require(topic)
        check_name(subscriber, "subscriber")
        if subscriber in self._subscribers[topic]:
            raise BusError(f"{subscriber!r} already subscribes to {topic!r}")
        self._subscribers[topic].append(subscriber)

    def unsubscribe(self, topic, subscriber):
        self._require(topic)
        if subscriber not in self._subscribers[topic]:
            raise BusError(f"{subscriber!r} does not subscribe to {topic!r}")
        self._subscribers[topic].remove(subscriber)

    def unsubscribe_all(self, subscriber):
        removed = 0
        for subscribers in self._subscribers.values():
            if subscriber in subscribers:
                subscribers.remove(subscriber)
                removed += 1
        return removed

    def publish(self, topic, message):
        self._require(topic)
        check_message(message)
        receivers = self._subscribers[topic]
        for subscriber in receivers:
            self._log.append((subscriber, topic, message))
        self._publishes[topic] += 1
        return len(receivers)

    def get_topics(self):
        return list(self._subscribers)

    def get_subscribers(self, topic):
        self._require(topic)
        return list(self._subscribers[topic])

    def get_deliveries(self, subscriber):
        return [(topic, message) for who, topic, message in self._log if who == subscriber]

    # -- statistics --

    def get_delivery_count(self, subscriber):
        return len(self.get_deliveries(subscriber))

    def get_publish_count(self, topic):
        self._require(topic)
        return self._publishes[topic]

    def get_topic_delivery_count(self, topic):
        self._require(topic)
        return sum(1 for _, where, _ in self._log if where == topic)

    def get_topics_by_deliveries(self):
        # sorted is stable, so equal counts keep creation order.
        return sorted(self._subscribers, key=lambda t: -self.get_topic_delivery_count(t))

    def _require(self, topic):
        # Non-str names are never stored, so they count as "does not exist" too.
        if not isinstance(topic, str) or topic not in self._subscribers:
            raise KeyError(topic)
