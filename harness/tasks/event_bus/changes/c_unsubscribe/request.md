Let subscribers leave topics in `bus.py`.

- Add `EventBus.unsubscribe(topic, subscriber)`, which removes the subscriber
  from the topic. It raises `KeyError` for a topic that does not exist, and
  `BusError` for an existing topic that the subscriber does not currently
  subscribe to. In each case nothing changes.
- After unsubscribing, the subscriber is no longer listed by
  `get_subscribers`, messages published to the topic are not delivered to it,
  and `publish` does not count it. Its subscriptions to other topics are not
  affected.
- Everything the subscriber received before leaving stays in
  `get_deliveries`.
- A subscriber that left may subscribe to the same topic again; it is then
  placed at the end of the topic's subscriber order.
- Add `EventBus.unsubscribe_all(subscriber) -> int`, which removes the
  subscriber from every topic it subscribes to and returns the number of
  topics it was removed from. A name that subscribes to nothing gives 0 and
  raises nothing. As with `unsubscribe`, earlier deliveries are kept.
- Leaving never removes a topic. For example, if `"billing"` is the only
  subscriber of `"alerts"`, then after `unsubscribe_all("billing")` (or
  `unsubscribe("alerts", "billing")`), `get_topics()` still lists
  `"alerts"`, `get_subscribers("alerts")` is `[]`, and
  `publish("alerts", "x")` returns 0.

All existing behavior must keep working.
