# Event bus

Write a module `bus.py` that routes messages from topics to the subscribers
of those topics and remembers what every subscriber has received.

## Interface

```python
class BusError(Exception): ...


class EventBus:
    def __init__(self): ...
    def add_topic(self, topic: str) -> None: ...
    def subscribe(self, topic: str, subscriber: str) -> None: ...
    def publish(self, topic: str, message: str) -> int: ...
    def get_topics(self) -> list[str]: ...
    def get_subscribers(self, topic: str) -> list[str]: ...
    def get_deliveries(self, subscriber: str) -> list[tuple[str, str]]: ...
```

## Topics

- `add_topic(topic)` creates a topic with no subscribers. An empty name
  raises `ValueError`, and a name that is already a topic raises `BusError`.
- `get_topics()` returns the names of all topics, in the order they were
  added.
- Every other method that takes a topic raises `KeyError` when the topic does
  not exist, including values that are not strings at all, such as `None` or
  `1`.

## Subscribers

- `subscribe(topic, subscriber)` adds the subscriber to the topic. A
  subscriber is a non-empty `str`; anything else raises `ValueError`. A
  subscriber that already subscribes to the topic raises `BusError`. The same
  subscriber may subscribe to any number of topics.
- `get_subscribers(topic)` returns the topic's subscribers in the order they
  subscribed.

## Publishing

- `publish(topic, message)` delivers the message to every subscriber of the
  topic, in the order they subscribed, and returns the number of deliveries
  made (0 when the topic has no subscribers). The message must be a `str`;
  anything else raises `ValueError`. The empty string is a valid message.
- `get_deliveries(subscriber)` returns everything the subscriber has
  received, oldest first, as `(topic, message)` tuples. A name that has never
  received anything gives `[]`, even if it never subscribed to any topic.
- A subscriber only receives messages published after it subscribed.

When a call has several problems, `ValueError` for an invalid subscriber
or message is raised before `BusError` for a subscriber that already
subscribes to the topic.

A failed call has no effect: if a method raises, the topics, the subscribers
and every subscriber's deliveries are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which of `KeyError` and `ValueError` is raised when a call has
both problems, topic names that are not strings passed to `add_topic`, values that
are not strings passed to `get_deliveries`, what happens if a returned list is
changed, the text of error messages, saving the bus to a file, and use from
several threads.
