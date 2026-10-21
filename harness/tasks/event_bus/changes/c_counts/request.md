Add delivery statistics to `bus.py`.

- Add `EventBus.get_delivery_count(subscriber) -> int`: how many deliveries
  the subscriber has received so far, over all topics. A name that received
  nothing gives 0.
- Add `EventBus.get_publish_count(topic) -> int`: how many successful
  `publish` calls have been made on the topic, including calls that
  delivered to nobody. Calls that raised are not counted.
- Add `EventBus.get_topic_delivery_count(topic) -> int`: the total number of
  deliveries made on the topic, summed over all its subscribers.
- Add `EventBus.get_topics_by_deliveries() -> list[str]`: every topic, the
  one with the most deliveries first. Topics with equal delivery counts keep
  the order they were added in. Topics with no deliveries are included.
- `get_publish_count` and `get_topic_delivery_count` raise `KeyError` for a
  topic that does not exist.

All existing behavior must keep working.
