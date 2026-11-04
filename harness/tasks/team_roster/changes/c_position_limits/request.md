Limit how many players each position may have in `roster.py`.

- `Roster` takes a new keyword argument `position_limits=None`. It is either
  `None` (no limits) or a `dict` from a position to the most players allowed
  at that position. Every key must be one of `POSITIONS` and every value an
  `int` that is 0 or more; otherwise `Roster(...)` raises
  `ValueError`. Positions missing from the dict have no limit.
- `add_player` raises `RosterError` if the player's position is already
  full.
- `trade` raises `RosterError` if any position would be over its limit after
  the trade.
- When a call also has another problem (for example a bad salary, a
  repeated name, or going over the salary cap), which error is raised is
  unspecified.
- Nothing changes when either method raises.

All existing behavior must keep working.
