Passengers want to know where they can change trams. Add two queries to
`trams.py`.

- Add `TramNetwork.get_connections(line) -> list[str]`: the names of the
  other lines that share at least one stop with `line`, in the order of
  `get_lines()`. A line is never listed among its own connections, and a
  line that shares no stop with another line (including a line with no
  stops) returns `[]`.
- Add `TramNetwork.get_shared_stops(first, second) -> list[str]`: the stops
  that both lines have, in the order they come on line `first`, or `[]` if
  they share none. Passing the same line twice raises `ValueError`.
- Both raise `KeyError` for a line that is not in use, like the other
  methods.
- Both only read the network: they change no line and no stop.
- Connections always follow the current stops: a stop taken off a line by
  `remove_stop` or `close_stop` no longer connects it, and after
  `merge_lines` the first line connects through all of its stops.

All existing behavior must keep working.
