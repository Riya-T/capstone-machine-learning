Add topic groups to `bus.py`, so one message can go to several related
topics at once.

- Add `EventBus.add_group(group)`, which creates an empty group. The name
  must be a non-empty `str`, or `ValueError` is raised; a name that is
  already a group raises `BusError`. Group names and topic names are
  independent: a group may have the same name as a topic.
- Add `EventBus.add_to_group(group, topic)`, which puts an existing topic
  into the group. It raises `KeyError` for a group that does not exist, then
  `KeyError` for a topic that does not exist, then `BusError` if the topic is
  already in the group. A topic may belong to any number of groups.
- Add `EventBus.get_groups() -> list[str]`, the groups in the order they
  were added, and `EventBus.get_group_topics(group) -> list[str]`, the
  group's topics in the order they were added to it (`KeyError` for a group
  that does not exist).
- Add `EventBus.publish_group(group, message) -> int`, which publishes the
  message to each topic of the group, in the group's topic order, exactly as
  `publish` would, and returns the total number of deliveries. It raises
  `KeyError` for a group that does not exist, then `ValueError` for a message
  that is not a `str`. A subscriber of two topics in the group receives the
  message twice. An empty group gives 0.
- Add `EventBus.get_group_subscribers(group) -> list[str]`: every subscriber
  of at least one topic in the group, listed once each, in order of first
  appearance when walking the group's topics in order and each topic's
  subscribers in subscription order. `KeyError` for a group that does not
  exist.

A failed call changes nothing. All existing behavior must keep working.
