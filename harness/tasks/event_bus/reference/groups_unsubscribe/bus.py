"""Event bus where subscribers can leave topics and topics form groups.

Correct solution for event_bus after c_unsubscribe and c_groups.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from bus import EventBus
    bus = EventBus()
    bus.add_topic("orders")
    bus.add_group("money")
    bus.add_to_group("money", "orders")
    bus.publish_group("money", "closing")
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
        self._groups = {}  # group -> topics in the order they were added

    def add_topic(self, topic):
        check_name(topic, "topic")
        if topic in self._subscribers:
            raise BusError(f"topic {topic!r} already exists")
        self._subscribers[topic] = []

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
        return len(receivers)

    def get_topics(self):
        return list(self._subscribers)

    def get_subscribers(self, topic):
        self._require(topic)
        return list(self._subscribers[topic])

    def get_deliveries(self, subscriber):
        return [(topic, message) for who, topic, message in self._log if who == subscriber]

    # -- groups --

    def add_group(self, group):
        check_name(group, "group")
        if group in self._groups:
            raise BusError(f"group {group!r} already exists")
        self._groups[group] = []

    def add_to_group(self, group, topic):
        self._require_group(group)
        self._require(topic)
        if topic in self._groups[group]:
            raise BusError(f"topic {topic!r} is already in group {group!r}")
        self._groups[group].append(topic)

    def publish_group(self, group, message):
        self._require_group(group)
        check_message(message)
        return sum(self.publish(topic, message) for topic in self._groups[group])

    def get_groups(self):
        return list(self._groups)

    def get_group_topics(self, group):
        self._require_group(group)
        return list(self._groups[group])

    def get_group_subscribers(self, group):
        self._require_group(group)
        seen = []
        for topic in self._groups[group]:
            for subscriber in self._subscribers[topic]:
                if subscriber not in seen:
                    seen.append(subscriber)
        return seen

    def _require(self, topic):
        # Non-str names are never stored, so they count as "does not exist" too.
        if not isinstance(topic, str) or topic not in self._subscribers:
            raise KeyError(topic)

    def _require_group(self, group):
        if not isinstance(group, str) or group not in self._groups:
            raise KeyError(group)
