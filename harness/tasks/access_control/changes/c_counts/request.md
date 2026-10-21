Add message statistics to `gateway.py`.

- Add `Gateway.get_message_count(client_id) -> int`: how many messages the
  client has sent. It raises `KeyError` for a client that is not registered.
- Add `Gateway.get_character_count(client_id) -> int`: the total length of
  the client's messages, in characters. It raises `KeyError` for a client
  that is not registered.
- Add `Gateway.get_total_messages() -> int`: the number of messages sent
  over all clients.
- Add `Gateway.get_ranking() -> list[tuple[str, int]]`: every registered
  client with its message count, most messages first. Clients with equal
  counts come in the order they were registered. Clients that sent nothing
  are included with a count of 0.
- Only messages that were recorded count: a `send` that raised adds
  nothing. Taking a client off the allow list changes none of its counts.

All existing behavior must keep working.
