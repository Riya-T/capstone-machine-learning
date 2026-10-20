Limit how many players each position may have in `roster.py`.

- `Roster` takes a new keyword argument `position_limits=None`. It is either
  `None` (no limits) or a `dict` from a position to the most players allowed
  at that position. Every key must be one of `POSITIONS` and every value an
  `int` that is 0 or more (not a `bool`); otherwise `Roster(...)` raises
  `ValueError`. Positions missing from the dict have no limit.
- `add_player` raises `RosterError` if the player's position is already
  full. This comes after every check `add_player` already makes, except the
  salary cap check, which still comes last.
- `trade` raises `RosterError` if any position would be over its limit after
  the trade. This comes after the trade's other `RosterError` checks and
  before the salary cap check.
- Nothing changes when either method raises.

All existing behavior must keep working.
